# -*- coding: utf-8 -*-
# Copyright (c) 2022-2024, Harry Huang
# @ BSD 3-Clause License
import os.path as osp
import json
import types
import pkgutil
import importlib.util

import numpy as np
from .utils.Config import Config, PerformanceLevel
from .utils.GlobalMethods import print, rmdir, get_filelist, is_ab_file, is_known_asset_file
from .utils.Logger import Logger
from .utils.SaverUtils import SafeSaver
from .utils.TaskUtils import ThreadCtrl, UICtrl, TimeRecorder


class PackageHelper:
    """Helper class for dynamic package inspection."""

    @staticmethod
    def get_modules_from_package(package:types.ModuleType):
        walk_result = pkgutil.walk_packages(package.__path__, package.__name__ + '.')
        module_names = [name for _, name, is_pkg in walk_result if not is_pkg]
        return [importlib.import_module(name) for name in module_names]

    @staticmethod
    def get_modules_from_package_name(package_name:str):
        package = importlib.import_module(package_name)
        return PackageHelper.get_modules_from_package(package)

class ArkFBOLibrary:
    """Helper class for Arknights FlatBuffers Objects decoding."""
    CN = PackageHelper.get_modules_from_package_name('src.fbs.CN')
    _AUTO_GUESS_ROOT_TYPE = None

    @staticmethod
    def is_binary_file(path:str, guess_encoding:str='UTF-8'):
        try:
            with open(path, encoding=guess_encoding) as f:
                f.read()
            return False
        except UnicodeError:
            return True

    @staticmethod
    def guess_root_type(path:str):
        target = osp.basename(path)
        for m in ArkFBOLibrary.CN:
            name = m.__name__.split('.')[-1]
            if name in target:
                return getattr(m, 'ROOT_TYPE', None)
        return None

    @staticmethod
    def decode(path:str, root_type:type=_AUTO_GUESS_ROOT_TYPE):
        if not root_type:
            root_type = ArkFBOLibrary.guess_root_type(path)
        if not root_type:
            Logger.error(f"ResolveFBO: Failed to guess root type of \"{path}\"")
            Logger.error(f"ResolveFBO: CN lib data = {ArkFBOLibrary.CN}")
            raise AssertionError("Failed to guess root type")
        with open(path, 'rb') as f:
            data = bytearray(f.read())[128:]
            handle = FBOHandler(data, root_type)
            return handle.to_json_dict()

class FBOHandler:
    """Handler for FlatBuffers Objects, implementing conversion to Python dict type."""
    def __init__(self, data:bytearray, root_type:type):
        self._root = root_type.GetRootAs(data, 0)

    @staticmethod
    def _to_literal(obj:object):
        if obj is None:
            return None
        if isinstance(obj, bytes):
            return str(obj, encoding='UTF-8')
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if not isinstance(obj, (bool, int, float, str, dict, list)):
            return FBOHandler._to_json_dict(obj)
        return obj

    @staticmethod
    def _to_json_dict(obj:object):
        if obj is None:
            return None
        data = {}
        if 'Key' in dir(obj) and 'Value' in dir(obj):
            # As key-value table:
            val = None
            val_len_method = getattr(obj, 'ValueLength', None)
            if val_len_method:
                # As key-array table
                val = [FBOHandler._to_literal(obj.Value(i)) for i in range(val_len_method())]
            else:
                val = FBOHandler._to_literal(obj.Value())
            data[FBOHandler._to_literal(obj.Key())] = val
        else:
            # As general object:
            for field_name in dir(obj):
                # For each fields in the object
                # Exclude FBO universal fields
                if field_name in ('Init'):
                    continue
                if field_name.startswith(('_', 'GetRootAs')):
                    continue
                if field_name.endswith(('IsNone', 'Length')):
                    continue
                # Collect field data from callable
                field = getattr(obj, field_name)
                if callable(field):
                    val = None
                    # Try as none
                    is_none_method = getattr(obj, f'{field_name}IsNone', None)
                    if is_none_method and is_none_method():
                        continue
                    # Try as table
                    field_len_method = getattr(obj, f'{field_name}Length', None)
                    if field_len_method:
                        # As table:
                        field_len = field_len_method()
                        if field_len:
                            if 'Key' in dir(field(0)):
                                # As key-value table:
                                val = {}
                                for i in range(field_len):
                                    val.update(FBOHandler._to_json_dict(field(i)))
                            else:
                                # As general table:
                                val = []
                                for i in range(field_len):
                                    val.append(FBOHandler._to_literal(field(i)))
                        else:
                            # TODO handle empty table
                            pass
                    else:
                        # As other literal field:
                        val = FBOHandler._to_literal(field())
                    # Add this field to the object data
                    data[field_name] = val
        # Return the whole object data
        return data

    def to_json_dict(self):
        return FBOHandler._to_json_dict(self._root)

