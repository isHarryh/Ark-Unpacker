# Copyright (c) 2022-2026, Harry Huang
# @ BSD 3-Clause License
from enum import StrEnum
import multiprocessing as mp
from typing import Callable, Dict, Generator, List, Optional, Sequence, Union

import glob
import os.path as osp

import UnityPy
import UnityPy.classes as uc
from spine_asset.v38 import AtlasFile, SkeletonBinary, SkeletonJson, SkeletonData

from .ResolveAB import Resource, TreeReader
from .CombineRGBwithA import AlphaRGBCombiner, image_resize
from .mp.FsGuardProcess import FsGuardClient, FsGuardClientSlot, FsGuardProcess
from .mp.Messages import ResolveSpineTask, StopMessage
from .mp.Process import ProcessUtils
from .mp.ProcessResultBus import ProcessResultBus, ProcessResultSender
from .mp.ProcessReporter import ProcessReporter
from .ui.RichCLI import RichCLI
from .ui.TaskLive import TaskDetailField, TaskLiveView, TaskValueField
from .utils.Config import Config, PerformanceLevel
from .utils.GlobalMethods import rmdir, is_ab_file, stacktrace
from .utils.Logger import Logger
from .utils.SaverUtils import SafeSaver
from .utils.TaskUtils import TaskReporter, TaskReporterTracker

CLI = RichCLI.get_instance()


SDPathID2NamesMap = Dict[int, Union[str, List[str]]]


class SpineType(StrEnum):
    UNKNOWN = "Unknown"
    BUILDING = "Building"
    BATTLE_FRONT = "BattleFront"
    BATTLE_BACK = "BattleBack"
    DYN_ILLUST = "DynIllust"
    DYN_ILLUST_START = "DynIllustStart"
    DYN_PORTRAIT = "DynPortrait"
    DYN_UNKNOWN = "DynUnknown"


class SpineAssetHandler:
    def __init__(self, obj: Union[uc.TextAsset, uc.Texture2D]):
        self.obj = obj
        self.original_name = obj.m_Name

    @property
    def name(self) -> str:
        return self.obj.m_Name

    def set_path_prefix(self, prefix: str):
        """Sets the path prefix for the Spine asset object using its original name.

        :param prefix: The directory prefix to use;
        :rtype: None;
        """
        self.obj.m_Name = prefix + self.original_name

    def __repr__(self) -> str:
        return f"<SpineAssetHandler name={self.name}>"


class SpineAtlasHandler(SpineAssetHandler):
    def __init__(self, atlas: uc.TextAsset):
        super().__init__(atlas)
        self.content = atlas.m_Script
        self.atlas_data = self._load_atlas_data()

    def _load_atlas_data(self) -> AtlasFile:
        return AtlasFile.loads(self.content)

    def guess_type(self) -> SpineType:
        t = self.name.lower()

        if t.startswith("dyn_"):
            if t.startswith("dyn_portrait_"):
                return SpineType.DYN_PORTRAIT  # Reliable
            elif t.startswith("dyn_illust_"):
                return SpineType.DYN_ILLUST  # Not reliable, DYN_ILLUST_START may also match this
            else:
                Logger.info(f'ResolveSpine: Unknown dynamic illust Spine type of "{t}"')
                return SpineType.DYN_UNKNOWN  # Unrecognized
        elif t.startswith("enemy_"):
            return SpineType.BATTLE_FRONT  # Reliable
        elif t.startswith("build_"):
            return SpineType.BUILDING  # Not reliable, few BUILDING may bypass this

        t = self.content.lower()
        if t.count("\nf_") + t.count("\nc_") >= t.count("\nb_"):
            return SpineType.BATTLE_FRONT
        else:
            return SpineType.BATTLE_BACK


