# -*- coding: utf-8 -*-
# Copyright (c) 2022-2024, Harry Huang
# @ BSD 3-Clause License
import time
import argparse
import os
import os.path as osp

from src.utils import ArgParser
from src.utils.Config import Config
from src.utils.Logger import Logger
from src.utils.GlobalMethods import color, input, print, clear, title, stacktrace, rmdir
from src import ResolveAB       as AU_Rs
from src import DecodeTextAsset as AU_Fb
from src import CombineRGBwithA as AU_Cb
from src import CollectModels   as AU_Cm
from src import ModelsDataDist  as AU_Mdd

ARKUNPACKER_VERSION = 'v3.2'
ARKUNPACKER_LOCAL = 'zh-CN'


def prt_homepage():
    Logger.info("CI: In Homepage.")
    clear()
    os.chdir('.')
    print(f"欢迎使用ArkUnpacker {ARKUNPACKER_VERSION}", s=1)
    print("=" * 20)
    print("""模式选择：
1: 一键执行
2: 自定义资源解包
3: 自定义图片合并
4: 自定义文本资源解码
5: ArkModels提取与分拣工具
0: 退出""", c=6)
    print("输入序号后按Enter即可，\n如果您不清楚以上功能的含义，强烈建议您先阅读使用手册(README)：\nhttps://github.com/isHarryh/Ark-Unpacker ")

def prt_subtitle(msg:str):
    clear()
    os.chdir('.')
    print("=" * 10, s=1)
    print(msg, s=1)
    print("=" * 10, s=1)

def prt_continue():
    UserInput.request("\n> 按Enter以继续...")

def run_quickaccess():
    Logger.info("CI: Run quick access.")
    title("ArkUnpacker - Processing")
    destdir = f'Unpacked_{int(time.time())}'
    ###
    prt_subtitle("步骤1|资源解包")
    time.sleep(1)
    AU_Rs.main('.', destdir)
    ###
    prt_subtitle("步骤2|合并图片")
    time.sleep(1)
    AU_Cb.main(destdir, f'Combined_{int(time.time())}')

def run_custom_resolve_ab():
    Logger.info("CI: Customized unpack mode.")
    prt_subtitle("自定义资源解包")
    ###
    print("\n请输入要解包的目录或文件路径")
    src = UserInput.request_path()
    print("解包目标路径：", c=2)
    print(f"  {osp.abspath(src)}", c=6)
    ###
    print("\n请输入导出目录的路径")
    print("  支持相对路径，留空表示自动创建")
    destdir = input("> ", c=2)
    if not destdir:
        destdir = f'Unpacked_{int(time.time())}'
    print("导出目录路径：", c=2)
    print(f"  {osp.abspath(destdir)}", c=6)
    ###
    do_del = False
    if osp.isdir(destdir):
        print("\n该导出目录已存在，您要删除它里面的全部文件吗？")
        print("  请!慎重!选择：[y]删除，[n]保留(默认)", c=3)
        do_del = UserInput.request_yes_or_no(False)
    ###
    separate = True
    if not osp.isfile(src):
        print("\n是否对导出的文件按来源进行分组？")
        print("  [y]是(默认)，[n]否", c=3)
        separate = UserInput.request_yes_or_no(True)
    ###
    print("\n请输入要导出的资源类型")
    print("  [i]图片，[t]文本，[a]音频", c=3)
    print("  [s]Spine动画模型", c=3)
    print("  示例输入：\"ita\"，\"ia\"")
    do_them = input("> ", c=2).lower()
    do_img = True if "i" in do_them else False
    do_txt = True if "t" in do_them else False
    do_aud = True if "a" in do_them else False
    do_spi = True if "s" in do_them else False
    print(f"  [{'√' if do_img else '×'}]图片，[{'√' if do_txt else '×'}]文本，[{'√' if do_aud else '×'}]音频", c=6)
    print(f"  [{'√' if do_spi else '×'}]Spine动画模型", c=6)
    ###
    prt_continue()
    title("ArkUnpacker - Processing")
    AU_Rs.main(src, destdir, do_del, do_img, do_txt, do_aud, do_spi, separate)

