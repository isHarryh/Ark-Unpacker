# -*- coding: utf-8 -*-
# Copyright (c) 2022-2025, Harry Huang
# @ BSD 3-Clause License
from __future__ import annotations
from typing import Dict, List

import threading
import time
from collections import defaultdict
from contextlib import ContextDecorator


class CodeProfiler(ContextDecorator):
    """Utility class for profiling the time consumption of running a specified code block.
    Usage is shown below.

    ```
    with CodeProfiler('scope'):
        pass  # The code block to test
    print(CodeProfiler.get_avg_time('scope'))
    ```
    """

    _records: Dict[str, List[float]] = defaultdict(list)
    _internal_lock = threading.Lock()

    def __init__(self, name: str):
        self._name = name
        self._start_time = None

    def __enter__(self):
        self._start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._start_time:
            with CodeProfiler._internal_lock:
                while len(CodeProfiler._records[self._name]) >= 65536:
                    CodeProfiler._records[self._name].pop(0)
                CodeProfiler._records[self._name].append(
                    time.perf_counter() - self._start_time
                )
        return False  # Hand down the exception

    @staticmethod
    def get_avg_time(name: str):
        times = CodeProfiler._records.get(name, None)
        return sum(times) / len(times) if times else None

    @staticmethod
    def get_avg_time_all():
        return {k: CodeProfiler.get_avg_time(k) for k in CodeProfiler._records}

    @staticmethod
    def get_total_time(name: str):
        times = CodeProfiler._records.get(name, None)
        return sum(times) if times else None

    @staticmethod
    def get_total_time_all():
        return {k: CodeProfiler.get_total_time(k) for k in CodeProfiler._records}
