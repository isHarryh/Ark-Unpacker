# -*- coding: utf-8 -*-
# Copyright (c) 2022-2025, Harry Huang
# @ BSD 3-Clause License
from typing import Union

import re
from io import TextIOBase


class AtlasFile:
    PAGE_PARSERS = {
        "size": lambda v: tuple(map(int, re.split(r"\s*,\s*", v))),
        "filter": lambda v: tuple(map(str.strip, re.split(r"\s*,\s*", v))),
        "format": lambda v: v,
        "repeat": lambda v: v,
    }
    REGION_PARSERS = {
        "rotate": lambda v: v.lower() == "true",
        "xy": lambda v: tuple(map(int, re.split(r"\s*,\s*", v))),
        "size": lambda v: tuple(map(int, re.split(r"\s*,\s*", v))),
        "orig": lambda v: tuple(map(int, re.split(r"\s*,\s*", v))),
        "offset": lambda v: tuple(map(int, re.split(r"\s*,\s*", v))),
        "index": lambda v: int(v),
    }

    @classmethod
    def loads(cls, text: str):
        pages = []
        lines = [line.rstrip("\n") for line in text.splitlines()]
        page_blocks = []

        current_page = []
        for line in lines:
            stripped = line.strip()
            if not stripped:
                if current_page:
                    page_blocks.append(current_page)
                    current_page = []
            else:
                current_page.append(line)
        if current_page:
            page_blocks.append(current_page)

        for block in page_blocks:
            if not block:
                continue
            page_info = {"regions": []}
            page_info["filename"] = block[0].strip()
            remaining_lines = block[1:]
            page_attrs = {}
            current_line = 0
            while current_line < len(remaining_lines):
                line = remaining_lines[current_line]
                if not line.startswith((" ", "\t")) and ":" in line:
                    key, value = cls._parse_line(line)
                    parsed_value = cls.PAGE_PARSERS.get(key, lambda v: v)(value)
                    page_attrs[key] = parsed_value
                    current_line += 1
                else:
                    break
            regions = []
            regions_lines = remaining_lines[current_line:]
            i = 0
            while i < len(regions_lines):
                line = regions_lines[i]
                if not line.startswith((" ", "\t")):
                    region_name = line.strip()
                    region_attrs = {}
                    i += 1
                    while i < len(regions_lines) and regions_lines[i].startswith(
                        (" ", "\t")
                    ):
                        attr_line = regions_lines[i].strip()
                        key, value = cls._parse_line(attr_line)
                        parsed_value = cls.REGION_PARSERS.get(key, lambda v: v)(value)
                        region_attrs[key] = parsed_value
                        i += 1
                    regions.append({"name": region_name, **region_attrs})
                else:
                    i += 1
            page_info.update(page_attrs)
            page_info["regions"] = regions
            pages.append(page_info)
        return {"pages": pages}

    @classmethod
    def load(cls, file: Union[str, TextIOBase]):
        if isinstance(file, str):
            with open(file, "r") as f:
                text = f.read()
        elif isinstance(file, TextIOBase):
            text = file.read()
        else:
            raise TypeError("Expected str or TextIOBase")
        return cls.loads(text)

    @classmethod
    def dumps(cls, data: dict):
        raise NotImplementedError()

    @classmethod
    def dump(cls, data: dict, file: Union[str, TextIOBase]):
        text = cls.dumps(data)
        if isinstance(file, str):
            with open(file, "w") as f:
                f.write(text)
        elif isinstance(file, TextIOBase):
            file.write(text)
        else:
            raise TypeError("Expected str or TextIOBase")

    @staticmethod
    def _parse_line(line):
        line = line.strip()
        key, value = re.split(r"\s*:\s*", line, 1)
        return key, value

    @staticmethod
    def _serialize_value(key, value):
        if isinstance(value, tuple):
            return ",".join(map(str, value))
        elif isinstance(value, bool):
            return "true" if value else "false"
        elif key == "index" and isinstance(value, int):
            return str(value)
        else:
            return str(value)


if __name__ == "__main__":
    data = """
example.png
size: 2048,2048
format: RGBA8888
filter: Linear,Linear
repeat: none
Example_Region_1
  rotate: false
  xy: 1900, 1800
  size: 65, 60
  orig: 65, 60
  offset: 0, 0
  index: -1
Example_Region_2
  rotate: true
  xy: 250, 450
  size: 100, 25
  orig: 100, 25
  offset: 0, 0
  index: 1

example_2.png
size: 1024,1024
format: RGBA8888
filter: Linear,Linear
repeat: none
Example_Region_Bad
  rotate:false
  xy:0,200
  size:230,125
  orig:230,125
  offset:0,0
  index:-1
Example_Region_/\\!@#$%
  rotate: false
  xy: 500, 450
  size: 140, 120
  orig: 140, 120
  offset: 0, 0
  index: -1

"""
    loaded = AtlasFile.loads(data)
    print(loaded)
