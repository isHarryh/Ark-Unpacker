# -*- coding: utf-8 -*-
# Copyright (c) 2022-2023, Harry Huang
# @ BSD 3-Clause License
import os.path, time
try:
    from .utils._ImportAllUtils import *
    from .CombineRGBwithA import combine_rgb_a
except:
    from utils._ImportAllUtils import*
    from CombineRGBwithA import combine_rgb_a
from UnityPy import load as UpyLoad #UnityPy库用于操作Unity文件
from UnityPy import classes as UpyClasses
from UnityPy import Environment
'''
Python批量解包Unity(.ab)资源文件
明日方舟定制版本
'''


class Resource:
    '存放env内的资源的类'
    
    @staticmethod
    def _get_image(obj):
        #### 类内静态方法：获取object中的图片，返回Image实例
        return obj.image

    @staticmethod
    def _get_script(obj):
        #### 类内静态方法：获取object中的文本，返回字节流
        return bytes(obj.script)

    @staticmethod
    def _get_samples(obj):
        #### 类内静态方法：获取object中的音频，返回音频采样点列表
        return obj.samples.items()

    @staticmethod
    def __rename_add_prefix(obj:UpyClasses.GameObject, pre:str):
        #### 私有静态方法：辅助重命名小人相关文件，为资源名称添加前缀
        if len(obj.name) <= len(pre) or obj.name[:len(pre)] != pre:
            obj.name = str(pre + obj.name)

    @staticmethod
    def __rename_add_suffix(obj:UpyClasses.GameObject, suf:str):
        #### 私有静态方法：辅助重命名小人相关文件，为资源名称添加后缀
        if len(obj.name) <= len(suf) or obj.name[:-len(suf)]:
            obj.name = str(obj.name + suf)

    def __init__(self, env:Environment):
        '''
        #### 通过传入一个UnityPy.environment实例，初始化一个resource类
        :param env: UnityPy.load()创建的environment实例;
        :returns:   (none);
        '''
        self.env:Environment = env
        '''The UnityPy Environment instance'''
        self.name:str = env.file.name
        '''The file name of the UnityPy Environment instance'''
        self.length:int = len(env.objects)
        '''The count of all objects'''
        ###
        self.sprites:list[UpyClasses.Sprite] = []
        self.texture2ds:list[UpyClasses.Texture2D] = []
        self.textassets:list[UpyClasses.TextAsset] = []
        self.audioclips:list[UpyClasses.AudioClip] = []
        self.materials:list[UpyClasses.Material] = []
        self.monobehaviors:list[UpyClasses.MonoBehaviour] = []
        self.__spines:list[Resource.SpineAsset] = []
        self.typelist = [ #[0:类型名称,1:类型列表,2:保存后缀,3:内容提取方法,4:安全保存方法]
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
            #(i是单个object)
            itypename = i.type.name
            for j in self.typelist:
                #(j是某资源类型的特征的列表)
                if itypename == j[0]:
                    j[1].append(i.read())
                    break
    
    def get_object_by_pathid(self, pathid:"int|dict", search_in:"list|None"=None):
        '''
        #### 获取具有指定PathID的GameObject对象
        :param pathid:     PathID，可以是具体的值，也可以是包含m_PathID字段的字典;
        :param search_in:  搜索范围，如果是None则表示搜索范围是全部对象;
        :returns:          (GameObject) 若未找到则返回None;
        '''
        _key = 'm_PathID'
        pathid:int = pathid[_key] if type(pathid) == dict and _key in pathid.keys() else pathid
        lst:list[UpyClasses.GameObject] = self.env.objects if not search_in else search_in
        for i in lst:
            if i.path_id == pathid:
                return i
        return None

    def save_all_the(self, typename:str, intodir:str, callback:staticmethod=None):
        '''
        #### 保存Reource类中某个类型的所有文件
        :param typename: 类型名称;
        :param intodir:  保存目的地的目录;
        :param callback: 每保存一个文件后的回调函数;
        :returns:        (none);
        '''
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
        '''
        #### 保存所有找到的Spine动画，请确保已先执行sort_skeletons
        :param intodir:  保存目的地的目录;
        :param callback: 每保存一个文件后的回调函数;
        :returns:        (none);
        '''
        for s in self.__spines:
            s.save_spine(intodir, callback)

    def sort_skeletons(self):
        '''
        #### 整理Spine骨骼动画
        :returns: (none);
        '''
        spines:list[Resource.SpineAsset] = []
        for mono in self.monobehaviors:
            #(i是遍历的单个Mono对象)
            success = False
            if mono.serialized_type.nodes:
                #对骨骼动画对象操作
                tree = mono.read_typetree()
                if 'skeletonDataAsset' not in tree.keys():
                    continue #不是骨骼动画对象，跳过
                mono_sd = self.get_object_by_pathid(tree['skeletonDataAsset'], self.monobehaviors)
                if mono_sd.serialized_type.nodes:
                    #对骨骼数据对象操作
                    tree_sd = mono_sd.read_typetree()
                    skel = self.get_object_by_pathid(tree_sd['skeletonJSON'], self.textassets)
                    mono_ad = self.get_object_by_pathid(tree_sd['atlasAssets'][0], self.monobehaviors)
                    if mono_ad.serialized_type.nodes:
                        #对ATLAS数据对象操作
                        tree_ad = mono_ad.read_typetree()
                        atlas = self.get_object_by_pathid(tree_ad['atlasFile'], self.textassets)
                        list2mat = [self.get_object_by_pathid(i, self.materials) for i in tree_ad['materials']]
                        list2tex = []
                        for mat in list2mat:
                            tex_rgb, tex_alpha = None, None
                            if mat.serialized_type.nodes:
                                #对材质对象操作
                                tree_mat = mat.read_typetree()
                                tex_envs = tree_mat['m_SavedProperties']['m_TexEnvs']
                                for tex in tex_envs:
                                    if tex[0] == '_MainTex':
                                        tex_rgb = self.get_object_by_pathid(tex[1]['m_Texture'], self.texture2ds)
                                    elif tex[0] == '_AlphaTex':
                                        tex_alpha = self.get_object_by_pathid(tex[1]['m_Texture'], self.texture2ds)
                            list2tex.append((tex_rgb, tex_alpha))
                        #封装为SpineAsset对象
                        spine = Resource.SpineAsset(self, skel, atlas, list2tex)
                        if spine.is_available():
                            #该骨骼数据解析成功
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
        '''
        #### 重设Spine骨骼动画文件的路径（包括Skel/Atlas/Png）
        明日方舟的骨骼动画分为三种类型，战斗正面、战斗背面、基建。
        为了更好地进行区分，需要将它们的导出文件路径更改为与其类型相对应的特定目录。
        :returns: (none);
        '''
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

        def __init__(self, resource, skel:UpyClasses.TextAsset, atlas:UpyClasses.TextAsset, tex_list:"list[tuple]", type:int=UNKNOWN):
            self.__r:Resource = resource
            self.skel = skel
            self.atlas = atlas
            self.tex_list = tex_list
            self.type = type
        
        def is_front_geq_back(self):
            t = self.atlas.text
            return t.count('\nF_') + t.count('\nf_') + t.count('\nC_') + t.count('\nc_') >= t.count('\nB_') + t.count('\nb_')
        
        def is_available(self):
            if type(self.skel) != UpyClasses.TextAsset or type(self.atlas) != UpyClasses.TextAsset:
                return False
            if type(self.tex_list) != list or len(self.tex_list) == 0:
                return False
            return True
        
        def get_common_name(self):
            if type(self.atlas) == UpyClasses.TextAsset:
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
                                callback()
                    else:
                        Logger.warn(f"ResolveAB: Spine asset \"{i[0].name}\" texture lost.")
                for i in (self.atlas, self.skel):
                    if MySaver.save_script(Resource._get_script(i), intodir, i.name):
                        Logger.debug(f"ResolveAB: Spine asset \"{i.name}\" saved.")
                        if callback:
                            callback()
        #EndClass
    #EndClass


def ab_resolve(abfile:str, intodir:str, doimg:bool, dotxt:bool, doaud:bool, dospine:bool, callback=None, subcallback=None):
    '''
    #### 解包ab文件env实例
    :param abfile:      ab文件的路径;
    :param intodir:     解包目的地的目录;
    :param doimg:       是否导出图片资源;
    :param dotxt:       是否导出文本资源;
    :param doaud:       是否导出音频资源;
    :param dospine:     是否导出Spine动画，注意Spine动画和图片资源、文本资源有重叠的部分;
    :param callback:    完成后的回调函数，默认None;
    :param subcallback: 每导出一个文件后的回调函数，默认None;
    :returns:       (None);
    '''
    env = UpyLoad(abfile)
    reso = Resource(env)
    Logger.debug(f'ResolveAB: "{reso.name}" has {reso.length} objects.')
    if reso.length >= 10000:
        Logger.info(f'ResolveAB: Too many objects in file "{reso.name}", unpacking it may take a long time.')
    elif reso.length == 0:
        Logger.info(f'ResolveAB: No object in file "{reso.name}", skipped it.')
        return
    ###
    try:
        #进行骨骼动画整理和重命名
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
        #错误反馈
        Logger.error(f'ResolveAB: Error occurred while unpacking file "{env.file}": Exception{type(arg)} {arg}')
        #raise(arg) #调试时使用
    if callback:
        callback()


########## Main-主程序 ##########
def main(rootdir:str, destdir:str, dodel:bool=False, 
    doimg:bool=True, dotxt:bool=True, doaud:bool=True, dospine:bool=False, separate:bool=True, threads:int=8):
    '''
    #### 批量地从指定目录的ab文件中，导出指定类型的资源
    :param rootdir:   来源文件夹的根目录的路径;
    :param destdir:   解包目的地的根目录的路径;
    :param dodel:     预先删除目的地文件夹的所有文件，默认False;
    :param doimg:     是否导出图片资源，默认True;
    :param dotxt:     是否导出文本资源，默认True;
    :param doaud:     是否导出音频资源，默认True;
    :param onlyspine: 是否导出Spine动画，注意Spine动画和图片资源、文本资源有重叠的部分，默认False;
    :param separate:  是否按AB文件分类保存，默认True;
    :param threads:   最大线程数，默认8;
    :returns: (None);
    '''
    print("\n正在解析目录...", s=1)
    Logger.info("ResolveAB: Reading directories...")
    ospath = os.path
    rootdir = ospath.normpath(ospath.realpath(rootdir)) #标准化目录名
    destdir = ospath.normpath(ospath.realpath(destdir)) #标准化目录名
    flist = [] #目录下所有文件的列表
    flist = get_filelist(rootdir)
    flist = list(filter(lambda x:ospath.splitext(x)[1] in ['.ab','.AB'], flist)) #初筛
    
    cont_p = 0 #进度百分比计数
    if dodel:
        print("\n正在清理...", s=1)
        rmdir(destdir) #慎用，会预先删除目的地目录的所有内容
    mkdir(destdir)
    Cprogs = Counter()
    Cfiles = Counter()
    MySaver.reset()
    MySaver.thread_ctrl.set_max_subthread(threads)
    TC = ThreadCtrl(threads)
    TR = TimeRecorder(len(flist))

    os.system('cls')
    for i in flist:
        #递归处理各个文件(i是文件的路径名)
        if not ospath.isfile(i):
            continue #跳过目录等非文件路径
        print(f'正在批量解包...', y=1)
        print(f'|{progress_bar(cont_p, 25)}| {color(2, 0, 1)}{round(cont_p*100, 1)}%', y=2)
        print(f'当前目录：\t{ospath.basename(ospath.dirname(i))}', y=3)
        print(f'当前文件：\t{ospath.basename(i)}', y=4)
        print(f'累计解包：\t{Cprogs.get_sum()}', y=5)
        print(f'累计导出：\t{Cfiles.get_sum()}', y=6)
        print(f'剩余时间：\t{round(TR.get_remaining_time()/60,1)}min', y=7)
        ###
        subdestdir = ospath.dirname(i).strip(ospath.sep).replace(rootdir, '').strip(ospath.sep)
        curdestdir = os.path.join(destdir, subdestdir, ospath.splitext(ospath.basename(i))[0]) \
            if separate else os.path.join(destdir, subdestdir)
        TC.run_subthread(ab_resolve, (i, curdestdir, doimg, dotxt, doaud, dospine), \
            {'callback': Cprogs.update, 'subcallback': Cfiles.update}, name=f"RsThread:{id(i)}")
        TR.update()
        cont_p = TR.get_progress()

    RD = Rounder()
    os.system('cls')
    while TC.count_subthread() or MySaver.thread_ctrl.count_subthread():
        #等待子进程结束
        print('正在批量解包...', y=1)
        print(f'|正在等待子进程结束| {color(2)}{RD.next()}', y=2)
        print(f'累计解包：\t{Cprogs.get_sum()}', y=3)
        print(f'累计导出：\t{Cfiles.get_sum()}', y=4)
        print(f'剩余时间：\t--', y=5)
        time.sleep(0.2)

    os.system('cls')
    print(f'\n批量解包结束!', s=1)
    print(f'  累计解包 {Cprogs.get_sum()} 个文件')
    print(f'  累计导出 {Cfiles.get_sum()} 个文件')
    print(f'  此项用时 {round(TR.get_consumed_time())} 秒')
    time.sleep(2)
