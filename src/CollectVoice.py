# -*- coding: utf-8 -*-
# Copyright (c) 2022-2025, Harry Huang
# @ BSD 3-Clause License
import os.path as osp
import json
import threading
from io import BytesIO
from typing import Callable
from pydub import AudioSegment

from .utils.GlobalMethods import print, rmdir, get_dirlist, get_filelist
from .utils.Logger import Logger
from .utils.SaverUtils import SafeSaver
from .utils.TaskUtils import (
    ThreadCtrl,
    Counter,
    UICtrl,
    TaskReporter,
    TaskReporterTracker,
)

_INTERNAL_LOCK = threading.Lock()


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
    for file in sorted(get_filelist(upkdir, max_depth=1)):
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
        Logger.debug(
            f'CollectVoice: Completed collection at "{ori_name}", {len(clips)} clips merged'
        )
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
    print("\n正在解析目录...", s=1)
    Logger.info("CollectVoice: Reading directories...")

    flist = []  # [(upkdir, destdir), ...]
    print(f"\t正在读取目录 {srcdir}")
    for upkdir in get_dirlist(srcdir, max_depth=1):
        flist.append((upkdir, destdir))
    flist = list(filter(lambda x: osp.basename(x[0]).startswith("char_"), flist))
    info_merged = {}

    thread_ctrl = ThreadCtrl()
    collected = Counter()
    ui = UICtrl()
    tr_finished = TaskReporter(1, len(flist))
    tracker = TaskReporterTracker(tr_finished)

    ui.reset()
    ui.loop_start()
    for upkdir, destdir in flist:
        # (i stands for a source dir's path)
        ui.request(
            [
                "正在分拣语音...",
                tracker.to_progress_bar_str(),
                f"当前搜索：\t{osp.basename(upkdir)}",
                f"累计分拣：\t{collected.now()}",
                f"剩余时间：\t{tracker.to_eta_str()}",
            ]
        )
        ###
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

    ui.reset()
    ui.loop_stop()
    while (
        thread_ctrl.count_subthread()
        or not SafeSaver.get_instance().completed()
        or tracker.get_progress() < 1
    ):
        ui.request(
            [
                "正在分拣语音...",
                tracker.to_progress_bar_str(),
                f"累计分拣：\t{collected.now()}",
                f"剩余时间：\t{tracker.to_eta_str()}",
            ]
        )
        ui.refresh(post_delay=0.1)

    if len(info_merged):
        json.dump(
            info_merged,
            open(osp.join(destdir, "voice_data_part.json"), "w", encoding="UTF-8"),
            indent=4,
            ensure_ascii=False,
        )
        Logger.info("CollectVoice: Saved voice data")

    ui.loop_stop()
    ui.reset()
    print("\n分拣语音结束!", s=1)
    print(f"  累计分拣 {collected.now()} 套语音")
    print(f"  此项用时 {round(tracker.get_rt(), 1)} 秒")
