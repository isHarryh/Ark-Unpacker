# -*- coding: utf-8 -*-
# Copyright (c) 2022-2023, Harry Huang
# @ BSD 3-Clause License
import os, time
from src.osTool       import *
from src.colorTool    import *
from src import ResolveAB       as AU_Rs
from src import CombineRGBwithA as AU_Cb
from src import CollectModels   as AU_Cm
from src import ModelsDataDist  as AU_Mdd
'''
ArkUnpacker主程序
'''
AU_ver='v2.2'
AU_i18n='zh-CN'
MAX_THS=32


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
    print('1: 一键执行\n2: 自定义资源解包\n3: 自定义图片合并\n4: ArkModels提取与分拣工具\n0: 退出')
    print(f'{color(7)}输入序号后按回车即可，\n如果您不清楚以上功能的含义，强烈建议您先阅读使用手册(README)：\nhttps://github.com/isHarryh/Ark-Unpacker ')

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

def prt_continue():
    '''
    #### 打印按任意键返回的信息
    :returns: (none);
    '''
    input(f'{color(2)}\n按任意键返回')

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
    inpt = os.path.normpath(input(msg))
    while not os.path.isdir(inpt):
            inpt = os.path.normpath(input(excpt))
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
    AU_Rs.main('.',destdir)
    ###
    prt_subtitle('步骤2|合并图片')
    time.sleep(1)
    AU_Cb.main(destdir,f'Combined_{int(time.time())}')

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
    print(f'{color(7)}\n请指定最大线程数（同时执行任务数）：')
    print('  建议：5-15')
    ths = input_allow(f'{color(2)}> ', [str(i) for i in range(1,MAX_THS)], '  请重新输入合理的数字\n> ')
    ths = int(ths)
    ###
    input(f'{color(2)}\n再按一次回车以开始任务...')
    os.system('title ArkUnpacker - Processing')
    AU_Rs.main(rootdir,destdir,dodel,doimg,dotxt,doaud,separate,ths)

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
    print(f'{color(7)}\n请指定最大线程数（同时执行任务数）：')
    print('  建议：5-15')
    ths = input_allow(f'{color(2)}> ', [str(i) for i in range(1,MAX_THS)], '  请重新输入合理的数字\n> ')
    ths = int(ths)
    ###
    input(f'{color(2)}\n再按一次回车以开始任务...')
    os.system('title ArkUnpacker - Processing')
    AU_Cb.main(rootdir,destdir,dodel,ths)

def run_arkmodels_unpacking(dirs, destdir1, destdir2):
    '''
    #### 以ArkModels仓库的标准执行Spine模型提取
    :returns: (none);
    '''
    prt_subtitle('ArkModels 模型提取')
    ###
    for i in dirs:
        if not os.path.exists(i):
            print(f'{color(3)}在工作目录下找不到 {i}，请确保该文件夹直接位于工作目录中。也有可能是本程序版本与您的资源版本不再兼容，可尝试获取新版程序。{color(7)}')
            return
    ###
    print(f'{color(7)}请指定最大线程数（同时执行任务数）：')
    print('  建议：5-15')
    ths = input_allow(f'{color(2)}> ', [str(i) for i in range(1,MAX_THS)], '  请重新输入合理的数字\n> ')
    ths = int(ths)
    ###
    input(f'{color(2)}\n准备就绪，再按一次回车以开始任务...')
    os.system('title ArkUnpacker - Processing')
    ###
    Delete_File_Dir(destdir1)
    for i in dirs:
        AU_Rs.main(i,destdir1,doaud=False,threads=ths)
    ###
    Delete_File_Dir(destdir2)
    AU_Cb.main(destdir1,destdir2,threads=ths)

