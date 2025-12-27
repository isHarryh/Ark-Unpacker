# -*- coding: utf-8 -*-
# Copyright (c) 2022-2025, Harry Huang
# @ BSD 3-Clause License
from enum import StrEnum
from typing import Callable, List, Optional, Sequence, TYPE_CHECKING, Union

import os.path as osp

import UnityPy
import UnityPy.classes as uc
from spine_asset.v38 import AtlasFile, SkeletonBinary, SkeletonJson, SkeletonData

from .CombineRGBwithA import AlphaRGBCombiner, image_resize
from .utils.GlobalMethods import print, rmdir, get_filelist, is_ab_file, stacktrace
from .utils.Logger import Logger
from .utils.SaverUtils import SafeSaver
from .utils.TaskUtils import ThreadCtrl, UICtrl, TaskReporter, TaskReporterTracker

if TYPE_CHECKING:
    from .ResolveAB import Resource


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

    @property
    def name(self) -> str:
        return self.obj.m_Name

    def add_prefix(self, prefix: str):
        """Adds a prefix to the name of the Spine asset object to avoid conflicts.

        :param prefix: The prefix to add;
        :rtype: None;
        """
        if not self.obj.m_Name.startswith(prefix):
            self.obj.m_Name = prefix + self.obj.m_Name


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
                return (
                    SpineType.DYN_ILLUST
                )  # Not reliable, DYN_ILLUST_START may also match this
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
                    Logger.info(
                        f'ResolveSpine: Unknown dynamic illust Spine type of "{t}", animations={anim_names}'
                    )
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

    def add_prefix(self, prefix: str):
        super().add_prefix(prefix)
        if self.tex_alpha and not self.tex_alpha.m_Name.startswith(prefix):
            self.tex_alpha.m_Name = prefix + self.tex_alpha.m_Name


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

    def rename_by_sd_mapping(self, skel_name_mapping: dict):
        """Renames the Spine asset based on skeleton data mapping.

        This is used to differentiate same-skeleton different-skin models.
        Renames skeleton, atlas, and texture assets to match the GameObject name.

        :param skel_name_mapping: Dict mapping skeleton data asset path id to names;
        :rtype: None;
        """
        if not self.sd_pathid:
            return
        if self.sd_pathid not in skel_name_mapping:
            return

        custom_name = skel_name_mapping[self.sd_pathid]
        modified = 0

        # Rename skeleton
        old_skel_base = osp.splitext(self.skel_handler.name)[0]
        skel_ext = osp.splitext(self.skel_handler.name)[1]
        new_skel_name = custom_name + skel_ext
        if self.skel_handler.obj.m_Name != new_skel_name:
            self.skel_handler.obj.m_Name = new_skel_name
            modified += 1

        # Rename atlas to match skeleton name
        old_atlas_base = osp.splitext(self.atlas_handler.name)[0]
        atlas_ext = osp.splitext(self.atlas_handler.name)[1]
        new_atlas_name = custom_name + atlas_ext
        if self.atlas_handler.obj.m_Name != new_atlas_name:
            self.atlas_handler.obj.m_Name = new_atlas_name
            modified += 1

        # Rename textures to match skeleton name
        for tex_handler in self.tex_handlers:
            old_tex_base = osp.splitext(tex_handler.name)[0]
            tex_ext = osp.splitext(tex_handler.name)[1]

            # If texture has a suffix (e.g., _02), preserve it
            if old_tex_base != old_atlas_base and old_tex_base.startswith(
                old_atlas_base
            ):
                suffix = old_tex_base[len(old_atlas_base) :]
                new_tex_name = custom_name + suffix + tex_ext
            else:
                new_tex_name = custom_name + tex_ext

            if tex_handler.tex_rgb.m_Name != new_tex_name:
                tex_handler.tex_rgb.m_Name = new_tex_name
                modified += 1

        if modified > 0:
            Logger.info(
                f'ResolveSpine: Renamed Spine assets to "{custom_name}" based on skeleton data mapping (modified {modified} objects)'
            )

    def add_prefix(self):
        """Adds a prefix to the names of the Spine asset objects to avoid conflicts.

        :rtype: None;
        """
        prefix = f"{self.type.value}/{osp.splitext(osp.basename(self.atlas_handler.name))[0]}/"
        for h in list((self.atlas_handler, self.skel_handler)) + list(
            self.tex_handlers
        ):
            h.add_prefix(prefix)

    def save_spine(
        self,
        destdir: str,
        on_queued: Optional[Callable],
        on_saved: Optional[Callable],
    ):
        """Saves the Spine assets to the destination directory.

        :param destdir: Destination directory;
        :param on_queued: Callback `f(file_path)` invoked when a file was queued, `None` for ignore;
        :param on_saved: Callback `f(file_path_or_none_for_not_saved)` invoked when a file was saved, `None` for ignore;
        :rtype: None;
        """
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
                Logger.debug(
                    f'ResolveSpine: Spine asset "{tex.name}" found with Alpha texture.'
                )
                rgba = AlphaRGBCombiner(tex.alpha).combine_with(tex.rgb)
            else:
                Logger.debug(
                    f'ResolveSpine: Spine asset "{tex.name}" found with NO Alpha texture.'
                )
                rgba = AlphaRGBCombiner.apply_premultiplied_alpha(tex.rgb)
            SafeSaver.save_image(
                rgba,
                destdir,
                tex.name,
                on_queued=on_queued,
                on_saved=on_saved,
            )
        for i in (self.atlas_handler, self.skel_handler):
            SafeSaver.save_object(i.obj, destdir, i.name, on_queued, on_saved)

    @classmethod
    def _extract_skeleton_name_mapping_from_pfb(cls, res: "Resource") -> dict:
        """Extracts skeleton data asset path id to GameObject name mapping from pfb resource.

        This is used to differentiate same-skeleton different-skin models that have
        identical internal skeleton names (e.g., enemy_1046_agent vs enemy_1046_agent_2).

        :param res: The Resource instance (pfb file) to extract mappings from;
        :returns: A dict mapping skeleton data asset path id to GameObject m_Name;
        """
        mapping = {}
        try:
            for obj in res.get_objects_by_type(uc.GameObject):
                with TreeReader(obj) as tree_go:
                    m_name = tree_go.get("m_Name", "")
                    if not m_name.startswith("enemy_"):
                        continue

                    for comp in tree_go.get("m_Component", []):
                        comp_ref = comp.get("component", {})
                        if "m_PathID" not in comp_ref:
                            continue
                        comp_obj = res.get_object_by_pathid(comp_ref, uc.Component)
                        if comp_obj is None:
                            continue

                        with TreeReader(comp_obj) as tree_comp:
                            if "_animator" not in tree_comp:
                                continue
                            animator_ref = tree_comp.get("_animator", {})
                            if "m_PathID" not in animator_ref:
                                continue
                            animator_obj = res.get_object_by_pathid(
                                animator_ref, uc.MonoBehaviour
                            )
                            if animator_obj is None:
                                continue

                            with TreeReader(animator_obj) as tree_animator:
                                skeleton_ref = tree_animator.get("_skeleton", {})
                                if "m_PathID" not in skeleton_ref:
                                    Logger.info(
                                        f'ResolveSpine: Pfb mapping skeleton reference not found in animator of "{m_name}", may be non-spine character'
                                    )
                                    continue
                                skeleton_obj = res.get_object_by_pathid(
                                    skeleton_ref, uc.MonoBehaviour
                                )
                                if skeleton_obj is None:
                                    continue

                                with TreeReader(skeleton_obj) as tree_skel:
                                    skel_data_ref = tree_skel.get(
                                        "skeletonDataAsset", {}
                                    )
                                    if "m_PathID" in skel_data_ref:
                                        skel_data_pathid = skel_data_ref["m_PathID"]
                                        mapping[skel_data_pathid] = m_name
                                        Logger.debug(
                                            f'ResolveSpine: Pfb mapping mapped skeleton data asset {skel_data_pathid} to "{m_name}"'
                                        )
                                        break
        except Exception:
            Logger.warn(
                f'ResolveSpine: Pfb mapping failed to process pfb "{res.name}": {stacktrace()}'
            )
        Logger.info(
            f'ResolveSpine: Pfb mapping extracted total {len(mapping)} skeleton name mappings from pfb "{res.name}"'
        )
        return mapping

    @classmethod
    def from_resource(cls, res: "Resource") -> List["SpineAsset"]:
        """Gets Spine assets from the given resource.

        :param res: The Resource instance to extract Spine assets from;
        :returns: A list of SpineAsset instances;
        """
        spines = []
        found_front_and_back = list(cls._find_front_and_back_skel_data(res))
        try:
            # sd = SkeletonData
            for mono_sd, tree_sd in cls._find_typetree_by_keys(
                res.get_objects_by_type(uc.MonoBehaviour),
                ["atlasAssets", "skeletonJSON"],
            ):
                skel = res.get_object_by_pathid(tree_sd["skeletonJSON"], uc.TextAsset)
                mono_ad = res.get_object_by_pathid(
                    tree_sd["atlasAssets"][0], uc.MonoBehaviour
                )
                # ad = AtlasData
                with TreeReader(mono_ad) as tree_ad:
                    atlas = res.get_object_by_pathid(tree_ad["atlasFile"], uc.TextAsset)
                    tex_handlers: List[SpineTextureHandler] = []
                    for mat in (
                        res.get_object_by_pathid(i, uc.Material)
                        for i in tree_ad["materials"]
                    ):
                        # mat = MaterialData
                        tex_rgb, tex_alpha = None, None
                        with TreeReader(mat) as tree_mat:
                            tex_envs = tree_mat["m_SavedProperties"]["m_TexEnvs"]
                            for tex in tex_envs:
                                if tex[0] == "_MainTex":
                                    tex_rgb = res.get_object_by_pathid(
                                        tex[1]["m_Texture"], uc.Texture2D
                                    )
                                elif tex[0] == "_AlphaTex":
                                    tex_alpha = res.get_object_by_pathid(
                                        tex[1]["m_Texture"], uc.Texture2D
                                    )
                        if tex_rgb is None:
                            raise ValueError("RGB main texture not found")
                        tex_handlers.append(SpineTextureHandler(tex_rgb, tex_alpha))

                    if not skel or not atlas or not tex_handlers:
                        raise ValueError("Incomplete Spine asset")

                    sd_pathid = (
                        mono_sd.object_reader.path_id if mono_sd.object_reader else None
                    )

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
            Logger.warn(
                f'ResolveSpine: Failed to handle skeletons in resource "{res.name}": {stacktrace()}'
            )
        return spines

    @classmethod
    def _find_front_and_back_skel_data(cls, res: "Resource"):
        try:
            # ca = CharacterAnimator
            for _, tree_ca in cls._find_typetree_by_keys(
                res.get_objects_by_type(uc.MonoBehaviour),
                ["_animations", "_front", "_back"],
            ):
                mono_sa_front = res.get_object_by_pathid(
                    tree_ca["_front"]["skeleton"], uc.MonoBehaviour
                )
                mono_sa_back = res.get_object_by_pathid(
                    tree_ca["_back"]["skeleton"], uc.MonoBehaviour
                )
                # sa = SkeletonAnimation
                if mono_sa_front and mono_sa_back:
                    with TreeReader(mono_sa_front) as tree_sa:
                        mono_sd_front = res.get_object_by_pathid(
                            tree_sa["skeletonDataAsset"], uc.MonoBehaviour
                        )
                    with TreeReader(mono_sa_back) as tree_sa:
                        mono_sd_back = res.get_object_by_pathid(
                            tree_sa["skeletonDataAsset"], uc.MonoBehaviour
                        )
                    # sd = SkeletonData
                    if mono_sd_front and mono_sd_back:
                        yield mono_sd_front, mono_sd_back
        except Exception:
            Logger.warn(
                f'ResolveSpine: Failed to find front-and-back skeleton data in resource "{res.name}": {stacktrace()}'
            )

    @classmethod
    def _find_typetree_by_keys(
        cls, objs: Sequence[uc.Object], contains_keys: Sequence[str]
    ):
        for obj in objs:
            with TreeReader(obj) as tree:
                if not all(k in tree for k in contains_keys):
                    continue
                yield obj, tree


