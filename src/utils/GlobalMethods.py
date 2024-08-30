# -*- coding: utf-8 -*-
# Copyright (c) 2022-2024, Harry Huang
# @ BSD 3-Clause License
import builtins
import importlib.util
import os
import os.path as osp
import pkgutil
import shutil
import traceback
import types


##### ↓ CLI related ↓ #####

os.system('')

def color(c:int=7, bg:int=0, s:int=0):
    """Gets a color controller string in interactive CLI.

    :param c: The color [0=black,1=red,2=green,3=yellow,4=blue,5=purple,6=cyan,7=white];
    :param bg: The background color [0=black,1=red,2=green,3=yellow,4=blue,5=purple,6=cyan,7=white];
    :param s: The style [0=default,1=bold,4=underlined,5=flashing,7=inverted,8=none];
    :returns: The color controller string.
    :rtype: str;
    """
    return f'\033[{s};3{c};4{bg}m'

def input(text:str="", c:int=7, bg:int=0, s:int=0, y:int=0):
    """Enhanced version of inputting in interactive CLI.

    :param text: The text to display;
    :param c: The color [0=black,1=red,2=green,3=yellow,4=blue,5=purple,6=cyan,7=white];
    :param bg: The background color [0=black,1=red,2=green,3=yellow,4=blue,5=purple,6=cyan,7=white];
    :param s: The style [0=default,1=bold,4=underlined,5=flashing,7=inverted,8=none];
    :param y: The y-position of the line to print or overwrite [0=append];
    :returns: The inputted text;
    :rtype: str;
    """
    ctrl = f"\033[K\033[{y};1H" if y > 0 else ""
    return builtins.input(f"{ctrl}{color(c, bg, s)}{text}\033[?25h")

def print(text:str="", c:int=7, bg:int=0, s:int=0, y:int=0):
    """Enhanced version of printing in interactive CLI.

    :param text: The text to print;
    :param c: The color [0=black,1=red,2=green,3=yellow,4=blue,5=purple,6=cyan,7=white];
    :param bg: The background color [0=black,1=red,2=green,3=yellow,4=blue,5=purple,6=cyan,7=white];
    :param s: The style [0=default,1=bold,4=underlined,5=flashing,7=inverted,8=none];
    :param y: The y-position of the line to print or overwrite [0=append];
    :rtype: None;
    """
    ctrl = f'\033[K\033[{y};{1}H' if y > 0 else ''
    builtins.print(f"\033[?25l{ctrl}{color(c, bg, s)}{text}")

def clear(use_ansi:bool=False):
    """Clears the CLI output.

    rtype: None;
    """
    if use_ansi:
        builtins.print('\033[2J')
    else:
        os.system('cls' if os.name == 'nt' else 'clear')

def title(text:str):
    """Sets the CLI window title. Windows only.

    :param text: The text of the title;
    rtype: None;
    """
    if os.name == 'nt':
        os.system(f'title {text}')

def stacktrace():
    return traceback.format_exc()

##### ↓ IO related ↓ #####

def mkdir(path:str):
    """Creates a directory.

    :param path: Path to the directory to be created;
    :rtype: None;
    """
    try:
        path = path.strip().strip('/\\')
        os.makedirs(path, exist_ok=True)
    except BaseException:
        pass

def rmdir(path:str):
    """Deletes a directory."""
    shutil.rmtree(path, ignore_errors=True)

def get_dir_size(path:str):
    """Gets the size of the given directory.

    :param path: Path to the directory;
    :returns: Size in bytes;
    :rtype: int;
    """
    size = 0
    lst = get_filelist(path)
    for i in lst:
        if osp.isfile(i):
            size += osp.getsize(i)
    return size

def get_filelist(path:str, max_depth=0):
    """Gets a list containing all the files in the given dir and its sub dirs.
    Note that If `max_depth` is specified to unlimited,
    `os.walk` (the most efficient way) will be used in this method instead of `os.listdir`.

    :param path: Path to the specified parent dir;
    :param max_depth: Max searching depth, `0` for unlimited;
    :returns: A list of paths;
    :rtype: list[str];
    """
    lst = []
    max_depth = int(max_depth)
    if max_depth <= 0:
        for root, _, files in os.walk(path):
            for file in files:
                lst.append(osp.join(root, file))
    else:
        for i in os.listdir(path):
            lst.append(osp.join(path, i))
    return lst

def get_dirlist(path:str, max_depth=0):
    """Gets a list containing all the sub dirs in the given dir.
    Note that If `max_depth` is specified to unlimited,
    `os.walk` (the most efficient way) will be used in this method instead of `os.listdir`.

    :param path: Path to the specified parent dir;
    :param max_depth: Max searching depth, `0` for unlimited;
    :returns: A list of paths;
    :rtype: list[str];
    """
    lst = []
    max_depth = int(max_depth)
    if max_depth <= 0:
        for root, dirs, _ in os.walk(path):
            for i in dirs:
                lst.append(osp.join(root, i))
    else:
        for i in os.listdir(path):
            i = osp.join(path, i)
            if osp.isdir(i):
                lst.append(i)
                if max_depth != 1:
                    lst.extend(get_filelist(i, max_depth - 1))
    return lst

_EXT_IMAGE = ('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff')

def is_image_file(path:str):
    """Returns `True` if the given file is an image judging from its path.

    :param path: Path;
    :returns: `True` if the file is an image;
    :rtype: bool;
    """
    return any(path.lower().endswith(ext) for ext in _EXT_IMAGE)

_EXT_KNOWN = ('.atlas', '.skel', '.wav', '.mp3', '.m4a', '.mp4', '.avi', '.mov', '.mkv', '.flv')

def is_known_asset_file(path:str):
    """Returns `True` if the given file is a known asset type from its path.
    Images, audios, videos and Spine are all known asset types.

    :param path: Path;
    :returns: `True` if the file is a known asset type;
    :rtype: bool;
    """
    return is_image_file(path) or any(path.lower().endswith(ext) for ext in _EXT_KNOWN)

def is_ab_file(path:str):
    """Returns `True` if the given file is an asset bundle judging from its path.

    :param path: Path;
    :returns: `True` if the file is an asset bundle;
    :rtype: bool;
    """
    return path.lower().endswith('.ab')

def is_binary_file(path:str, guess_encoding:str='UTF-8'):
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

##### ↓ Dynamic import related ↓ #####

def get_modules_from_package(package:types.ModuleType):
    walk_result = pkgutil.walk_packages(package.__path__, package.__name__ + '.')
    module_names = [name for _, name, is_pkg in walk_result if not is_pkg]
    return [importlib.import_module(name) for name in module_names]

def get_modules_from_package_name(package_name:str):
    package = importlib.import_module(package_name)
    return get_modules_from_package(package)
