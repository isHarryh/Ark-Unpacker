# Copyright (c) 2022-2026, Harry Huang
# @ BSD 3-Clause License
import os
import os.path as osp
import sys
import time

from src.utils import ArgParser
from src.utils.Config import Config
from src.utils.Logger import Logger
from src.utils.GlobalMethods import color, print, clear, title, stacktrace, rmdir, try_shorten_path
from src.utils.UserInput import UserInput

from src import ResolveAB as AU_Rs
from src import ResolveSpine as AU_Sp
from src import DecodeTextAsset as AU_Fb
from src import CombineRGBwithA as AU_Cb
from src import CollectModels as AU_Cm
from src import CollectVoice as AU_Cv
from src import ModelsDataDist as AU_Mdd
from src import VoiceDataDist as AU_Vdd
from src import ResolveUSM as AU_Usm

ARKUNPACKER_VERSION = "v4.5"
ARKUNPACKER_LOCAL = "zh-CN"


def prt_homepage():
    Logger.info("CI: In Homepage.")
    clear()
    os.chdir(".")
    print(f"欢迎使用ArkUnpacker {ARKUNPACKER_VERSION}", s=1)
    print("=" * 20)
    print(
        """模式选择：
1: 一键执行
2: 自定义资源解包
3: 自定义图片合并
4: 自定义文本资源解码
5: 自定义Spine模型导出
6: 自定义Criware USM音视频提取
7: ArkModels提取与分拣工具
8: ArkVoice提取与分拣工具
0: 退出""",
        c=6,
    )
    print(
        "输入序号后按Enter即可，\n如果您不清楚以上功能的含义，强烈建议您先阅读使用手册(README)：\nhttps://github.com/isHarryh/Ark-Unpacker "
    )


def prt_subtitle(msg: str):
    clear()
    os.chdir(".")
    print("=" * 10, s=1)
    print(msg, s=1)
    print("=" * 10, s=1)


def prt_continue():
    UserInput.request("\n> 按Enter以继续...")


def warn_large_srcdir(srcdir: str, threshold: int = 10000):
    if not osp.isdir(srcdir):
        return
    count = 0
    for _, _, files in os.walk(srcdir):
        count += len(files)
        if count > threshold:
            print("\n注意，所选的目录包含大量文件！", c=3)
            print("  这可能导致耗时过长、占用大量内存和存储空间。")
            print("  我们建议您仅对部分目录进行单独的操作。")
            print("  您仍要继续本次任务吗？")
            print("  请选择：[y]继续任务，[n]取消任务(默认)", c=3)
            uin = UserInput.request().strip().lower()
            if uin != "y":
                print("  已取消任务", c=3)
                raise InterruptedError("User cancelled due to large directory")
            break


def warn_dir_intersection(srcdir: str, destdir: str):
    srcdir = os.path.abspath(srcdir)
    destdir = os.path.abspath(destdir)

    def is_subdir(parent, child):
        parent = os.path.join(parent, "")
        child = os.path.join(child, "")
        return os.path.commonprefix([parent, child]) == parent

    if srcdir == destdir or is_subdir(destdir, srcdir):
        print("\n注意，源目录包含于导出目录中！", c=3)
        print("  这可能导致数据覆盖等意外行为。")
        print("  您仍要继续本次任务吗？")
        print("  请选择：[y]继续任务，[n]取消任务(默认)", c=3)
        uin = UserInput.request().strip().lower()
        if uin != "y":
            print("  已取消任务", c=3)
            raise InterruptedError("User cancelled due to directory intersection")


def warn_ffmpeg_not_available():
    print("正在检查FFmpeg可用性...")
    if AU_Usm.is_ffmpeg_available():
        print("  通过！", c=2)
        return
    print("  失败！", c=1)
    print("\n注意，检测到FFmpeg似乎不可用！", c=3)
    print("  如果您未在计算机中安装FFmpeg，请访问它的官网来下载合适的版本")
    print("  并将FFmpeg的bin目录添加到系统环境变量Path。")
    print("  FFmpeg 官网：https://ffmpeg.org/download.html\n")
    print("  您仍要继续本次任务吗？")
    print("  请选择：[y]继续任务，[n]取消任务(默认)", c=3)
    uin = UserInput.request().strip().lower()
    if uin != "y":
        print("  已取消任务", c=3)
        raise InterruptedError("User cancelled due to FFmpeg not available")


