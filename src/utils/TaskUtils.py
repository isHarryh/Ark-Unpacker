# -*- coding: utf-8 -*-
# Copyright (c) 2022-2025, Harry Huang
# @ BSD 3-Clause License
from typing import Callable, Optional, Set, Union

import asyncio
import psutil
import queue
import threading
import time

from .Config import PerformanceLevel, Config
from .GlobalMethods import color, print, clear
from .Logger import Logger


class ThreadCtrl:
    """Controller for Multi Threading."""

    def __init__(self, max_subthread: Optional[int] = None):
        """Initializes a tool for multi threading."""
        self.__sts: "list[threading.Thread]" = []
        if not max_subthread:
            max_subthread = PerformanceLevel.get_thread_limit(
                Config.get("performance_level")
            )
        self.set_max_subthread(max_subthread)

    def set_max_subthread(self, max_subthread: int):
        """Sets the max number of sub threads."""
        self.__max: int = max(1, max_subthread)

    def count_subthread(self):
        """Gets the number of alive sub threads."""
        self.__sts = list(filter(lambda x: x.is_alive(), self.__sts))
        return len(self.__sts)

    def run_subthread(
        self,
        fun,
        args: Optional[tuple] = None,
        kwargs: Optional[dict] = None,
        name: Optional[str] = None,
    ):
        """Creates a sub thread and run it."""
        while self.count_subthread() >= self.__max:
            pass
        ts = threading.Thread(
            target=fun,
            args=args if args is not None else (),
            kwargs=kwargs if kwargs is not None else {},
            daemon=True,
            name=name,
        )
        self.__sts.append(ts)
        ts.start()

    # EndClass


