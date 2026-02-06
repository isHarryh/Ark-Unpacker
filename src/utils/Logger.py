# Copyright (c) 2022-2026, Harry Huang
# @ BSD 3-Clause License
import queue
import threading
from datetime import datetime

from .GlobalMethods import color


class Logger:
    """Logger class for ArkUnpacker"""

    __time_format = "%Y-%m-%d %H:%M:%S"
    __file_encoding = "UTF-8"
    __instance = None

    LV_NONE = 0
    LV_ERROR = 1
    LV_WARN = 2
    LV_INFO = 3
    LV_DEBUG = 4

    def __init__(self, log_file_path: str, level: int):
        """Not recommended to use. Please use the singleton instance."""
        self._log_level = level
        self._log_file_path = log_file_path
        self._file = None
        self._queue = queue.Queue()

        self._internal_lock = threading.Lock()
        self._level_stats = {}
        self._reset_stats()

        def loop(self: Logger):
            buffer = []
            while True:
                try:
                    while len(buffer) < 0x10:
                        try:
                            timeout = 1 / ((len(buffer) + 1) ** 2)
                            buffer.append(self._queue.get(timeout=timeout))
                        except queue.Empty:
                            break
                    if buffer and self._log_file_path:
                        with open(
                            self._log_file_path,
                            "a",
                            encoding=Logger.__file_encoding,
                        ) as f:
                            f.writelines(buffer)
                    buffer.clear()
                except BaseException:
                    pass

        self.thread = threading.Thread(name=self.__class__.__name__, target=loop, args=(self,), daemon=True)
        self.thread.start()

    def _set_level(self, level: int):
        if level is not None:
            self._log_level = level

    def _reset_stats(self):
        with self._internal_lock:
            self._level_stats = {
                Logger.LV_ERROR: 0,
                Logger.LV_WARN: 0,
                Logger.LV_INFO: 0,
                Logger.LV_DEBUG: 0,
            }

    def _log(self, tag: str, msg: str):
        try:
            self._queue.put(f"{datetime.now().strftime(Logger.__time_format)} [{tag}] {msg}\n")
        except BaseException:
            pass

    def _error(self, msg: str):
        if self._log_level >= Logger.LV_ERROR:
            with self._internal_lock:
                self._level_stats[Logger.LV_ERROR] += 1
            self._log("ERROR", msg)

    def _warn(self, msg: str):
        if self._log_level >= Logger.LV_WARN:
            with self._internal_lock:
                self._level_stats[Logger.LV_WARN] += 1
            self._log("WARN", msg)

    def _info(self, msg: str):
        if self._log_level >= Logger.LV_INFO:
            with self._internal_lock:
                self._level_stats[Logger.LV_INFO] += 1
            self._log("INFO", msg)

    def _debug(self, msg: str):
        if self._log_level >= Logger.LV_DEBUG:
            with self._internal_lock:
                self._level_stats[Logger.LV_DEBUG] += 1
            self._log("DEBUG", msg)

    @staticmethod
    def set_instance(log_file_path: str, level: int = LV_INFO):
        """Initializes the Logger static instance.
        If the instance has been initialized yet, this method does nothing.

        :param log_file_path: The path to the log file;
        :param level: The logging level;
        :rtype: None;
        """
        if not Logger.__instance:
            Logger.set_instance_override(log_file_path, level)

    @staticmethod
    def set_instance_override(log_file_path: str, level: int = LV_INFO):
        """Initializes the Logger static instance forcibly.
        If the instance has been initialized yet, this method will override it.

        :param log_file_path: The path to the log file;
        :param level: The logging level;
        :rtype: None;
        """
        Logger.__instance = Logger(log_file_path, level)

    @staticmethod
    def set_level(level: int):
        """Sets the logging level.

        :param level: The new logging level;
        :rtype: None;
        """
        if Logger.__instance:
            Logger.__instance._set_level(level)

    @staticmethod
    def reset_stats():
        """Resets the logging level stats.

        :rtype: None;
        """
        if Logger.__instance:
            Logger.__instance._reset_stats()

    @staticmethod
    def get_stats(key: int):
        """Returns the logging level stats of the specified level key.

        :param key: The logging level;
        :returns: The number of hit count;
        :rtype: int;
        """
        if Logger.__instance:
            return Logger.__instance._level_stats[key]
        return 0

    @staticmethod
    def to_ew_stats_str():
        """Returns the error-warning logging level stats string.

        :returns: A string that can be printed to CLI;
        :rtype: str;
        """
        errors = Logger.get_stats(Logger.LV_ERROR)
        warns = Logger.get_stats(Logger.LV_WARN)
        if errors + warns <= 0:
            return f"{color()}正常"
        rst = ""
        if errors > 0:
            rst += f"{color(1)}{errors}{color()} 个错误"
        if warns > 0:
            if rst:
                rst += "，"
            rst += f"{color(3)}{warns}{color()} 个警告"
        return rst

    @staticmethod
    def log(tag: str, msg: str):
        if Logger.__instance:
            Logger.__instance._log(tag, msg)

    @staticmethod
    def error(msg: str):
        if Logger.__instance:
            Logger.__instance._error(msg)

    @staticmethod
    def warn(msg: str):
        if Logger.__instance:
            Logger.__instance._warn(msg)

    @staticmethod
    def info(msg: str):
        if Logger.__instance:
            Logger.__instance._info(msg)

    @staticmethod
    def debug(msg: str):
        if Logger.__instance:
            Logger.__instance._debug(msg)
