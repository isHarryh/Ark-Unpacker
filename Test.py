# -*- coding: utf-8 -*-
# Copyright (c) 2022-2023, Harry Huang
# @ BSD 3-Clause License
import os, sys, json, shutil
import subprocess
from src.utils.Profiler import CodeProfiler
from src.utils.GlobalMethods import print, stacktrace


def __assert_file_count(path, expected_count):
    if not os.path.isdir(path):
        raise AssertionError(f"Directory {path} not found")
    count = 0
    for _, _, files in os.walk(path):
        count += len(files)
    if count != expected_count:
        raise AssertionError(
            f"Expected {expected_count} files but got {count} files in {path}"
        )


def __run_cli(args: list):
    cmd = [sys.executable, "Main.py"] + args
    result = subprocess.run(
        cmd, stdout=sys.stdout, stderr=sys.stderr, encoding="utf-8", errors="replace"
    )
    return "", "", result.returncode


def test():
    for i in range(int(sys.argv[1]) if len(sys.argv) > 1 else 1):
        try:
            print(f"[#{i}] Preparing...", c=6)
            DIR_UPK = "test/upk"
            DIR_CMB = "test/cmb"
            DIR_DTA = "test/dta"
            DIR_SPI = "test/spi"
            shutil.rmtree(DIR_UPK, ignore_errors=True)
            shutil.rmtree(DIR_CMB, ignore_errors=True)
            shutil.rmtree(DIR_DTA, ignore_errors=True)
            shutil.rmtree(DIR_SPI, ignore_errors=True)

            print(f"[#{i}] Testing...", c=6)
            with CodeProfiler("unit_1"):
                out, err, code = __run_cli(
                    [
                        "-m",
                        "ab",
                        "-i",
                        "test/res",
                        "-o",
                        DIR_UPK,
                        "--image",
                        "--text",
                        "--audio",
                        "--mesh",
                        "-g",
                    ]
                )
                if code != 0:
                    print(out)
                    print(err)
                    raise AssertionError(f"ArkUnpacker ab mode failed, code={code}")
            with CodeProfiler("unit_2"):
                out, err, code = __run_cli(
                    [
                        "-m",
                        "cb",
                        "-i",
                        DIR_UPK,
                        "-o",
                        DIR_CMB,
                    ]
                )
                if code != 0:
                    print(out)
                    print(err)
                    raise AssertionError(f"ArkUnpacker cb mode failed, code={code}")
            with CodeProfiler("unit_3"):
                out, err, code = __run_cli(
                    [
                        "-m",
                        "fb",
                        "-i",
                        DIR_UPK,
                        "-o",
                        DIR_DTA,
                    ]
                )
                if code != 0:
                    print(out)
                    print(err)
                    raise AssertionError(f"ArkUnpacker fb mode failed, code={code}")
            with CodeProfiler("unit_4"):
                out, err, code = __run_cli(
                    [
                        "-m",
                        "sp",
                        "-i",
                        "test/res",
                        "-o",
                        DIR_SPI,
                    ]
                )
                if code != 0:
                    print(out)
                    print(err)
                    raise AssertionError(f"ArkUnpacker sp mode failed, code={code}")

            print(f"[#{i}] Analysing...", c=6)
            __assert_file_count(DIR_UPK, 1470)
            __assert_file_count(DIR_CMB, 157)
            __assert_file_count(DIR_DTA, 2)
            __assert_file_count(DIR_SPI, 208)

            print(f"[#{i}] Test success!", c=2)
        except BaseException as arg:
            print(f"[#{i}] Test failed because an error occurred!", c=1)
            print(stacktrace(), c=3)
    json.dump(
        {
            "average": CodeProfiler.get_avg_time_all(),
            "total": CodeProfiler.get_total_time_all(),
        },
        open("test/time_consumption.json", "w", encoding="UTF-8"),
        indent=4,
    )


if __name__ == "__main__":
    test()
