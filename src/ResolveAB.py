# Copyright (c) 2022-2026, Harry Huang
# @ BSD 3-Clause License
from typing import (
    Collection,
    Generator,
    List,
    Literal,
    Optional,
    Tuple,
    TypeVar,
    Union,
)
import glob
import os.path as osp
import multiprocessing as mp

import UnityPy
import UnityPy.classes as uc
from UnityPy.enums.BundleFile import CompressionFlags
from UnityPy.files.File import File, ObjectReader
from UnityPy.helpers import CompressionHelper
from UnityPy.streams.EndianBinaryReader import EndianBinaryReader

from .lz4ak.Block import decompress_lz4ak
from .mp.FsGuardProcess import FsGuardClient, FsGuardClientSlot, FsGuardProcess
from .mp.Messages import ResolveABTask, StopMessage
from .mp.Process import ProcessUtils
from .mp.ProcessResultBus import ProcessResultBus, ProcessResultSender
from .mp.ProcessReporter import ProcessReporter
from .ui.RichCLI import RichCLI
from .ui.TaskLive import TaskDetailField, TaskLiveView, TaskValueField
from .utils.GlobalMethods import rmdir, is_ab_file
from .utils.Config import Config, PerformanceLevel
from .utils.Logger import Logger
from .utils.SaverUtils import SafeSaver
from .utils.TaskUtils import TaskReporter, TaskReporterTracker

# New compression algorithm introduced in Arknights v2.5.04+
CompressionHelper.DECOMPRESSION_MAP[CompressionFlags.LZHAM] = decompress_lz4ak
CLI = RichCLI.get_instance()

_T = TypeVar("_T", bound=uc.Object)


class TreeReader:
    def __init__(self, obj: Optional[uc.Object]):
        self.obj = getattr(obj, "object_reader", obj)

    def __enter__(self):
        if self.obj is None:
            raise AttributeError("Given object or object reader is none")
        read_typetree = getattr(self.obj, "read_typetree", None)
        if callable(read_typetree):
            tree = read_typetree()
            if isinstance(tree, dict):
                return tree
        raise AttributeError("Given object has no serialized type tree")

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False


