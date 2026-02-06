# Copyright (c) 2022-2026, Harry Huang
# @ BSD 3-Clause License
from typing import Callable, List, Optional

import os
import os.path as osp

import ffmpeg
from wannacri import usm

from .utils.GlobalMethods import get_filelist, is_usm_file, print, rmdir, stacktrace
from .utils.Logger import Logger
from .utils.SaverUtils import SafeSaver
from .utils.TaskUtils import ThreadCtrl, UICtrl, TaskReporter, TaskReporterTracker
from .utils.Config import Config


FFMPEG_RUN_PARAMS = {"quiet": True}


def is_ffmpeg_available() -> bool:
    """Checks if FFmpeg is available.
    This will create a small test video file and delete it afterwards.

    :returns: True if FFmpeg is available, False otherwise;
    :rtype: bool;
    """
    test_file = "ArkUnpackerFFmpegTest.mp4"
    try:
        s_in = ffmpeg.input("testsrc=duration=1:size=320x240:rate=1", f="lavfi")
        s_out = s_in.output(test_file, vcodec="h264", acodec="aac", t=1, y=None)
        s_out.run(**FFMPEG_RUN_PARAMS)
        return True
    except Exception:
        return False
    finally:
        try:
            if osp.exists(test_file):
                os.unlink(test_file)
        except Exception:
            pass


