# -*- coding: utf-8 -*-
# Copyright (c) 2022, Harry Huang
# @ BSD 3-Clause License
'''
控制台多颜色输出函数
'''

def color(mode:int=0, front:int=0, back:int=0):
    '''
    ## Get a Colored Cmd-Output Prefix
    #### 获得一个用于命令行着色的前缀。
    #### e.g. print(color(0,1,0)+"Your Words.")
    :param mode:  Display Method [0=default,1=bold,4=underlined,5=flashing,7=inverted,8=none];
    :param front: Foreground Color (0~7);
    :param back:  Background Color (0~7);
    :returns:     (str) The Prefix;
    '''
    return str('\033['+str(mode)+';3'+str(front)+';4'+str(back)+'m')