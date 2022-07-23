# -*- coding: utf-8 -*-
# Copyright (c) 2022, Harry Huang
# @ BSD 3-Clause License
import os.path, time
try:
    from osTool import *
    from colorTool import *
except:
    from .osTool import *
    from .colorTool import *
from re import findall
from PIL import Image #PIL库用于操作图像
'''
Python批量合并RGB通道图和A通道图
'''


def combine_rgb_a(fp_rgb:str, fp_a:str):
    '''
    #### 将RGB通道图和A通道图合并
    :param fp_rgb: RGB通道图的文件路径;
    :param fp_a:   A通道图的文件路径;
    :returns:      Image实例;
    '''
    IM1 = Image.open(fp_rgb).convert('RGB') #RGB通道图实例化
    IM2 = Image.open(fp_a).convert('L') #A通道图实例化(L:灰度模式)
    w,h = IM1.size #新图片尺寸取自RGB通道图
    if not (IM1.size == IM2.size):
        #两张图片尺寸不同，对A通道图的尺寸进行缩放
        print(f'{color(3)}  警告：通道图尺寸不一，已缩放处理')
        IM2 = IM2.resize((w,h), Image.ANTIALIAS)
    #载入原图片的像素到数组
    IM1L = IM1.load()
    IM2L = IM2.load()
    #输出到新图片
    IM3  = Image.new('RGBA', (w,h), (0,0,0,0))
    IM3L = IM3.load()
    for x in range(0, w):
        for y in range(0, h):
            #遍历到每个像素(x,y是像素的坐标)
            a = IM2L[x, y] #该像素的A值
            r,g,b = IM1L[x, y] if a > 0 else (0,0,0) #当A值为全透明(0)时抹除掉该像素RGB值
            IM3L[x, y] = (r, g, b, a) #使用新RGBA数据填充新图片的像素
    return IM3

def spine_resolve(fp:str):
    ''''
    #### 干员战斗小人Spine图片的正背面的名称都一样，但解包时我们加了后缀"_#"，
    #### 这时就需要此函数帮我们找到哪个RGB通道图的"_#"能和这个A通道图匹配了
    :param fp: A通道图的文件路径;
    :returns:  (str|bool) RGB通道图的文件路径，失败返回False;
    '''
    spines = [] #[filepath,confidence]
    ospath = os.path
    fpdir = ospath.dirname(fp)
    fpfile = ospath.basename(fp)
    flist = os.listdir(os.path.dirname(fp))
    flist = list(filter(lambda x:'_#' in x, flist)) #初筛
    flist = list(filter(lambda x:'[alpha]_#' not in x, flist)) #初筛
    for i in flist:
        #(i是初筛后文件的路径名)
        i = ospath.basename(i)
        if '_#' in i and fpfile != i\
            and len(i) >8 and fpfile[:8] == i[:8]:
            i = ospath.join(fpdir, i)
            if ospath.isfile(i):
                #找到了一个疑似的图片
                spines.append([i,similarity(i,fp)])
    if len(spines) == 0:
        return False #找不到，退出
    spines = sorted(spines, key=lambda x:-x[1]) #根据置信度降序排序
    print(f'{color(6)} Match {ospath.basename(spines[0][0])}  Confi {spines[0][1]}')
    return spines[0][0] #成功，返回置信度最高的图片的文件路径

def similarity(fp_rgb:str, fp_a:str, prec:float=0.1):
    '''
    #### 返回两张图片的相似度，仅对比各像素的灰度
    :param fp_rgb: RGB通道图的文件路径;
    :param fp_a:   A通道图的文件路径;
    :param prec:   介于(0,1]的判断精度，值越大越精确，不宜过小，默认0.1;
    :returns:      (int) 介于[0,255]的相似度，值越大越相似;
    '''
    IM1 = Image.open(fp_rgb).convert('L') #RGB通道图实例化(L:灰度模式)
    IM2 = Image.open(fp_a).convert('L') #A通道图实例化(L:灰度模式)
    prec = 1 if prec > 1 else (0 if prec < 0 else prec)
    w,h = (int(IM1.size[0]*prec), int(IM1.size[0]*prec)) #新图片尺寸取自RGB通道图尺寸再乘以精度
    if not (w > 0 and h > 0):
        return 0 #精度太小，退出
    #对两张图片进行缩放
    IM1 = IM1.resize((w,h), Image.ANTIALIAS)
    IM2 = IM2.resize((w,h), Image.ANTIALIAS)
    #载入原图片的像素到数组
    IM1L = IM1.load()
    IM2L = IM2.load()
    Diff = [] #所有位点的差值的数组
    #对比各像素灰度
    for y in range(0, h):
        for x in range(0, w):
            #遍历到每个像素(x,y是像素的坐标)
            Diff.append(abs(IM1L[x,y]-IM2L[x,y]))
    #计算差值的平均值，然后返回相似度
    Diff_mean = round(mean(Diff))
    return 0 if Diff_mean >= 255 else (255 if Diff_mean <= 0 else 255-Diff_mean)

def mean(lst:list):
    '''
    #### 返回数组平均值
    :param lst: 要计算的列表;
    :returns:   (float) 数组平均值;
    '''
    if len(lst) == 0:
        return float(0)
    s = 0
    for i in lst:
        s += i
    return float(s/len(lst))

