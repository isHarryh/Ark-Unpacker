# -*- coding: utf-8 -*-
# Copyright (c) 2022-2025, Harry Huang
# @ BSD 3-Clause License
from typing import Any, Callable, List, Optional, Tuple, Union

import os.path as osp

import UnityPy
import UnityPy.classes as uc

from .ResolveAB import Resource
from .CombineRGBwithA import AlphaRGBCombiner, image_resize
from .utils.AtlasFile import AtlasFile
from .utils.GlobalMethods import print, rmdir, get_filelist, is_ab_file, stacktrace
from .utils.Logger import Logger
from .utils.SaverUtils import SafeSaver
from .utils.TaskUtils import ThreadCtrl, UICtrl, TaskReporter, TaskReporterTracker


class TreeReader:
    def __init__(self, obj: Optional[uc.Object]):
        self.obj = getattr(obj, "object_reader", obj)

    def __enter__(self):
        if self.obj is None:
            raise AttributeError("Given object or object reader is none")
        read_typetree = getattr(self.obj, "read_typetree", None)
        if callable(read_typetree):
            tree = read_typetree()
            if isinstance(tree, dict):
                return tree
        raise AttributeError("Given object has no serialized type tree")

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False


class SpineAsset:
    UNKNOWN = "Unknown"
    BUILDING = "Building"
    BATTLE_FRONT = "BattleFront"
    BATTLE_BACK = "BattleBack"
    DYN_ILLUST = "DynIllust"

    def __init__(
        self,
        skel: Any,
        atlas: Any,
        tex_list: List[Tuple[uc.Texture2D, uc.Texture2D]],
        anim_list: Optional[List[str]],
    ):
        if not isinstance(skel, uc.TextAsset) or not isinstance(atlas, uc.TextAsset):
            raise TypeError("Spine asset unavailable, bad skel or atlas")
        if not isinstance(tex_list, list) or len(tex_list) == 0:
            raise TypeError("Spine asset unavailable, bad textures")
        self.skel = skel
        self.atlas = atlas
        self.tex_list = tex_list
        self.type = SpineAsset.UNKNOWN
        if skel.m_Name.lower().startswith("dyn_"):
            self.type = SpineAsset.DYN_ILLUST
        elif (
            anim_list
            and "Relax" in anim_list
            or skel.m_Name.lower().startswith("build_")
        ):
            self.type = SpineAsset.BUILDING
        else:
            t = self.atlas.m_Script.lower()
            if t.count("\nf_") + t.count("\nc_") >= t.count("\nb_"):
                self.type = SpineAsset.BATTLE_FRONT
            else:
                self.type = SpineAsset.BATTLE_BACK

    def add_prefix(self):
        def _add_prefix(obj: Union[uc.TextAsset, uc.Texture2D], pre: str):
            if obj and not obj.m_Name.startswith(pre):
                obj.m_Name = pre + obj.m_Name

        prefix = (
            self.type
            + osp.sep
            + osp.splitext(osp.basename(self.atlas.m_Name))[0]
            + osp.sep
        )
        _add_prefix(self.skel, prefix)
        _add_prefix(self.atlas, prefix)
        for i in self.tex_list:
            for j in i:
                _add_prefix(j, prefix)

    def save_spine(
        self,
        destdir: str,
        on_queued: Optional[Callable],
        on_saved: Optional[Callable],
    ):
        atlas = AtlasFile.loads(self.atlas.m_Script)
        for i in self.tex_list:
            if i[0]:
                rgb = i[0].image
                if i[1]:
                    Logger.debug(
                        f'ResolveSpine: Spine asset "{i[0].m_Name}" found with Alpha texture.'
                    )
                    rgba = AlphaRGBCombiner(i[1].image).combine_with(rgb)
                else:
                    Logger.debug(
                        f'ResolveSpine: Spine asset "{i[0].m_Name}" found with NO Alpha texture.'
                    )
                    rgba = AlphaRGBCombiner.apply_premultiplied_alpha(rgb)
                for p in atlas["pages"]:
                    n1 = osp.basename(osp.splitext(p["filename"])[0]).lower()
                    n2 = osp.basename(osp.splitext(i[0].m_Name)[0]).lower()
                    if n1 == n2:
                        rgba = image_resize(rgba, p["size"])
                        break
                SafeSaver.save_image(
                    rgba,
                    destdir,
                    i[0].m_Name,
                    on_queued=on_queued,
                    on_saved=on_saved,
                )
            else:
                Logger.warn("ResolveSpine: Spine asset RGB texture missing.")
        for i in (self.atlas, self.skel):
            SafeSaver.save_object(i, destdir, i.m_Name, on_queued, on_saved)
            Logger.debug(f'ResolveSpine: Spine asset "{i.m_Name}" found.')

    @classmethod
    def from_resource(cls, res: Resource) -> List["SpineAsset"]:
        spines = []
        try:
            for mono in res.monobehaviors:
                with TreeReader(mono) as tree:
                    if "skeletonDataAsset" not in tree.keys():
                        continue
                    mono_sd = res.get_object_by_pathid(
                        tree["skeletonDataAsset"], res.monobehaviors
                    )
                    with TreeReader(mono_sd) as tree_sd:
                        skel = res.get_object_by_pathid(
                            tree_sd["skeletonJSON"], res.textassets
                        )
                        mono_ad = res.get_object_by_pathid(
                            tree_sd["atlasAssets"][0], res.monobehaviors
                        )
                        with TreeReader(mono_ad) as tree_ad:
                            atlas = res.get_object_by_pathid(
                                tree_ad["atlasFile"], res.textassets
                            )
                            list2mat = [
                                res.get_object_by_pathid(i, res.materials)
                                for i in tree_ad["materials"]
                            ]
                            list2tex = []
                            for mat in list2mat:
                                tex_rgb, tex_alpha = None, None
                                with TreeReader(mat) as tree_mat:
                                    tex_envs = tree_mat["m_SavedProperties"][
                                        "m_TexEnvs"
                                    ]
                                    for tex in tex_envs:
                                        if tex[0] == "_MainTex":
                                            tex_rgb = res.get_object_by_pathid(
                                                tex[1]["m_Texture"], res.texture2ds
                                            )
                                        elif tex[0] == "_AlphaTex":
                                            tex_alpha = res.get_object_by_pathid(
                                                tex[1]["m_Texture"], res.texture2ds
                                            )
                                list2tex.append((tex_rgb, tex_alpha))
                            spine = cls(
                                skel, atlas, list2tex, tree.get("_animationName", None)
                            )
                            spine.add_prefix()
                            spines.append(spine)
        except Exception as arg:
            Logger.warn(
                f'ResolveSpine: Failed to handle skeletons in resource "{res.name}": {stacktrace()}'
            )
        return spines


