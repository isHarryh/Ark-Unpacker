# -*- coding: utf-8 -*-
# Copyright (c) 2022-2023, Harry Huang
# @ BSD 3-Clause License
import os.path, re, shutil
try:
    from osTool import *
except:
    from .osTool import *
'''
从ArkUnpacker解包出来的文件中筛选出指定Spine模型（ArkModels仓库定制）
'''


def get_oper_id(str):
    str = str.lower()
    rst = re.findall(r'char_[0-9]+_', str)
    if len(rst): #char_000_
        return rst[0][5:-1]
    return ""

def get_oper_name(str):
    str = str.lower()
    rst = re.findall(r'char_[0-9]+_.+\.', str)
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
    if echo:
        print(f"From {src_com} and {src_unp}")
        print(f"  to {dest}")
    if dele:
        if echo:
            print("Deleteing...")
        Delete_File_Dir(dest)
    flist = []
    for j in [src_unp, src_com]:
        flist += get_filelist(j)
    n_all = len(flist)
    n_cur = 0
    n_pst = 0
    if echo:
        print("Filtering...")
    for i in flist:
        #遍历文件
        i = i.lower() #特殊处理：可能有些文件名没有规范地变成小写，需要强制小写以识别。
        n_cur += 1
        if os.path.isfile(i):
            #i是文件
            base = os.path.basename(i)
            id = get_oper_id(base)
            name = get_oper_name(base)
            if ("[alpha]" not in base) and ("build_" in base) and \
                (os.path.splitext(base)[1] in [".png", ".atlas", ".skel"]):
                #i是模型文件
                to = os.path.join(dest, f"{id}_{name}", base)
                mkdir(os.path.dirname(to))
                shutil.copyfile(i, to)
        elif os.path.isdir(i):
            #i是目录
            if os.path.exists(os.path.join(i,"BattleFront")):
                #特殊处理：有些干员只有一套Spine，可以同时用在战斗正面、背面和基建小人，
                #解包时只会解包出战斗正面的，这时需要手动复制一份作为它的基建小人模型。
                flag = False
                if flag:
                    continue
                for j in get_filelist(os.path.join(i,"BattleFront")):
                    #遍历原目录下BattleFront内的文件
                    if os.path.isfile(j):
                        #j是文件
                        base = os.path.basename(j)
                        id = get_oper_id(base)
                        name = get_oper_name(base)
                        if id == "" or name == "":
                            continue #可能不是干员模型文件
                        if contains_file(os.path.join(i,"BattleBack"),os.path.basename(j)):
                            continue #可能不是只有一套Spine的模型
                        if contains_file(i,"build_" + base):
                            continue #可能目录下本身就能找到基建小人
                        if os.path.splitext(base)[1] in [".atlas", ".skel"]:
                            #j是模型文件
                            to = os.path.join(dest, f"{id}_{name}", base)
                            mkdir(os.path.dirname(to))
                            shutil.copyfile(j, to)
                            tryimg = os.path.join(src_com, os.path.splitext(base)[0], os.path.splitext(base)[0] + ".png")
                            if os.path.isfile(tryimg):
                                to = os.path.join(dest, f"{id}_{name}", os.path.basename(tryimg))
                                mkdir(os.path.dirname(to))
                                shutil.copyfile(tryimg, to)
        if (n_cur/n_all*100)-n_pst >= 10:
            n_pst += 10
            print(f"  {n_pst}%")
    if echo:
        print(f"Completed.\n")

########## Main-主程序 ##########
if __name__ == '__main__':
    input()