class SpineSkeletonHandler(SpineAssetHandler):
    def __init__(self, skel: uc.TextAsset):
        super().__init__(skel)
        self.content = skel.m_Script
        self.skeleton_data = self._load_skeleton_data()

    def _load_skeleton_data(self) -> SkeletonData:
        if self.content.startswith("{"):
            return SkeletonJson().read_skeleton_data(self.content)
        else:
            bytes_content = self.content.encode("utf-8", "surrogateescape")
            return SkeletonBinary().read_skeleton_data(bytes_content)

    def guess_type(self) -> SpineType:
        t = self.name.lower()
        anim_names = [a.name.lower() for a in self.skeleton_data.animations]

        if t.startswith("dyn_"):
            if t.startswith("dyn_portrait_"):
                return SpineType.DYN_PORTRAIT  # Reliable
            elif t.startswith("dyn_illust_"):
                if "interact" in anim_names and "idle" in anim_names:
                    return SpineType.DYN_ILLUST  # Reliable
                elif "start" in anim_names:
                    return SpineType.DYN_ILLUST_START  # Reliable
                elif "idle" in anim_names:
                    return SpineType.DYN_ILLUST  # Fallback
                else:
                    Logger.info(f'ResolveSpine: Unknown dynamic illust Spine type of "{t}", animations={anim_names}')
                    return SpineType.DYN_UNKNOWN  # Unrecognized
            else:
                Logger.info(f'ResolveSpine: Unknown dynamic illust Spine type of "{t}"')
                return SpineType.DYN_UNKNOWN  # Unrecognized
        elif t.startswith("enemy_"):
            return SpineType.BATTLE_FRONT  # Reliable

        if "default" in anim_names and "relax" in anim_names:
            return SpineType.BUILDING  # Reliable
        else:
            return SpineType.UNKNOWN  # Need more info, please use atlas to guess


class SpineTextureHandler(SpineAssetHandler):
    def __init__(self, tex_rgb: uc.Texture2D, tex_alpha: Optional[uc.Texture2D] = None):
        super().__init__(tex_rgb)
        self.tex_rgb = tex_rgb
        self.tex_alpha = tex_alpha
        self.rgb = tex_rgb.image
        self.alpha = tex_alpha.image if tex_alpha else None
        self.original_alpha_name = tex_alpha.m_Name if tex_alpha else None

    def set_path_prefix(self, prefix: str):
        super().set_path_prefix(prefix)
        if self.tex_alpha and self.original_alpha_name:
            self.tex_alpha.m_Name = prefix + self.original_alpha_name


