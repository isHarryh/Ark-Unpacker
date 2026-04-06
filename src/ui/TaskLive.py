# Copyright (c) 2022-2026, Harry Huang
# @ BSD 3-Clause License
from typing import Callable, Optional, Protocol, Sequence

from rich import box
from rich.align import Align
from rich.console import Group, RenderableType
from rich.live import Live
from rich.panel import Panel
from rich.progress import BarColumn, Progress, TaskID, TaskProgressColumn, TimeElapsedColumn, TimeRemainingColumn
from rich.rule import Rule
from rich.table import Column, Table
from rich.text import Text

from .RichCLI import RichCLI


class TaskTrackerLike(Protocol):
    def get_progress(self, force_inc: bool = False) -> float: ...


class TaskDetailField:
    def __init__(self, name: str, value_getter: Callable[[], Optional[object]]):
        self._name = name
        self._value_getter = value_getter

    def get_name(self) -> str:
        return self._name

    def get_value(self) -> Optional[object]:
        return self._value_getter()


class TaskValueField(TaskDetailField):
    def __init__(self, name: str, value: Optional[object] = None):
        self._value = value
        super().__init__(name, self._get_current_value)

    def set_value(self, value: Optional[object]) -> None:
        self._value = value

    def _get_current_value(self) -> Optional[object]:
        return self._value


class TaskLiveView:
    @staticmethod
    def _none_progress() -> Optional[float]:
        return None

    def __init__(
        self,
        title: str = "运行中",
        *,
        refresh_rate: float = 0.1,
        detail_fields: Optional[Sequence[TaskDetailField]] = None,
        progress_getter: Callable[[], Optional[float]] = _none_progress,
    ):
        self._refresh_per_second = max(1.0, 1.0 / refresh_rate) if refresh_rate > 0 else 10.0
        self._title = title
        self._detail_fields = list(detail_fields or [])
        assert progress_getter is not None
        self._progress_getter = progress_getter
        self._progress: Optional[float] = None
        self._rows: list[tuple[str, str]] = []
        self._label_width = 10
        self._tracker: Optional[TaskTrackerLike] = None
        self._tracker_force_inc = True
        self._progress_widget: Optional[Progress] = None
        self._progress_task_id: Optional[TaskID] = None
        self._cli = RichCLI.get_instance()
        self._live: Optional[Live] = None

    def set_title(self, title: str) -> None:
        self._title = title

    def set_detail_fields(self, detail_fields: Sequence[TaskDetailField]) -> None:
        self._detail_fields = list(detail_fields)
        if self._detail_fields:
            self._label_width = max(len(field.get_name()) for field in self._detail_fields) * 2

    def bind_tracker(self, tracker: Optional[TaskTrackerLike], *, force_inc: bool = True) -> None:
        self._tracker = tracker
        self._tracker_force_inc = force_inc
        if tracker is not None:
            self._progress_getter = lambda: tracker.get_progress(force_inc=force_inc)
        else:
            self._progress_getter = TaskLiveView._none_progress

    def get_progress(self) -> Optional[float]:
        progress = self._progress_getter()
        if progress is None:
            return None
        return max(0.0, min(1.0, progress))

    def get_rows(self) -> list[tuple[str, object]]:
        rows = []
        for field in self._detail_fields:
            value = field.get_value()
            if value is None:
                continue
            rows.append((field.get_name(), value))
        return rows

    def start(self) -> None:
        if self._live is not None:
            return
        self._progress = self.get_progress()
        self._ensure_progress_widget()
        self._live = Live(
            self._render(),
            console=self._cli.console,
            refresh_per_second=self._refresh_per_second,
            transient=True,
        )
        self._live.start()

    def stop(self) -> None:
        if self._live is None:
            return
        self._live.stop()
        self._live = None

    def update(self) -> None:
        self._rows = [(str(key), str(value)) for key, value in self.get_rows()]

        self._progress = self.get_progress()
        if self._progress is None and self._progress_widget is not None:
            self._progress_widget = None
            self._progress_task_id = None
        self._ensure_progress_widget()
        if self._progress_widget is not None and self._progress_task_id is not None and self._progress is not None:
            self._progress_widget.update(self._progress_task_id, completed=self._progress * 100)

        if self._live is not None:
            self._live.update(self._render(), refresh=True)

    def _render(self) -> RenderableType:
        body: list[RenderableType] = []
        if self._progress_widget is not None:
            body.append(self._progress_widget)

        if self._rows:
            if body:
                body.append(Rule(style="dim cyan"))
            body.append(Align.left(self._build_details_table(self._rows)))

        return Panel(
            Group(*body) if body else Text(""),
            title=f"[bold]{self._title}[/bold]",
            border_style="cyan",
            box=box.ROUNDED,
            padding=(0, 2),
        )

    def _build_details_table(self, rows: Sequence[tuple[str, str]]) -> Table:
        table = Table.grid(expand=False, padding=(0, 1))
        table.add_column(no_wrap=True, width=self._label_width, justify="right")
        table.add_column(overflow="fold")
        for key, value in rows:
            table.add_row(
                Text(key, style="bold cyan"),
                Text(value, style="white"),
            )
        return table

    def _ensure_progress_widget(self) -> None:
        if self._progress_widget is not None or self._progress is None:
            return
        self._progress_widget = Progress(
            BarColumn(
                bar_width=None,
                complete_style="green",
                finished_style="green",
                table_column=Column(ratio=4),
            ),
            TaskProgressColumn(style="green", table_column=Column(width=6)),
            TimeElapsedColumn(table_column=Column(width=8)),
            TimeRemainingColumn(table_column=Column(width=8)),
            expand=True,
            console=self._cli.console,
        )
        self._progress_task_id = self._progress_widget.add_task(
            "progress", total=100, completed=int(self._progress * 100)
        )
