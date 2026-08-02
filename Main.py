# Copyright (c) 2022-2026, Harry Huang
# @ BSD 3-Clause License
import os
import os.path as osp
import sys
import time
from multiprocessing import freeze_support

from src.ui.RichCLI import MenuOption, RichCLI
from src.utils import ArgParser
from src.utils.Config import Config
from src.utils.Logger import Logger
from src.utils.GlobalMethods import stacktrace, rmdir, try_shorten_path
from src.ui.UserInput import UserInput, ParamInputSession

from src import ResolveAB as AU_Rs
from src import ResolveSpine as AU_Sp
from src import DecodeTextAsset as AU_Fb
from src import CombineRGBwithA as AU_Cb
from src import CollectModels as AU_Cm
from src import CollectVoice as AU_Cv
from src import ModelsDataDist as AU_Mdd
from src import VoiceDataDist as AU_Vdd
from src import ResolveUSM as AU_Usm

ARKUNPACKER_VERSION = "v5.1"
ARKUNPACKER_LOCAL = "zh-CN"
CLI = RichCLI.get_instance()


def prt_homepage():
    Logger.info("CI: In Homepage.")
    CLI.clear()
    os.chdir(".")
    CLI.show_menu(
        f"欢迎使用 ArkUnpacker {ARKUNPACKER_VERSION}",
        [
            MenuOption("1", "一键执行", "对当前文件夹依次执行资源解包与图片合并"),
            MenuOption("2", "自定义资源解包", "批量解包 AB 文件并导出指定类型的资源"),
            MenuOption("3", "自定义图片合并", "自动匹配 RGB-Alpha 图片并导出合并图片"),
            MenuOption("4", "自定义文本资源解码", "解码 FlatBuffers/AES 文本资源"),
            MenuOption("5", "自定义 Spine 模型导出", "提取和导出 Spine 模型资源"),
            MenuOption("6", "自定义 Criware USM 提取", "提取过场动画并进行格式转换"),
            MenuOption("7", "ArkModels 工具", "面向 Ark-Models 仓库更新的专用工作流"),
            MenuOption("8", "ArkVoice 工具", "面向 Ark-Voice 仓库更新的专用工作流"),
            MenuOption("0", "退出"),
        ],
    )


def prt_subtitle(msg: str):
    CLI.clear()
    os.chdir(".")
    CLI.show_section(msg)


def prt_continue():
    UserInput.press_enter_to_continue()


def warn_large_srcdir(srcdir: str, threshold: int = 10000):
    if not osp.isdir(srcdir):
        return
    count = 0
    for _, _, files in os.walk(srcdir):
        count += len(files)
        if count > threshold:
            CLI.show_notice(
                "高负载提示",
                "所选目录包含大量文件，可能导致耗时过长，并显著增加内存和存储占用。\n建议优先针对子目录分批操作。",
            )
            if not UserInput.request_yes_or_no(
                "仍要继续本次任务吗？",
                default=False,
                note="默认取消任务",
            ):
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
        CLI.show_notice(
            "目录重叠警告",
            "检测到源目录位于导出目录内部，或两者相同。这可能引发覆盖、重复扫描或不可预期的结果。",
        )
        if not UserInput.request_yes_or_no(
            "仍要继续本次任务吗？",
            default=False,
            note="默认取消任务",
        ):
            raise InterruptedError("User cancelled due to directory intersection")


def warn_ffmpeg_not_available():
    with CLI.console.status("正在检查 FFmpeg 可用性..."):
        available = AU_Usm.is_ffmpeg_available()
    if available:
        return
    CLI.show_notice(
        "FFmpeg 不可用",
        "检测到 FFmpeg 似乎不可用。\n如果尚未安装，请访问官网下载安装，并将 FFmpeg 的 bin 目录加入系统环境变量 Path。\n官网：https://ffmpeg.org/download.html",
        style="yellow",
    )
    if not UserInput.request_yes_or_no(
        "仍要继续本次任务吗？",
        default=False,
        note="默认取消",
    ):
        raise InterruptedError("User cancelled due to FFmpeg not available")


