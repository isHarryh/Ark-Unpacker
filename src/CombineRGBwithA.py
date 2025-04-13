# -*- coding: utf-8 -*-
# Copyright (c) 2022-2025, Harry Huang
# @ BSD 3-Clause License
import re
import os
import os.path as osp
import numpy as np
from typing import Callable, Optional

from PIL import Image
from .utils.GlobalMethods import print, rmdir, get_filelist, is_image_file
from .utils.Logger import Logger
from .utils.SaverUtils import SafeSaver
from .utils.TaskUtils import ThreadCtrl, UICtrl, TaskReporter, TaskReporterTracker


class NoRGBImageMatchedError(FileNotFoundError):
    def __init__(self, *args):
        super().__init__(*args)


class AlphaRGBCombiner:
    def __init__(self, alpha: "str|Image.Image"):
        self.img_alpha = image_open(alpha, "RGBA")

    def combine_with(
        self,
        rgb: "str|Image.Image",
        resize: Optional[tuple] = None,
        remove_bleeding: bool = True,
    ):
        """Merges the RGB image and the Alpha image in an efficient way.

        :param rgb: Instance of RGB image or its file path;
        :param resize: Resize the final image to the given size, `None` for disabled;
        :param remove_bleeding: Whether to remove the color bleeding;
        :returns: A new image instance;
        :rtype: Image;
        """
        img_rgb: Image.Image = image_open(rgb, "RGBA")
        img_alpha: Image.Image = self.img_alpha.convert("L")
        if resize:
            img_rgb = image_resize(img_rgb, resize)
            img_alpha = image_resize(img_alpha, resize)
        else:
            img_alpha = image_resize(img_alpha, img_rgb.size)
        img_rgb.putalpha(img_alpha)
        if remove_bleeding:
            img_rgb = AlphaRGBCombiner.remove_bleeding(img_rgb)
        return img_rgb

    @staticmethod
    def remove_bleeding(rgba: "str|Image.Image", min_alpha: int = 0):
        """Removes the color bleeding in the given RGBA image
        by setting the RGB value of the transparent pixel to (0, 0, 0).

        :param rgba: Instance of RGBA image or its file path;
        :param min_alpha: The minimal alpha value to determine transparency;
        :returns: A new image instance;
        :rtype: Image;
        """
        img_rgba: Image.Image = image_open(rgba, "RGBA")
        img_black = Image.new("RGBA", img_rgba.size)
        img_alpha = img_rgba.getchannel("A")
        img_mask = img_alpha.point(lambda x: 0 if x > min_alpha else 255)
        img_rgba.paste(img_black, img_mask)
        return img_rgba

    @staticmethod
    def apply_premultiplied_alpha(
        rgba: "str|Image.Image", resize: Optional[tuple] = None
    ):
        """Multiplies the RGB channels with the alpha channel.
        Useful when handling non-PMA Spine textures.

        :param rgba: Instance of RGBA image or its file path;
        :param resize: Resize the final image to the given size, `None` for disabled;
        :returns: A new image instance;
        :rtype: Image;
        """
        img_rgba: Image.Image = image_open(rgba, "RGBA")
        if resize:
            # Resize RGB/A channel separately
            data = np.array(img_rgba, dtype=np.float32)
            img_rgb = Image.fromarray(data[:, :, :3], "RGB")
            img_alpha = Image.fromarray(data[:, :, 3], "L")
            img_rgb = image_resize(img_rgb, resize)
            img_alpha = image_resize(img_alpha, resize)
            img_rgb.putalpha(img_alpha)
        # Apply PMA
        data = np.array(img_rgba, dtype=np.float32)
        data[:, :, :3] *= data[:, :, 3:] / 255.0
        data_int = np.clip(data, 0, 255).astype(np.uint8)
        return Image.fromarray(data_int, "RGBA")