class SpineAsset:
    def __init__(
        self,
        atlas_handler: SpineAtlasHandler,
        skel_handler: SpineSkeletonHandler,
        tex_pairs: Sequence[SpineTextureHandler],
        sd_pathid: Optional[int] = None,
        type_: Optional[SpineType] = None,
    ):
        """Initializes a Spine asset with the given handlers.

        :param atlas_handler: The SpineAtlasHandler instance for the atlas;
        :param skel_handler: The SpineSkeletonHandler instance for the skeleton;
        :param tex_pairs: A sequence of SpineTextureHandler instances for the textures;
        :param sd_pathid: The skeleton data asset path id, optional but useful if provided;
        :param type_: The explicit SpineType of the asset, `None` for auto-detection;
        """
        self.atlas_handler = atlas_handler
        self.skel_handler = skel_handler
        self.tex_handlers = tex_pairs
        self.sd_pathid = sd_pathid

        if type_ is None:
            type_ = skel_handler.guess_type()
            if type_ == SpineType.UNKNOWN:
                type_ = atlas_handler.guess_type()
        self.type = type_

    def process_path(self, custom_folder_name: Optional[str] = None):
        """Sets the path prefix for all associated Spine asset objects based on type and folder name.

        :param custom_folder_name: Custom folder name to use instead of the atlas name, optional;
        :rtype: None;
        """
        folder_name = (
            custom_folder_name
            if custom_folder_name
            else osp.splitext(osp.basename(self.atlas_handler.original_name))[0]
        )
        prefix = f"{self.type.value}/{folder_name}/"
        for h in list((self.atlas_handler, self.skel_handler)) + list(self.tex_handlers):
            h.set_path_prefix(prefix)

    def iter_export_items(self) -> Generator[SafeSaver.ExportItem, None, None]:
        Logger.debug(
            f'ResolveSpine: Exporting Spine "{self.skel_handler.name}" + "{self.atlas_handler.name}" + {len(self.tex_handlers)} textures with type "{self.type}"'
        )
        for tex in self.tex_handlers:
            for p in self.atlas_handler.atlas_data.pages:
                n1 = osp.basename(osp.splitext(p.filename)[0]).lower()
                n2 = osp.basename(osp.splitext(tex.name)[0]).lower()
                if n1 == n2:
                    tex.rgb = image_resize(tex.rgb, p.size)
                    break
            if tex.alpha:
                Logger.debug(f'ResolveSpine: Spine asset "{tex.name}" found with Alpha texture.')
                rgba = AlphaRGBCombiner(tex.alpha).combine_with(tex.rgb)
            else:
                Logger.debug(f'ResolveSpine: Spine asset "{tex.name}" found with NO Alpha texture.')
                rgba = AlphaRGBCombiner.apply_premultiplied_alpha(tex.rgb)
            yield SafeSaver.ExportItem(tex.name, ".png", SafeSaver.encode_image_bytes(rgba))
        for i in (self.atlas_handler, self.skel_handler):
            yield from SafeSaver.iter_object_export_items(i.obj, i.name)

    def __repr__(self) -> str:
        return f"<SpineAsset type={self.type}>"

    @classmethod
    def _extract_skeleton_name_mapping_from_pfb(cls, res: Resource) -> SDPathID2NamesMap:
        """Extracts skeleton data asset path id to GameObject name mapping from pfb resource.

        This is used to differentiate same-skeleton different-skin models that have
        identical internal skeleton names (e.g., enemy_1046_agent vs enemy_1046_agent_2).

        :param res: The Resource instance (pfb file) to extract mappings from;
        :returns: A dict mapping skeleton data asset path id to list of GameObject m_Names;
        """
        mapping = {}
        try:
            for _, tree_go in res.find_object_and_typetree_with_key(
                uc.GameObject,
                ["m_Name", "m_Component"],
            ):
                m_name = tree_go.get("m_Name", "")
                if not m_name.startswith("enemy_"):
                    continue

                for comp in tree_go.get("m_Component", []):
                    comp_ref = comp.get("component", {})
                    if "m_PathID" not in comp_ref:
                        continue
                    comp_obj = res.get_object_by_pathid(comp_ref, uc.Component)

                    with TreeReader(comp_obj) as tree_comp:
                        if "_animator" not in tree_comp:
                            continue
                        animator_ref = tree_comp.get("_animator", {})
                        if "m_PathID" not in animator_ref:
                            continue
                        animator_obj = res.get_object_by_pathid(animator_ref, uc.MonoBehaviour)

                        with TreeReader(animator_obj) as tree_animator:
                            skeleton_ref = tree_animator.get("_skeleton", {})
                            if "m_PathID" not in skeleton_ref:
                                Logger.info(
                                    f'ResolveSpine: Pfb mapping skeleton reference not found in animator of "{m_name}", may be non-spine character'
                                )
                                continue
                            skeleton_obj = res.get_object_by_pathid(skeleton_ref, uc.MonoBehaviour)

                            with TreeReader(skeleton_obj) as tree_skel:
                                skel_data_ref = tree_skel.get("skeletonDataAsset", {})
                                if "m_PathID" in skel_data_ref:
                                    skel_data_pathid = skel_data_ref["m_PathID"]
                                    if skel_data_pathid not in mapping:
                                        mapping[skel_data_pathid] = []
                                    mapping[skel_data_pathid].append(m_name)
                                    Logger.debug(
                                        f'ResolveSpine: Pfb mapping mapped skeleton data asset {skel_data_pathid} to "{m_name}"'
                                    )
        except Exception:
            Logger.warn(f'ResolveSpine: Pfb mapping failed to process pfb "{res.name}": {stacktrace()}')
        Logger.info(
            f'ResolveSpine: Pfb mapping extracted total {len(mapping)} skeleton name mappings from pfb "{res.name}"'
        )
        return mapping

    @classmethod
    def from_resource(cls, res: Resource) -> List["SpineAsset"]:
        """Gets Spine assets from the given resource.

        :param res: The Resource instance to extract Spine assets from;
        :returns: A list of SpineAsset instances;
        """
        spines = []
        found_front_and_back = list(cls._find_front_and_back_skel_data(res))
        try:
            # sd = SkeletonData
            for mono_sd, tree_sd in res.find_object_and_typetree_with_key(
                uc.MonoBehaviour,
                ["atlasAssets", "skeletonJSON"],
            ):
                skel = res.get_object_by_pathid(tree_sd["skeletonJSON"], uc.TextAsset)
                mono_ad = res.get_object_by_pathid(tree_sd["atlasAssets"][0], uc.MonoBehaviour)
                # ad = AtlasData
                with TreeReader(mono_ad) as tree_ad:
                    atlas = res.get_object_by_pathid(tree_ad["atlasFile"], uc.TextAsset)
                    tex_handlers: List[SpineTextureHandler] = []
                    for mat in (res.get_object_by_pathid(i, uc.Material) for i in tree_ad["materials"]):
                        # mat = MaterialData
                        tex_rgb, tex_alpha = None, None
                        with TreeReader(mat) as tree_mat:
                            tex_envs = tree_mat["m_SavedProperties"]["m_TexEnvs"]
                            for tex in tex_envs:
                                if tex[0] == "_MainTex":
                                    tex_rgb = res.get_object_by_pathid(tex[1]["m_Texture"], uc.Texture2D)
                                elif tex[0] == "_AlphaTex":
                                    tex_alpha = res.try_get_object_by_pathid(tex[1]["m_Texture"], uc.Texture2D)
                        if tex_rgb is None:
                            raise ValueError("RGB main texture not found")
                        tex_handlers.append(SpineTextureHandler(tex_rgb, tex_alpha))

                    if not skel or not atlas or not tex_handlers:
                        raise ValueError("Incomplete Spine asset")

                    sd_pathid = mono_sd.object_reader.path_id if mono_sd.object_reader else None

                    sp_type = None
                    if any(mono_sd is f for f, _ in found_front_and_back):
                        sp_type = SpineType.BATTLE_FRONT
                    elif any(mono_sd is b for _, b in found_front_and_back):
                        sp_type = SpineType.BATTLE_BACK

                    spine = cls(
                        SpineAtlasHandler(atlas),
                        SpineSkeletonHandler(skel),
                        tex_handlers,
                        sd_pathid,
                        sp_type,
                    )
                    spines.append(spine)
        except Exception:
            Logger.warn(f'ResolveSpine: Failed to handle skeletons in resource "{res.name}": {stacktrace()}')
        return spines

    @classmethod
    def _find_front_and_back_skel_data(cls, res: Resource):
        try:
            # ca = CharacterAnimator
            for _, tree_ca in res.find_object_and_typetree_with_key(
                uc.MonoBehaviour,
                ["_animations", "_front", "_back"],
            ):
                mono_sa_front = res.get_object_by_pathid(tree_ca["_front"]["skeleton"], uc.MonoBehaviour)
                mono_sa_back = res.get_object_by_pathid(tree_ca["_back"]["skeleton"], uc.MonoBehaviour)
                # sa = SkeletonAnimation
                if mono_sa_front and mono_sa_back:
                    with TreeReader(mono_sa_front) as tree_sa:
                        mono_sd_front = res.get_object_by_pathid(tree_sa["skeletonDataAsset"], uc.MonoBehaviour)
                    with TreeReader(mono_sa_back) as tree_sa:
                        mono_sd_back = res.get_object_by_pathid(tree_sa["skeletonDataAsset"], uc.MonoBehaviour)
                    # sd = SkeletonData
                    if mono_sd_front and mono_sd_back:
                        yield mono_sd_front, mono_sd_back
        except Exception:
            Logger.warn(
                f'ResolveSpine: Failed to find front-and-back skeleton data in resource "{res.name}": {stacktrace()}'
            )


