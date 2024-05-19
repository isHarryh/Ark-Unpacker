# -*- coding: utf-8 -*-
# Copyright (c) 2022-2023, Harry Huang
# @ BSD 3-Clause License
import os.path, time
import UnityPy
from .utils import *
from .CombineRGBwithA import combine_rgb_a
from UnityPy.classes import *


class Resource:
    """The class representing a collection of the objects in an UnityPy Environment."""
    
    @staticmethod
    def _get_image(obj:GameObject):
        """Gets the image inner the object."""
        return obj.image

    @staticmethod
    def _get_script(obj:GameObject):
        """Gets the text script inner the object."""
        return bytes(obj.script)

    @staticmethod
    def _get_samples(obj:GameObject):
        """Gets the audio samples inner the object"""
        return obj.samples.items()

    @staticmethod
    def __rename_add_prefix(obj:GameObject, pre:str):
        """Adds a prefix to rename the Spine-related files."""
        if len(obj.name) <= len(pre) or obj.name[:len(pre)] != pre:
            obj.name = str(pre + obj.name)

    @staticmethod
    def __rename_add_suffix(obj:GameObject, suf:str):
        """Adds a suffix to rename the Spine-related files."""
        if len(obj.name) <= len(suf) or obj.name[:-len(suf)]:
            obj.name = str(obj.name + suf)

    def __init__(self, env:UnityPy.Environment):
        """Initializes with the given UnityPy Environment instance.

        :param env: The Environment instance from `UnityPy.load()`;
        :rtype: None;
        """
        self.env:UnityPy.Environment = env
        """The UnityPy Environment instance"""
        self.name:str = env.file.name
        """The file name of the UnityPy Environment instance"""
        self.length:int = len(env.objects)
        """The count of all objects"""
        ###
        self.sprites:list[Sprite] = []
        self.texture2ds:list[Texture2D] = []
        self.textassets:list[TextAsset] = []
        self.audioclips:list[AudioClip] = []
        self.materials:list[Material] = []
        self.monobehaviors:list[MonoBehaviour] = []
        self.__spines:list[Resource.SpineAsset] = []
        self.typelist = [ #[0:TypeName,1:TypeList,2:FileExt,3:ExtractMethod,4:SaveMethod]
            ['Sprite',self.sprites,'.png',Resource._get_image,MySaver.save_image],
            ['Texture2D',self.texture2ds,'.png',Resource._get_image,MySaver.save_image],
            ['TextAsset',self.textassets,'',Resource._get_script,MySaver.save_script],
            ['AudioClip',self.audioclips,'.wav',Resource._get_samples,MySaver.save_samples],
            ['Material',self.materials,'',None,None],
            ['MonoBehaviour',self.monobehaviors,'',None,None]
        ]
        ###
        objs = [i for i in env.objects]
        for i in objs:
            #(i stands for an object)
            itypename = i.type.name
            for j in self.typelist:
                #(j stands for a type list)
                if itypename == j[0]:
                    j[1].append(i.read())
                    break
    
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

    def save_all_the(self, typename:str, intodir:str, callback:staticmethod=None):
        """Saves every files of the certain type.

        :param typename: Type name;
        :param intodir: Destination directory;
        :param callback: Callback for every saved file;
        :rtype: None;
        """
        for j in self.typelist:
            #(j是某资源类型的特征的列表)
            if typename == j[0]:
                for i in j[1]:
                    #(i是单个object)
                    data = j[3](i) #内容提取
                    j[4](data, intodir, i.name, j[2], callback) #保存
                    Logger.debug(f"ResolveAB: \"{self.name}\" -> \"{i.name}{j[2]}\"")
                break
    
    def save_skeletons(self, intodir:str, callback:staticmethod=None):
        """Saves every Spine asset. Note that sort_skeletons should be invoked first.

        :param intodir: Destination directory;
        :param callback: Callback for every saved file;
        :rtype: None;
        """
        for s in self.__spines:
            s.save_spine(intodir, callback)

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
                        spine = Resource.SpineAsset(self, skel, atlas, list2tex)
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
        self.__spines = spines
    
    def rename_skeletons(self):
        """Renames the Spine assets which includes skel, atlas and png files.
        Since the Spine in Arknights have 4 or more forms (Building, BattleFront, BattleBack, DynIllust),
        it is necessary to rename them so that name collisions can be avoid.
        
        :rtype: None;
        """
        for spine in self.__spines:
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

    class SpineAsset:
        UNKNOWN = 0
        BUILDING = 1
        BATTLE_FRONT = 2
        BATTLE_BACK = 3
        DYN_ILLUST = 4

        def __init__(self, resource, skel:TextAsset, atlas:TextAsset, tex_list:"list[tuple]", type:int=UNKNOWN):
            self.__r:Resource = resource
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
        
        def save_spine(self, intodir:str, callback:staticmethod=None):
            if self.is_available():
                for i in self.tex_list:
                    if i[0]:
                        rgb = Resource._get_image(i[0])
                        if i[1]:
                            rgba = combine_rgb_a(rgb, Resource._get_image(i[1]))
                        else:
                            Logger.info(f"ResolveAB: Spine asset \"{i[0].name}\" has no Alpha texture.")
                            rgba = rgb
                        if MySaver.save_image(rgba, intodir, i[0].name):
                            Logger.debug(f"ResolveAB: Spine asset \"{i[0].name}\" saved.")
                            if callback:
                                callback(True)
                    else:
                        Logger.warn(f"ResolveAB: Spine asset \"{i[0].name}\" texture lost.")
                for i in (self.atlas, self.skel):
                    if MySaver.save_script(Resource._get_script(i), intodir, i.name):
                        Logger.debug(f"ResolveAB: Spine asset \"{i.name}\" saved.")
                        if callback:
                            callback(True)
        #EndClass
    #EndClass