def run_quickaccess():
    Logger.info("CI: Run quick access.")
    CLI.title("ArkUnpacker - Processing")
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
    session = ParamInputSession("自定义资源解包")
    src = session.request_input_path(
        "输入路径",
        prompt="需要解包的文件或目录",
        note="接受资源目录或单个 AB 文件路径，支持相对路径",
    )
    warn_large_srcdir(src)
    destdir = session.request_output_path(
        "导出目录",
        lambda: f"Unpacked_{int(time.time())}",
        prompt="用于保存解包后文件的目录",
    )
    warn_dir_intersection(src, destdir)
    do_del = False
    if osp.isdir(destdir):
        do_del = session.request_yes_or_no(
            "清空目标目录",
            default=False,
            prompt="导出目录已存在，是否先清空？",
            note="默认保留现有内容",
        )
    session.set_bool("清空目标目录", do_del)
    separate = True
    if not osp.isfile(src):
        separate = session.request_yes_or_no(
            "按来源分组",
            default=True,
            prompt="是否按来源目录对导出结果分组？",
            note="默认分组",
        )
    session.set_bool("按来源分组", separate)
    do_them = (
        session.request(
            "需要导出的资源类型（可多选，例如 itam 或 it）",
            note="可选项：i=图片，t=文本，a=音频，m=Mesh，j=Typetree JSON",
        )
        .lower()
        .strip()
    )
    do_img = True if "i" in do_them else False
    do_txt = True if "t" in do_them else False
    do_aud = True if "a" in do_them else False
    do_mesh = True if "m" in do_them else False
    do_tree = True if "j" in do_them else False
    session.set_bool("图片", do_img)
    session.set_bool("文本", do_txt)
    session.set_bool("音频", do_aud)
    session.set_bool("Mesh", do_mesh)
    session.set_bool("Typetree JSON", do_tree)
    session.confirm_start()
    CLI.title("ArkUnpacker - Processing")
    AU_Rs.main(src, destdir, do_del, do_img, do_txt, do_aud, do_mesh, do_tree, separate)


def run_custom_combine_image():
    Logger.info("CI: Customized image combine mode.")
    session = ParamInputSession("自定义合并图片")
    rootdir = session.request_input_path(
        "输入目录",
        prompt="源图片所在的目录",
        note="需要包含待合并的 RGB/Alpha 图片，支持相对路径",
    )
    destdir = session.request_output_path(
        "导出目录",
        lambda: f"Combined_{int(time.time())}",
        prompt="保存合并结果的目录",
    )
    warn_dir_intersection(rootdir, destdir)
    do_del = False
    if osp.isdir(destdir):
        do_del = session.request_yes_or_no(
            "清空目标目录",
            default=False,
            prompt="导出目录已存在，是否先清空？",
            note="默认保留现有内容",
        )
    session.set_bool("清空目标目录", do_del)
    session.confirm_start()
    CLI.title("ArkUnpacker - Processing")
    AU_Cb.main(rootdir, destdir, do_del)


def run_custom_textasset_decode():
    Logger.info("CI: Customized textasset decoding mode.")
    session = ParamInputSession("自定义文本资源解码")
    rootdir = session.request_input_path(
        "输入目录",
        prompt="待解码的文件所在的目录",
        note="若不确定哪些文件属于 TextAsset，直接选择整个解包目录",
    )
    destdir = session.request_output_path(
        "导出目录",
        lambda: f"Decoded_{int(time.time())}",
        prompt="导出解码结果的目录",
    )
    warn_dir_intersection(rootdir, destdir)
    do_del = False
    if osp.isdir(destdir):
        do_del = session.request_yes_or_no(
            "清空目标目录",
            default=False,
            prompt="导出目录已存在，是否先清空？",
            note="默认保留现有内容",
        )
    session.set_bool("清空目标目录", do_del)
    session.confirm_start()
    CLI.title("ArkUnpacker - Processing")
    AU_Fb.main(rootdir, destdir, do_del)