def run_custom_combine_image():
    Logger.info("CI: Customized image combine mode.")
    prt_subtitle("自定义合并图片")
    ###
    print("\n请输入源图片目录的路径")
    rootdir = UserInput.request_path()
    print("源图片目录路径：")
    print(f"  {osp.abspath(rootdir)}", c=6)
    ###
    print("\n请输入导出的目的地")
    print("  支持相对路径，留空表示自动创建")
    destdir = input("> ", c=2)
    if not destdir:
        destdir = f'Combined_{int(time.time())}'
    print("您选择的导出目录是：")
    print(f"  {osp.abspath(destdir)}", c=6)
    ###
    do_del = False
    if osp.isdir(destdir):
        print("\n该导出目录已存在，您要删除它里面的全部文件吗？")
        print("  请!慎重!选择：[y]删除，[n]保留(默认)", c=3)
        do_del = UserInput.request_yes_or_no(False)
    ###
    prt_continue()
    title("ArkUnpacker - Processing")
    AU_Cb.main(rootdir, destdir, do_del)

def run_custom_textasset_decode():
    Logger.info("CI: Customized textasset decoding mode.")
    prt_subtitle("自定义文本资源解码")
    ###
    print("Arknights游戏内数据文件主要位于TextAsset中，采用FlatBuffers格式或AES加密存储。")
    print("在资源解包后需要对这些文件进行解码才可得到游戏数据。")
    print("\n请输入源文件目录的路径")
    print("若您不清楚哪些文件是TextAsset，请选择整个解包后的目录。")
    rootdir = UserInput.request_path()
    print(" 源文件的目录是：")
    print(f"  {osp.abspath(rootdir)}", c=6)
    ###
    print("\n请输入导出的目的地")
    print("  支持相对路径，留空表示自动创建")
    destdir = input("> ", c=2)
    if not destdir:
        destdir = f'Decoded_{int(time.time())}'
    print("您选择的导出目录是：")
    print(f"  {osp.abspath(destdir)}", c=6)
    ###
    do_del = False
    if osp.isdir(destdir):
        print("\n该导出目录已存在，您要删除它里面的全部文件吗？")
        print("  请!慎重!选择：[y]删除，[n]保留(默认)", c=3)
        do_del = UserInput.request_yes_or_no(False)
    ###
    prt_continue()
    title("ArkUnpacker - Processing")
    AU_Fb.main(rootdir, destdir, do_del)

def run_arkmodels_unpacking(dirs, destdir):
    Logger.info("CI: ArkModels unpack mode.")
    prt_subtitle("ArkModels 模型提取")
    ###
    for i in dirs:
        if not osp.exists(i):
            print(f"在工作目录下找不到 {i}，请确保该文件夹直接位于工作目录中。也有可能是本程序版本与您的资源版本不再兼容，可尝试获取新版程序。", c=3)
            return
    title("ArkUnpacker - Processing")
    ###
    print("正在清理...")
    rmdir(destdir)
    for i in dirs:
        AU_Rs.main(i, destdir, do_img=False, do_txt=False, do_aud=False, do_spine=True)

def run_arkmodels_filtering(dirs, destdirs):
    Logger.info("CI: ArkModels file filter mode.")
    prt_subtitle("ArkModels 文件分拣")
    ###
    dirs_ = []
    destdirs_ = []
    for i, j in zip(dirs, destdirs):
        if not osp.exists(i):
            print(f"在工作目录下找不到 {i}，请确保该文件夹直接位于工作目录中。也有可能是您事先没有进行\"模型提取\"的步骤。", c=3)
            UserInput.request("> 输入符号 \"*\" 以取消任务，或直接按Enter以强制继续")
        else:
            dirs_.append(i)
            destdirs_.append(j)
    ###
    AU_Cm.main(dirs_, destdirs_)

