# -*- coding: utf-8 -*-
# Copyright (c) 2022-2025, Harry Huang
# @ BSD 3-Clause License
from typing import Callable, Optional

import os.path as osp
import re

from .GlobalMethods import input, print


class UserInput:
    CANCEL_CMD = "*"

    @staticmethod
    def request(prompt: str = "> "):
        uin = input(prompt, c=2)
        if uin == UserInput.CANCEL_CMD:
            print("  已取消任务", c=3)
            raise InterruptedError("User cancelled")
        return uin

    @staticmethod
    def request_options(options: list):
        print(f'  输入符号 "{UserInput.CANCEL_CMD}" 以取消任务')
        uin = UserInput.request()
        while uin not in options:
            print("  输入的选项不合法", c=3)
            uin = UserInput.request()
        return uin

    @staticmethod
    def request_input_path():
        print(f'  输入符号 "{UserInput.CANCEL_CMD}" 以取消任务，支持输入相对路径')
        while True:
            uin = UserInput.request().strip()
            if not uin:
                print("  路径不能为空", c=3)
                continue
            uin = osp.normpath(uin)
            if not osp.exists(uin):
                print("  输入的路径不存在", c=3)
                continue
            return osp.abspath(uin)

    @staticmethod
    def request_output_path(default_generator: Optional[Callable[[], str]] = None):
        print("  支持相对路径" + ("，留空表示自动创建" if default_generator else ""))
        while True:
            uin = UserInput.request().strip()
            if not uin:
                if default_generator:
                    return osp.abspath(default_generator())
                else:
                    print("  路径不能为空", c=3)
                    continue
            uin = osp.normpath(uin)
            if re.search(r'[*?"<>|\x00-\x1F]', uin):
                print("  路径不能包含非法字符", c=3)
                continue
            return osp.abspath(uin)

    @staticmethod
    def request_yes_or_no(default: bool):
        print(f'  输入符号 "{UserInput.CANCEL_CMD}" 以取消任务')
        uin = UserInput.request().strip().lower()
        if default:
            return False if uin == "n" else True
        else:
            return True if uin == "y" else False

    @staticmethod
    def press_enter_to_exit():
        input("> 按Enter退出...", c=1)
