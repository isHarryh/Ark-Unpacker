# -*- coding: utf-8 -*-
# Copyright (c) 2022-2023, Harry Huang
# @ BSD 3-Clause License
import os
from io import BytesIO
from PIL import Image
from .GlobalMethods import *
from .Logger import *
from .TaskUtils import *

class SafeSaver():
    '''
    The base class for file saver
    使保存文件更安全的基类，即避免文件重名并且选择性地覆盖已存在的文件
    '''
    thread_ctrl = ThreadCtrl(1)
    total_processed = Counter()
    total_requested = Counter()

    @staticmethod
    def get_progress():
        '''
        ## Get the progress (/100%).
        #### 获取进度百分比，即线程池空闲率
        :returns: (float);
        '''
        return 1 - MySaver.thread_ctrl.get_idle_ratio()

    @staticmethod
    def reset():
        '''
        ## Reset the status
        #### 重置状态
        :returns: (none);
        '''
        MySaver.total_processed = Counter()
        MySaver.total_requested = Counter()

    @staticmethod
    def save(data:bytes, intodir:str, name:str, ext:str, callback:staticmethod):
        '''
        ## Save binary data to a file
        #### 安全地以二进制形式保存文件
        :param data:    数据;
        :param intodir: 保存目的地的目录;
        :param name:    纯文件名;
        :param ext:     文件后缀;
        :param callbak: 成功保存回调，参数(has_saved);
        :returns:       (none);
        '''
        MySaver.thread_ctrl.run_subthread(MySaver._save, (data, intodir, name, ext, callback), name=f"SaverThread:{id(data)}")
    
    @staticmethod
    def _save(data:bytes, intodir:str, name:str, ext:str, callback:staticmethod):
        #### 保护方法：单线程保存数据
        MySaver.total_requested.update()
        try:
            dest = os.path.join(intodir, name)
            name = os.path.basename(dest)
            intodir = os.path.dirname(dest)
            if SafeSaver.__is_unique(data, intodir, name, ext):
                dest = SafeSaver.__no_namesake(intodir, name, ext)
                SafeSaver._save_bytes(data, dest)
                if callback:
                    callback(True)
            if callback:
                callback(False)
        except Exception as arg:
            Logger.error(f"Saver: Failed to save file {dest} because: Exception{type(arg)} {arg}")
        MySaver.total_processed.update()

    @staticmethod
    def _save_bytes(data:bytes, dest:str):
        #### 保护方法：保存字节流数据
        mkdir(os.path.dirname(dest))
        with open(dest, 'wb') as f:
            f.write(data)

    @staticmethod
    def __is_same(data:bytes, fp:str):
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
                if SafeSaver.__is_same(data, os.path.join(intodir, i)):
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
    def save_image(IM:Image.Image, intodir:str, name:str, ext:str='.png', callback:staticmethod=None):
        '''
        #### 通过传入一个PIL.Image实例，安全地保存一个图片文件
        :param IM:      PIL.Image图像实例;
        :param intodir: 保存目的地的目录;
        :param name:    纯文件名;
        :param ext:     文件后缀;
        :param callbak: 成功保存回调，参数(has_saved);
        :returns:       (bool) 是否调用了保存;
        '''
        ext = ext.lower()
        if ext not in ['.png', '.jpg', '.jpeg', '.bmp']:
            return False
        if IM.height <= 0 and IM.width <= 0:
            return False
        byt = BytesIO()
        IM.save(byt, format = ('PNG' if ext == '.png' else 'JPEG'))
        byt = byt.getvalue()
        SafeSaver.save(byt, intodir, name, ext, callback)
        return True

    @staticmethod
    def save_script(byt:bytes, intodir:str, name:str, ext:str='', callback:staticmethod=None):
        '''
        #### 通过传入一个字节流，安全地保存一个文本文件
        :param byt:     字节流;
        :param intodir: 保存目的地的目录;
        :param name:    纯文件名;
        :param ext:     文件后缀;
        :param callbak: 成功保存回调，参数(has_saved);
        :returns:       (bool) 是否调用了保存;
        '''
        ext = ext.lower()
        if not byt:
            return False
        SafeSaver.save(byt, intodir, name, ext, callback)
        return True

    @staticmethod
    def save_samples(items:bytes, intodir:str, name:str, ext:str='', callback:staticmethod=None):
        '''
        #### 通过传入一个音频采样点列表，安全地保存一个音频文件
        :param items:   音频采样点列表;
        :param intodir: 保存目的地的目录;
        :param name:    纯文件名;
        :param ext:     文件后缀;
        :param callbak: 成功保存回调，参数(has_saved);
        :returns:       (bool) 是否调用了保存;
        '''
        ext = ext.lower()
        byt = bytes()
        for n, d in items:
            byt += d
        if not byt:
            return False
        SafeSaver.save(byt, intodir, name, ext, callback)
        return True
    #EndClass
