# Copyright (c) 2022-2026, Harry Huang
# @ BSD 3-Clause License
from typing import Callable

import glob
import json
import os.path as osp
import threading
import time
from io import BytesIO
from pydub import AudioSegment

from .ui.RichCLI import RichCLI
from .ui.TaskLive import TaskDetailField, TaskLiveView, TaskValueField
from .utils.Config import Config
from .utils.GlobalMethods import rmdir
from .utils.Logger import Logger
from .utils.SaverUtils import SafeSaver
from .utils.TaskUtils import ThreadCtrl, Counter, TaskReporter, TaskReporterTracker

_INTERNAL_LOCK = threading.Lock()
CLI = RichCLI.get_instance()


class FixedFloat(float):
    def __init__(self, f_str: str):
        self._s = f_str

    def __repr__(self):
        return self._s

    def __float__(self):
        return self


def collect_voice(
    upkdir: str,
    destdir: str,
    do_del: bool,
    force_std_name: bool,
    info_merged: dict,
    on_finished: Callable,
    on_collected: Callable,
):
    global _INTERNAL_LOCK
    ori_name = osp.basename(upkdir)
    std_name = "_".join(ori_name.split("_")[:3]) if force_std_name else ori_name
    voice_merged: AudioSegment = AudioSegment.empty()
    duration_merged = 0.0
    clips = []
    # For each audio file unpacked
    for file in sorted(i for i in glob.iglob(osp.join(glob.escape(upkdir), "*")) if osp.isfile(i)):
        name, ext = osp.splitext(osp.basename(file))
        # Ensure the audio file is supported
        if not ext.lower() == ".wav":
            Logger.warn(f'CollectVoice: Unexpected file type "{ext}"')
            continue
        if not name.startswith("CN_"):
            Logger.info(f'CollectVoice: Unsupported voice type at "{file}"')
            continue
        # Merge this audio file
        voice_clip: AudioSegment = AudioSegment.from_file(file)
        duration_clip = voice_clip.frame_count() / voice_clip.frame_rate
        clips.append(
            {
                "name": name,
                "start": FixedFloat(f"{duration_merged:6f}"),  # Start time (second)
            }
        )
        voice_merged += voice_clip
        duration_merged += duration_clip
        # Logger.debug(f"CollectVoice: Merged \"{name}\" from \"{osp.basename(upkdir)}\"")

    if clips:
        # Save the final audio file
        Logger.debug(f'CollectVoice: Completed collection at "{ori_name}", {len(clips)} clips merged')
        voice_io = BytesIO()
        voice_merged.export(voice_io, format="ogg", parameters=["-q:a", str(3)])
        voice_bytes = voice_io.read()
        SafeSaver.save_bytes(voice_bytes, destdir, std_name, ".ogg")
        # Post processing
        if on_collected:
            on_collected()
        with _INTERNAL_LOCK:
            if info_merged is not None:
                info_merged[std_name] = {
                    "size": len(voice_bytes),
                    "duration": FixedFloat(f"{duration_merged:6f}"),
                    "clips": clips,
                }
    else:
        Logger.warn(f'CollectVoice: Collection not performed at "{ori_name}"')

    if do_del:
        rmdir(upkdir)
    if on_finished:
        on_finished()


########## Main-主程序 ##########
def main(srcdir: str, destdir: str, force_std_name: bool):
    """Collects the voice files from the source directory to the destination directory.
    The structure of the source directory is shown below.

    ```
    ├─source_dir
    │  ├─unpacked_dir
    │  │  ├─files (typically .wav)
    ```

    :param srcdir: Source directory;
    :param destdir: Destination directory;
    :param force_std_name: Forces the keys to use standard character name;
    :rtype: None;
    """
    Logger.reset_stats()

    collected = Counter()
    current_stage = TaskValueField("阶段", "正在解析目录")
    current_search = TaskValueField("当前搜索")
    panel = TaskLiveView("正在分拣语音...", progress_getter=lambda: 0.0)
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
        Logger.info("CollectVoice: Reading directories...")
        flist = []  # [(upkdir, destdir), ...]
        current_stage.set_value("正在读取目录")
        current_search.set_value(srcdir)
        panel.update()
        for upkdir in glob.iglob(osp.join(glob.escape(srcdir), "*")):
            if osp.isdir(upkdir):
                flist.append((upkdir, destdir))
        flist = list(filter(lambda x: osp.basename(x[0]).startswith("char_"), flist))
        info_merged = {}

        thread_ctrl = ThreadCtrl()
        tr_finished = TaskReporter(1, len(flist))
        tracker = TaskReporterTracker(tr_finished)
        panel.bind_tracker(tracker)
        current_stage.set_value("正在分拣语音")

        for upkdir, destdir in flist:
            current_search.set_value(osp.basename(upkdir))
            panel.update()
            thread_ctrl.run_subthread(
                collect_voice,
                (
                    upkdir,
                    destdir,
                    False,
                    force_std_name,
                    info_merged,
                    tr_finished.report,
                    collected.update,
                ),
                name=f"CvThread:{id(upkdir)}",
            )

        current_search.set_value(None)
        current_stage.set_value("正在等待任务完成")
        while thread_ctrl.count_subthread() or not SafeSaver.get_instance().completed() or tracker.get_progress() < 1:
            panel.update()
            time.sleep(0.1)
    finally:
        panel.stop()

    if len(info_merged):
        json.dump(
            info_merged,
            open(
                osp.join(destdir, "voice_data_part.json"),
                "w",
                encoding=Config.get("export_encoding"),
            ),
            indent=Config.get("export_json_indent"),
            ensure_ascii=False,
        )
        Logger.info("CollectVoice: Saved voice data")

    CLI.show_summary(
        "分拣语音结束",
        [
            ("累计分拣", f"{collected.now()} 套语音"),
            ("耗时", f"{round(tracker.get_rt(), 1)} 秒"),
        ],
    )