class ResolveSpineWorkerSession:
    def __init__(self, reporter: ProcessReporter, fs_client: FsGuardClient):
        self._reporter = reporter
        self._fs_client = fs_client

    def log(self, level: str, msg: str):
        self._reporter.log(level, msg)

    def processed(self, success: bool = True):
        self._reporter.processed(success)

    def worker_done(self):
        self._reporter.worker_done()

    def save_item(self, item: SafeSaver.ExportItem, destdir: str):
        dest = self._fs_client.prepare_write(
            destdir,
            item.name,
            item.ext,
            SafeSaver.hash_data(item.data),
        )
        if dest is None:
            self._reporter.file_saved(False)
            return
        try:
            SafeSaver.write_data(dest, item.data)
            self._reporter.file_saved(True)
        except Exception as arg:
            self.log("error", f'ResolveSpine: Failed to write file "{dest}": {arg}')
            self._reporter.file_saved(False)


def pfb_resolve(srcdir: str) -> dict:
    """Extracts skeleton data asset path id to GameObject name mappings from all pfb files.

    :param srcdir: Source directory containing pfb files;
    :returns: A dict mapping skeleton data asset path id to list of GameObject m_Names;
    """
    from .ResolveAB import Resource

    Logger.info(f'ResolveSpine: Pfb resolve started for directory "{srcdir}"')
    srcdir = osp.normpath(osp.realpath(srcdir))
    pfb_files = [srcdir] if osp.isfile(srcdir) else []
    if osp.isdir(srcdir):
        for i in glob.iglob(osp.join(glob.escape(srcdir), "**", "*"), recursive=True):
            if osp.isfile(i) and is_ab_file(i) and "enm_pfb_" in i:
                pfb_files.append(i)
    else:
        pfb_files = [f for f in pfb_files if is_ab_file(f) and "enm_pfb_" in f]

    all_mappings = {}
    for pfb_file in pfb_files:
        try:
            Logger.debug(f'ResolveSpine: Pfb resolve processing "{pfb_file}"')
            with open(pfb_file, "rb") as f:
                res_pfb = Resource(UnityPy.load(f))
                mapping = SpineAsset._extract_skeleton_name_mapping_from_pfb(res_pfb)
                for pid, names in mapping.items():
                    if pid not in all_mappings:
                        all_mappings[pid] = []
                    for name in names:
                        if name not in all_mappings[pid]:
                            all_mappings[pid].append(name)
        except Exception:
            Logger.warn(f'ResolveSpine: Pfb resolve failed to process "{pfb_file}": {stacktrace()}')

    Logger.info(
        f"ResolveSpine: Pfb resolve completed with {len(all_mappings)} total mappings from {len(pfb_files)} pfb files"
    )
    return all_mappings


