# -*- coding: utf-8 -*-
# Copyright (c) 2022-2023, Harry Huang
# @ BSD 3-Clause License
import os, sys, json, shutil
from src import ResolveAB
from src import CombineRGBwithA
from src import DecodeTextAsset
from src.utils.Profiler import CodeProfiler
from src.utils.GlobalMethods import print, stacktrace


def __count_files(path):
    count = 0
    for _, _, files in os.walk(path):
        count += len(files)
    return count


if __name__ == "__main__":
    for i in range(int(sys.argv[1]) if len(sys.argv) > 1 else 1):
        try:
            print(f"[#{i}] Preparing...", c=0)
            DIR_UPK = "test/upk"
            DIR_CMB = "test/cmb"
            DIR_DTA = "test/dta"
            shutil.rmtree(DIR_UPK, ignore_errors=True)
            shutil.rmtree(DIR_CMB, ignore_errors=True)
            shutil.rmtree(DIR_DTA, ignore_errors=True)

            print(f"[#{i}] Testing...", c=0)
            with CodeProfiler("unit_1"):
                ResolveAB.main(
                    "test/res",
                    DIR_UPK,
                    do_del=False,
                    do_img=True,
                    do_txt=True,
                    do_aud=True,
                    do_spine=False,
                )
            with CodeProfiler("unit_2"):
                CombineRGBwithA.main(DIR_UPK, DIR_CMB, do_del=False)
            with CodeProfiler("unit_3"):
                DecodeTextAsset.main(DIR_UPK, DIR_DTA, do_del=False)

            print(f"[#{i}] Analysing...", c=0)
            if __count_files(DIR_UPK) != 1374:
                raise AssertionError("Unpacked files count mismatch")
            if __count_files(DIR_CMB) != 153:
                raise AssertionError("Combined images count mismatch")
            if __count_files(DIR_DTA) != 2:
                raise AssertionError("Decoded textassets count mismatch")

            print(f"[#{i}] Test success!", c=0)
        except BaseException as arg:
            print(f"[#{i}] Test failed because an error occurred!", c=7)
            print(stacktrace(), c=3)
    json.dump(
        CodeProfiler.get_avg_time_all(),
        open("test/rt.json", "w", encoding="UTF-8"),
        indent=4,
    )
