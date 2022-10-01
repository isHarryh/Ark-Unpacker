# -*- coding: utf-8 -*-
# Copyright (c) 2022, Harry Huang
# @ BSD 3-Clause License
import os, time
from typing import ClassVar
try:
    from osTool import *
except:
    from .osTool import *
from io import BytesIO
from PIL import Image #PIL库用于操作图像
from threading import Thread, enumerate, Event #threading库用于进行多线程
'''
为ArkUnpacker提供一些可复用的代码
'''

class SafeSaver():
    '使保存文件更安全的基类，即避免文件重名并且选择性地覆盖已存在的文件'

    @staticmethod
    def save(data:bytes, intodir:str, name:str, ext:str):
        '''
        #### 安全地以二进制形式保存文件
        :param data:    数据;
        :param intodir: 保存目的地的目录;
        :param name:    纯文件名;
        :param ext:     文件后缀;
        :returns:       (bool) 是否进行了保存;
        '''
        dest = os.path.join(intodir, name)
        name = os.path.basename(dest)
        intodir = os.path.dirname(dest)
        if SafeSaver.__is_unique(data, intodir, name, ext):
            dest = SafeSaver.__no_namesake(intodir, name, ext)
            SafeSaver.__save_bytes(data, dest)
            return True
        return False

    @staticmethod
    def __save_bytes(data:bytes, dest:str):
        #### 私有方法：保存字节流数据
        mkdir(os.path.dirname(dest))
        with open(dest, 'wb') as f:
            f.write(data)

    @staticmethod
    def __is_identical(data:bytes, fp:str):
        #### 私有方法：判断是否和某指定文件内容相同
        with open(fp, 'rb') as f:
            cache = f.read()
        return True if bytes(data) == bytes(cache) else False

    @staticmethod
    def __is_unique(data:bytes, intodir:str, name:str, ext:str):
        #### 私有方法：判断是否不存在内容相同的原本重名的文件
        if os.path.isdir(intodir):
            lenname = len(name)
            flist = os.listdir(intodir)
            flist = list(filter(lambda x:(name == x[:lenname] and ext in x), flist)) #初筛
            for i in flist:
                #(i是初筛后文件的路径名)
                if SafeSaver.__is_identical(data, os.path.join(intodir, i)):
                    return False
        return True

    @staticmethod
    def __no_namesake(intodir:str, name:str, ext:str):
        #### 私有方法：解决重名问题
        tmp = 0
        dest = os.path.join(intodir, f'{name}{ext}')
        while os.path.isfile(dest):
            dest = os.path.join(intodir, f'{name}_#{tmp}{ext}')
            tmp += 1
        return dest
    #EndClass

class MySaver(SafeSaver):
    '用于保存文件的类（实质上是函数载体）'

    @staticmethod
    def save_image(IM:Image.Image, intodir:str, name:str, ext:str='.png'):
        '''
        #### 通过传入一个PIL.Image实例，安全地保存一个图片文件
        :param IM:      PIL.Image图像实例;
        :param intodir: 保存目的地的目录;
        :param name:    纯文件名;
        :param ext:     文件后缀;
        :returns:       (bool) 是否进行了保存;
        '''
        ext = ext.lower()
        if ext not in ['.png', '.jpg', '.jpeg', '.bmp']:
            return False
        if IM.height <= 0 and IM.width <= 0:
            return False
        byt = BytesIO()
        IM.save(byt, format = ('PNG' if ext == '.png' else 'JPEG'))
        byt = byt.getvalue()
        return SafeSaver.save(byt, intodir, name, ext)

    @staticmethod
    def save_script(byt:bytes, intodir:str, name:str, ext:str=''):
        '''
        #### 通过传入一个字节流，安全地保存一个文本文件
        :param byt:     字节流;
        :param intodir: 保存目的地的目录;
        :param name:    纯文件名;
        :param ext:     文件后缀;
        :returns:       (bool) 是否进行了保存;
        '''
        ext = ext.lower()
        if not byt:
            return False
        return SafeSaver.save(byt, intodir, name, ext)

    @staticmethod
    def save_samples(items:bytes, intodir:str, name:str, ext:str=''):
        '''
        #### 通过传入一个音频采样点列表，安全地保存一个音频文件
        :param items:   音频采样点列表;
        :param intodir: 保存目的地的目录;
        :param name:    纯文件名;
        :param ext:     文件后缀;
        :returns:       (bool) 是否进行了保存;
        '''
        byt = bytes()
        for n, d in items:
            byt += d
        if not byt:
            return False
        return SafeSaver.save(byt, intodir, name, ext)
    #EndClass

