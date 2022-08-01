# -*- coding: utf-8 -*-
# Copyright (c) 2022, Harry Huang
# @ BSD 3-Clause License
import os
'''
为ArkUnpacker提供一些可复用的代码
'''

class SafeSaver():
    '安全地保存文件的基类（避免重名）'

    def __is_identical(self, data:bytes, fp:str):
        #### 私有方法：判断是否和某指定文件内容相同
        with open(fp, 'rb') as f:
            cache = f.read()
        return True if bytes(data) == bytes(cache) else False

    def __is_unique(self, data:bytes, intodir:str, name:str, ext:str):
        #### 私有方法：判断是否不存在内容相同的原本重名的文件
        flist = os.listdir(intodir)
        flist = list(filter(lambda x:(name in x and ext in x), flist)) #初筛
        for i in flist:
            #(i是初筛后文件的路径名)
            if self.__is_identical(data, os.path.join(intodir, i)):
                return False
        return True

    def __no_namesake(self, intodir:str, name:str, ext:str):
        #### 私有方法：解决重名问题
        tmp = 0
        dest = os.path.join(intodir, f'{name}{ext}')
        while os.path.isfile(dest):
            dest = os.path.join(intodir, f'{name}_#{tmp}{ext}')
            tmp += 1
        return dest

class Save_Image(SafeSaver):
    '保存图片的类'
    
    def __init__(self, IM, intodir:str, name:str, ext:str='.png'):
        '''
        #### 通过传入一个PIL.Image实例，安全地保存一个图片
        :param IM:      PIL.Image图像实例;
        :param intodir: 保存目的地的目录;
        :param name:    纯文件名;
        :param ext:     文件后缀;
        :returns:       (none);
        '''
        pass
        