class Resource:
    """The class representing a collection of the objects in an UnityPy Environment."""

    def __init__(self, env: UnityPy.Environment):
        """Initializes with the given UnityPy Environment instance.

        :param env: The Environment instance from `UnityPy.load()`;
        :rtype: None;
        """
        if isinstance(env.file, File):
            self.name: str = env.file.name
        elif isinstance(env.file, EndianBinaryReader):
            self.name: str = ""
        else:
            raise TypeError(f"Unknown type of UnityPy Environment file: {type(env.file).__name__}")
        self.env: UnityPy.Environment = env
        self.length: int = len(env.objects)

        self._build_pathid_lut()
        self._build_type_lut()
        self._build_roi_type_lut()

        for obj in self.get_objects_by_type(uc.AssetBundle):
            if getattr(obj, "m_Name", None):
                if self.name != osp.basename(obj.m_Name):
                    Logger.debug(f'ResolveAB: Resource "{self.name}" internally named "{obj.m_Name}"')
                    self.name = osp.basename(obj.m_Name)

    def _build_pathid_lut(self):
        all_pathid = set()
        for reader in self.env.objects:
            all_pathid.add(reader.path_id)
        max_pathid = max(all_pathid) if all_pathid else 0

        self._lut_pathid: dict[int, Tuple[ObjectReader, Optional[uc.Object]]] = {}
        for reader in self.env.objects:
            if reader.path_id in self._lut_pathid:
                other_reader, _ = self._lut_pathid[reader.path_id]
                replace_pathid = max_pathid + 1
                max_pathid += 1
                Logger.info(
                    f'Resource: Duplicate PathID found when building LUT for "{self.name}"\n'
                    f"- Existing: {other_reader.peek_name()} ({other_reader.type.name}) PathID={other_reader.path_id}\n"
                    f"- Incoming: {reader.peek_name()} ({reader.type.name}) PathID={reader.path_id}"
                    f" (will be reassigned to {replace_pathid})"
                )
                reader.path_id = replace_pathid
            self._lut_pathid[reader.path_id] = (reader, None)

    def _build_type_lut(self):
        self._lut_type: dict[str, List[int]] = {}
        for reader in self.env.objects:
            clz = reader.get_class()
            if not clz:
                continue
            if clz.__name__ not in self._lut_type:
                self._lut_type[clz.__name__] = []
            self._lut_type[clz.__name__].append(reader.path_id)

    def _build_roi_type_lut(self):
        self._lut_roi_type: dict[str, List[int]] = {}
        for reader in self.env.objects:
            clz = reader.get_class()
            if not clz:
                continue
            if issubclass(clz, uc.Sprite) or issubclass(clz, uc.Texture2D):
                roi = "Image"
            elif issubclass(clz, uc.TextAsset) and not issubclass(clz, uc.MonoScript):
                roi = "Text"
            elif issubclass(clz, uc.AudioClip):
                roi = "Audio"
            elif issubclass(clz, uc.Mesh):
                roi = "Mesh"
            elif issubclass(clz, uc.AssetBundle):
                roi = "AssetBundle"
            else:
                continue
            if roi not in self._lut_roi_type:
                self._lut_roi_type[roi] = []
            self._lut_roi_type[roi].append(reader.path_id)

    def try_get_object_by_pathid(
        self,
        pathid: Union[int, dict],
        assert_type: type[_T] = uc.Object,
    ) -> Optional[_T]:
        """Tries to get the object with the given PathID.

        :param pathid: PathID in int or a dict containing `m_PathID` field;
        :param assert_type: The expected type of the object;
        :returns: The first object matching the PathID and type, or `None` if failed;
        """
        try:
            return self.get_object_by_pathid(pathid, assert_type)
        except (KeyError, TypeError):
            return None

    def get_object_by_pathid(
        self,
        pathid: Union[int, dict],
        assert_type: type[_T] = uc.Object,
    ) -> _T:
        """Gets the object with the given PathID.

        :param pathid: PathID in int or a dict containing `m_PathID` field;
        :param assert_type: The expected type of the object;
        :returns: The first object matching the PathID and type;
        """
        if not self.env:
            raise RuntimeError("Environment has been disposed or not initialized")
        if isinstance(pathid, dict):
            if "m_PathID" not in pathid:
                raise KeyError(f"Given dict does not contain m_PathID field")
            pid = pathid["m_PathID"]
        elif isinstance(pathid, int):
            pid = pathid
        else:
            raise TypeError(f"Argument pathid must be int or dict")
        if pid not in self._lut_pathid:
            raise KeyError(f"Object with PathID {pid} not found")
        reader, obj = self._lut_pathid[pid]
        if obj is None:
            obj = reader.read()
            self._lut_pathid[pid] = (reader, obj)
        if not isinstance(obj, assert_type):
            raise TypeError(f"Object with PathID {pid} is not of type {assert_type}, but {type(obj).__name__}")
        return obj

    def get_objects_by_type(self, obj_type: type[_T]) -> Generator[_T, None, None]:
        """Gets all the objects of the given type.

        :param obj_type: The expected type of the objects;
        :returns: A generator of the objects;
        """
        if not self.env:
            raise RuntimeError("Environment has been disposed or not initialized")
        tn = obj_type.__name__
        if tn not in self._lut_type:
            return
        for pid in self._lut_type[tn]:
            reader, obj = self._lut_pathid[pid]
            if obj is None:
                obj = reader.read()
                self._lut_pathid[pid] = (reader, obj)
            if obj is not None:
                yield obj  # type: ignore

    def get_objects_by_roi_type(
        self, roi_type: Literal["Image", "Text", "Audio", "Mesh", "AssetBundle"]
    ) -> Generator[uc.Object, None, None]:
        """Gets all the objects of the given ROI type.

        :param roi_type: The expected ROI type of the objects;
        :returns: A generator of the objects;
        """
        if not self.env:
            raise RuntimeError("Environment has been disposed or not initialized")
        if roi_type not in self._lut_roi_type:
            return
        for pid in self._lut_roi_type[roi_type]:
            reader, obj = self._lut_pathid[pid]
            if obj is None:
                obj = reader.read()
                self._lut_pathid[pid] = (reader, obj)
            if obj is not None:
                yield obj

    def find_object_and_typetree_with_key(
        self, obj_type: type[_T], contains_keys: Collection[str]
    ) -> Generator[Tuple[_T, dict], None, None]:
        """Finds all the objects of the given type whose typetree contains all the given keys.

        :param obj_type: The expected type of the objects;
        :param contains_keys: The collection of keys that the typetree should contain;
        :returns: A generator of tuples of the object and its typetree;
        """
        if not self.env:
            raise RuntimeError("Environment has been disposed or not initialized")
        for obj in self.get_objects_by_type(obj_type):
            with TreeReader(obj) as tree:
                if all(k in tree for k in contains_keys):
                    yield (obj, tree)


