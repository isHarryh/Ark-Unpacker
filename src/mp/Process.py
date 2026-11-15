# Copyright (c) 2022-2026, Harry Huang
# @ BSD 3-Clause License
from typing import Protocol


class ProcessLike(Protocol):
    def is_alive(self) -> bool: ...

    def start(self) -> None: ...

    def join(self, timeout: float | None = None) -> None: ...

    def terminate(self) -> None: ...


class ProcessUtils:
    @staticmethod
    def start_all(*processes: ProcessLike):
        for process in processes:
            process.start()

    @staticmethod
    def join_all(*processes: ProcessLike, timeout: float | None = None):
        for process in processes:
            process.join(timeout=timeout)

    @staticmethod
    def terminate_all(*processes: ProcessLike, timeout: float = 5.0):
        for process in processes:
            if process.is_alive():
                process.terminate()
        ProcessUtils.join_all(*processes, timeout=timeout)
