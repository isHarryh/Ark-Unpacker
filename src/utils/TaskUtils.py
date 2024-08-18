# -*- coding: utf-8 -*-
# Copyright (c) 2022-2024, Harry Huang
# @ BSD 3-Clause License
import time
import queue
import threading

from .GlobalMethods import color, print, clear
from .Logger import Logger


class ThreadCtrl():
    """Controller for Multi Threading."""

    def __init__(self, max_subthread):
        """Initializes a tool for multi threading."""
        self.__sts:"list[threading.Thread]" = []
        self.set_max_subthread(max_subthread)

    def set_max_subthread(self, max_subthread:int):
        """Sets the max number of sub threads."""
        self.__max:int = max(1, max_subthread)

    def count_subthread(self):
        """Gets the number of alive sub threads."""
        self.__sts = list(filter(lambda x:x.is_alive(), self.__sts))
        return len(self.__sts)

    def run_subthread(self, fun, args:tuple=None, kwargs:dict=None, name:"str|None"=None):
        """Creates a sub thread and run it."""
        while self.count_subthread() >= self.__max:
            pass
        ts = threading.Thread(target=fun,
                              args=args if args else (),
                              kwargs=kwargs if kwargs else {},
                              daemon=True,
                              name=name)
        self.__sts.append(ts)
        ts.start()
    #EndClass

class WorkerCtrl():
    """Controller for Permanent Worker Threads."""
    LAYOFF_INTERVAL = 5
    BACKUP_THRESHOLD = 5

    def __init__(self, handler:staticmethod, max_workers:int=1, name:str=""):
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

class TimeRecorder():
    """Tasking Time Recorder."""

    def __init__(self):
        """Initializes a Tasking Time Recorder.
        """
        self.t_init = time.time()
        self.done = {}
        self.dest = {}
        self._lock = threading.Lock()
        self._cache_p = -1.0

    def update_dest(self, weight:int, advance:int=1):
        """Updates the destination value of the specified task weight.

        :param weight: The task weight whose destination value should be updated;
        :param count: The advance value;
        :rtype: None;
        """
        if weight <= 0:
            raise ValueError("Arg weight should be positive")
        with self._lock:
            self.dest[weight] = self.dest.get(weight, 0) + advance

    def done_once(self, weight:int):
        """Updates the current value of the specified task wight by `1`.

        :param weight: The task weight whose current value should be updated;
        :rtype: None;
        """
        with self._lock:
            if weight in self.done:
                self.done[weight].append(time.time())
            else:
                self.done[weight] = [time.time()]

    def get_dest_of(self, weight:int):
        """Gets the destination value of the specified task weight.

        :param weight: The task weight whose destination value should be returned;
        :returns: The destination value;
        :rtype: int;
        """
        return self.dest[weight] if weight in self.dest else 0

    def get_done_of(self, weight:int):
        """Gets the current value of the specified task weight.

        :param weight: The task weight whose current value should be returned;
        :returns: The current value;
        :rtype: int;
        """
        return len(self.done[weight]) if weight in self.done else 0

    def get_done_dest_str_of(self, weight:int):
        """Gets a string representing the done and destination of the specified task weight.

        :param weight: The task weight to inspect;
        :returns: A string that can be printed to CLI;
        :rtype: str;
        """
        return f"{self.get_done_of(weight)}/{self.get_dest_of(weight)}"

    def get_progress(self, force_inc:bool=True):
        """Gets the current progress.

        :param force_inc: Whether prevent the progress to decrease;
        :returns: The progress in `[0.0, 1.0]`;
        :rtype: float;
        """
        p = self._get_total_done_weight() / self._get_total_dest_weight() if self._get_total_dest_weight() else 1.0
        p = self._cache_p if p < self._cache_p and force_inc else p
        self._cache_p = p
        return p

    def get_progress_str(self, force_inc:bool=True, length:int=25):
        """Gets a string representing the current progress.

        :param force_inc: Whether prevent the progress to decrease;
        :param length: The length of the progress bar;
        :returns: A progress bar string that can be printed to CLI;
        :rtype: str;
        """
        p = self.get_progress(force_inc)
        return f"[{TimeRecorder._get_progress_bar_str(p, length)}] {color(2, 0, 1)}{p:.1%}"

    def get_speed(self, basis:int=500):
        """Gets the processing speed.

        :param basis: The max records used to calculate the speed;
        :returns: Weight per second;
        :rtype: float;
        """
        items = []
        for k, v in self.done.items():
            length = min(len(v), basis)
            if length <= 2:
                continue
            for i in range(length):
                items.append((k, v[-i - 1]))
        length = min(len(items), basis)
        if length <= 2:
            return 0
        items.sort(key=lambda x:x[1])
        sum_weight = sum([x[0] for x in items[:length]])
        delta_time = items[-1][1] - items[-length][1]
        return sum_weight / delta_time if delta_time != 0 else 0

    def get_eta(self, basis:int=500):
        """Gets the estimated time of arrival.

        :param basis: How many records do we use to calculate the speed;
        :returns: Remaining time in seconds;
        :rtype: float;
        """
        speed = self.get_speed(basis)
        return (self._get_total_dest_weight() - self._get_total_done_weight()) / speed if speed else 0

    def get_eta_str(self, basis:int=500):
        """Gets a string representing the estimated time of arrival.

        :param basis: How many records do we use to calculate the speed;
        :returns: A human-readable string;
        :rtype: str;
        """
        eta = self.get_eta(basis)
        h = int(eta / 3600)
        m = int(eta % 3600 / 60)
        s = int(eta % 60)
        if h != 0:
            return f'{h}:{m:02}:{s:02}'
        if eta != 0:
            return f'{m:02}:{s:02}'
        return '--:--'

    def get_rt(self):
        """Gets the running time since this instance was initialized.

        :returns: Time in seconds;
        :rtype: float;
        """
        return time.time() - self.t_init

    def _get_total_dest_weight(self):
        s = 0
        for k, v in self.dest.items():
            s += k * v
        return s

    def _get_total_done_weight(self):
        s = 0
        for k, v in self.done.items():
            s += k * len(v)
        return s

    @staticmethod
    def _get_progress_bar_str(progress:float, length:int):
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
