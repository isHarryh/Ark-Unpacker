# -*- coding: utf-8 -*-
# Copyright (c) 2022-2025, Harry Huang
# @ BSD 3-Clause License
from typing import Callable, Collection, List, Literal, Optional, Tuple, TypeVar, Union

import os.path as osp

import UnityPy
import UnityPy.classes as uc
from UnityPy.enums.BundleFile import CompressionFlags
from UnityPy.files.File import File, ObjectReader
from UnityPy.helpers import CompressionHelper
from UnityPy.streams.EndianBinaryReader import EndianBinaryReader

from .lz4ak.Block import decompress_lz4ak
from .utils.GlobalMethods import print, rmdir, get_filelist, is_ab_file
from .utils.Logger import Logger
from .utils.SaverUtils import SafeSaver
from .utils.TaskUtils import ThreadCtrl, UICtrl, TaskReporter, TaskReporterTracker

# New compression algorithm introduced in Arknights v2.5.04+
CompressionHelper.DECOMPRESSION_MAP[CompressionFlags.LZHAM] = decompress_lz4ak


_T = TypeVar("_T", bound=uc.Object)


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

        self._build_pathid_lut()
        self._build_type_lut()
        self._build_roi_type_lut()

        for obj in self.get_objects_by_type(uc.AssetBundle):
            if getattr(obj, "m_Name", None):
                if self.name != osp.basename(obj.m_Name):
                    Logger.debug(
                        f'ResolveAB: Resource "{self.name}" internally named "{obj.m_Name}"'
                    )
                    self.name = osp.basename(obj.m_Name)

    def _build_pathid_lut(self):
        all_pathid = set()
        for reader in self.env.objects:
            all_pathid.add(reader.path_id)
        max_pathid = max(all_pathid) if all_pathid else 0

        self._lut_pathid: dict[int, Tuple[ObjectReader, Optional[uc.Object]]] = {}
        for reader in self.env.objects:
            if reader.path_id in self._lut_pathid:
                other_reader, _ = self._lut_pathid[reader.path_id]
                replace_pathid = max_pathid + 1
                max_pathid += 1
                Logger.info(
                    f'Resource: Duplicate PathID found when building LUT for "{self.name}"\n'
                    f"- Existing: {other_reader.peek_name()} ({other_reader.type.name}) PathID={other_reader.path_id}\n"
                    f"- Incoming: {reader.peek_name()} ({reader.type.name}) PathID={reader.path_id}"
                    f" (will be reassigned to {replace_pathid})"
                )
                reader.path_id = replace_pathid
            self._lut_pathid[reader.path_id] = (reader, None)

    def _build_type_lut(self):
        self._lut_type: dict[str, List[int]] = {}
        for reader in self.env.objects:
            clz = reader.get_class()
            if not clz:
                continue
            if clz.__name__ not in self._lut_type:
                self._lut_type[clz.__name__] = []
            self._lut_type[clz.__name__].append(reader.path_id)

    def _build_roi_type_lut(self):
        self._lut_roi_type: dict[str, List[int]] = {}
        for reader in self.env.objects:
            clz = reader.get_class()
            if not clz:
                continue
            if issubclass(clz, uc.Sprite) or issubclass(clz, uc.Texture2D):
                roi = "Image"
            elif issubclass(clz, uc.TextAsset) and not issubclass(clz, uc.MonoScript):
                roi = "Text"
            elif issubclass(clz, uc.AudioClip):
                roi = "Audio"
            elif issubclass(clz, uc.Mesh):
                roi = "Mesh"
            elif issubclass(clz, uc.AssetBundle):
                roi = "AssetBundle"
            else:
                continue
            if roi not in self._lut_roi_type:
                self._lut_roi_type[roi] = []
            self._lut_roi_type[roi].append(reader.path_id)

    def try_get_object_by_pathid(
        self,
        pathid: Union[int, dict],
        assert_type: type[_T] = uc.Object,
    ) -> Optional[_T]:
        """Tries to get the object with the given PathID.

        :param pathid: PathID in int or a dict containing `m_PathID` field;
        :param assert_type: The expected type of the object;
        :returns: The first object matching the PathID and type, or `None` if failed;
        """
        try:
            return self.get_object_by_pathid(pathid, assert_type)
        except (KeyError, TypeError):
            return None

    def get_object_by_pathid(
        self,
        pathid: Union[int, dict],
        assert_type: type[_T] = uc.Object,
    ) -> _T:
        """Gets the object with the given PathID.

        :param pathid: PathID in int or a dict containing `m_PathID` field;
        :param assert_type: The expected type of the object;
        :returns: The first object matching the PathID and type;
        """
        if not self.env:
            raise RuntimeError("Environment has been disposed or not initialized")
        if isinstance(pathid, dict):
            if "m_PathID" not in pathid:
                raise KeyError(f"Given dict does not contain m_PathID field")
            pid = pathid["m_PathID"]
        elif isinstance(pathid, int):
            pid = pathid
        else:
            raise TypeError(f"Argument pathid must be int or dict")
        if pid not in self._lut_pathid:
            raise KeyError(f"Object with PathID {pid} not found")
        reader, obj = self._lut_pathid[pid]
        if obj is None:
            obj = reader.read()
            self._lut_pathid[pid] = (reader, obj)
        if not isinstance(obj, assert_type):
            raise TypeError(
                f"Object with PathID {pid} is not of type {assert_type}, but {type(obj).__name__}"
            )
        return obj

    def get_objects_by_type(self, obj_type: type[_T]) -> List[_T]:
        """Gets all the objects of the given type.

        :param obj_type: The expected type of the objects;
        :returns: The list of objects;
        """
        if not self.env:
            raise RuntimeError("Environment has been disposed or not initialized")
        tn = obj_type.__name__
        if tn not in self._lut_type:
            return []
        objs: List[_T] = []
        for pid in self._lut_type[tn]:
            reader, obj = self._lut_pathid[pid]
            if obj is None:
                obj = reader.read()
                self._lut_pathid[pid] = (reader, obj)
            if obj is not None:
                objs.append(obj)  # type: ignore
        return objs

    def get_objects_by_roi_type(
        self, roi_type: Literal["Image", "Text", "Audio", "Mesh", "AssetBundle"]
    ) -> List[uc.Object]:
        """Gets all the objects of the given ROI type.

        :param roi_type: The expected ROI type of the objects;
        :returns: The list of objects;
        """
        if not self.env:
            raise RuntimeError("Environment has been disposed or not initialized")
        if roi_type not in self._lut_roi_type:
            return []
        objs: List[uc.Object] = []
        for pid in self._lut_roi_type[roi_type]:
            reader, obj = self._lut_pathid[pid]
            if obj is None:
                obj = reader.read()
                self._lut_pathid[pid] = (reader, obj)
            if obj is not None:
                objs.append(obj)
        return objs

    def find_object_and_typetree_with_key(
        self, obj_type: type[_T], contains_keys: Collection[str]
    ) -> List[Tuple[_T, dict]]:
        """Finds all the objects of the given type whose typetree contains all the given keys.

        :param obj_type: The expected type of the objects;
        :param contains_keys: The collection of keys that the typetree should contain;
        :returns: The list of tuples of the object and its typetree;
        """
        if not self.env:
            raise RuntimeError("Environment has been disposed or not initialized")
        result: List[Tuple[_T, dict]] = []
        for obj in self.get_objects_by_type(obj_type):
            with TreeReader(obj) as tree:
                if all(k in tree for k in contains_keys):
                    result.append((obj, tree))
        return result


