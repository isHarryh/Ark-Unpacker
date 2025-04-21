# -*- coding: utf-8 -*-
# Copyright (c) 2022-2025, Harry Huang
# @ BSD 3-Clause License
from typing import Callable, Optional, Union

import json
import os.path as osp
from collections import defaultdict

import bson
import numpy as np
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

from .utils.GlobalMethods import (
    print,
    rmdir,
    get_filelist,
    is_ab_file,
    is_known_asset_file,
    is_binary_file,
    get_modules_from_package_name,
)
from .utils.Logger import Logger
from .utils.SaverUtils import SafeSaver
from .utils.TaskUtils import ThreadCtrl, UICtrl, TaskReporter, TaskReporterTracker


class ArkFBOLibrary:
    """Helper class for Arknights **FlatBuffers Objects** (FBO) decoding,
    which provides access to the Arknights FlatBuffers Schema (FBS).

    Conventionally, Arknights FBO can be converted to JSON format, assuming that FBS are known.
    Note that the FBS may be incompatible between different Arknights servers.

    *Special thanks to OpenArknightsFBS (https://github.com/MooncellWiki/OpenArknightsFBS).*
    """

    CN = get_modules_from_package_name("src.fbs.CN")
    _AUTO_GUESS_ROOT_TYPE = None

    @staticmethod
    def guess_root_type(path: str):
        """Returns the type class of the most possible FBS root type of the given file.

        :param path: The file path;
        :returns: The root type or `None` indicates that the file may not be a FlatBuffer Object file;
        :rtype: Type or None;
        """
        target = osp.basename(path)
        for m in ArkFBOLibrary.CN:
            name = m.__name__.split(".")[-1]
            if name in target:
                return getattr(m, "ROOT_TYPE", None)
        return None

    @staticmethod
    def decode(path: str, root_type: Optional[type] = _AUTO_GUESS_ROOT_TYPE):
        """Decodes the given FlatBuffers binary file.

        :param path: The file path;
        :param root_type: The root type of the FBO;
        :returns: The decoded object;
        :rtype: JSON serializable object;
        """
        if not root_type:
            root_type = ArkFBOLibrary.guess_root_type(path)
        if not root_type:
            Logger.error(f'DecodeTextAsset: Failed to guess root type of "{path}"')
            Logger.error(f"DecodeTextAsset: CN lib data = {ArkFBOLibrary.CN}")
            raise AssertionError("Failed to guess root type")
        with open(path, "rb") as f:
            data = bytearray(f.read())[128:]
            handle = FBOHandler(data, root_type)
            dic = handle.to_json_dict()
            Logger.debug(
                f'DecodeTextAsset: FBS decoded "{path}" with type {root_type.__name__}'
            )
            return dic


# spell-checker: disable


class ArkAESLibrary:
    """Helper class for Arknights **AES-CBC encrypted files** decoding,
    which provides methods and keys for decryption.

    Conventionally, Arknights AES-CBC encrypted files are originally JSON or BSON format.
    Note that the secret key (chat_mask) may be incompatible between different major version of Arknights.

    *Special thanks to ashlen (https://github.com/thesadru).*
    """

    MASK_V2 = b"UITpAi82pHAWwnzqHRMCwPonJLIB3WCl"

    # spell-checker: enable

    @staticmethod
    def aes_cbc_decrypt_bytes(data: bytes, mask: bytes, has_rsa: bool = True):
        """Decrypts the given AES-CBC encrypted data using the specified mask.

        :param data: The data to decrypt;
        :param mask: The 32-bytes secret mask whose first 16-bytes are incomplete key
                     and last 16-bytes are initialization vector (IV);
        :param has_rsa: Whether the data has a 128-bytes RSA signature in the very beginning;
        :returns: The decrypted data;
        :rtype: bytes;
        """
        if not isinstance(data, bytes) or len(data) < 16:
            raise ValueError(
                "The data argument should be a bytes object longer than 16 bytes"
            )
        if not isinstance(mask, bytes) or len(mask) != 32:
            raise ValueError("The mask argument should be a 32-byte-long bytes object")
        # Trim the signature
        if has_rsa:
            data = data[128:]
        # Calculate the key and IV
        key = mask[:16]
        iv = bytearray(d ^ m for d, m in zip(data[:16], mask[16:]))
        # Decrypt the data
        aes = AES.new(key, AES.MODE_CBC, iv)
        return unpad(aes.decrypt(data[16:]), AES.block_size)

    @staticmethod
    def decode(path: str, mask: bytes = MASK_V2):
        """Decodes the given AES-CBC encrypted file using the given mask.
        If the decrypted data is not JSON, it will be recognized as BSON and be converted to JSON.

        :param path: The file path;
        :param mask: The 32-bytes secret mask;
        :returns: The decoded object;
        :rtype: JSON serializable object;
        """
        with open(path, "rb") as f:
            data = f.read()
            decrypted = ArkAESLibrary.aes_cbc_decrypt_bytes(data, mask)
            try:
                dic = json.loads(decrypted)
                Logger.debug(f'DecodeTextAsset: AES decoded JSON document "{path}"')
            except UnicodeError:
                dic = bson.loads(decrypted)
                Logger.debug(f'DecodeTextAsset: AES decoded BSON document "{path}"')
            return dic


