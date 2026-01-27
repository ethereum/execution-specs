"""Simple CLI tool to hash a directory of JSON fixtures."""

import hashlib
import json
import sys
from dataclasses import dataclass, field
from enum import IntEnum, auto
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, TypeVar

import click
from rich.console import Console
from rich.markup import escape as rich_escape


class HashableItemType(IntEnum):
    """Represents the type of a hashable item."""

    FOLDER = 0
    FILE = auto()
    TEST = auto()


@dataclass(kw_only=True)
class HashableItem:
    """
    Represents an item that can be hashed containing other items that can be
    hashed as well.
    """

    type: HashableItemType
    parents: List[str] = field(default_factory=list)
    root: Optional[bytes] = None
    items: Optional[Dict[str, "HashableItem"]] = None

    def hash(self) -> bytes:
        """Return the hash of the item."""
        if self.root is not None:
            return self.root
        if self.items is None:
            raise ValueError("No items to hash")
        all_hash_bytes = b""
        for _, item in sorted(self.items.items()):
            item_hash_bytes = item.hash()
            all_hash_bytes += item_hash_bytes
        return hashlib.sha256(all_hash_bytes).digest()

    def format_lines(
        self,
        *,
        name: str,
        level: int = 0,
        print_type: Optional[HashableItemType] = None,
        max_depth: Optional[int] = None,
    ) -> List[str]:
        """Return the hash lines for the item and sub-items."""
        lines: List[str] = []
        next_level = level
        print_name = name

        if level == 0 and self.parents:
            separator = "::" if self.type == HashableItemType.TEST else "/"
            print_name = f"{'/'.join(self.parents)}{separator}{name}"

        if print_type is None or self.type >= print_type:
            next_level += 1
            lines.append(f"{' ' * level}{print_name}: 0x{self.hash().hex()}")

        # Stop recursion if we've reached max_depth
        if max_depth is not None and next_level > max_depth:
            return lines

        if self.items is not None:
            for key, item in sorted(self.items.items()):
                lines.extend(
                    item.format_lines(
                        name=key,
                        level=next_level,
                        print_type=print_type,
                        max_depth=max_depth,
                    )
                )

        return lines

    @classmethod
    def from_json_file(
        cls, *, file_path: Path, parents: List[str]
    ) -> "HashableItem":
        """Create a hashable item from a JSON file."""
        items = {}
        with file_path.open("r") as f:
            data = json.load(f)
        for key, item in sorted(data.items()):
            if not isinstance(item, dict):
                raise TypeError(f"Expected dict, got {type(item)} for {key}")
            if "_info" not in item:
                raise KeyError(
                    f"Expected '_info' in {key}, json file: {file_path.name}"
                )

            # EEST uses 'hash'; ethereum/tests use 'generatedTestHash'
            hash_value = item["_info"].get("hash") or item["_info"].get(
                "generatedTestHash"
            )
            if hash_value is None:
                raise KeyError(
                    f"Expected 'hash' or 'generatedTestHash' in {key}"
                )

            if not isinstance(hash_value, str):
                raise TypeError(
                    f"Expected hash to be a string in {key}, "
                    f"got {type(hash_value)}"
                )

            item_hash_bytes = bytes.fromhex(hash_value[2:])
            items[key] = cls(
                type=HashableItemType.TEST,
                root=item_hash_bytes,
                parents=parents + [file_path.name],
            )
        return cls(type=HashableItemType.FILE, items=items, parents=parents)

    @classmethod
    def from_folder(
        cls, *, folder_path: Path, parents: Optional[List[str]] = None
    ) -> "HashableItem":
        """Create a hashable item from a folder."""
        if parents is None:
            parents = []
        items = {}
        for file_path in sorted(folder_path.iterdir()):
            if ".meta" in file_path.parts:
                continue
            if file_path.is_file() and file_path.suffix == ".json":
                item = cls.from_json_file(
                    file_path=file_path, parents=parents + [folder_path.name]
                )
                items[file_path.name] = item
            elif file_path.is_dir():
                item = cls.from_folder(
                    folder_path=file_path, parents=parents + [folder_path.name]
                )
                items[file_path.name] = item
        return cls(type=HashableItemType.FOLDER, items=items, parents=parents)


def render_hash_report(
    folder: Path,
    *,
    files: bool,
    tests: bool,
    root: bool,
    name_override: Optional[str] = None,
    max_depth: Optional[int] = None,
) -> List[str]:
    """Return canonical output lines for a folder."""
    item = HashableItem.from_folder(folder_path=folder)
    if root:
        return [f"0x{item.hash().hex()}"]
    print_type: Optional[HashableItemType] = None
    if files:
        print_type = HashableItemType.FILE
    elif tests:
        print_type = HashableItemType.TEST
    name = name_override if name_override is not None else folder.name
    return item.format_lines(
        name=name, print_type=print_type, max_depth=max_depth
    )


def collect_hashes(
    item: HashableItem,
    *,
    path: str = "",
    print_type: Optional[HashableItemType] = None,
    max_depth: Optional[int] = None,
    depth: int = 0,
) -> Dict[str, str]:
    """Collect hashes from item tree as {path: hash_hex}."""
    result: Dict[str, str] = {}

    if print_type is None or item.type >= print_type:
        if path:
            result[path] = f"0x{item.hash().hex()}"
        depth += 1
        if max_depth is not None and depth > max_depth:
            return result

    if item.items:
        for name, child in sorted(item.items.items()):
            child_path = f"{path}/{name}" if path else name
            result.update(
                collect_hashes(
                    child,
                    path=child_path,
                    print_type=print_type,
                    max_depth=max_depth,
                    depth=depth,
                )
            )

    return result


