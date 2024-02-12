# -*- coding: utf-8 -*-
# Copyright (c) 2022-2023, Harry Huang
# @ BSD 3-Clause License
import os, time
from src.utils._ImportAllUtils import *
from src import ResolveAB       as AU_Rs
from src import CombineRGBwithA as AU_Cb
from src import CollectModels   as AU_Cm
from src import ModelsDataDist  as AU_Mdd
'''
ArkUnpacker主程序
'''
AU_ver = 'v2.6'
AU_i18n = 'zh-CN'
AU_thread_suggest = '10-20'


def prt_homepage():
    '''
    #### 打印主页
    :returns: (none);
    '''
    Logger.info("CI: In Homepage.")
    os.system('cls')
    os.chdir('.')
    print(f'欢迎使用ArkUnpacker {AU_ver}', s=1)
    print('='*20)
    print(f'模式选择：')
    print(f'1: 一键执行\n2: 自定义资源解包\n3: 自定义图片合并\n4: ArkModels提取与分拣工具\n0: 退出', c=6)
    print(f'输入序号后按回车即可，\n如果您不清楚以上功能的含义，强烈建议您先阅读使用手册(README)：\nhttps://github.com/isHarryh/Ark-Unpacker ')

def prt_subtitle(msg:str):
    '''
    #### 打印子标题
    :param msg: 标题;
    :returns: (none);
    '''
    os.system('cls')
    os.chdir('.')
    print(f'{"="*10}', s=1)
    print(msg, s=1)
    print(f'{"="*10}\n', s=1)

def prt_continue():
    '''
    #### 打印按任意键返回的信息
    :returns: (none);
    '''
    input(f'\n按任意键返回', c=2)

def input_allow(msg:str, allow:list, excpt:str):
    '''
    #### 获取合规的键盘命令输入
    :param msg:   提示信息;
    :param allow: 包含了合规的输入的列表;
    :param excpt: 输入不合规时的提示信息;
    :returns:     (str) 一个合规的输入;
    '''
    inpt = input(msg, c=2)
    while not (inpt in allow):
        inpt = input(excpt, c=2)
    return inpt

def input_path(msg:str, excpt:str):
    '''
    #### 获取合规的目录路径输入
    :param msg:   提示信息;
    :param excpt: 输入目录不存在时的提示信息;
    :returns:     (str) 一个合规的输入;
    '''
    inpt = os.path.normpath(input(msg, c=2))
    while not os.path.isdir(inpt):
            inpt = os.path.normpath(input(excpt, c=2))
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
    Logger.info("CI: Run quick access.")
    os.system('title ArkUnpacker - Processing')
    destdir = f'Unpacked_{int(time.time())}'
    ignore = [".vscode","__pycache__",".git"]
    ###
    prt_subtitle('步骤1|资源解包')
    time.sleep(1)
    AU_Rs.main('.',destdir,threads=config.get("threads_default"))
    ###
    prt_subtitle('步骤2|合并图片')
    time.sleep(1)
    AU_Cb.main(destdir,f'Combined_{int(time.time())}',threads=config.get("threads_default"))

