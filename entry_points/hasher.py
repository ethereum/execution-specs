"""
Simple CLI tool to hash a directory of JSON fixtures.
"""

import argparse
import hashlib
import json
from dataclasses import dataclass, field
from enum import IntEnum, auto
from pathlib import Path
from typing import Dict, List, Optional


class HashableItemType(IntEnum):
    """
    Represents the type of a hashable item.
    """

    FOLDER = 0
    FILE = auto()
    TEST = auto()


@dataclass(kw_only=True)
class HashableItem:
    """
    Represents an item that can be hashed containing other items that can be hashed as well.
    """

    type: HashableItemType
    parents: List[str] = field(default_factory=list)
    root: Optional[bytes] = None
    items: Optional[Dict[str, "HashableItem"]] = None

    def hash(self) -> bytes:
        """
        Return the hash of the item.
        """
        if self.root is not None:
            return self.root
        if self.items is None:
            raise ValueError("No items to hash")
        all_hash_bytes = b""
        for _, item in sorted(self.items.items()):
            item_hash_bytes = item.hash()
            all_hash_bytes += item_hash_bytes
        return hashlib.sha256(all_hash_bytes).digest()

    def print(
        self, *, name: str, level: int = 0, print_type: Optional[HashableItemType] = None
    ) -> None:
        """
        Print the hash of the item and sub-items.
        """
        next_level = level
        print_name = name
        if level == 0 and self.parents:
            separator = "::" if self.type == HashableItemType.TEST else "/"
            print_name = f"{'/'.join(self.parents)}{separator}{name}"
        if print_type is None or self.type >= print_type:
            next_level += 1
            print(f"{' ' * level}{print_name}: 0x{self.hash().hex()}")

        if self.items is not None:
            for key, item in sorted(self.items.items()):
                item.print(name=key, level=next_level, print_type=print_type)

    @classmethod
    def from_json_file(cls, *, file_path: Path, parents: List[str]) -> "HashableItem":
        """
        Create a hashable item from a JSON file.
        """
        items = {}
        with file_path.open("r") as f:
            data = json.load(f)
        for key, item in sorted(data.items()):
            assert isinstance(item, dict), f"Expected dict, got {type(item)}"
            assert "_info" in item, f"Expected _info in {key}"
            assert "hash" in item["_info"], f"Expected hash in {key}"
            assert isinstance(
                item["_info"]["hash"], str
            ), f"Expected hash to be a string in {key}, got {type(item['_info']['hash'])}"
            item_hash_bytes = bytes.fromhex(item["_info"]["hash"][2:])
            items[key] = cls(
                type=HashableItemType.TEST,
                root=item_hash_bytes,
                parents=parents + [file_path.name],
            )
        return cls(type=HashableItemType.FILE, items=items, parents=parents)

    @classmethod
    def from_folder(cls, *, folder_path: Path, parents: List[str] = []) -> "HashableItem":
        """
        Create a hashable item from a folder.
        """
        items = {}
        for file_path in sorted(folder_path.iterdir()):
            if file_path.is_file() and file_path.suffix == ".json":
                item = cls.from_json_file(
                    file_path=file_path, parents=parents + [folder_path.name]
                )
                items[file_path.name] = item
            elif file_path.is_dir():
                item = cls.from_folder(folder_path=file_path, parents=parents + [folder_path.name])
                items[file_path.name] = item
        return cls(type=HashableItemType.FOLDER, items=items, parents=parents)


def main() -> None:
    """
    Main function.
    """
    parser = argparse.ArgumentParser(description="Hash folders of JSON fixtures.")

    parser.add_argument("folder_path", type=Path, help="The path to the JSON fixtures directory")
    parser.add_argument("--files", "-f", action="store_true", help="Print hash of files")
    parser.add_argument("--tests", "-t", action="store_true", help="Print hash of tests")
    parser.add_argument("--root", "-r", action="store_true", help="Only print hash of root folder")

    args = parser.parse_args()

    item = HashableItem.from_folder(folder_path=args.folder_path)

    if args.root:
        print(f"0x{item.hash().hex()}")
        return

    print_type: Optional[HashableItemType] = None

    if args.files:
        print_type = HashableItemType.FILE
    elif args.tests:
        print_type = HashableItemType.TEST

    item.print(name=args.folder_path.name, print_type=print_type)
