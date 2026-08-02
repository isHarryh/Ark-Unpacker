# Copyright (c) 2022-2026, Harry Huang
# @ BSD 3-Clause License
"""A dependency-free local web UI for browsing ArkUnpacker resources."""

from __future__ import annotations

import argparse
import hashlib
import json
import mimetypes
import os
import re
import shutil
import tempfile
import threading
import zipfile
import webbrowser
from collections import OrderedDict
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path, PurePosixPath
from typing import Any, Optional
from urllib.parse import parse_qs, quote, urlparse


APP_VERSION = "1.0"
MAX_DIRECTORY_RESULTS = 1000
MAX_SEARCH_RESULTS = 500
MAX_TEXT_PREVIEW = 1024 * 1024

_ASSET_DIR = Path(__file__).with_name("assets")
_BUNDLE_EXTENSIONS = {".ab", ".bin"}
_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".tif", ".tiff"}
_AUDIO_EXTENSIONS = {".wav", ".mp3", ".ogg", ".m4a", ".aac", ".flac", ".wem"}
_VIDEO_EXTENSIONS = {".mp4", ".webm", ".mov", ".mkv", ".avi", ".usm"}
_TEXT_EXTENSIONS = {
    ".txt", ".json", ".xml", ".csv", ".yaml", ".yml", ".md", ".ini", ".cfg",
    ".atlas", ".skel", ".asset", ".bytes", ".lua", ".shader", ".html", ".css", ".js",
}
_MODEL_EXTENSIONS = {".obj", ".fbx", ".gltf", ".glb", ".mesh"}
_TYPE_TO_KIND = {
    "Sprite": "image",
    "Texture2D": "image",
    "AudioClip": "audio",
    "TextAsset": "text",
    "MonoScript": "text",
    "Mesh": "model",
}


class BrowserError(Exception):
    """An error safe to show in the browser."""

    def __init__(self, message: str, status: HTTPStatus = HTTPStatus.BAD_REQUEST):
        super().__init__(message)
        self.status = status


def _file_kind(path: Path) -> str:
    if path.is_dir():
        return "directory"
    ext = path.suffix.lower()
    if ext in _BUNDLE_EXTENSIONS:
        return "bundle"
    if ext in _IMAGE_EXTENSIONS:
        return "image"
    if ext in _AUDIO_EXTENSIONS:
        return "audio"
    if ext in _VIDEO_EXTENSIONS:
        return "video"
    if ext in _MODEL_EXTENSIONS:
        return "model"
    if ext in _TEXT_EXTENSIONS:
        return "text"
    return "other"


def _format_mtime(timestamp: float) -> str:
    return datetime.fromtimestamp(timestamp).astimezone().isoformat(timespec="seconds")


def _parse_date_boundary(value: str, *, end: bool) -> Optional[float]:
    if not value:
        return None
    try:
        day = date.fromisoformat(value)
    except ValueError as exc:
        raise BrowserError(f"日期格式无效：{value}") from exc
    if end:
        day += timedelta(days=1)
    return datetime.combine(day, time.min).astimezone().timestamp()


def _safe_download_name(value: str, fallback: str = "resource") -> str:
    value = re.sub(r"[\x00-\x1f\x7f\"\\/]", "_", value).strip(" .")
    return value or fallback


def _content_disposition(mode: str, filename: str) -> str:
    filename = _safe_download_name(filename)
    ascii_name = filename.encode("ascii", errors="ignore").decode("ascii").strip(" .") or "resource"
    return f'{mode}; filename="{ascii_name}"; filename*=UTF-8\'\'{quote(filename, safe="")}'