def fbo_resolve(fp:str, destdir:str, on_processed:staticmethod, on_file_queued:staticmethod, on_file_saved:staticmethod):
    """Decodes the give Arknights FlatBuffers binary file if it is a Arknights FlatBuffers binary file,
    otherwise does nothing.

    :param fp: Path to the file;
    :param destdir: Destination directory;
    :param on_processed: Callback `f()` for finished, `None` for ignore;
    :param on_file_queued: Callback `f()` invoked when a file was queued, `None` for ignore;
    :param on_file_saved: Callback `f(file_path_or_none_for_not_saved)`, `None` for ignore;
    :rtype: None;
    """
    try:
        if osp.isfile(fp):
            typ = ArkFBOLibrary.guess_root_type(fp)
            if typ and ArkFBOLibrary.is_binary_file(fp):
                dic = ArkFBOLibrary.decode(fp, typ)
                byt = bytes(json.dumps(dic, ensure_ascii=False, indent=4), encoding='UTF-8')
                Logger.debug(f"ResolveFBO: \"{fp}\" decoded, using {typ}")
                SafeSaver.save_bytes(byt, destdir, osp.basename(fp), '.json', on_file_queued, on_file_saved)
            else:
                Logger.debug(f"ResolveFBO: \"{fp}\" not a binary file")
    except Exception as arg:
        Logger.error(f"ResolveFBO: Failed to handle \"{fp}\": Exception{type(arg)} {arg}")
    if on_processed:
        on_processed()

########## Main-主程序 ##########
def main(rootdir:str, destdir:str, do_del:bool=False):
    """Decodes the possible Arknights FlatBuffers binary files in the specified directory
    then saves the decoded data into another given directory.

    :param rootdir: Source directory;
    :param destdir: Destination directory;
    :param do_del: Whether to delete the existed destination directory first, `False` for default;
    :rtype: None;
    """
    print("\n正在解析路径...", s=1)
    Logger.info("ResolveFBO: Retrieving file paths...")
    rootdir = osp.normpath(osp.realpath(rootdir))
    destdir = osp.normpath(osp.realpath(destdir))
    flist = get_filelist(rootdir)
    flist = list(filter(lambda x:not is_known_asset_file(x), flist))
    flist = list(filter(lambda x:not is_ab_file(x), flist))

    if do_del:
        print("\n正在清理...", s=1)
        rmdir(destdir)
    SafeSaver.get_instance().reset_counter()
    thread_ctrl = ThreadCtrl(PerformanceLevel.get_thread_limit(Config.get('performance_level')))
    ui = UICtrl()
    recorder = TimeRecorder()
    recorder.update_dest(2, len(flist))
    on_processed = lambda: recorder.done_once(2)
    on_file_queued = lambda: recorder.update_dest(1)
    on_file_saved = lambda x: recorder.done_once(1) if x else recorder.update_dest(1, -1)

    ui.reset()
    ui.loop_start()
    for i in flist:
        ui.request([
            "正在批量解码FlatBuffers数据...",
            recorder.get_progress_str(),
            f"当前目录：\t{osp.basename(osp.dirname(i))}",
            f"当前搜索：\t{osp.basename(i)}",
            f"累计搜索：\t{recorder.get_done_dest_str_of(2)}",
            f"累计解码：\t{recorder.get_done_dest_str_of(1)}",
            f"剩余时间：\t{recorder.get_eta_str()}",
        ])
        ###
        subdestdir = osp.dirname(i).strip(osp.sep).replace(rootdir, '').strip(osp.sep)
        thread_ctrl.run_subthread(fbo_resolve, (i, osp.join(destdir, subdestdir), on_processed, on_file_queued, on_file_saved), \
            name=f"RFThread:{id(i)}")

    ui.reset()
    ui.loop_stop()
    while thread_ctrl.count_subthread() or not SafeSaver.get_instance().completed() or recorder.get_progress() < 1:
        ui.request([
            "正在批量解码FlatBuffers数据...",
            recorder.get_progress_str(),
            f"累计搜索：\t{recorder.get_done_dest_str_of(2)}",
            f"累计解码：\t{recorder.get_done_dest_str_of(1)}",
            f"剩余时间：\t{recorder.get_eta_str()}",
        ])
        ui.refresh(post_delay=0.1)

    ui.reset()
    print("\n批量解码FlatBuffers数据结束!", s=1)
    print(f"  累计搜索 {recorder.get_done_of(2)} 个文件")
    print(f"  累计解码 {recorder.get_done_of(1)} 个文件")
    print(f"  此项用时 {round(recorder.get_rt(), 1)} 秒")
