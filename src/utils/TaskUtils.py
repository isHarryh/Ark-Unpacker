# -*- coding: utf-8 -*-
# Copyright (c) 2022-2024, Harry Huang
# @ BSD 3-Clause License
import time
import queue
import threading
from typing import Callable

from .Config import PerformanceLevel, Config
from .GlobalMethods import color, print, clear
from .Logger import Logger


class ThreadCtrl():
    """Controller for Multi Threading."""

    def __init__(self, max_subthread:"int|None"=None):
        """Initializes a tool for multi threading."""
        self.__sts:"list[threading.Thread]" = []
        if not max_subthread:
            max_subthread = PerformanceLevel.get_thread_limit(Config.get('performance_level'))
        self.set_max_subthread(max_subthread)

    def set_max_subthread(self, max_subthread:int):
        """Sets the max number of sub threads."""
        self.__max:int = max(1, max_subthread)

    def count_subthread(self):
        """Gets the number of alive sub threads."""
        self.__sts = list(filter(lambda x:x.is_alive(), self.__sts))
        return len(self.__sts)

    def run_subthread(self, fun, args:"tuple|None"=None, kwargs:"dict|None"=None, name:"str|None"=None):
        """Creates a sub thread and run it."""
        while self.count_subthread() >= self.__max:
            pass
        ts = threading.Thread(target=fun,
                              args=args if args is not None else (),
                              kwargs=kwargs if kwargs is not None else {},
                              daemon=True,
                              name=name)
        self.__sts.append(ts)
        ts.start()
    #EndClass

class WorkerCtrl():
    """Controller for Permanent Worker Threads."""
    LAYOFF_INTERVAL = 5
    BACKUP_THRESHOLD = 5

    def __init__(self, handler:Callable, max_workers:int=1, name:str=""):
        """Initializes a Worker Controller.

        :param handler: The handler function of the workers;
        :param max_workers: The maximum number of workers;
        :param name: The optional name for the workers;
        """
        if max_workers < 1:
            raise ValueError("max_workers should not be less than 1")
        self.__queue = queue.Queue()
        self.__handler = handler
        self.__opened = True
        self.__workers = []
        self.__idle_timestamp = time.time()
        self.__max_workers = max_workers
        self._name = name
        self._total_requested = Counter()
        self._total_processed = Counter()
        self._backup_worker()
        Logger.debug(f"Worker: Workers are ready to work for {name}!")

    def submit(self, data:tuple):
        """Submits new data to workers.

        :param data: A tuple that contains the arguments that the handler required;
        :rtype: None;
        """
        if self.__opened:
            self.__queue.put(data)
            self._total_requested.update()
        else:
            raise RuntimeError("The worker controller has terminated")

    def terminate(self, block:bool=False):
        """Requests the workers to terminate and stop receiving new data.

        :param block: Whether to wait for workers to complete.
        :rtype: None;
        """
        if self.__opened:
            self.__opened = False
            if block:
                self.__queue.join()

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
            raise RuntimeError("Cannot reset counter while the workers are busy")

    def _loop(self):
        while self.__opened or not self.__queue.empty():
            # Intelligent scheduling
            if self.__queue.empty():
                if self.__idle_timestamp <= 0:
                    self.__idle_timestamp = time.time()
                elif self.__idle_timestamp + WorkerCtrl.LAYOFF_INTERVAL < time.time():
                    cur_worker = threading.current_thread()
                    if cur_worker in self.__workers and self.__workers.index(cur_worker) != 0:
                        self._layoff_worker(cur_worker)
                        break
            else:
                self.__idle_timestamp = 0
                if self.__queue.qsize() > WorkerCtrl.BACKUP_THRESHOLD:
                    self._backup_worker()
            # Task receiving
            try:
                args = self.__queue.get(timeout=WorkerCtrl.LAYOFF_INTERVAL)
                try:
                    self.__handler(*args)
                finally:
                    self.__queue.task_done()
                    self._total_processed.update()
            except queue.Empty:
                pass

    def _backup_worker(self):
        if len(self.__workers) < self.__max_workers:
            t = threading.Thread(target=self._loop, name=f"Worker:{self._name}", daemon=True)
            self.__workers.append(t)
            t.start()
            if len(self.__workers) >= self.__max_workers:
                Logger.debug("Worker: Workers are in full load, slogging guts out!")

    def _layoff_worker(self, worker:threading.Thread):
        if worker in self.__workers:
            self.__workers.remove(worker)
            if len(self.__workers) <= 1:
                Logger.debug("Worker: Workers nodded off, sleeping for new tasks!")

