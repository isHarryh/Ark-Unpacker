# -*- coding: utf-8 -*-
# Copyright (c) 2022-2025, Harry Huang
# @ BSD 3-Clause License
import argparse
import os


class ArgParserFailure(Exception):
    def __init__(self, *args: object):
        super().__init__(*args)


class _ArkUnpackerArgParser(argparse.ArgumentParser):
    def __init__(self, prog: str, description: str, epilog: str):
        super().__init__(prog=prog, description=description, epilog=epilog)

    def error(self, message: str):
        raise ArgParserFailure(message)

    def validate_input_output_arg(self, args, allow_file_input: bool = False):
        if not getattr(args, "input", None):
            self.error("input should be defined in this mode")
        if not getattr(args, "output", None):
            self.error("output should be defined in this mode")
        if not allow_file_input and os.path.isfile(args.input):
            self.error("input should be a directory, not file")
        if not os.path.isdir(args.input) and not (
            allow_file_input and os.path.isfile(args.input)
        ):
            self.error(
                f"input should be a {'file or ' if allow_file_input else ''}directory that exists"
            )

    def validate_logging_level_arg(self, args):
        if getattr(args, "logging_level", None) is None:
            return
        if args.logging_level not in range(5):
            self.error("invalid logging level")

    @staticmethod
    def instantiate():
        parser = _ArkUnpackerArgParser(
            prog="ArkUnpacker",
            description="Arknights Assets Unpacker. Use no argument to run to enter the interactive CLI mode.",
            epilog="GitHub: https://github.com/isHarryh/Ark-Unpacker",
        )
        parser.add_argument(
            "-v",
            "--version",
            action="store_true",
            help="show a version message and exit",
        )
        parser.add_argument(
            "-m",
            "--mode",
            choices=["ab", "cb", "fb", "sp", "cu"],
            help="working mode, ab=resolve-ab, cb=combine-image, fb=decode-flatbuffers, sp=resolve-spine, cu=resolve-usm",
        )
        parser.add_argument("-i", "--input", help="source file or directory path")
        parser.add_argument("-o", "--output", help="destination directory path")
        parser.add_argument(
            "-d",
            "-delete",
            action="store_true",
            help="delete the existed destination directory first",
        )
        parser.add_argument(
            "--image",
            action="store_true",
            help="in resolve ab mode: export image files",
        )
        parser.add_argument(
            "--text",
            action="store_true",
            help="in resolve ab mode: export text or binary files",
        )
        parser.add_argument(
            "--audio",
            action="store_true",
            help="in resolve ab mode: export audio files",
        )
        parser.add_argument(
            "--spine",
            action="store_true",
            help="in resolve ab mode: export spine asset files",
        )
        parser.add_argument(
            "--mesh",
            action="store_true",
            help="in resolve ab mode: export mesh resources",
        )
        parser.add_argument(
            "-g",
            "--group",
            action="store_true",
            help="in resolve ab mode: group files into separate directories named by their source ab file",
        )
        parser.add_argument(
            "--no-video",
            action="store_true",
            help="in resolve usm mode: skip video processing",
        )
        parser.add_argument(
            "--no-audio",
            action="store_true",
            help="in resolve usm mode: skip audio processing",
        )
        parser.add_argument(
            "-l",
            "--logging-level",
            choices=range(5),
            type=int,
            help="logging level, 0=none, 1=error, 2=warn, 3=info, 4=debug",
        )
        return parser


INSTANCE = _ArkUnpackerArgParser.instantiate()