def ab_resolve(
    abfile: str,
    destdir: str,
    do_img: bool,
    do_txt: bool,
    do_aud: bool,
    do_mesh: bool,
    do_tree: bool,
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
    :param do_mesh: Whether to extract mesh;
    :param do_tree: Whether to export typetrees as JSON;
    :param on_processed: Callback `f()` for finished, `None` for ignore;
    :param on_file_queued: Callback `f()` invoked when a file was queued, `None` for ignore;
    :param on_file_saved: Callback `f(file_path_or_none_for_not_saved)`, `None` for ignore;
    :rtype: None;
    """
    from .ResolveSpine import SpineAsset

    if not osp.isfile(abfile):
        if on_processed:
            on_processed()
        return
    try:
        with open(abfile, "rb") as f:
            res = Resource(UnityPy.load(f))

            Logger.debug(f'ResolveAB: "{res.name}" has {res.length} objects.')
            if res.length >= 10000:
                Logger.info(
                    f'ResolveAB: Too many objects in file "{res.name}", unpacking it may take a long time.'
                )
            elif res.length == 0:
                Logger.info(f'ResolveAB: No object in file "{res.name}".')

            for s in SpineAsset.from_resource(res):
                s.add_prefix()

            for roi_flag, roi_type in [
                (do_img, "Image"),
                (do_txt, "Text"),
                (do_aud, "Audio"),
                (do_mesh, "Mesh"),
            ]:
                if roi_flag:
                    SafeSaver.save_objects(
                        res.get_objects_by_roi_type(roi_type),  # type: ignore
                        destdir,
                        on_file_queued,
                        on_file_saved,
                    )

            # Export typetrees as JSON
            if do_tree:
                typetrees = {}
                for obj in res.env.objects:
                    if hasattr(obj, "read_typetree"):
                        try:
                            tree = obj.read_typetree()
                            if tree:
                                typetrees[str(obj.path_id)] = tree
                        except Exception as e:
                            Logger.debug(
                                f"ResolveAB: Failed to read typetree for {obj.type.name}_{obj.path_id}: {e}"
                            )

                if typetrees:
                    result = {res.name: typetrees}
                    SafeSaver.save_json(
                        result,
                        destdir,
                        f"TT_{res.name}",
                        on_file_queued,
                        on_file_saved,
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
    do_mesh: bool = True,
    do_tree: bool = False,
    separate: bool = True,
):
    """Extract all the AB files from the given directory or extract a given AB file.

    :param src: Source directory or file;
    :param destdir: Destination directory;
    :param do_del: Whether to delete the existing files in the destination directory, `False` for default;
    :param do_img: Whether to extract images;
    :param do_txt: Whether to extract text scripts;
    :param do_aud: Whether to extract audios;
    :param do_mesh: Whether to extract mesh;
    :param do_tree: Whether to export typetrees as JSON;
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

    Logger.reset_stats()
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
        curdestdir = (
            destdir
            if osp.samefile(i, src)
            else (
                osp.join(
                    destdir,
                    osp.relpath(osp.dirname(i), src),
                    osp.splitext(osp.basename(i))[0],
                )
                if separate
                else osp.join(destdir, osp.relpath(osp.dirname(i), src))
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
                do_mesh,
                do_tree,
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
