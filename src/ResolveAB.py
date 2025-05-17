# -*- coding: utf-8 -*-
# Copyright (c) 2022-2025, Harry Huang
# @ BSD 3-Clause License
from typing import Callable, List, Optional, Sequence, Union

import os.path as osp

import UnityPy
import UnityPy.classes as uc
from UnityPy.enums.BundleFile import CompressionFlags
from UnityPy.files.File import File
from UnityPy.helpers import CompressionHelper
from UnityPy.streams.EndianBinaryReader import EndianBinaryReader

from .lz4ak.Block import decompress_lz4ak
from .utils.GlobalMethods import print, rmdir, get_filelist, is_ab_file
from .utils.Logger import Logger
from .utils.SaverUtils import SafeSaver
from .utils.TaskUtils import ThreadCtrl, UICtrl, TaskReporter, TaskReporterTracker

# New compression algorithm introduced in Arknights v2.5.04+
CompressionHelper.DECOMPRESSION_MAP[CompressionFlags.LZHAM] = decompress_lz4ak


class Resource:
    """The class representing a collection of the objects in an UnityPy Environment."""

    def __init__(self, env: UnityPy.Environment):
        """Initializes with the given UnityPy Environment instance.

        :param env: The Environment instance from `UnityPy.load()`;
        :rtype: None;
        """
        if isinstance(env.file, File):
            self.name: str = env.file.name
        elif isinstance(env.file, EndianBinaryReader):
            self.name: str = ""
        else:
            raise TypeError(
                f"Unknown type of UnityPy Environment file: {type(env.file).__name__}"
            )
        self.env: UnityPy.Environment = env
        self.length: int = len(env.objects)
        ###
        self.sprites: List[uc.Sprite] = []
        self.texture2ds: List[uc.Texture2D] = []
        self.textassets: List[uc.TextAsset] = []
        self.audioclips: List[uc.AudioClip] = []
        self.materials: List[uc.Material] = []
        self.monobehaviors: List[uc.MonoBehaviour] = []
        ###
        for i in [o.read() for o in env.objects]:
            if isinstance(i, uc.Sprite):
                self.sprites.append(i)
            elif isinstance(i, uc.Texture2D):
                self.texture2ds.append(i)
            elif isinstance(i, uc.TextAsset) and not isinstance(i, uc.MonoScript):
                self.textassets.append(i)
            elif isinstance(i, uc.AudioClip):
                self.audioclips.append(i)
            elif isinstance(i, uc.Material):
                self.materials.append(i)
            elif isinstance(i, uc.MonoBehaviour):
                self.monobehaviors.append(i)
            elif isinstance(i, uc.AssetBundle):
                if getattr(i, "m_Name", None):
                    if self.name != osp.basename(i.m_Name):
                        Logger.debug(
                            f'ResolveAB: Resource "{self.name}" internally named "{i.m_Name}"'
                        )
                        self.name = osp.basename(i.m_Name)

    def get_object_by_pathid(
        self, pathid: Union[int, dict], search_in: Sequence[uc.Object]
    ):
        """Gets the object with the given PathID.

        :param pathid: PathID in int or a dict containing `m_PathID` field;
        :param search_in: Searching range;
        :returns: The object, `None` for not found;
        """
        _key = "m_PathID"
        if isinstance(pathid, dict):
            if _key in pathid:
                _pathid = int(pathid[_key])
            else:
                return None
        else:
            _pathid = pathid
        for i in search_in:
            if i.object_reader is not None and i.object_reader.path_id == _pathid:
                return i
        return None


def ab_resolve(
    abfile: str,
    destdir: str,
    do_img: bool,
    do_txt: bool,
    do_aud: bool,
    on_processed: Optional[Callable] = None,
    on_file_queued: Optional[Callable] = None,
    on_file_saved: Optional[Callable] = None,
):
    """Extracts an AB file.

    :param abfile: Path to the AB file;
    :param destdir: Destination directory;
    :param do_img: Whether to extract images;
    :param do_txt: Whether to extract text scripts;
    :param do_aud: Whether to extract audios;
    :param on_processed: Callback `f()` for finished, `None` for ignore;
    :param on_file_queued: Callback `f()` invoked when a file was queued, `None` for ignore;
    :param on_file_saved: Callback `f(file_path_or_none_for_not_saved)`, `None` for ignore;
    :rtype: None;
    """
    if not osp.isfile(abfile):
        if on_processed:
            on_processed()
        return
    try:
        res = Resource(UnityPy.load(abfile))
        Logger.debug(f'ResolveAB: "{res.name}" has {res.length} objects.')
        if res.length >= 10000:
            Logger.info(
                f'ResolveAB: Too many objects in file "{res.name}", unpacking it may take a long time.'
            )
        elif res.length == 0:
            Logger.info(f'ResolveAB: No object in file "{res.name}".')

        if do_img:
            SafeSaver.save_objects(res.sprites, destdir, on_file_queued, on_file_saved)
            SafeSaver.save_objects(
                res.texture2ds, destdir, on_file_queued, on_file_saved
            )
        if do_txt:
            SafeSaver.save_objects(
                res.textassets, destdir, on_file_queued, on_file_saved
            )
        if do_aud:
            SafeSaver.save_objects(
                res.audioclips, destdir, on_file_queued, on_file_saved
            )
    except BaseException as arg:
        # Error feedback
        Logger.error(
            f'ResolveAB: Error occurred while unpacking file "{abfile}": Exception{type(arg)} {arg}'
        )
        # raise(arg)
    if on_processed:
        on_processed()