def run_quickaccess():
    Logger.info("CI: Run quick access.")
    title("ArkUnpacker - Processing")
    warn_large_srcdir(".")
    destdir = f"Unpacked_{int(time.time())}"
    ###
    prt_subtitle("步骤1|资源解包")
    time.sleep(1)
    AU_Rs.main(".", destdir)
    ###
    prt_subtitle("步骤2|合并图片")
    time.sleep(1)
    AU_Cb.main(destdir, f"Combined_{int(time.time())}")


def run_custom_resolve_ab():
    Logger.info("CI: Customized unpack mode.")
    prt_subtitle("自定义资源解包")
    ###
    print("\n请输入要解包的目录或文件路径")
    src = UserInput.request_input_path()
    print("解包目标路径：", c=2)
    print(f"  {src}", c=6)
    warn_large_srcdir(src)
    ###
    print("\n请输入导出目录的路径")
    destdir = UserInput.request_output_path(default_generator=lambda: f"Unpacked_{int(time.time())}")
    print("导出目录路径：", c=2)
    print(f"  {destdir}", c=6)
    warn_dir_intersection(src, destdir)
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
    print("  [i]图片(纹理)，[t]文本，[a]音频，[m]3D模型(Mesh)，[j]Typetree(JSON)", c=3)
    print('  可多选，示例输入："itam"，"it"')
    do_them = UserInput.request().lower()
    do_img = True if "i" in do_them else False
    do_txt = True if "t" in do_them else False
    do_aud = True if "a" in do_them else False
    do_mesh = True if "m" in do_them else False
    do_tree = True if "j" in do_them else False
    print(
        f"  [{'√' if do_img else '×'}]图片(纹理)，[{'√' if do_txt else '×'}]文本，[{'√' if do_aud else '×'}]音频，[{'√' if do_mesh else '×'}]3D模型(Mesh)，[{'√' if do_tree else '×'}]Typetree(JSON)",
        c=6,
    )
    ###
    prt_continue()
    title("ArkUnpacker - Processing")
    AU_Rs.main(src, destdir, do_del, do_img, do_txt, do_aud, do_mesh, do_tree, separate)


def run_custom_combine_image():
    Logger.info("CI: Customized image combine mode.")
    prt_subtitle("自定义合并图片")
    ###
    print("\n请输入源图片目录的路径")
    rootdir = UserInput.request_input_path()
    print("源图片目录路径：")
    print(f"  {rootdir}", c=6)
    ###
    print("\n请输入导出的目的地")
    destdir = UserInput.request_output_path(default_generator=lambda: f"Combined_{int(time.time())}")
    print("您选择的导出目录是：")
    print(f"  {destdir}", c=6)
    warn_dir_intersection(rootdir, destdir)
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
    rootdir = UserInput.request_input_path()
    print(" 源文件的目录是：")
    print(f"  {rootdir}", c=6)
    ###
    print("\n请输入导出的目的地")
    destdir = UserInput.request_output_path(default_generator=lambda: f"Decoded_{int(time.time())}")
    print("您选择的导出目录是：")
    print(f"  {destdir}", c=6)
    warn_dir_intersection(rootdir, destdir)
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


def run_custom_resolve_spine():
    Logger.info("CI: Customized Spine export mode.")
    prt_subtitle("自定义Spine模型导出")
    ###
    print("\n请输入要导出的目录或文件路径")
    src = UserInput.request_input_path()
    print("导出目标路径：", c=2)
    print(f"  {src}", c=6)
    ###
    print("\n请输入导出目录的路径")
    destdir = UserInput.request_output_path(default_generator=lambda: f"Spine_{int(time.time())}")
    print("导出目录路径：", c=2)
    print(f"  {destdir}", c=6)
    warn_dir_intersection(src, destdir)
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
    prt_continue()
    title("ArkUnpacker - Processing")
    AU_Sp.main(src, destdir, do_del, separate)