class FBOHandler:
    """Handler for FlatBuffers Objects, implementing conversion to Python dict type."""

    SERIALIZE_AS_IS = Union[bool, int, str, list, tuple, dict, None]
    SERIALIZE_AS_STR = Union[bytes, bytearray, memoryview]
    SERIALIZE_ENCODING = "UTF-8"

    def __init__(self, data: bytearray, root_type: type):
        self._root = root_type.GetRootAs(data, 0)

    @staticmethod
    def _to_literal(obj: object):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, FBOHandler.SERIALIZE_AS_IS):
            return obj
        if isinstance(obj, FBOHandler.SERIALIZE_AS_STR):
            return str(obj, encoding=FBOHandler.SERIALIZE_ENCODING)
        return FBOHandler._to_json_dict(obj)

    @staticmethod
    def _to_json_dict(obj: object):
        if obj is None:
            return None

        data = {}

        f_obj_key = getattr(obj, "Key", None)
        f_obj_value = getattr(obj, "Value", None)
        f_obj_value_len = getattr(obj, "ValueLength", None)

        if f_obj_key and f_obj_value:
            # As key-value item:
            assert isinstance(f_obj_key, Callable) and isinstance(f_obj_value, Callable)
            if f_obj_value_len:
                # Value is array
                assert isinstance(f_obj_value_len, Callable)
                data[FBOHandler._to_literal(f_obj_key())] = [
                    FBOHandler._to_literal(f_obj_value(i))
                    for i in range(f_obj_value_len())
                ]
            else:
                # Value is single
                data[FBOHandler._to_literal(f_obj_key())] = FBOHandler._to_literal(
                    f_obj_value()
                )
        else:
            # As table object:
            # Collect field names
            field_name_map = defaultdict(lambda: [None, None, None])
            for field_name in dir(obj):
                if field_name in ("Init", "Clear"):
                    continue
                elif field_name.startswith(("_", "GetRootAs")):
                    continue
                elif field_name != "IsNone" and field_name.endswith("IsNone"):
                    field_name_map[field_name[:-6]][0] = getattr(obj, field_name, None)
                elif field_name != "Length" and field_name.endswith("Length"):
                    field_name_map[field_name[:-6]][1] = getattr(obj, field_name, None)
                else:
                    field_name_map[field_name][2] = getattr(obj, field_name, None)

            # Collect field values
            for field_name, (
                f_field_is_none,
                f_field_len,
                f_field,
            ) in field_name_map.items():
                if isinstance(f_field, Callable):
                    value = None
                    if isinstance(f_field_is_none, Callable) and f_field_is_none():
                        # Value is explicit null
                        continue
                    elif isinstance(f_field_len, Callable):
                        # Value is table or array
                        field_len = f_field_len()
                        if field_len:
                            if "Key" in dir(f_field(0)):
                                # Value is table
                                value = {}
                                for i in range(field_len):
                                    item = FBOHandler._to_json_dict(f_field(i))
                                    assert isinstance(item, dict)
                                    value.update(item)
                            else:
                                # Value is array
                                value = [
                                    FBOHandler._to_literal(f_field(i))
                                    for i in range(field_len)
                                ]
                        else:
                            # TODO handle empty table
                            pass
                    else:
                        # Value is common literal
                        value = FBOHandler._to_literal(f_field())
                    # Add this field to the object data
                    data[field_name] = value

        # Return the whole object data
        return data

    def to_json_dict(self):
        return FBOHandler._to_json_dict(self._root)