class BrowserState:
    """Stores the selected root and resolves browser paths without traversal."""

    def __init__(self, root: str | os.PathLike[str]):
        self._lock = threading.RLock()
        self._root = self._validate_root(root)

    @staticmethod
    def _validate_root(root: str | os.PathLike[str]) -> Path:
        path = Path(root).expanduser().resolve()
        if not path.exists():
            raise BrowserError(f"目录不存在：{path}")
        if not path.is_dir():
            raise BrowserError(f"资源根路径必须是目录：{path}")
        return path

    @property
    def root(self) -> Path:
        with self._lock:
            return self._root

    def set_root(self, root: str | os.PathLike[str]) -> Path:
        new_root = self._validate_root(root)
        with self._lock:
            self._root = new_root
        return new_root

    def resolve(self, relative: str, *, require_file: bool = False, require_dir: bool = False) -> Path:
        relative = (relative or "").replace("\\", "/").strip("/")
        parts = PurePosixPath(relative).parts if relative else ()
        if any(part in {"", ".", ".."} for part in parts):
            raise BrowserError("路径无效。")
        root = self.root
        candidate = root.joinpath(*parts).resolve()
        try:
            candidate.relative_to(root)
        except ValueError as exc:
            raise BrowserError("拒绝访问资源根目录之外的路径。", HTTPStatus.FORBIDDEN) from exc
        if not candidate.exists():
            raise BrowserError("资源不存在。", HTTPStatus.NOT_FOUND)
        if require_file and not candidate.is_file():
            raise BrowserError("所选资源不是文件。")
        if require_dir and not candidate.is_dir():
            raise BrowserError("所选路径不是目录。")
        return candidate

    def relative(self, path: Path) -> str:
        return path.relative_to(self.root).as_posix()

    def describe_entry(self, path: Path) -> dict[str, Any]:
        stat = path.stat()
        kind = _file_kind(path)
        return {
            "name": path.name,
            "path": self.relative(path),
            "kind": kind,
            "extension": path.suffix.lower(),
            "size": 0 if kind == "directory" else stat.st_size,
            "modified": _format_mtime(stat.st_mtime),
        }

    def list_entries(
        self,
        relative: str = "",
        query: str = "",
        kind: str = "all",
        regex: bool = False,
        modified_from: str = "",
        modified_to: str = "",
    ) -> dict[str, Any]:
        directory = self.resolve(relative, require_dir=True)
        query_folded = query.strip().casefold()
        time_from = _parse_date_boundary(modified_from, end=False)
        time_to = _parse_date_boundary(modified_to, end=True)
        if time_from is not None and time_to is not None and time_from >= time_to:
            raise BrowserError("开始日期不能晚于结束日期。")
        pattern = None
        if regex and query.strip():
            try:
                pattern = re.compile(query, re.IGNORECASE)
            except re.error as exc:
                raise BrowserError(f"正则表达式无效：{exc}") from exc
        limit = MAX_SEARCH_RESULTS if query_folded else MAX_DIRECTORY_RESULTS
        entries: list[dict[str, Any]] = []
        truncated = False

        def accepts(path: Path) -> bool:
            path_kind = _file_kind(path)
            matches_kind = kind in {"", "all"} or path_kind == kind
            modified = path.stat().st_mtime
            matches_time = (time_from is None or modified >= time_from) and (time_to is None or modified < time_to)
            if not query_folded:
                return matches_kind and matches_time
            if pattern is not None:
                return matches_kind and matches_time and pattern.search(self.relative(path)) is not None
            return matches_kind and matches_time and query_folded in path.name.casefold()

        iterator = directory.rglob("*") if query_folded else directory.iterdir()
        try:
            for child in iterator:
                try:
                    if not accepts(child):
                        continue
                    if len(entries) >= limit:
                        truncated = True
                        break
                    entries.append(self.describe_entry(child))
                except (OSError, ValueError):
                    continue
        except OSError as exc:
            raise BrowserError(f"无法读取目录：{exc}", HTTPStatus.FORBIDDEN) from exc

        entries.sort(key=lambda item: (item["kind"] != "directory", item["name"].casefold()))
        summary: dict[str, int] = {}
        for item in entries:
            summary[item["kind"]] = summary.get(item["kind"], 0) + 1
        return {
            "root": str(self.root),
            "path": self.relative(directory),
            "entries": entries,
            "summary": summary,
            "query": query,
            "regex": regex,
            "modifiedFrom": modified_from,
            "modifiedTo": modified_to,
            "truncated": truncated,
        }


@dataclass
class BundlePayload:
    data: bytes
    filename: str
    content_type: str
    kind: str


