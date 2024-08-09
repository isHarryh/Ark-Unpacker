# -*- coding: utf-8 -*-
# Copyright (c) 2022-2024, Harry Huang
# @ BSD 3-Clause License
import re
import shutil
import os.path as osp

from .utils.Config import Config, PerformanceLevel
from .utils.GlobalMethods import print, rmdir, get_dirlist
from .utils.Logger import Logger
from .utils.SaverUtils import SafeSaver
from .utils.TaskUtils import ThreadCtrl, Counter, UICtrl, TimeRecorder


def collect_models(upkdir:str, destdir:str, do_del:bool, on_finished:staticmethod, on_collected:staticmethod):
    error_occurred = False
    for model_type_dir in get_dirlist(upkdir, max_depth=1):
        model_type:str = osp.basename(model_type_dir) # Sub dir of one model type
        for model_dir in get_dirlist(model_type_dir, max_depth=1):
            model:str = osp.basename(model_dir) # Sub dir of one determined model
            if not model.islower():
                # To solve model typo caused by Arknights side
                model = model.lower()
                Logger.info(f"CollectModels: \"{model_dir}\" may has a typo name")
            try:
                newname = None
                if model_type.startswith('Building') and re.match(r'(build_)?char_', model):
                    newname = re.match(r'(build_)?char_(\d+_[0-9a-zA-Z]+(_[0-9a-zA-Z#]+)?)', model).group(2)
                elif model_type.startswith('Battle') and re.match(r'enemy_', model):
                    newname = re.match(r'enemy_(\d+_[0-9a-zA-Z]+(_\d+)?)', model).group(1)
                elif model_type.startswith('DynIllust') and re.match(r'dyn_illust_char_', model):
                    newname = "dyn_illust_" + re.match(r'dyn_illust_char_(\d+_[0-9a-zA-Z]+(_[0-9a-zA-Z#]+)?)', model).group(1)
                if newname:
                    # Move
                    dest = osp.join(destdir, newname)
                    Logger.debug(f"CollectModels: \"{model_dir}\" -> \"{dest}\"")
                    shutil.copytree(model_dir, dest, dirs_exist_ok=True)
                    rmdir(model_dir)
                    if on_collected:
                        on_collected()
                else:
                    # Not matched any rules
                    pass
            except Exception as arg:
                error_occurred = True
                Logger.error(f"CollectModels: Error occurred while handling \"{model_dir}\": Exception{type(arg)} {arg}")
    if do_del and not error_occurred:
        rmdir(upkdir)
    if on_finished:
        on_finished()

########## Main-主程序 ##########
def main(srcdirs:"list[str]", destdirs:"list[str]"):
    """Collects the Spine models from the source directories to the destination directories accordingly.
    The structure of the source directory is shown below.

    ```
    ├─source_dir
    │  ├─unpacked_dir
    │  │  ├─model_type_dir
    │  │  │  ├─model_dir
    │  │  │  │  ├─files
    ```

    :param srcdirs: Source directories list;
    :param destdirs: Destination directories list;
    :rtype: None;
    """
    print("\n正在解析目录...", s=1)
    Logger.info("CollectModels: Reading directories...")
    if len(srcdirs) != len(destdirs):
        Logger.error("CollectModels: Arguments error")
        print("参数错误", c=3)
        return

    flist = [] # [(upkdir, destdir), ...]
    for srcdir, destdir in zip(srcdirs, destdirs):
        print(f"\t正在读取目录 {srcdir}")
        for upkdir in get_dirlist(srcdir, max_depth=1):
            flist.append((upkdir, destdir))

    thread_ctrl = ThreadCtrl(PerformanceLevel.get_thread_limit(Config.get('performance_level')))
    collected = Counter()
    ui = UICtrl()
    recorder = TimeRecorder()
    recorder.update_dest(1, len(flist))
    on_finished = lambda: recorder.done_once(1)
    on_collected = collected.update

    ui.reset()
    ui.loop_start()
    for upkdir, destdir in flist:
        #(i stands for a source dir's path)
        ui.request([
            "正在分拣模型...",
            recorder.get_progress_str(),
            f"当前搜索：\t{osp.basename(upkdir)}",
            f"累计分拣：\t{collected.now()}",
            f"剩余时间：\t{recorder.get_eta_str()}",
        ])
        ###
        thread_ctrl.run_subthread(collect_models, (upkdir, destdir, True, on_finished, on_collected), \
            name=f"CmThread:{id(upkdir)}")

    ui.reset()
    ui.loop_stop()
    while thread_ctrl.count_subthread() or not SafeSaver.get_instance().completed() or recorder.get_progress() < 1:
        ui.request([
            "正在分拣模型...",
            recorder.get_progress_str(),
            f"累计分拣：\t{collected.now()}",
            f"剩余时间：\t{recorder.get_eta_str()}",
        ])
        ui.refresh(post_delay=0.1)

    ui.loop_stop()
    ui.reset()
    print("\n分拣模型结束!", s=1)
    print(f"  累计分拣 {collected.now()} 套模型")
    print(f"  此项用时 {round(recorder.get_rt(), 1)} 秒")
