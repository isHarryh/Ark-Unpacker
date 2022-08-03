# -*- coding: utf-8 -*-
# Copyright (c) 2022, Harry Huang
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
from io import BytesIO
from UnityPy import load as UpyLoad #UnityPy库用于操作Unity文件，这里仅导入个load函数
'''
Python批量解包Unity(.ab)资源文件
明日方舟定制版本
'''


class resource:
    '存放env内的资源的类'
    
    @classmethod
    def __get_image(self, obj):
        #### 私有方法：获取object中的图片，返回Image实例
        return obj.image

    @classmethod
    def __get_script(self, obj):
        #### 私有方法：获取object中的文本，返回字节流
        return bytes(obj.script)

    @classmethod
    def __get_samples(self, obj):
        #### 私有方法：获取object中的音频，返回音频采样点列表
        return obj.samples.items

    @classmethod
    def __rename_add_prefix(self, objlist:list, idx:int, pre:str):
        #### 私有方法：辅助重命名小人相关文件，前缀
        tmp = objlist[idx].name
        objlist[idx].name = str(pre+tmp)

    @classmethod
    def __rename_add_suffix(self, objlist:list, idx:int, suf:str):
        #### 私有方法：辅助重命名小人相关文件，后缀
        tmp = objlist[idx].name
        objlist[idx].name = str(tmp+suf)

    @classmethod
    def __search_in_pathid(self, objlist:list, pathid:int):
        #### 私有方法：按照路径ID搜索特定对象，返回其索引
        for i in range(len(objlist)):
            if objlist[i].path_id == pathid:
                return i
        return False

    @classmethod
    def __init__(self, env):
        '''
        #### 通过传入一个UnityPy.environment实例，初始化一个resource类
        :param env: UnityPy.load()创建的environment实例;
        :returns:   (none);
        '''
        self.sprites = []
        self.texture2ds = []
        self.textassets = []
        self.audioclips = []
        self.monobehaviors = []
        self.typelist = [ #[0:类型名称,1:类型列表,2:保存后缀,3:内容提取方法,4:安全保存方法]
            ['Sprite',self.sprites,'.png',self.__get_image,MySaver.save_image],
            ['Texture2D',self.texture2ds,'.png',self.__get_image,MySaver.save_image],
            ['TextAsset',self.textassets,'',self.__get_script,MySaver.save_script],
            ['AudioClip',self.audioclips,'.wav',self.__get_samples,MySaver.save_samples],
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

    @classmethod
    def save_all_the(self, typename:str, intodir:str, detail:bool=False):
        '''
        #### 保存reource类中所有的某个类型的文件
        :param typename: 类型名称;
        :param intodir:  保存目的地的目录;
        :param detail:   是否回显详细信息;
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
                        cont += 1
                break
        if detail and cont:
            print(f'{color(6)}  成功导出 {cont}\t{typename}')
        return cont

    @classmethod
    def rename_spine_images(self):
        '''
        #### 重命名小人图片文件
        明日方舟的战斗界面的小人有正面和背面之分，但是其文件名都一样，此函数将会尝试对其作出区分
        当前尚未找到准确区分图片文件的方法QwQ
        :returns: (int);
        '''
        ##基建小人（无需处理）
        '''
        build = []
        for i in range(len(self.texture2ds)):
            #(i是单个Texture2D对象的索引)
            iname = self.texture2ds[i].name
            if len(iname) > 11 and 'build_char_' == iname[:11]:
                build.append(i)
        for i in range(len(build)):
            pass
        '''
        ##战斗小人
        spines = []
        for i in range(len(self.texture2ds)):
            #(i是单个Texture2D对象的索引)
            iname = self.texture2ds[i].name
            if len(iname) > 5 and 'char_' == iname[:5] and iname.count('_') == 2:
                spines.append(i)
        spines = sorted(spines, key=lambda x:self.texture2ds[x].path_id)
        for i in range(len(spines)):
            self.__rename_add_suffix(self.texture2ds,spines[i],'_#'+str(i))
        return len(spines)

    @classmethod
    def rename_spine_texts(self):
        '''
        #### 重命名小人文本文件（包括.skel和.atlas）
        明日方舟的战斗界面的小人有正面和背面之分，但是其文件名都一样，此函数将会尝试对其作出区分
        文本文件倒是被我找到了有准确区分的方法:D
        :returns: (int);
        '''
        ##基建小人
        build = []
        for i in range(len(self.textassets)):
            #(i是单个TextAsset对象的索引)
            iname = self.textassets[i].name
            if 'build_char_' == iname[:10]:
                build.append(i)
        for i in range(len(build)):
            self.__rename_add_prefix(self.textassets,build[i],'Building\\')
        ##战斗小人
        ##在MonoBehaviour中筛选出SkelData并读取
        datas = [] #[Idx:SkelData,Idx:Skel,Idx:AtlasData,Idx:Atlas,Front/Back]
        for i in range(len(self.monobehaviors)):
            #(i是单个Mono对象的索引)
            iname = self.monobehaviors[i].name
            if len(iname) > 18 and '_char_' not in iname and iname[-13:] == '_SkeletonData':
                j = self.monobehaviors[i] #SkelData对象
                if j.serialized_type.nodes:
                    #假如可读树状内容
                    tree = j.read_typetree() #Mono的树状内容
                    i_skel = self.__search_in_pathid(self.textassets,
                        tree['skeletonJSON']['m_PathID'])
                    i_atlasdata = self.__search_in_pathid(self.monobehaviors,
                        tree['atlasAssets'][0]['m_PathID'])
                    #至此已找到SkelData,Skel,AtlasData的索引
                    data = [i,i_skel,i_atlasdata,None,None]
                    datas.append(data)
        if len(datas) == 0:
            return 0
        ##读取AtlasData
        for k in range(len(datas)):
            #(k是单个Data的索引)
            data = datas[k] #Data的副本
            j = self.monobehaviors[data[2]] #AtlasData对象
            if j.serialized_type.nodes:
                    #假如可读树状内容
                    tree = j.read_typetree() #Mono的树状内容
                    i_atlas = self.__search_in_pathid(self.textassets,
                        tree['atlasFile']['m_PathID'])
                    ##读取Atlas并判断Front/Back
                    atlas = self.textassets[i_atlas].text #Atlas的文本内容
                    ct_f = atlas.count('F_') + atlas.count('f_')
                    ct_b = atlas.count('B_') + atlas.count('b_')
                    #至此又找到了Atlas的索引和Front/Back
                    data[3] = i_atlas
                    data[4] = 'Front' if ct_f >= ct_b else 'Back'
                    datas[k] = data
                    ##重命名Skel
                    self.__rename_add_prefix(self.textassets,datas[k][1],'Battle'+datas[k][4]+'\\')
                    ##重命名Atlas
                    self.__rename_add_prefix(self.textassets,datas[k][3],'Battle'+datas[k][4]+'\\')
        return len(datas)
    #EndClass


def ab_resolve(env, intodir:str, doimg:bool, dotxt:bool, doaud:bool, detail:bool):
    '''
    #### 解包ab文件env实例
    更新内容：解决了战斗小人正背面导出紊乱的问题
    :param env:     UnityPy.load()创建的environment实例;
    :param intodir: 解包目的地的目录;
    :param doimg:   是否导出图片资源;
    :param dotxt:   是否导出文本资源;
    :param doaud:   是否导出音频资源;
    :param detail:  是否回显详细信息;
    :returns:       (int) 已导出的文件数;
    '''
    mkdir(intodir)
    cont_obj = len(env.objects)
    if detail:
        print(f'{color(2)}  找到了 {cont_obj} 个资源，正在处理...')
    if cont_obj >= 1000:
        print(f'{color(6)}  提示：此文件包含资源较多，用时可能较长')
    elif cont_obj <= 0:
        return 0
    cont_s = 0 #已导出资源计数
    ###
    reso = resource(env)
    try:
        succ = reso.rename_spine_images()
        if detail:
            print(f'{color(2)}  BattileSpineImgs: {succ}')
        succ = reso.rename_spine_texts()
        if detail:
            print(f'{color(2)}  BattelSkel&Atlas: {succ}')
        ###
        if doimg:
            cont_s += reso.save_all_the('Sprite', intodir, detail)
            cont_s += reso.save_all_the('Texture2D', intodir, detail)
        if dotxt:
            cont_s += reso.save_all_the('TextAsset', intodir, detail)
        if doaud:
            cont_s += reso.save_all_the('AudioClip', intodir, detail)
    except BaseException as arg:
        #错误反馈
        print(f'{color(1)}  意外错误：{arg}')
        input(f'  按下回车键以跳过此文件并继续任务...')
    ###
    if detail:
        print(f'{color(2)}  导出了 {cont_s} 个文件{color(7)}')
    return cont_s
        

########## Main-主程序 ##########
def main(rootdir:list, destdir:str, dodel:bool=False, 
    doimg:bool=True, dotxt:bool=True, doaud:bool=True, detail:bool=True):
    '''
    #### 批量地从指定目录的ab文件中，导出指定类型的资源
    :param rootdir: 包含来源文件夹们的路径的列表;
    :param destdir: 解包目的地的根目录的路径;
    :param dodel:   预先删除目的地文件夹的所有文件，默认False;
    :param doimg:   是否导出图片资源，默认True;
    :param dotxt:   是否导出文本资源，默认True;
    :param doaud:   是否导出音频资源，默认True;
    :param detail:  是否回显详细信息，默认True，否则回显进度条;
    :returns: (None);
    '''
    print(color(7,0,1)+"\n正在解析目录..."+color(7))
    ospath = os.path
    flist = [] #目录下所有文件的列表
    for i in rootdir:
        flist += get_filelist(i)
    flist = list(filter(lambda x:ospath.splitext(x)[1] in ['.ab','.AB'], flist)) #初筛
    
    cont_f = 0 #已处理文件计数
    cont_a = 0 #已遍历文件计数
    cont_p = 0 #进度百分比计数
    cont_s_sum = 0 #已导出文件计数（累加）
    if dodel:
        Delete_File_Dir(destdir) #慎用，会预先删除目的地目录的所有内容
    mkdir(destdir)

    if detail:
        print(f'{color(7,0,1)}开始批量解包!\n{color(7)}')
    t1=time.time() #计时器开始

    for i in flist:
        #递归处理各个文件(i是文件的路径名)
        cont_a += 1
        cont_p = round((cont_a/len(flist))*100,1)
        if not ospath.isfile(i):
            continue #跳过目录等非文件路径
        cont_f += 1
        ###
        if detail:
            #显示模式A：流式
            print(f'{color(7)}{os.path.dirname(i)}')
            print(f'[{ospath.basename(i)}]')
        else:
            #显示模式B：简洁
            os.system('cls')
            print(f'{color(7)}正在批量解包...')
            print(f'|{"■"*int(cont_p//5)}{"□"*int(20-cont_p//5)}| {color(2)}{cont_p}%{color(7)}')
            print(f'当前目录：\t{ospath.dirname(i)}')
            print(f'当前文件：\t{ospath.basename(i)}')
            print(f'累计解包：\t{cont_f-1}')
            print(f'累计导出：\t{cont_s_sum}\n')
        ###
        Ue = UpyLoad(i) #ab文件实例化
        cont_s_sum += ab_resolve(Ue, os.path.join(destdir, os.path.dirname(i)), doimg, dotxt, doaud, detail)
        ###
        if detail and cont_f % 25 == 0:
            print(f'{color(7,0,1)}■ 已累计解包{cont_f}个文件 ({cont_p}%)')
            print(f'■ 已累计导出{cont_s_sum}个文件')

    t2=time.time() #计时器结束
    if not detail:
        os.system('cls')
    print(f'{color(7,0,1)}\n批量解包结束!')
    print(f'  累计解包 {cont_f} 个文件')
    print(f'  累计导出 {cont_s_sum} 个文件')
    print(f'  此项用时 {round(t2-t1, 1)} 秒{color(7)}')
    time.sleep(2)

'''
#测试相关：
Ue = UpyLoad('')
ab_resolve(Ue, 'temp', True, True, False, True, True)
'''