class BrowserBundle:
    """A bundle object index whose IDs remain unique across nested files."""

    def __init__(self, environment: Any, fallback_name: str):
        self.environment = environment
        self.readers: dict[str, Any] = {}
        self.entries: list[dict[str, Any]] = []
        self.name = getattr(getattr(environment, "file", None), "name", "") or fallback_name

        for index, reader in enumerate(environment.objects):
            object_id = str(index)
            type_name = getattr(getattr(reader, "type", None), "name", "Unknown")
            try:
                name = reader.peek_name() or f"{type_name}_{reader.path_id}"
            except Exception:
                name = f"{type_name}_{reader.path_id}"
            self.readers[object_id] = reader
            self.entries.append(
                {
                    "name": str(name),
                    "objectId": object_id,
                    # PathID is local to a SerializedFile and is only metadata;
                    # objectId is the unique identifier used by WebUI requests.
                    "pathId": str(reader.path_id),
                    "source": self._source_path(reader),
                    "type": type_name,
                    "kind": _TYPE_TO_KIND.get(type_name, "object"),
                    "size": int(getattr(reader, "byte_size", 0)),
                }
            )
            if type_name == "AssetBundle":
                try:
                    internal_name = getattr(reader.read(), "m_Name", "")
                    if internal_name:
                        self.name = Path(str(internal_name)).name
                except Exception:
                    pass

    @staticmethod
    def _source_path(reader: Any) -> str:
        parts: list[str] = []
        current = getattr(reader, "assets_file", None)
        visited: set[int] = set()
        while current is not None and id(current) not in visited:
            visited.add(id(current))
            name = getattr(current, "name", None)
            if name:
                parts.append(str(name))
            current = getattr(current, "parent", None)
        parts.reverse()
        return "/".join(parts)

    def get_reader(self, *, object_id: Optional[str] = None, path_id: Optional[int] = None):
        if object_id is not None:
            reader = self.readers.get(str(object_id))
            if reader is None:
                raise BrowserError("Bundle 中不存在该对象。", HTTPStatus.NOT_FOUND)
            return reader
        matches = [reader for reader in self.readers.values() if reader.path_id == path_id]
        if not matches:
            raise BrowserError("Bundle 中不存在该对象。", HTTPStatus.NOT_FOUND)
        if len(matches) > 1:
            raise BrowserError("该 PathID 在嵌套 Bundle 中不唯一，请刷新页面后重试。", HTTPStatus.CONFLICT)
        return matches[0]


