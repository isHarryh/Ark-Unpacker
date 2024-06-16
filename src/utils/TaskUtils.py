# -*- coding: utf-8 -*-
# Copyright (c) 2022-2024, Harry Huang
# @ BSD 3-Clause License
import time, queue
from threading import Thread
from .GlobalMethods import *


class ThreadCtrl():
    """Controller for Multi Threading."""

    def __init__(self, max_subthread):
        """Initializes a tool for multi threading."""
        self.__sts:list[Thread] = []
        self.set_max_subthread(max_subthread)
    
    def set_max_subthread(self, max_subthread:int):
        """Sets the max number of sub threads."""
        self.__max:int = max(1, max_subthread)
    
    def count_subthread(self):
        """Gets the number of alive sub threads."""
        self.__sts = list(filter(lambda x:x.is_alive(), self.__sts))
        return len(self.__sts)
    
    def run_subthread(self, fun, args:tuple=(), kwargs:dict={}, name:"str|None"=None):
        """Creates a sub thread and run it."""
        while self.count_subthread() >= self.__max:
            pass
        ts = Thread(target=fun, args=args, kwargs=kwargs, daemon=False, name=name)
        self.__sts.append(ts)
        ts.start()
    #EndClass

class WorkerCtrl():
    """Controller for Permanent Worker Threads."""

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
        self._total_requested = Counter()
        self._total_processed = Counter()
        for i in range(max_workers):
            t = Thread(target=self._loop, name=f"Worker:{name}#{i}")
            self.__workers.append(t)
            t.start()

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
            self.__opened == False
            if block:
                self.__queue.join()
    
    def completed(self):
        """Returns `True` if there is no data in queue or in handler.

        :rtype: bool;
        """
        return self._total_requested.now() == self._total_processed.now()
    
    def get_total_requested(self):
        return self._total_requested.now()
    
    def get_total_processed(self):
        return self._total_processed.now()

    def reset_counter(self):
        if self.completed():
            self._total_requested = Counter()
            self._total_processed = Counter()
        else:
            raise RuntimeError("Cannot reset counter while the workers are busy")

    def _loop(self):
        while self.__opened or not self.__queue.empty():
            args = self.__queue.get()
            try:
                self.__handler(*args)
            finally:
                self.__queue.task_done()
                self._total_processed.update()

class UICtrl():
    """UI Controller in the separated thread."""
    THREAD_NAME = 'UIThread'

    def __init__(self, interval:float):
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
        Thread(target=self.__loop, daemon=False, name=UICtrl.THREAD_NAME).start()

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
        os.system('cls')
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
        if type(val) == int:
            self.__s += val
        elif val:
            self.__s += 1
        return self.__s
    
    def now(self):
        """Gets the current value.

        :returns: Current value;
        :rtype: int;"""
        return self.__s
    #EndClass

class TimeRecorder():
    """Tasking Time Recorder."""

    def __init__(self, dest:int):
        """Initializes a Tasking Time Recorder.

        :param dest: The destination value of the task;
        """
        self.t_init = time.time()
        self.t_rec = [[self.t_init, 0]] #[curTime,Time(Seconds)OfEach]
        self.n_dest = dest
        self.n_cur = 0

    def update(self):
        """Updates the current value of the task."""
        self.n_cur += 1
        t_cur = time.time()
        self.t_rec.append([t_cur, t_cur-self.t_rec[len(self.t_rec)-1][0]])
    
    def get_progress(self):
        """Gets the current progress.

        :returns: The progress in `[0.0, 1.0]`;
        :rtype: float;
        """
        return self.n_cur / self.n_dest
    
    def get_speed(self, basis:int=100):
        """Gets the processing speed.

        :param basis: How many records do we use to calculate the speed;
        :returns: Items per second;
        :rtype: float;
        """
        sum = []
        for i in range(len(self.t_rec)-1, -1, -1):
            if i+basis < self.n_cur:
                break
            if self.t_rec[i][1]:
                sum.append(self.t_rec[i][1])
        rst = trimmean(sum, 0.05)
        return 1 / rst if rst != 0 else 0
    
    def get_remaining_time(self, basis:int=100):
        """Gets the time remaining.

        :param basis: How many records do we use to calculate the speed;
        :returns: Time in seconds;
        :rtype: float;
        """
        return (self.n_dest-self.n_cur) / self.get_speed(basis) if self.get_speed(basis) != 0 else 0
    
    def get_consumed_time(self):
        """Gets the used time from the first record to now.

        :returns: Time in seconds;
        :rtype: float;
        """
        return time.time() - self.t_rec[0][0]
    #EndClass

class LineSpinner():
    """Line Spinner for loading operations."""

    char = ('/', '-', '\\', '|')

    def __init__(self):
        self.__n = 0

    def next(self):
        self.__n = 0 if self.__n >= len(self.char)-1 else self.__n+1
        return self.char[self.__n]
    #EndClass