def _iter_resolved_spine_export_items(
    res: Resource,
    sd_name_mapping: SDPathID2NamesMap,
) -> Generator[SafeSaver.ExportItem, None, None]:
    spines = SpineAsset.from_resource(res)
    if len(spines) >= 10:
        Logger.info(f'ResolveSpine: "{res.name}" has {len(spines)} spines, unpacking it may take a long time.')

    for spine in spines:
        assert spine.sd_pathid is not None
        mapped_names = sd_name_mapping.get(spine.sd_pathid)
        if mapped_names:
            if not isinstance(mapped_names, list):
                mapped_names = [mapped_names]
            for name in mapped_names:
                spine.process_path(name)
                yield from spine.iter_export_items()
        else:
            spine.process_path()
            yield from spine.iter_export_items()


def spine_resolve(
    abfile: str,
    destdir: str,
    sd_name_mapping: SDPathID2NamesMap,
    on_processed: Optional[Callable] = None,
    on_file_queued: Optional[Callable] = None,
    on_file_saved: Optional[Callable] = None,
):
    """Extracts Spine assets from an AB file.

    :param abfile: Path to the AB file;
    :param destdir: Destination directory;
    :param sd_name_mapping: Skeleton data asset path id to names mapping;
    :param on_processed: Callback `f()` for finished, `None` for ignore;
    :param on_file_queued: Callback `f()` invoked when a file was queued, `None` for ignore;
    :param on_file_saved: Callback `f(file_path_or_none_for_not_saved)`, `None` for ignore;
    :rtype: None;
    """
    from .ResolveAB import Resource

    if not osp.isfile(abfile):
        if on_processed:
            on_processed()
        return
    try:
        with open(abfile, "rb") as f:
            res = Resource(UnityPy.load(f))
            for item in _iter_resolved_spine_export_items(res, sd_name_mapping):
                SafeSaver.save_bytes(item.data, destdir, item.name, item.ext, on_file_queued, on_file_saved)
    except BaseException as arg:
        Logger.error(f'ResolveSpine: Error occurred while unpacking file "{abfile}": Exception{type(arg)} {arg}')
    if on_processed:
        on_processed()


