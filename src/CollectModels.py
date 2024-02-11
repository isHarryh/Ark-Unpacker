# -*- coding: utf-8 -*-
# Copyright (c) 2022-2023, Harry Huang
# @ BSD 3-Clause License
import os.path, re
try:
    from .utils._ImportAllUtils import *
except:
    from utils._ImportAllUtils import*
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

def get_dyn_illust_common_name(str):
    return "" if len(get_oper_common_name(str)) == 0 else 'dyn_illust_' + get_oper_common_name(str)

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
    print("\n正在解析目录...", s=1)
    Logger.info("CollectModels: Reading directories...")
    ospath = os.path
    if len(srcdirs) != len(destdirs):
        print("参数错误", c=3)
        return
    
    flist = [] #[(subsub-srcdir, sub-srcdir, destdir),...]
    for src, dest in zip(srcdirs, destdirs):
        print("\t正在读取目录 "+src)
        for dir1 in get_filelist(src, only_dirs=True, max_depth=1):
            for dir2 in get_filelist(dir1, only_dirs=True, max_depth=1):
                flist.append((dir2, dir1, dest))
    
    cont_f = 0 #已分拣模型计数
    cont_p = 0 #进度百分比计数
    if dodel:
        print("\n正在清理...", s=1)
        for i in destdirs:
            print("\t正在清理目录 "+i)
            rmdir(i) #慎用，会预先删除目的地目录的所有内容
    TR = TimeRecorder(len(flist))

    os.system('cls')
    for dir2, dir1, dest in flist:
        #递归处理各个目录(i是元组(sub-srcdir, destdir))
        print(f'正在分拣模型...', y=1)
        print(f'|{progress_bar(cont_p, 25)}| {color(2, 0, 1)}{round(cont_p*100, 1)}%', y=2)
        print(f'当前目录：\t{dir2}', y=3)
        print(f'累计分拣：\t{cont_f}', y=4)
        print(f'剩余时间：\t{round(TR.get_remaining_time() / 60, 1)}min', y=5)
        ###
        try:
            dir1_base = ospath.basename(dir1)
            dir2_base = ospath.basename(dir2)
            models = get_filelist(dir2, only_dirs=True, max_depth=1)
            if (dir2_base in ['Building']) and 'char_' in dir1_base:
                for m in models:
                    newname = get_oper_common_name(ospath.basename(m)+'.')
                    mvfile(m, ospath.join(dest, newname))
                    cont_f += 1
            elif 'enemy_' in dir1_base:
                for m in models:
                    newname = get_enemy_common_name(ospath.basename(m)+'.')
                    mvfile(m, ospath.join(dest, newname))
                    cont_f += 1
            elif (dir2_base in ['DynIllust']) and 'char_' in dir1_base:
                for m in models:
                    m_base = ospath.basename(m)
                    if '_start' not in m_base.lower() and 'dyn_illust_' in m_base.lower():
                        newname = get_dyn_illust_common_name(m_base+'.')
                        mvfile(m, ospath.join(dest, newname))
                        cont_f += 1
        except BaseException as arg:
            Logger.error(f'CollectModels: Error occurred while handleing "{dir2}": Exception{type(arg)} {arg}')
        TR.update()
        cont_p = TR.get_progress()

    os.system('cls')
    print(f'\n分拣模型结束!', s=1)
    print(f'  累计分拣 {cont_f} 套模型')
    print(f'  此项用时 {round(TR.get_consumed_time())} 秒')
    time.sleep(2)
