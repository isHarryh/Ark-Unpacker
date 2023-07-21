# -*- coding: utf-8 -*-
# Copyright (c) 2022-2023, Harry Huang
# @ BSD 3-Clause License
import os, builtins, shutil
'''
GlobalMethods
全局方法
'''

##### ↓ CLI related ↓ #####

os.system('')

def color(c:int=7, bg:int=0, s:int=0):
    '''
    ## Get a color controller string in CLI
    #### 获得命令行着色字符串
    :param c:  The color [0=balck,1=red,2=green,3=yellow,4=blue,5=purple,6=cyan,7=white];
    :param bg: The background color [0=balck,1=red,2=green,3=yellow,4=blue,5=purple,6=cyan,7=white];
    :param s:  The style [0=default,1=bold,4=underlined,5=flashing,7=inverted,8=none];
    :returns:  (str);
    '''
    return f'\033[{s};3{c};4{bg}m'

def input(text:str="", c:int=7, bg:int=0, s:int=0, y:int=0):
    '''
    ## Enhanced version of inputting in CLI
    #### 增强版的命令行界面输入函数
    :param text: The text to print;
    :param c:    The color [0=balck,1=red,2=green,3=yellow,4=blue,5=purple,6=cyan,7=white];
    :param bg:   The background color [0=balck,1=red,2=green,3=yellow,4=blue,5=purple,6=cyan,7=white];
    :param s:    The style [0=default,1=bold,4=underlined,5=flashing,7=inverted,8=none];
    :param y:    The y-position of the line to print or overwrite [0=append];
    :returns:    (str);
    '''
    ctrl = f"\033[K\033[{y};1H" if y > 0 else ""
    return builtins.input(f"{ctrl}{color(c, bg, s)}{text}\033[?25h")

def print(text:str="", c:int=7, bg:int=0, s:int=0, y:int=0):
    '''
    ## Enhanced version of printing in CLI
    #### 增强版的命令行界面打印函数
    :param text: The text to print;
    :param c:    The color [0=balck,1=red,2=green,3=yellow,4=blue,5=purple,6=cyan,7=white];
    :param bg:   The background color [0=balck,1=red,2=green,3=yellow,4=blue,5=purple,6=cyan,7=white];
    :param s:    The style [0=default,1=bold,4=underlined,5=flashing,7=inverted,8=none];
    :param y:    The y-position of the line to print or overwrite [0=append];
    :returns:    (none);
    '''
    ctrl = f'\033[K\033[{y};{1}H' if y > 0 else ''
    builtins.print(f"\033[?25l{ctrl}{color(c, bg, s)}{text}")

def progress_bar(progress:float, length:int):
    '''
    ## Get a progress bar string
    #### 获得代表的进度条字符串
    '''
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

def mkdir(path:str, echo:bool=False):
    '''
    ## Create a Dir
    #### 创建一个文件夹
    :param path: Path of the new dir;
    :param echo: Whether to echo info;
    :returns:    (bool) Execution result;
    '''
    path = path.strip().strip('/').rstrip('\\')
    if not os.path.exists(path):
        try:
            os.makedirs(path)
            if echo:
                if len(path) > 24:
                    print(f'  目录已创建 ...{path[-20:]}')
                else:
                    print(f'  目录已创建 {path}')
            return True
        except:
            #错误
            if echo:
                print("  目录创建失败", c=3)
            return False
    else:
        #目录已存在
        return False

def mvfile(path_from:str, path_to:str):
    '''
    ## Move a File
    #### 移动一个文件
    :param path_from: Path from;
    :param path_to:   Path to;
    :returns:         (none);
    '''
    mkdir(os.path.dirname(path_to))
    shutil.move(path_from, path_to)

def rmdir(path:str):
    '''
    ## Delete a Dir
    #### 删除一个文件夹
    :param path: Path of the dir;
    :returns:    (none);
    '''
    shutil.rmtree(path, ignore_errors=True)

def get_dir_size(path:str):
    '''
    ## Get the size of a Dir
    #### 获取一个目录的大小
    :param path: Path of the dir;
    :returns:    (int) Size in Byte;
    '''
    size = 0
    lst = os.listdir(path)
    for el in lst:
        new = path+'\\'+el
        if os.path.isfile(new):
            size += os.path.getsize(new)
        else:
            size += get_dir_size(new)
    return size

def get_filelist(path:str, max_depth=0, only_dirs=False):
    '''
    ## Get a list containing all the sub dirs (and files) in the given dir
    #### 获取指定目录中的所有子文件夹（和文件）的列表
    :param path:      Path of the specified parent dir;
    :param max_depth: Max searching depth, 0 for unlimited;
    :param only_dirs: Whether to exclude files;
    :returns:         (list) A list of file paths;
    '''
    max_depth = int(max_depth)
    lst = []
    for i in os.listdir(path):
        i = os.path.join(path, i)
        if os.path.isdir(i):
            lst.append(i)
            if max_depth != 1:
                lst.extend(get_filelist(i, max_depth - 1))
        elif not only_dirs:
            lst.append(i)
    return lst

def get_path_authority(path:str):
    '''
    ## Judge the accessibility of the given path 
    #### 判断路径可访问性
    :param path: Path;
    :returns:    (bool) True=Available, False=Unavailable;
    '''
    if os.path.exists(path)\
        and os.access(path,os.X_OK|os.W_OK|os.R_OK):
        return True
    else:
        return False

##### ↓ Stat related ↓ #####

def mean(lst:list):
    '''
    ## Get the mean value of an array
    #### 返回数组平均值
    :param lst: List of values;
    :returns:   (float) Mean value;
    '''
    if len(lst) == 0:
        return float(0)
    s = 0
    for i in lst:
        s += i
    return float(s / len(lst))

def trimmean(lst:list, percent:float):
    '''
    ## Trim extreme values from the both ends of the list and get the mean
    #### 去除数组两极的极端值，返回数组平均值
    :param lst:     List of values;
    :param percent: (float) Ratio of extreme values of each end;
    '''
    if len(lst) == 0:
        return float(0)
    if percent < 0 or percent > 1:
        return float(0)
    newlst = lst[:]
    newlst.sort()
    blocked = int(len(lst) * percent)
    newlst = newlst[blocked:-blocked]
    if len(newlst) == 0:
        return mean(lst)
    else:
        return mean(newlst)
