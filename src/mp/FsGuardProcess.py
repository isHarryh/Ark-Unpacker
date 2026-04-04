# Copyright (c) 2022-2026, Harry Huang
# @ BSD 3-Clause License
import multiprocessing as mp
import os
import os.path as osp
from functools import lru_cache
from hashlib import blake2b
from multiprocessing.context import SpawnContext
from typing import NamedTuple, Optional

from .Messages import PrepareWriteRequest, PrepareWriteResponse, StopMessage
from .ProcessResultBus import ProcessResultSender
from .ProcessReporter import ProcessReporter


class _FamilyState(NamedTuple):
    hashes: set[bytes]
    used_paths: set[str]


class _DirEntry(NamedTuple):
    name: str
    path: str
    data_hash: Optional[bytes]


class _DirState(NamedTuple):
    files_by_ext: dict[str, list[_DirEntry]]


class FsGuardClient:
    def __init__(
        self,
        request_queue: mp.Queue,
        response_queue: mp.Queue,
        worker_slot: int,
        reporter: Optional[ProcessReporter] = None,
    ):
        self._request_queue = request_queue
        self._response_queue = response_queue
        self._worker_slot = worker_slot
        self._reporter = reporter
        self._request_id = 0

    def prepare_write(self, destdir: str, name: str, ext: str, data_hash: bytes) -> Optional[str]:
        if self._reporter:
            self._reporter.file_queued()
        response = self._request(
            PrepareWriteRequest(
                worker_slot=self._worker_slot,
                request_id=self._request_id,
                destdir=destdir,
                name=name,
                ext=ext,
                data_hash=data_hash,
            )
        )
        self._request_id += 1
        if not response.approved:
            return None
        return response.path

    def _request(self, request: PrepareWriteRequest) -> PrepareWriteResponse:
        self._request_queue.put(request)
        response = self._response_queue.get()
        if not isinstance(response, PrepareWriteResponse):
            raise RuntimeError(f"FsGuardClient: Unexpected response type {type(response).__name__}")
        if response.request_id != request.request_id:
            raise RuntimeError(
                f"FsGuardClient: Unexpected response request_id={response.request_id}, expected {request.request_id}"
            )
        return response


class FsGuardClientSlot:
    def __init__(self, request_queue: mp.Queue, response_queue: mp.Queue, worker_slot: int):
        self._request_queue = request_queue
        self._response_queue = response_queue
        self._worker_slot = worker_slot

    def create_client(self, reporter: Optional[ProcessReporter] = None) -> FsGuardClient:
        return FsGuardClient(
            self._request_queue,
            self._response_queue,
            self._worker_slot,
            reporter,
        )


class FsGuardProcess:
    def __init__(
        self,
        ctx: SpawnContext,
        result_sender: ProcessResultSender,
        worker_count: int,
        *,
        request_queue_maxsize: int = 0,
        response_queue_maxsize: int = 0,
        process_name: str = "FsGuard",
    ):
        self.request_queue: mp.Queue = ctx.Queue(maxsize=request_queue_maxsize)
        self.response_queues: list[mp.Queue] = [ctx.Queue(maxsize=response_queue_maxsize) for _ in range(worker_count)]
        self._process = ctx.Process(
            target=FsGuardProcess._bootstrap,
            args=(self.request_queue, self.response_queues, result_sender),
            name=process_name,
            daemon=True,
        )

    @staticmethod
    def _bootstrap(
        request_queue: mp.Queue,
        response_queues: list[mp.Queue],
        result_sender: ProcessResultSender,
    ):
        _FsGuardRuntime(response_queues, result_sender).run(request_queue)

    @property
    def exitcode(self):
        return self._process.exitcode

    @property
    def pid(self):
        return self._process.pid

    def is_alive(self) -> bool:
        return self._process.is_alive()

    def join(self, timeout: Optional[float] = None):
        self._process.join(timeout=timeout)

    def start(self):
        self._process.start()

    def create_client_slot(self, worker_slot: int) -> FsGuardClientSlot:
        return FsGuardClientSlot(
            self.request_queue,
            self.response_queues[worker_slot],
            worker_slot,
        )

    def stop(self):
        self.request_queue.put(StopMessage())

    def terminate(self):
        self._process.terminate()