def run_arkmodels_data_dist():
    Logger.info("CI: ArkModels dataset mode.")
    prt_subtitle("ArkModels 生成数据集")
    ###
    for i in ["models", "models_enemies"]:
        if not osp.exists(i):
            print(f"在工作目录下找不到 {i}，请确认您先前已运行了\"文件分拣\"。", c=3)
            UserInput.request("> 输入符号 \"*\" 以取消任务，或直接按Enter以强制继续")
            return
    AU_Mdd.main()

def run_arkmodels_workflow():
    def visual(fp:str, default_c:int=6):
        return f"{color(2 if osp.exists(fp) else 3)}{fp}{color(default_c)}"
    Logger.info("CI: In ArkModels workflow.")
    def prt_arkmodels_menu():
        clear()
        os.chdir('.')
        print("ArkModels提取与分拣工具", s=1)
        print("="*20)
        print("""ArkModels是作者建立的明日方舟Spine模型仓库（https://github.com/isHarryh/Ark-Models），以下功能专门为ArkModels仓库的更新而设计。
运行部分功能之前，需要确保括号内所示的资源文件夹已位于程序所在目录中。""")
        print(f"""功能选择：
1: 一键执行
2: 干员基建模型提取 ({visual('chararts')}, {visual('skinpack')})
3: 敌方战斗模型提取 ({visual('battle')})
4: 动态立绘模型提取 ({visual('arts')})
5: 模型分拣
6: 生成数据集 ({visual('gamedata')})
0: 返回""", c=6)
        print("输入序号后按Enter即可，\n如有必要请阅读使用手册(README)：\nhttps://github.com/isHarryh/Ark-Unpacker")
    temp_dir_1 = 'temp/am_upk_operator'
    temp_dir_2 = 'temp/am_upk_enemy'
    temp_dir_3 = 'temp/am_upk_dynillust'
    while True:
        title("ArkUnpacker")
        prt_arkmodels_menu()
        order = input("> ", c=2)
        wildcard = False
        if order == '1':
            wildcard = True
        if order == '2' or wildcard:
            run_arkmodels_unpacking(['chararts', 'skinpack'], temp_dir_1)
        if order == '3' or wildcard:
            run_arkmodels_unpacking(['battle/prefabs/enemies'], temp_dir_2)
        if order == '4' or wildcard:
            run_arkmodels_unpacking(['arts/dynchars'], temp_dir_3)
        if order == '5' or wildcard:
            run_arkmodels_filtering([temp_dir_1, temp_dir_2, temp_dir_3], ['models', 'models_enemies', 'models_illust'])
        if order == '6' or wildcard:
            run_arkmodels_data_dist()
        if order in ['1', '2', '3', '4', '5', '6']:
            prt_continue()
        if order == '0':
            return

def validate_input_output_arg(parser:argparse.ArgumentParser, args:argparse.Namespace, allow_file_input:bool=False):
    if not getattr(args, 'input', None):
        parser.error("input should be defined in this mode")
    if not getattr(args, 'output', None):
        parser.error("output should be defined in this mode")
    if not allow_file_input and os.path.isfile(args.input):
        parser.error("input should be a directory, not file")
    if not os.path.isdir(args.input) and not (allow_file_input and os.path.isfile(args.input)):
        parser.error(f"input should be a {'file or ' if allow_file_input else ''}directory that exists")

def validate_logging_level_arg(parer:argparse.ArgumentParser, args:argparse.Namespace):
    if getattr(args, 'logging_level', None) is None:
        return
    if args.logging_level not in range(5):
        parser.error("invalid logging level")
    Logger.set_level(args.logging_level)

