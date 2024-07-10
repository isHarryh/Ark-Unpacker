# -*- coding: utf-8 -*-
# Copyright (c) 2022-2024, Harry Huang
# @ BSD 3-Clause License
import os.path, time
from .utils import *
from re import findall
from PIL import Image


def combine_rgb_a(rgb:"str|Image.Image", a:"str|Image.Image"):
    """ Merges the RGB image and the Alpha image in an efficient way.

    :param fp_rgb: Instance of RGB image or its file path;
    :param fp_a: Instance of Alpha image or its file path;
    :returns: A new image instance;
    :rtype: Image;
    """
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
    """ Finds which RGB image could match this Alpha image.

    :param fp: Path to the Alpha image;
    :returns: Path to the RGB image, False for failure;
    :rtype: str|bool;
    """
    os.path = os.path
    fpdir = os.path.dirname(fp)
    fpfile = os.path.basename(fp)
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
        iname, iext = os.path.splitext(i)
        if not iext.lower() == '.png':
            continue #不是png图片文件，跳过
        ireal = findall(r'.+$', iname)
        ireal = iname if len(ireal) == 0 else ireal[0][:-2]
        if ireal == fpreal:
            i = os.path.join(fpdir, i) #i变成初筛后的路径名
            if os.path.isfile(i):
                #找到了一个疑似的图片
                spines.append([i, similarity(i, fp)])
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

def similarity(fp_rgb:str, fp_a:str, prec:int=150):
    """ Compares the similarity between the RGB image and the Alpha image.

    :param fp_rgb: Path to the RGB image;
    :param fp_a: Path to the Alpha image;
    :param prec: Precision of the judgement, higher for more precise, `150` for default;
    :returns: Similarity value in `[0, 255]`, higher for more similar;
    :rtype: int;
    """
    IM1 = Image.open(fp_rgb).convert('L') #RGB通道图实例化(L:灰度模式)
    IM2 = Image.open(fp_a).convert('L') #A通道图实例化
    prec = 100 if prec < 0 else prec
    #对两张图片进行缩放
    IM1 = IM1.resize((prec, prec), Image.BICUBIC)
    IM2 = IM2.resize((prec, prec), Image.BICUBIC)
    #载入原图片的像素到数组
    IM1L = IM1.load()
    IM2L = IM2.load()
    Diff = [] #所有位点的差值的数组
    #对比它们每个像素的相似度
    for y in range(prec):
        for x in range(prec):
            #遍历到每个像素(x,y是像素的坐标)
            Diff.append((((IM1L[x, y] if IM1L[x, y] < 255 else 0) - IM2L[x, y])**2)/256)
    #计算差值的平均值，然后返回相似度
    Diff_mean = round(mean(Diff))
    return 0 if Diff_mean >= 255 else (255 if Diff_mean <= 0 else 255-Diff_mean)

def image_resolve(fp:str, destdir:str, \
                  on_processed:staticmethod, on_file_queued:staticmethod, on_file_saved:staticmethod):
    """ Judges whether the given image may be an Alpha image from its file name,
    then tries to find an RGB image to merge with it.

    :param fp: Path to the image;
    :param destdir: Destination directory;
    :param on_processed: Callback `f()` for finished, `None` for ignore;
    :param on_file_queued: Callback `f()` invoked when a file was queued, `None` for ignore;
    :param on_file_saved: Callback `f(file_path_or_none_for_not_saved)`, `None` for ignore;
    :returns: Status code;
    :rtype: int;
    """
    oridir = os.path.dirname(fp) #原图的目录
    name, ext = os.path.splitext(os.path.basename(fp)) #纯文件名和纯扩展名
    if not ext.lower() == '.png' or not os.path.isfile(fp):
        if on_processed: on_processed()
        return 1 #不是png图片文件，退出
    ###
    if '[alpha]' in name: #xxx[alpha]xxx.png形式 
        fp2 = alpha_resolve(fp)
        if not fp2:
            if on_processed: on_processed()
            return 2 #匹配不到，退出
        real = findall(r'.+\[alpha\]', name)[0][:-7]
    elif name[-6:] == '_alpha': #xxx_alpha.png形式
        fp2 = os.path.join(oridir, name[:-6] + ext)
        real = name[:-6]
    else:
        if on_processed: on_processed()
        return 3 #不是指定的A通道图，退出
    ###
    if not os.path.isfile(fp):
        Logger.warn(f"CombineRGBwithA: Alpha-image not found: \"{fp}\"")
        if on_processed: on_processed()
        return 4 #找不到对应的A通道图，退出
    if not os.path.isfile(fp2):
        Logger.warn(f"CombineRGBwithA: RGB-image not found: \"{fp}\"")
        if on_processed: on_processed()
        return 5 #找不到对应的RGB通道图，退出
    IM = combine_rgb_a(fp2, fp)
    if IM:
        Logger.debug(f"CombineRGBwithA: \"{fp}\" -> \"{fp2}\"")
        SafeSaver.save_image(IM, destdir, real, on_queued=on_file_queued, on_saved=on_file_saved)
        if on_processed: on_processed()
    else:
        Logger.warn(f"CombineRGBwithA: Failed to combine \"{fp}\" with \"{fp2}\"")
        if on_processed: on_processed()
        return -1 #图片合成函数返回了失败的结果，退出


