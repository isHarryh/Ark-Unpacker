# Copyright (c) 2022-2026, Harry Huang
# @ BSD 3-Clause License
import os
import os.path as osp
import re
import json
import threading
from contextlib import ContextDecorator
from io import BytesIO
from typing import Callable, Optional, Sequence

import UnityPy.classes as uc
from PIL import Image

from .Profiler import CodeProfiler
from .Config import Config, PerformanceLevel
from .Logger import Logger
from .TaskUtils import CoroutineCtrl


class EntryLock(ContextDecorator):
    """The entry lock class to prevent simultaneous access to the same entry."""

    _ENTRIES = set()
    _INTERNAL_LOCK = threading.Condition()

    def __init__(self, entry):
        self.entry = entry

    def __enter__(self):
        with EntryLock._INTERNAL_LOCK:
            while self.entry in EntryLock._ENTRIES:
                EntryLock._INTERNAL_LOCK.wait()
            EntryLock._ENTRIES.add(self.entry)

    def __exit__(self, exc_type, exc_val, exc_tb):
        with EntryLock._INTERNAL_LOCK:
            EntryLock._ENTRIES.discard(self.entry)
            EntryLock._INTERNAL_LOCK.notify_all()

    # EndClass


class SafeSaver(CoroutineCtrl):
    """The file saver class to save file and avoid file name collision."""

    __instance = None
    _EXT_IMAGE = ".png"
    _EXT_RAW = ""

    def __init__(self):
        """Not recommended to use. Please use the static methods."""
        max_concurrency = PerformanceLevel.get_thread_limit(Config.get("performance_level"))
        super(SafeSaver, self).__init__(self._save_async, max_concurrency=max_concurrency, name="Saver")
        # Cache config values to avoid repeated reads
        self._export_encoding = Config.get("export_encoding")
        self._export_json_indent = Config.get("export_json_indent")

    @staticmethod
    def get_instance():
        if not SafeSaver.__instance:
            SafeSaver.__instance = SafeSaver()
        return SafeSaver.__instance

    @staticmethod
    def save_bytes(
        data: bytes,
        destdir: str,
        name: str,
        ext: str,
        on_queued: Optional[Callable] = None,
        on_saved: Optional[Callable] = None,
    ):
        """Saves a binary data to a file.

        :param data: Bytes data;
        :param destdir: Destination directory;
        :param name: File name (without the extension);
        :param ext: File extension;
        :param on_queued: Callback `f()` invoked when the file was queued, `None` for ignore;
        :param on_saved: Callback `f(file_path_or_none_for_not_saved)`, `None` for ignore;
        :rtype: None;
        """
        if on_queued:
            on_queued()
        SafeSaver.get_instance().submit((data, destdir, name, ext, on_saved))

    @staticmethod
    def save_image(
        img: Image.Image,
        destdir: str,
        name: str,
        ext: str = _EXT_IMAGE,
        on_queued: Optional[Callable] = None,
        on_saved: Optional[Callable] = None,
    ):
        """Saves an image to a file.

        :param img: Image instance;
        :param destdir: Destination directory;
        :param name: File name (without the extension);
        :param ext: File extension, `png` for default;
        :param on_queued: Callback `f()` invoked when the file was queued, `None` for ignore;
        :param on_saved: Callback `f(file_path_or_none_for_not_saved)`, `None` for ignore;
        :rtype: None;
        """
        bio = BytesIO()
        img.save(bio, format=ext.lstrip("."))
        SafeSaver.save_bytes(bio.getvalue(), destdir, name, ext, on_queued, on_saved)

    @staticmethod
    def save_object(
        obj: uc.Object,
        destdir: str,
        name: str,
        on_queued: Optional[Callable] = None,
        on_saved: Optional[Callable] = None,
    ):
        """Saves the given Unity object as a file. If a object is not exportable, it does nothing.

        :param obj: The object to save as file;
        :param destdir: Destination directory;
        :param name: File name (without the extension);
        :param on_queued: Callback `f()` invoked when the file was queued, `None` for ignore;
        :param on_saved: Callback `f(file_path_or_none_for_not_saved)`, `None` for ignore;
        :rtype: None;
        """
        if obj.object_reader is None or obj.object_reader.byte_size == 0:
            # No data:
            pass
        elif isinstance(obj, (uc.Sprite, uc.Texture2D)):
            # As image file:
            if obj.image.width > 0 and obj.image.height > 0:
                SafeSaver.save_image(obj.image, destdir, name, SafeSaver._EXT_IMAGE, on_queued, on_saved)
                return
        elif isinstance(obj, uc.AudioClip):
            # As audio file:
            samples = obj.samples
            if samples:
                for name, byte in samples.items():
                    SafeSaver.save_bytes(byte, destdir, name, SafeSaver._EXT_RAW, on_queued, on_saved)
            return
        elif isinstance(obj, uc.TextAsset):
            # As raw file:
            byte = obj.m_Script.encode("utf-8", "surrogateescape")
            SafeSaver.save_bytes(byte, destdir, name, SafeSaver._EXT_RAW, on_queued, on_saved)
            return
        elif isinstance(obj, uc.Mesh):
            # As mesh file (.obj):
            try:
                obj_data = obj.export()
                SafeSaver.save_bytes(obj_data.encode("utf-8"), destdir, name, ".obj", on_queued, on_saved)
            except Exception as e:
                Logger.warn(f"SafeSaver: Failed to export Mesh: {e}")
            return
        else:
            # Not an exportable type:
            pass

    @staticmethod
    def save_json(
        data: dict,
        destdir: str,
        name: str,
        on_queued: Optional[Callable] = None,
        on_saved: Optional[Callable] = None,
    ):
        """Saves the given data as a JSON file.

        :param data: The data dictionary to save;
        :param destdir: Destination directory;
        :param name: File name (without the extension);
        :param on_queued: Callback `f()` invoked when the file was queued, `None` for ignore;
        :param on_saved: Callback `f(file_path_or_none_for_not_saved)`, `None` for ignore;
        :rtype: None;
        """

        def serialize_inplace(tree: dict):
            for k, v in tree.items():
                if isinstance(v, dict):
                    serialize_inplace(v)
                    tree[k] = v
                elif isinstance(v, list):
                    new_list = []
                    for item in v:
                        if isinstance(item, dict):
                            serialize_inplace(item)
                            new_list.append(item)
                        elif isinstance(item, bytes):
                            new_list.append(str(item, "utf-8", errors="surrogateescape"))
                        else:
                            new_list.append(item)
                    tree[k] = new_list
                elif isinstance(v, bytes):
                    tree[k] = str(v, "utf-8", errors="surrogateescape")
                else:
                    tree[k] = v

        try:
            instance = SafeSaver.get_instance()
            new_data = data.copy()
            serialize_inplace(new_data)
            json_str = json.dumps(new_data, indent=instance._export_json_indent, ensure_ascii=False)
            SafeSaver.save_bytes(
                json_str.encode(instance._export_encoding, errors="surrogateescape"),
                destdir,
                name,
                ".json",
                on_queued,
                on_saved,
            )
        except Exception as e:
            Logger.warn(f"SafeSaver: Failed to save data as JSON: {e}")

    @staticmethod
    def save_objects(
        lst: Sequence[uc.Object],
        destdir: str,
        on_queued: Optional[Callable] = None,
        on_saved: Optional[Callable] = None,
    ):
        """Saves all the Unity objects in the given list as files.
        If a object is not exportable, it does nothing.

        :param lst: The objects list;
        :param destdir: Destination directory;
        :param on_queued: Callback `f()` invoked when the file was queued, `None` for ignore;
        :param on_saved: Callback `f(file_path_or_none_for_not_saved)`, `None` for ignore;
        :rtype: None;
        """
        for i in lst:
            SafeSaver.save_object(i, destdir, getattr(i, "m_Name", "Unknown"), on_queued, on_saved)

    @staticmethod
    def _save_async(data: bytes, destdir: str, name: str, ext: str, on_saved: Optional[Callable]):
        dest = SafeSaver._sanitize_dest(osp.join(destdir, name + ext))
        try:
            with CodeProfiler("saver_save"):
                # Lock on the sanitized canonical target so equivalent names serialize together.
                with EntryLock(dest):
                    if SafeSaver._is_unique(data, dest):
                        dest = SafeSaver._purify_name(dest)
                        os.makedirs(osp.dirname(dest), exist_ok=True)
                        with open(dest, "wb") as f:
                            f.write(data)
                        if on_saved:
                            on_saved(dest)
                            Logger.debug(f'Saver: Saved file "{dest}"')
                            return
        except Exception as arg:
            Logger.error(f'Saver: Failed to save file "{dest}" because: Exception{type(arg)} {arg}')
        # Invoke call back with `None` indicating the file was not saved
        if on_saved:
            on_saved(None)

    @staticmethod
    def _is_unique(data: bytes, dest: str):
        destdir = osp.dirname(dest)
        name, ext = osp.splitext(osp.basename(dest))
        if not osp.isdir(destdir):
            return True
        for entry in os.scandir(destdir):
            if not entry.is_file():
                continue
            entry_name, entry_ext = osp.splitext(entry.name)
            if not entry_name.startswith(name) or entry_ext != ext:
                continue
            with open(entry.path, "rb") as f:
                if f.read() == data:
                    Logger.debug(f'Saver: File "{entry.name}" duplication was prevented, size {len(data)}')
                    return False
        return True

    @staticmethod
    def _sanitize_dest(dest: str):
        destdir = osp.dirname(dest)
        name, ext = osp.splitext(osp.basename(dest))
        new_name = re.sub(r"[\\/:*?\"<>|\x00-\x1F]", "#", name)
        if new_name != name:
            Logger.debug(f'Saver: File name "{name}" was modified to "{new_name}" to prevent invalid characters')
            name = new_name
        return osp.join(destdir, name + ext)

    @staticmethod
    def _purify_name(dest: str):
        dest = SafeSaver._sanitize_dest(dest)
        destdir = osp.dirname(dest)
        name, ext = osp.splitext(osp.basename(dest))
        tmp = 0
        while osp.isfile(dest):
            dest = osp.join(destdir, f"{name}${tmp}{ext}")
            tmp += 1
        return dest

    # EndClass
