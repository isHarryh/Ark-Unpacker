# -*- coding: utf-8 -*-
# Copyright (c) 2022, Harry Huang
# @ BSD 3-Clause License
import os, time
from src.osTool    import *
from src.colorTool import *
from src import ResolveAB       as AU_Rs
from src import CombineRGBwithA as AU_Cb
'''
ArkUnpacker主程序
'''
AU_ver='v1.0'


def prt_homepage():
    '''
    #### 打印主页
    :returns: (none);
    '''
    os.system('cls')
    print(color(7)+'欢迎使用ArkUnpacker '+AU_ver)

def prt_subtitle(msg:str):
    '''
    #### 打印子标题
    :param msg: 标题;
    :returns: (none);
    '''
    os.system('cls')
    os.chdir('.')
    print("")
    print(color(7,0,1)+'='*10)
    print(color(7,0,1)+msg)
    print(color(7,0,1)+'='*10)
    print(color(7))

def run_quickaccess():
    '''
    #### 启动一键执行模式
    :returns: (none);
    '''
    prt_subtitle('步骤1|解包')
    #AU_Rs.main(["test"],"temp",dotxt=False,doaud=False,dodel=True,detail=False)
    prt_subtitle('步骤2|合并')
    AU_Cb.main(["temp\\test"],"temp2",dodel=True,detail=False)
    exit()


if __name__ == '__main__':
    prt_homepage()
    run_quickaccess()
    input()