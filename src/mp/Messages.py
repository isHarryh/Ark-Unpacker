# Copyright (c) 2022-2026, Harry Huang
# @ BSD 3-Clause License
from dataclasses import dataclass
from typing import Literal, Optional


@dataclass(frozen=True)
class StopMessage:
    pass


@dataclass(frozen=True)
class ResolveABTask:
    abfile: str
    destdir: str
    do_img: bool
    do_txt: bool
    do_aud: bool
    do_mesh: bool
    do_tree: bool


@dataclass(frozen=True)
class PrepareWriteRequest:
    worker_slot: int
    request_id: int
    destdir: str
    name: str
    ext: str
    data_hash: bytes


@dataclass(frozen=True)
class PrepareWriteResponse:
    request_id: int
    decision: Literal["write", "skip"]
    path: Optional[str] = None