class _FsGuardRuntime:
    def __init__(self, response_queues: list[mp.Queue], result_sender: ProcessResultSender):
        self._response_queues = response_queues
        self._reporter = result_sender.create_reporter()
        self._created_dirs: set[str] = set()

    def run(self, request_queue: mp.Queue):
        while True:
            request = request_queue.get()
            if isinstance(request, StopMessage):
                break

            try:
                if isinstance(request, PrepareWriteRequest):
                    self._prepare_write(request)
                else:
                    self._reporter.log("warn", f'FsGuard: Unknown request type "{type(request).__name__}"')
            except BaseException as arg:
                self._reporter.log(
                    "error",
                    f'FsGuard: Failed to handle request "{type(request).__name__}": Exception{type(arg)} {arg}',
                )
                if isinstance(request, PrepareWriteRequest):
                    self._respond(request.worker_slot, PrepareWriteResponse(request.request_id, False))

        self._reporter.fs_guard_done(os.getpid())

    def _respond(self, worker_slot: int, response: PrepareWriteResponse):
        self._response_queues[worker_slot].put(response)

    def _ensure_dir(self, path: str):
        norm_path = self._normalize_path(path)
        if norm_path in self._created_dirs:
            return
        os.makedirs(path, exist_ok=True)
        self._created_dirs.add(norm_path)

    def _prepare_write(self, request: PrepareWriteRequest):
        dest = self._sanitize_dest(osp.join(request.destdir, request.name + request.ext))
        destdir = osp.dirname(dest)
        norm_destdir = self._normalize_path(destdir)
        name, ext = osp.splitext(osp.basename(dest))
        state = self._get_family_state(norm_destdir, name, ext)

        if request.data_hash in state.hashes:
            self._respond(request.worker_slot, PrepareWriteResponse(request.request_id, False))
            return

        candidate = dest
        suffix = 0
        while self._normalize_path(candidate) in state.used_paths:
            candidate = osp.join(destdir, f"{name}${suffix}{ext}")
            suffix += 1

        self._ensure_dir(destdir)
        state.hashes.add(request.data_hash)
        normalized_candidate = self._normalize_path(candidate)
        state.used_paths.add(normalized_candidate)
        self._remember_file(
            norm_destdir,
            osp.splitext(osp.basename(candidate))[0],
            ext,
            normalized_candidate,
            request.data_hash,
        )
        self._respond(
            request.worker_slot,
            PrepareWriteResponse(
                request_id=request.request_id,
                approved=True,
                path=candidate,
            ),
        )

    @lru_cache(maxsize=1024)
    def _get_family_state(self, destdir: str, name: str, ext: str) -> _FamilyState:
        state = _FamilyState(set(), set())
        dir_state = self._get_dir_state(destdir)
        for entry in dir_state.files_by_ext.get(ext, []):
            if not entry.name.startswith(name):
                continue
            state.used_paths.add(entry.path)
            if entry.data_hash is not None:
                state.hashes.add(entry.data_hash)
        return state

    @lru_cache(maxsize=1024)
    def _get_dir_state(self, destdir: str) -> _DirState:
        state: dict[str, list[_DirEntry]] = {}
        if osp.isdir(destdir):
            for entry in os.scandir(destdir):
                if not entry.is_file():
                    continue
                entry_name, entry_ext = osp.splitext(entry.name)
                entry_path = self._normalize_path(entry.path)
                entry_hash: Optional[bytes] = None
                try:
                    entry_hash = self._hash_file(entry.path)
                except Exception as arg:
                    self._reporter.log(
                        "warn",
                        f'FsGuard: Failed to read existing file "{entry.path}" for de-duplication: {arg}',
                    )
                if entry_ext not in state:
                    state[entry_ext] = []
                state[entry_ext].append(_DirEntry(entry_name, entry_path, entry_hash))
        return _DirState(state)

    def _remember_file(
        self,
        destdir: str,
        name: str,
        ext: str,
        normalized_path: str,
        data_hash: bytes,
    ):
        dir_state = self._get_dir_state(destdir).files_by_ext
        if ext not in dir_state:
            dir_state[ext] = []
        dir_state[ext].append(_DirEntry(name, normalized_path, data_hash))

    def _hash_file(self, path: str) -> bytes:
        h = blake2b(digest_size=32)
        with open(path, "rb") as f:
            while True:
                chunk = f.read(1048576)  # 1 MB
                if not chunk:
                    break
                h.update(chunk)
        return h.digest()

    def _normalize_path(self, path: str) -> str:
        return osp.normcase(osp.normpath(path))

    def _sanitize_dest(self, dest: str) -> str:
        invalid = '\\/:*?"<>|' + "".join(chr(i) for i in range(0x20))
        destdir = osp.dirname(dest)
        name, ext = osp.splitext(osp.basename(dest))
        safe_name = "".join("#" if c in invalid else c for c in name)
        return osp.join(destdir, safe_name + ext)