def run_custom_resolve_usm():
    Logger.info("CI: Customized Criware USM extraction mode.")
    prt_subtitle("自定义Criware USM音视频提取")
    ###
    warn_ffmpeg_not_available()
    print("\n请输入要处理的USM文件的目录路径")
    src = UserInput.request_input_path()
    print("USM文件路径：", c=2)
    print(f"  {src}", c=6)
    warn_large_srcdir(src)
    ###
    print("\n请输入导出目录的路径")
    destdir = UserInput.request_output_path(default_generator=lambda: f"USM_Extracted_{int(time.time())}")
    print("导出目录路径：", c=2)
    print(f"  {destdir}", c=6)
    warn_dir_intersection(src, destdir)
    ###
    do_del = False
    if osp.isdir(destdir):
        print("\n该导出目录已存在，您要删除它里面的全部文件吗？")
        print("  请!慎重!选择：[y]删除，[n]保留(默认)", c=3)
        do_del = UserInput.request_yes_or_no(False)
    ###
    print("\n请选择提取方式")
    print("  [1]仅导出音频文件", c=3)
    print("  [2]仅导出视频文件", c=3)
    print("  [3]将音频与视频合并之后导出", c=3)
    extract_mode = UserInput.request_options(["1", "2", "3"])
    print("提取方式：", c=2)
    if extract_mode == "1":
        print("  仅导出音频文件", c=6)
        do_vid, do_aud = False, True
    elif extract_mode == "2":
        print("  仅导出视频文件", c=6)
        do_vid, do_aud = True, False
    else:  # extract_mode == "3"
        print("  将音频与视频合并之后导出", c=6)
        do_vid, do_aud = True, True
    ###
    prt_continue()
    title("ArkUnpacker - Processing")
    AU_Usm.main(src, destdir, do_del, do_vid, do_aud)


def run_arkmodels_unpacking(*, and_dirs=None, or_dirs=None, destdir):
    Logger.info("CI: ArkModels unpack mode.")
    prt_subtitle("ArkModels 模型提取")
    ###
    assert (and_dirs is not None) ^ (or_dirs is not None)
    dirs = []
    if and_dirs is not None:
        for i in and_dirs:
            if not osp.exists(i):
                print(
                    f"在工作目录下找不到文件夹 {i}"
                    "请确保该文件夹直接位于工作目录中。"
                    "也有可能是本程序版本与您的资源版本不兼容，可尝试获取其他版本的程序。",
                    c=3,
                )
                return
        dirs = and_dirs[:]
    if or_dirs is not None:
        found = False
        for i in or_dirs:
            if osp.exists(i):
                found = True
                dirs.append(i)
        if not found:
            print(
                f"在工作目录下找不到以下任一文件夹：{', '.join(or_dirs)}\n"
                "请确保其中至少有一个文件夹直接位于工作目录中。"
                "也有可能是本程序版本与您的资源版本不兼容，可尝试获取其他版本的程序。",
                c=3,
            )
            return
    title("ArkUnpacker - Processing")
    ###
    print("正在清理...")
    rmdir(destdir)
    for i in dirs:
        if "refs/arts" == i:
            AU_Sp.main(i, destdir, do_del=False, separate=True, pfb_dir="battle")
        else:
            AU_Sp.main(i, destdir, do_del=False, separate=True, pfb_dir=None)


def run_arkmodels_anon_unpacking(dirs, destdir):
    Logger.info("CI: ArkModels unpack mode.")
    prt_subtitle("ArkModels 模型提取")
    ###
    for i in dirs:
        if not osp.exists(i):
            print(
                f"在工作目录下找不到 {i}，请确保该文件夹直接位于工作目录中。也有可能是本程序版本与您的资源版本不兼容，可尝试获取其他版本的程序。",
                c=3,
            )
            return
    title("ArkUnpacker - Processing")
    ###
    print("正在清理...")
    rmdir(destdir)
    for i in dirs:
        AU_Rs.main(
            i,
            destdir,
            do_del=False,
            do_img=False,
            do_txt=True,
            do_aud=False,
            separate=True,
        )


