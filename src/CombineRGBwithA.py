# -*- coding: utf-8 -*-
# Copyright (c) 2022, Harry Huang
# @ BSD 3-Clause License
import os, time
try:
    from osTool import *
    from colorTool import *
except:
    from .osTool import *
    from .colorTool import *
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
        print(color(3)+'  警告：通道图尺寸不一，已缩放处理')
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


def image_resolve(fp:str, intodir:str, docover:bool=True):
    '''
    #### 判断某图片的名称是否包含A通道图的特定命名特征，
    #### 如果是的话就寻找它的RGB通道图进行合并，然后保存合并的图片
    :param fp:      图片的文件路径;
    :param intodir: 保存目的地的目录;
    :param docover: 是否覆盖重名的已存在的文件，默认True;
    :returns:       (int) 执行状态代码;
    '''
    oridir = os.path.dirname(fp) #原图的目录
    name, ext = os.path.splitext(os.path.basename(fp)) #原图纯文件名和纯扩展名
    if not ext.lower() in ['.png', '.jpg', '.jpeg', '.bmp']:
        return 1 #不是图片文件，退出
    if name[-7:].lower() == '[alpha]':
        fp2 = os.path.join(oridir, name[:-7] + ext) #RGB通道图的路径
    elif name[-6:].lower() == '_alpha':
        fp2 = os.path.join(oridir, name[:-6] + ext)
    else:
        return 2 #不是指定的A通道图，退出
    dest = os.path.join(intodir, os.path.basename(fp2)) #新图的路径
    if not docover and os.path.isfile(dest):
        return 3 #新图已存在且没让覆盖，退出
    if not os.path.isfile(fp):
        print(color(1)+'  错误：alpha通道图缺失'+color(7), fp)
        return 4 #找不到对应的A通道图，退出
    if not os.path.isfile(fp2):
        print(color(1)+'  错误：RGB通道图缺失'+color(7), fp2)
        return 5 #找不到对应的RGB通道图，退出
    mkdir(intodir)
    #print(color(7)+fp2)
    IM = combine_rgb_a(fp2, fp)
    if IM:
        IM.save(dest) #保存新图
        return 0 #成功，返回0
    else:
        print(color(1)+'  错误：通道图合成失败'+color(7))
        return -1 #图片合成函数返回了失败的结果，退出



########## Main-主程序 ##########
def main(rootdir:list, destdir:str, dodel:bool=False, docover:bool=True):
    '''
    #### 批量地从指定目录中，找到名称相互匹配的RGB通道图和A通道图，然后合并图片后保存到另一目录
    :param rootdir: 包含来源文件夹们的路径的列表;
    :param destdir: 解包目的地的根目录的路径;
    :param dodel:   预先删除目的地文件夹的所有文件，默认False;
    :param docover: 是否覆盖重名的已存在的文件，默认True;
    :returns: (None);
    '''
    print(color(7,0,1)+'\n正在解析目录...'+color(7))
    flist = [] #目录下所有文件的列表
    for i in rootdir:
        flist += get_filelist(i)

    cont_f = 0 #已合并图片计数
    if dodel:
        Delete_File_Dir(destdir) #慎用，会预先删除目的地目录的所有内容
    mkdir(destdir)

    print(color(7,0,1)+'开始批量合并图片!\n'+color(7))
    t1=time.time() #计时器1开始

    for i in flist:
        #递归处理各个文件(i是文件的路径名)
        if not os.path.isfile(i):
            continue #跳过目录等非文件路径
        if not os.path.splitext(i)[1].lower() in ['.png', '.jpg', '.jpeg', '.bmp']:
            continue #不是图片文件，跳过
        #测试相关：
        #abc=combine_rgb_a('',
        #    '')
        #abc.save('1.png')
        #input()
        print(color(7)+os.path.basename(i))
        t3=time.time() #计时器2开始
        result = image_resolve(i, destdir, docover=True)
        if result == 0:
            t4=time.time() #计时器2结束
            print(color(2)+'  成功 (', round(t4-t3, 2), 's )'+color(7))
            cont_f += 1
        elif result in [1,2]:
            print(color(6)+'  跳过'+color(7))
        elif result in [3]:
            print(color(6)+'  跳过(重名)'+color(7))

    t2=time.time() #计时器1结束
    print(color(7,0,1)+'\n批量合成图片结束!')
    print('  累计合成', cont_f, '张图片')
    print('  用时', round(t2-t1, 1), '秒'+color(7))