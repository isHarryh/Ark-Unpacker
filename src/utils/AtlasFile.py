# -*- coding: utf-8 -*-
# Copyright (c) 2022-2025, Harry Huang
# @ BSD 3-Clause License
from typing import Union, Tuple, Any

import re
from io import TextIOBase


def _deserialize_field(line: str) -> Tuple[str, str]:
    line = line.strip()
    key, value = re.split(r"\s*:\s*", line, maxsplit=1)
    return key, value


def _serialize_field(
    key: str, value: Any, indent: int, dense_tuple: bool = False
) -> str:
    indent_str = " " * indent
    if isinstance(value, tuple):
        value_str = ("," if dense_tuple else ", ").join(map(str, value))
    elif isinstance(value, bool):
        value_str = "true" if value else "false"
    else:
        value_str = str(value)
    return f"{indent_str}{key}: {value_str}"


class AtlasRegion:
    """Atlas region object representing a texture region."""

    def __init__(self, name: str, **attributes: Any):
        self._name = name
        self._rotate = attributes.get("rotate", False)
        self._xy = attributes.get("xy", (0, 0))
        self._size = attributes.get("size", (0, 0))
        self._orig = attributes.get("orig", (0, 0))
        self._offset = attributes.get("offset", (0, 0))
        self._index = attributes.get("index", -1)
        self._extra_attrs = {
            k: v
            for k, v in attributes.items()
            if k not in {"rotate", "xy", "size", "orig", "offset", "index"}
        }
        if len(self._extra_attrs) > 0:
            raise ValueError(
                f"Unexpected attributes for region '{name}': {', '.join(self._extra_attrs.keys())}"
            )

    @property
    def name(self) -> str:
        return self._name

    @property
    def rotate(self) -> bool:
        return self._rotate

    @property
    def xy(self) -> Tuple[int, int]:
        return self._xy

    @property
    def size(self) -> Tuple[int, int]:
        return self._size

    @property
    def orig(self) -> Tuple[int, int]:
        return self._orig

    @property
    def offset(self) -> Tuple[int, int]:
        return self._offset

    @property
    def index(self) -> int:
        return self._index

    @classmethod
    def from_lines(
        cls, name: str, lines: Tuple[str, ...], start_index: int = 0
    ) -> Tuple["AtlasRegion", int]:
        attributes = {}
        line_index = start_index

        while line_index < len(lines) and lines[line_index].startswith((" ", "\t")):
            attr_line = lines[line_index].strip()
            try:
                key, value = _deserialize_field(attr_line)
                if key == "rotate":
                    if value.isdecimal():
                        attributes[key] = int(value)
                    elif value.lower() == "true":
                        attributes[key] = True
                    elif value.lower() == "false":
                        attributes[key] = False
                    else:
                        raise ValueError(f"Invalid value for 'rotate': {value}")
                elif key in {"xy", "size", "orig", "offset"}:
                    attributes[key] = tuple(map(int, re.split(r"\s*,\s*", value)))
                elif key == "index":
                    attributes[key] = int(value)
            except Exception as e:
                raise ValueError(
                    f"Failed to parse region attribute '{attr_line}': {e}"
                ) from e
            line_index += 1

        return cls(name, **attributes), line_index

    def dumps(self) -> str:
        lines = []
        lines.append(self.name)
        lines.append(_serialize_field("rotate", self.rotate, 2))
        lines.append(_serialize_field("xy", self.xy, 2))
        lines.append(_serialize_field("size", self.size, 2))
        lines.append(_serialize_field("orig", self.orig, 2))
        lines.append(_serialize_field("offset", self.offset, 2))
        lines.append(_serialize_field("index", self.index, 2))

        for key, value in self._extra_attrs.items():
            lines.append(_serialize_field(key, value, 2))

        return "\n".join(lines)

    def __repr__(self) -> str:
        return f"AtlasRegion(name='{self.name}')"