class UICtrl():
    """UI Controller in the separated thread."""
    THREAD_NAME = 'UIThread'

    def __init__(self, interval:float=0.1):
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
        threading.Thread(target=self.__loop, daemon=True, name=UICtrl.THREAD_NAME).start()

    def loop_stop(self):
        """Stops auto-refresh."""
        self.__status = False
        self.__cache_lines = []

    def refresh(self, post_delay:float=0, force_refresh:bool=False):
        """Requests a immediate refresh.

        :param post_delay: Set the post delay after this refresh (seconds);
        :param force_refresh: If `True`, do refresh regardless of whether the content has changed or not;
        :rtype: None;
        """
        if self.__lines != self.__cache_lines or force_refresh:
            try:
                self.__cache_lines = self.__lines[:]
                for i in range(len(self.__cache_lines)):
                    print(self.__cache_lines[i], y=i+1)
            except IndexError:
                pass
        if post_delay > 0:
            time.sleep(post_delay)

    def request(self, lines:"list[str]"):
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

    def set_refresh_rate(self, interval:float):
        """Sets the auto-refresh interval.

        :param interval: Auto-refresh interval (seconds);
        :rtype: None;
        """
        self.__interval = interval
    #EndClass

class Counter():
    """Cumulative Counter."""

    def __init__(self):
        """Initializes a cumulative counter."""
        self.__s = 0

    def update(self, val:"int|bool"=1):
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
    #EndClass

class TaskReporter():
    """Task reporter providing functions to record time consumptions of one kind of tasks."""

    def __init__(self, weight:int, demand:int=0, window_size:int=100):
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

    def report(self, success:bool=True):
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

    def update_demand(self, delta:int=1):
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
    #EndClass

class TaskReporterTracker():
    """Task reporter tracker providing functions to manage multiple task reporters."""

    def __init__(self, *reporters:TaskReporter):
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
            eta += (reporter._demand - reporter._done) / s if s > 0 else float('inf')
        return eta if eta != float('inf') else 0.0

    def get_progress(self, force_inc:bool=False):
        """Calculates the overall progress of tasks completed.

        :param force_inc: Whether prevent the progress to decrease;
        :returns: The overall progress in `[0.0, 1.0]`;
        :rtype: float;
        """
        done = sum(reporter._done * reporter._weight for reporter in self._reporters)
        demand = sum(reporter._demand * reporter._weight for reporter in self._reporters)
        pg = max(0.0, min(1.0, done / demand)) if demand > 0 else 1.0
        self._cache_pg = max(self._cache_pg, pg)
        return self._cache_pg if force_inc else pg

    def to_progress_bar_str(self, force_inc:bool=True, length:int=25):
        """Gets a string representing the current progress.

        :param force_inc: Whether prevent the progress to decrease;
        :param length: The length of the progress bar;
        :returns: A progress bar string that can be printed to CLI;
        :rtype: str;
        """
        p = self.get_progress(force_inc)
        return f"[{TaskReporterTracker._format_progress_bar_str(p, length)}] {color(2, 0, 1)}{p:.1%}"

    def to_eta_str(self):
        """Gets a string representing the estimated time to complete all tasks.

        :returns: A human-readable string;
        :rtype: str;
        """
        eta = self.get_eta()
        h = int(eta / 3600)
        m = int(eta % 3600 / 60)
        s = int(eta % 60)
        if h != 0:
            return f'{h}:{m:02}:{s:02}'
        if eta != 0:
            return f'{m:02}:{s:02}'
        return '--:--'

    @staticmethod
    def _format_progress_bar_str(progress:float, length:int):
        try:
            add_chars = (' ', '▏', '▎', '▍', '▌', '▋', '▊', '▉', '█')
            max_idx = len(add_chars) - 1
            rst = ''
            unit = 1 / length
            for i in range(length):
                ratio = (progress - i * unit) / unit
                rst += add_chars[max(0, min(max_idx, round(ratio * max_idx)))]
            return rst
        except BaseException:
            return ''
    #EndClass
