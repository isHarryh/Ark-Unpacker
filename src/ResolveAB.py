# -*- coding: utf-8 -*-
# Copyright (c) 2022-2024, Harry Huang
# @ BSD 3-Clause License
import os.path as osp

import UnityPy
import UnityPy.classes as uc
import UnityPy.files
import UnityPy.streams
from .CombineRGBwithA import AlphaRGBCombiner
from .utils.Config import Config, PerformanceLevel
from .utils.GlobalMethods import print, rmdir, get_filelist, is_ab_file
from .utils.Logger import Logger
from .utils.SaverUtils import SafeSaver
from .utils.TaskUtils import ThreadCtrl, UICtrl, TimeRecorder

class Resource:
    """The class representing a collection of the objects in an UnityPy Environment."""

    def __init__(self, env:UnityPy.Environment):
        """Initializes with the given UnityPy Environment instance.

        :param env: The Environment instance from `UnityPy.load()`;
        :rtype: None;
        """
        if isinstance(env.file, UnityPy.files.File):
            self.name:str = env.file.name
        elif isinstance(env.file, UnityPy.streams.EndianBinaryReader):
            self.name:str = ""
        else:
            raise TypeError(f"Unknown type of UnityPy Environment file: {type(env.file).__name__}")
        self.env:UnityPy.Environment = env
        self.length:int = len(env.objects)
        ###
        self.sprites:"list[uc.Sprite]" = []
        self.texture2ds:"list[uc.Texture2D]" = []
        self.textassets:"list[uc.TextAsset]" = []
        self.audioclips:"list[uc.AudioClip]" = []
        self.materials:"list[uc.Material]" = []
        self.monobehaviors:"list[uc.MonoBehaviour]" = []
        self.spines:"list[Resource.SpineAsset]" = []
        ###
        for i in [o.read() for o in env.objects]:
            if isinstance(i, uc.Sprite):
                self.sprites.append(i)
            elif isinstance(i, uc.Texture2D):
                self.texture2ds.append(i)
            elif isinstance(i, uc.TextAsset):
                self.textassets.append(i)
            elif isinstance(i, uc.AudioClip):
                self.audioclips.append(i)
            elif isinstance(i, uc.Material):
                self.materials.append(i)
            elif isinstance(i, uc.MonoBehaviour):
                self.monobehaviors.append(i)

    def get_object_by_pathid(self, pathid:"int|dict", search_in:"list|None"=None):
        """Gets the object with the given PathID.

        :param pathid: PathID in int or a dict containing `m_PathID` field;
        :param search_in: Searching range, `None` for all objects;
        :returns: The GameObject, `None` for not found;
        """
        _key = 'm_PathID'
        pathid:int = pathid[_key] if isinstance(pathid, dict) and _key in pathid.keys() else pathid
        lst:"list[uc.GameObject]" = self.env.objects if not search_in else search_in
        for i in lst:
            if i.path_id == pathid:
                return i
        return None

    def sort_skeletons(self):
        """Sorts the Spine assets.

        :rtype: None;
        """
        spines:"list[Resource.SpineAsset]" = []
        for mono in self.monobehaviors:
            #(i stans for a MonoBehavior)
            success = False
            if mono.serialized_type.nodes:
                # As asset:
                tree = mono.read_typetree()
                if 'skeletonDataAsset' not in tree.keys():
                    continue # Skip non-skeleton asset
                mono_sd = self.get_object_by_pathid(tree['skeletonDataAsset'], self.monobehaviors)
                if mono_sd.serialized_type.nodes:
                    # As skeleton data asset:
                    tree_sd = mono_sd.read_typetree()
                    skel = self.get_object_by_pathid(tree_sd['skeletonJSON'], self.textassets)
                    mono_ad = self.get_object_by_pathid(tree_sd['atlasAssets'][0], self.monobehaviors)
                    if mono_ad.serialized_type.nodes:
                        # As atlas data asset:
                        tree_ad = mono_ad.read_typetree()
                        atlas = self.get_object_by_pathid(tree_ad['atlasFile'], self.textassets)
                        list2mat = [self.get_object_by_pathid(i, self.materials) for i in tree_ad['materials']]
                        list2tex = []
                        for mat in list2mat:
                            tex_rgb, tex_alpha = None, None
                            if mat.serialized_type.nodes:
                                # As material asset:
                                tree_mat = mat.read_typetree()
                                tex_envs = tree_mat['m_SavedProperties']['m_TexEnvs']
                                for tex in tex_envs:
                                    if tex[0] == '_MainTex':
                                        tex_rgb = self.get_object_by_pathid(tex[1]['m_Texture'], self.texture2ds)
                                    elif tex[0] == '_AlphaTex':
                                        tex_alpha = self.get_object_by_pathid(tex[1]['m_Texture'], self.texture2ds)
                            list2tex.append((tex_rgb, tex_alpha))
                        # Pack into Spine asset instance
                        spine = Resource.SpineAsset(skel, atlas, list2tex)
                        if spine.is_available():
                            # Succeeded
                            if skel.name.lower().startswith('dyn_'):
                                spine.type = Resource.SpineAsset.DYN_ILLUST
                            elif 'Relax' in tree['_animationName'] or skel.name.lower().startswith('build_'):
                                spine.type = Resource.SpineAsset.BUILDING
                            else:
                                spine.type = Resource.SpineAsset.BATTLE_FRONT if spine.is_front_geq_back() else Resource.SpineAsset.BATTLE_BACK
                            spines.append(spine)
                            success = True
            if not success:
                Logger.warn(f"ResolveAB: Failed to handle skeletonDataAsset at pathId {mono.path_id} of {skel.name}.")
        self.spines = spines

    def rename_skeletons(self):
        """Renames the Spine assets which includes skel, atlas and png files.
        Since the Spine in Arknights have 4 or more forms (Building, BattleFront, BattleBack, DynIllust),
        it is necessary to rename them so that name collisions can be avoid.

        :rtype: None;
        """
        for spine in self.spines:
            prefix = spine.get_common_name() + osp.sep
            if spine.type == Resource.SpineAsset.BUILDING:
                prefix = 'Building' + osp.sep + prefix
            elif spine.type == Resource.SpineAsset.BATTLE_FRONT:
                prefix = 'BattleFront' + osp.sep + prefix
            elif spine.type == Resource.SpineAsset.BATTLE_BACK:
                prefix = 'BattleBack' + osp.sep + prefix
            elif spine.type == Resource.SpineAsset.DYN_ILLUST:
                prefix = 'DynIllust' + osp.sep + prefix
            self.__rename_add_prefix(spine.skel, prefix)
            self.__rename_add_prefix(spine.atlas, prefix)
            for i in spine.tex_list:
                for j in i:
                    if j:
                        self.__rename_add_prefix(j, prefix)

    @staticmethod
    def __rename_add_prefix(obj:uc.GameObject, pre:str):
        """Adds a prefix to rename the Spine-related files."""
        if not obj.name.startswith(pre):
            obj.name = str(pre + obj.name)

    class SpineAsset:
        UNKNOWN = 0
        BUILDING = 1
        BATTLE_FRONT = 2
        BATTLE_BACK = 3
        DYN_ILLUST = 4

        def __init__(self, skel:uc.TextAsset, atlas:uc.TextAsset, tex_list:"list[tuple[uc.Texture2D]]", type:int=UNKNOWN):
            self.skel = skel
            self.atlas = atlas
            self.tex_list = tex_list
            self.type = type

        def is_front_geq_back(self):
            t = self.atlas.text
            return t.count('\nF_') + t.count('\nf_') + t.count('\nC_') + t.count('\nc_') >= t.count('\nB_') + t.count('\nb_')

        def is_available(self):
            if not isinstance(self.skel, uc.TextAsset) or not isinstance(self.atlas, uc.TextAsset):
                return False
            if not isinstance(self.tex_list, list) or len(self.tex_list) == 0:
                return False
            return True

        def get_common_name(self):
            if isinstance (self.atlas, uc.TextAsset):
                return osp.splitext(osp.basename(self.atlas.name))[0]
            return "Unknown"

        def save_spine(self, destdir:str, on_queued:staticmethod, on_saved:staticmethod):
            if self.is_available():
                for i in self.tex_list:
                    if i[0]:
                        rgb = i[0].image
                        if i[1]:
                            rgba = AlphaRGBCombiner(i[1].image).combine_with(rgb)
                        else:
                            Logger.debug(f"ResolveAB: Spine asset \"{i[0].name}\" found with no Alpha texture.")
                            rgba = rgb
                        if SafeSaver.save_image(rgba, destdir, i[0].name, on_queued=on_queued, on_saved=on_saved):
                            Logger.debug(f"ResolveAB: Spine asset \"{i[0].name}\" found.")
                    else:
                        Logger.warn("ResolveAB: Spine asset RGB texture missing.")
                for i in (self.atlas, self.skel):
                    SafeSaver.save_object(i, destdir, i.name, on_queued, on_saved)
                    Logger.debug(f"ResolveAB: Spine asset \"{i.name}\" found.")
        #EndClass
    #EndClass


