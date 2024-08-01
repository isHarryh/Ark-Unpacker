# -*- coding: utf-8 -*-
# Copyright (c) 2022-2024, Harry Huang
# @ BSD 3-Clause License
import os.path as osp
import re
from .utils import *
from PIL import Image


class NoRGBImageMatchedError(FileNotFoundError):
    def __init__(self, *args):
        super().__init__(*args)

class AlphaRGBCombiner:
    PATTERNS = [
        re.compile(r'(.+)\[alpha\](\$[0-9]+)?'),
        re.compile(r'(.+)_alpha(\$[0-9]+)?'),
        re.compile(r'(.+)alpha(\$[0-9]+)?'),
        re.compile(r'(.+)a(\$[0-9]+)?'),
        ]

    def __init__(self, alpha:"str|Image.Image"):
        self.img_alpha = AlphaRGBCombiner.as_image(alpha, 'RGBA')
    
    def combine_with(self, rgb:"str|Image.Image"):
        """ Merges the RGB image and the Alpha image in an efficient way.

        :param rgb: Instance of RGB image or its file path;
        :returns: A new image instance;
        :rtype: Image;
        """
        img_rgb:Image.Image = AlphaRGBCombiner.as_image(rgb, 'RGBA')
        img_alpha:Image.Image = self.img_alpha.convert('L')
        if not (img_rgb.size == img_alpha.size):
            img_alpha = img_alpha.resize(img_rgb.size, Image.BILINEAR)
        img_black = Image.new('RGBA', img_rgb.size) #透明抹除全黑图实例化
        img_mask = img_alpha.point(lambda x:0 if x > 0 else 255) #透明抹除蒙版图实例化
        img_rgb.putalpha(img_alpha) #RGB通道图使用A通道图作为alpha层
        img_rgb.paste(img_black, img_mask) #RGB通道图被执行透明抹除
        return img_rgb
    
    @staticmethod
    def search_rgb(fp_alpha:str):
        real = AlphaRGBCombiner.get_real_name(fp_alpha)
        if not real:
            raise ValueError("Not a recognized alpha image name")
        if not is_image_file(fp_alpha):
            raise ValueError("Not a image file path")
        ext = osp.splitext(fp_alpha)[1]
        dirname = osp.dirname(fp_alpha)
        flist = os.listdir(dirname)
        flist = list(filter(lambda x:is_image_file(x), flist))
        flist = list(filter(lambda x:x == real + ext or (x.startswith(real) and '$' in x), flist))
        flist = [osp.join(dirname, x) for x in flist]
        if len(flist) == 0:
            Logger.info(f"CombineRGBwithA: No RGB-image could be matched to \"{fp_alpha}\"")
            raise NoRGBImageMatchedError(fp_alpha)
        elif len(flist) == 1:
            Logger.debug(f"CombineRGBwithA: \"{flist[0]}\" matched \"{fp_alpha}\" exclusively")
            return flist[0]
        else:
            best, similarity = AlphaRGBCombiner.choose_most_similar_rgb(fp_alpha, flist)
            Logger.info(f"CombineRGBwithA: \"{best}\" matched \"{fp_alpha}\" among {len(flist)} candidates, confidentiality {similarity}")
            return best
    
    @staticmethod
    def choose_most_similar_rgb(alpha, candidates:"list[str]"):
        best_candidate = None
        best_similarity = -1
        for i in candidates:
            similarity = AlphaRGBCombiner.similarity(i, alpha)
            if similarity > best_similarity:
                best_candidate = i
                best_similarity = similarity
        return best_candidate, similarity
    
    @staticmethod
    def get_real_name(fp_alpha:str):
        basename, ext = osp.splitext(osp.basename(fp_alpha))
        for i in AlphaRGBCombiner.PATTERNS:
            m = i.fullmatch(basename)
            if m:
                return m.group(1)
        return  None

    @staticmethod    
    def as_image(obj:"str|Image.Image", mode:str):
        return (obj if type(obj) == Image.Image else Image.open(obj)).convert(mode)
    
    @staticmethod
    def similarity(fp_rgb:str, fp_alpha:str, mode:str='L', prec:int=150):
        """ Compares the similarity between the RGB image and the Alpha image.

        :param fp_rgb: Path to the RGB image;
        :param fp_alpha: Path to the Alpha image;
        :param mode: Image mode, `L` for default;
        :param prec: Precision of the judgement, higher for more precise, `150` for default;
        :returns: Similarity value in `[0, 255]`, higher for more similar;
        :rtype: int;
        """
        img_rgb = Image.open(fp_rgb).convert(mode)
        img_a = Image.open(fp_alpha).convert(mode)
        prec = 150 if prec <= 0 else prec
        # Resize the two images
        img_rgb = img_rgb.resize((prec, prec), Image.BILINEAR)
        img_a = img_a.resize((prec, prec), Image.BILINEAR)
        # Load pixels into arrays
        px_rgb = img_rgb.load()
        px_a = img_a.load()
        # Calculate differences of every pixel
        diff = []
        for y in range(prec):
            for x in range(prec):
                diff.append((((px_rgb[x, y] if px_rgb[x, y] < 255 else 0) - px_a[x, y]) ** 2) / 256)
        # Return the similarity
        diff_mean = round(sum(diff) / len(diff))
        return 0 if diff_mean >= 255 else (255 if diff_mean <= 0 else 255 - diff_mean)