class ResolveABWorkerSession:
    def __init__(
        self,
        reporter: ProcessReporter,
        fs_client: FsGuardClient,
        export_encoding: str,
        export_json_indent: int,
    ):
        self._reporter = reporter
        self._fs_client = fs_client
        self._export_encoding = export_encoding
        self._export_json_indent = export_json_indent

    def log(self, level: str, msg: str):
        self._reporter.log(level, msg)

    def processed(self, success: bool = True):
        self._reporter.processed(success)

    def worker_done(self):
        self._reporter.worker_done()

    def save_item(self, item: SafeSaver.ExportItem, destdir: str):
        dest = self._fs_client.prepare_write(
            destdir,
            item.name,
            item.ext,
            SafeSaver.hash_data(item.data),
        )
        if dest is None:
            self._reporter.file_saved(False)
            return
        try:
            SafeSaver.write_data(dest, item.data)
            self._reporter.file_saved(True)
        except Exception as arg:
            self.log("error", f'ResolveAB: Failed to write file "{dest}": {arg}')
            self._reporter.file_saved(False)

    def save_object(self, obj: uc.Object, destdir: str):
        try:
            for item in SafeSaver.iter_object_export_items(obj):
                self.save_item(item, destdir)
        except Exception as arg:
            self.log(
                "warn", f"ResolveAB: Failed to export {type(obj).__name__} '{getattr(obj, 'm_Name', 'Unknown')}': {arg}"
            )

    def save_json(self, data: dict, destdir: str, name: str):
        self.save_item(
            SafeSaver.ExportItem(
                name,
                ".json",
                SafeSaver.serialize_json_data(data, self._export_encoding, self._export_json_indent),
            ),
            destdir,
        )


def _resolve_ab_task(
    abfile: str,
    destdir: str,
    do_img: bool,
    do_txt: bool,
    do_aud: bool,
    do_mesh: bool,
    do_tree: bool,
    session: ResolveABWorkerSession,
):
    from .ResolveSpine import SpineAsset

    if not osp.isfile(abfile):
        session.processed()
        return

    try:
        with open(abfile, "rb") as f:
            res = Resource(UnityPy.load(f))

            if res.length >= 10000:
                session.log(
                    "info", f'ResolveAB: Too many objects in file "{res.name}", unpacking it may take a long time.'
                )
            elif res.length == 0:
                session.log("info", f'ResolveAB: No object in file "{res.name}".')

            for s in SpineAsset.from_resource(res):
                s.process_path()

            for roi_flag, roi_type in [
                (do_img, "Image"),
                (do_txt, "Text"),
                (do_aud, "Audio"),
                (do_mesh, "Mesh"),
            ]:
                if roi_flag:
                    for obj in res.get_objects_by_roi_type(roi_type):  # type: ignore
                        session.save_object(obj, destdir)

            # Export typetrees as JSON
            if do_tree:
                typetrees = {}
                for obj in res.env.objects:
                    if hasattr(obj, "read_typetree"):
                        try:
                            tree = obj.read_typetree()
                            if tree:
                                typetrees[str(obj.path_id)] = tree
                        except Exception as e:
                            session.log(
                                "debug", f"ResolveAB: Failed to read typetree for {obj.type.name}_{obj.path_id}: {e}"
                            )

                if typetrees:
                    result = {res.name: typetrees}
                    session.save_json(result, destdir, f"TT_{res.name}")
    except BaseException as arg:
        session.log("error", f'ResolveAB: Error occurred while unpacking file "{abfile}": Exception{type(arg)} {arg}')
    session.processed()