class BundleStore:
    """Small thread-safe LRU cache for loaded Unity bundles."""

    def __init__(self, max_entries: int = 2):
        self._max_entries = max_entries
        self._lock = threading.RLock()
        self._cache: OrderedDict[tuple[str, int, int], BrowserBundle] = OrderedDict()

    def clear(self) -> None:
        with self._lock:
            self._cache.clear()

    def _load_locked(self, path: Path):
        stat = path.stat()
        key = (str(path), stat.st_mtime_ns, stat.st_size)
        cached = self._cache.get(key)
        if cached is not None:
            self._cache.move_to_end(key)
            return cached

        try:
            import UnityPy
            import src.ResolveAB  # noqa: F401 - installs Arknights decompression support
        except ImportError as exc:
            raise BrowserError(
                "缺少资源解析依赖，请先运行 poetry install 安装项目依赖。",
                HTTPStatus.SERVICE_UNAVAILABLE,
            ) from exc

        try:
            environment = UnityPy.load(path.read_bytes())
            resource = BrowserBundle(environment, path.name)
        except Exception as exc:
            raise BrowserError(f"无法解析 AssetBundle：{exc}", HTTPStatus.UNPROCESSABLE_ENTITY) from exc

        stale_keys = [item for item in self._cache if item[0] == str(path)]
        for stale in stale_keys:
            self._cache.pop(stale, None)
        self._cache[key] = resource
        while len(self._cache) > self._max_entries:
            self._cache.popitem(last=False)
        return resource

    def describe(self, path: Path) -> dict[str, Any]:
        with self._lock:
            resource = self._load_locked(path)
            objects = []
            summary: dict[str, int] = {}
            for entry in resource.entries:
                kind = entry["kind"]
                summary[kind] = summary.get(kind, 0) + 1
                objects.append(entry.copy())
            objects.sort(key=lambda item: (item["kind"], item["name"].casefold(), int(item["pathId"])))
            return {
                "name": resource.name or path.name,
                "path": path.name,
                "objectCount": len(objects),
                "summary": summary,
                "objects": objects,
            }

    def object_payload(
        self,
        path: Path,
        path_id: int | str | None = None,
        *,
        object_id: Optional[str] = None,
    ) -> BundlePayload:
        with self._lock:
            numeric_path_id: Optional[int] = None
            if object_id is None:
                try:
                    numeric_path_id = int(path_id)  # type: ignore[arg-type]
                except (TypeError, ValueError) as exc:
                    raise BrowserError("对象标识无效。") from exc
            resource = self._load_locked(path)
            reader = resource.get_reader(object_id=object_id, path_id=numeric_path_id)
            actual_path_id = reader.path_id
            type_name = getattr(getattr(reader, "type", None), "name", "Unknown")
            try:
                name = reader.peek_name() or f"{type_name}_{actual_path_id}"
            except Exception:
                name = f"{type_name}_{actual_path_id}"

            try:
                obj = reader.read()
                from src.utils.SaverUtils import SafeSaver

                exported = next(iter(SafeSaver.iter_object_export_items(obj)), None)
                if exported is not None:
                    filename = _safe_download_name(exported.name + exported.ext)
                    content_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
                    if type_name in {"TextAsset", "MonoScript"} and content_type == "application/octet-stream":
                        content_type = "text/plain; charset=utf-8"
                    return BundlePayload(exported.data, filename, content_type, _TYPE_TO_KIND.get(type_name, "object"))
            except Exception as export_error:
                export_message = str(export_error)
            else:
                export_message = "该对象没有直接可导出的媒体内容"

            try:
                tree = reader.read_typetree()
                data = json.dumps(tree, ensure_ascii=False, indent=2, default=str).encode("utf-8")
                return BundlePayload(data, _safe_download_name(f"{name}.json"), "application/json; charset=utf-8", "text")
            except Exception as tree_error:
                raise BrowserError(
                    f"无法预览该 {type_name} 对象：{export_message}；Typetree：{tree_error}",
                    HTTPStatus.UNPROCESSABLE_ENTITY,
                ) from tree_error

    @staticmethod
    def _archive_source_dir(source: str) -> str:
        parts = [
            _safe_download_name(part, "source")
            for part in source.replace("\\", "/").split("/")
            if part not in {"", ".", ".."}
        ]
        return "/".join(parts) or "root"

    @staticmethod
    def _unique_archive_name(desired: str, used: set[str]) -> str:
        if desired not in used:
            used.add(desired)
            return desired
        path = PurePosixPath(desired)
        parent = "" if str(path.parent) == "." else f"{path.parent.as_posix()}/"
        stem, suffix = path.stem, path.suffix
        index = 1
        while True:
            candidate = f"{parent}{stem}${index}{suffix}"
            if candidate not in used:
                used.add(candidate)
                return candidate
            index += 1

    def write_archive(self, path: Path, destination: Path) -> dict[str, int]:
        """Export all supported objects into a ZIP grouped by nested source."""
        with self._lock:
            resource = self._load_locked(path)
            try:
                from src.utils.SaverUtils import SafeSaver
            except ImportError as exc:
                raise BrowserError("缺少资源导出依赖。", HTTPStatus.SERVICE_UNAVAILABLE) from exc

            used: set[str] = set()
            exported = 0
            skipped = 0
            failed = 0
            manifest_objects: list[dict[str, Any]] = []
            destination.parent.mkdir(parents=True, exist_ok=True)
            try:
                with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
                    for entry in resource.entries:
                        reader = resource.get_reader(object_id=entry["objectId"])
                        written: list[str] = []
                        try:
                            obj = reader.read()
                            items = list(SafeSaver.iter_object_export_items(obj))
                            if not items:
                                skipped += 1
                            for item in items:
                                source_dir = self._archive_source_dir(entry["source"])
                                filename = _safe_download_name(item.name + item.ext)
                                archive_name = self._unique_archive_name(f"{source_dir}/{filename}", used)
                                archive.writestr(archive_name, item.data)
                                written.append(archive_name)
                                exported += 1
                        except Exception as exc:
                            failed += 1
                            written.append(f"ERROR: {exc}")
                        manifest_objects.append(
                            {
                                "name": entry["name"],
                                "type": entry["type"],
                                "pathId": entry["pathId"],
                                "source": entry["source"],
                                "exported": written,
                            }
                        )

                    manifest = {
                        "source": path.name,
                        "bundleName": resource.name,
                        "objectCount": len(resource.entries),
                        "exportedFileCount": exported,
                        "skippedObjectCount": skipped,
                        "failedObjectCount": failed,
                        "objects": manifest_objects,
                    }
                    archive.writestr(
                        "_arkunpacker_manifest.json",
                        json.dumps(manifest, ensure_ascii=False, indent=2).encode("utf-8"),
                    )
            except Exception as exc:
                try:
                    destination.unlink(missing_ok=True)
                except OSError:
                    pass
                raise BrowserError(f"AssetBundle 自动解包失败：{exc}", HTTPStatus.UNPROCESSABLE_ENTITY) from exc
            return {"exported": exported, "skipped": skipped, "failed": failed}


