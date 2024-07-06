# -*- coding: utf-8 -*-
# Copyright (c) 2022-2024, Harry Huang
# @ BSD 3-Clause License
import os, builtins, shutil


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

def progress_bar(progress:float, length:int):
    """Gets a progress bar string."""
    try:
        add_chars = (' ', '▏', '▎', '▍', '▌', '▋', '▊', '▉', '█')
        max_idx = len(add_chars) - 1
        bar = ''
        unit = 1 / length
        for i in range(length):
            ratio = (progress - i * unit) / unit
            bar += add_chars[max(0, min(max_idx, round(ratio * max_idx)))]
        return bar
    except:
        return ''

##### ↓ IO related ↓ #####

def mkdir(path:str):
    """Creates a directory.

    :param path: Path to the directory to be created;
    :returns: Execution result;
    :rtype: bool;
    """
    path = path.strip().strip('/').rstrip('\\')
    try:
        os.makedirs(path, exist_ok=True)
        return True
    except:
        return False

def mvfile(path_from:str, path_to:str):
    """Moves a file."""
    mkdir(os.path.dirname(path_to))
    shutil.move(path_from, path_to)

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
        if os.path.isfile(i):
            size += os.path.getsize(i)
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
                lst.append(os.path.join(root, file))
    else:
        for i in os.listdir(path):
            lst.append(os.path.join(path, i))
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
            for dir in dirs:
                lst.append(os.path.join(root, dir))
    else:
        for i in os.listdir(path):
            i = os.path.join(path, i)
            if os.path.isdir(i):
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

##### ↓ Stat related ↓ #####

def mean(lst:list):
    """Gets the mean value (the average value) of an array.

    :param lst: List of values;
    :returns: Mean value;
    :rtype: float;
    """
    if len(lst) == 0:
        return float(0)
    s = 0
    for i in lst:
        s += i
    return float(s / len(lst))

def trimmean(lst:list, percent:float):
    """Trims extreme values from the both ends of the list and gets the mean.

    :param lst: List of values;
    :param percent: Ratio of extreme values of each end;
    :returns: Mean value;
    :rtype: float;
    """
    if len(lst) == 0 or percent < 0 or percent > 1:
        return float(0)
    newlst = lst[:]
    newlst.sort()
    blocked = int(len(lst) * percent)
    newlst = newlst[blocked:-blocked]
    if len(newlst) == 0:
        return mean(lst)
    else:
        return mean(newlst)