class CoroutineCtrl:
    """Controller for Coroutine-based Task Processing."""

    def __init__(
        self,
        handler: Callable,
        name: str = "",
        max_concurrency: Optional[int] = None,
        min_spare_memory_mb: Optional[int] = None,
    ):
        """Initializes a Coroutine Controller.

        :param handler: The handler function of the tasks;
        :param name: The optional name for the controller;
        :param max_concurrency: The maximum number of concurrent tasks;
        :param min_spare_memory_mb: The minimum spare system memory in MB to allow new tasks;
        """
        self.__handler = handler
        self.__opened = True
        self._name = name
        self._total_requested = Counter()
        self._total_processed = Counter()
        self.__thread = None
        self.__loop: Optional[asyncio.AbstractEventLoop] = None
        self.__queue: Optional[asyncio.Queue] = None
        self.__semaphore: Optional[asyncio.Semaphore] = None

        if max_concurrency is None:
            max_concurrency = PerformanceLevel.get_thread_limit(
                Config.get("performance_level")
            )
        if not isinstance(max_concurrency, int) or max_concurrency < 1:
            raise ValueError("max_concurrency must be an integer that not less than 1")
        self.__max_concurrency = max_concurrency

        if min_spare_memory_mb is None:
            min_spare_memory_mb = Config.get("min_spare_memory_mb")
        if not isinstance(min_spare_memory_mb, (int, float)) or min_spare_memory_mb < 0:
            raise ValueError("min_spare_memory_mb must be a positive number")
        self.__min_spare_memory_mb = min_spare_memory_mb

        self._start()

    def submit(self, data: tuple):
        """Submits new data to the controller.
        If system memory is low, it will block until enough memory is available.

        :param data: A tuple that contains the arguments that the handler required;
        :rtype: None;
        """
        if not self.__opened:
            raise RuntimeError("The coroutine controller has terminated")
        if not self.__loop or not self.__queue:
            raise RuntimeError("The coroutine controller is not ready")

        # Check memory condition if queue has tasks
        mb = self._get_spare_memory_mb()
        while mb < self.__min_spare_memory_mb and not self.__queue.empty():
            for _ in range(100):
                time.sleep(0)
            mb = self._get_spare_memory_mb()

        # Schedule the task in the event loop
        asyncio.run_coroutine_threadsafe(self.__queue.put(data), self.__loop)
        self._total_requested.update()

    def terminate(self):
        """Requests the controller to terminate.

        :rtype: None;
        """
        self.__opened = False

    def completed(self):
        """Returns `True` if there is no data in queue or in handler.

        :rtype: bool;
        """
        return self._total_requested.now() == self._total_processed.now()

    def get_total_requested(self):
        """Gets the total number of requested tasks.

        :rtype: int;
        """
        return self._total_requested.now()

    def get_total_processed(self):
        """Gets the total number of processed tasks.

        :rtype: int;
        """
        return self._total_processed.now()

    def reset_counter(self):
        """Resets the counter of requested tasks and processed tasks.

        :rtype: None;
        """
        if self.completed():
            self._total_requested = Counter()
            self._total_processed = Counter()
        else:
            raise RuntimeError("Cannot reset counter while the controller is busy")

    def _get_spare_memory_mb(self) -> float:
        """Gets the available system memory in MB.

        :returns: Available memory in MB, `inf` if not available;
        """
        try:
            memory_info = psutil.virtual_memory()
            return memory_info.available / 1024 / 1024
        except Exception:
            return float("inf")

    def _start(self):
        """Starts the event loop in a separate thread."""
        loop_ready = threading.Event()

        def thread_function():
            # Initialize the event loop in this thread
            self.__loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.__loop)

            # Initialize async objects within the event loop
            self.__queue = asyncio.Queue()
            self.__semaphore = asyncio.Semaphore(self.__max_concurrency)
            loop_ready.set()

            # Start the processing loop
            self.__loop.run_until_complete(self._loop())

        self.__thread = threading.Thread(
            target=thread_function, name=f"CoroutineCtrl:{self._name}", daemon=True
        )
        self.__thread.start()
        loop_ready.wait()

    async def _loop(self):
        """Main processing loop that handles tasks from the queue."""
        if not self.__queue:
            raise RuntimeError("Queue not initialized")

        async def task_function(data: tuple):
            """Handles a single task with semaphore control."""
            if not self.__semaphore:
                raise RuntimeError("Semaphore not initialized")

            async with self.__semaphore:
                try:
                    # Check if handler is async
                    if asyncio.iscoroutinefunction(self.__handler):
                        await self.__handler(*data)
                    else:
                        # Run sync handler in thread pool
                        loop = asyncio.get_event_loop()
                        await loop.run_in_executor(None, self.__handler, *data)
                except Exception as e:
                    Logger.error(
                        f"CoroutineCtrl: {self._name}: Error handling task: {e}"
                    )
                finally:
                    self._total_processed.update()

        Logger.debug(f"CoroutineCtrl: {self._name}: Loop started")

        running_tasks: Set[asyncio.Task] = set()

        while True:
            try:
                # Check if we should shutdown
                if not self.__opened and self.__queue.empty():
                    break

                # Clean up completed tasks
                if running_tasks:
                    running_tasks -= set(map(asyncio.Task.done, running_tasks))

                # Check if we have room for more tasks
                if len(running_tasks) < self.__max_concurrency:
                    # Try to get a new task
                    try:
                        data = await asyncio.wait_for(self.__queue.get(), timeout=0.1)
                        task = asyncio.create_task(task_function(data))
                        running_tasks.add(task)
                        self.__queue.task_done()
                    except asyncio.TimeoutError:
                        # No task available for now
                        continue
                else:
                    # Wait for at least one task to complete
                    if running_tasks:
                        _, pending = await asyncio.wait(
                            running_tasks,
                            return_when=asyncio.FIRST_COMPLETED,
                            timeout=0.1,
                        )
                        running_tasks = pending
                    else:
                        raise RuntimeError(
                            "No running tasks but max concurrency reached"
                        )

            except Exception as e:
                Logger.error(f"CoroutineCtrl: {self._name}: Error in loop: {e}")

        # Wait for all remaining tasks to complete after the shutdown request
        if running_tasks:
            await asyncio.gather(*running_tasks, return_exceptions=True)

        Logger.debug(f"CoroutineCtrl: {self._name}: Loop finished")

    # EndClass


