# Copyright (c) 2022-2026, Harry Huang
# @ BSD 3-Clause License
import os, sys, json, shutil
import subprocess

from src.ui.RichCLI import RichCLI
from src.utils.Profiler import CodeProfiler
from src.utils.GlobalMethods import stacktrace

CLI = RichCLI.get_instance()


def _print_status(message: str, *, style: str = "white") -> None:
    CLI.console.print(message, style=style, markup=False, highlight=False)


def __check_file_list(dir_path: str):
    name = os.path.basename(dir_path)
    actual_path = f"test/_summary/{name}.out"
    std_file_path = f"test/_summary/{name}.std"
    if not os.path.isdir(dir_path):
        return

    os.makedirs(os.path.dirname(actual_path), exist_ok=True)
    actual_list = []
    for root, _, files in os.walk(dir_path):
        for file in files:
            rel_path = os.path.normpath(os.path.relpath(os.path.join(root, file), dir_path))
            actual_list.append(rel_path.replace("\\", "/"))
    actual_list.sort()
    with open(actual_path, "w", encoding="utf-8") as f:
        f.write("\n".join(actual_list))
    actual_set = set(actual_list)

    if not os.path.isfile(std_file_path):
        raise AssertionError(f"Expected file list {std_file_path} not found")
    with open(std_file_path, "r", encoding="utf-8") as f:
        expected_set = set(f.read().splitlines())

    if actual_set != expected_set:
        added = sorted(list(actual_set - expected_set))
        removed = sorted(list(expected_set - actual_set))
        _print_status(f"\n[File Mismatch] {os.path.basename(actual_path)}", style="bold red")
        if added:
            _print_status(f"  Added ({len(added)}):", style="bold yellow")
            for f in added[:10]:
                _print_status(f"    + {f}", style="bold green")
            if len(added) > 10:
                _print_status(f"    ... and {len(added) - 10} more", style="bold green")
        if removed:
            _print_status(f"  Removed ({len(removed)}):", style="bold yellow")
            for f in removed[:10]:
                _print_status(f"    - {f}", style="bold red")
            if len(removed) > 10:
                _print_status(f"    ... and {len(removed) - 10} more", style="bold red")
        raise AssertionError(f"File list mismatch for {actual_path}: {len(added)} added, {len(removed)} removed")


def __run_cli(args: list):
    cmd = [sys.executable, "Main.py"] + args
    result = subprocess.run(cmd, stdout=sys.stdout, stderr=sys.stderr, encoding="utf-8", errors="replace")
    return "", "", result.returncode


def test():
    for i in range(int(sys.argv[1]) if len(sys.argv) > 1 else 1):
        try:
            _print_status(f"[#{i}] Preparing...", style="bold cyan")
            DIR_UPK = "test/upk"
            DIR_CMB = "test/cmb"
            DIR_DTA = "test/dta"
            DIR_SPI = "test/spi"
            DIR_USM = "test/usm"
            shutil.rmtree(DIR_UPK, ignore_errors=True)
            shutil.rmtree(DIR_CMB, ignore_errors=True)
            shutil.rmtree(DIR_DTA, ignore_errors=True)
            shutil.rmtree(DIR_SPI, ignore_errors=True)
            shutil.rmtree(DIR_USM, ignore_errors=True)

            _print_status(f"[#{i}] Testing...", style="bold cyan")
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
                        "--typetree",
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
            with CodeProfiler("unit_5"):
                out, err, code = __run_cli(
                    [
                        "-m",
                        "cu",
                        "-i",
                        "test/res",
                        "-o",
                        DIR_USM,
                    ]
                )
                if code != 0:
                    print(out)
                    print(err)
                    raise AssertionError(f"ArkUnpacker cu mode failed, code={code}")

            _print_status(f"[#{i}] Analysing...", style="bold cyan")
            __check_file_list(DIR_UPK)
            __check_file_list(DIR_CMB)
            __check_file_list(DIR_DTA)
            __check_file_list(DIR_SPI)
            __check_file_list(DIR_USM)

            _print_status(f"[#{i}] Test success!", style="bold green")
        except BaseException as arg:
            _print_status(f"[#{i}] Test failed because an error occurred!", style="bold red")
            _print_status(stacktrace(), style="bold yellow")
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