def _worker_loop(
    task_queue: mp.Queue,
    fs_client_slot: FsGuardClientSlot,
    result_sender: ProcessResultSender,
    export_encoding: str,
    export_json_indent: int,
):
    reporter = result_sender.create_reporter()
    Logger.set_forwarder(reporter.log)
    fs_client = fs_client_slot.create_client(reporter)
    session = ResolveABWorkerSession(
        reporter,
        fs_client,
        export_encoding,
        export_json_indent,
    )
    while True:
        task = task_queue.get()
        if isinstance(task, StopMessage):
            break
        if not isinstance(task, ResolveABTask):
            reporter.log("warn", f'ResolveAB: Ignoring unexpected worker task type "{type(task).__name__}"')
            continue
        _resolve_ab_task(
            task.abfile,
            task.destdir,
            task.do_img,
            task.do_txt,
            task.do_aud,
            task.do_mesh,
            task.do_tree,
            session,
        )
    session.worker_done()


########## Main-主程序 ##########
def main(
    src: str,
    destdir: str,
    do_del: bool = False,
    do_img: bool = True,
    do_txt: bool = True,
    do_aud: bool = True,
    do_mesh: bool = True,
    do_tree: bool = False,
    separate: bool = True,
):
    """Extract all the AB files from the given directory or extract a given AB file.

    :param src: Source directory or file;
    :param destdir: Destination directory;
    :param do_del: Whether to delete the existing files in the destination directory, `False` for default;
    :param do_img: Whether to extract images;
    :param do_txt: Whether to extract text scripts;
    :param do_aud: Whether to extract audios;
    :param do_mesh: Whether to extract mesh;
    :param do_tree: Whether to export typetrees as JSON;
    :param separate: Whether to sort the extracted files by their source AB file path.
    :rtype: None;
    """
    Logger.reset_stats()

    tr_processed = TaskReporter(50, 1)
    tr_file_saving = TaskReporter(1)
    tracker = TaskReporterTracker(tr_processed, tr_file_saving)
    current_stage = TaskValueField("阶段", "正在解析路径")
    current_dir = TaskValueField("当前目录")
    panel = TaskLiveView("正在批量解包...")
    panel.set_detail_fields(
        [
            current_stage,
            current_dir,
            TaskDetailField("累计解包", tr_processed.to_progress_str),
            TaskDetailField("累计导出", tr_file_saving.to_progress_str),
            TaskDetailField("运行状态统计", Logger.to_ew_stats_str),
        ]
    )
    panel.bind_tracker(tracker)
    panel.start()

    try:
        Logger.info("ResolveAB: Retrieving file paths...")
        src = osp.normpath(osp.realpath(src))
        destdir = osp.normpath(osp.realpath(destdir))
        flist = [src] if osp.isfile(src) else []
        if osp.isdir(src):
            for i in glob.iglob(osp.join(glob.escape(src), "**", "*"), recursive=True):
                if osp.isfile(i) and is_ab_file(i):
                    flist.append(i)
        tr_processed.update_demand(len(flist) - 1)

        if do_del:
            current_stage.set_value("正在清理目标目录")
            panel.update()
            rmdir(destdir)  # Danger zone

        if not flist:
            current_stage.set_value("未找到可处理文件")
            panel.update()
            CLI.show_summary("批量解包结束", [("结果", "没有找到符合解包条件的文件。")], border_style="yellow")
            return

        ctx = mp.get_context("spawn")
        worker_count = min(len(flist), PerformanceLevel.get_process_limit(Config.get("performance_level")))
        Logger.info(f"ResolveAB: Using {worker_count} worker processes for {len(flist)} files")

        task_queue: mp.Queue = ctx.Queue(maxsize=max(64, worker_count * 8))
        result_bus = ProcessResultBus(ctx)
        result_sender = result_bus.create_sender()

        fs_guard = FsGuardProcess(
            ctx,
            result_sender,
            worker_count,
            request_queue_maxsize=max(2, min(8, worker_count)),
        )
        export_encoding = Config.get("export_encoding")
        export_json_indent = Config.get("export_json_indent")
        workers = [
            ctx.Process(
                target=_worker_loop,
                args=(
                    task_queue,
                    fs_guard.create_client_slot(idx),
                    result_sender,
                    export_encoding,
                    export_json_indent,
                ),
                name=f"RsWorker:{idx}",
                daemon=True,
            )
            for idx in range(worker_count)
        ]
        ProcessUtils.start_all(fs_guard, *workers)
        current_stage.set_value("正在分发任务")

        worker_done = set()
        fs_guard_done = False
        fs_guard_stop_sent = False
        fatal_error = None

        def _set_fs_guard_done(_pid: int):
            nonlocal fs_guard_done
            fs_guard_done = True

        result_bus = (
            result_bus.set_on_file_queued(tr_file_saving.update_demand)
            .set_on_file_saved(tr_file_saving.report)
            .set_on_processed(tr_processed.report)
            .set_on_worker_done(worker_done.add)
            .set_on_fs_guard_done(_set_fs_guard_done)
            .set_on_log(Logger.log)
        )

        for i in flist:
            current_dir.set_value(osp.basename(osp.dirname(i)))
            panel.update()
            curdestdir = (
                destdir
                if osp.samefile(i, src)
                else (
                    osp.join(
                        destdir,
                        osp.relpath(osp.dirname(i), src),
                        osp.splitext(osp.basename(i))[0],
                    )
                    if separate
                    else osp.join(destdir, osp.relpath(osp.dirname(i), src))
                )
            )
            task_queue.put(
                ResolveABTask(
                    abfile=i,
                    destdir=curdestdir,
                    do_img=do_img,
                    do_txt=do_txt,
                    do_aud=do_aud,
                    do_mesh=do_mesh,
                    do_tree=do_tree,
                )
            )
            result_bus.drain(timeout=0.0)
            for worker in workers:
                if worker.exitcode is not None and worker.pid not in worker_done:
                    if worker.exitcode != 0:
                        fatal_error = f'Worker process "{worker.name}" exited unexpectedly with code {worker.exitcode}'
                        Logger.error(f"ResolveAB: {fatal_error}")
                    worker_done.add(worker.pid)
            if fatal_error:
                break

        for _ in workers:
            task_queue.put(StopMessage())

        current_stage.set_value("正在处理任务")
        current_dir.set_value(None)

        while len(worker_done) < len(workers) or not fs_guard_done:
            result_bus.drain(timeout=0.1)

            for worker in workers:
                if worker.exitcode is not None and worker.pid not in worker_done:
                    if worker.exitcode != 0:
                        fatal_error = f'Worker process "{worker.name}" exited unexpectedly with code {worker.exitcode}'
                        Logger.error(f"ResolveAB: {fatal_error}")
                    worker_done.add(worker.pid)

            if len(worker_done) == len(workers) and not fs_guard_stop_sent:
                fs_guard.stop()
                fs_guard_stop_sent = True

            if fs_guard.exitcode is not None and not fs_guard_done:
                if fs_guard.exitcode != 0:
                    fatal_error = f"FsGuard process exited unexpectedly with code {fs_guard.exitcode}"
                    Logger.error(f"ResolveAB: {fatal_error}")
                fs_guard_done = True

            if fatal_error:
                break

            panel.update()

        result_bus.drain(timeout=0.0)
        if fatal_error:
            ProcessUtils.terminate_all(*workers, fs_guard)
            raise RuntimeError(fatal_error)
    finally:
        panel.stop()

    ProcessUtils.join_all(*workers, fs_guard)
    result_bus.drain(timeout=0.0)
    for worker in workers:
        if worker.exitcode not in (0, None):
            raise RuntimeError(f'Worker process "{worker.name}" exited with code {worker.exitcode}')
    if fs_guard.exitcode not in (0, None):
        raise RuntimeError(f"FsGuard process exited with code {fs_guard.exitcode}")

    CLI.show_summary(
        "批量解包结束",
        [
            ("累计解包", f"{tr_processed.get_done()} 个文件"),
            ("累计导出", f"{tr_file_saving.get_done()} 个文件"),
            ("耗时", f"{round(tracker.get_rt(), 1)} 秒"),
        ],
    )
