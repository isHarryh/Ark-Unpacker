# -*- coding: utf-8 -*-
# Copyright (c) 2022-2023, Harry Huang
# @ BSD 3-Clause License
from datetime import datetime
from threading import Thread

class Logger():
    '''
    Logger class for ArkUnpacker
    日志类
    '''

    __time_format   = '%Y-%m-%d %H:%M:%S'
    __file_encoding = 'UTF-8'
    __instance      = None
    LV_NONE     = 0
    LV_ERROR    = 1
    LV_WARN     = 2
    LV_INFO     = 3
    LV_DEBUG    = 4
    
    def __init__(self, log_file_path:str, level:int):
        '''
        ## Not recommended. Please use the static instance.
        #### 不推荐直接实例化，请使用日志静态实例
        '''
        self.log_level = level
        self.log_file_path = log_file_path
        self.file = None
        self.queue = []
        def loop(self:Logger):
            while True:
                try:
                    if len(self.queue):
                        t = self.queue.pop(0)
                        if type(self.log_file_path) == str and len(self.log_file_path) > 0:
                            with open(self.log_file_path, 'a', encoding=Logger.__file_encoding) as f:
                                f.write(t)
                except BaseException:
                    pass
        self.thread = Thread(name=self.__class__.__name__, target=loop, args=(self,), daemon=True)
        self.thread.start()
    
    def __set_level(self, level:int):
        self.log_level = level
    
    def __log(self, tag:str, msg:str):
        try:
            self.queue.append(f"{datetime.now().strftime(Logger.__time_format)} [{tag}] {msg}\n")
            return True
        except BaseException:
            return False
    
    def __error(self, msg:str):
        if self.log_level >= Logger.LV_ERROR: self.__log('ERROR', msg)
    
    def __warn(self, msg:str):
        if self.log_level >= Logger.LV_WARN: self.__log('WARN', msg)
    
    def __info(self, msg:str):
        if self.log_level >= Logger.LV_INFO: self.__log('INFO', msg)
    
    def __debug(self, msg:str):
        if self.log_level >= Logger.LV_DEBUG: self.__log('DEBUG', msg)
    
    @staticmethod
    def set_instance(log_file_path:str, level:int=LV_INFO):
        '''
        ## Initialize the Logger static instance
        #### 初始化日志静态实例
        Note: If the instance has been initialized yet, this method does nothing.
        :param log_gile_path: The path to the log file;
        :param level:         The logging level;
        :returns:             (none);
        '''
        if not Logger.__instance: Logger.set_instance_override(log_file_path, level)

    @staticmethod
    def set_instance_override(log_file_path:str, level:int=LV_INFO):
        '''
        ## Initialize the Logger static instance forcibly
        #### 强制初始化日志静态实例
        Note: If the instance has been initialized yet, this method will override it.
        :param log_gile_path: The path to the log file;
        :param level:         The logging level;
        :returns:             (none);
        '''
        Logger.__instance = Logger(log_file_path, level)
    
    @staticmethod
    def set_level(level:int):
        '''
        ## Set the logging level
        #### 设置日志等级
        :param level: The new logging level;
        :returns:     (none);
        '''
        if Logger.__instance: Logger.__instance.__set_level(level)
    
    @staticmethod
    def log(tag:str, msg:str):
        if Logger.__instance: Logger.__instance.__log(tag, msg)
    
    @staticmethod
    def error(msg:str):
        if Logger.__instance: Logger.__instance.__error(msg)
    
    @staticmethod
    def warn(msg:str):
        if Logger.__instance: Logger.__instance.__warn(msg)
    
    @staticmethod
    def info(msg:str):
        if Logger.__instance: Logger.__instance.__info(msg)
    
    @staticmethod
    def debug(msg:str):
        if Logger.__instance: Logger.__instance.__debug(msg)
