# -*- coding: utf-8 -*-
# Copyright (c) 2022-2024, Harry Huang
# @ BSD 3-Clause License
import os
from io import BytesIO
from PIL import Image
from UnityPy.classes import *
from .Config import *
from .GlobalMethods import *
from .Logger import *
from .TaskUtils import *


class SafeSaver(WorkerCtrl):
    """The base class for file saver which is able to avoid name collision."""

    __instance  = None
    __ext_image = 'png'
    __ext_audio = 'wav'
    __ext_raw   = ''

    def __init__(self):
        """Not recommended to use. Please use the static methods."""
        max_workers = PerformanceLevel.get_thread_limit(Config.get('performance_level'))
        super(SafeSaver, self).__init__(self._save, max_workers=max_workers, name="Saver")

    @staticmethod
    def get_instance():
        if not SafeSaver.__instance:
            SafeSaver.__instance = SafeSaver()
        return SafeSaver.__instance

    @staticmethod
    def save_bytes(data:bytes, destdir:str, name:str, ext:str, callback:staticmethod=None):
        """Saves a binary data to a file.

        :param data: Bytes data;
        :param destdir: Destination directory;
        :param name: File name (without the extension);
        :param ext: File extension;
        :param callback: Callback `f(file_path_or_none_for_not_saved)`, `None` for ignore;
        :rtype: None;
        """
        SafeSaver.get_instance().submit((data, destdir, name, ext, callback))
    
    @staticmethod
    def save_image(img:Image.Image, destdir:str, name:str, ext:str=__ext_image, callback:staticmethod=None):
        """Saves an image to a file.

        :param img: Image instance;
        :param destdir: Destination directory;
        :param name: File name (without the extension);
        :param ext: File extension, `png` for default;
        :param callback: Callback `f(file_path_or_none_for_not_saved)`, `None` for ignore;
        :rtype: None;
        """
        bio = BytesIO()
        img.save(bio, format=ext)
        SafeSaver.save_bytes(bio.getvalue(), destdir, name, ext, callback)
    
    @staticmethod
    def save_object(obj:GameObject, destdir:str, name:str, callback:staticmethod=None):
        """Saves the given Unity GameObject as a file. If a GameObject is not exportable, it does nothing.

        :param obj: The GameObject to save as file;
        :param destdir: Destination directory;
        :param name: File name (without the extension);
        :param callback: Callback `f(file_path_or_none_for_not_saved)`, `None` for ignore;
        :rtype: None;
        """
        if obj.byte_size == 0:
            # No data:
            pass
        elif isinstance(obj, (Sprite, Texture2D)):
            # As image file:
            if obj.image.width > 0 and obj.image.height > 0:
                SafeSaver.save_image(obj.image, destdir, name, SafeSaver.__ext_image, callback)
                return
        elif isinstance(obj, AudioClip):
            # As audio file:
            if len(obj.samples) > 0:
                byte = bytes()
                for _, d in obj.samples.items():
                    byte += d
                SafeSaver.save_bytes(byte, destdir, name, SafeSaver.__ext_audio, callback)
                return
        elif isinstance(obj, TextAsset):
            # As raw file:
            byte = bytes(obj.script)
            SafeSaver.save_bytes(byte, destdir, name, SafeSaver.__ext_raw, callback)
            return
        else:
            # Not an exportable type:
            pass
        if callback:
            callback(None)
    
    @staticmethod
    def save_objects(lst:"list[GameObject]", destdir:str, callback:staticmethod):
        """Saves all the Unity GameObjects in the given list as files. If a GameObject is not exportable, it does nothing.

        :param lst: The GameObjects list;
        :param destdir: Destination directory;
        :param callback: Callback `f(game_object_name, file_path_or_none_for_not_saved)` for every saving trail, `None` for ignore;
        :rtype: None;
        """
        if callback:
            for i in lst:
                SafeSaver.save_object(i, destdir, i.name, lambda x: callback(i.name, x))
        else:
            for i in lst:
                SafeSaver.save_object(i, destdir, i.name)
    
    @staticmethod
    def _save(data:bytes, destdir:str, name:str, ext:str, callback:staticmethod):
        try:
            dest = os.path.join(destdir, name)
            name = os.path.basename(dest)
            destdir = os.path.dirname(dest)
            if SafeSaver._is_unique(data, destdir, name, ext):
                dest = SafeSaver._no_namesake(destdir, name, ext)
                SafeSaver._save_bytes(data, dest)
                if callback:
                    callback(dest)
            else:
                if callback:
                    callback(None)
        except Exception as arg:
            Logger.error(f"Saver: Failed to save file {dest} because: Exception{type(arg)} {arg}")

    @staticmethod
    def _save_bytes(data:bytes, dest:str):
        mkdir(os.path.dirname(dest))
        with open(dest, 'wb') as f:
            f.write(data)

    @staticmethod
    def _is_same(data:bytes, fp:str):
        with open(fp, 'rb') as f:
            cache = f.read()
        return True if bytes(data) == bytes(cache) else False

    @staticmethod
    def _is_unique(data:bytes, destdir:str, name:str, ext:str):
        if os.path.isdir(destdir):
            lenname = len(name)
            flist = os.listdir(destdir)
            flist = list(filter(lambda x:(name == x[:lenname] and ext in x), flist)) #初筛
            for i in flist:
                if SafeSaver._is_same(data, os.path.join(destdir, i)):
                    return False
        return True

    @staticmethod
    def _no_namesake(destdir:str, name:str, ext:str):
        tmp = 0
        dest = os.path.join(destdir, f'{name}.{ext}')
        while os.path.isfile(dest):
            dest = os.path.join(destdir, f'{name}_#{tmp}.{ext}')
            tmp += 1
        return dest
    #EndClass