def run_arkmodels_filtering(dirs, destdirs):
    Logger.info("CI: ArkModels file filter mode.")
    prt_subtitle("ArkModels 文件分拣")
    ###
    dirs_ = []
    destdirs_ = []
    for i, j in zip(dirs, destdirs):
        if not osp.exists(i):
            print(
                f'在工作目录下找不到 {i}，请确保该文件夹直接位于工作目录中。也有可能是您事先没有进行"模型提取"的步骤。',
                c=3,
            )
            UserInput.request('> 输入符号 "*" 以取消任务，或直接按Enter以强制继续')
        else:
            dirs_.append(i)
            destdirs_.append(j)
    ###
    AU_Cm.main(dirs_, destdirs_)


def run_arkmodels_data_dist():
    Logger.info("CI: ArkModels dataset mode.")
    prt_subtitle("ArkModels 生成数据集")
    ###
    for i in ["models", "models_enemies", "models_illust"]:
        if not osp.exists(i):
            print(f'在工作目录下找不到 {i}，请确认您先前已运行了"模型分拣"。', c=3)
            UserInput.request('> 输入符号 "*" 以取消任务，或直接按Enter以强制继续')
    if not osp.exists(AU_Mdd.ModelsDist.TEMP_DIR):
        print(
            f'在工作目录下找不到 {AU_Mdd.ModelsDist.TEMP_DIR}，请确认您先前已运行了"匿名数据提取"。',
            c=3,
        )
        return
    AU_Mdd.main()


def run_arkmodels_workflow():
    def visual(fp: str, default_c: int = 6):
        return f"{color(2 if osp.exists(fp) else 3)}{fp}{color(default_c)}"

    Logger.info("CI: In ArkModels workflow.")

    def prt_arkmodels_menu():
        clear()
        os.chdir(".")
        print("ArkModels提取与分拣工具", s=1)
        print("=" * 20)
        print(
            """ArkModels是作者建立的明日方舟Spine模型仓库（https://github.com/isHarryh/Ark-Models），以下功能专门为ArkModels仓库的更新而设计。
运行部分功能之前，需要确保括号内所示的资源文件夹已位于程序所在目录中。"""
        )
        cwd = osp.abspath(osp.normpath(os.getcwd()))
        cwd_shortened = try_shorten_path(cwd)
        if cwd != cwd_shortened:
            print("为了缩短文件路径长度，输出文件将会保存到：", c=3)
            print(f"  {cwd_shortened}", c=3)
        print(
            f"""功能选择：
1: 一键执行
2: 干员基建模型提取 ({visual('chararts')} 和 {visual('skinpack')})
3: 敌方战斗模型提取 ({visual('battle')} 或 {visual('refs')})
4: 动态立绘模型提取 ({visual('arts')})
5: 匿名数据提取 ({visual(AU_Mdd.ModelsDist.GAMEDATA_DIR)})
6: 模型分拣
7: 生成数据集
0: 返回""",
            c=6,
        )
        print("输入序号后按Enter即可，\n如有必要请阅读使用手册(README)：\nhttps://github.com/isHarryh/Ark-Unpacker")

    norm_tmp_dir = lambda x: try_shorten_path(osp.abspath(osp.normpath(x)))
    temp_dir_1 = norm_tmp_dir("temp/am_upk_operator")
    temp_dir_2 = norm_tmp_dir("temp/am_upk_enemy")
    temp_dir_3 = norm_tmp_dir("temp/am_upk_dynillust")
    temp_dir_4 = norm_tmp_dir(AU_Mdd.ModelsDist.TEMP_DIR)

    while True:
        title("ArkUnpacker")
        prt_arkmodels_menu()
        order = UserInput.request()
        wildcard = False
        if order == "1":
            wildcard = True
        if order == "2" or wildcard:
            run_arkmodels_unpacking(
                and_dirs=["chararts", "skinpack"],
                destdir=temp_dir_1,
            )
        if order == "3" or wildcard:
            # battle/prefabs/enemies: enemy spine for game version <= v2.5.05
            # refs/arts: enemy spine for game version >= v2.5.60
            run_arkmodels_unpacking(
                or_dirs=["battle/prefabs/enemies", "refs/arts"],
                destdir=temp_dir_2,
            )
        if order == "4" or wildcard:
            run_arkmodels_unpacking(
                and_dirs=["arts/dynchars"],
                destdir=temp_dir_3,
            )
        if order == "5" or wildcard:
            run_arkmodels_anon_unpacking(
                [AU_Mdd.ModelsDist.GAMEDATA_DIR],
                temp_dir_4,
            )
        if order == "6" or wildcard:
            run_arkmodels_filtering(
                [temp_dir_1, temp_dir_2, temp_dir_3],
                ["models", "models_enemies", "models_illust"],
            )
        if order == "7" or wildcard:
            run_arkmodels_data_dist()
        if order in ["1", "2", "3", "4", "5", "6", "7"]:
            prt_continue()
        if order == "0":
            return