########## Main-主程序 ##########
def main(rootdir:str, destdir:str, dodel:bool=False):
    """Combines the RGB images and the Alpha images in the given directory automatically according to their file names,
    then saves the combined images into another given directory.

    :param rootdir: Source directory;
    :param destdir: Destination directory;
    :param dodel: Whether to delete the existed destination directory first, `False` for default;
    :rtype: None;
    """
    print(f'\n正在解析路径...', s=1)
    Logger.info("CombineRGBwithA: Retrieving file paths...")
    rootdir = os.path.normpath(os.path.realpath(rootdir))
    destdir = os.path.normpath(os.path.realpath(destdir))
    flist = get_filelist(rootdir)
    flist = list(filter(lambda x:'alpha' in os.path.basename(x), flist))
    flist = list(filter(lambda x:is_image_file(x), flist))

    if dodel:
        print("\n正在清理...", s=1)
        rmdir(destdir) #慎用，会预先删除目的地目录的所有内容
    SafeSaver.get_instance().reset_counter()
    TC = ThreadCtrl(PerformanceLevel.get_thread_limit(Config.get('performance_level')))
    UI = UICtrl(0.5)
    TR = TimeRecorder()
    TR.update_dest(2, len(flist))
    on_processed = lambda: TR.done_once(2)
    on_file_queued = lambda: TR.update_dest(1)
    on_file_saved = lambda x: TR.done_once(1) if x else TR.update_dest(1, -1)

    UI.reset()
    UI.loop_start()
    for i in flist:
        #递归处理各个文件(i是文件的路径名)
        TR_p = TR.get_progress()
        TR_r = TR.get_remaining_time()
        UI.request([
            f'正在批量合并图片...',
            f'|{progress_bar(TR_p, 25)}| {color(2, 0, 1)}{round(TR_p*100, 1)}%',
            f'当前目录：\t{os.path.basename(os.path.dirname(i))}',
            f'当前文件：\t{os.path.basename(i)}',
            f'累计处理：\t{TR.get_done_of(2)}',
            f'累计导出：\t{TR.get_done_of(1)}',
            f'剩余时间：\t{f"{round(TR_r / 60, 1)}min" if TR_r > 0 else "计算中"}',
        ])
        ###
        subdestdir = os.path.dirname(i).strip(os.path.sep).replace(rootdir, '').strip(os.path.sep)
        TC.run_subthread(image_resolve, (i, os.path.join(destdir, subdestdir), on_processed, on_file_queued, on_file_saved), \
            name=f"CBThread:{id(i)}")

    spin = LineSpinner()
    UI.reset()
    UI.loop_stop()
    while TC.count_subthread() or not SafeSaver.get_instance().completed():
        #等待子进程结束
        while TR.get_progress() < 1:
            TR_p = TR.get_progress()
            TR_r = TR.get_remaining_time()
            UI.request([
                f'正在批量合并图片...',
                f'|{progress_bar(TR_p, 25)}| {color(2, 0, 1)}{round(TR_p*100, 1)}%',
                f'累计处理：\t{TR.get_done_of(2)}',
                f'累计导出：\t{TR.get_done_of(1)}',
                f'剩余时间：\t{f"{round(TR_r / 60, 1)}min" if TR_r > 0 else "计算中"}',
            ])
            UI.refresh(post_delay=0.2)
        UI.request([
            '正在批量合并图片...',
            f'|正在等待子进程结束| {color(2, 0, 1)}{spin.next()}',
            f'累计处理：\t{TR.get_done_of(2)}',
            f'累计导出：\t{TR.get_done_of(1)}',
            f'剩余时间：\t--',
        ])
        UI.refresh(post_delay=0.2)

    UI.reset()
    print(f'\n批量合并图片结束!', s=1)
    print(f'  累计导出 {TR.get_done_of(1)} 张照片')
    print(f'  此项用时 {round(TR.get_consumed_time())} 秒')
    time.sleep(2)
