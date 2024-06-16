# -*- coding: utf-8 -*-
# Copyright (c) 2022-2023, Harry Huang
# @ BSD 3-Clause License
import os, csv, time, shutil
from src import ResolveAB
from src import CombineRGBwithA

def __count_files(path):
    count = 0
    for _, _, files in os.walk(path):
        count += len(files)
    return count

def test_unit_1():
    try:
        t = time.time()
        ResolveAB.main('test/res',
                    'test/upk',
                    dodel=False,
                    doimg=True,
                    dotxt=True,
                    doaud=True,
                    dospine=True
                    )
        return time.time() - t
    except BaseException:
        return -1

def test_unit_2():
    try:
        t = time.time()
        CombineRGBwithA.main('test/upk',
                            'test/cmb',
                            dodel=False
                            )
        return time.time() - t
    except BaseException:
        return -1

if __name__ == '__main__':
    print("Preparing...")
    shutil.rmtree('test/upk', ignore_errors=True)
    shutil.rmtree('test/cmb', ignore_errors=True)
    print("Testing...")
    result = [["Unit1", test_unit_1()],
            ["Unit2", test_unit_2()]
            ]
    with open('test/result.csv', 'w', newline='', encoding='UTF-8') as f:
        csv.writer(f).writerows(result)
    print("Test done!")
    print("Time consumption results: (-1 for failed)")
    print(result)
