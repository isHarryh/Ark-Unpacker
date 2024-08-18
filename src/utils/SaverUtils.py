# -*- coding: utf-8 -*-
# Copyright (c) 2022-2024, Harry Huang
# @ BSD 3-Clause License
import os
import os.path as osp
import threading
from io import BytesIO
from contextlib import ContextDecorator

import UnityPy.classes as uc
from PIL import Image
from .AnalyUtils import TestRT
from .Config import Config, PerformanceLevel
from .GlobalMethods import mkdir
from .Logger import Logger
from .TaskUtils import WorkerCtrl


class EntryLock(ContextDecorator):
    """The entry lock class to prevent simultaneous access to the same entry."""

    _ENTRIES = set()
    _INTERNAL_LOCK = threading.Condition()

    def __init__(self, entry):
        self.entry = entry

    def __enter__(self):
        with EntryLock._INTERNAL_LOCK:
            while self.entry in EntryLock._ENTRIES:
                EntryLock._INTERNAL_LOCK.wait()
            EntryLock._ENTRIES.add(self.entry)

    def __exit__(self, exc_type, exc_val, exc_tb):
        with EntryLock._INTERNAL_LOCK:
            EntryLock._ENTRIES.discard(self.entry)
            EntryLock._INTERNAL_LOCK.notify_all()
    #EndClass

class SafeSaver(WorkerCtrl):
    """The file saver class to save file and avoid file name collision."""

    __instance = None
    _EXT_IMAGE = '.png'
    _EXT_RAW = ''
    _AUDIO_ACCESS_LOCK = threading.Lock()

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
    def save_bytes(data:bytes, destdir:str, name:str, ext:str, on_queued:staticmethod=None, on_saved:staticmethod=None):
        """Saves a binary data to a file.

        :param data: Bytes data;
        :param destdir: Destination directory;
        :param name: File name (without the extension);
        :param ext: File extension;
        :param on_queued: Callback `f()` invoked when the file was queued, `None` for ignore;
        :param on_saved: Callback `f(file_path_or_none_for_not_saved)`, `None` for ignore;
        :rtype: None;
        """
        if on_queued:
            on_queued()
        SafeSaver.get_instance().submit((data, destdir, name, ext, on_saved))

    @staticmethod
    def save_image(img:Image.Image, destdir:str, name:str, ext:str=_EXT_IMAGE, on_queued:staticmethod=None, on_saved:staticmethod=None):
        """Saves an image to a file.

        :param img: Image instance;
        :param destdir: Destination directory;
        :param name: File name (without the extension);
        :param ext: File extension, `png` for default;
        :param on_queued: Callback `f()` invoked when the file was queued, `None` for ignore;
        :param on_saved: Callback `f(file_path_or_none_for_not_saved)`, `None` for ignore;
        :rtype: None;
        """
        bio = BytesIO()
        img.save(bio, format=ext.lstrip('.'))
        SafeSaver.save_bytes(bio.getvalue(), destdir, name, ext, on_queued, on_saved)

    @staticmethod
    def save_object(obj:uc.GameObject, destdir:str, name:str, on_queued:staticmethod=None, on_saved:staticmethod=None):
        """Saves the given Unity GameObject as a file. If a GameObject is not exportable, it does nothing.

        :param obj: The GameObject to save as file;
        :param destdir: Destination directory;
        :param name: File name (without the extension);
        :param on_queued: Callback `f()` invoked when the file was queued, `None` for ignore;
        :param on_saved: Callback `f(file_path_or_none_for_not_saved)`, `None` for ignore;
        :rtype: None;
        """
        if obj.byte_size == 0:
            # No data:
            pass
        elif isinstance(obj, (uc.Sprite, uc.Texture2D)):
            # As image file:
            if obj.image.width > 0 and obj.image.height > 0:
                SafeSaver.save_image(obj.image, destdir, name, SafeSaver._EXT_IMAGE, on_queued, on_saved)
                return
        elif isinstance(obj, uc.AudioClip):
            # As audio file:
            samples = None
            with SafeSaver._AUDIO_ACCESS_LOCK:
                samples = obj.samples
            if samples:
                for name, byte in samples.items():
                    SafeSaver.save_bytes(byte, destdir, name, SafeSaver._EXT_RAW, on_queued, on_saved)
            return
        elif isinstance(obj, uc.TextAsset):
            # As raw file:
            byte = bytes(obj.script)
            SafeSaver.save_bytes(byte, destdir, name, SafeSaver._EXT_RAW, on_queued, on_saved)
            return
        else:
            # Not an exportable type:
            pass

    @staticmethod
    def save_objects(lst:"list[uc.GameObject]", destdir:str, on_queued:staticmethod=None, on_saved:staticmethod=None):
        """Saves all the Unity GameObjects in the given list as files.
        If a GameObject is not exportable, it does nothing.

        :param lst: The GameObjects list;
        :param destdir: Destination directory;
        :param on_queued: Callback `f()` invoked when the file was queued, `None` for ignore;
        :param on_saved: Callback `f(file_path_or_none_for_not_saved)`, `None` for ignore;
        :rtype: None;
        """
        for i in lst:
            SafeSaver.save_object(i, destdir, i.name, on_queued, on_saved)

    @staticmethod
    def _save(data:bytes, destdir:str, name:str, ext:str, on_saved:staticmethod):
        try:
            dest = osp.join(destdir, name + ext)
            with TestRT('lock'):
                # Ensure files with identical name cannot be saved simultaneously
                with EntryLock(dest):
                    # Ensure this new file is unique to prevent duplication
                    if SafeSaver._is_unique(data, dest):
                        # Modify the file name to avoid namesake
                        dest = SafeSaver._no_namesake(dest)
                        # Save the file eventually
                        mkdir(osp.dirname(dest))
                        SafeSaver._save_bytes(data, dest)
                        # Invoke callback with destination path as argument
                        if on_saved:
                            on_saved(dest)
                            return
        except Exception as arg:
            Logger.error(f"Saver: Failed to save file {dest} because: Exception{type(arg)} {arg}")
        # Invoke call back with `None` indicating the file was not saved
        if on_saved:
            on_saved(None)

    @staticmethod
    def _save_bytes(data:bytes, dest:str):
        with open(dest, 'wb') as f:
            f.write(data)

    @staticmethod
    def _is_unique(data:bytes, dest:str):
        destdir = osp.dirname(dest)
        name, ext = osp.splitext(osp.basename(dest))
        if not osp.isdir(destdir):
            return True
        flist = filter(lambda x:x.startswith(name) and x.endswith(ext), os.listdir(destdir))
        for i in flist:
            with open(osp.join(destdir, i), 'rb') as f:
                if f.read() == data:
                    Logger.debug(f"Saver: File \"{i}\" duplication was prevented, size {len(data)}")
                    return False
        return True

    @staticmethod
    def _no_namesake(dest:str):
        destdir = osp.dirname(dest)
        name, ext = osp.splitext(osp.basename(dest))
        tmp = 0
        while osp.isfile(dest):
            dest = osp.join(destdir, f'{name}${tmp}{ext}')
            tmp += 1
        return dest
    #EndClass
