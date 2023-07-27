# -*- coding: utf-8 -*-
# Copyright (c) 2022-2023, Harry Huang
# @ BSD 3-Clause License
import os.path, time
try:
    from .utils._ImportAllUtils import *
except:
    from utils._ImportAllUtils import*
from re import findall
from PIL import Image #PIL库用于操作图像
'''
Python批量合并RGB通道图和A通道图
明日方舟定制版本
'''


def combine_rgb_a(rgb:"str|Image.Image", a:"str|Image.Image"):
    '''
    #### 将RGB通道图和A通道图合并
    此算法更新后速率提升了400%
    :param fp_rgb: RGB通道图的图片对象或其路径;
    :param fp_a:   A通道图的图片对象或其路径;
    :returns:      Image实例;
    '''
    IM1 = (rgb if type(rgb) == Image.Image else Image.open(rgb)).convert('RGBA') #RGB通道图实例化
    IM2 = (a if type(a) == Image.Image else Image.open(a)).convert('L') #A通道图实例化(L:灰度模式)
    if not (IM1.size == IM2.size):
        #两张图片尺寸不同，对A通道图的尺寸进行缩放
        IM2 = IM2.resize(IM1.size, Image.ANTIALIAS)
    IM3 = Image.new('RGBA', IM1.size) #透明抹除全黑图实例化
    IM4 = IM2.point(lambda x:0 if x>0 else 255) #透明抹除反色图实例化
    IM1.putalpha(IM2) #RGB通道图使用A通道图作为alpha层
    IM1.paste(IM3, IM4) #RGB通道图被执行透明抹除
    return IM1

def alpha_resolve(fp:str):
    ''''
    #### 找到哪个RGB通道图的能和这个A通道图匹配
    :param fp: A通道图的文件路径;
    :returns:  (str|bool) RGB通道图的文件路径，失败返回False;
    '''
    ospath = os.path
    fpdir = ospath.dirname(fp)
    fpfile = ospath.basename(fp)
    fpreal = findall(r'.+\[alpha\]', fpfile)
    if len(fpreal) == 0:
        return False #输入不合法，退出
    fpreal = fpreal[0][:-7]
    ###
    flist = os.listdir(os.path.dirname(fp))
    flist = list(filter(lambda x:fpreal in x, flist)) #初筛
    flist = list(filter(lambda x:'.png' in x, flist)) #初筛
    flist = list(filter(lambda x:'[alpha]' not in x, flist)) #初筛
    spines = [] #[filepath,confidence]
    for i in flist:
        #(i是初筛后的文件名)
        iname, iext = ospath.splitext(i)
        if not iext.lower() == '.png':
            continue #不是png图片文件，跳过
        ireal = findall(r'.+_#', iname)
        ireal = iname if len(ireal) == 0 else ireal[0][:-2]
        if ireal == fpreal:
            i = ospath.join(fpdir, i) #i变成初筛后的路径名
            if ospath.isfile(i):
                #找到了一个疑似的图片
                spines.append([i,similarity(i,fp)])
    if len(spines) == 0:
        Logger.warn(f"CombineRGBwithA: No RGB-image could be matched to \"{fp}\"")
        return False #找不到，退出
    elif len(spines) == 1:
        return spines[0][0] #成功，唯一图片的文件路径
    else:
        spines = sorted(spines, key=lambda x:-x[1]) #根据置信度降序排序
        if spines[0][1] < 128:
            Logger.info(f"CombineRGBwithA: Low confidentiality ({spines[0][1]}) about \"{fp}\" and \"{spines[0][0]}\"")
        return spines[0][0] #成功，返回置信度最高的图片的文件路径

def showimg(fp:str):
    IM = Image.open(fp)
    IM.show()

