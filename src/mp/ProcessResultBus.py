# Copyright (c) 2022-2026, Harry Huang
# @ BSD 3-Clause License
import multiprocessing as mp
import queue
from typing import Callable, Optional
from .ProcessReporter import (
    RESULT_FILE_QUEUED,
    RESULT_FILE_SAVED,
    RESULT_FS_GUARD_DONE,
    RESULT_LOG,
    RESULT_PROCESSED,
    RESULT_WORKER_DONE,
)
from .ProcessReporter import ProcessReporter


class _ProcessResultReceiver:
    def __init__(self, result_queue: mp.Queue):
        self._queue = result_queue
        self._on_file_queued: Optional[Callable[[int], None]] = None
        self._on_file_saved: Optional[Callable[[bool], None]] = None
        self._on_log: Optional[Callable[[str, str], None]] = None
        self._on_processed: Optional[Callable[[bool], None]] = None
        self._on_worker_done: Optional[Callable[[int], None]] = None
        self._on_fs_guard_done: Optional[Callable[[int], None]] = None
        self._handlers = {
            RESULT_FILE_QUEUED: self._handle_file_queued,
            RESULT_FILE_SAVED: self._handle_file_saved,
            RESULT_LOG: self._handle_log,
            RESULT_PROCESSED: self._handle_processed,
            RESULT_WORKER_DONE: self._handle_worker_done,
            RESULT_FS_GUARD_DONE: self._handle_fs_guard_done,
        }

    def drain(self, timeout: float = 0.0):
        while True:
            try:
                result = self._queue.get(timeout=timeout)
            except queue.Empty:
                return
            self._dispatch(result)
            timeout = 0.0

    def _dispatch(self, result):
        if not isinstance(result, tuple) or not result:
            return
        handler = self._handlers.get(result[0])
        if handler:
            handler(result[1:])

    def _handle_file_queued(self, payload: tuple):
        if self._on_file_queued:
            self._on_file_queued(payload[0])

    def _handle_file_saved(self, payload: tuple):
        if self._on_file_saved:
            self._on_file_saved(payload[0])

    def _handle_log(self, payload: tuple):
        if self._on_log:
            self._on_log(payload[0], payload[1])

    def _handle_processed(self, payload: tuple):
        if self._on_processed:
            self._on_processed(payload[0])

    def _handle_worker_done(self, payload: tuple):
        if self._on_worker_done:
            self._on_worker_done(payload[0])

    def _handle_fs_guard_done(self, payload: tuple):
        if self._on_fs_guard_done:
            self._on_fs_guard_done(payload[0])


class ProcessResultSender:
    def __init__(self, queue: mp.Queue):
        self._queue = queue

    def create_reporter(self) -> ProcessReporter:
        return ProcessReporter(self._queue)


class ProcessResultBus:
    def __init__(self, ctx):
        self._queue: mp.Queue = ctx.Queue()
        self._receiver = _ProcessResultReceiver(self._queue)
        self._sender = ProcessResultSender(self._queue)

    def create_sender(self) -> ProcessResultSender:
        return self._sender

    def set_on_file_queued(self, callback: Callable[[int], None]):
        self._receiver._on_file_queued = callback
        return self

    def set_on_file_saved(self, callback: Callable[[bool], None]):
        self._receiver._on_file_saved = callback
        return self

    def set_on_log(self, callback: Callable[[str, str], None]):
        self._receiver._on_log = callback
        return self

    def set_on_processed(self, callback: Callable[[bool], None]):
        self._receiver._on_processed = callback
        return self

    def set_on_worker_done(self, callback: Callable[[int], None]):
        self._receiver._on_worker_done = callback
        return self

    def set_on_fs_guard_done(self, callback: Callable[[int], None]):
        self._receiver._on_fs_guard_done = callback
        return self

    def drain(self, timeout: float = 0.0):
        self._receiver.drain(timeout)