def run_costm_Rs():
    '''
    #### 启动自定义资源解包模式
    :returns: (none);
    '''
    Logger.info("CI: Customized unpack mode.")
    prt_subtitle('自定义资源解包')
    ###
    print(f'\n请输入要解包的目录后按回车')
    print('  支持相对路径，\".\"表示选择当前目录')
    rootdir = input_path(f'> ','  该目录似乎不存在\n> ')
    print(f'您选择的解包目录是：', c=2)
    print(f'  {os.path.abspath(rootdir)}', c=6)
    ###
    print(f'\n请输入导出的目的地后按回车')
    print('  支持相对路径，留空表示自动创建')
    destdir = input(f'> ', c=2)
    if not destdir:
        destdir = f'Unpacked_{int(time.time())}'
    print(f'您选择的导出目录是：', c=2)
    print(f'  {os.path.abspath(destdir)}', c=6)
    ###
    dodel = False
    if os.path.isdir(destdir):
        print(f'\n该导出目录已存在，您要删除它里面的全部文件吗？')
        print(f'  请!慎重!选择：y=删除，n=保留(默认)', c=3)
        dodel = input(f'> ', c=2)
        dodel = True if dodel in ['y','Y'] else False
    ###
    print(f'\n您希望用AB文件原名来分类每组文件吗？')
    print(f'  y=是(默认)，n=否', c=3)
    separate = input(f'> ', c=2)
    separate = False if separate in ['n','N'] else True
    ###
    print(f'\n请输入要导出的资源类型后按回车')
    print('  可多选：i=图片，t=文本，a=音频')
    print('  示例输入：\"ita\"，\"ia\"')
    dothem = input(f'> ', c=2)
    doimg = True if 'i' in dothem or 'I' in dothem else False
    dotxt = True if 't' in dothem or 'T' in dothem else False
    doaud = True if 'a' in dothem or 'A' in dothem else False
    ###
    print(f'\n请指定最大线程数（同时执行任务数）：')
    print(f'  建议：{AU_thread_suggest}')
    ths = input_allow(f'> ', [str(i) for i in range(1,config.get('threads_limit'))], '  请重新输入合理的数字\n> ')
    ths = int(ths)
    ###
    input(f'\n再按一次回车以开始任务...', c=2)
    os.system('title ArkUnpacker - Processing')
    AU_Rs.main(rootdir,destdir,dodel,doimg,dotxt,doaud,False,separate,ths)

def run_costm_Cb():
    '''
    #### 启动自定义合并图片模式
    :returns: (none);
    '''
    Logger.info("CI: Customized image combine mode.")
    prt_subtitle('自定义合并图片')
    ###
    print(f'\n请输入存放图片的目录后按回车')
    print('  支持相对路径，\".\"表示选择当前目录')
    rootdir = input_path(f'> ','  该目录似乎不存在\n> ')
    print(f'您选择的存放图片的目录是：')
    print(f' {os.path.abspath(rootdir)}', c=6)
    ###
    print(f'\n请输入导出的目的地后按回车')
    print('  支持相对路径，留空表示自动创建')
    destdir = input(f'> ', c=2)
    if not destdir:
        destdir = f'Combined_{int(time.time())}'
    print(f'您选择的导出目录是：')
    print(f'  {os.path.abspath(destdir)}', c=6)
    ###
    dodel = False
    if os.path.isdir(destdir):
        print(f'\n该导出目录已存在，您要删除它里面的全部文件吗？')
        print(f'  请!慎重!选择：y=删除，n=保留(默认)', c=3)
        dodel = input(f'> ', c=2)
        dodel = True if dodel in ['y','Y'] else False
    ###
    print(f'\n请指定最大线程数（同时执行任务数）：')
    print(f'  建议：{AU_thread_suggest}')
    ths = input_allow(f'> ', [str(i) for i in range(1,config.get('threads_limit'))], '  请重新输入合理的数字\n> ')
    ths = int(ths)
    ###
    input(f'\n再按一次回车以开始任务...', c=2)
    os.system('title ArkUnpacker - Processing')
    AU_Cb.main(rootdir,destdir,dodel,ths)

def run_arkmodels_unpacking(dirs, destdir):
    '''
    #### 以ArkModels仓库的标准执行Spine模型提取
    :returns: (none);
    '''
    Logger.info("CI: ArkModels unpack mode.")
    prt_subtitle('ArkModels 模型提取')
    ###
    for i in dirs:
        if not os.path.exists(i):
            print(f'在工作目录下找不到 {i}，请确保该文件夹直接位于工作目录中。也有可能是本程序版本与您的资源版本不再兼容，可尝试获取新版程序。', c=3)
            return
    ###
    print(f'请指定最大线程数（同时执行任务数）：')
    print(f'  建议：{AU_thread_suggest}')
    ths = input_allow(f'> ', [str(i) for i in range(1,config.get('threads_limit'))], '  请重新输入合理的数字\n> ')
    ths = int(ths)
    ###
    input(f'\n准备就绪，再按一次回车以开始任务...', c=2)
    os.system('title ArkUnpacker - Processing')
    ###
    print(f'正在清理...')
    rmdir(destdir)
    for i in dirs:
        AU_Rs.main(i,destdir,doimg=False,dotxt=False,doaud=False,dospine=True,threads=ths)