def spine_resolve(
    abfile: str,
    destdir: str,
    on_processed: Optional[Callable] = None,
    on_file_queued: Optional[Callable] = None,
    on_file_saved: Optional[Callable] = None,
):
    """Extracts Spine assets from an AB file.

    :param abfile: Path to the AB file;
    :param destdir: Destination directory;
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
        spines = SpineAsset.from_resource(res)
        if len(spines) >= 10:
            Logger.info(
                f'ResolveSpine: "{res.name}" has {len(spines)} spines, unpacking it may take a long time.'
            )
        for i in spines:
            i.save_spine(destdir, on_file_queued, on_file_saved)
    except BaseException as arg:
        Logger.error(
            f'ResolveSpine: Error occurred while unpacking file "{abfile}": Exception{type(arg)} {arg}'
        )
    if on_processed:
        on_processed()


def main(
    src: str,
    destdir: str,
    do_del: bool = False,
    separate: bool = True,
):
    """Extracts all Spine assets from the given directory or a given AB file.

    :param src: Source directory or file;
    :param destdir: Destination directory;
    :param do_del: Whether to delete the existing files in the destination directory, `False` for default;
    :param separate: Whether to sort the extracted files by their source AB file path;
    :rtype: None;
    """
    print("\n正在解析路径...", s=1)
    Logger.info("ResolveSpine: Retrieving file paths...")
    src = osp.normpath(osp.realpath(src))
    destdir = osp.normpath(osp.realpath(destdir))
    flist = [src] if osp.isfile(src) else get_filelist(src)
    flist = list(filter(is_ab_file, flist))
    if do_del:
        print("\n正在清理...", s=1)
        rmdir(destdir)
    SafeSaver.get_instance().reset_counter()
    thread_ctrl = ThreadCtrl()
    ui = UICtrl()
    tr_processed = TaskReporter(50, len(flist))
    tr_file_saving = TaskReporter(1)
    tracker = TaskReporterTracker(tr_processed, tr_file_saving)
    ui.reset()
    ui.loop_start()
    for i in flist:
        ui.request(
            [
                "正在批量导出Spine...",
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
            spine_resolve,
            (
                i,
                curdestdir,
                tr_processed.report,
                tr_file_saving.update_demand,
                tr_file_saving.report,
            ),
            name=f"SpineThread:{id(i)}",
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
                "正在批量导出Spine...",
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
    print("\nSpine批量导出结束!", s=1)
    print(f"  累计解包 {tr_processed.get_done()} 个文件")
    print(f"  累计导出 {tr_file_saving.get_done()} 个文件")
    print(f"  此项用时 {round(tracker.get_rt(), 1)} 秒")
