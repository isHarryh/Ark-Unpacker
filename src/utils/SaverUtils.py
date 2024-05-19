# -*- coding: utf-8 -*-
# Copyright (c) 2022-2023, Harry Huang
# @ BSD 3-Clause License
import os
from io import BytesIO
from PIL import Image
from .GlobalMethods import *
from .Logger import *
from .TaskUtils import *


class SafeSaver():
    """The base class for file saver which is able to avoid name collision."""
    thread_ctrl = ThreadCtrl(1)
    total_processed = Counter()
    total_requested = Counter()

    @staticmethod
    def get_progress():
        """Gets the progress, aka. the saver thread idle ratio.

        :returns: The progress in `[0.0, 1.0]`;
        :rtype: float;
        """
        return 1 - MySaver.thread_ctrl.get_idle_ratio()

    @staticmethod
    def reset():
        """Resets the recording status."""
        MySaver.total_processed = Counter()
        MySaver.total_requested = Counter()

    @staticmethod
    def save(data:bytes, destdir:str, name:str, ext:str, callback:staticmethod):
        """Saves a binary data to a file.

        :param data: Bytes data;
        :param destdir: Destination directory;
        :param name: File name (without the extension);
        :param ext: File extension;
        :param callback: Callback `f(whether_saved_this_file)`;
        :rtype: None;
        """
        MySaver.thread_ctrl.run_subthread(MySaver._save, (data, destdir, name, ext, callback), name=f"SaverThread:{id(data)}")
    
    @staticmethod
    def _save(data:bytes, destdir:str, name:str, ext:str, callback:staticmethod):
        MySaver.total_requested.update()
        try:
            dest = os.path.join(destdir, name)
            name = os.path.basename(dest)
            destdir = os.path.dirname(dest)
            if SafeSaver.__is_unique(data, destdir, name, ext):
                dest = SafeSaver.__no_namesake(destdir, name, ext)
                SafeSaver._save_bytes(data, dest)
                if callback:
                    callback(True)
            else:
                if callback:
                    callback(False)
        except Exception as arg:
            Logger.error(f"Saver: Failed to save file {dest} because: Exception{type(arg)} {arg}")
        MySaver.total_processed.update()

    @staticmethod
    def _save_bytes(data:bytes, dest:str):
        mkdir(os.path.dirname(dest))
        with open(dest, 'wb') as f:
            f.write(data)

    @staticmethod
    def __is_same(data:bytes, fp:str):
        with open(fp, 'rb') as f:
            cache = f.read()
        return True if bytes(data) == bytes(cache) else False

    @staticmethod
    def __is_unique(data:bytes, destdir:str, name:str, ext:str):
        if os.path.isdir(destdir):
            lenname = len(name)
            flist = os.listdir(destdir)
            flist = list(filter(lambda x:(name == x[:lenname] and ext in x), flist)) #初筛
            for i in flist:
                if SafeSaver.__is_same(data, os.path.join(destdir, i)):
                    return False
        return True

    @staticmethod
    def __no_namesake(destdir:str, name:str, ext:str):
        tmp = 0
        dest = os.path.join(destdir, f'{name}{ext}')
        while os.path.isfile(dest):
            dest = os.path.join(destdir, f'{name}_#{tmp}{ext}')
            tmp += 1
        return dest
    #EndClass

class MySaver(SafeSaver):
    """The implemented saver."""

    @staticmethod
    def save_image(IM:Image.Image, destdir:str, name:str, ext:str='.png', callback:staticmethod=None):
        """Saves an image.

        :param IM: `PIL.Image` instance;
        :param destdir: Destination directory;
        :param name: File name (without the extension);
        :param ext: File extension;
        :param callback: Callback `f(whether_saved_this_file)`;
        :returns: Whether saved this file;
        :rtype: bool;
        """
        ext = ext.lower()
        if ext not in ['.png', '.jpg', '.jpeg', '.bmp']:
            return False
        if IM.height <= 0 and IM.width <= 0:
            return False
        byt = BytesIO()
        IM.save(byt, format = ('PNG' if ext == '.png' else 'JPEG'))
        byt = byt.getvalue()
        SafeSaver.save(byt, destdir, name, ext, callback)
        return True

    @staticmethod
    def save_script(byt:bytes, destdir:str, name:str, ext:str='', callback:staticmethod=None):
        """Saves a binary file.

        :param byt: Bytes data;
        :param destdir: Destination directory;
        :param name: File name (without the extension);
        :param ext: File extension;
        :param callback: Callback `f(whether_saved_this_file)`;
        :returns: Whether saved this file;
        :rtype: bool;
        """
        ext = ext.lower()
        if not byt:
            return False
        SafeSaver.save(byt, destdir, name, ext, callback)
        return True

    @staticmethod
    def save_samples(items:bytes, destdir:str, name:str, ext:str='', callback:staticmethod=None):
        """Saves a audio file with the sample items list.

        :param items: Audio sample items list;
        :param destdir: Destination directory;
        :param name: File name (without the extension);
        :param ext: File extension;
        :param callback: Callback `f(whether_saved_this_file)`;
        :returns: Whether saved this file;
        :rtype: bool;
        """
        ext = ext.lower()
        byt = bytes()
        for n, d in items:
            byt += d
        if not byt:
            return False
        SafeSaver.save(byt, destdir, name, ext, callback)
        return True
    #EndClass
