# -*- coding: utf-8 -*-
# Copyright (c) 2022-2023, Harry Huang
# @ BSD 3-Clause License
import os, sys, csv, time, shutil
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
        if __count_files('test/upk') != 1269:
            raise AssertionError("Upk files count error")
        return time.time() - t
    except BaseException as arg:
        return arg

def test_unit_2():
    try:
        t = time.time()
        CombineRGBwithA.main('test/upk',
                            'test/cmb',
                            dodel=False
                            )
        if __count_files('test/cmb') != 112:
            raise AssertionError("Cmb files count error")
        return time.time() - t
    except BaseException as arg:
        return arg

if __name__ == '__main__':
    for i in range(int(sys.argv[1]) if len(sys.argv) > 1 else 1):
        print(f"#{i} Preparing...")
        shutil.rmtree('test/upk', ignore_errors=True)
        shutil.rmtree('test/cmb', ignore_errors=True)
        print(f"#{i} Testing...")
        result = [["Unit1", test_unit_1()],
                ["Unit2", test_unit_2()]
                ]
        for n, t in result:
            if type(t) in (float, int):
                print(f"[OKAY] {n} used {round(t, 3)}s")
            elif type(t) == AssertionError:
                print(f"[FAIL] {n} assertion failed, {t.args}")
            elif type(t) == BaseException:
                print(f"[FAIL] {n} raised {t}")
            else:
                raise TypeError("Unknown result")
        with open('test/result.csv', 'a', newline='', encoding='UTF-8') as f:
            for n, t in result:
                csv.writer(f).writerow((n, t if type(t) in (float, int) else -1))
        print(f"#{i} Test done!")
