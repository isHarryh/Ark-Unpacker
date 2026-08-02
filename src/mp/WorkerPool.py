# Copyright (c) 2022-2026, Harry Huang
# @ BSD 3-Clause License
from multiprocessing.context import SpawnContext
from typing import Any, Callable, Iterable, Optional

import multiprocessing as mp
import queue

from .FsGuardProcess import FsGuardProcess
from .Messages import StopMessage
from .Process import ProcessUtils
from .ProcessResultBus import ProcessResultBus, ProcessResultSender


class WorkerPool:
    """Runs a batch of tasks on a pool of worker processes guarded by an FsGuard process.

    The pool handles task distribution, progress draining, crash detection and
    process cleanup internally, so that callers only need to provide the tasks
    and the worker entry point.
    """

    def __init__(
        self,
        ctx: SpawnContext,
        worker_count: int,
        worker_target: Callable,
        worker_args_factory: Callable[[mp.Queue, FsGuardProcess, ProcessResultSender, int], tuple],
        process_name: str = "Worker",
    ):
        self._task_queue: mp.Queue = ctx.Queue(maxsize=worker_count)
        self._result_bus = ProcessResultBus(ctx)
        self._sender = self._result_bus.create_sender()
        self._fs_guard = FsGuardProcess(
            ctx,
            self._sender,
            worker_count,
            request_queue_maxsize=max(2, min(8, worker_count)),
        )
        self._workers = [
            ctx.Process(
                target=worker_target,
                args=worker_args_factory(self._task_queue, self._fs_guard, self._sender, idx),
                name=f"{process_name}:{idx}",
                daemon=True,
            )
            for idx in range(worker_count)
        ]
        self._worker_done: set[int] = set()
        self._fs_guard_done = False
        self._fs_guard_stop_sent = False
        self._fatal_error: Optional[str] = None
        self._on_error: Optional[Callable[[str], None]] = None
        self._on_tick: Optional[Callable[[], None]] = None

    def set_handlers(
        self,
        *,
        on_file_queued: Optional[Callable[[int], None]] = None,
        on_file_saved: Optional[Callable[[bool], None]] = None,
        on_processed: Optional[Callable[[bool], None]] = None,
        on_log: Optional[Callable[[str, str], None]] = None,
        on_error: Optional[Callable[[str], None]] = None,
        on_tick: Optional[Callable[[], None]] = None,
    ):
        self._on_error = on_error
        self._on_tick = on_tick
        for name, callback in {
            "file_queued": on_file_queued,
            "file_saved": on_file_saved,
            "processed": on_processed,
            "log": on_log,
        }.items():
            if callback is not None:
                getattr(self._result_bus, f"set_on_{name}")(callback)
        return self

    def dispatch(self, tasks: Iterable, on_dispatch: Optional[Callable[[Any], None]] = None):
        """Distributes the given tasks to the workers, then signals them to stop.

        Enqueueing never blocks indefinitely: if the bounded queue is full, the
        progress is drained and worker crashes are checked in short intervals,
        so the caller can keep rendering updates and early-exit on failures.
        """
        for task in tasks:
            if on_dispatch is not None:
                on_dispatch(task)
            if not self._enqueue(task):
                return
        self._send_stop()

    def __enter__(self):
        self._result_bus = (
            self._result_bus.set_on_worker_done(self._worker_done.add)
            .set_on_fs_guard_done(self._mark_fs_guard_done)
        )
        ProcessUtils.start_all(self._fs_guard, *self._workers)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None and self._fatal_error is None:
            self._wait_for_completion()
        if self._fatal_error:
            ProcessUtils.terminate_all(self._fs_guard, *self._workers)
            raise RuntimeError(self._fatal_error) from None
        if exc_type is not None:
            ProcessUtils.terminate_all(self._fs_guard, *self._workers)
            return False
        ProcessUtils.join_all(self._fs_guard, *self._workers)
        self._result_bus.drain(timeout=0.0)
        for worker in self._workers:
            if worker.exitcode not in (0, None):
                raise RuntimeError(f'Worker process "{worker.name}" exited with code {worker.exitcode}')
        if self._fs_guard.exitcode not in (0, None):
            raise RuntimeError(f"FsGuard process exited with code {self._fs_guard.exitcode}")
        return False

    def _enqueue(self, task) -> bool:
        """Puts a task into the queue, returns `False` if a fatal error occurred."""
        while True:
            try:
                self._task_queue.put(task, timeout=0.1)
            except queue.Full:
                self._result_bus.drain(timeout=0.0)
                if self._check_crashes():
                    return False
                continue
            if self._check_crashes():
                return False
            return True

    def _send_stop(self):
        for _ in self._workers:
            if not self._enqueue(StopMessage()):
                return

    def _wait_for_completion(self):
        while len(self._worker_done) < len(self._workers) or not self._fs_guard_done:
            self._result_bus.drain(timeout=0.1)
            self._check_crashes()
            if self._fatal_error:
                return
            if len(self._worker_done) == len(self._workers) and not self._fs_guard_stop_sent:
                self._fs_guard.stop()
                self._fs_guard_stop_sent = True
            if self._on_tick is not None:
                self._on_tick()
        self._result_bus.drain(timeout=0.0)

    def _check_crashes(self) -> bool:
        """Returns `True` if any worker or the FsGuard exited unexpectedly."""
        for worker in self._workers:
            if (
                worker.exitcode is not None
                and worker.pid is not None
                and worker.pid not in self._worker_done
            ):
                self._worker_done.add(worker.pid)
                if worker.exitcode != 0:
                    self._set_fatal(f'Worker process "{worker.name}" exited unexpectedly with code {worker.exitcode}')
        if self._fs_guard.exitcode is not None and not self._fs_guard_done:
            self._fs_guard_done = True
            if self._fs_guard.exitcode != 0:
                self._set_fatal(f"FsGuard process exited unexpectedly with code {self._fs_guard.exitcode}")
        return self._fatal_error is not None

    def _set_fatal(self, msg: str):
        self._fatal_error = msg
        if self._on_error is not None:
            self._on_error(msg)

    def _mark_fs_guard_done(self, _pid: int):
        self._fs_guard_done = True