def run_custom_resolve_spine():
    Logger.info("CI: Customized Spine export mode.")
    session = ParamInputSession("自定义 Spine 模型导出")
    src = session.request_input_path(
        "输入路径",
        prompt="需要解包的文件或目录",
        note="接受资源目录或单个文件路径，支持相对路径",
    )
    destdir = session.request_output_path(
        "导出目录",
        lambda: f"Spine_{int(time.time())}",
        prompt="导出 Spine 模型的目录",
    )
    warn_dir_intersection(src, destdir)
    do_del = False
    if osp.isdir(destdir):
        do_del = session.request_yes_or_no(
            "清空目标目录",
            default=False,
            prompt="导出目录已存在，是否先清空？",
            note="默认保留现有内容",
        )
    session.set_bool("清空目标目录", do_del)
    separate = True
    if not osp.isfile(src):
        separate = session.request_yes_or_no(
            "按来源分组",
            default=True,
            prompt="是否按来源目录对导出结果分组？",
            note="默认分组",
        )
    session.set_bool("按来源分组", separate)
    session.confirm_start()
    CLI.title("ArkUnpacker - Processing")
    AU_Sp.main(src, destdir, do_del, separate)


def run_custom_resolve_usm():
    Logger.info("CI: Customized Criware USM extraction mode.")
    session = ParamInputSession("自定义 Criware USM 音视频提取")
    warn_ffmpeg_not_available()
    src = session.request_input_path(
        "输入路径",
        prompt="USM 来源文件或目录",
        note="接受目录或单个 USM 文件路径，支持相对路径",
    )
    warn_large_srcdir(src)
    destdir = session.request_output_path(
        "导出目录",
        lambda: f"USM_Extracted_{int(time.time())}",
        prompt="导出输出结果的目录",
    )
    warn_dir_intersection(src, destdir)
    do_del = False
    if osp.isdir(destdir):
        do_del = session.request_yes_or_no(
            "清空目标目录",
            default=False,
            prompt="导出目录已存在，是否先清空？",
            note="默认保留现有内容",
        )
    session.set_bool("清空目标目录", do_del)
    CLI.clear()
    CLI.show_menu(
        session.title,
        [
            MenuOption("1", "仅导出音频文件"),
            MenuOption("2", "仅导出视频文件"),
            MenuOption("3", "合并音视频后导出", "（推荐）"),
        ],
        intro=[f"{name}: {value}" for name, value in session.rows],
    )
    extract_mode = UserInput.request_options(["1", "2", "3"])
    if extract_mode == "1":
        do_vid, do_aud = False, True
    elif extract_mode == "2":
        do_vid, do_aud = True, False
    else:  # extract_mode == "3"
        do_vid, do_aud = True, True
    session.set_bool("导出视频", do_vid)
    session.set_bool("导出音频", do_aud)
    session.confirm_start()
    CLI.title("ArkUnpacker - Processing")
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
                CLI.show_error("路径缺失", f"在工作目录下找不到文件夹 {i}。请确认资源目录位置或程序版本。")
                return
        dirs = and_dirs[:]
    if or_dirs is not None:
        found = False
        for i in or_dirs:
            if osp.exists(i):
                found = True
                dirs.append(i)
        if not found:
            CLI.show_error(
                "路径缺失",
                f"在工作目录下找不到以下任一文件夹：{', '.join(or_dirs)}。\n请确认资源目录位置或程序版本。",
            )
            return
    CLI.title("ArkUnpacker - Processing")
    ###
    CLI.show_stage("正在清理...")
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
            CLI.show_error(
                "路径缺失",
                f"在工作目录下找不到 {i}。请确认该文件夹位于工作目录中，或检查程序版本兼容性。",
            )
            return
    CLI.title("ArkUnpacker - Processing")
    ###
    CLI.show_stage("正在清理...")
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
            CLI.show_error(
                "路径缺失",
                f'在工作目录下找不到 {i}。请确认该文件夹直接位于工作目录中，或先执行"模型提取"。',
            )
            try:
                UserInput.request("按 Enter 强制继续")
            except InterruptedError:
                return
        else:
            dirs_.append(i)
            destdirs_.append(j)
    ###
    AU_Cm.main(dirs_, destdirs_)