class AlphaRGBSearcher:
    PATTERNS = [
        re.compile(r"(.+)\[alpha\](\$[0-9]+)?"),
        re.compile(r"(.+)_alpha(\$[0-9]+)?"),
        re.compile(r"(.+)alpha(\$[0-9]+)?"),
        re.compile(r"(.+)a(\$[0-9]+)?"),
    ]

    def __init__(self, fp_alpha: str):
        self.fp_alpha = fp_alpha

    def get_real_name(self):
        return AlphaRGBSearcher.calc_real_name(self.fp_alpha)

    def search_rgb(self):
        real = self.get_real_name()
        if not real:
            raise ValueError("Not a recognized alpha image name")
        if not is_image_file(self.fp_alpha):
            raise ValueError("Not a image file path")
        ext = osp.splitext(self.fp_alpha)[1]
        dirname = osp.dirname(self.fp_alpha)
        flist = os.listdir(dirname)
        flist = list(filter(is_image_file, flist))
        flist = list(
            filter(
                lambda x: x == real + ext or (x.startswith(real) and "$" in x), flist
            )
        )
        flist = [osp.join(dirname, x) for x in flist]

        if len(flist) == 0:
            Logger.info(
                f'CombineRGBwithA: No RGB-image could be matched to "{self.fp_alpha}"'
            )
            raise NoRGBImageMatchedError(self.fp_alpha)
        elif len(flist) == 1:
            Logger.debug(
                f'CombineRGBwithA: "{flist[0]}" matched "{self.fp_alpha}" exclusively'
            )
            return flist[0]
        else:
            best, similarity = self.choose_most_similar_rgb(flist)
            if best:
                Logger.info(
                    f'CombineRGBwithA: "{best}" matched "{self.fp_alpha}" among {len(flist)} candidates, confidentiality {similarity}'
                )
                return best
            else:
                raise NoRGBImageMatchedError(self.fp_alpha)

    def choose_most_similar_rgb(self, candidates: "list[str]"):
        best_candidate = None
        best_similarity = -1
        for i in candidates:
            similarity = AlphaRGBSearcher.calc_similarity(i, self.fp_alpha)
            if similarity > best_similarity:
                best_candidate = i
                best_similarity = similarity
        return best_candidate, best_similarity

    @staticmethod
    def calc_real_name(fp_alpha: str):
        basename, _ = osp.splitext(osp.basename(fp_alpha))
        for p in AlphaRGBSearcher.PATTERNS:
            m = p.fullmatch(basename)
            if m:
                return m.group(1)

    @staticmethod
    def calc_similarity(
        rgb: "str|Image.Image",
        alpha: "str|Image.Image",
        mode: str = "L",
        precision: int = 150,
    ):
        """Compares the similarity between the RGB image and the Alpha image.

        :param rgb: Instance of RGB image or its file path;
        :param alpha: Instance of Alpha image or its file path;
        :param mode: Image mode during comparing, `L` for default;
        :param precision: Precision of the judgement, higher for more precise, `150` for default;
        :returns: Similarity value in `[0, 255]`, higher for more similar;
        :rtype: int;
        """
        img_rgb = image_open(rgb, mode)
        img_alpha = image_open(alpha, mode)
        precision = 150 if precision <= 0 else precision
        # Resize the two images
        img_rgb = image_resize(img_rgb, (precision, precision))
        img_alpha = image_resize(img_alpha, (precision, precision))
        # Load pixels into arrays
        px_rgb = img_rgb.load()
        px_a = img_alpha.load()
        # Calculate differences of every pixel
        diff = []
        for y in range(precision):
            for x in range(precision):
                diff.append(
                    (((px_rgb[x, y] if px_rgb[x, y] < 255 else 0) - px_a[x, y]) ** 2)
                    / 256.0
                )
        # Return the similarity
        diff_mean = round(sum(diff) / len(diff))
        return 0 if diff_mean >= 255 else (255 if diff_mean <= 0 else 255 - diff_mean)


def image_open(fp_or_img: "str|Image.Image", mode: str):
    if isinstance(fp_or_img, Image.Image):
        img = fp_or_img
    else:
        img = Image.open(fp_or_img)
    img = img.convert(mode)
    assert isinstance(img, Image.Image)
    return img


def image_resize(img: Image.Image, size: tuple):
    if len(img.size) == 2 and len(size) == 2:
        if img.size[0] != size[0] or img.size[1] != size[1]:
            img = img.resize(size, resample=Image.BILINEAR)
    assert isinstance(img, Image.Image)
    return img