class UserInput:
    CANCEL_CMD = '*'

    @staticmethod
    def request(prompt:str="> "):
        uin = input(prompt, c=2)
        if uin == UserInput.CANCEL_CMD:
            print("  已取消任务", c=3)
            raise InterruptedError("User cancelled")
        return uin

    @staticmethod
    def request_options(options:list):
        print(f"  输入符号 \"{UserInput.CANCEL_CMD}\" 以取消任务")
        uin = UserInput.request()
        while uin not in options:
            print('  输入的选项不合法', c=3)
            uin = UserInput.request()
        return uin

    @staticmethod
    def request_path():
        print(f"  输入符号 \"{UserInput.CANCEL_CMD}\" 以取消任务，支持输入相对路径")
        uin = osp.normpath(UserInput.request())
        while not osp.exists(uin):
            print('  输入的路径不存在', c=3)
            uin = osp.normpath(UserInput.request())
        return uin

    @staticmethod
    def request_yes_or_no(default:bool):
        print(f"  输入符号 \"{UserInput.CANCEL_CMD}\" 以取消任务")
        uin = UserInput.request().strip().lower()
        if default:
            return False if uin == 'n' else True
        else:
            return True if uin == 'y' else False

if __name__ == '__main__':
    try:
        Logger.set_instance(Config.get('log_file'), Config.get('log_level'))
        Logger.info("CI: Initialized")
        parser = ArgParser.INSTANCE
        print('')
        args = parser.parse_args()
        if getattr(args, 'mode', None) is None:
            # No argument input -> ENTER -> Interactive CLI mode
            while True:
                try:
                    title("ArkUnpacker")
                    prt_homepage()
                    order = input("> ", c=2)
                    if order == '1':
                        run_quickaccess()
                        prt_continue()
                    elif order == '2':
                        run_custom_resolve_ab()
                        prt_continue()
                    elif order == '3':
                        run_custom_combine_image()
                        prt_continue()
                    elif order == '4':
                        run_custom_textasset_decode()
                        prt_continue()
                    elif order == '5':
                        run_arkmodels_workflow()
                    elif order == '0':
                        print("\n用户退出")
                        break
                except InterruptedError as arg:
                    Logger.warn("CI: Program was slightly interrupted by user.")
                    print("\n[InterruptedError] 用户轻度中止", c=3)
        else:
            # Has arguments input -> GOTO -> The specified mode
            validate_logging_level_arg(parser, args)
            if args.mode == 'ab':
                validate_input_output_arg(parser, args, allow_file_input=True)
                AU_Rs.main(args.input, args.output, args.d, args.image, args.text, args.audio, args.spine, args.group)
            elif args.mode == 'cb':
                validate_input_output_arg(parser, args)
                AU_Cb.main(args.input, args.output, args.d)
            elif args.mode == 'fb':
                validate_input_output_arg(parser, args)
                AU_Fb.main(args.input, args.output, args.d)
    # Global error handlers
    except SystemExit as arg:
        Logger.info(f"CI: Program received explicit exit code {arg.code}")
        print("\n[SystemExit] 显式退出程序", c=3)
        exit(arg.code)
    except KeyboardInterrupt as arg:
        Logger.error("CI: Program was forcibly interrupted by user.")
        print("\n[KeyboardInterrupt] 用户强制中止", c=1, s=7)
        print(stacktrace(), c=3)
        exit(1)
    except ArgParser.ArgParserFailure as arg:
        Logger.error(f"CI: Program failed ti parse input arguments, {arg}")
        print(parser.format_usage())
        print("[ArgParserFailure] 命令行参数解析失败", c=1, s=7)
        print(f"{parser.prog} failed to parse arguments", c=1)
        print(arg, c=3)
        exit(2)
    except BaseException as arg:
        Logger.error(f"CI: Oops! Unexpected error occurred: {stacktrace()}")
        print(f"\n[{type(arg).__name__}] 发生了未处理的异常", c=1, s=7)
        print(stacktrace(), c=3)
        input("> 按Enter退出...", c=1)
        exit(1)
    exit(0)
