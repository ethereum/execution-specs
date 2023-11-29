"""
Methods to work with the filesystem and json
"""

import json
import os
import stat
from json import dump
from typing import Any, Dict


def write_json_file(data: Dict[str, Any], file_path: str) -> None:
    """
    Write a JSON file to the given path.
    """
    with open(file_path, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def dump_files_to_directory(output_path: str, files: Dict[str, Any]) -> None:
    """
    Dump the files to the given directory.
    """
    os.makedirs(output_path, exist_ok=True)
    for file_rel_path_flags, file_contents in files.items():
        file_rel_path, flags = (
            file_rel_path_flags.split("+")
            if "+" in file_rel_path_flags
            else (file_rel_path_flags, "")
        )
        rel_path = os.path.dirname(file_rel_path)
        if rel_path:
            os.makedirs(os.path.join(output_path, rel_path), exist_ok=True)
        file_path = os.path.join(output_path, file_rel_path)
        with open(file_path, "w") as f:
            if isinstance(file_contents, str):
                f.write(file_contents)
            else:
                dump(file_contents, f, ensure_ascii=True, indent=4)
        if flags:
            file_mode = os.stat(file_path).st_mode
            if "x" in flags:
                file_mode |= stat.S_IEXEC
            os.chmod(file_path, file_mode)