def text_asset_resolve(
    fp: str,
    destdir: str,
    on_processed: Optional[Callable],
    on_file_queued: Optional[Callable],
    on_file_saved: Optional[Callable],
):
    """Decodes the give Arknights TextAsset file that is either FBO stored format or AES encrypted format,
    otherwise does nothing.

    :param fp: Path to the file;
    :param destdir: Destination directory;
    :param on_processed: Callback `f()` for finished, `None` for ignore;
    :param on_file_queued: Callback `f()` invoked when a file was queued, `None` for ignore;
    :param on_file_saved: Callback `f(file_path_or_none_for_not_saved)`, `None` for ignore;
    :rtype: None;
    """
    try:
        if osp.isfile(fp) and is_binary_file(fp):
            typ = ArkFBOLibrary.guess_root_type(fp)
            dic = ArkFBOLibrary.decode(fp, typ) if typ else ArkAESLibrary.decode(fp)
            if dic:
                byt = bytes(
                    json.dumps(dic, ensure_ascii=False, indent=2), encoding="UTF-8"
                )
                SafeSaver.save_bytes(
                    byt,
                    destdir,
                    osp.basename(fp),
                    ".json",
                    on_file_queued,
                    on_file_saved,
                )
        else:
            Logger.debug(f'DecodeTextAsset: "{fp}" not binary file')
    except Exception as arg:
        Logger.error(
            f'DecodeTextAsset: Failed to handle "{fp}": Exception{type(arg)} {arg}'
        )
    if on_processed:
        on_processed()


########## Main-主程序 ##########
def main(rootdir: str, destdir: str, do_del: bool = False):
    """Decodes the possible Arknights TextAsset files in the specified directory
    then saves the decoded data into another given directory.

    :param rootdir: Source directory;
    :param destdir: Destination directory;
    :param do_del: Whether to delete the existed destination directory first, `False` for default;
    :rtype: None;
    """
    print("\n正在解析路径...", s=1)
    Logger.info("DecodeTextAsset: Retrieving file paths...")
    rootdir = osp.normpath(osp.realpath(rootdir))
    destdir = osp.normpath(osp.realpath(destdir))
    flist = get_filelist(rootdir)
    flist = list(filter(lambda x: not is_known_asset_file(x), flist))
    flist = list(filter(lambda x: not is_ab_file(x), flist))

    if do_del:
        print("\n正在清理...", s=1)
        rmdir(destdir)
    SafeSaver.get_instance().reset_counter()
    thread_ctrl = ThreadCtrl()
    ui = UICtrl()
    tr_processed = TaskReporter(2)
    tr_file_saving = TaskReporter(1)
    tracker = TaskReporterTracker(tr_processed, tr_file_saving)

    ui.reset()
    ui.loop_start()
    for i in flist:
        ui.request(
            [
                "正在批量解码文本资源...",
                tracker.to_progress_bar_str(),
                f"当前目录：\t{osp.basename(osp.dirname(i))}",
                f"当前搜索：\t{osp.basename(i)}",
                f"累计搜索：\t{tr_processed.to_progress_str()}",
                f"累计解码：\t{tr_file_saving.to_progress_str()}",
                f"预计剩余时间：\t{tracker.to_eta_str()}",
                f"累计消耗时间：\t{tracker.to_rt_str()}",
                f"运行状态统计：\t{Logger.to_ew_stats_str()}",
            ]
        )
        ###
        subdestdir = osp.dirname(i).strip(osp.sep).replace(rootdir, "").strip(osp.sep)
        thread_ctrl.run_subthread(
            text_asset_resolve,
            (
                i,
                osp.join(destdir, subdestdir),
                tr_processed.report,
                tr_file_saving.update_demand,
                tr_file_saving.report,
            ),
            name=f"RFThread:{id(i)}",
        )

    ui.reset()
    ui.loop_stop()
    while (
        thread_ctrl.count_subthread()
        or not SafeSaver.get_instance().completed()
        or tracker.get_progress() < 1
    ):
        ui.request(
            [
                "正在批量解码文本资源...",
                tracker.to_progress_bar_str(),
                f"累计搜索：\t{tr_processed.to_progress_str()}",
                f"累计解码：\t{tr_file_saving.to_progress_str()}",
                f"预计剩余时间：\t{tracker.to_eta_str()}",
                f"累计消耗时间：\t{tracker.to_rt_str()}",
                f"运行状态统计：\t{Logger.to_ew_stats_str()}",
            ]
        )
        ui.refresh(post_delay=0.1)

    ui.reset()
    print("\n批量解码文本资源结束!", s=1)
    print(f"  累计搜索 {tr_processed.get_done()} 个文件")
    print(f"  累计解码 {tr_file_saving.get_done()} 个文件")
    print(f"  此项用时 {round(tracker.get_rt(), 1)} 秒")
