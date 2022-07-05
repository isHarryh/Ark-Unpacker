# -*- coding: utf-8 -*-
# Copyright (c) 2022, Harry Huang
# @ BSD 3-Clause License
import os, time
from src.osTool import *
from src import ResolveAB as AU_Rs
from src import CombineRGBwithA as AU_Cb
'''
ArkUnpacker主程序
v1.0
'''


if __name__ == '__main__':
    os.chdir('.')
    AU_Rs.main(["test"],"temp",dodel=True)
    os.chdir('.')
    AU_Cb.main(["temp\\test"],"temp2")
    exit()