def similarity(fp_rgb:str, fp_a:str, prec:int=150):
    '''
    #### 对比RGB通道图和A通道图的相似度
    :param fp_rgb: RGB通道图的文件路径;
    :param fp_a:   A通道图的文件路径;
    :param prec:   判断精度，值越大越精确，不宜过小过大，默认100;
    :returns:      (int) 介于[0,255]的相似度，值越大越相似;
    '''
    IM1 = Image.open(fp_rgb).convert('L') #RGB通道图实例化(L:灰度模式)
    IM2 = Image.open(fp_a).convert('L') #A通道图实例化
    prec = 100 if prec < 0 else prec
    #对两张图片进行缩放
    IM1 = IM1.resize((prec,prec), Image.BICUBIC)
    IM2 = IM2.resize((prec,prec), Image.BICUBIC)
    #载入原图片的像素到数组
    IM1L = IM1.load()
    IM2L = IM2.load()
    Diff = [] #所有位点的差值的数组
    #对比它们每个像素的相似度
    for y in range(prec):
        for x in range(prec):
            #遍历到每个像素(x,y是像素的坐标)
            Diff.append((((IM1L[x,y] if IM1L[x,y] < 255 else 0) - IM2L[x,y])**2)/256)
    #计算差值的平均值，然后返回相似度
    Diff_mean = round(mean(Diff))
    return 0 if Diff_mean >= 255 else (255 if Diff_mean <= 0 else 255-Diff_mean)

def image_resolve(fp:str, intodir:str, callback:staticmethod=None, successcallback:staticmethod=None):
    '''
    #### 判断某图片的名称是否包含A通道图的特定命名特征，
    #### 如果是的话就寻找它的RGB通道图进行合并，然后保存合并的图片
    :param fp:              图片的文件路径;
    :param intodir:         保存目的地的目录;
    :param callback:        完成后的回调函数（无参数），默认None;
    :param successcallback: 成功导出后的回调函数（接受一个布尔参数“是否进行了保存”），默认None;
    :returns:               (int) 执行状态代码;
    '''
    ospath = os.path
    oridir = ospath.dirname(fp) #原图的目录
    name, ext = ospath.splitext(ospath.basename(fp)) #纯文件名和纯扩展名
    if not ext.lower() == '.png':
        if callback: callback()
        return 1 #不是png图片文件，退出
    ###
    if '[alpha]' in name: #xxx[alpha]xxx.png形式 
        fp2 = alpha_resolve(fp)
        if not fp2:
            if callback: callback()
            return 2 #匹配不到，退出
        real = findall(r'.+\[alpha\]', name)[0][:-7]
    elif name[-6:] == '_alpha': #xxx_alpha.png形式
        fp2 = ospath.join(oridir, name[:-6] + ext)
        real = name[:-6]
    else:
        if callback: callback()
        return 3 #不是指定的A通道图，退出
    ###
    if not ospath.isfile(fp):
        Logger.warn(f"CombineRGBwithA: Alpha-image not found: \"{fp}\"")
        if callback: callback()
        return 4 #找不到对应的A通道图，退出
    if not ospath.isfile(fp2):
        Logger.warn(f"CombineRGBwithA: RGB-image not found: \"{fp}\"")
        if callback: callback()
        return 5 #找不到对应的RGB通道图，退出
    IM = combine_rgb_a(fp2, fp)
    if IM:
        Logger.debug(f"CombineRGBwithA: \"{fp}\" -> \"{fp2}\"")
        MySaver.save_image(IM, intodir, real, '.png', successcallback) #保存新图
        if callback: callback()
    else:
        Logger.warn(f"CombineRGBwithA: Failed to combine \"{fp}\" with \"{fp2}\"")
        if callback: callback()
        return -1 #图片合成函数返回了失败的结果，退出