class BundleArchiveStore:
    """Caches ZIP archives generated from AssetBundles."""

    def __init__(self, bundles: BundleStore, max_entries: int = 2):
        self._bundles = bundles
        self._max_entries = max_entries
        self._lock = threading.RLock()
        self._tempdir = tempfile.TemporaryDirectory(prefix="arkunpacker-ab-")
        self._cache: OrderedDict[tuple[str, int, int], tuple[Path, dict[str, int]]] = OrderedDict()

    @staticmethod
    def _key(path: Path) -> tuple[str, int, int]:
        stat = path.stat()
        return str(path), stat.st_mtime_ns, stat.st_size

    @staticmethod
    def _remove(path: Path) -> None:
        try:
            path.unlink(missing_ok=True)
        except OSError:
            pass

    def prepare(self, path: Path) -> tuple[Path, dict[str, int]]:
        key = self._key(path)
        with self._lock:
            cached = self._cache.get(key)
            if cached is not None and cached[0].is_file():
                self._cache.move_to_end(key)
                return cached
            digest = hashlib.sha256(f"{key[0]}:{key[1]}:{key[2]}".encode("utf-8")).hexdigest()[:24]
            output = Path(self._tempdir.name) / f"{digest}.zip"
            self._remove(output)
            stats = self._bundles.write_archive(path, output)
            stale = [item for item in self._cache if item[0] == str(path)]
            for stale_key in stale:
                stale_path, _ = self._cache.pop(stale_key)
                if stale_path != output:
                    self._remove(stale_path)
            self._cache[key] = (output, stats)
            while len(self._cache) > self._max_entries:
                _, (expired, _) = self._cache.popitem(last=False)
                self._remove(expired)
            return output, stats

    def clear(self) -> None:
        with self._lock:
            for path, _ in self._cache.values():
                self._remove(path)
            self._cache.clear()

    def close(self) -> None:
        with self._lock:
            self.clear()
            self._tempdir.cleanup()