def image_resolve(fp:str, destdir:str, \
                  on_processed:staticmethod, on_file_queued:staticmethod, on_file_saved:staticmethod):
    """Finds an RGB image to combine with the given Alpha image then saves the combined image into the given directory.

    :param fp: Path to the Alpha image;
    :param destdir: Destination directory;
    :param on_processed: Callback `f()` for finished, `None` for ignore;
    :param on_file_queued: Callback `f()` invoked when a file was queued, `None` for ignore;
    :param on_file_saved: Callback `f(file_path_or_none_for_not_saved)`, `None` for ignore;
    :rtype: None;
    """
    try:
        handle = AlphaRGBCombiner(fp)
        result = handle.combine_with(AlphaRGBCombiner.search_rgb(fp))
        SafeSaver.save_image(result, destdir, AlphaRGBCombiner.get_real_name(fp), \
                             on_queued=on_file_queued, on_saved=on_file_saved)
    except NoRGBImageMatchedError:
        pass
    except BaseException as arg:
        # Error feedback
        Logger.error(f"CombineRGBwithA: Error occurred while processing alpha image \"{fp}\": Exception{type(arg)} {arg}")
        raise(arg)
    if on_processed:
        on_processed()

########## Main-主程序 ##########
def main(rootdir:str, destdir:str, dodel:bool=False):
    """Combines the RGB images and the Alpha images in the given directory automatically according to their file names,
    then saves the combined images into another given directory.

    :param rootdir: Source directory;
    :param destdir: Destination directory;
    :param dodel: Whether to delete the existed destination directory first, `False` for default;
    :rtype: None;
    """
    print(f"\n正在解析路径...", s=1)
    Logger.info("CombineRGBwithA: Retrieving file paths...")
    rootdir = osp.normpath(osp.realpath(rootdir))
    destdir = osp.normpath(osp.realpath(destdir))
    flist = get_filelist(rootdir)
    flist = list(filter(lambda x:is_image_file(x), flist))
    flist = list(filter(lambda x:AlphaRGBCombiner.get_real_name(x) != None, flist))

    if dodel:
        print("\n正在清理...", s=1)
        rmdir(destdir) #慎用，会预先删除目的地目录的所有内容
    SafeSaver.get_instance().reset_counter()
    TC = ThreadCtrl(PerformanceLevel.get_thread_limit(Config.get('performance_level')))
    UI = UICtrl()
    TR = TimeRecorder()
    TR.update_dest(2, len(flist))
    on_processed = lambda: TR.done_once(2)
    on_file_queued = lambda: TR.update_dest(1)
    on_file_saved = lambda x: TR.done_once(1) if x else TR.update_dest(1, -1)

    UI.reset()
    UI.loop_start()
    for i in flist:
        #递归处理各个文件(i是文件的路径名)
        UI.request([
            f"正在批量合并图片...",
            TR.get_progress_str(),
            f"当前目录：\t{osp.basename(osp.dirname(i))}",
            f"当前文件：\t{osp.basename(i)}",
            f"累计搜索：\t{TR.get_done_dest_str_of(2)}",
            f"累计导出：\t{TR.get_done_dest_str_of(1)}",
            f"剩余时间：\t{TR.get_eta_str()}",
        ])
        ###
        subdestdir = osp.dirname(i).strip(osp.sep).replace(rootdir, '').strip(osp.sep)
        TC.run_subthread(image_resolve, (i, osp.join(destdir, subdestdir), on_processed, on_file_queued, on_file_saved), \
            name=f"CBThread:{id(i)}")

    UI.reset()
    UI.loop_stop()
    while TC.count_subthread() or not SafeSaver.get_instance().completed() or TR.get_progress() < 1:
        UI.request([
            f"正在批量合并图片...",
            TR.get_progress_str(),
            f"累计搜索：\t{TR.get_done_dest_str_of(2)}",
            f"累计导出：\t{TR.get_done_dest_str_of(1)}",
            f"剩余时间：\t{TR.get_eta_str()}",
        ])
        UI.refresh(post_delay=0.1)

    UI.reset()
    print(f"\n批量合并图片结束!", s=1)
    print(f"  累计导出 {TR.get_done_of(1)} 张照片")
    print(f"  此项用时 {round(TR.get_rt(), 1)} 秒")