def ab_resolve(abfile:str, intodir:str, \
    doimg:bool, dotxt:bool, doaud:bool, dospine:bool, \
    callback:staticmethod=None, subcallback:staticmethod=None):
    """Extracts an AB file.

    :param abfile: Path to the AB file;
    :param intodir: Destination directory;
    :param doimg: Whether to extract images;
    :param dotxt: Whether to extract text scripts;
    :param doaud: Whether to extract audios;
    :param dospine: Whether to extract Spine assets, note that the Spine assets may have some identical file with the images/scripts;
    :param callback: Callback `f()`, None for ignore;
    :param subcallback: Callback `f(whether_saved_this_file:bool)` for every saved file, `None` for ignore;
    :rtype: None;
    """
    env = UnityPy.load(abfile)
    reso = Resource(env)
    Logger.debug(f'ResolveAB: "{reso.name}" has {reso.length} objects.')
    if reso.length >= 10000:
        Logger.info(f'ResolveAB: Too many objects in file "{reso.name}", unpacking it may take a long time.')
    elif reso.length == 0:
        Logger.info(f'ResolveAB: No object in file "{reso.name}", skipped it.')
        return
    ###
    try:
        # Preprocess
        reso.sort_skeletons()
        reso.rename_skeletons()
        ###
        if dospine:
            reso.save_skeletons(intodir, subcallback)
        if doimg:
            reso.save_all_the('Sprite', intodir, subcallback)
            reso.save_all_the('Texture2D', intodir, subcallback)
        if dotxt:
            reso.save_all_the('TextAsset', intodir, subcallback)
        if doaud:
            reso.save_all_the('AudioClip', intodir, subcallback)
    except BaseException as arg:
        # Error feedback
        Logger.error(f'ResolveAB: Error occurred while unpacking file "{env.file}": Exception{type(arg)} {arg}')
        # raise(arg)
    if callback:
        callback()


