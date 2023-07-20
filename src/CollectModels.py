# -*- coding: utf-8 -*-
# Copyright (c) 2022-2023, Harry Huang
# @ BSD 3-Clause License
import os.path, re
try:
    from osTool import *
    from colorTool import *
    from communalTool import *
except:
    from .osTool import *
    from .colorTool import *
    from .communalTool import *
'''
从ArkUnpacker解包出来的文件中筛选出指定Spine模型（ArkModels仓库定制）
'''

def get_oper_common_name(str):
    def get_oper_id(str):
        rst = re.findall(r'char_[0-9]+_', str.lower())
        if len(rst): #char_000_
            return rst[0][5:-1]
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
    id, name = get_oper_id(str), get_oper_name(str)
    return "" if len(id) * len(name) == 0 else f"{id}_{name}"

def get_enemy_common_name(str):
    def get_enemy_id(str):
        rst = re.findall(r'enemy_[0-9]+_', str.lower())
        if len(rst): #enemy_000_
            return rst[0][6:-1]
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
    id, name = get_enemy_id(str), get_enemy_name(str)
    return "" if len(id) * len(name) == 0 else f"{id}_{name}"

def contains_file(dir, filename):
    if os.path.isdir(dir):
        for j in get_filelist(dir):
            if os.path.basename(j) == filename and os.path.isfile(j):
                return True
    return False

########## Main-主程序 ##########
def main(srcdirs:"list[str]", destdirs:"list[str]", dodel:bool=False):
    '''
    #### 分别从每个来源文件夹分拣模型到目标文件夹
    :param srcdirs:    来源文件夹的路径列表;
    :param destdirs:   目标文件夹的路径列表;
    :param dodel:      预先删除目标文件夹的所有文件，默认False;
    :returns: (None);
    '''
    print(color(7,0,1)+"\n正在解析目录..."+color(7))
    Logger.info("CollectModels: Reading directories...")
    ospath = os.path
    if len(srcdirs) != len(destdirs):
        print(color(1)+"参数错误")
        return
    
    flist = [] #[(subsub-srcdir, sub-srcdir, destdir),...]
    for src, dest in zip(srcdirs, destdirs):
        print(color(7)+"\t正在读取目录 "+src)
        for dir1 in get_filelist(src, only_dirs=True, max_depth=1):
            for dir2 in get_filelist(dir1, only_dirs=True, max_depth=1):
                flist.append((dir2, dir1, dest))
    
    cont_f = 0 #已分拣模型计数
    cont_p = 0 #进度百分比计数
    if dodel:
        print(color(7,0,1)+"\n正在清理..."+color(7))
        for i in destdirs:
            rmdir(i) #慎用，会预先删除目的地目录的所有内容
    TR = TimeRecorder(len(flist))

    for dir2, dir1, dest in flist:
        #递归处理各个目录(i是元组(sub-srcdir, destdir))
        echo = f'''{color(7)}正在分拣模型...
|{"■"*int(cont_p//5)}{"□"*int(20-cont_p//5)}| {color(2)}{cont_p}%{color(7)}
当前目录：\t{dir2}
累计分拣：\t{cont_f}
剩余时间：\t{round(TR.getRemainingTime(),1)}min
'''
        os.system('cls')
        print(echo)
        ###
        dir1_base = ospath.basename(dir1)
        dir2_base = ospath.basename(dir2)
        models = get_filelist(dir2, only_dirs=True, max_depth=1)
        if (dir2_base == 'Building' and 'char_' in dir1_base):
            for m in models:
                newname = get_oper_common_name(ospath.basename(m)+'.')
                mvfile(m, ospath.join(dest, newname))
                cont_f += 1
        elif 'enemy_' in dir1_base:
            for m in models:
                newname = get_enemy_common_name(ospath.basename(m)+'.')
                mvfile(m, ospath.join(dest, newname))
                cont_f += 1
        TR.update()
        cont_p = TR.getProgress()

    os.system('cls')
    print(f'{color(7,0,1)}\n分拣模型结束!')
    print(f'  累计分拣 {cont_f} 套模型')
    print(f'  此项用时 {round(TR.getTotalTime())} 秒{color(7)}')
    time.sleep(2)
