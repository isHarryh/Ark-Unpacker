# Copyright (c) 2022-2026, Harry Huang
# @ BSD 3-Clause License
import os.path as osp
import re
import sys
from typing import Callable, Optional, Sequence

from rich.text import Text
from src.utils.GlobalMethods import try_shorten_path

from .RichCLI import RichCLI

_UNWRAP_QUOTED = re.compile(r'^(?:& )?(["\'])(.*)\1$')
_ILLEGAL_PATH_CHARS = re.compile(r'[*?"<>|\x00-\x1F]')


class UserInput:
    EOF_TRIGGER = "Ctrl+Z" if "win" in sys.platform else "Ctrl+D"
    _CLI = RichCLI.get_instance()

    @staticmethod
    def _ask_text(
        prompt: str,
        *,
        choices: Optional[Sequence[str]] = None,
        default: Optional[str] = None,
        case_sensitive: bool = True,
        inline_prompt: bool = False,
    ) -> str:
        normalized_choices = [str(choice) for choice in choices] if choices is not None else None
        while True:
            if inline_prompt and prompt:
                UserInput._CLI.console.print(Text(prompt, style="bold white"))
            try:
                value = UserInput._CLI.console.input(Text("» ", style="bold green")).strip()
            except EOFError:
                UserInput._CLI.console.print("  已取消任务", style="bold yellow")
                raise InterruptedError("User cancelled")
            if not value and default is not None:
                return str(default)
            candidate = value
            allowed = normalized_choices
            if normalized_choices is not None and not case_sensitive:
                candidate = value.lower()
                allowed = [choice.lower() for choice in normalized_choices]
            if allowed is not None and candidate not in allowed:
                assert normalized_choices is not None
                UserInput._CLI.console.print(f"  提供的输入必须在可选项中", style="bold yellow")
                continue
            return candidate if (allowed is not None and not case_sensitive) else value

    @staticmethod
    def _show_prompt_page(
        title: Optional[str],
        prompt: str,
        *,
        rows: Optional[Sequence[tuple[str, object]]] = None,
        note: Optional[str] = None,
        error: Optional[str] = None,
        input_label: Optional[str] = None,
        input_choices: Optional[str] = None,
        input_default: Optional[str] = None,
        input_hint: Optional[str] = None,
    ) -> str:
        normalized_error = error.rstrip("。").strip() if error else None
        if not title:
            if prompt:
                UserInput._CLI.console.print(Text(prompt, style="bold white"))
            if input_choices:
                UserInput._CLI.console.print(f"  可选项：{input_choices}", style="dim", markup=False, highlight=False)
            if input_default not in (None, ""):
                UserInput._CLI.console.print(f"  默认值：{input_default}", style="dim", markup=False, highlight=False)
            if input_hint:
                for line in input_hint.splitlines():
                    text = line.strip()
                    if text:
                        UserInput._CLI.console.print(f"  {text}", style="dim", markup=False, highlight=False)
            if normalized_error:
                UserInput._CLI.console.print(
                    f"  注意：{normalized_error}",
                    style="bold red",
                    markup=False,
                    highlight=False,
                )
            return ""
        UserInput._CLI.clear()
        UserInput._CLI.show_prompt_page(
            title,
            prompt,
            rows=rows,
            note=note,
            error=normalized_error,
            input_label=input_label,
            input_choices=input_choices,
            input_default=input_default,
            input_hint=input_hint,
        )
        return prompt

    @staticmethod
    def _preprocess_path_input(value: str) -> str:
        return _UNWRAP_QUOTED.sub(r"\2", value.strip())

    @staticmethod
    def _compose_note(
        note: Optional[str],
    ) -> Optional[str]:
        lines: list[str] = []
        if note:
            for line in note.splitlines():
                stripped = line.strip()
                if stripped:
                    lines.append(stripped)

        return "\n".join(lines) if lines else None

    @staticmethod
    def _compose_input_hint(note: Optional[str], *, lite: bool = False) -> str:
        lines: list[str] = []
        if note:
            lines.extend([line.strip() for line in note.splitlines() if line.strip()])
        if not lite:
            if not lines:
                lines.append("请直接输入并按 Enter 提交")
            lines.append(f"输入快捷键 {UserInput.EOF_TRIGGER} 可取消")
        return "\n".join(lines)

    @staticmethod
    def _show_validation_error(title: Optional[str], message: str) -> Optional[str]:
        if title:
            return message
        UserInput._CLI.console.print(f"  {message.rstrip('。')}", style="bold red", markup=False, highlight=False)
        return None

    @staticmethod
    def request(
        prompt: str = "» ",
        *,
        title: Optional[str] = None,
        rows: Optional[Sequence[tuple[str, object]]] = None,
        input_label: str = "请输入",
        note: Optional[str] = None,
        default: Optional[str] = None,
    ) -> str:
        input_hint = UserInput._compose_input_hint(UserInput._compose_note(note), lite=(title is None))
        ask_prompt = UserInput._show_prompt_page(
            title,
            prompt,
            rows=rows,
            note=None,
            input_label=input_label,
            input_default=str(default) if default not in (None, "") else None,
            input_hint=input_hint,
        )
        return UserInput._ask_text(
            ask_prompt,
            default=default,
            inline_prompt=(title is None),
        )

    @staticmethod
    def request_options(
        options: Sequence[object],
        *,
        title: Optional[str] = None,
        rows: Optional[Sequence[tuple[str, object]]] = None,
        prompt: str = "请选择一个选项",
        note: Optional[str] = None,
        default: Optional[str] = None,
    ) -> str:
        choices = [str(option) for option in options]
        if not choices:
            raise ValueError("options cannot be empty")
        input_hint = UserInput._compose_input_hint(UserInput._compose_note(note), lite=(title is None))
        ask_prompt = UserInput._show_prompt_page(
            title,
            prompt,
            rows=rows,
            note=None,
            input_label="请选择",
            input_choices=", ".join(choices),
            input_default=str(default) if default not in (None, "") else None,
            input_hint=input_hint,
        )
        return UserInput._ask_text(
            ask_prompt,
            choices=choices,
            default=default,
            inline_prompt=(title is None),
        )

    @staticmethod
    def request_input_path(
        *,
        title: Optional[str] = None,
        rows: Optional[Sequence[tuple[str, object]]] = None,
        prompt: str = "路径",
        note: Optional[str] = None,
    ) -> str:
        error: Optional[str] = None
        note_text = note or "支持相对路径"
        while True:
            input_hint = UserInput._compose_input_hint(UserInput._compose_note(note_text), lite=(title is None))
            ask_prompt = UserInput._show_prompt_page(
                title,
                prompt,
                rows=rows,
                note=None,
                error=error,
                input_label="请输入",
                input_hint=input_hint,
            )
            uin = UserInput._preprocess_path_input(UserInput._ask_text(ask_prompt, inline_prompt=(title is None)))
            if not uin:
                error = UserInput._show_validation_error(title, "路径不能为空。")
                continue
            norm_path = osp.normpath(uin)
            if not osp.exists(norm_path):
                error = UserInput._show_validation_error(title, "输入的路径不存在。")
                continue
            return osp.abspath(norm_path)

    @staticmethod
    def request_output_path(
        *,
        default_generator: Optional[Callable[[], str]] = None,
        title: Optional[str] = None,
        rows: Optional[Sequence[tuple[str, object]]] = None,
        prompt: str = "输出路径",
        note: Optional[str] = None,
    ) -> str:
        error: Optional[str] = None
        note_text = note or ("支持相对路径" + ("，留空表示自动创建" if default_generator else ""))
        while True:
            input_hint = UserInput._compose_input_hint(UserInput._compose_note(note_text), lite=(title is None))
            ask_prompt = UserInput._show_prompt_page(
                title,
                prompt,
                rows=rows,
                note=None,
                error=error,
                input_label="请输入",
                input_hint=input_hint,
            )
            uin = UserInput._preprocess_path_input(UserInput._ask_text(ask_prompt, inline_prompt=(title is None)))
            if not uin:
                if default_generator is not None:
                    return osp.abspath(default_generator())
                error = UserInput._show_validation_error(title, "路径不能为空。")
                continue

            norm_path = osp.normpath(uin)
            if len(norm_path) > 4096:
                error = UserInput._show_validation_error(title, "路径长度太长。")
                continue
            if _ILLEGAL_PATH_CHARS.search(norm_path):
                error = UserInput._show_validation_error(title, "路径不能包含非法字符。")
                continue

            abs_path = osp.abspath(norm_path)
            shortened = try_shorten_path(abs_path)
            if shortened != abs_path:
                use_shortened = UserInput.request_yes_or_no(
                    "检测到路径较长，是否改用推荐路径？",
                    default=True,
                    title=title,
                    rows=(list(rows) if rows else []) + [("当前路径", abs_path), ("推荐路径", shortened)],
                    note="默认接受推荐路径",
                )
                if use_shortened:
                    return osp.abspath(shortened)
            return abs_path

    @staticmethod
    def request_yes_or_no(
        prompt: str,
        *,
        default: bool,
        title: Optional[str] = None,
        rows: Optional[Sequence[tuple[str, object]]] = None,
        note: Optional[str] = None,
    ) -> bool:
        default_text = "y" if default else "n"
        input_hint = UserInput._compose_input_hint(UserInput._compose_note(note), lite=(title is None))
        ask_prompt = UserInput._show_prompt_page(
            title,
            prompt,
            rows=rows,
            note=None,
            input_label="请确认",
            input_choices=f"y / n（默认 {default_text}）",
            input_hint=input_hint,
        )
        answer = UserInput._ask_text(
            ask_prompt,
            choices=["y", "n"],
            default=default_text,
            case_sensitive=False,
            inline_prompt=(title is None),
        )
        return answer == "y"

    @staticmethod
    def press_enter_to_exit() -> None:
        UserInput.request("按 Enter 退出...", default="", note=None)

    @staticmethod
    def press_enter_to_continue() -> None:
        UserInput.request("按 Enter 继续...", default="", note=None)