########## Main-主程序 ##########
def main(rootdir:str, destdir:str, dodel:bool=False, 
    doimg:bool=True, dotxt:bool=True, doaud:bool=True, dospine:bool=False, separate:bool=True, threads:int=8):
    """Extract all the AB files from the given directory.

    :param rootdir: Source directory;
    :param destdir: Destination directory;
    :param dodel: Whether to delete the existing files in the destination directory, `False` for default;
    :param doimg: Whether to extract images;
    :param dotxt: Whether to extract text scripts;
    :param doaud: Whether to extract audios;
    :param onlyspine: Whether to extract Spine assets, note that the Spine assets may have some identical file with the images/scripts;
    :param separate: Whether to sort the extracted files by their source AB file path.
    :param threads: Max thread count;
    :rtype: None;
    """
    print("\n正在解析目录...", s=1)
    Logger.info("ResolveAB: Reading directories...")
    ospath = os.path
    rootdir = ospath.normpath(ospath.realpath(rootdir))
    destdir = ospath.normpath(ospath.realpath(destdir))
    flist = [] # All-files list
    flist = get_filelist(rootdir)
    flist = list(filter(lambda x:ospath.splitext(x)[1] in ['.ab','.AB'], flist))

    if dodel:
        print("\n正在清理...", s=1)
        rmdir(destdir) # Danger zone
    MySaver.reset()
    MySaver.thread_ctrl.set_max_subthread(threads)
    Cprogs = Counter()
    Cfiles = Counter()
    TC = ThreadCtrl(threads)
    UI = UICtrl(0.5)
    TR = TimeRecorder(len(flist))
    callback = lambda: (Cprogs.update(), TR.update())
    subcallback = lambda x: (Cfiles.update(x))

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
            f'累计解包：\t{Cprogs.get_sum()}',
            f'累计导出：\t{Cfiles.get_sum()}',
            f'剩余时间：\t{f"{round(TR_r / 60, 1)}min" if TR_r > 0 else "计算中"}',
        ])
        ###
        subdestdir = ospath.dirname(i).strip(ospath.sep).replace(rootdir, '').strip(ospath.sep)
        curdestdir = os.path.join(destdir, subdestdir, ospath.splitext(ospath.basename(i))[0]) \
            if separate else os.path.join(destdir, subdestdir)
        TC.run_subthread(ab_resolve, (i, curdestdir, doimg, dotxt, doaud, dospine), \
            {'callback': callback, 'subcallback': subcallback}, name=f"RsThread:{id(i)}")

    RD = Rounder()
    UI.reset()
    UI.loop_stop()
    while TC.count_subthread() or MySaver.thread_ctrl.count_subthread():
        # Waiting for sub threads to terminate
        while TR.get_progress() < 1:
            TR_p = TR.get_progress()
            TR_r = TR.get_remaining_time()
            UI.request([
                f'正在批量解包...',
                f'|{progress_bar(TR_p, 25)}| {color(2, 0, 1)}{round(TR_p*100, 1)}%',
                f'累计解包：\t{Cprogs.get_sum()}',
                f'累计导出：\t{Cfiles.get_sum()}',
                f'剩余时间：\t{f"{round(TR_r / 60, 1)}min" if TR_r > 0 else "计算中"}',
            ])
            UI.refresh(post_delay=0.2)
        UI.request([
            f'正在批量解包...',
            f'|正在等待子进程结束| {color(2, 0, 1)}{RD.next()}',
            f'累计解包：\t{Cprogs.get_sum()}',
            f'累计导出：\t{Cfiles.get_sum()}',
            f'剩余时间：\t--',
        ])
        UI.refresh(post_delay=0.2)

    UI.reset()
    print(f'\n批量解包结束!', s=1)
    print(f'  累计解包 {Cprogs.get_sum()} 个文件')
    print(f'  累计导出 {Cfiles.get_sum()} 个文件')
    print(f'  此项用时 {round(TR.get_consumed_time())} 秒')
    time.sleep(2)