def _resolve_spine_task(
    abfile: str,
    destdir: str,
    sd_name_mapping: SDPathID2NamesMap,
    session: ResolveSpineWorkerSession,
):
    if not osp.isfile(abfile):
        session.processed()
        return

    try:
        with open(abfile, "rb") as f:
            res = Resource(UnityPy.load(f))
            for item in _iter_resolved_spine_export_items(res, sd_name_mapping):
                session.save_item(item, destdir)
    except BaseException as arg:
        session.log(
            "error", f'ResolveSpine: Error occurred while unpacking file "{abfile}": Exception{type(arg)} {arg}'
        )
    session.processed()


def _worker_loop(
    task_queue: mp.Queue,
    fs_client_slot: FsGuardClientSlot,
    result_sender: ProcessResultSender,
    sd_name_mapping: SDPathID2NamesMap,
):
    reporter = result_sender.create_reporter()
    Logger.set_forwarder(reporter.log)
    fs_client = fs_client_slot.create_client(reporter)
    session = ResolveSpineWorkerSession(reporter, fs_client)

    while True:
        task = task_queue.get()
        if isinstance(task, StopMessage):
            break
        if not isinstance(task, ResolveSpineTask):
            reporter.log("warn", f'ResolveSpine: Ignoring unexpected worker task type "{type(task).__name__}"')
            continue
        _resolve_spine_task(task.abfile, task.destdir, sd_name_mapping, session)

    session.worker_done()