def pfb_resolve(srcdir: str) -> dict:
    """Extracts skeleton data asset path id to GameObject name mappings from all pfb files.

    :param srcdir: Source directory containing pfb files;
    :returns: A dict mapping skeleton data asset path id to GameObject m_Name;
    """
    from .ResolveAB import Resource

    Logger.info(f'ResolveSpine: Pfb resolve started for directory "{srcdir}"')
    srcdir = osp.normpath(osp.realpath(srcdir))
    pfb_files = get_filelist(srcdir) if osp.isdir(srcdir) else [srcdir]
    pfb_files = [f for f in pfb_files if is_ab_file(f) and "enm_pfb_" in f]

    all_mappings = {}
    for pfb_file in pfb_files:
        try:
            Logger.debug(f'ResolveSpine: Pfb resolve processing "{pfb_file}"')
            with open(pfb_file, "rb") as f:
                res_pfb = Resource(UnityPy.load(f))
                mapping = SpineAsset._extract_skeleton_name_mapping_from_pfb(res_pfb)
                all_mappings.update(mapping)
        except Exception:
            Logger.warn(
                f'ResolveSpine: Pfb resolve failed to process "{pfb_file}": {stacktrace()}'
            )

    Logger.info(
        f"ResolveSpine: Pfb resolve completed with {len(all_mappings)} total mappings from {len(pfb_files)} pfb files"
    )
    return all_mappings