def run_arkvoice_unpacking(dir, destdir1, destdir2, wildcard=False):
    def visual(fp: str, default_c: int = 6):
        return f"{color(2 if osp.exists(fp) else 3)}{fp}{color(default_c)}"

    Logger.info("CI: ArkVoice unpack mode.")

    def prt_arkvoice_unpacking_menu(dir, destdir1):
        clear()
        os.chdir(".")
        print("ArkVoice提取与分拣工具", s=1)
        print("=" * 20)
        print(
            f"""模式选择：
1: 仅提取 Wav 文件 ({visual(dir)})
2: 仅合并 Wav 文件为 Ogg 文件 ({visual(destdir1)})
3: 提取与合并
0: 取消""",
            c=6,
        )

    while True:
        title("ArkUnpacker")
        prt_arkvoice_unpacking_menu(dir, destdir1)
        order = "0"
        if not wildcard:
            order = UserInput.request()
        if order == "3":
            wildcard = True
        if order == "1" or wildcard:
            if not osp.exists(dir):
                print(f"在工作目录下找不到 {dir}，请确保该文件夹直接位于工作目录中。", c=3)
                return
            print("正在清理...")
            rmdir(destdir1)
            title("ArkUnpacker - Processing")
            AU_Rs.main(
                dir,
                destdir1,
                do_del=False,
                do_img=False,
                do_txt=False,
                do_aud=True,
                separate=True,
            )
        if order == "2" or wildcard:
            if not osp.exists(destdir1):
                print(f"在工作目录下找不到 {destdir1}，请确保您已执行前置步骤。", c=3)
                return
            print("正在清理...")
            rmdir(destdir2)
            title("ArkUnpacker - Processing")
            AU_Cv.main(destdir1, destdir2, "custom" in destdir2)
        if order == "0":
            return


def run_arkvoice_data_dist():
    Logger.info("CI: ArkVoice dataset mode.")
    prt_subtitle("ArkVoice 生成数据集")
    ###
    AU_Vdd.main()


def run_arkvoice_workflow():
    Logger.info("CI: In ArkVoice workflow.")

    def prt_arkvoice_menu():
        clear()
        os.chdir(".")
        print("ArkVoice提取与分拣工具", s=1)
        print("=" * 20)
        print(
            "ArkVoice是作者建立的明日方舟语音仓库（https://github.com/isHarryh/Ark-Voice），以下功能专门为ArkVoice仓库的更新而设计。"
        )
        print(
            f"""功能选择：
1: 一键执行
2: 提取并分拣日文语音
3: 提取并分拣中文语音
4: 提取并分拣英文语音
5: 提取并分拣韩文语音
6: 提取并分拣个性语音
7: 生成数据集
0: 返回""",
            c=6,
        )
        print("输入序号后按Enter即可，\n如有必要请阅读使用手册(README)：\nhttps://github.com/isHarryh/Ark-Unpacker")

    while True:
        title("ArkUnpacker")
        prt_arkvoice_menu()
        order = UserInput.request()
        wildcard = False
        if order == "1":
            wildcard = True
        if order == "2" or wildcard:
            run_arkvoice_unpacking("audio/sound_beta_2/voice", "temp/av_upk", "voice", wildcard)
        if order == "3" or wildcard:
            run_arkvoice_unpacking("audio/sound_beta_2/voice_cn", "temp/av_upk_cn", "voice_cn", wildcard)
        if order == "4" or wildcard:
            run_arkvoice_unpacking("audio/sound_beta_2/voice_en", "temp/av_upk_en", "voice_en", wildcard)
        if order == "5" or wildcard:
            run_arkvoice_unpacking("audio/sound_beta_2/voice_kr", "temp/av_upk_kr", "voice_kr", wildcard)
        if order == "6" or wildcard:
            run_arkvoice_unpacking(
                "audio/sound_beta_2/voice_custom",
                "temp/av_upk_custom",
                "voice_custom",
                wildcard,
            )
        if order == "7" or wildcard:
            run_arkvoice_data_dist()
        if order in ["1", "2", "3", "4", "5", "6", "7"]:
            prt_continue()
        if order == "0":
            return


