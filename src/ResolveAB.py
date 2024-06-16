# -*- coding: utf-8 -*-
# Copyright (c) 2022-2024, Harry Huang
# @ BSD 3-Clause License
import os.path, time
import UnityPy
from .utils import *
from .CombineRGBwithA import combine_rgb_a
from UnityPy.classes import *


class Resource:
    """The class representing a collection of the objects in an UnityPy Environment."""

    def __init__(self, env:UnityPy.Environment):
        """Initializes with the given UnityPy Environment instance.

        :param env: The Environment instance from `UnityPy.load()`;
        :rtype: None;
        """
        self.env:UnityPy.Environment = env
        self.name:str = env.file.name
        self.length:int = len(env.objects)
        ###
        self.sprites:list[Sprite] = []
        self.texture2ds:list[Texture2D] = []
        self.textassets:list[TextAsset] = []
        self.audioclips:list[AudioClip] = []
        self.materials:list[Material] = []
        self.monobehaviors:list[MonoBehaviour] = []
        self.spines:list[Resource.SpineAsset] = []
        ###
        for i in [o.read() for o in env.objects]:
            if isinstance(i, Sprite):
                self.sprites.append(i)
            elif isinstance(i, Texture2D):
                self.texture2ds.append(i)
            elif isinstance(i, TextAsset):
                self.textassets.append(i)
            elif isinstance(i, AudioClip):
                self.audioclips.append(i)
            elif isinstance(i, Material):
                self.materials.append(i)
            elif isinstance(i, MonoBehaviour):
                self.materials.append(i)
    
    def get_object_by_pathid(self, pathid:"int|dict", search_in:"list|None"=None):
        """Gets the object with the given PathID.

        :param pathid: PathID in int or a dict containing `m_PathID` field;
        :param search_in: Searching range, `None` for all objects;
        :returns: The GameObject, `None` for not found;
        """
        _key = 'm_PathID'
        pathid:int = pathid[_key] if type(pathid) == dict and _key in pathid.keys() else pathid
        lst:list[GameObject] = self.env.objects if not search_in else search_in
        for i in lst:
            if i.path_id == pathid:
                return i
        return None

    def sort_skeletons(self):
        """Sorts the Spine assets.
        
        :rtype: None;
        """
        spines:list[Resource.SpineAsset] = []
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
                            if len(skel.name) > 4 and skel.name[:4] == 'dyn_':
                                spine.type = Resource.SpineAsset.DYN_ILLUST
                            elif 'Relax' in tree['_animationName'] or \
                                (len(skel.name) > 6 and skel.name[:6] == 'build_'):
                                spine.type = Resource.SpineAsset.BUILDING
                            else:
                                spine.type = Resource.SpineAsset.BATTLE_FRONT if spine.is_front_geq_back() else Resource.SpineAsset.BATTLE_BACK
                            spines.append(spine)
                            success = True
            if not success:
                Logger.warn(f'ResolveAB: Failed to handle skeletonDataAsset at pathId {mono.path_id} of {self.name}.')
        self.spines = spines
    
    def rename_skeletons(self):
        """Renames the Spine assets which includes skel, atlas and png files.
        Since the Spine in Arknights have 4 or more forms (Building, BattleFront, BattleBack, DynIllust),
        it is necessary to rename them so that name collisions can be avoid.
        
        :rtype: None;
        """
        for spine in self.spines:
            prefix = spine.get_common_name() + os.path.sep
            if spine.type == Resource.SpineAsset.BUILDING:
                prefix = 'Building' + os.path.sep + prefix
            elif spine.type == Resource.SpineAsset.BATTLE_FRONT:
                prefix = 'BattleFront' + os.path.sep + prefix
            elif spine.type == Resource.SpineAsset.BATTLE_BACK:
                prefix = 'BattleBack' + os.path.sep + prefix
            elif spine.type == Resource.SpineAsset.DYN_ILLUST:
                prefix = 'DynIllust' + os.path.sep + prefix
            self.__rename_add_prefix(spine.skel, prefix)
            self.__rename_add_prefix(spine.atlas, prefix)
            for i in spine.tex_list:
                for j in i:
                    if j:
                        self.__rename_add_prefix(j, prefix)

    @staticmethod
    def __rename_add_prefix(obj:GameObject, pre:str):
        """Adds a prefix to rename the Spine-related files."""
        if len(obj.name) <= len(pre) or obj.name[:len(pre)] != pre:
            obj.name = str(pre + obj.name)

    class SpineAsset:
        UNKNOWN = 0
        BUILDING = 1
        BATTLE_FRONT = 2
        BATTLE_BACK = 3
        DYN_ILLUST = 4

        def __init__(self, skel:TextAsset, atlas:TextAsset, tex_list:"list[tuple[Texture2D]]", type:int=UNKNOWN):
            self.skel = skel
            self.atlas = atlas
            self.tex_list = tex_list
            self.type = type
        
        def is_front_geq_back(self):
            t = self.atlas.text
            return t.count('\nF_') + t.count('\nf_') + t.count('\nC_') + t.count('\nc_') >= t.count('\nB_') + t.count('\nb_')
        
        def is_available(self):
            if type(self.skel) != TextAsset or type(self.atlas) != TextAsset:
                return False
            if type(self.tex_list) != list or len(self.tex_list) == 0:
                return False
            return True
        
        def get_common_name(self):
            if type(self.atlas) == TextAsset:
                return os.path.splitext(os.path.basename(self.atlas.name))[0]
            return "Unknown"
        
        def save_spine(self, destdir:str, callback:staticmethod=None):
            if self.is_available():
                for i in self.tex_list:
                    if i[0]:
                        rgb = i[0].image
                        if i[1]:
                            rgba = combine_rgb_a(rgb, i[1].image)
                        else:
                            Logger.info(f"ResolveAB: Spine asset \"{i[0].name}\" found with no Alpha texture.")
                            rgba = rgb
                        if SafeSaver.save_image(rgba, destdir, i[0].name, callback=callback):
                            Logger.debug(f"ResolveAB: Spine asset \"{i[0].name}\" found.")
                    else:
                        Logger.warn(f"ResolveAB: Spine asset RGB texture missing.")
                for i in (self.atlas, self.skel):
                    SafeSaver.save_object(i, destdir, i.name, callback)
                    Logger.debug(f"ResolveAB: Spine asset \"{i.name}\" found.")
        #EndClass
    #EndClass


