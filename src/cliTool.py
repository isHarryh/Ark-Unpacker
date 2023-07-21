# -*- coding: utf-8 -*-
# Copyright (c) 2022-2023, Harry Huang
# @ BSD 3-Clause License
import os, builtins
'''
控制台多颜色输出函数
'''

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
