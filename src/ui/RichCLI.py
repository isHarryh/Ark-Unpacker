# Copyright (c) 2022-2026, Harry Huang
# @ BSD 3-Clause License
import os
from dataclasses import dataclass
from typing import Iterable, Optional, Sequence

from rich import box
from rich.console import Console, Group, RenderableType
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table
from rich.text import Text

_MENU_FOOTER_LINES = (
    "项目仓库和帮助文档: https://github.com/isHarryh/Ark-Unpacker",
    "Tip: 输入快捷键 Ctrl+Z 可以取消任务；按下 Enter 以提交输入的内容。",
)


@dataclass(frozen=True)
class MenuOption:
    key: str
    label: str
    detail: str = ""


class RichCLI:
    _instance: Optional["RichCLI"] = None

    def __init__(self):
        self.console = Console(highlight=False, soft_wrap=True)

    @classmethod
    def get_instance(cls) -> "RichCLI":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def clear(self) -> None:
        os.system("cls" if os.name == "nt" else "clear")

    def title(self, text: str) -> None:
        if os.name == "nt":
            os.system(f"title {text}")

    def rule(self, title: str, *, style: str = "cyan") -> None:
        self.console.rule(Text(title, style="bold white"), style=style)

    def show_menu(
        self,
        title: str,
        options: Sequence[MenuOption],
        *,
        intro: Optional[Iterable[str]] = None,
        footer: Optional[Iterable[str]] = None,
        border_style: str = "cyan",
    ) -> None:
        body: list[RenderableType] = []

        if intro:
            intro_group = Group(*[Text(line) for line in intro if line])
            body.append(intro_group)

        menu = Table.grid(expand=False, padding=(0, 2))
        menu.add_column(style="bold cyan", justify="right", no_wrap=True, width=1)
        menu.add_column(style="bold white", no_wrap=True)
        menu.add_column(style="dim")
        for item in options:
            menu.add_row(item.key, item.label, item.detail)
        body.append(menu)

        footer_lines = [line for line in (footer or []) if line]
        footer_lines.extend(_MENU_FOOTER_LINES)
        body.append(Text(""))
        footer_group = Group(*[Text(line, style="dim") for line in footer_lines])
        body.append(footer_group)

        self.console.print(
            Panel(
                Group(*body),
                title=f"[bold]{title}[/bold]",
                border_style=border_style,
                box=box.ROUNDED,
                padding=(1, 1),
            )
        )

    def show_section(self, title: str, description: Optional[str] = None) -> None:
        content: RenderableType = Text(description, style="white") if description else Text("")
        self.console.print(
            Panel(
                content,
                title=f"[bold]{title}[/bold]",
                border_style="cyan",
                box=box.ROUNDED,
                padding=(1, 2),
            )
        )

    def show_summary(self, title: str, rows: Sequence[tuple[str, object]], *, border_style: str = "green") -> None:
        table = self._build_kv_table(rows)
        for key, value in rows:
            table.add_row(key, str(value))
        self.console.print(
            Panel(
                table,
                title=f"[bold]{title}[/bold]",
                border_style=border_style,
                box=box.ROUNDED,
                padding=(1, 2),
            )
        )

    def show_prompt_page(
        self,
        title: str,
        prompt: str,
        *,
        rows: Optional[Sequence[tuple[str, object]]] = None,
        note: Optional[str] = None,
        error: Optional[str] = None,
        input_label: Optional[str] = None,
        input_choices: Optional[str] = None,
        input_default: Optional[str] = None,
        input_hint: Optional[str] = None,
        border_style: str = "cyan",
    ) -> None:
        body: list[RenderableType] = []
        effective_input_prompt = prompt if prompt else None
        effective_input_hint = input_hint or note
        normalized_error = error.rstrip("。").strip() if error else None
        hint_lines: list[str] = []
        if input_choices:
            hint_lines.append(f"可选项：{input_choices}")
        if input_default not in (None, ""):
            hint_lines.append(f"默认值：{input_default}")
        if effective_input_hint:
            hint_lines.extend(line for line in effective_input_hint.splitlines() if line)

        if rows:
            table = self._build_kv_table(rows)
            for key, value in rows:
                table.add_row(key, str(value))
            body.append(table)
        elif effective_input_prompt:
            body.append(Text("请按照下方的提示来输入任务参数", style="dim"))

        if effective_input_prompt:
            body.append(Rule(style="dim cyan"))
            input_table = Table.grid(expand=False, padding=(0, 1))
            input_table.add_column(style="bold cyan", justify="right", no_wrap=True, width=8)
            input_table.add_column(style="white", justify="left")
            input_table.add_row(input_label or "请输入", Text(effective_input_prompt, style="bold white"))
            if hint_lines:
                input_table.add_row("", Text("\n".join(hint_lines), style="dim"))
            if normalized_error:
                input_table.add_row("注意", Text(normalized_error, style="bold red"))
            body.append(input_table)
        else:
            if hint_lines:
                hint_table = Table.grid(expand=False, padding=(0, 1))
                hint_table.add_column(style="bold cyan", justify="right", no_wrap=True, width=8)
                hint_table.add_column(style="white", justify="left")
                hint_table.add_row("提示", Text("\n".join(hint_lines), style="dim"))
                body.append(hint_table)
            if normalized_error:
                error_table = Table.grid(expand=False, padding=(0, 1))
                error_table.add_column(style="bold cyan", justify="right", no_wrap=True, width=8)
                error_table.add_column(style="white", justify="left")
                error_table.add_row("注意", Text(normalized_error, style="bold red"))
                body.append(error_table)
        if not body:
            body.append(Text(""))
        self.console.print(
            Panel(
                Group(*body),
                title=f"[bold]{title}[/bold]",
                border_style=border_style,
                box=box.ROUNDED,
                padding=(1, 1),
            )
        )

    def show_notice(self, title: str, message: str, *, style: str = "yellow") -> None:
        self.console.print(
            Panel(
                Text(message),
                title=f"[bold]{title}[/bold]",
                border_style=style,
                box=box.ROUNDED,
                padding=(1, 2),
            )
        )

    def show_error(self, title: str, message: str) -> None:
        self.show_notice(title, message, style="red")

    def show_stage(self, message: str) -> None:
        self.console.print(Text(message, style="bold cyan"))

    def show_success(self, message: str) -> None:
        self.console.print(Text(message, style="bold green"))

    def show_warning(self, message: str) -> None:
        self.console.print(Text(message, style="bold yellow"))

    def show_dim(self, message: str) -> None:
        self.console.print(Text(message, style="dim"))

    def blank(self) -> None:
        self.console.print()

    def show_issue(
        self,
        key: str,
        detail: str,
        *,
        name: Optional[str] = None,
        type_name: Optional[str] = None,
        severity: str = "warning",
    ) -> None:
        detail_style = "bold red" if severity == "error" else "bold yellow"
        text = Text()
        text.append("[", style="dim")
        text.append(key, style="bold yellow")
        text.append("] ", style="dim")
        if name:
            text.append(str(name), style="bold white")
            if type_name:
                text.append(" ", style="white")
        if type_name:
            text.append(f"（{type_name}）", style="magenta")
            text.append("：", style="white")
        text.append(detail, style=detail_style)
        self.console.print(text)

    def print_exception(self) -> None:
        self.console.print_exception(show_locals=False)

    @staticmethod
    def format_path_state(path: str, exists: bool) -> str:
        state = "可用" if exists else "缺失"
        return f"{state}  {path}"

    @staticmethod
    def _build_kv_table(rows: Sequence[tuple[str, object]]) -> Table:
        label_width = 0
        if rows:
            label_width = max(len(str(key)) for key, _ in rows) * 2
        table = Table.grid(expand=False, padding=(0, 1))
        table.add_column(style="bold cyan", no_wrap=True, width=max(10, label_width), justify="right")
        table.add_column(style="white", justify="left")
        return table