def spine_resolve(
    abfile: str,
    destdir: str,
    sd_name_mapping: dict,
    on_processed: Optional[Callable] = None,
    on_file_queued: Optional[Callable] = None,
    on_file_saved: Optional[Callable] = None,
):
    """Extracts Spine assets from an AB file.

    :param abfile: Path to the AB file;
    :param destdir: Destination directory;
    :param sd_name_mapping: Skeleton data asset path id to name mapping;
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
        # Now extract Spine assets from the given AB file
        with open(abfile, "rb") as f:
            res = Resource(UnityPy.load(f))
            spines = SpineAsset.from_resource(res)
            if len(spines) >= 10:
                Logger.info(
                    f'ResolveSpine: "{res.name}" has {len(spines)} spines, unpacking it may take a long time.'
                )
            for s in spines:
                s.rename_by_sd_mapping(sd_name_mapping)
                s.add_prefix()
                s.save_spine(destdir, on_file_queued, on_file_saved)
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
    print("\n正在解析路径...", s=1)
    Logger.info("ResolveSpine: Retrieving file paths...")
    src = osp.normpath(osp.realpath(src))
    destdir = osp.normpath(osp.realpath(destdir))
    flist = [src] if osp.isfile(src) else get_filelist(src)
    flist = list(filter(is_ab_file, flist))
    if do_del:
        print("\n正在清理...", s=1)
        rmdir(destdir)

    # Extract skeleton name mapping from pfb files if pfb_dir is provided
    sd_name_mapping = {}
    if pfb_dir is not None and osp.isdir(pfb_dir):
        print(f"\n正在从 {pfb_dir} 中提取额外的骨骼名称映射...", s=1)
        sd_name_mapping = pfb_resolve(pfb_dir)

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
        ui.request(
            [
                "正在批量导出Spine模型...",
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
            spine_resolve,
            (
                i,
                curdestdir,
                sd_name_mapping,
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
                "正在批量导出Spine模型...",
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
    print("\nSpine模型批量导出结束!", s=1)
    print(f"  累计解包 {tr_processed.get_done()} 个文件")
    print(f"  累计导出 {tr_file_saving.get_done()} 个文件")
    print(f"  此项用时 {round(tracker.get_rt(), 1)} 秒")
