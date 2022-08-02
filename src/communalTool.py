# -*- coding: utf-8 -*-
# Copyright (c) 2022, Harry Huang
# @ BSD 3-Clause License
import os
try:
    from osTool import *
except:
    from .osTool import *
from io import BytesIO
from PIL import Image #PIL库用于操作图像
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
            flist = os.listdir(intodir)
            flist = list(filter(lambda x:(name in x and ext in x), flist)) #初筛
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