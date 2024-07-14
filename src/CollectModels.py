# -*- coding: utf-8 -*-
# Copyright (c) 2022-2024, Harry Huang
# @ BSD 3-Clause License
import os.path, re, shutil
from .utils import*


def collect_models(upkdir:str, destdir:str, dodel:bool, on_finished:staticmethod, on_collected:staticmethod):
    """
    
    """
    error_occurred = False
    for model_type_dir in get_dirlist(upkdir, max_depth=1):
        model_type:str = os.path.basename(model_type_dir) # Sub dir of one model type
        for model_dir in get_dirlist(model_type_dir, max_depth=1):
            model:str = os.path.basename(model_dir) # Sub dir of one determined model
            if not model.islower():
                # To solve model typo caused by Arknights side
                model = model.lower()
                Logger.warn(f"CollectModels: \"{model_dir}\" may has a typo name")
            try:
                newname = None
                if model_type.startswith('Building') and re.match(r'(build_)?char_', model):
                    newname = re.match(r'(build_)?char_(\d+_[0-9a-zA-Z]+(_[0-9a-zA-Z#]+)?)', model).group(2)
                elif model_type.startswith('Battle') and re.match(r'enemy_', model):
                    newname = re.match(r'enemy_(\d+_[0-9a-zA-Z]+(_\d+)?)', model).group(1)
                elif model_type.startswith('DynIllust') and re.match(r'dyn_illust_char_', model):
                    newname = "dyn_illust_" + re.match(r'dyn_illust_char_(\d+_[0-9a-zA-Z]+(_[0-9a-zA-Z#]+)?)', model).group(1)
                if newname:
                    # Move to 
                    dest = os.path.join(destdir, newname)
                    Logger.debug(f"CollectModels: \"{model_dir}\" -> \"{dest}\"")
                    shutil.copytree(model_dir, dest, dirs_exist_ok=True)
                    rmdir(model_dir)
                    if on_collected:
                        on_collected()
                else:
                    # Not matched any rules
                    pass 
            except Exception as arg:
                error_occurred = True
                Logger.error(f"CollectModels: Error occurred while handling \"{model_dir}\": Exception{type(arg)} {arg}")
    if dodel and not error_occurred:
        rmdir(upkdir)
    if on_finished:
        on_finished()

########## Main-主程序 ##########
def main(srcdirs:"list[str]", destdirs:"list[str]"):
    """Collects the Spine models from the source directories to the destination directories accordingly.
    The structure of the source directory is shown below.

    ```
    ├─source_dir
    │  ├─unpacked_dir
    │  │  ├─model_type_dir
    │  │  │  ├─model_dir
    │  │  │  │  ├─files
    ```

    :param srcdirs: Source directories list;
    :param destdirs: Destination directories list;
    :rtype: None;
    """
    print("\n正在解析目录...", s=1)
    Logger.info("CollectModels: Reading directories...")
    if len(srcdirs) != len(destdirs):
        Logger.error("CollectModels: Arguments error")
        print("参数错误", c=3)
        return
    
    flist = [] # [(upkdir, destdir), ...]
    for srcdir, destdir in zip(srcdirs, destdirs):
        print(f"\t正在读取目录 {srcdir}")
        for upkdir in get_dirlist(srcdir, max_depth=1):
            flist.append((upkdir, destdir))
    
    TC = ThreadCtrl(PerformanceLevel.get_thread_limit(Config.get('performance_level')))
    collected = Counter()
    UI = UICtrl(0.5)
    TR = TimeRecorder()
    TR.update_dest(1, len(flist))
    on_finished = lambda: TR.done_once(1)
    on_collected = lambda: collected.update()

    UI.reset()
    UI.loop_start()
    for upkdir, destdir in flist:
        #(i stands for a source dir's path)
        TR_p = TR.get_progress()
        TR_r = TR.get_remaining_time()
        UI.request([
            f'正在分拣模型...',
            f'|{progress_bar(TR_p, 25)}| {color(2, 0, 1)}{round(TR_p*100, 1)}%',
            f'当前搜索：\t{os.path.basename(upkdir)}',
            f'累计分拣：\t{collected.now()}',
            f'剩余时间：\t{f"{round(TR_r / 60, 1)}min" if TR_r > 0 else "计算中"}',
        ])
        ###
        TC.run_subthread(collect_models, (upkdir, destdir, True, on_finished, on_collected), \
            name=f"CmThread:{id(upkdir)}")

    UI.reset()
    UI.loop_stop()
    while TC.count_subthread() or not SafeSaver.get_instance().completed() or TR.get_progress() < 1:
        TR_p = TR.get_progress()
        TR_r = TR.get_remaining_time()
        UI.request([
            f'正在分拣模型...',
            f'|{progress_bar(TR_p, 25)}| {color(2, 0, 1)}{round(TR_p*100, 1)}%',
            f'累计分拣：\t{collected.now()}',
            f'剩余时间：\t{f"{round(TR_r / 60, 1)}min" if TR_r > 0 else "计算中"}',
        ])
        UI.refresh(post_delay=0.2)

    UI.loop_stop()
    UI.reset()
    print(f'\n分拣模型结束!', s=1)
    print(f'  累计分拣 {collected.now()} 套模型')
    print(f'  此项用时 {round(TR.get_consumed_time())} 秒')
    time.sleep(2)