def display_diff(
    left: Dict[str, str],
    right: Dict[str, str],
    *,
    left_label: str,
    right_label: str,
) -> None:
    """Render diff showing only changed hashes."""
    differences: List[tuple[str, str, str]] = []

    for path in left:
        right_hash = right.get(path, "<missing>")
        if left[path] != right_hash:
            differences.append((path, left[path], right_hash))

    for path in right:
        if path not in left:
            differences.append((path, "<missing>", right[path]))

    if not differences:
        return

    console = Console()
    console.print("── Fixture Hash Differences ──", style="bold")
    console.print(f"[dim]--- {left_label}[/dim]")
    console.print(f"[dim]+++ {right_label}[/dim]")
    console.print()

    for path, left_hash, right_hash in differences:
        depth = path.count("/")
        indent = "  " * (depth + 1)
        console.print(f"{indent}[bold]{rich_escape(path)}[/bold]")
        console.print(f"{indent}  [red]- {left_hash}[/red]")
        console.print(f"{indent}  [green]+ {right_hash}[/green]")
        console.print()


class DefaultGroup(click.Group):
    """Click group with a default command fallback."""

    def __init__(
        self, *args: Any, default_cmd_name: str = "hash", **kwargs: Any
    ):
        super().__init__(*args, **kwargs)
        self.default_cmd_name = default_cmd_name

    def resolve_command(
        self, ctx: click.Context, args: List[str]
    ) -> tuple[Optional[str], Optional[click.Command], List[str]]:
        """Resolve command, inserting default if no subcommand given."""
        first_arg_idx = next(
            (i for i, a in enumerate(args) if not a.startswith("-")), None
        )
        if (
            first_arg_idx is not None
            and args[first_arg_idx] not in self.commands
        ):
            args = list(args)
            args.insert(first_arg_idx, self.default_cmd_name)
        return super().resolve_command(ctx, args)


F = TypeVar("F", bound=Callable[..., None])


def hash_options(func: F) -> F:
    """Decorator for common hash options."""
    func = click.option(
        "--root", "-r", is_flag=True, help="Only print hash of root folder"
    )(func)
    func = click.option(
        "--tests", "-t", is_flag=True, help="Print hash of tests"
    )(func)
    func = click.option(
        "--files", "-f", is_flag=True, help="Print hash of files"
    )(func)
    return func


@click.group(
    cls=DefaultGroup,
    default_cmd_name="hash",
    context_settings={"help_option_names": ["-h", "--help"]},
)
def hasher() -> None:
    """Hash folders of JSON fixtures and compare them."""
    pass


@hasher.command(name="hash")
@click.argument(
    "folder_path_str",
    type=click.Path(
        exists=True, file_okay=False, dir_okay=True, readable=True
    ),
)
@hash_options
def hash_cmd(
    folder_path_str: str, files: bool, tests: bool, root: bool
) -> None:
    """Hash folders of JSON fixtures and print their hashes."""
    lines = render_hash_report(
        Path(folder_path_str), files=files, tests=tests, root=root
    )
    for line in lines:
        print(line)


@hasher.command(name="compare")
@click.argument(
    "left_folder",
    type=click.Path(
        exists=True, file_okay=False, dir_okay=True, readable=True
    ),
)
@click.argument(
    "right_folder",
    type=click.Path(
        exists=True, file_okay=False, dir_okay=True, readable=True
    ),
)
@click.option(
    "--depth",
    "-d",
    type=int,
    default=None,
    help="Limit to N levels (0=root, 1=folders, 2=files, 3=tests).",
)
@hash_options
def compare_cmd(
    left_folder: str,
    right_folder: str,
    files: bool,
    tests: bool,
    root: bool,
    depth: Optional[int],
) -> None:
    """Compare two fixture directories and show differences."""
    try:
        left_item = HashableItem.from_folder(folder_path=Path(left_folder))
        right_item = HashableItem.from_folder(folder_path=Path(right_folder))

        if root:
            if left_item.hash() == right_item.hash():
                sys.exit(0)
            left_hashes = {"root": f"0x{left_item.hash().hex()}"}
            right_hashes = {"root": f"0x{right_item.hash().hex()}"}
        else:
            print_type: Optional[HashableItemType] = None
            if files:
                print_type = HashableItemType.FILE
            elif tests:
                print_type = HashableItemType.TEST

            left_hashes = collect_hashes(
                left_item, print_type=print_type, max_depth=depth
            )
            right_hashes = collect_hashes(
                right_item, print_type=print_type, max_depth=depth
            )

        if left_hashes == right_hashes:
            sys.exit(0)

        display_diff(
            left_hashes,
            right_hashes,
            left_label=left_folder,
            right_label=right_folder,
        )
        sys.exit(1)
    except PermissionError as e:
        click.echo(f"Error: Permission denied - {e}", err=True)
        sys.exit(2)
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        click.echo(f"Error: Invalid fixture format - {e}", err=True)
        sys.exit(2)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(2)


main = hasher  # Entry point alias


if __name__ == "__main__":
    main()
