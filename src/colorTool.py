# -*- coding: utf-8 -*-
# Copyright (c) 2022, Harry Huang
# @ BSD 3-Clause License
import os
'''
控制台多颜色输出函数
'''

os.system('')
def color(front:int=7, back:int=0, mode:int=0):
    '''
    ## Get a Colored Cmd-Output Prefix
    #### 获得一个用于命令行着色的前缀。
    e.g. print(color(0,1,0)+"Your Words.")
    tip: [0=balck,1=red,2=green,3=yellow,4=blue,5=purple,6=cyan,7=white]
    :param front: Foreground Color (0~7);
    :param back:  Background Color (0~7);
    :param mode:  Display Method [0=default,1=bold,4=underlined,5=flashing,7=inverted,8=none];
    :returns:     (str) The Prefix;
    '''
    return f'\033[{mode};3{front};4{back}m'