def image_resolve(fp:str, intodir:str, docover:bool=True):
    '''
    #### 判断某图片的名称是否包含A通道图的特定命名特征，
    #### 如果是的话就寻找它的RGB通道图进行合并，然后保存合并的图片
    :param fp:      图片的文件路径;
    :param intodir: 保存目的地的目录;
    :param docover: 是否覆盖重名的已存在的文件，默认True;
    :returns:       (int) 执行状态代码;
    '''
    ospath = os.path
    oridir = ospath.dirname(fp) #原图的目录
    name, ext = ospath.splitext(ospath.basename(fp)) #纯文件名和纯扩展名
    if '[alpha]_#' in name and '.png' == ext:
        #我的天！居然是解包出来的Spine图片
        fp2 = spine_resolve(fp)
        if not fp2:
            return 6 #居然匹配不到，退出
        #dest是新图的保存路径
        tmp = 0
        dest = findall(r'.+\[alpha\]_#', name)
        dest = ospath.join(intodir, dest[0])
        while ospath.isfile(dest+str(tmp)+'.png'):
            tmp += 1
        dest = dest+str(tmp)+'.png'
    else:
        if not ext.lower() in ['.png', '.jpg', '.jpeg', '.bmp']:
            return 1 #不是图片文件，退出
        elif name[-7:] == '[alpha]':
            fp2 = ospath.join(oridir, name[:-7] + ext)
        elif name[-6:] == '_alpha':
            fp2 = ospath.join(oridir, name[:-6] + ext)
        else:
            return 2 #不是指定的A通道图，退出
        dest = ospath.join(intodir, ospath.basename(fp2))
    ###
    if not docover and ospath.isfile(dest):
        return 3 #新图已存在且没让覆盖，退出
    if not ospath.isfile(fp):
        print(f'{color(1)}  错误：alpha通道图缺失{color(7)} {fp}')
        return 4 #找不到对应的A通道图，退出
    if not ospath.isfile(fp2):
        print(f'{color(1)}  错误：RGB通道图缺失{color(7)} {fp2}')
        return 5 #找不到对应的RGB通道图，退出
    mkdir(intodir)
    #print(color(7)+fp2)
    IM = combine_rgb_a(fp2, fp)
    if IM:
        IM.save(dest) #保存新图
        return 0 #成功，返回0
    else:
        print(f'{color(1)}  错误：通道图合成失败{color(7)}')
        return -1 #图片合成函数返回了失败的结果，退出



########## Main-主程序 ##########
def main(rootdir:list, destdir:str, dodel:bool=False, docover:bool=True, detail:bool=True):
    '''
    #### 批量地从指定目录中，找到名称相互匹配的RGB通道图和A通道图，然后合并图片后保存到另一目录
    :param rootdir: 包含来源文件夹们的路径的列表;
    :param destdir: 解包目的地的根目录的路径;
    :param dodel:   预先删除目的地文件夹的所有文件，默认False;
    :param docover: 是否覆盖重名的已存在的文件，默认True;
    :param detail:  是否回显详细信息，默认True，否则回显进度条;
    :returns: (None);
    '''
    print(f'{color(7,0,1)}\n正在解析目录...{color(7)}')
    ospath = os.path
    flist = [] #目录下所有文件的列表
    for i in rootdir:
        flist += get_filelist(i)
    flist = list(filter(lambda x:'alpha' in ospath.basename(x), flist)) #初筛
    flist = list(filter(lambda x:ospath.splitext(x)[1].lower() in ['.png', '.jpg', '.jpeg', '.bmp'], flist)) #初筛
    
    cont_f = 0 #已合并图片计数
    cont_a = 0 #已遍历文件计数
    cont_p = 0 #进度百分比计数
    cont_l1 = 0 #上个文件用时
    if dodel:
        Delete_File_Dir(destdir) #慎用，会预先删除目的地目录的所有内容
    mkdir(destdir)

    if detail:
        print(f'{color(7,0,1)}开始批量合并图片!\n{color(7)}')
    t1=time.time() #计时器1开始

    for i in flist:
        #递归处理各个文件(i是文件的路径名)
        cont_a += 1
        cont_p = round((cont_a/len(flist))*100,1)
        if not ospath.isfile(i):
            continue #跳过目录等非文件路径
        #测试相关：
        #abc=combine_rgb_a('', '')
        #abc.save('1.png')
        #input()
        if detail:
            print(f'{color(7)}{ospath.basename(i)}')
        else:
            #显示模式B：简洁
            os.system('cls')
            print(f'{color(7)}正在合并图片...')
            print(f'|{"■"*int(cont_p//5)}{"□"*int(20-cont_p//5)}| {color(2)}{cont_p}%{color(7)}')
            print(f'当前目录：\t{ospath.dirname(i)}')
            print(f'当前文件：\t{ospath.basename(i)}')
            print(f'累计合并：\t{cont_f}')
            print(f'{color(6)}上个用时：\t{cont_l1}秒{color(7)}\n')
        ###
        t3=time.time() #计时器2开始
        result = image_resolve(i, ospath.join(destdir, ospath.dirname(i)), docover)
        if result == 0:
            t4=time.time() #计时器2结束
            cont_f += 1
            cont_l1 = round(t4-t3,2)
            if detail:
                print(f'{color(2)}  成功 ({cont_l1}s){color(7)}')
        elif result in [3]:
            if detail:
                print(f'{color(6)}  跳过 (重名){color(7)}')
        else:
            if detail:
                print(f'{color(6)}  跳过 (状态码{result}){color(7)}')

    t2=time.time() #计时器1结束
    if not detail:
        os.system('cls')
    print(f'{color(7,0,1)}\n批量合并图片结束!')
    print(f'  累计合并 {cont_f} 张图片')
    print(f'  此项用时 {round(t2-t1, 1)} 秒{color(7)}')
    time.sleep(2)