if __name__ == "__main__":
    parser = ArgParser.INSTANCE
    try:
        Logger.set_instance(Config.get("log_file"), Config.get("log_level"))
        Logger.info("CI: Initialized")
        print("")
        args = parser.parse_args()
        parser.validate_logging_level_arg(args)
        Logger.set_level(args.logging_level)
        if getattr(args, "mode", None) is None:
            # No argument input -> ENTER -> Interactive CLI mode
            while True:
                try:
                    title("ArkUnpacker")
                    prt_homepage()
                    order = UserInput.request()
                    if order == "1":
                        run_quickaccess()
                        prt_continue()
                    elif order == "2":
                        run_custom_resolve_ab()
                        prt_continue()
                    elif order == "3":
                        run_custom_combine_image()
                        prt_continue()
                    elif order == "4":
                        run_custom_textasset_decode()
                        prt_continue()
                    elif order == "5":
                        run_custom_resolve_spine()
                        prt_continue()
                    elif order == "6":
                        run_custom_resolve_usm()
                        prt_continue()
                    elif order == "7":
                        run_arkmodels_workflow()
                    elif order == "8":
                        run_arkvoice_workflow()
                    elif order == "0":
                        print("\n用户退出")
                        break
                except InterruptedError as arg:
                    Logger.warn("CI: Program was slightly interrupted by user.")
                    print("\n[InterruptedError] 用户轻度中止", c=3)
        else:
            # Has arguments input -> GOTO -> The specified mode
            if args.mode == "ab":
                parser.validate_input_output_arg(args, allow_file_input=True)
                AU_Rs.main(
                    args.input,
                    args.output,
                    args.d,
                    args.image,
                    args.text,
                    args.audio,
                    args.mesh,
                    args.typetree,
                    args.group,
                )
            elif args.mode == "sp":
                parser.validate_input_output_arg(args, allow_file_input=True)
                AU_Sp.main(
                    args.input,
                    args.output,
                    args.d,
                    args.group,
                )
            elif args.mode == "cb":
                parser.validate_input_output_arg(args)
                AU_Cb.main(args.input, args.output, args.d)
            elif args.mode == "fb":
                parser.validate_input_output_arg(args)
                AU_Fb.main(args.input, args.output, args.d)
            elif args.mode == "cu":
                parser.validate_input_output_arg(args, allow_file_input=True)
                do_vid = not getattr(args, "no_video", False)
                do_aud = not getattr(args, "no_audio", False)
                AU_Usm.main(
                    args.input,
                    args.output,
                    args.d,
                    do_vid,
                    do_aud,
                )
    # Global error handlers
    except SystemExit as arg:
        Logger.info(f"CI: Program received explicit exit code {arg.code}")
        print("\n[SystemExit] 显式退出程序", c=3)
        sys.exit(arg.code)
    except KeyboardInterrupt as arg:
        Logger.error("CI: Program was forcibly interrupted by user.")
        print("\n[KeyboardInterrupt] 用户强制中止", c=1, s=7)
        print(stacktrace(), c=3)
        sys.exit(1)
    except ArgParser.ArgParserFailure as arg:
        Logger.error(f"CI: Program failed ti parse input arguments, {arg}")
        print(parser.format_usage())
        print("[ArgParserFailure] 命令行参数解析失败", c=1, s=7)
        print(f"{parser.prog} failed to parse arguments", c=1)
        print(arg, c=3)
        sys.exit(2)
    except BaseException as arg:
        Logger.error(f"CI: Oops! Unexpected error occurred: {stacktrace()}")
        print(f"\n[{type(arg).__name__}] 发生了未处理的异常", c=1, s=7)
        print(stacktrace(), c=3)
        UserInput.press_enter_to_exit()
        sys.exit(1)
    sys.exit(0)
