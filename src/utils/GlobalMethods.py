# Copyright (c) 2022-2026, Harry Huang
# @ BSD 3-Clause License
from typing import List

import importlib
import glob
import os
import os.path as osp
import pkgutil
import re
import shutil
import traceback
import types

os.system("")


def stacktrace() -> str:
    return traceback.format_exc()


##### ↓ IO related ↓ #####


def rmdir(path: str):
    """Deletes a directory.

    :param path: Path to the directory;
    :rtype: None;
    """
    shutil.rmtree(path, ignore_errors=True)


_EXT_IMAGE = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".tiff"}

_EXT_KNOWN = {
    ".atlas",
    ".skel",
    ".wav",
    ".mp3",
    ".m4a",
    ".mp4",
    ".avi",
    ".mov",
    ".mkv",
    ".flv",
}

_EXT_AB = {".ab", ".bin"}


def is_image_file(path: str) -> bool:
    """Returns `True` if the given file is an image judging from its path.

    :param path: Path;
    :returns: `True` if the file is an image;
    :rtype: bool;
    """
    return any(path.lower().endswith(ext) for ext in _EXT_IMAGE)


def is_known_asset_file(path: str) -> bool:
    """Returns `True` if the given file is a known asset type from its judging from its name.
    Images, audios, videos and Spine are all known asset types.

    :param path: Path;
    :returns: `True` if the file is a known asset type;
    :rtype: bool;
    """
    return is_image_file(path) or any(path.lower().endswith(ext) for ext in _EXT_KNOWN)


def is_ab_file(path: str) -> bool:
    """Returns `True` if the given file is an asset bundle judging from its name.

    :param path: Path;
    :returns: `True` if the file is an asset bundle;
    :rtype: bool;
    """
    return any(path.lower().endswith(ext) for ext in _EXT_AB)


def collect_ab_files(src: str) -> List[str]:
    """Collects all the AB files from the given file or directory recursively.

    :param src: Source file or directory;
    :returns: A list of AB file paths;
    :rtype: List[str];
    """
    flist = [src] if osp.isfile(src) else []
    if osp.isdir(src):
        for i in glob.iglob(osp.join(glob.escape(src), "**", "*"), recursive=True):
            if osp.isfile(i) and is_ab_file(i):
                flist.append(i)
    return flist


def calc_destdir(abfile: str, src: str, destdir: str, separate: bool) -> str:
    """Calculates the destination directory of the given AB file.

    :param abfile: Path to the AB file;
    :param src: Source file or directory;
    :param destdir: Destination directory;
    :param separate: Whether to group the files by their source AB file path;
    :returns: The destination directory path;
    :rtype: str;
    """
    return (
        destdir
        if osp.samefile(abfile, src)
        else (
            osp.join(
                destdir,
                osp.relpath(osp.dirname(abfile), src),
                osp.splitext(osp.basename(abfile))[0],
            )
            if separate
            else osp.join(destdir, osp.relpath(osp.dirname(abfile), src))
        )
    )


def is_usm_file(path: str) -> bool:
    """Returns `True` if the given file is a Criware USM file judging from its name.

    :param path: Path;
    :returns: `True` if the file is a USM video file;
    :rtype: bool;
    """
    return path.lower().endswith(".usm")


def is_binary_file(path: str, guess_encoding: str = "UTF-8") -> bool:
    """Returns `True` if the given file is a binary file rather than text file.

    :param path: Path;
    :param guess_encoding: The specified charset to test the file;
    :returns: `True` if the file is a binary file;
    :rtype: bool;
    """
    try:
        with open(path, encoding=guess_encoding) as f:
            f.read()
        return False
    except UnicodeError:
        return True


def try_shorten_path(path: str) -> str:
    """Tries to shorten the path.

    :param path: Path;
    :returns: A shortened path, or the original path if the path cannot be shortened.
    :rtype: bool;
    """
    matched = re.search(r"(\w+)\s*Game[/\\](\w+)\s*Data[/\\]StreamingAssets([/\\]AB)?([/\\]Windows)?", path)
    if matched:
        game_name = matched.group(1)
        return path.replace(matched.group(), f"{game_name} Unpacked")
    return path


##### ↓ Dynamic import related ↓ #####


def get_modules_from_package(package: types.ModuleType) -> List[types.ModuleType]:
    """Gets all the modules from the given package.

    :param package: The package to get modules from;
    :returns: A list of modules;
    :rtype: List[types.ModuleType];
    """
    walk_result = pkgutil.walk_packages(package.__path__, package.__name__ + ".")
    module_names = [name for _, name, is_pkg in walk_result if not is_pkg]
    return [importlib.import_module(name) for name in module_names]


def get_modules_from_package_name(package_name: str) -> List[types.ModuleType]:
    """Gets all the modules from the package with the given name.

    :param package_name: The name of the package to get modules from;
    :returns: A list of modules;
    :rtype: List[types.ModuleType];
    """
    package = importlib.import_module(package_name)
    return get_modules_from_package(package)