def ab_resolve(abfile:str, destdir:str, \
               do_img:bool, do_txt:bool, do_aud:bool, do_spine:bool, \
               on_processed:staticmethod=None, on_file_queued:staticmethod=None, on_file_saved:staticmethod=None):
    """Extracts an AB file.

    :param abfile: Path to the AB file;
    :param destdir: Destination directory;
    :param do_img: Whether to extract images;
    :param do_txt: Whether to extract text scripts;
    :param do_aud: Whether to extract audios;
    :param do_spine: Whether to extract Spine assets, note that the Spine assets may have some identical file with the images/scripts;
    :param on_processed: Callback `f()` for finished, `None` for ignore;
    :param on_file_queued: Callback `f()` invoked when a file was queued, `None` for ignore;
    :param on_file_saved: Callback `f(file_path_or_none_for_not_saved)`, `None` for ignore;
    :rtype: None;
    """
    if not osp.isfile(abfile):
        if on_processed:
            on_processed()
        return
    ###
    res = Resource(UnityPy.load(abfile))
    Logger.debug(f"ResolveAB: \"{res.name}\" has {res.length} objects.")
    if res.length >= 10000:
        Logger.info(f"ResolveAB: Too many objects in file \"{res.name}\", unpacking it may take a long time.")
    elif res.length == 0:
        Logger.info(f"ResolveAB: No object in file \"{res.name}\".")
    ###
    try:
        # Preprocess
        res.sort_skeletons()
        res.rename_skeletons()
        ###
        if do_spine:
            for i in res.spines:
                i.save_spine(destdir, on_file_queued, on_file_saved)
        if do_img:
            SafeSaver.save_objects(res.sprites, destdir, on_file_queued, on_file_saved)
            SafeSaver.save_objects(res.texture2ds, destdir, on_file_queued, on_file_saved)
        if do_txt:
            SafeSaver.save_objects(res.textassets, destdir, on_file_queued, on_file_saved)
        if do_aud:
            SafeSaver.save_objects(res.audioclips, destdir, on_file_queued, on_file_saved)
    except BaseException as arg:
        # Error feedback
        Logger.error(f"ResolveAB: Error occurred while unpacking file \"{res.name}\": Exception{type(arg)} {arg}")
        # raise(arg)
    if on_processed:
        on_processed()