class ParamInputSession:
    def __init__(self, title: str):
        self._title = title
        self._rows: list[tuple[str, object]] = []

    @property
    def title(self) -> str:
        return self._title

    @property
    def rows(self) -> list[tuple[str, object]]:
        return self._rows[:]

    def set_value(self, key: str, value: object) -> None:
        for idx, (name, _) in enumerate(self._rows):
            if name == key:
                self._rows[idx] = (key, value)
                return
        self._rows.append((key, value))

    def set_bool(self, key: str, value: bool) -> None:
        self.set_value(key, "[√]" if value else "[×]")

    def request(
        self,
        prompt: str,
        *,
        input_label: str = "请输入",
        note: Optional[str] = None,
        default: Optional[str] = None,
    ) -> str:
        return UserInput.request(
            prompt,
            title=self._title,
            rows=self.rows,
            input_label=input_label,
            note=note,
            default=default,
        )

    def request_input_path(
        self,
        key: str,
        *,
        prompt: str,
        note: Optional[str] = None,
    ) -> str:
        value = UserInput.request_input_path(
            title=self._title,
            rows=self.rows,
            prompt=prompt,
            note=note,
        )
        self.set_value(key, value)
        return value

    def request_output_path(
        self,
        key: str,
        default_generator: Optional[Callable[[], str]] = None,
        *,
        prompt: str,
        note: Optional[str] = None,
    ) -> str:
        value = UserInput.request_output_path(
            default_generator=default_generator,
            title=self._title,
            rows=self.rows,
            prompt=prompt,
            note=note,
        )
        self.set_value(key, value)
        return value

    def request_yes_or_no(
        self,
        key: str,
        default: bool,
        *,
        prompt: str,
        note: Optional[str] = None,
    ) -> bool:
        value = UserInput.request_yes_or_no(
            prompt,
            default=default,
            title=self._title,
            rows=self.rows,
            note=note,
        )
        self.set_bool(key, value)
        return value

    def confirm_start(self) -> None:
        self.request(
            "请按 Enter 以开始！",
            default="",
            input_label="已就绪",
        )