class UsmProcessor:
    """USM file processor for parsing and exporting Criware USM format video files."""

    def __init__(self, usm_path: str, encoding: str = "utf-8"):
        """Initializes the USM processor.

        :param usm_path: Path to the USM file;
        :param encoding: Encoding for the USM file;
        :rtype: None;
        """
        self._usm_path = usm_path
        self._encoding = encoding
        self.usm_obj: Optional[usm.Usm] = None
        self.video_paths: List[str] = []
        self.audio_paths: List[str] = []

    def load_usm(self):
        """Loads the USM file."""
        try:
            self.usm_obj = usm.Usm.open(self._usm_path, encoding=self._encoding)
            Logger.info(f'ResolveUSM: USM file loaded successfully: "{self._usm_path}"')
        except Exception as e:
            Logger.error(f'ResolveUSM: Failed to load USM file "{self._usm_path}": {stacktrace()}')
            raise e

    def extract_media(self, output_dir: str):
        """Extracts video and audio streams.
        The extracted video and audio files are encoded with the original codecs.

        :param output_dir: Output directory;
        :rtype: None;
        """
        if not self.usm_obj:
            self.load_usm()

        if self.usm_obj is None:
            raise ValueError("USM object loading failed")

        try:
            self.video_paths, self.audio_paths = self.usm_obj.demux(
                path=output_dir,
                save_video=True,
                save_audio=True,
                save_pages=False,
                folder_name=osp.splitext(osp.basename(self._usm_path))[0],
            )
            Logger.debug(
                f'ResolveUSM: Media extraction completed for "{self._usm_path}": {len(self.video_paths)} videos, {len(self.audio_paths)} audios'
            )
        except Exception as e:
            Logger.error(f'ResolveUSM: Media extraction failed for "{self._usm_path}": {stacktrace()}')
            raise e

    def convert_formats(
        self,
        output_dir: str,
        *,
        v: bool,
        a: bool,
        v_codec: str,
        a_codec: str,
        v_ext: str,
        a_ext: str,
    ):
        """Converts the formats of the extracted media files.

        :param output_dir: Output directory;
        :param v: Whether to process video files;
        :param a: Whether to process audio files;
        :param v_codec: Video codec to use;
        :param a_codec: Audio codec to use;
        :param v_ext: Video file extension;
        :param a_ext: Audio file extension;
        :rtype: None;
        """
        if not v and not a:
            return

        if v and not a:
            # Request to convert video only (silent video)
            for video_path in self.video_paths:
                out_path = osp.join(output_dir, f"{osp.splitext(osp.basename(video_path))[0]}{v_ext}")
                try:
                    ffmpeg.input(video_path).output(
                        out_path,
                        vcodec=v_codec,
                        y=None,
                    ).run(**FFMPEG_RUN_PARAMS)
                    Logger.debug(f'ResolveUSM: Conversion (v) completed: "{out_path}"')
                except ffmpeg.Error as e:
                    Logger.error(f'ResolveUSM: Conversion (v) failed for "{video_path}": {stacktrace()}')
                    raise e

        elif not v and a:
            # Request to convert audio only
            for audio_path in self.audio_paths:
                out_path = osp.join(output_dir, f"{osp.splitext(osp.basename(audio_path))[0]}{a_ext}")
                try:
                    ffmpeg.input(audio_path).output(
                        out_path,
                        acodec=a_codec,
                        y=None,
                    ).run(**FFMPEG_RUN_PARAMS)
                    Logger.debug(f'ResolveUSM: Conversion (a) completed: "{out_path}"')
                except ffmpeg.Error as e:
                    Logger.error(f'ResolveUSM: Conversion (a) failed for "{audio_path}": {stacktrace()}')
                    raise e

        else:
            # Request to convert both video and audio
            if len(self.audio_paths) == 0:
                # No audio files, convert video only
                for video_path in self.video_paths:
                    out_path = osp.join(
                        output_dir,
                        f"{osp.splitext(osp.basename(video_path))[0]}{v_ext}",
                    )
                    try:
                        ffmpeg.input(video_path).output(
                            out_path,
                            vcodec=v_codec,
                            y=None,
                        ).run(**FFMPEG_RUN_PARAMS)
                        Logger.debug(f'ResolveUSM: Conversion (v) completed: "{out_path}"')
                    except ffmpeg.Error as e:
                        Logger.error(f'ResolveUSM: Conversion (v) failed for "{video_path}": {stacktrace()}')
                        raise e
            elif len(self.video_paths) == len(self.audio_paths):
                # Equal counts, merge them sequentially
                for video_path, audio_path in zip(self.video_paths, self.audio_paths):
                    out_path = osp.join(
                        output_dir,
                        f"{osp.splitext(osp.basename(video_path))[0]}{v_ext}",
                    )

                    try:
                        # Concat video and audio
                        ffmpeg.concat(
                            ffmpeg.input(video_path),
                            ffmpeg.input(audio_path),
                            v=1,
                            a=1,
                        ).output(
                            out_path,
                            vcodec=v_codec,
                            acodec=a_codec,
                            y=None,
                        ).run(**FFMPEG_RUN_PARAMS)
                        Logger.debug(f'ResolveUSM: Conversion (va) completed: "{out_path}"')
                    except ffmpeg.Error as e:
                        Logger.error(
                            f'ResolveUSM: Conversion (va) failed for "{video_path}" + "{audio_path}": {stacktrace()}'
                        )
                        raise e
            else:
                # Mismatched counts and audio is not empty
                raise ValueError("Mismatched video and audio counts")


def process_usm_file(
    usm_file_path: str,
    destdir: str,
    do_vid: bool = True,
    do_aud: bool = True,
    on_processed: Optional[Callable] = None,
    on_converting: Optional[Callable] = None,
    on_converted: Optional[Callable] = None,
):
    """Processes a single USM file.

    :param usm_file_path: USM file path;
    :param destdir: Destination directory;
    :param do_vid: Whether to process video files;
    :param do_aud: Whether to process audio files;
    :param on_processed: Callback function when a usm file processed, `None` to ignore;
    :param on_converting: Callback function when a format conversion started, `None` to ignore;
    :param on_converted: Callback function when a format conversion completed, `None` to ignore;
    :rtype: None;
    """
    try:
        processor = UsmProcessor(usm_file_path, encoding=Config.get("usm_encoding"))

        # Create output subdirectory
        os.makedirs(destdir, exist_ok=True)

        # Extract media
        processor.extract_media(destdir)
        if on_converting:
            on_converting()

        # Convert formats
        processor.convert_formats(
            destdir,
            v=do_vid,
            a=do_aud,
            v_codec=Config.get("usm_export_video_codec"),
            a_codec=Config.get("usm_export_audio_codec"),
            v_ext=Config.get("usm_export_video_ext"),
            a_ext=Config.get("usm_export_audio_ext"),
        )
        if on_converted:
            on_converted()

        Logger.info(f'ResolveUSM: USM file processing completed: "{usm_file_path}"')

    except Exception:
        Logger.error(f'ResolveUSM: USM file processing failed for "{usm_file_path}": {stacktrace()}')

    if on_processed:
        on_processed()