########## Main-主程序 ##########
def main(rootdir:str, destdir:str, dodel:bool=False, threads:int=8):
    '''
    #### 批量地从指定目录中，找到名称相互匹配的RGB通道图和A通道图，然后合并图片后保存到另一目录
    :param rootdir: 来源文件夹的根目录的路径;
    :param destdir: 解包目的地的根目录的路径;
    :param dodel:   预先删除目的地文件夹的所有文件，默认False;
    :param threads: 最大线程数，默认8;
    :returns: (None);
    '''
    print(f'\n正在解析目录...', s=1)
    Logger.info("CombineRGBwithA: Reading directories...")
    ospath = os.path
    rootdir = ospath.normpath(ospath.realpath(rootdir)) #标准化目录名
    destdir = ospath.normpath(ospath.realpath(destdir)) #标准化目录名
    flist = [] #目录下所有文件的列表
    flist = get_filelist(rootdir)
    flist = list(filter(lambda x:'alpha' in ospath.basename(x), flist)) #初筛
    flist = list(filter(lambda x:ospath.splitext(x)[1].lower() in ['.png', '.jpg', '.jpeg', '.bmp'], flist)) #初筛

    if dodel:
        print("\n正在清理...", s=1)
        rmdir(destdir) #慎用，会预先删除目的地目录的所有内容
    MySaver.reset()
    MySaver.thread_ctrl.set_max_subthread(threads)
    Cprogs = Counter()
    Cfiles = Counter()
    TC = ThreadCtrl(threads)
    UI = UICtrl(0.5)
    TR = TimeRecorder(len(flist))
    callback = lambda: (Cprogs.update(), TR.update())
    successcallback = lambda x: (Cfiles.update(x))

    UI.reset()
    UI.loop_start()
    for i in flist:
        #递归处理各个文件(i是文件的路径名)
        if not ospath.isfile(i):
            continue #跳过目录等非文件路径
        TR_p = TR.get_progress()
        TR_r = TR.get_remaining_time()
        UI.request([
            f'正在批量合并图片...',
            f'|{progress_bar(TR_p, 25)}| {color(2, 0, 1)}{round(TR_p*100, 1)}%',
            f'当前目录：\t{ospath.basename(ospath.dirname(i))}',
            f'当前文件：\t{ospath.basename(i)}',
            f'累计处理：\t{Cprogs.get_sum()}',
            f'累计导出：\t{Cfiles.get_sum()}',
            f'剩余时间：\t{f"{round(TR_r / 60, 1)}min" if TR_r > 0 else "计算中"}',
        ])
        ###
        subdestdir = ospath.dirname(i).strip(ospath.sep).replace(rootdir, '').strip(ospath.sep)
        TC.run_subthread(image_resolve,(i, ospath.join(destdir, subdestdir)), \
            {'callback': callback, 'successcallback': successcallback}, name=f"CBThread:{id(i)}")

    RD = Rounder()
    UI.reset()
    UI.loop_stop()
    while TC.count_subthread() or MySaver.thread_ctrl.count_subthread():
        #等待子进程结束
        while TR.get_progress() < 1:
            TR_p = TR.get_progress()
            TR_r = TR.get_remaining_time()
            UI.request([
                f'正在批量合并图片...',
                f'|{progress_bar(TR_p, 25)}| {color(2, 0, 1)}{round(TR_p*100, 1)}%',
                f'累计处理：\t{Cprogs.get_sum()}',
                f'累计导出：\t{Cfiles.get_sum()}',
                f'剩余时间：\t{f"{round(TR_r / 60, 1)}min" if TR_r > 0 else "计算中"}',
            ])
            UI.refresh(post_delay=0.2)
        UI.request([
            '正在批量合并图片...',
            f'|正在等待子进程结束| {color(2, 0, 1)}{RD.next()}',
            f'累计处理：\t{Cprogs.get_sum()}',
            f'累计导出：\t{Cfiles.get_sum()}',
            f'剩余时间：\t--',
        ])
        UI.refresh(post_delay=0.2)

    UI.reset()
    print(f'\n批量合并图片结束!', s=1)
    print(f'  累计导出 {Cfiles.get_sum()} 张照片')
    print(f'  此项用时 {round(TR.get_consumed_time())} 秒')
    time.sleep(2)