def run_arkmodels_filtering(func, destdir, fromdir1, fromdir2):
    '''
    #### 以ArkModels仓库的标准执行Spine模型文件分拣（干员基建小人）
    :returns: (none);
    '''
    prt_subtitle('ArkModels 文件分拣')
    ###
    for i in [fromdir1,fromdir2]:
        if not os.path.exists(i):
            print(f'{color(3)}在工作目录下找不到 {i}，请确保该文件夹直接位于工作目录中。也有可能是您事先没有进行"模型提取"的步骤。{color(7)}')
            return
    Delete_File_Dir(destdir)
    func(destdir,os.path.join(fromdir2),os.path.join(fromdir1),dele=False)
    ###
    print(f'{color(2)}\n任务执行完毕')
    print(f'{color(7)}\n您希望删除分拣前的解包文件吗？')
    print(f'{color(3)}  y=是，n=否(默认)')
    if input() in ['y','Y']:
        Delete_File_Dir(fromdir1)
        Delete_File_Dir(fromdir2)

def run_arkmodels_data_dist():
    '''
    #### 以ArkModels仓库的标准生成Spine模型数据集
    此功能专门服务于ArkModels仓库（一个存储明日方舟Spine模型的仓库）。
    :returns: (none);
    '''
    prt_subtitle('ArkModels 生成数据集')
    ###
    dir = "models"
    if not os.path.exists(dir):
        input(f'{color(3)}在工作目录下找不到 {dir}，请确认您先前已运行了"文件分拣"。按Enter以忽略此错误继续。{color(7)}')
    AU_Mdd.main()

def run_arkmodels_workflow():
    '''
    #### 进入ArkModels提取与分拣工具的页面
    此功能专门服务于ArkModels仓库（一个存储明日方舟Spine模型的仓库）。
    :returns: (none);
    '''
    def prt_arkmodels_menu():
        os.system('cls')
        os.chdir('.')
        print(f'{color(7,0,1)}ArkModels提取与分拣工具')
        print('='*20)
        print(f'{color(7)}ArkModels是作者建立的明日方舟Spine模型仓库（https://github.com/isHarryh/Ark-Models）\n以下功能专门为ArkModels仓库的更新而设计，开始工作流程前需要将skinpack，chararts 以及battle/prefabs/enemies文件夹直接放到程序所在目录。\n执行步骤选择：{color(6)}')
        print('1: 干员基建模型提取\n2: 敌方战斗模型提取\n3: 干员基建模型分拣\n4: 敌方战斗模型分拣\n5: 生成数据集\n0: 返回')
        print(f'{color(7)}输入序号后按回车即可，\n如有必要请阅读使用手册(README)：\nhttps://github.com/isHarryh/Ark-Unpacker ')
    while True:
        os.system('title ArkUnpacker')
        prt_arkmodels_menu()
        order = input(f'{color(2)}> ')
        if order == '1':
            run_arkmodels_unpacking(['chararts', 'skinpack'], "unpacked_temp_arkmodels", "combined_temp_arkmodels")
            prt_continue()
        elif order == '2':
            run_arkmodels_unpacking(['enemies'], "unpacked_temp_arkmodels_enemies", "combined_temp_arkmodels_enemies")
            prt_continue()
        elif order == '3':
            run_arkmodels_filtering(AU_Cm.sort_oper_build, "models", "unpacked_temp_arkmodels", "combined_temp_arkmodels")
            prt_continue()
        elif order == '4':
            run_arkmodels_filtering(AU_Cm.sort_enemy, "models_enemies", "unpacked_temp_arkmodels_enemies", "combined_temp_arkmodels_enemies")
            prt_continue()
        elif order == '5':
            run_arkmodels_data_dist()
            prt_continue()
        elif order == '0':
            return

if __name__ == '__main__':
    while True:
        os.system('title ArkUnpacker')
        prt_homepage()
        order = input(f'{color(2)}> ')
        if order == '1':
            run_quickaccess()
            prt_continue()
        elif order == '2':
            run_costm_Rs()
            prt_continue()
        elif order == '3':
            run_costm_Cb()
            prt_continue()
        elif order == '4':
            run_arkmodels_workflow()
        elif order == '0':
            exit()