def run_arkmodels_filtering(dirs, destdirs):
    '''
    #### 以ArkModels仓库的标准执行Spine模型文件分拣
    :returns: (none);
    '''
    Logger.info("CI: ArkModels file filter mode.")
    prt_subtitle('ArkModels 文件分拣')
    ###
    dirs_ = []
    destdirs_ = []
    for i, j in zip(dirs, destdirs):
        #TODO 检查二者长度相等
        if not os.path.exists(i):
            input(f'在工作目录下找不到 {i}，请确保该文件夹直接位于工作目录中。也有可能是您事先没有进行"模型提取"的步骤。按Enter以尝试继续。', c=3)
        else:
            dirs_.append(i)
            destdirs_.append(j)
    ###
    AU_Cm.main(dirs_, destdirs_)
    print('\n任务执行完毕', c=2)
    print('\n您希望删除分拣前的解包文件吗？')
    print('  y=是，n=否(默认)', c=3)
    if input(c=2) in ['y','Y']:
        print('正在清理...')
        print('这可能需要一段时间。您也可以关闭程序，然后手动删除。')
        for i in dirs_:
            rmdir(i) 

def run_arkmodels_data_dist():
    '''
    #### 以ArkModels仓库的标准生成Spine模型数据集
    此功能专门服务于ArkModels仓库（一个存储明日方舟Spine模型的仓库）。
    :returns: (none);
    '''
    Logger.info("CI: ArkModels dataset mode.")
    prt_subtitle('ArkModels 生成数据集')
    ###
    for i in ['models', 'models_enemies']:
        if not os.path.exists(i):
            print(f'在工作目录下找不到 {i}，请确认您先前已运行了"文件分拣"。按Enter以忽略此错误继续。', c=3)
            return
    AU_Mdd.main()

def run_arkmodels_workflow():
    '''
    #### 进入ArkModels提取与分拣工具的页面
    此功能专门服务于ArkModels仓库（一个存储明日方舟Spine模型的仓库）。
    :returns: (none);
    '''
    Logger.info("CI: In ArkModels workflow.")
    def prt_arkmodels_menu():
        os.system('cls')
        os.chdir('.')
        print(f'ArkModels提取与分拣工具', s=1)
        print('='*20)
        print(f'ArkModels是作者建立的明日方舟Spine模型仓库（https://github.com/isHarryh/Ark-Models），以下功能专门为ArkModels仓库的更新而设计。')
        print(f'运行部分功能之前，需要将括号内所示的资源文件夹放到程序所在目录中。\n执行步骤选择：')
        print('1: 干员基建模型提取（skinpack，chararts）\n2: 敌方战斗模型提取（battle/prefabs/enemies）\n3: 动态立绘模型提取（arts/dynchars）\n4: 模型分拣\n5: 生成数据集\n0: 返回', c=6)
        print(f'输入序号后按回车即可，\n如有必要请阅读使用手册(README)：\nhttps://github.com/isHarryh/Ark-Unpacker ')
    while True:
        os.system('title ArkUnpacker')
        prt_arkmodels_menu()
        order = input(f'> ', c=2)
        if order == '1':
            run_arkmodels_unpacking(['chararts', 'skinpack'], "temp_arkmodels")
            prt_continue()
        elif order == '2':
            run_arkmodels_unpacking(['enemies'], "temp_arkmodels_enemies")
            prt_continue()
        elif order == '3':
            run_arkmodels_unpacking(['dynchars'], "temp_arkmodels_dynchars")
            prt_continue()
        elif order == '4':
            run_arkmodels_filtering(["temp_arkmodels", "temp_arkmodels_enemies", "temp_arkmodels_dynchars"], ['models', 'models_enemies', 'models_illust'])
            prt_continue()
        elif order == '5':
            run_arkmodels_data_dist()
            prt_continue()
        elif order == '0':
            return

if __name__ == '__main__':
    config = Config()
    Logger.set_instance(config.get('log_file'), config.get('log_level'))
    try:
        Logger.info("Initialized")
        while True:
            os.system('title ArkUnpacker')
            prt_homepage()
            order = input(f'> ', c=2)
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
                break
        
    except InterruptedError as arg:
        Logger.info("CI: Program was interrupted.")
    except SystemExit as arg:
        Logger.info(f"CI: Program was exited explicitly with code {arg.code}.")
    except BaseException as arg:
        Logger.error(f"CI: Oops! Unexpected error occurred: Exception{type(arg)} {arg}")
        raise arg