def main(
    src: str,
    destdir: str,
    do_del: bool = False,
    separate: bool = True,
    pfb_dir: Optional[str] = None,
):
    """Extracts all Spine assets from the given directory or a given AB file.

    :param src: Source directory or file;
    :param destdir: Destination directory;
    :param do_del: Whether to delete the existing files in the destination directory, `False` for default;
    :param separate: Whether to sort the extracted files by their source AB file path;
    :param pfb_dir: Directory containing pfb files for skeleton name mapping, `None` to disable;
    :rtype: None;
    """
    Logger.reset_stats()

    tr_processed = TaskReporter(50, 1)
    tr_file_saving = TaskReporter(1)
    tracker = TaskReporterTracker(tr_processed, tr_file_saving)
    current_stage = TaskValueField("阶段", "正在解析路径")
    current_dir = TaskValueField("当前目录")
    panel = TaskLiveView("正在批量导出Spine模型...")
    panel.set_detail_fields(
        [
            current_stage,
            current_dir,
            TaskDetailField("累计解包", tr_processed.to_progress_str),
            TaskDetailField("累计导出", tr_file_saving.to_progress_str),
            TaskDetailField("运行状态统计", Logger.to_ew_stats_str),
        ]
    )
    panel.bind_tracker(tracker)
    panel.start()

    try:
        Logger.info("ResolveSpine: Retrieving file paths...")
        src = osp.normpath(osp.realpath(src))
        destdir = osp.normpath(osp.realpath(destdir))
        flist = [src] if osp.isfile(src) else []
        if osp.isdir(src):
            for i in glob.iglob(osp.join(glob.escape(src), "**", "*"), recursive=True):
                if osp.isfile(i) and is_ab_file(i):
                    flist.append(i)
        tr_processed.update_demand(len(flist) - 1)

        if do_del:
            current_stage.set_value("正在清理目标目录")
            panel.update()
            rmdir(destdir)

        # Extract skeleton name mapping from pfb files if pfb_dir is provided
        sd_name_mapping = {}
        if pfb_dir is not None and osp.isdir(pfb_dir):
            current_stage.set_value("正在提取骨骼名称映射")
            current_dir.set_value(osp.basename(osp.normpath(pfb_dir)))
            panel.update()
            sd_name_mapping = pfb_resolve(pfb_dir)

        if not flist:
            current_stage.set_value("未找到可处理文件")
            current_dir.set_value(None)
            panel.update()
            CLI.show_summary(
                "Spine 模型批量导出结束", [("结果", "没有找到符合解包条件的文件。")], border_style="yellow"
            )
            return

        ctx = mp.get_context("spawn")
        worker_count = min(len(flist), PerformanceLevel.get_process_limit(Config.get("performance_level")))
        Logger.info(f"ResolveSpine: Using {worker_count} worker processes for {len(flist)} files")

        task_queue: mp.Queue = ctx.Queue(maxsize=max(1, worker_count))
        result_bus = ProcessResultBus(ctx)
        result_sender = result_bus.create_sender()

        fs_guard = FsGuardProcess(
            ctx,
            result_sender,
            worker_count,
            request_queue_maxsize=max(2, min(8, worker_count)),
        )
        workers = [
            ctx.Process(
                target=_worker_loop,
                args=(
                    task_queue,
                    fs_guard.create_client_slot(idx),
                    result_sender,
                    sd_name_mapping,
                ),
                name=f"SpWorker:{idx}",
                daemon=True,
            )
            for idx in range(worker_count)
        ]
        ProcessUtils.start_all(fs_guard, *workers)
        current_stage.set_value("正在分发任务")

        for i in flist:
            current_dir.set_value(osp.basename(osp.dirname(i)))
            panel.update()
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
            task_queue.put(
                ResolveSpineTask(
                    abfile=i,
                    destdir=curdestdir,
                )
            )
        for _ in workers:
            task_queue.put(StopMessage())

        current_stage.set_value("正在处理任务")
        current_dir.set_value(None)
        worker_done = set()
        fs_guard_done = False
        fs_guard_stop_sent = False
        fatal_error = None

        def _set_fs_guard_done(_pid: int):
            nonlocal fs_guard_done
            fs_guard_done = True

        result_bus = (
            result_bus.set_on_file_queued(tr_file_saving.update_demand)
            .set_on_file_saved(tr_file_saving.report)
            .set_on_processed(tr_processed.report)
            .set_on_worker_done(worker_done.add)
            .set_on_fs_guard_done(_set_fs_guard_done)
            .set_on_log(Logger.log)
        )

        while len(worker_done) < len(workers) or not fs_guard_done:
            result_bus.drain(timeout=0.1)

            for worker in workers:
                if worker.exitcode is not None and worker.pid not in worker_done:
                    if worker.exitcode != 0:
                        fatal_error = f'Worker process "{worker.name}" exited unexpectedly with code {worker.exitcode}'
                        Logger.error(f"ResolveSpine: {fatal_error}")
                    worker_done.add(worker.pid)

            if len(worker_done) == len(workers) and not fs_guard_stop_sent:
                fs_guard.stop()
                fs_guard_stop_sent = True

            if fs_guard.exitcode is not None and not fs_guard_done:
                if fs_guard.exitcode != 0:
                    fatal_error = f"FsGuard process exited unexpectedly with code {fs_guard.exitcode}"
                    Logger.error(f"ResolveSpine: {fatal_error}")
                fs_guard_done = True

            if fatal_error:
                break

            panel.update()

        result_bus.drain(timeout=0.0)
        if fatal_error:
            ProcessUtils.terminate_all(*workers, fs_guard)
            raise RuntimeError(fatal_error)
    finally:
        panel.stop()

    ProcessUtils.join_all(*workers, fs_guard)
    result_bus.drain(timeout=0.0)
    for worker in workers:
        if worker.exitcode not in (0, None):
            raise RuntimeError(f'Worker process "{worker.name}" exited with code {worker.exitcode}')
    if fs_guard.exitcode not in (0, None):
        raise RuntimeError(f"FsGuard process exited with code {fs_guard.exitcode}")

    CLI.show_summary(
        "Spine 模型批量导出结束",
        [
            ("累计解包", f"{tr_processed.get_done()} 个文件"),
            ("累计导出", f"{tr_file_saving.get_done()} 个文件"),
            ("耗时", f"{round(tracker.get_rt(), 1)} 秒"),
        ],
    )