class UsmPreviewStore:
    """Creates and caches browser-compatible MP4 previews for USM files."""

    def __init__(self, max_entries: int = 3):
        self._max_entries = max_entries
        self._lock = threading.RLock()
        self._tempdir = tempfile.TemporaryDirectory(prefix="arkunpacker-usm-")
        self._cache: OrderedDict[tuple[str, int, int], Path] = OrderedDict()

    def close(self) -> None:
        with self._lock:
            self.clear()
            self._tempdir.cleanup()

    def clear(self) -> None:
        with self._lock:
            cached_dirs = {path.parent for path in self._cache.values()}
            self._cache.clear()
            for cached_dir in cached_dirs:
                self._remove_path(cached_dir)

    @staticmethod
    def _cache_key(path: Path) -> tuple[str, int, int]:
        stat = path.stat()
        return str(path), stat.st_mtime_ns, stat.st_size

    @staticmethod
    def _remove_path(path: Path) -> None:
        if path.is_dir():
            shutil.rmtree(path, ignore_errors=True)
        else:
            try:
                path.unlink(missing_ok=True)
            except OSError:
                pass

    def prepare(self, path: Path) -> Path:
        key = self._cache_key(path)
        with self._lock:
            cached = self._cache.get(key)
            if cached is not None and cached.is_file():
                self._cache.move_to_end(key)
                return cached

            try:
                import ffmpeg
                from src.ResolveUSM import UsmProcessor
                from src.utils.Config import Config
            except ImportError as exc:
                raise BrowserError(
                    "缺少 USM 解析依赖，请先安装项目依赖和 FFmpeg。",
                    HTTPStatus.SERVICE_UNAVAILABLE,
                ) from exc

            digest = hashlib.sha256(f"{key[0]}:{key[1]}:{key[2]}".encode("utf-8")).hexdigest()[:24]
            work_dir = Path(self._tempdir.name) / digest
            self._remove_path(work_dir)
            work_dir.mkdir(parents=True)
            output = work_dir / "preview.mp4"

            try:
                processor = UsmProcessor(str(path), encoding=Config.get("usm_encoding"))
                processor.extract_media(str(work_dir))
                if not processor.video_paths:
                    raise BrowserError("该 USM 文件中没有视频轨道。", HTTPStatus.UNPROCESSABLE_ENTITY)

                video_input = ffmpeg.input(processor.video_paths[0])
                output_args: dict[str, Any] = {
                    "vcodec": "libx264",
                    "pix_fmt": "yuv420p",
                    "movflags": "+faststart",
                }
                if processor.audio_paths:
                    audio_input = ffmpeg.input(processor.audio_paths[0])
                    stream = ffmpeg.output(
                        video_input.video,
                        audio_input.audio,
                        str(output),
                        acodec="aac",
                        shortest=None,
                        **output_args,
                    )
                else:
                    stream = ffmpeg.output(video_input.video, str(output), **output_args)
                stream.overwrite_output().run(quiet=True)
                if not output.is_file() or output.stat().st_size == 0:
                    raise RuntimeError("FFmpeg did not create a preview file")
            except BrowserError:
                self._remove_path(work_dir)
                raise
            except Exception as exc:
                self._remove_path(work_dir)
                raise BrowserError(
                    f"USM 预览转换失败，请确认 FFmpeg 可用：{exc}",
                    HTTPStatus.UNPROCESSABLE_ENTITY,
                ) from exc

            # Keep only the MP4; demuxed source streams are no longer needed.
            for child in list(work_dir.iterdir()):
                if child != output:
                    self._remove_path(child)

            stale = [item for item in self._cache if item[0] == str(path)]
            for stale_key in stale:
                stale_path = self._cache.pop(stale_key)
                if stale_path.parent != output.parent:
                    self._remove_path(stale_path.parent)
            self._cache[key] = output
            while len(self._cache) > self._max_entries:
                _, expired = self._cache.popitem(last=False)
                self._remove_path(expired.parent)
            return output


class ResourceBrowserServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, address: tuple[str, int], root: str | os.PathLike[str]):
        self.state = BrowserState(root)
        self.bundles = BundleStore()
        self.bundle_archives = BundleArchiveStore(self.bundles)
        self.usm_previews = UsmPreviewStore()
        super().__init__(address, ResourceBrowserHandler)

    def server_close(self) -> None:
        self.bundle_archives.close()
        self.usm_previews.close()
        super().server_close()