########## Main-主程序 ##########
def main(
    rootdir: str,
    destdir: str,
    do_del: bool = False,
    do_vid: bool = True,
    do_aud: bool = True,
):
    """Batch processes all Criware USM files in the directory.

    :param rootdir: Source directory;
    :param destdir: Destination directory;
    :param do_del: Whether to delete the existing destination directory first, `False` for default;
    :param do_vid: Whether to process video files, `True` for default;
    :param do_aud: Whether to process audio files, `True` for default;
    :rtype: None;
    """
    print("\n正在解析路径...", s=1)
    Logger.info("ResolveUSM: Retrieving USM file paths...")
    rootdir = osp.normpath(osp.realpath(rootdir))
    destdir = osp.normpath(osp.realpath(destdir))
    flist = get_filelist(rootdir)
    flist = list(filter(is_usm_file, flist))

    if do_del:
        print("\n正在清理目标目录...", s=1)
        rmdir(destdir)

    Logger.reset_stats()
    SafeSaver.get_instance().reset_counter()
    thread_ctrl = ThreadCtrl()
    ui = UICtrl()
    tr_processed = TaskReporter(1, len(flist))
    tr_converted = TaskReporter(1)
    tracker = TaskReporterTracker(tr_processed)

    ui.reset()
    ui.loop_start()

    for i in flist:
        ui.request(
            [
                "正在批量处理Criware USM文件...",
                tracker.to_progress_bar_str(),
                f"当前目录：\t{osp.basename(osp.dirname(i))}",
                f"当前文件：\t{osp.basename(i)}",
                f"累计处理：\t{tr_processed.to_progress_str()}",
                f"累计转换：\t{tr_converted.to_progress_str()}",
                f"预计剩余时间：\t{tracker.to_eta_str()}",
                f"累计消耗时间：\t{tracker.to_rt_str()}",
                f"运行状态统计：\t{Logger.to_ew_stats_str()}",
            ]
        )

        thread_ctrl.run_subthread(
            process_usm_file,
            (
                i,
                osp.join(destdir, osp.relpath(os.path.splitext(i)[0], rootdir)),
                do_vid,
                do_aud,
                tr_processed.report,
                tr_converted.update_demand,
                tr_converted.report,
            ),
            name=f"USMThread:{id(i)}",
        )

    ui.reset()
    ui.loop_stop()

    while thread_ctrl.count_subthread() or not SafeSaver.get_instance().completed() or tracker.get_progress() < 1:
        ui.request(
            [
                "正在批量处理Criware USM文件...",
                tracker.to_progress_bar_str(),
                f"累计处理：\t{tr_processed.to_progress_str()}",
                f"累计转换：\t{tr_converted.to_progress_str()}",
                f"预计剩余时间：\t{tracker.to_eta_str()}",
                f"累计消耗时间：\t{tracker.to_rt_str()}",
                f"运行状态统计：\t{Logger.to_ew_stats_str()}",
            ]
        )
        ui.refresh(post_delay=0.1)

    ui.reset()
    print("\n批量处理Criware USM文件结束!", s=1)
    print(f"  累计处理 {tr_processed.get_done()} 个文件")
    print(f"  累计转换 {tr_converted.get_done()} 个媒体文件")
    print(f"  此项用时 {round(tracker.get_rt(), 1)} 秒")