def run_arkmodels_data_dist(mdd_temp_dir):
    Logger.info("CI: ArkModels dataset mode.")
    prt_subtitle("ArkModels 生成数据集")
    ###
    for i in ["models", "models_enemies", "models_illust"]:
        if not osp.exists(i):
            CLI.show_error("路径缺失", f'在工作目录下找不到 {i}。请确认您先前已运行了"模型分拣"。')
            try:
                UserInput.request("按 Enter 强制继续")
            except InterruptedError:
                return
    if not osp.exists(mdd_temp_dir):
        CLI.show_error("路径缺失", f'找不到 {mdd_temp_dir}。请确认您先前已运行了"匿名数据提取"。')
        return
    AU_Mdd.main(mdd_temp_dir)


def run_arkmodels_workflow():
    def visual(fp: str):
        return RichCLI.format_path_state(fp, osp.exists(fp))

    Logger.info("CI: In ArkModels workflow.")

    def prt_arkmodels_menu():
        CLI.clear()
        os.chdir(".")
        cwd = osp.abspath(osp.normpath(os.getcwd()))
        cwd_shortened = try_shorten_path(cwd)
        intro = []
        if cwd != cwd_shortened:
            intro.append(f"输出目录: {cwd_shortened}")
        CLI.show_menu(
            "ArkModels 提取与分拣工具",
            [
                MenuOption("1", "一键执行", "按顺序完成所有步骤"),
                MenuOption("2", "干员基建模型提取", f"{visual('chararts')}；{visual('skinpack')}"),
                MenuOption("3", "敌方战斗模型提取", f"{visual('battle/prefabs/enemies')}；{visual('refs/arts')}"),
                MenuOption("4", "动态立绘模型提取", visual("arts/dynchars")),
                MenuOption("5", "匿名数据提取", visual(AU_Mdd.ModelsDist.GAMEDATA_DIR)),
                MenuOption("6", "模型分拣"),
                MenuOption("7", "生成数据集"),
                MenuOption("0", "返回"),
            ],
            intro=intro or None,
        )

    norm_tmp_dir = lambda x: try_shorten_path(osp.abspath(osp.normpath(x)))
    temp_dir_1 = norm_tmp_dir("temp/am_upk_operator")
    temp_dir_2 = norm_tmp_dir("temp/am_upk_enemy")
    temp_dir_3 = norm_tmp_dir("temp/am_upk_dynillust")
    temp_dir_4 = norm_tmp_dir("temp/am_upk_mdd")

    while True:
        CLI.title("ArkUnpacker")
        prt_arkmodels_menu()
        order = UserInput.request_options(["0", "1", "2", "3", "4", "5", "6", "7"])
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
            run_arkmodels_data_dist(temp_dir_4)
        if order in ["1", "2", "3", "4", "5", "6", "7"]:
            prt_continue()
        if order == "0":
            return