########## Main-主程序 ##########
def main(src:str, destdir:str, do_del:bool=False,
    do_img:bool=True, do_txt:bool=True, do_aud:bool=True, do_spine:bool=False, separate:bool=True):
    """Extract all the AB files from the given directory or extract a given AB file.

    :param src: Source directory or file;
    :param destdir: Destination directory;
    :param do_del: Whether to delete the existing files in the destination directory, `False` for default;
    :param do_img: Whether to extract images;
    :param do_txt: Whether to extract text scripts;
    :param do_aud: Whether to extract audios;
    :param do_spine: Whether to extract Spine assets, note that the Spine assets may have some identical file with the images/scripts;
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
        rmdir(destdir) # Danger zone
    SafeSaver.get_instance().reset_counter()
    thread_ctrl = ThreadCtrl(PerformanceLevel.get_thread_limit(Config.get('performance_level')))
    ui = UICtrl()
    recorder = TimeRecorder()
    recorder.update_dest(50, len(flist))
    on_processed = lambda: recorder.done_once(50)
    on_file_queued = lambda: recorder.update_dest(1)
    on_file_saved = lambda x: (recorder.done_once(1) if x else recorder.update_dest(1, -1), \
                               Logger.debug(f"ResolveAB: Saved \"{x}\"") if x else None)

    ui.reset()
    ui.loop_start()
    for i in flist:
        #(i stands for a file's path)
        ui.request([
            "正在批量解包...",
            recorder.get_progress_str(),
            f"当前目录：\t{osp.basename(osp.dirname(i))}",
            f"当前文件：\t{osp.basename(i)}",
            f"累计解包：\t{recorder.get_done_dest_str_of(50)}",
            f"累计导出：\t{recorder.get_done_dest_str_of(1)}",
            f"剩余时间：\t{recorder.get_eta_str()}",
        ])
        ###
        subdestdir = osp.dirname(i).strip(osp.sep).replace(src, '').strip(osp.sep)
        curdestdir = destdir if osp.samefile(i, src) else \
            osp.join(destdir, subdestdir, osp.splitext(osp.basename(i))[0]) if separate else \
            osp.join(destdir, subdestdir)
        thread_ctrl.run_subthread(ab_resolve, (i, curdestdir, do_img, do_txt, do_aud, do_spine, on_processed, on_file_queued, on_file_saved), \
            name=f"RsThread:{id(i)}")

    ui.reset()
    ui.loop_stop()
    while thread_ctrl.count_subthread() or not SafeSaver.get_instance().completed() or recorder.get_progress() < 1:
        ui.request([
            "正在批量解包...",
            recorder.get_progress_str(),
            f"累计解包：\t{recorder.get_done_dest_str_of(50)}",
            f"累计导出：\t{recorder.get_done_dest_str_of(1)}",
            f"剩余时间：\t{recorder.get_eta_str()}",
        ])
        ui.refresh(post_delay=0.1)

    ui.reset()
    print("\n批量解包结束!", s=1)
    print(f"  累计解包 {recorder.get_done_of(50)} 个文件")
    print(f"  累计导出 {recorder.get_done_of(1)} 个文件")
    print(f"  此项用时 {round(recorder.get_rt(), 1)} 秒")