class UICtrl:
    """UI Controller in the separated thread."""

    THREAD_NAME = "UIThread"

    def __init__(self, interval: float = 0.1):
        """Initializes a UI Controller.

        :param interval: Auto-refresh interval (seconds);
        """
        self.__lines = []
        self.__cache_lines = []
        self.__status = True
        self.set_refresh_rate(interval)

    def __loop(self):
        while self.__status:
            self.refresh(post_delay=self.__interval)

    def loop_start(self):
        """Starts auto-refresh."""
        self.__status = True
        self.__cache_lines = []
        threading.Thread(
            target=self.__loop, daemon=True, name=UICtrl.THREAD_NAME
        ).start()

    def loop_stop(self):
        """Stops auto-refresh."""
        self.__status = False
        self.__cache_lines = []

    def refresh(self, post_delay: float = 0, force_refresh: bool = False):
        """Requests a immediate refresh.

        :param post_delay: Set the post delay after this refresh (seconds);
        :param force_refresh: If `True`, do refresh regardless of whether the content has changed or not;
        :rtype: None;
        """
        if self.__lines != self.__cache_lines or force_refresh:
            try:
                self.__cache_lines = self.__lines[:]
                for i in range(len(self.__cache_lines)):
                    print(self.__cache_lines[i], y=i + 1)
            except IndexError:
                pass
        if post_delay > 0:
            time.sleep(post_delay)

    def request(self, lines: "list[str]"):
        """Updates the content

        :param lines: A list containing the content of each line;
        :rtype: None;
        """
        self.__lines = lines

    def reset(self):
        """Clears the content."""
        clear()
        self.__lines = []
        self.__cache_lines = []

    def set_refresh_rate(self, interval: float):
        """Sets the auto-refresh interval.

        :param interval: Auto-refresh interval (seconds);
        :rtype: None;
        """
        self.__interval = interval

    # EndClass


class Counter:
    """Cumulative Counter."""

    def __init__(self):
        """Initializes a cumulative counter."""
        self.__s = 0

    def update(self, val: Union[int, bool] = 1):
        """Updates the counter.

        :param val: Delta value in int or bool (`True` for 1 and `False` for 0);
        :returns: Current value;
        :rtype: int;
        """
        if isinstance(val, int):
            self.__s += val
        elif val is True:
            self.__s += 1
        return self.__s

    def now(self):
        """Gets the current value.

        :returns: Current value;
        :rtype: int;
        """
        return self.__s

    # EndClass


class TaskReporter:
    """Task reporter providing functions to record time consumptions of one kind of tasks."""

    def __init__(self, weight: int, demand: int = 0, window_size: int = 100):
        """Initializes a task reporter with a sliding window for time tracking.

        :param weight: The weight per task, higher weight indicating more time consumption;
        :param demand: The initial number of the tasks to be done;
        :param window_size: The size of the sliding window for speed calculation;
        """
        self._weight = weight
        self._demand = demand
        self._done = 0
        self._timestamps = queue.Queue(maxsize=window_size)
        self._internal_lock = threading.Lock()

    def report(self, success: bool = True):
        """Reports that one task has been successfully done (or failed).

        :param success: `True` to let `done += 1`, `False` to let `demand -= 1`;
        :rtype: None;
        """
        with self._internal_lock:
            if success:
                self._done += 1
                if self._timestamps.full():
                    # Remove the oldest timestamp if the queue is full
                    self._timestamps.get()
                # Record the current completion timestamp
                self._timestamps.put(time.time())
            else:
                # Task failed, decrease the demand
                self._demand -= 1

    def update_demand(self, delta: int = 1):
        """Updates the number of the tasks to be done by the given value."""
        with self._internal_lock:
            self._demand += delta

    def get_demand(self):
        """Gets the number of the tasks to be done."""
        return self._demand

    def get_done(self):
        """Gets the number of the tasks done."""
        return self._done

    def get_speed(self):
        """Calculates the average time per task based on the sliding window.

        :returns: The average speed (tasks per second), `0` if no enough data;
        :rtype: float;
        """
        if self._timestamps.qsize() < 2:
            return 0.0
        timestamps = list(self._timestamps.queue)
        delta_time = float(timestamps[-1] - timestamps[0])
        task_count = len(timestamps) - 1
        return task_count / delta_time if delta_time > 0 else 0.0

    def to_progress_str(self):
        """Returns a string representing the done and demand of the tasks.

        :returns: A human-readable string;
        :rtype: str;
        """
        return f"{self._done}/{self._demand}"

    # EndClass


