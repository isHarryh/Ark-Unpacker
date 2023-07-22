# -*- coding: utf-8 -*-
# Copyright (c) 2022-2023, Harry Huang
# @ BSD 3-Clause License
import time
from threading import Thread
from .GlobalMethods import *

class ThreadCtrl():
    '''
    Controller for Multi Threading
    多线程任务控制器
    '''

    def __init__(self, max_subthread):
        '''
        ## Initialize a tool for multi threading.
        #### 初始化一个多线程控制器
        :param max_subthread: The max number of sub threads;
        :returns: (none);
        '''
        self.__sts:list[Thread] = []
        self.set_max_subthread(max_subthread)
    
    def set_max_subthread(self, max_subthread:int):
        '''
        ## Set the max number of sub threads.
        #### 设置最大子线程数
        :param max_subthread: The max number of sub threads;
        :returns: (none);
        '''
        self.__max:int = max(1, max_subthread)
    
    def get_max_sub_thread(self):
        '''
        ## Set the max number of sub threads.
        #### 获取最大子线程数
        :returns: (int);
        '''
        return self.__max
    
    def get_idle_ratio(self, ndigits:int=3):
        '''
        ## Get the idle ratio
        #### 获取空闲率
        :param ndigits: Decimal Digits;
        :returns: (float);
        '''
        return self.count_subthread() - self.get_max_sub_thread()
    
    def count_subthread(self):
        '''
        ## Get the number of alive sub threads.
        #### 获取当前存在的子线程数量
        :returns: (int);
        '''
        self.__sts = list(filter(lambda x:x.is_alive(), self.__sts))
        return len(self.__sts)
    
    def run_subthread(self, fun, args:tuple=(), kwargs:dict={}, name:"str|None"=None):
        '''
        ## Create a sub thread and run it.
        #### 创建并运行一个子线程
        :returns: (none);
        '''
        while self.count_subthread() >= self.__max:
            pass
        ts = Thread(target=fun, args=args, kwargs=kwargs, daemon=False, name=name)
        self.__sts.append(ts)
        ts.start()
    #EndClass

class Counter():
    '''
    Counter
    累加计数器
    '''

    def __init__(self):
        '''
        ## Initialize a counter.
        #### 初始化一个计数器
        :returns: (none);
        '''
        self.__s = 0

    def update(self, val:"int|bool"=1):
        '''
        ## Update the counter.
        #### 更新计数
        :param val: Delta value;
        :returns: (int) Current value;
        '''
        self.__s += int(val)
        return self.__s
    
    def get_sum(self):
        '''
        ## Get the current value.
        #### 获取当前计数
        :returns: (int) Current value;
        '''
        return self.__s
    #EndClass

class TimeRecorder():
    '''
    Tasking Time Recorder
    任务时间记录器
    '''

    def __init__(self, dest:int):
        '''
        ## Initialize a Tasking Time Recorder.
        #### 初始化一个任务时间记录器
        :param dest: The destination value of the task;
        :returns: (none);
        '''
        self.t_init = time.time()
        self.t_rec = [[self.t_init, 0]] #[curTime,Time(Seconds)OfEach]
        self.n_dest = dest
        self.n_cur = 0

    def update(self):
        '''
        ## Update the current value of the task.
        #### 追加一个时间节点
        :returns: (none);
        '''
        self.n_cur += 1
        t_cur = time.time()
        self.t_rec.append([t_cur, t_cur-self.t_rec[len(self.t_rec)-1][0]])
    
    def get_progress(self, ndigits:int=3):
        '''
        ## Get the progress (/100%).
        #### 获取进度百分比
        :param ndigits: Decimal Digits;
        :returns: (float);
        '''
        return round((self.n_cur/self.n_dest), ndigits)
    
    def get_speed(self, basis:int=100):
        '''
        ## Get the processing speed.
        #### 计算当前任务速度
        :param basis: How many records do we use to calculate the speed;
        :returns: (float) Items per second;
        '''
        sum = []
        for i in range(len(self.t_rec)-1, -1, -1):
            if i+basis < self.n_cur:
                break
            if self.t_rec[i][1]:
                sum.append(self.t_rec[i][1])
        rst = trimmean(sum, 0.05)
        return 1 / rst if rst != 0 else 0
    
    def get_remaining_time(self, basis:int=100):
        '''
        ## Get the time remaining.
        #### 计算当前剩余时间
        :param basis: How many records do we use to calculate the speed;
        :returns: (float) Seconds;
        '''
        return (self.n_dest-self.n_cur) / self.get_speed(basis) if self.get_speed(basis) != 0 else 0
    
    def get_consumed_time(self):
        '''
        ## Get the time from the first record to now.
        #### 计算截至目前的用时
        :returns: (float) Seconds;
        '''
        return time.time() - self.t_rec[0][0]
    #EndClass

class Rounder():
    '''
    Loading Rounder
    转圈圈加载字符工具
    '''

    char = ('/', '-', '\\', '|', '/', '-', '\\', '|')

    def __init__(self):
        self.__n = 0

    def next(self):
        self.__n = 0 if self.__n >= len(self.char)-1 else self.__n+1
        return self.char[self.__n]
    #EndClass
