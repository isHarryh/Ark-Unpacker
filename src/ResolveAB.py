# -*- coding: utf-8 -*-
# Copyright (c) 2022-2023, Harry Huang
# @ BSD 3-Clause License
import os.path, time
try:
    from osTool import *
    from colorTool import *
    from communalTool import *
except:
    from .osTool import *
    from .colorTool import *
    from .communalTool import *
from UnityPy import load as UpyLoad #UnityPy库用于操作Unity文件
from UnityPy import classes as UpyClasses
from UnityPy import Environment
'''
Python批量解包Unity(.ab)资源文件
明日方舟定制版本
'''


class Resource:
    '存放env内的资源的类'
    
    def __get_image(self, obj):
        #### 私有方法：获取object中的图片，返回Image实例
        return obj.image

    def __get_script(self, obj):
        #### 私有方法：获取object中的文本，返回字节流
        return bytes(obj.script)

    def __get_samples(self, obj):
        #### 私有方法：获取object中的音频，返回音频采样点列表
        return obj.samples.items()

    def __rename_add_prefix(self, objlist:list, idx:int, pre:str):
        #### 私有方法：辅助重命名小人相关文件，为资源名称添加前缀
        tmp = objlist[idx].name
        objlist[idx].name = str(pre+tmp)

    def __rename_add_suffix(self, objlist:list, idx:int, suf:str):
        #### 私有方法：辅助重命名小人相关文件，为资源名称添加后缀
        tmp = objlist[idx].name
        objlist[idx].name = str(tmp+suf)

    def __search_in_pathid(self, objlist:list, pathid:int):
        #### 私有方法：按照路径ID搜索特定对象，返回其索引，未找到返回-1
        for i in range(len(objlist)):
            if objlist[i].path_id == pathid:
                return i
        return -1

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
        self.typelist = [ #[0:类型名称,1:类型列表,2:保存后缀,3:内容提取方法,4:安全保存方法]
            ['Sprite',self.sprites,'.png',self.__get_image,MySaver.save_image],
            ['Texture2D',self.texture2ds,'.png',self.__get_image,MySaver.save_image],
            ['TextAsset',self.textassets,'',self.__get_script,MySaver.save_script],
            ['AudioClip',self.audioclips,'.wav',self.__get_samples,MySaver.save_samples],
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

    def save_all_the(self, typename:str, intodir:str, callback=None):
        '''
        #### 保存reource类中所有的某个类型的文件
        :param typename: 类型名称;
        :param intodir:  保存目的地的目录;
        :param detail:   是否回显详细信息;
        :param callback: 每保存一个文件后的回调函数;
        :returns:        (int) 已保存的文件数;
        '''
        cont = 0
        for j in self.typelist:
            #(j是某资源类型的特征的列表)
            if typename == j[0]:
                for i in j[1]:
                    #(i是单个object)
                    data = j[3](i) #内容提取
                    if j[4](data, intodir, i.name, j[2]): #安全保存
                        Logger.debug(f"ResolveAB: \"{self.name}\" -> \"{i.name}{j[2]}\"")
                        cont += 1
                        if callback:
                            callback()
                break
        return cont

    def rename_skeletons(self):
        '''
        #### 重设Spine骨骼动画文件的路径（包括Skel/Atlas/Png）
        明日方舟的骨骼动画分为三种类型，战斗正面、战斗背面、基建。
        为了更好地进行区分，需要将它们的导出文件路径更改为与其类型相对应的特定目录。
        :returns: (none);
        '''
        class SpineAsset:
            UNKNOWN = 0
            BUILDING = 1
            BATTLE_FRONT = 2
            BATTLE_BACK = 3

            def __init__(self, resource:Resource, skel_idx:int, atlas_idx:int, rgb_idx:int, alpha_idx:int, type:int=UNKNOWN):
                self.__resource = resource
                self.skel_idx = skel_idx
                self.atlas_idx = atlas_idx
                self.rgb_idx = rgb_idx
                self.alpha_idx = alpha_idx
                self.type = type
            
            def is_front_geq_back(self):
                text = self.__resource.textassets[self.atlas_idx].text
                return text.count('F_') + text.count('f_') >= text.count('B_') + text.count('b_')
            
            def is_available(self):
                for i in (self.skel_idx, self.atlas_idx, self.rgb_idx, self.alpha_idx):
                    if i < 0:
                        return False
                return True

        spines:list[SpineAsset] = []
        for i in range(len(self.monobehaviors)):
            #(i是单个Mono对象的索引)
            mono = self.monobehaviors[i]
            success = False
            if mono.serialized_type.nodes:
                #对骨骼动画对象操作
                tree = mono.read_typetree()
                if 'skeletonDataAsset' not in tree.keys():
                    continue #不是骨骼动画对象，跳过
                path2skeldata = tree['skeletonDataAsset']['m_PathID']
                idx2skeldata = self.__search_in_pathid(self.monobehaviors, path2skeldata)
                mono_sd = self.monobehaviors[idx2skeldata]
                if mono_sd.serialized_type.nodes:
                    #对骨骼数据对象操作
                    tree_sd = mono_sd.read_typetree()
                    path2skel = tree_sd['skeletonJSON']['m_PathID']
                    path2atlasdata = tree_sd['atlasAssets'][0]['m_PathID']
                    idx2skel = self.__search_in_pathid(self.textassets, path2skel)
                    idx2atlasdata = self.__search_in_pathid(self.monobehaviors, path2atlasdata)
                    mono_ad = self.monobehaviors[idx2atlasdata]
                    if mono_ad.serialized_type.nodes:
                        #对ATLAS数据对象操作
                        tree_ad = mono_ad.read_typetree()
                        path2atlas = tree_ad['atlasFile']['m_PathID']
                        path2mat = tree_ad['materials'][0]['m_PathID']
                        idx2atlas = self.__search_in_pathid(self.textassets, path2atlas)
                        idx2mat = self.__search_in_pathid(self.materials, path2mat)
                        if idx2mat >= 0:
                            mat = self.materials[idx2mat]
                            idx2rgb, idx2alpha = -1, -1
                            if mat.serialized_type.nodes:
                                #对材质对象操作
                                tree_mat = mat.read_typetree()
                                tex_envs = tree_mat['m_SavedProperties']['m_TexEnvs']
                                for tex in tex_envs:
                                    if tex[0] == '_MainTex':
                                        path2rgb = tex[1]['m_Texture']['m_PathID']
                                        idx2rgb = self.__search_in_pathid(self.texture2ds, path2rgb)
                                    elif tex[0] == '_AlphaTex':
                                        path2alpha = tex[1]['m_Texture']['m_PathID']
                                        idx2alpha = self.__search_in_pathid(self.texture2ds, path2alpha)
                                #封装为SpineAsset对象
                                spine = SpineAsset(self, idx2skel, idx2atlas, idx2rgb, idx2alpha)
                                if spine.is_available():
                                    #该骨骼数据解析成功
                                    if 'Relax' in tree['_animationName'] or \
                                        (len(self.textassets[idx2skel].name) > 6 and self.textassets[idx2skel].name[:6] == 'build_'):
                                        spine.type = SpineAsset.BUILDING
                                    else:
                                        spine.type = SpineAsset.BATTLE_FRONT if spine.is_front_geq_back() else SpineAsset.BATTLE_BACK
                                    spines.append(spine)
                                    success = True
            if not success:
                Logger.warn(f'ResolveAB: Failed to handle skeletonDataAsset at pathId {mono.path_id} of {self.name}.')
        
        for spine in spines:
            prefix = ""
            if spine.type == SpineAsset.BUILDING:
                prefix = 'Building' + os.path.sep
            elif spine.type == SpineAsset.BATTLE_FRONT:
                prefix = 'BattleFront' + os.path.sep
            elif spine.type == SpineAsset.BATTLE_BACK:
                prefix = 'BattleBack' + os.path.sep
            self.__rename_add_prefix(self.textassets, spine.skel_idx, prefix)
            self.__rename_add_prefix(self.textassets, spine.atlas_idx, prefix)
            self.__rename_add_prefix(self.texture2ds, spine.rgb_idx, prefix)
            self.__rename_add_prefix(self.texture2ds, spine.alpha_idx, prefix)
    #EndClass


def ab_resolve(env:Environment, intodir:str, doimg:bool, dotxt:bool, doaud:bool, callback=None, subcallback=None):
    '''
    #### 解包ab文件env实例
    :param env:     UnityPy.load()创建的environment实例;
    :param intodir: 解包目的地的目录;
    :param doimg:   是否导出图片资源;
    :param dotxt:   是否导出文本资源;
    :param doaud:   是否导出音频资源;
    :param callback:完成后的回调函数，默认None;
    :param subcallback:每导出一个文件后的回调函数，默认None;
    :returns:       (None);
    '''
    mkdir(intodir)
    reso = Resource(env)
    Logger.debug(f'ResolveAB: "{reso.name}" has {reso.length} objects.')
    if reso.length >= 10000:
        Logger.info(f'ResolveAB: Too many objects in file "{reso.name}", unpacking it may take a long time.')
    elif reso.length == 0:
        Logger.info(f'ResolveAB: No object in file "{reso.name}", skipped it.')
        return
    ###
    try:
        if reso.name[:5] == 'char_':
            #如果这个文件可能是干员模型文件，则进行骨骼动画整理
            reso.rename_skeletons()
        ###
        if doimg:
            reso.save_all_the('Sprite', intodir, subcallback)
            reso.save_all_the('Texture2D', intodir, subcallback)
        if dotxt:
            reso.save_all_the('TextAsset', intodir, subcallback)
        if doaud:
            reso.save_all_the('AudioClip', intodir, subcallback)
    except BaseException as arg:
        #错误反馈
        Logger.error(f'ResolveAB: Error occurred while unpacking file "{env.file}": Eception{type(arg)} {arg}')
        #raise(arg) #调试时使用
    if callback:
        callback()
        

########## Main-主程序 ##########
def main(rootdir:str, destdir:str, dodel:bool=False, 
    doimg:bool=True, dotxt:bool=True, doaud:bool=True, separate:bool=True, threads:int=8):
    '''
    #### 批量地从指定目录的ab文件中，导出指定类型的资源
    :param rootdir: 来源文件夹的根目录的路径;
    :param destdir: 解包目的地的根目录的路径;
    :param dodel:   预先删除目的地文件夹的所有文件，默认False;
    :param doimg:   是否导出图片资源，默认True;
    :param dotxt:   是否导出文本资源，默认True;
    :param doaud:   是否导出音频资源，默认True;
    :param separate:是否按AB文件分类保存，默认True;
    :param threads: 最大线程数，默认8;
    :returns: (None);
    '''
    print(color(7,0,1)+"\n正在解析目录..."+color(7))
    Logger.info("ResolveAB: Reading directories...")
    ospath = os.path
    rootdir = ospath.normpath(ospath.realpath(rootdir)) #标准化目录名
    destdir = ospath.normpath(ospath.realpath(destdir)) #标准化目录名
    flist = [] #目录下所有文件的列表
    flist = get_filelist(rootdir)
    flist = list(filter(lambda x:ospath.splitext(x)[1] in ['.ab','.AB'], flist)) #初筛
    
    cont_p = 0 #进度百分比计数
    if dodel:
        print(color(7,0,1)+"\n正在初始化..."+color(7))
        Delete_File_Dir(destdir) #慎用，会预先删除目的地目录的所有内容
    mkdir(destdir)
    Cprogs = Counter()
    Cfiles = Counter()
    TC = ThreadCtrl(threads if threads >= 1 else 1)
    TR = TimeRecorder(len(flist))

    t1=time.time() #计时器开始

    for i in flist:
        #递归处理各个文件(i是文件的路径名)
        if not ospath.isfile(i):
            continue #跳过目录等非文件路径
        echo = f'''{color(7)}正在批量解包...
|{"■"*int(cont_p//5)}{"□"*int(20-cont_p//5)}| {color(2)}{cont_p}%{color(7)}
当前目录：\t{ospath.basename(ospath.dirname(i))}
当前文件：\t{ospath.basename(i)}
累计解包：\t{Cprogs.get_sum()}
累计导出：\t{Cfiles.get_sum()}
剩余时间：\t{round(TR.getRemainingTime(),1)}min
'''
        os.system('cls')
        print(echo)
        ###
        Ue = UpyLoad(i) #ab文件实例化
        subdestdir = ospath.dirname(i).strip(ospath.sep).replace(rootdir, '').strip(ospath.sep)
        curdestdir = os.path.join(destdir, subdestdir, ospath.splitext(ospath.basename(i))[0]) \
            if separate else os.path.join(destdir, subdestdir)
        TC.run_subthread(ab_resolve,(Ue, curdestdir, doimg, dotxt, doaud), \
            {'callback': Cprogs.update, 'subcallback': Cfiles.update})
        TR.update()
        cont_p = TR.getProgress()

    RD = Rounder()
    while TC.count_subthread():
        #等待子进程结束
        os.system('cls')
        print(
f'''{color(7)}正在批量解包...
|正在等待子进程结束| {color(2)}{RD.next()}{color(7)}
剩余进程：\t{TC.count_subthread()}
累计解包：\t{Cprogs.get_sum()}
累计导出：\t{Cfiles.get_sum()}
剩余时间：\t--
''')
        time.sleep(0.2)

    t2=time.time() #计时器结束
    os.system('cls')
    print(f'{color(7,0,1)}\n批量解包结束!')
    print(f'  累计解包 {Cprogs.get_sum()} 个文件')
    print(f'  累计导出 {Cfiles.get_sum()} 个文件')
    print(f'  此项用时 {round(t2-t1, 1)} 秒{color(7)}')
    time.sleep(2)