def run_arkvoice_unpacking(dir, destdir1, destdir2, wildcard=False):
    def visual(fp: str):
        return RichCLI.format_path_state(fp, osp.exists(fp))

    Logger.info("CI: ArkVoice unpack mode.")

    def prt_arkvoice_unpacking_menu(dir, destdir1):
        CLI.clear()
        os.chdir(".")
        CLI.show_menu(
            "ArkVoice 提取与分拣工具",
            [
                MenuOption("1", "仅提取 Wav 文件", visual(dir)),
                MenuOption("2", "仅合并 Wav 为 Ogg", visual(destdir1)),
                MenuOption("3", "提取并合并"),
                MenuOption("0", "取消"),
            ],
        )

    while True:
        CLI.title("ArkUnpacker")
        prt_arkvoice_unpacking_menu(dir, destdir1)
        order = "0"
        if not wildcard:
            order = UserInput.request_options(["0", "1", "2", "3"])
        if order == "3":
            wildcard = True
        if order == "1" or wildcard:
            if not osp.exists(dir):
                CLI.show_error("路径缺失", f"在工作目录下找不到 {dir}。请确保该文件夹直接位于工作目录中。")
                return
            CLI.show_stage("正在清理...")
            rmdir(destdir1)
            CLI.title("ArkUnpacker - Processing")
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
                CLI.show_error("路径缺失", f"在工作目录下找不到 {destdir1}。请确保您已执行前置步骤。")
                return
            CLI.show_stage("正在清理...")
            rmdir(destdir2)
            CLI.title("ArkUnpacker - Processing")
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
        CLI.clear()
        os.chdir(".")
        CLI.show_menu(
            "ArkVoice 提取与分拣工具",
            [
                MenuOption("1", "一键执行", "按顺序完成所有步骤"),
                MenuOption("2", "提取并分拣日文语音", "audio/sound_beta_2/voice"),
                MenuOption("3", "提取并分拣中文语音", "audio/sound_beta_2/voice_cn"),
                MenuOption("4", "提取并分拣英文语音", "audio/sound_beta_2/voice_en"),
                MenuOption("5", "提取并分拣韩文语音", "audio/sound_beta_2/voice_kr"),
                MenuOption("6", "提取并分拣个性语音", "audio/sound_beta_2/voice_custom"),
                MenuOption("7", "生成数据集"),
                MenuOption("0", "返回"),
            ],
        )

    while True:
        CLI.title("ArkUnpacker")
        prt_arkvoice_menu()
        order = UserInput.request_options(["0", "1", "2", "3", "4", "5", "6", "7"])
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
    freeze_support()
    parser = ArgParser.INSTANCE
    try:
        Logger.set_instance(Config.get("log_file"), Config.get("log_level"))
        Logger.info("CI: Initialized")
        CLI.blank()
        args = parser.parse_args()
        parser.validate_logging_level_arg(args)
        Logger.set_level(args.logging_level)
        if getattr(args, "version", False):
            CLI.show_summary(
                "ArkUnpacker 版本信息",
                [
                    ("版本", ARKUNPACKER_VERSION),
                    ("语言", ARKUNPACKER_LOCAL),
                ],
                border_style="cyan",
            )
            sys.exit(0)
        if getattr(args, "mode", None) is None:
            # No argument input -> ENTER -> Interactive CLI mode
            while True:
                try:
                    CLI.title("ArkUnpacker")
                    prt_homepage()
                    order = UserInput.request_options(["0", "1", "2", "3", "4", "5", "6", "7", "8"])
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
                        break
                except InterruptedError as arg:
                    Logger.warn("CI: Program was slightly interrupted by user.")
                    CLI.show_notice("轻度中止", str(arg), style="yellow")
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
        if arg.code not in (0, None):
            CLI.blank()
            CLI.show_error("程序非常规退出", f"程序以显式退出码结束：{arg.code}")
        sys.exit(arg.code)
    except KeyboardInterrupt as arg:
        Logger.error("CI: Program was forcibly interrupted by user.")
        CLI.blank()
        CLI.show_error("用户强制中止", "检测到 KeyboardInterrupt，已强制退出程序。")
        sys.exit(1)
    except ArgParser.ArgParserFailure as arg:
        Logger.error(f"CI: Program failed ti parse input arguments, {arg}")
        CLI.blank()
        CLI.show_error("命令行参数解析失败", str(arg))
        CLI.show_dim(parser.format_usage().rstrip())
        sys.exit(2)
    except BaseException as arg:
        Logger.error(f"CI: Oops! Unexpected error occurred: {stacktrace()}")
        CLI.blank()
        CLI.show_error("发生了未处理的异常", f"{type(arg).__name__}: {arg}")
        CLI.print_exception()
        UserInput.press_enter_to_exit()
        sys.exit(1)
    sys.exit(0)