class ThreadCtrl():
    'Tool for Multi Threading'

    def __init__(self, max_subthread):
        '''
        ## Initialize a tool for multi threading.
        #### 初始化一个多线程控制类
        :param max_subthread: The max number of sub threads;
        :returns: (none);
        '''
        self.__max = max_subthread
        self.__sts = []
    
    def count_subthread(self):
        '''
        ## Get the number of alive sub threads.
        #### 获取当前存在的子线程数量
        :returns: (int);
        '''
        self.__sts = list(filter(lambda x:x.is_alive(), self.__sts))
        return len(self.__sts)
    
    def run_subthread(self, fun, args:tuple=(), kwargs:dict={}):
        '''
        ## Create a sub thread and run it.
        #### 创建并运行一个子线程
        :returns: (none);
        '''
        while self.count_subthread() >= self.__max:
            pass
        ts = Thread(target=fun, args=args, kwargs=kwargs, daemon=False)
        self.__sts.append(ts)
        ts.start()
    #EndClass

class Counter():
    'Counter'

    def __init__(self):
        '''
        ## Initialize a counter.
        #### 初始化一个计数器
        :returns: (none);
        '''
        self.__s = 0

    def update(self, val:int=1):
        '''
        ## Update the counter.
        #### 更新计数
        :param val: Delta value;
        :returns: (int) Current value;
        '''
        self.__s += val
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
    'Tasking Time Recorder'

    t_init = 0
    t_rec = [] #[curVal,curTime,Time(Seconds)OfEach]
    n_dest = 0
    n_cur = 0

    def __init__(self, dest:int):
        '''
        ## Initialize a Tasking Time Recorder.
        #### 初始化一个任务时间计数器
        :param dest: The destination value of the task;
        :returns: (none);
        '''
        self.t_init = time.time()
        self.t_rec = [[self.t_init, 0]]
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
    
    def getProgress(self, ndigits:int=1):
        '''
        ## Get the progress (%).
        #### 获取进度百分比
        :param ndigits: Decimal Digits;
        :returns: (int);
        '''
        return round((self.n_cur/self.n_dest)*100, ndigits)
    
    def getSpeed(self, basis:int=100):
        '''
        ## Get the processing speed.
        #### 计算当前任务速度
        :param basis: How many records do we use to calculate the speed;
        :returns: (float) Items per minute;
        '''
        sum = []
        for i in range(len(self.t_rec)-1, -1, -1):
            if i+basis < self.n_cur:
                break
            if self.t_rec[i][1]:
                sum.append(self.t_rec[i][1])
        rst = trimmean(sum, 0.05)
        return 60 / rst if rst != 0 else 0
    
    def getRemainingTime(self, basis:int=100):
        '''
        ## Get the time remaining.
        #### 计算当前剩余时间
        :param basis: How many records do we use to calculate the speed;
        :returns: (float) Minutes;
        '''
        return (self.n_dest-self.n_cur) / self.getSpeed(basis) if self.getSpeed(basis) != 0 else 0
    #EndClass

class rounder():
    'Loading Rounder'

    char = ['/','-','\\','|','/','-','\\','|']

    def __init__(self):
        self.__n = 0

    def next(self):
        self.__n = 0 if self.__n >= len(self.char)-1 else self.__n+1
        return self.char[self.__n]
    #EndClass

def mean(lst:list):
    '''
    ## Get the mean
    #### 返回数组平均值
    :param lst: List of values;
    :returns:   (float) Mean;
    '''
    if len(lst) == 0:
        return float(0)
    s = 0
    for i in lst:
        s += i
    return float(s / len(lst))

def trimmean(lst:list, percent:float):
    '''
    ## Trim extreme values from the both ends of the list and get the mean
    #### 去除数组两极的极端值，返回数组平均值
    :param lst: List of values;
    :param percent: (float) Ratio of extreme values of one end;
    '''
    if len(lst) == 0:
        return float(0)
    if percent < 0 or percent > 1:
        return float(0)
    newlst = lst[:]
    newlst.sort()
    blocked = int(len(lst) * percent) if len(lst) * percent >= 0 else 0
    newlst = newlst[blocked:-blocked]
    if len(newlst) == 0:
        return mean(lst)
    else:
        return mean(newlst)