class ResourceBrowserHandler(BaseHTTPRequestHandler):
    server: ResourceBrowserServer
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt: str, *args: Any) -> None:
        print(f"[WebUI] {self.address_string()} - {fmt % args}")

    def do_GET(self) -> None:
        try:
            parsed = urlparse(self.path)
            params = parse_qs(parsed.query)
            route = parsed.path
            if route == "/api/status":
                self._send_json({"version": APP_VERSION, "root": str(self.server.state.root)})
            elif route == "/api/files":
                self._send_json(
                    self.server.state.list_entries(
                        self._param(params, "path"),
                        self._param(params, "q"),
                        self._param(params, "kind", "all"),
                        self._param(params, "regex") == "1",
                        self._param(params, "modifiedFrom"),
                        self._param(params, "modifiedTo"),
                    )
                )
            elif route == "/api/bundle":
                path = self._resolve_bundle(params)
                payload = self.server.bundles.describe(path)
                payload["path"] = self.server.state.relative(path)
                self._send_json(payload)
            elif route == "/api/bundle/object":
                self._serve_bundle_object(params)
            elif route == "/api/bundle/archive/prepare":
                path = self._resolve_bundle(params)
                archive, stats = self.server.bundle_archives.prepare(path)
                self._send_json({"ready": True, "size": archive.stat().st_size, **stats})
            elif route == "/api/bundle/archive":
                path = self._resolve_bundle(params)
                archive, _ = self.server.bundle_archives.prepare(path)
                self._stream_path(
                    archive,
                    "application/zip",
                    _content_disposition("attachment", f"{path.stem}_unpacked.zip"),
                )
            elif route == "/api/usm/prepare":
                path = self._resolve_usm(params)
                preview = self.server.usm_previews.prepare(path)
                self._send_json({"ready": True, "size": preview.stat().st_size})
            elif route == "/api/usm/preview":
                path = self._resolve_usm(params)
                preview = self.server.usm_previews.prepare(path)
                disposition = "attachment" if self._param(params, "download") == "1" else "inline"
                self._stream_path(
                    preview,
                    "video/mp4",
                    _content_disposition(disposition, f"{path.stem}.mp4"),
                )
            elif route == "/api/text":
                self._serve_text(params)
            elif route == "/api/file":
                self._serve_file(params)
            elif route == "/":
                self._serve_asset("index.html")
            elif route.startswith("/assets/"):
                self._serve_asset(route.removeprefix("/assets/"))
            else:
                raise BrowserError("页面不存在。", HTTPStatus.NOT_FOUND)
        except BrowserError as exc:
            self._send_json({"error": str(exc)}, exc.status)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            pass
        except Exception as exc:
            self._send_json({"error": f"服务器内部错误：{exc}"}, HTTPStatus.INTERNAL_SERVER_ERROR)

    def do_POST(self) -> None:
        try:
            route = urlparse(self.path).path
            if route != "/api/root":
                raise BrowserError("接口不存在。", HTTPStatus.NOT_FOUND)
            length = int(self.headers.get("Content-Length", "0"))
            if length > 64 * 1024:
                raise BrowserError("请求内容过大。", HTTPStatus.REQUEST_ENTITY_TOO_LARGE)
            try:
                data = json.loads(self.rfile.read(length).decode("utf-8"))
            except (UnicodeError, json.JSONDecodeError) as exc:
                raise BrowserError("请求不是有效的 JSON。") from exc
            root = self.server.state.set_root(str(data.get("path", "")))
            self.server.bundle_archives.clear()
            self.server.bundles.clear()
            self.server.usm_previews.clear()
            self._send_json({"root": str(root)})
        except BrowserError as exc:
            self._send_json({"error": str(exc)}, exc.status)
        except Exception as exc:
            self._send_json({"error": f"服务器内部错误：{exc}"}, HTTPStatus.INTERNAL_SERVER_ERROR)

    @staticmethod
    def _param(params: dict[str, list[str]], key: str, default: str = "") -> str:
        return params.get(key, [default])[0]

    def _serve_asset(self, relative: str) -> None:
        if not relative or "/" in relative or "\\" in relative or relative.startswith("."):
            raise BrowserError("静态资源路径无效。", HTTPStatus.NOT_FOUND)
        path = _ASSET_DIR / relative
        if not path.is_file():
            raise BrowserError("静态资源不存在。", HTTPStatus.NOT_FOUND)
        content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        self._send_bytes(path.read_bytes(), content_type, cache="no-cache")

    def _serve_text(self, params: dict[str, list[str]]) -> None:
        path = self.server.state.resolve(self._param(params, "path"), require_file=True)
        size = path.stat().st_size
        with path.open("rb") as source:
            raw = source.read(MAX_TEXT_PREVIEW + 1)
        truncated = len(raw) > MAX_TEXT_PREVIEW
        raw = raw[:MAX_TEXT_PREVIEW]
        if b"\x00" in raw[:8192]:
            raise BrowserError("该文件是二进制数据，无法作为文本预览。", HTTPStatus.UNSUPPORTED_MEDIA_TYPE)
        text = raw.decode("utf-8", errors="replace")
        if path.suffix.lower() == ".json":
            try:
                text = json.dumps(json.loads(text), ensure_ascii=False, indent=2)
            except json.JSONDecodeError:
                pass
        self._send_json({"text": text, "size": size, "truncated": truncated})

    def _serve_file(self, params: dict[str, list[str]]) -> None:
        path = self.server.state.resolve(self._param(params, "path"), require_file=True)
        download = self._param(params, "download") == "1"
        content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        disposition = "attachment" if download else "inline"
        self._stream_path(path, content_type, _content_disposition(disposition, path.name))

    def _serve_bundle_object(self, params: dict[str, list[str]]) -> None:
        path = self.server.state.resolve(self._param(params, "path"), require_file=True)
        object_id = self._param(params, "objectId")
        path_id: Optional[int] = None
        if not object_id:
            try:
                path_id = int(self._param(params, "pathId"))
            except ValueError as exc:
                raise BrowserError("对象标识无效。") from exc
        payload = self.server.bundles.object_payload(path, path_id, object_id=object_id or None)
        disposition = "attachment" if self._param(params, "download") == "1" else "inline"
        self._send_bytes(
            payload.data,
            payload.content_type,
            disposition=_content_disposition(disposition, payload.filename),
        )

    def _resolve_bundle(self, params: dict[str, list[str]]) -> Path:
        path = self.server.state.resolve(self._param(params, "path"), require_file=True)
        if _file_kind(path) != "bundle":
            raise BrowserError("所选文件不是 AssetBundle。")
        return path

    def _resolve_usm(self, params: dict[str, list[str]]) -> Path:
        path = self.server.state.resolve(self._param(params, "path"), require_file=True)
        if path.suffix.lower() != ".usm":
            raise BrowserError("所选文件不是 USM 视频。")
        return path

    def _stream_path(self, path: Path, content_type: str, disposition: str) -> None:
        total = path.stat().st_size
        start, end = 0, max(total - 1, 0)
        status = HTTPStatus.OK
        range_header = self.headers.get("Range")
        if range_header and total:
            match = re.fullmatch(r"bytes=(\d*)-(\d*)", range_header.strip())
            if not match:
                self.send_error(HTTPStatus.REQUESTED_RANGE_NOT_SATISFIABLE)
                return
            first, last = match.groups()
            if not first and last:
                length = min(int(last), total)
                start = total - length
            else:
                start = int(first or 0)
                end = min(int(last), total - 1) if last else total - 1
            if start > end or start >= total:
                self.send_response(HTTPStatus.REQUESTED_RANGE_NOT_SATISFIABLE)
                self.send_header("Content-Range", f"bytes */{total}")
                self.send_header("Content-Length", "0")
                self.end_headers()
                return
            status = HTTPStatus.PARTIAL_CONTENT

        length = end - start + 1 if total else 0
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(length))
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Disposition", disposition)
        self.send_header("X-Content-Type-Options", "nosniff")
        if status == HTTPStatus.PARTIAL_CONTENT:
            self.send_header("Content-Range", f"bytes {start}-{end}/{total}")
        self.end_headers()
        if self.command == "HEAD" or not length:
            return
        with path.open("rb") as source:
            source.seek(start)
            remaining = length
            while remaining:
                chunk = source.read(min(64 * 1024, remaining))
                if not chunk:
                    break
                self.wfile.write(chunk)
                remaining -= len(chunk)

    def _send_json(self, payload: Any, status: HTTPStatus = HTTPStatus.OK) -> None:
        self._send_bytes(
            json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            "application/json; charset=utf-8",
            status=status,
            cache="no-store",
        )

    def _send_bytes(
        self,
        payload: bytes,
        content_type: str,
        *,
        status: HTTPStatus = HTTPStatus.OK,
        cache: str = "private, max-age=3600",
        disposition: Optional[str] = None,
    ) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", cache)
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'self'; img-src 'self' data:; media-src 'self'; style-src 'self'; script-src 'self'")
        if disposition:
            self.send_header("Content-Disposition", disposition)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(payload)


