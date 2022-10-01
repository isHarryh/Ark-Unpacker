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
from re import findall
from PIL import Image #PIL库用于操作图像
'''
Python批量合并RGB通道图和A通道图
明日方舟定制版本
'''


def combine_rgb_a(fp_rgb:str, fp_a:str):
    '''
    #### 将RGB通道图和A通道图合并
    此算法更新后速率提升了400%
    :param fp_rgb: RGB通道图的文件路径;
    :param fp_a:   A通道图的文件路径;
    :returns:      Image实例;
    '''
    IM1 = Image.open(fp_rgb).convert('RGBA') #RGB通道图实例化
    IM2 = Image.open(fp_a).convert('L') #A通道图实例化(L:灰度模式)
    if not (IM1.size == IM2.size):
        #两张图片尺寸不同，对A通道图的尺寸进行缩放
        IM2 = IM2.resize(IM1.size, Image.ANTIALIAS)
        #print(f'{color(3)}  警告：通道图尺寸不一，已缩放处理')    
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
        return False #找不到，退出
    elif len(spines) == 1:
        return spines[0][0] #成功，唯一图片的文件路径
    else:
        spines = sorted(spines, key=lambda x:-x[1]) #根据置信度降序排序
        #print(f'{color(6)}  匹配到 {ospath.basename(spines[0][0])}\n  置信度 {spines[0][1]}')
        if spines[0][1] < 128:
            pass
            #print(f'{color(3)}  警告：置信度较低，可能匹配错误')
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

def image_resolve(fp:str, intodir:str, callback=None, successcallback=None):
    '''
    #### 判断某图片的名称是否包含A通道图的特定命名特征，
    #### 如果是的话就寻找它的RGB通道图进行合并，然后保存合并的图片
    :param fp:      图片的文件路径;
    :param intodir: 保存目的地的目录;
    :param callback:完成后的回调函数，默认None;
    :param successcallback:成功导出后的回调函数，默认None;
    :returns:       (int) 执行状态代码;
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
        print(f'{color(1)}  错误：alpha通道图缺失{color(7)} {fp}')
        if callback: callback()
        return 4 #找不到对应的A通道图，退出
    if not ospath.isfile(fp2):
        print(f'{color(1)}  错误：RGB通道图缺失{color(7)} {fp2}')
        if callback: callback()
        return 5 #找不到对应的RGB通道图，退出
    #print(color(7)+fp2)
    IM = combine_rgb_a(fp2, fp)
    if IM:
        if MySaver.save_image(IM, intodir, real, '.png'): #保存新图
            if callback: callback()
            if successcallback: successcallback()
            return 0 #成功，返回0
        else:
            if callback: callback()
            return 6 #未保存，返回6
    else:
        print(f'{color(1)}  错误：通道图合成失败{color(7)}')
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
    print(f'{color(7,0,1)}\n正在解析目录...{color(7)}')
    ospath = os.path
    rootdir = ospath.normpath(ospath.realpath(rootdir)) #标准化目录名
    destdir = ospath.normpath(ospath.realpath(destdir)) #标准化目录名
    flist = [] #目录下所有文件的列表
    flist = get_filelist(rootdir)
    flist = list(filter(lambda x:'alpha' in ospath.basename(x), flist)) #初筛
    flist = list(filter(lambda x:ospath.splitext(x)[1].lower() in ['.png', '.jpg', '.jpeg', '.bmp'], flist)) #初筛
    
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
        os.system('cls')
        print(
f'''{color(7)}正在批量解包...
|{"■"*int(cont_p//5)}{"□"*int(20-cont_p//5)}| {color(2)}{cont_p}%{color(7)}
当前目录：\t{ospath.basename(ospath.dirname(i))}
当前文件：\t{ospath.basename(i)}
累计处理：\t{Cprogs.get_sum()}
累计导出：\t{Cfiles.get_sum()}
剩余时间：\t{round(TR.getRemainingTime(),1)}min
''')
        ###
        subdestdir = ospath.dirname(i).strip(ospath.sep).replace(rootdir, '').strip(ospath.sep)
        TC.run_subthread(image_resolve,(i, ospath.join(destdir, subdestdir)), \
            {'callback': Cprogs.update, 'successcallback': Cfiles.update})
        TR.update()
        cont_p = TR.getProgress()

    RD = rounder()
    while TC.count_subthread():
        #等待子进程结束
        os.system('cls')
        print(
f'''{color(7)}正在批量解包...
|正在等待子进程结束| {color(2)}{RD.next()}{color(7)}
剩余进程：\t{TC.count_subthread()}
累计处理：\t{Cprogs.get_sum()}
累计导出：\t{Cfiles.get_sum()}
剩余时间：\t--
''')
        time.sleep(0.2)

    t2=time.time() #计时器结束
    os.system('cls')
    print(f'{color(7,0,1)}\n批量合并图片结束!')
    print(f'  累计导出 {Cfiles.get_sum()} 张照片')
    print(f'  此项用时 {round(t2-t1, 1)} 秒{color(7)}')
    time.sleep(2)
