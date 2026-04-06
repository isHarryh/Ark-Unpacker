# Copyright (c) 2022-2026, Harry Huang
# @ BSD 3-Clause License
from typing import Callable, Sequence

import glob
import os.path as osp
import re
import shutil
import time

from .ui.RichCLI import RichCLI
from .ui.TaskLive import TaskDetailField, TaskLiveView, TaskValueField
from .ResolveSpine import SpineType
from .utils.GlobalMethods import rmdir
from .utils.Logger import Logger
from .utils.SaverUtils import SafeSaver
from .utils.TaskUtils import ThreadCtrl, Counter, TaskReporter, TaskReporterTracker

CLI = RichCLI.get_instance()


PATTERN_BUILDING = re.compile(r"^(build_)?char_(\d+_[0-9a-zA-Z]+(_[0-9a-zA-Z#]+)?)$")
PATTERN_ENEMY = re.compile(r"^enemy_(\d+_[0-9a-zA-Z]+(_\d+)?)$")
PATTERN_ILLUST = re.compile(r"^dyn_illust_char_(\d+_[0-9a-zA-Z]+(_[0-9a-zA-Z#]+)?)$")


def collect_models(
    upkdir: str,
    destdir: str,
    do_del: bool,
    on_finished: Callable,
    on_collected: Callable,
):
    error_occurred = False
    for model_type_dir in glob.iglob(osp.join(glob.escape(upkdir), "*")):
        if not osp.isdir(model_type_dir):
            continue
        model_type: str = osp.basename(model_type_dir)  # Sub dir of one model type
        for model_dir in glob.iglob(osp.join(glob.escape(model_type_dir), "*")):
            if not osp.isdir(model_dir):
                continue
            model: str = osp.basename(model_dir)  # Sub dir of one determined model
            if not model.islower():
                # To solve model typo caused by Arknights side
                model = model.lower()
                Logger.debug(f'CollectModels: Found "{model_dir}" has uppercase char')
            try:
                newname = None
                if model_type == SpineType.BUILDING.value and PATTERN_BUILDING.match(model):
                    newname = PATTERN_BUILDING.match(model).group(2)  # type: ignore
                elif model_type in [
                    SpineType.BATTLE_FRONT.value,
                    SpineType.BATTLE_BACK.value,
                ] and PATTERN_ENEMY.match(model):
                    newname = PATTERN_ENEMY.match(model).group(1)  # type: ignore
                elif model_type == SpineType.DYN_ILLUST.value and PATTERN_ILLUST.match(model):
                    newname = "dyn_illust_" + PATTERN_ILLUST.match(model).group(1)  # type: ignore

                if newname:
                    # Move
                    dest = osp.join(destdir, newname)
                    Logger.debug(f'CollectModels: Moving "{model_dir}" -> "{dest}"')
                    shutil.copytree(model_dir, dest, dirs_exist_ok=True)
                    rmdir(model_dir)
                    if on_collected:
                        on_collected()
                else:
                    # Not match any rules
                    Logger.debug(f'CollectModels: Passed "{model_dir}", no rule matched')
            except Exception as arg:
                error_occurred = True
                Logger.error(f'CollectModels: Error occurred while handling "{model_dir}": Exception{type(arg)} {arg}')

    if do_del and not error_occurred:
        rmdir(upkdir)
    if on_finished:
        on_finished()


########## Main-主程序 ##########
def main(srcdirs: Sequence[str], destdirs: Sequence[str]):
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
    Logger.reset_stats()

    collected = Counter()
    current_stage = TaskValueField("阶段", "正在解析目录")
    current_search = TaskValueField("当前搜索")
    panel = TaskLiveView("正在分拣模型...", progress_getter=lambda: 0.0)
    panel.set_detail_fields(
        [
            current_stage,
            current_search,
            TaskDetailField("累计分拣", collected.now),
            TaskDetailField("运行状态统计", Logger.to_ew_stats_str),
        ]
    )
    panel.start()

    try:
        Logger.info("CollectModels: Reading directories...")
        if len(srcdirs) != len(destdirs):
            Logger.error("CollectModels: Arguments error")
            CLI.show_error("参数错误", "源目录与目标目录数量不一致。")
            return

        flist = []  # [(upkdir, destdir), ...]
        for srcdir, destdir in zip(srcdirs, destdirs):
            current_stage.set_value("正在读取目录")
            current_search.set_value(srcdir)
            panel.update()
            for upkdir in glob.iglob(osp.join(glob.escape(srcdir), "*")):
                if osp.isdir(upkdir):
                    flist.append((upkdir, destdir))

        thread_ctrl = ThreadCtrl()
        tr_finished = TaskReporter(1, len(flist))
        tracker = TaskReporterTracker(tr_finished)
        panel.bind_tracker(tracker)
        current_stage.set_value("正在分拣模型")

        for upkdir, destdir in flist:
            current_search.set_value(osp.basename(upkdir))
            panel.update()
            thread_ctrl.run_subthread(
                collect_models,
                (upkdir, destdir, True, tr_finished.report, collected.update),
                name=f"CmThread:{id(upkdir)}",
            )

        current_search.set_value(None)
        current_stage.set_value("正在等待任务完成")
        while thread_ctrl.count_subthread() or not SafeSaver.get_instance().completed() or tracker.get_progress() < 1:
            panel.update()
            time.sleep(0.1)
    finally:
        panel.stop()

    CLI.show_summary(
        "分拣模型结束",
        [
            ("累计分拣", f"{collected.now()} 套模型"),
            ("耗时", f"{round(tracker.get_rt(), 1)} 秒"),
        ],
    )