class TaskReporterTracker:
    """Task reporter tracker providing functions to manage multiple task reporters."""

    def __init__(self, *reporters: TaskReporter):
        """Initializes a task reporter tracker with multiple task reporters.

        :param reporters: Some TaskReporter instances to be managed;
        """
        self._reporters = reporters
        self._start_at = time.time()
        self._cache_pg = -1.0

    def get_rt(self):
        """Gets the running time since this instance was initialized.

        :returns: Time (seconds);
        :rtype: None;
        """
        return time.time() - self._start_at

    def get_eta(self):
        """Calculates the total estimated time to complete all tasks across all reporters.

        :returns: The total remaining time (seconds), `0` if not available;
        :rtype: float;
        """
        eta = 0.0
        for reporter in self._reporters:
            s = reporter.get_speed()
            eta += (reporter._demand - reporter._done) / s if s > 0 else float("inf")
        return eta if eta != float("inf") else 0.0

    def get_progress(self, force_inc: bool = False):
        """Calculates the overall progress of tasks completed.

        :param force_inc: Whether prevent the progress to decrease;
        :returns: The overall progress in `[0.0, 1.0]`;
        :rtype: float;
        """
        done = sum(reporter._done * reporter._weight for reporter in self._reporters)
        demand = sum(
            reporter._demand * reporter._weight for reporter in self._reporters
        )
        pg = max(0.0, min(1.0, done / demand)) if demand > 0 else 1.0
        self._cache_pg = max(self._cache_pg, pg)
        return self._cache_pg if force_inc else pg

    def to_progress_bar_str(self, force_inc: bool = True, length: int = 25):
        """Gets a string representing the current progress.

        :param force_inc: Whether prevent the progress to decrease;
        :param length: The length of the progress bar;
        :returns: A progress bar string that can be printed to CLI;
        :rtype: str;
        """
        p = self.get_progress(force_inc)
        return f"[{TaskReporterTracker._format_progress_bar_str(p, length)}] {color(2, 1)}{p:.1%}"

    def to_rt_str(self):
        """Gets a string representing the running time since this instance was initialized.

        :returns: A human-readable string;
        :rtype: str;
        """
        return TaskReporterTracker._format_time_str(self.get_rt())

    def to_eta_str(self):
        """Gets a string representing the estimated time to complete all tasks.

        :returns: A human-readable string;
        :rtype: str;
        """
        return TaskReporterTracker._format_time_str(self.get_eta())

    @staticmethod
    def _format_time_str(seconds: float):
        h = int(seconds / 3600)
        m = int(seconds % 3600 / 60)
        s = int(seconds % 60)
        if h != 0:
            return f"{h}:{m:02}:{s:02}"
        if seconds != 0:
            return f"{m:02}:{s:02}"
        return "--:--"

    @staticmethod
    def _format_progress_bar_str(progress: float, length: int):
        try:
            add_chars = (" ", "▏", "▎", "▍", "▌", "▋", "▊", "▉", "█")
            max_idx = len(add_chars) - 1
            rst = ""
            unit = 1 / length
            for i in range(length):
                ratio = (progress - i * unit) / unit
                rst += add_chars[max(0, min(max_idx, round(ratio * max_idx)))]
            return rst
        except BaseException:
            return ""

    # EndClass