def run_server(
    root: str | os.PathLike[str] = ".",
    host: str = "127.0.0.1",
    port: int = 0,
    *,
    open_browser: bool = True,
) -> None:
    """Run the resource browser until interrupted."""
    server = ResourceBrowserServer((host, port), root)
    actual_host, actual_port = server.server_address[:2]
    browser_host = "127.0.0.1" if actual_host in {"0.0.0.0", "::"} else actual_host
    url = f"http://{browser_host}:{actual_port}/"
    print(f"ArkUnpacker WebUI 已启动：{url}")
    print(f"资源根目录：{server.state.root}")
    print("按 Ctrl+C 停止服务。")
    if open_browser:
        threading.Timer(0.25, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever(poll_interval=0.25)
    except KeyboardInterrupt:
        print("\n正在停止 ArkUnpacker WebUI...")
    finally:
        server.server_close()


def main() -> None:
    parser = argparse.ArgumentParser(description="ArkUnpacker local web resource browser")
    parser.add_argument("root", nargs="?", default=".", help="initial resource directory")
    parser.add_argument("--host", default="127.0.0.1", help="listen address (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=0, help="listen port; 0 chooses an available port")
    parser.add_argument("--no-browser", action="store_true", help="do not open the default browser")
    args = parser.parse_args()
    run_server(args.root, args.host, args.port, open_browser=not args.no_browser)


if __name__ == "__main__":
    main()
