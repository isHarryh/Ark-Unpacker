# -*- coding: utf-8 -*-
# Copyright (c) 2022-2023, Harry Huang
# @ BSD 3-Clause License
import os.path, re, shutil
try:
    from osTool import *
    from communalTool import *
except:
    from .osTool import *
    from .communalTool import *
'''
从ArkUnpacker解包出来的文件中筛选出指定Spine模型（ArkModels仓库定制）
'''


def get_oper_id(str):
    rst = re.findall(r'char_[0-9]+_', str.lower())
    if len(rst): #char_000_
        return rst[0][5:-1]
    return ""

def get_enemy_id(str):
    rst = re.findall(r'enemy_[0-9]+_', str.lower())
    if len(rst): #enemy_000_
        return rst[0][6:-1]
    return ""

def get_oper_name(str):
    rst = re.findall(r'char_[0-9]+_.+\.', str.lower())
    if len(rst): #char_000_xxx(_xx).
        rst = re.findall(r'_.+\.', rst[0]) 
        if len(rst): #_000_xxx(_xx).
            if len(re.findall(r'_.+_#', rst[0])):
                rst = re.findall(r'_.+_#', rst[0][1:])
                if len(rst):
                    return rst[0][1:-2]
            elif len(re.findall(r'_.+\.', rst[0])):
                rst = re.findall(r'_.+\.', rst[0][1:])
                if len(rst):
                    return rst[0][1:-1]
    return ""

def get_enemy_name(str):
    rst = re.findall(r'enemy_[0-9]+_.+\.', str.lower())
    if len(rst): #enemy_000_xxx(_xx).
        rst = re.findall(r'_.+\.', rst[0]) 
        if len(rst): #_000_xxx(_xx).
            if len(re.findall(r'_.+_#', rst[0])):
                rst = re.findall(r'_.+_#', rst[0][1:])
                if len(rst):
                    return rst[0][1:-2]
            elif len(re.findall(r'_.+\.', rst[0])):
                rst = re.findall(r'_.+\.', rst[0][1:])
                if len(rst):
                    return rst[0][1:-1]
    return ""

def contains_file(dir, filename):
    if os.path.isdir(dir):
        for j in get_filelist(dir):
            if os.path.basename(j) == filename and os.path.isfile(j):
                return True
    return False

def sort_oper_build(dest, src_com, src_unp, dele=True, echo=True):
    '''
    #### 筛选基建小人Spine文件
    :param dest: 保存目的地;
    :param src_com: Combined文件夹;
    :param src_unp: Unpacked文件夹;
    :param dele: 是否预先删除目的地文件夹;
    :param echo: 是否回显进度;
    :returns: (none);
    '''
    Logger.info(f"CollectModels: From \"{src_com}\" and \"{src_unp}\" to \"{dest}\"")
    if echo:
        print(f"From {src_com} and {src_unp}")
        print(f"  to {dest}")
    if dele:
        if echo:
            print("Deleteing...")
        Delete_File_Dir(dest)
    flist = []
    for i in (src_com, src_unp):
        flist.extend(get_filelist(i, only_dirs=True, max_depth=1))
    n_all = len(flist)
    n_cur, n_pst = 0, 0

    Logger.info("CollectModels: Filtering...")
    if echo:
        print("Filtering...")
    for i in flist:
        #遍历文件
        i = i.lower() #特殊处理：可能有些文件名没有规范地变成小写，需要强制小写以识别。
        n_cur += 1
        if os.path.isdir(i):
            #i是目录
            if os.path.exists(os.path.join(i, 'Building')):
                #该目录下包含Building文件夹，则直接复制Building中的文件
                for j in get_filelist(os.path.join(i, 'Building'), max_depth=1):
                    if os.path.isfile(j):
                        #j是原目录下Building中的文件
                        base = os.path.basename(j)
                        id = get_oper_id(base)
                        name = get_oper_name(base)
                        if ('[alpha]' not in base) and \
                            (os.path.splitext(base)[1] in ['.png', '.atlas', '.skel']):
                            j2 = os.path.join(dest, f"{id}_{name}", os.path.basename(j))
                            if not os.path.exists(j2):
                                mkdir(os.path.dirname(j2))
                                shutil.copyfile(j, j2)
        if (n_cur / n_all*100) - n_pst >= 10:
            n_pst += 10
            print(f"  {n_pst}%")
    Logger.info("CollectModels: Completed.")
    if echo:
        print(f"Completed.\n")

def sort_enemy(dest, src_com, src_unp, dele=True, echo=True):
    '''
    #### 筛选敌方小人Spine文件
    :param dest: 保存目的地;
    :param src_com: Combined文件夹;
    :param src_unp: Unpacked文件夹;
    :param dele: 是否预先删除目的地文件夹;
    :param echo: 是否回显进度;
    :returns: (none);
    '''
    Logger.info(f"CollectModels: From \"{src_com}\" and \"{src_unp}\" to \"{dest}\"")
    if echo:
        print(f"From {src_com} and {src_unp}")
        print(f"  to {dest}")
    if dele:
        if echo:
            print("Deleteing...")
        Delete_File_Dir(dest)
    flist = []
    for i in (src_com, src_unp):
        flist.extend(get_filelist(i))
    n_all = len(flist)
    n_cur, n_pst = 0, 0

    Logger.info("CollectModels: Filtering...")
    if echo:
        print("Filtering...")
    for i in flist:
        #遍历文件
        i = i.lower() #特殊处理：可能有些文件名没有规范地变成小写，需要强制小写以识别。
        n_cur += 1
        if os.path.isfile(i):
            #i是文件
            base = os.path.basename(i)
            id = get_enemy_id(base)
            name = get_enemy_name(base)
            if ('[alpha]' not in base) and ('enemy_' in base) and \
                (os.path.splitext(base)[1] in ['.png', '.atlas', '.skel']):
                #i是模型文件
                to = os.path.join(dest, f"{id}_{name}", base)
                if not os.path.exists(to):
                    mkdir(os.path.dirname(to))
                    shutil.copyfile(i, to)
        if (n_cur/n_all*100)-n_pst >= 10:
            n_pst += 10
            print(f"  {n_pst}%")
    Logger.info("CollectModels: Completed.")
    if echo:
        print(f"Completed.\n")

########## Main-主程序 ##########
if __name__ == '__main__':
    input()