def ab_resolve(abfile:str, destdir:str, \
    doimg:bool, dotxt:bool, doaud:bool, dospine:bool, \
    callback:staticmethod, subcallback:staticmethod):
    """Extracts an AB file.

    :param abfile: Path to the AB file;
    :param destdir: Destination directory;
    :param doimg: Whether to extract images;
    :param dotxt: Whether to extract text scripts;
    :param doaud: Whether to extract audios;
    :param dospine: Whether to extract Spine assets, note that the Spine assets may have some identical file with the images/scripts;
    :param callback: Callback `f()` for finished, `None` for ignore;
    :param subcallback: Callback `f(game_object_name, file_path_or_none_for_not_saved)` for every saving trail, `None` for ignore;
    :rtype: None;
    """
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
        if dospine:
            for i in res.spines:
                i.save_spine(destdir, subcallback)
        if doimg:
            SafeSaver.save_objects(res.sprites, destdir, subcallback)
            SafeSaver.save_objects(res.texture2ds, destdir, subcallback)
        if dotxt:
            SafeSaver.save_objects(res.textassets, destdir, subcallback)
        if doaud:
            SafeSaver.save_objects(res.audioclips, destdir, subcallback)
    except BaseException as arg:
        # Error feedback
        Logger.error(f"ResolveAB: Error occurred while unpacking file \"{res.name}\": Exception{type(arg)} {arg}")
        # raise(arg)
    if callback:
        callback()