def image_resolve(
    fp: str,
    destdir: str,
    on_processed: Optional[Callable],
    on_file_queued: Optional[Callable],
    on_file_saved: Optional[Callable],
):
    """Finds an RGB image to combine with the given Alpha image then saves the combined image into the given directory.

    :param fp: Path to the Alpha image;
    :param destdir: Destination directory;
    :param on_processed: Callback `f()` for finished, `None` for ignore;
    :param on_file_queued: Callback `f()` invoked when a file was queued, `None` for ignore;
    :param on_file_saved: Callback `f(file_path_or_none_for_not_saved)`, `None` for ignore;
    :rtype: None;
    """
    try:
        combiner = AlphaRGBCombiner(fp)
        searcher = AlphaRGBSearcher(fp)
        result = combiner.combine_with(searcher.search_rgb())
        real_name = searcher.get_real_name()
        if real_name:
            SafeSaver.save_image(
                result,
                destdir,
                real_name,
                on_queued=on_file_queued,
                on_saved=on_file_saved,
            )
    except NoRGBImageMatchedError:
        pass
    except BaseException as arg:
        # Error feedback
        Logger.error(
            f'CombineRGBwithA: Error occurred while processing alpha image "{fp}": Exception{type(arg)} {arg}'
        )
        # raise(arg)
    if on_processed:
        on_processed()


########## Main-主程序 ##########
def main(rootdir: str, destdir: str, do_del: bool = False):
    """Combines the RGB images and the Alpha images in the given directory automatically according to their file names,
    then saves the combined images into another given directory.

    :param rootdir: Source directory;
    :param destdir: Destination directory;
    :param do_del: Whether to delete the existed destination directory first, `False` for default;
    :rtype: None;
    """
    print("\n正在解析路径...", s=1)
    Logger.info("CombineRGBwithA: Retrieving file paths...")
    rootdir = osp.normpath(osp.realpath(rootdir))
    destdir = osp.normpath(osp.realpath(destdir))
    flist = get_filelist(rootdir)
    flist = list(filter(is_image_file, flist))
    flist = list(
        filter(lambda x: AlphaRGBSearcher.calc_real_name(x) is not None, flist)
    )

    if do_del:
        print("\n正在清理...", s=1)
        rmdir(destdir)  # 慎用，会预先删除目的地目录的所有内容
    SafeSaver.get_instance().reset_counter()
    thread_ctrl = ThreadCtrl()
    ui = UICtrl()
    tr_processed = TaskReporter(2, len(flist))
    tr_file_saving = TaskReporter(1)
    tracker = TaskReporterTracker(tr_processed, tr_file_saving)

    ui.reset()
    ui.loop_start()
    for i in flist:
        # 递归处理各个文件(i是文件的路径名)
        ui.request(
            [
                "正在批量合并图片...",
                tracker.to_progress_bar_str(),
                f"当前目录：\t{osp.basename(osp.dirname(i))}",
                f"当前文件：\t{osp.basename(i)}",
                f"累计搜索：\t{tr_processed.to_progress_str()}",
                f"累计导出：\t{tr_file_saving.to_progress_str()}",
                f"剩余时间：\t{tracker.to_eta_str()}",
            ]
        )
        ###
        subdestdir = osp.dirname(i).strip(osp.sep).replace(rootdir, "").strip(osp.sep)
        thread_ctrl.run_subthread(
            image_resolve,
            (
                i,
                osp.join(destdir, subdestdir),
                tr_processed.report,
                tr_file_saving.update_demand,
                tr_file_saving.report,
            ),
            name=f"CBThread:{id(i)}",
        )

    ui.reset()
    ui.loop_stop()
    while (
        thread_ctrl.count_subthread()
        or not SafeSaver.get_instance().completed()
        or tracker.get_progress() < 1
    ):
        ui.request(
            [
                "正在批量合并图片...",
                tracker.to_progress_bar_str(),
                f"累计搜索：\t{tr_processed.to_progress_str()}",
                f"累计导出：\t{tr_file_saving.to_progress_str()}",
                f"剩余时间：\t{tracker.to_eta_str()}",
            ]
        )
        ui.refresh(post_delay=0.1)

    ui.reset()
    print("\n批量合并图片结束!", s=1)
    print(f"  累计导出 {tr_file_saving.get_done()} 张照片")
    print(f"  此项用时 {round(tracker.get_rt(), 1)} 秒")
