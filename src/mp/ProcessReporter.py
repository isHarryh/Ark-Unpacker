# Copyright (c) 2022-2026, Harry Huang
# @ BSD 3-Clause License
import multiprocessing as mp
import os
from typing import Optional

RESULT_FILE_QUEUED = 1
RESULT_FILE_SAVED = 2
RESULT_LOG = 3
RESULT_PROCESSED = 4
RESULT_WORKER_DONE = 5
RESULT_FS_GUARD_DONE = 6


class ProcessReporter:
    def __init__(self, queue: mp.Queue):
        self._queue = queue

    def emit(self, kind: int, *payload):
        self._queue.put((kind, *payload))

    def file_queued(self, count: int = 1):
        self.emit(RESULT_FILE_QUEUED, count)

    def file_saved(self, success: bool):
        self.emit(RESULT_FILE_SAVED, success)

    def log(self, level: str, msg: str):
        self.emit(RESULT_LOG, level, msg)

    def processed(self, success: bool = True):
        self.emit(RESULT_PROCESSED, success)

    def worker_done(self, pid: Optional[int] = None):
        self.emit(RESULT_WORKER_DONE, os.getpid() if pid is None else pid)

    def fs_guard_done(self, pid: Optional[int] = None):
        self.emit(RESULT_FS_GUARD_DONE, os.getpid() if pid is None else pid)