########## Main-主程序 ##########
def main(rootdir:str, destdir:str, dodel:bool=False, 
    doimg:bool=True, dotxt:bool=True, doaud:bool=True, dospine:bool=False, separate:bool=True):
    """Extract all the AB files from the given directory.

    :param rootdir: Source directory;
    :param destdir: Destination directory;
    :param dodel: Whether to delete the existing files in the destination directory, `False` for default;
    :param doimg: Whether to extract images;
    :param dotxt: Whether to extract text scripts;
    :param doaud: Whether to extract audios;
    :param dospine: Whether to extract Spine assets, note that the Spine assets may have some identical file with the images/scripts;
    :param separate: Whether to sort the extracted files by their source AB file path.
    :rtype: None;
    """
    print("\n正在解析目录...", s=1)
    Logger.info("ResolveAB: Reading directories...")
    ospath = os.path
    rootdir = ospath.normpath(ospath.realpath(rootdir))
    destdir = ospath.normpath(ospath.realpath(destdir))
    flist = [] # All-files list
    flist = get_filelist(rootdir)
    flist = list(filter(lambda x:ospath.splitext(x)[1] in ['.ab', '.AB'], flist))

    if dodel:
        print("\n正在清理...", s=1)
        rmdir(destdir) # Danger zone
    SafeSaver.get_instance().reset_counter()
    Cprogs = Counter()
    Cfiles = Counter()
    TC = ThreadCtrl(PerformanceLevel.get_thread_limit(Config.get('performance_level')))
    UI = UICtrl(0.5)
    TR = TimeRecorder(len(flist))
    callback = lambda: (Cprogs.update(), TR.update())
    subcallback = lambda x, y: (Cfiles.update(y), Logger.debug(f"ResolveAB: \"{x}\" -> \"{y}\""))

    UI.reset()
    UI.loop_start()
    for i in flist:
        #(i stands for a file's path)
        if not ospath.isfile(i):
            continue # Skip non-file
        TR_p = TR.get_progress()
        TR_r = TR.get_remaining_time()
        UI.request([
            f'正在批量解包...',
            f'|{progress_bar(TR_p, 25)}| {color(2, 0, 1)}{round(TR_p*100, 1)}%',
            f'当前目录：\t{ospath.basename(ospath.dirname(i))}',
            f'当前文件：\t{ospath.basename(i)}',
            f'累计解包：\t{Cprogs.now()}',
            f'累计导出：\t{Cfiles.now()}',
            f'剩余时间：\t{f"{round(TR_r / 60, 1)}min" if TR_r > 0 else "计算中"}',
        ])
        ###
        subdestdir = ospath.dirname(i).strip(ospath.sep).replace(rootdir, '').strip(ospath.sep)
        curdestdir = os.path.join(destdir, subdestdir, ospath.splitext(ospath.basename(i))[0]) \
            if separate else os.path.join(destdir, subdestdir)
        TC.run_subthread(ab_resolve, (i, curdestdir, doimg, dotxt, doaud, dospine, callback, subcallback), \
            name=f"RsThread:{id(i)}")

    spin = LineSpinner()
    UI.reset()
    UI.loop_stop()
    while TC.count_subthread() or not SafeSaver.get_instance().completed():
        # Waiting for sub threads to terminate
        while TR.get_progress() < 1:
            TR_p = TR.get_progress()
            TR_r = TR.get_remaining_time()
            UI.request([
                f'正在批量解包...',
                f'|{progress_bar(TR_p, 25)}| {color(2, 0, 1)}{round(TR_p*100, 1)}%',
                f'累计解包：\t{Cprogs.now()}',
                f'累计导出：\t{Cfiles.now()}',
                f'剩余时间：\t{f"{round(TR_r / 60, 1)}min" if TR_r > 0 else "计算中"}',
            ])
            UI.refresh(post_delay=0.2)
        UI.request([
            f'正在批量解包...',
            f'|正在等待子进程结束| {color(2, 0, 1)}{spin.next()}',
            f'累计解包：\t{Cprogs.now()}',
            f'累计导出：\t{Cfiles.now()}',
            f'剩余时间：\t--',
        ])
        UI.refresh(post_delay=0.2)

    UI.reset()
    print(f'\n批量解包结束!', s=1)
    print(f'  累计解包 {Cprogs.now()} 个文件')
    print(f'  累计导出 {Cfiles.now()} 个文件')
    print(f'  此项用时 {round(TR.get_consumed_time())} 秒')
    time.sleep(2)
