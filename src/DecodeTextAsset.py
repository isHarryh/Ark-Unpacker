# -*- coding: utf-8 -*-
# Copyright (c) 2022-2024, Harry Huang
# @ BSD 3-Clause License
import os.path as osp
import json
import bson
import numpy as np
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
from .utils.Config import Config, PerformanceLevel
from .utils.GlobalMethods import print, rmdir, get_filelist, is_ab_file, \
                                 is_known_asset_file, is_binary_file, get_modules_from_package_name
from .utils.Logger import Logger
from .utils.SaverUtils import SafeSaver
from .utils.TaskUtils import ThreadCtrl, UICtrl, TimeRecorder


class ArkFBOLibrary:
    """Helper class for Arknights **FlatBuffers Objects** (FBO) decoding,
    which provides access to the Arknights FlatBuffers Schema (FBS).

    Conventionally, Arknights FBO can be converted to JSON format, assuming that FBS are known.
    Note that the FBS may be incompatible between different Arknights servers.

    *Special thanks to OpenArknightsFBS (https://github.com/MooncellWiki/OpenArknightsFBS).*
    """
    CN = get_modules_from_package_name('src.fbs.CN')
    _AUTO_GUESS_ROOT_TYPE = None

    @staticmethod
    def guess_root_type(path:str):
        """Returns the type class of the most possible FBS root type of the given file.

        :param path: The file path;
        :returns: The root type or `None` indicates that the file may not be a FlatBuffer Object file;
        :rtype: Type or None;
        """
        target = osp.basename(path)
        for m in ArkFBOLibrary.CN:
            name = m.__name__.split('.')[-1]
            if name in target:
                return getattr(m, 'ROOT_TYPE', None)
        return None

    @staticmethod
    def decode(path:str, root_type:type=_AUTO_GUESS_ROOT_TYPE):
        """Decodes the given FlatBuffers binary file.

        :param path: The file path;
        :param root_type: The root type of the FBO;
        :returns: The decoded object;
        :rtype: JSON serializable object;
        """
        if not root_type:
            root_type = ArkFBOLibrary.guess_root_type(path)
        if not root_type:
            Logger.error(f"DecodeTextAsset: Failed to guess root type of \"{path}\"")
            Logger.error(f"DecodeTextAsset: CN lib data = {ArkFBOLibrary.CN}")
            raise AssertionError("Failed to guess root type")
        with open(path, 'rb') as f:
            data = bytearray(f.read())[128:]
            handle = FBOHandler(data, root_type)
            dic = handle.to_json_dict()
            Logger.debug(f"DecodeTextAsset: FBS decoded \"{path}\" with type {root_type.__name__}")
            return dic

class ArkAESLibrary:
    """Helper class for Arknights **AES-CBC encrypted files** decoding,
    which provides methods and keys for decryption.

    Conventionally, Arknights AES-CBC encrypted files are originally JSON or BSON format.
    Note that the secret key (chat_mask) may be incompatible between different major version of Arknights.

    *Special thanks to ashlen (https://github.com/thesadru).*
    """
    MASK_V2 = b'UITpAi82pHAWwnzqHRMCwPonJLIB3WCl'

    @staticmethod
    def aes_cbc_decrypt_bytes(data:bytes, mask:bytes, has_rsa:bool=True):
        """Decrypts the given AES-CBC encrypted data using the specified mask.

        :param data: The data to decrypt;
        :param mask: The 32-bytes secret mask whose first 16-bytes are incomplete key
                     and last 16-bytes are initialization vector (IV);
        :param has_rsa: Whether the data has a 128-bytes RSA signature in the very beginning;
        :returns: The decrypted data;
        :rtype: bytes;
        """
        if not isinstance(data, bytes) or len(data) < 16:
            raise ValueError("The data argument should be a bytes object longer than 16 bytes")
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
    def decode(path:str, mask:bytes=MASK_V2):
        """Decodes the given AES-CBC encrypted file using the given mask.
        If the decrypted data is not JSON, it will be recognized as BSON and be converted to JSON.

        :param path: The file path;
        :param mask: The 32-bytes secret mask;
        :returns: The decoded object;
        :rtype: JSON serializable object;
        """
        with open(path, 'rb') as f:
            data = f.read()
            decrypted = ArkAESLibrary.aes_cbc_decrypt_bytes(data, mask)
            try:
                dic = json.loads(decrypted)
                Logger.debug(f"DecodeTextAsset: AES decoded JSON document \"{path}\"")
            except UnicodeError:
                dic = bson.loads(decrypted)
                Logger.debug(f"DecodeTextAsset: AES decoded BSON document \"{path}\"")
            return dic

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


def text_asset_resolve(fp:str,
                       destdir:str,
                       on_processed:staticmethod,
                       on_file_queued:staticmethod,
                       on_file_saved:staticmethod):
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
                byt = bytes(json.dumps(dic, ensure_ascii=False, indent=2), encoding='UTF-8')
                SafeSaver.save_bytes(byt, destdir, osp.basename(fp), '.json', on_file_queued, on_file_saved)
        else:
            Logger.debug(f"DecodeTextAsset: \"{fp}\" not binary file")
    except Exception as arg:
        Logger.error(f"DecodeTextAsset: Failed to handle \"{fp}\": Exception{type(arg)} {arg}")
    if on_processed:
        on_processed()

########## Main-主程序 ##########
def main(rootdir:str, destdir:str, do_del:bool=False):
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
            "正在批量解码文本资源...",
            recorder.get_progress_str(),
            f"当前目录：\t{osp.basename(osp.dirname(i))}",
            f"当前搜索：\t{osp.basename(i)}",
            f"累计搜索：\t{recorder.get_done_dest_str_of(2)}",
            f"累计解码：\t{recorder.get_done_dest_str_of(1)}",
            f"剩余时间：\t{recorder.get_eta_str()}",
        ])
        ###
        subdestdir = osp.dirname(i).strip(osp.sep).replace(rootdir, '').strip(osp.sep)
        thread_ctrl.run_subthread(text_asset_resolve, (i, osp.join(destdir, subdestdir), on_processed, on_file_queued, on_file_saved), \
            name=f"RFThread:{id(i)}")

    ui.reset()
    ui.loop_stop()
    while thread_ctrl.count_subthread() or not SafeSaver.get_instance().completed() or recorder.get_progress() < 1:
        ui.request([
            "正在批量解码文本资源...",
            recorder.get_progress_str(),
            f"累计搜索：\t{recorder.get_done_dest_str_of(2)}",
            f"累计解码：\t{recorder.get_done_dest_str_of(1)}",
            f"剩余时间：\t{recorder.get_eta_str()}",
        ])
        ui.refresh(post_delay=0.1)

    ui.reset()
    print("\n批量解码文本资源结束!", s=1)
    print(f"  累计搜索 {recorder.get_done_of(2)} 个文件")
    print(f"  累计解码 {recorder.get_done_of(1)} 个文件")
    print(f"  此项用时 {round(recorder.get_rt(), 1)} 秒")