########## Main-主程序 ##########
def main(
    src: str,
    destdir: str,
    do_del: bool = False,
    do_img: bool = True,
    do_txt: bool = True,
    do_aud: bool = True,
    separate: bool = True,
):
    """Extract all the AB files from the given directory or extract a given AB file.

    :param src: Source directory or file;
    :param destdir: Destination directory;
    :param do_del: Whether to delete the existing files in the destination directory, `False` for default;
    :param do_img: Whether to extract images;
    :param do_txt: Whether to extract text scripts;
    :param do_aud: Whether to extract audios;
    :param separate: Whether to sort the extracted files by their source AB file path.
    :rtype: None;
    """
    print("\n正在解析路径...", s=1)
    Logger.info("ResolveAB: Retrieving file paths...")
    src = osp.normpath(osp.realpath(src))
    destdir = osp.normpath(osp.realpath(destdir))
    flist = [src] if osp.isfile(src) else get_filelist(src)
    flist = list(filter(is_ab_file, flist))

    if do_del:
        print("\n正在清理...", s=1)
        rmdir(destdir)  # Danger zone
    SafeSaver.get_instance().reset_counter()
    thread_ctrl = ThreadCtrl()
    ui = UICtrl()
    tr_processed = TaskReporter(50, len(flist))
    tr_file_saving = TaskReporter(1)
    tracker = TaskReporterTracker(tr_processed, tr_file_saving)

    ui.reset()
    ui.loop_start()
    for i in flist:
        # (i stands for a file's path)
        ui.request(
            [
                "正在批量解包...",
                tracker.to_progress_bar_str(),
                f"当前目录：\t{osp.basename(osp.dirname(i))}",
                f"当前文件：\t{osp.basename(i)}",
                f"累计解包：\t{tr_processed.to_progress_str()}",
                f"累计导出：\t{tr_file_saving.to_progress_str()}",
                f"预计剩余时间：\t{tracker.to_eta_str()}",
                f"累计消耗时间：\t{tracker.to_rt_str()}",
                f"运行状态统计：\t{Logger.to_ew_stats_str()}",
            ]
        )
        ###
        subdestdir = osp.dirname(i).strip(osp.sep).replace(src, "").strip(osp.sep)
        curdestdir = (
            destdir
            if osp.samefile(i, src)
            else (
                osp.join(destdir, subdestdir, osp.splitext(osp.basename(i))[0])
                if separate
                else osp.join(destdir, subdestdir)
            )
        )
        thread_ctrl.run_subthread(
            ab_resolve,
            (
                i,
                curdestdir,
                do_img,
                do_txt,
                do_aud,
                tr_processed.report,
                tr_file_saving.update_demand,
                tr_file_saving.report,
            ),
            name=f"RsThread:{id(i)}",
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
                "正在批量解包...",
                tracker.to_progress_bar_str(),
                f"累计解包：\t{tr_processed.to_progress_str()}",
                f"累计导出：\t{tr_file_saving.to_progress_str()}",
                f"预计剩余时间：\t{tracker.to_eta_str()}",
                f"累计消耗时间：\t{tracker.to_rt_str()}",
                f"运行状态统计：\t{Logger.to_ew_stats_str()}",
            ]
        )
        ui.refresh(post_delay=0.1)

    ui.reset()
    print("\n批量解包结束!", s=1)
    print(f"  累计解包 {tr_processed.get_done()} 个文件")
    print(f"  累计导出 {tr_file_saving.get_done()} 个文件")
    print(f"  此项用时 {round(tracker.get_rt(), 1)} 秒")
