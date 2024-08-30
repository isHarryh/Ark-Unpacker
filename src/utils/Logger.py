# -*- coding: utf-8 -*-
# Copyright (c) 2022-2024, Harry Huang
# @ BSD 3-Clause License
import threading
from datetime import datetime


class Logger():
    """Logger class for ArkUnpacker"""

    __time_format   = '%Y-%m-%d %H:%M:%S'
    __file_encoding = 'UTF-8'
    __instance      = None
    LV_NONE     = 0
    LV_ERROR    = 1
    LV_WARN     = 2
    LV_INFO     = 3
    LV_DEBUG    = 4

    def __init__(self, log_file_path:str, level:int):
        """Not recommended to use. Please use the singleton instance."""
        self.log_level = level
        self.log_file_path = log_file_path
        self.internal_lock = threading.Condition()
        self.file = None
        self.queue = []
        def loop(self:Logger):
            while True:
                try:
                    with self.internal_lock:
                        while not self.queue:
                            self.internal_lock.wait()
                        t = self.queue.pop(0)
                        if isinstance(self.log_file_path, str) and len(self.log_file_path) > 0:
                            with open(self.log_file_path, 'a', encoding=Logger.__file_encoding) as f:
                                f.write(t)
                except BaseException:
                    pass
        self.thread = threading.Thread(name=self.__class__.__name__, target=loop, args=(self,), daemon=True)
        self.thread.start()

    def _set_level(self, level:int):
        self.log_level = level

    def _log(self, tag:str, msg:str):
        try:
            with self.internal_lock:
                self.queue.append(f"{datetime.now().strftime(Logger.__time_format)} [{tag}] {msg}\n")
                self.internal_lock.notify_all()
        except BaseException:
            pass

    def _error(self, msg:str):
        if self.log_level >= Logger.LV_ERROR:
            self._log('ERROR', msg)

    def _warn(self, msg:str):
        if self.log_level >= Logger.LV_WARN:
            self._log('WARN', msg)

    def _info(self, msg:str):
        if self.log_level >= Logger.LV_INFO:
            self._log('INFO', msg)

    def _debug(self, msg:str):
        if self.log_level >= Logger.LV_DEBUG:
            self._log('DEBUG', msg)

    @staticmethod
    def set_instance(log_file_path:str, level:int=LV_INFO):
        """Initializes the Logger static instance.
        If the instance has been initialized yet, this method does nothing.

        :param log_file_path: The path to the log file;
        :param level: The logging level;
        :rtype: None;
        """
        if not Logger.__instance:
            Logger.set_instance_override(log_file_path, level)

    @staticmethod
    def set_instance_override(log_file_path:str, level:int=LV_INFO):
        """Initializes the Logger static instance forcibly.
        If the instance has been initialized yet, this method will override it.

        :param log_file_path: The path to the log file;
        :param level: The logging level;
        :rtype: None;
        """
        Logger.__instance = Logger(log_file_path, level)

    @staticmethod
    def set_level(level:int):
        """Sets the logging level

        :param level: The new logging level;
        :rtype: None;
        """
        if Logger.__instance:
            Logger.__instance._set_level(level)

    @staticmethod
    def log(tag:str, msg:str):
        if Logger.__instance:
            Logger.__instance._log(tag, msg)

    @staticmethod
    def error(msg:str):
        if Logger.__instance:
            Logger.__instance._error(msg)

    @staticmethod
    def warn(msg:str):
        if Logger.__instance:
            Logger.__instance._warn(msg)

    @staticmethod
    def info(msg:str):
        if Logger.__instance:
            Logger.__instance._info(msg)

    @staticmethod
    def debug(msg:str):
        if Logger.__instance:
            Logger.__instance._debug(msg)