class AtlasPage:
    """Atlas page object representing a texture page with multiple regions."""

    def __init__(
        self, filename: str, regions: Tuple[AtlasRegion, ...] = (), **attributes: Any
    ):
        self._filename = filename
        self._size = attributes.get("size", (0, 0))
        self._filter = attributes.get("filter", ("Linear", "Linear"))
        self._format = attributes.get("format", "RGBA8888")
        self._repeat = attributes.get("repeat", "none")
        self._regions = regions
        self._extra_attrs = {
            k: v
            for k, v in attributes.items()
            if k not in {"size", "filter", "format", "repeat"}
        }
        if len(self._extra_attrs) > 0:
            raise ValueError(
                f"Unexpected attributes for page '{filename}': {', '.join(self._extra_attrs.keys())}"
            )

    @property
    def filename(self) -> str:
        return self._filename

    @property
    def size(self) -> Tuple[int, int]:
        return self._size

    @property
    def filter(self) -> Tuple[str, str]:
        return self._filter

    @property
    def format(self) -> str:
        return self._format

    @property
    def repeat(self) -> str:
        return self._repeat

    @property
    def regions(self) -> Tuple[AtlasRegion, ...]:
        return self._regions

    @classmethod
    def from_block(cls, block: Tuple[str, ...]) -> "AtlasPage":
        if not block:
            raise ValueError("Empty page block")

        filename = block[0].strip()
        remaining_lines = block[1:]
        page_attrs = {}
        line_index = 0

        # Parse page attributes
        while line_index < len(remaining_lines):
            line = remaining_lines[line_index]
            if not line.startswith((" ", "\t")) and ":" in line:
                try:
                    key, value = _deserialize_field(line)
                    if key == "size":
                        page_attrs[key] = tuple(map(int, re.split(r"\s*,\s*", value)))
                    elif key == "filter":
                        page_attrs[key] = tuple(
                            map(str.strip, re.split(r"\s*,\s*", value))
                        )
                    else:
                        page_attrs[key] = value
                    line_index += 1
                except Exception as e:
                    raise ValueError(
                        f"Failed to parse page attribute '{line}': {e}"
                    ) from e
            else:
                break

        # Parse regions
        regions = (
            cls._parse_regions(remaining_lines[line_index:])
            if line_index < len(remaining_lines)
            else ()
        )
        return cls(filename, regions, **page_attrs)

    @classmethod
    def _parse_regions(cls, lines: Tuple[str, ...]) -> Tuple[AtlasRegion, ...]:
        regions = []
        line_index = 0

        while line_index < len(lines):
            line = lines[line_index]
            if not line.startswith((" ", "\t")):
                region_name = line.strip()
                line_index += 1

                region, next_index = AtlasRegion.from_lines(
                    region_name, lines, line_index
                )
                regions.append(region)
                line_index = next_index
            else:
                line_index += 1

        return tuple(regions)

    def dumps(self) -> str:
        lines = []
        lines.append(self.filename)
        lines.append(_serialize_field("size", self.size, 0, dense_tuple=True))
        lines.append(_serialize_field("format", self.format, 0, dense_tuple=True))
        lines.append(_serialize_field("filter", self.filter, 0, dense_tuple=True))
        lines.append(_serialize_field("repeat", self.repeat, 0, dense_tuple=True))

        # Add extra attributes
        for key, value in self._extra_attrs.items():
            lines.append(_serialize_field(key, value, 0))

        # Add regions
        for region in self.regions:
            lines.append(region.dumps())

        return "\n".join(lines)

    def __repr__(self) -> str:
        return f"AtlasPage(filename='{self.filename}', regions={len(self.regions)})"


class AtlasFile:
    """Atlas file with one or more pages inside."""

    def __init__(self, pages: Tuple[AtlasPage, ...] = ()):
        self._pages = pages

    @property
    def pages(self) -> Tuple[AtlasPage, ...]:
        return self._pages

    @classmethod
    def _split_into_page_blocks(cls, text: str) -> Tuple[Tuple[str, ...], ...]:
        lines = [line.rstrip("\n") for line in text.splitlines()]
        page_blocks = []
        current_block = []

        for line in lines:
            if line.strip():
                current_block.append(line)
            elif current_block:
                page_blocks.append(tuple(current_block))
                current_block = []

        if current_block:
            page_blocks.append(tuple(current_block))

        return tuple(page_blocks)

    @classmethod
    def loads(cls, text: str) -> "AtlasFile":
        if not text.strip():
            return cls()

        page_blocks = cls._split_into_page_blocks(text)
        pages = []

        for block in page_blocks:
            if block:
                try:
                    page = AtlasPage.from_block(tuple(block))
                    pages.append(page)
                except Exception as e:
                    raise ValueError(f"Failed to parse page block: {e}") from e

        return cls(tuple(pages))

    @classmethod
    def load(cls, file: Union[str, TextIOBase]) -> "AtlasFile":
        if isinstance(file, str):
            with open(file, "r") as f:
                text = f.read()
        elif isinstance(file, TextIOBase):
            text = file.read()
        else:
            raise TypeError("Expected str or TextIOBase")
        return cls.loads(text)

    def dumps(self) -> str:
        return "\n" + "\n\n".join(page.dumps() for page in self.pages) + "\n"

    def dump(self, file: Union[str, TextIOBase]):
        text = self.dumps()
        if isinstance(file, str):
            with open(file, "w") as f:
                f.write(text)
        elif isinstance(file, TextIOBase):
            file.write(text)
        else:
            raise TypeError("Expected str or TextIOBase")

    def __repr__(self) -> str:
        return f"AtlasFile(pages={len(self.pages)})"


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
    print("=== Atlas text to object ===")
    atlas_file = AtlasFile.loads(data)
    print(f"Loaded: {atlas_file}")

    for i, page in enumerate(atlas_file.pages):
        print(f"Page {i+1}: {page}")
        for j, region in enumerate(page.regions):
            print(f"  Region {j+1}: {region}")

    print("\n=== Object to atlas text ===")
    serialized = atlas_file.dumps()
    print(serialized)

    print("\n=== Roundtrip test ===")
    atlas_file2 = AtlasFile.loads(serialized)
    serialized2 = atlas_file2.dumps()
    print("Roundtrip successful:", serialized == serialized2)
