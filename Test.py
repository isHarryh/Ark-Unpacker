# -*- coding: utf-8 -*-
# Copyright (c) 2022-2023, Harry Huang
# @ BSD 3-Clause License
import os, sys, json, shutil
from src import ResolveAB
from src import CombineRGBwithA
from src import ResolveFBO
from src.utils.AnalyUtils import TestRT
from src.utils.GlobalMethods import print, stacktrace

def __count_files(path):
    count = 0
    for _, _, files in os.walk(path):
        count += len(files)
    return count

if __name__ == '__main__':
    for i in range(int(sys.argv[1]) if len(sys.argv) > 1 else 1):
        try:
            print(f"[#{i}] Preparing...", c=0, bg=6)
            DIR_UPK = 'test/upk'
            DIR_CMB = 'test/cmb'
            DIR_FBO = 'test/fbo'
            shutil.rmtree(DIR_UPK, ignore_errors=True)
            shutil.rmtree(DIR_CMB, ignore_errors=True)
            shutil.rmtree(DIR_FBO, ignore_errors=True)

            print(f"[#{i}] Testing...", c=0, bg=6)
            with TestRT('unit_1'):
                ResolveAB.main('test/res',
                            DIR_UPK,
                            dodel=False,
                            doimg=True,
                            dotxt=True,
                            doaud=True,
                            dospine=False
                            )
            with TestRT('unit_2'):
                CombineRGBwithA.main(DIR_UPK,
                                    DIR_CMB,
                                    dodel=False
                                    )
            with TestRT('unit_3'):
                ResolveFBO.main(DIR_UPK,
                                DIR_FBO,
                                dodel=False
                                )
            
            print(f"[#{i}] Analysing...", c=0, bg=6)
            if __count_files(DIR_UPK) != 1262:
                raise AssertionError("Unpacked files count mismatch")
            if __count_files(DIR_CMB) != 139:
                raise AssertionError("Combined images count mismatch")
            if __count_files(DIR_FBO) != 2:
                raise AssertionError("Decoded FBO count mismatch")
            
            print(f"[#{i}] Test success!", c=0, bg=2)
        except BaseException as arg:
            print(f"[#{i}] Test failed because an error occurred!", c=7, bg=1)
            print(stacktrace(), c=3)
    json.dump(TestRT.get_avg_time_all(), open('test/rt.json', 'w', encoding='UTF-8'), indent=4)
