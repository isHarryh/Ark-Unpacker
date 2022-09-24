# -*- coding: utf-8 -*-
# Copyright (c) 2022, Harry Huang
# @ BSD 3-Clause License
import os, time
from src.osTool       import *
from src.colorTool    import *
from src import ResolveAB       as AU_Rs
from src import CombineRGBwithA as AU_Cb
'''
ArkUnpacker主程序
'''
AU_ver='v2.0'
AU_i18n='zh-CN'


def prt_homepage():
    '''
    #### 打印主页
    :returns: (none);
    '''
    os.system('cls')
    os.chdir('.')
    print(f'{color(7,0,1)}欢迎使用ArkUnpacker {AU_ver}')
    print('='*20)
    print(f'{color(7)}模式选择：{color(6)}')
    print('1: 一键执行\n2: 自定义资源解包\n3: 自定义图片合并\n0: 退出')
    print(f'{color(7)}输入序号后按回车即可，\n如果您不清楚以上功能的含义，强烈建议您先阅读使用手册(README)：\nhttps://github.com/isHarryh/Ark-Unpacker/')

def prt_subtitle(msg:str):
    '''
    #### 打印子标题
    :param msg: 标题;
    :returns: (none);
    '''
    os.system('cls')
    os.chdir('.')
    print(f'{color(7,0,1)}{"="*10}')
    print(msg)
    print(f'{"="*10}\n{color(7)}')

def input_allow(msg:str,allow:list,excpt:str):
    '''
    #### 获取合规的键盘命令输入
    :param msg:   提示信息;
    :param allow: 包含了合规的输入的列表;
    :param excpt: 输入不合规时的提示信息;
    :returns:     (str) 一个合规的输入;
    '''
    inpt = input(msg)
    while not (inpt in allow):
        inpt = input(excpt)
    return inpt

def input_path(msg:str,excpt:str):
    '''
    #### 获取合规的目录路径输入
    :param msg:   提示信息;
    :param excpt: 输入目录不存在时的提示信息;
    :returns:     (str) 一个合规的输入;
    '''
    inpt = input(msg)
    while not (os.path.isdir(inpt)):
        inpt = input(excpt)
    return inpt

def get_dirlist(ignore:list=[]):
    '''
    #### 获取当前目录下的第一级子目录的列表
    :param ignore: 可选，忽略名单，精确匹配;
    :returns:      (list) 子目录的列表;
    '''
    filelist = []
    for i in os.listdir():
        if os.path.isdir(i) and os.path.basename(i) not in ignore:
            filelist.append(i)
    return filelist

def run_quickaccess():
    '''
    #### 启动一键执行模式
    :returns: (none);
    '''
    os.system('title ArkUnpacker - Processing')
    destdir = f'Unpacked_{int(time.time())}'
    ignore = [".vscode","__pycache__",".git"]
    ###
    prt_subtitle('步骤1|资源解包')
    time.sleep(1)
    AU_Rs.main(get_dirlist(ignore),destdir)
    ###
    prt_subtitle('步骤2|合并图片')
    time.sleep(1)
    AU_Cb.main([destdir],f'Combined_{int(time.time())}',detail=False)

def run_costm_Rs():
    '''
    #### 启动自定义资源解包模式
    :returns: (none);
    '''
    prt_subtitle('自定义资源解包')
    ###
    print(f'{color(7)}\n请输入要解包的目录后按回车')
    print('  支持相对路径，\".\"表示选择当前目录')
    rootdir = input_path(f'{color(2)}> ','  该目录似乎不存在\n> ')
    print(f'您选择的解包目录是：\n  {color(6)}{os.path.abspath(rootdir)}')
    ###
    print(f'{color(7)}\n请输入导出的目的地后按回车')
    print('  支持相对路径，留空表示自动创建')
    destdir = input(f'{color(2)}> ')
    if not destdir:
        destdir = f'Unpacked_{int(time.time())}'
    print(f'您选择的导出目录是：\n  {color(6)}{os.path.abspath(destdir)}')
    ###
    dodel = False
    if os.path.isdir(destdir):
        print(f'{color(7)}\n该导出目录已存在，您要删除它里面的全部文件吗？')
        print(f'{color(3)}  请!慎重!选择：y=删除，n=保留(默认)')
        dodel = input(f'{color(2)}> ')
        dodel = True if dodel in ['y','Y'] else False
    ###
    print(f'{color(7)}\n您希望用AB文件原名来分类每组文件吗？')
    print(f'{color(3)}  y=是(默认)，n=否')
    separate = input(f'{color(2)}> ')
    separate = False if separate in ['n','N'] else True
    ###
    print(f'{color(7)}\n请输入要导出的资源类型后按回车')
    print('  可多选：i=图片，t=文本，a=音频')
    print('  示例输入：\"ita\"，\"ia\"')
    dothem = input(f'{color(2)}> ')
    doimg = True if 'i' in dothem or 'I' in dothem else False
    dotxt = True if 't' in dothem or 'T' in dothem else False
    doaud = True if 'a' in dothem or 'A' in dothem else False
    ###
    input(f'{color(2)}\n再按一次回车以开始任务...')
    os.system('title ArkUnpacker - Processing')
    AU_Rs.main([rootdir],destdir,dodel,doimg,dotxt,doaud,separate)

def run_costm_Cb():
    '''
    #### 启动自定义合并图片模式
    :returns: (none);
    '''
    prt_subtitle('自定义合并图片')
    ###
    print(f'{color(7)}\n请输入存放图片的目录后按回车')
    print('  支持相对路径，\".\"表示选择当前目录')
    rootdir = input_path(f'{color(2)}> ','  该目录似乎不存在\n> ')
    print(f'您选择的存放图片的目录是：\n  {color(6)}{os.path.abspath(rootdir)}')
    ###
    print(f'{color(7)}\n请输入导出的目的地后按回车')
    print('  支持相对路径，留空表示自动创建')
    destdir = input(f'{color(2)}> ')
    if not destdir:
        destdir = f'Combined_{int(time.time())}'
    print(f'您选择的导出目录是：\n  {color(6)}{os.path.abspath(destdir)}')
    ###
    dodel = False
    if os.path.isdir(destdir):
        print(f'{color(7)}\n该导出目录已存在，您要删除它里面的全部文件吗？')
        print(f'{color(3)}  请!慎重!选择：y=删除，n=保留(默认)')
        dodel = input(f'{color(2)}> ')
        dodel = True if dodel in ['y','Y'] else False
    ###
    print(f'{color(7)}\n您希望的回显模式是？')
    print(f'{color(3)}  y=详细，n=简洁(默认)')
    detail = input(f'{color(2)}> ')
    detail = True if detail in ['y','Y'] else False
    ###
    input(f'{color(2)}\n再按一次回车以开始任务...')
    os.system('title ArkUnpacker - Processing')
    AU_Cb.main([rootdir],destdir,dodel,detail)


if __name__ == '__main__':
    while True:
        os.system('title ArkUnpacker')
        prt_homepage()
        order = input(f'{color(2)}> ')
        if order == '1':
            run_quickaccess()
            input(f'{color(2)}\n按任意键返回')
        elif order == '2':
            run_costm_Rs()
            input(f'{color(2)}\n按任意键返回')
        elif order == '3':
            run_costm_Cb()
            input(f'{color(2)}\n按任意键返回')
        elif order == '0':
            exit()