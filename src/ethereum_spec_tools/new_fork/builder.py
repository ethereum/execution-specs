"""
Defines `ForkBuilder`, a class that can take a template fork and transform it
into a new fork.
"""

import json
import re
import sys
import warnings
from abc import ABC, abstractmethod
from contextlib import ExitStack, chdir
from dataclasses import dataclass, field
from pathlib import Path
from shutil import copytree, ignore_patterns, rmtree
from tempfile import TemporaryDirectory
from typing import ClassVar, Final, NamedTuple

from ethereum_types.numeric import U64, U256, Uint
from libcst.tool import main as libcst_tool
from typing_extensions import override

from ethereum.fork_criteria import (
    ByBlockNumber,
    ByTimestamp,
    ForkCriteria,
    Unscheduled,
)

from ..forks import Hardfork


def _source_file_for(fork_root: Path, qualified_name: str) -> Path:
    """
    Resolve the source file that defines `qualified_name` within `fork_root`.

    Walk the dotted name from its longest module prefix to its shortest,
    returning the first prefix that resolves to a module file (or package
    `__init__.py`). Fall back to the fork's `__init__.py` for names bound
    directly in the package. Used to scope constant codemods to a single file
    instead of re-parsing the whole fork.
    """
    parts = qualified_name.split(".")
    for length in range(len(parts) - 1, 0, -1):
        module = fork_root.joinpath(*parts[:length])
        if module.with_suffix(".py").is_file():
            return module.with_suffix(".py")
        if (module / "__init__.py").is_file():
            return module / "__init__.py"
    return fork_root / "__init__.py"


def _assigns(source_file: Path, name: str) -> bool:
    """
    Return whether `source_file` assigns a value to `name`.

    Constants occasionally move between a fork's modules, so a modifier that
    accepts more than one template layout uses this to pick the qualified name
    that the template actually defines.
    """
    pattern = re.compile(rf"^\s*{re.escape(name)}\s*[:=]", re.MULTILINE)
    return pattern.search(source_file.read_text()) is not None


@dataclass
class CodemodArgs(ABC):
    """
    Description of a libcst codemod as understood by `libcst.tool:main`.
    """

    @abstractmethod
    def _to_args(
        self, fork_builder: "ForkBuilder", working_directory: Path
    ) -> list[list[str]]:
        raise NotImplementedError


@dataclass
class RenameFork(CodemodArgs):
    """
    Describe how to rename a fork to `libcst.tool:main`.
    """

    @override
    def _to_args(
        self, fork_builder: "ForkBuilder", working_directory: Path
    ) -> list[list[str]]:
        prefix = ".".join(fork_builder.template_fork.name.split(".")[:-1])

        commands = [
            [
                "codemod",
                "rename.RenameCommand",
                "--no-format",
                "--old_name",
                fork_builder.template_fork.name,
                "--new_name",
                f"{prefix}{fork_builder.new_fork}",
                str(working_directory),
            ]
        ]

        forks = Hardfork.discover()
        before_fork = None
        for fork in forks:
            if fork.criteria >= fork_builder.fork_criteria:
                break
            before_fork = fork

        if before_fork is None:
            if fork_builder.before_template_fork is not None:
                warnings.warn(
                    "creating genesis fork from a non-genesis fork "
                    + f"(`{fork_builder.template_fork.short_name}`)",
                    stacklevel=2,
                )
            return commands

        if fork_builder.before_template_fork is None:
            warnings.warn(
                "creating non-genesis fork from a genesis fork "
                + f"(`{fork_builder.template_fork.short_name}`)",
                stacklevel=2,
            )
            return commands

        commands.append(
            [
                "codemod",
                "rename.RenameCommand",
                "--no-format",
                "--old_name",
                fork_builder.before_template_fork.name,
                "--new_name",
                before_fork.name,
                str(working_directory),
            ]
        )

        return commands


class _Replacement(NamedTuple):
    qualified_name: str
    value: str
    imports: list[tuple[str, str]]


@dataclass
class ReplaceValue(CodemodArgs, ABC):
    """
    Base class for codemod descriptions that replace the value of an
    assignment.
    """

    @abstractmethod
    def _replacement(
        self, fork_builder: "ForkBuilder", working_directory: Path
    ) -> _Replacement:
        raise NotImplementedError

    @override
    def _to_args(
        self, fork_builder: "ForkBuilder", working_directory: Path
    ) -> list[list[str]]:
        qualified_name, value, imports = self._replacement(
            fork_builder, working_directory
        )

        output = fork_builder.output
        assert output is not None

        fully_qualified_name = (
            f"ethereum.{fork_builder.new_fork}.{qualified_name}"
        )

        fork_root = working_directory / "ethereum" / fork_builder.new_fork
        target = _source_file_for(fork_root, qualified_name)

        command = [
            "codemod",
            "-j1",
            "constant.SetConstantCommand",
            "--no-format",
            "--qualified-name",
            fully_qualified_name,
            "--value",
            value,
            str(target),
        ]

        for module, identifier in imports:
            command.extend(
                [
                    "--import",
                    module,
                    identifier,
                ]
            )

        return [command]


@dataclass
class SetConstant(ReplaceValue):
    """
    Instruct `libcst.tool:main` to replace the value of a constant.
    """

    qualified_name: str
    value: str
    imports: list[tuple[(str, str)]] = field(default_factory=list)

    @override
    def _replacement(
        self, fork_builder: "ForkBuilder", working_directory: Path
    ) -> _Replacement:
        return _Replacement(self.qualified_name, self.value, self.imports)


@dataclass
class SetMaxBlobGasPerBlock(ReplaceValue):
    """
    Instruct `libcst.tool:main` to replace the value of
    `MAX_BLOB_GAS_PER_BLOCK`, wherever the template fork defines it.
    """

    value: str

    # TODO: Replace this class with a plain `SetConstant` targeting
    # `vm.gas.MAX_BLOB_GAS_PER_BLOCK` once every fork usable as a template
    # defines the constant there (i.e. once the pre-Amsterdam forks, which
    # define it in `fork`, are gone).
    candidates: ClassVar[tuple[str, ...]] = (
        "vm.gas.MAX_BLOB_GAS_PER_BLOCK",
        "fork.MAX_BLOB_GAS_PER_BLOCK",
    )

    @override
    def _replacement(
        self, fork_builder: "ForkBuilder", working_directory: Path
    ) -> _Replacement:
        fork_root = working_directory / "ethereum" / fork_builder.new_fork

        for qualified_name in self.candidates:
            source = _source_file_for(fork_root, qualified_name)
            if _assigns(source, "MAX_BLOB_GAS_PER_BLOCK"):
                return _Replacement(qualified_name, self.value, [])

        raise Exception(
            "template fork defines MAX_BLOB_GAS_PER_BLOCK in none of: "
            + ", ".join(self.candidates)
        )


@dataclass
class SetForkCriteria(ReplaceValue):
    """
    Instruct `libcst.tool:main` to replace the value of `FORK_CRITERIA`.
    """

    @override
    def _replacement(
        self, fork_builder: "ForkBuilder", working_directory: Path
    ) -> _Replacement:
        return _Replacement(
            "FORK_CRITERIA",
            repr(fork_builder.fork_criteria),
            [
                ("ethereum.fork_criteria", "Unscheduled"),
                ("ethereum.fork_criteria", "ByBlockNumber"),
                ("ethereum.fork_criteria", "ByTimestamp"),
            ],
        )


@dataclass
class ReplaceForkName(CodemodArgs):
    """
    Replace occurrences of the template fork name with the new fork's name.
    """

    @override
    def _to_args(
        self, fork_builder: "ForkBuilder", working_directory: Path
    ) -> list[list[str]]:
        new_fork_title_case = fork_builder.new_fork.removeprefix("bpo")
        if new_fork_title_case == fork_builder.new_fork:
            new_fork_title_case = fork_builder.new_fork.replace(
                "_", " "
            ).title()
        else:
            new_fork_title_case = "BPO" + new_fork_title_case

        common = [
            str(working_directory),
            "--replace",
            fork_builder.template_fork.short_name,
            fork_builder.new_fork,
            "--replace",
            fork_builder.template_fork.title_case_name,
            new_fork_title_case,
            "--replace",
            fork_builder.template_fork.title_case_name.lower(),
            fork_builder.new_fork.replace("_", " ").lower(),
        ]

        commands = [
            [
                "codemod",
                "--no-format",
                "string_replace.StringReplaceCommand",
            ]
            + common,
            [
                "codemod",
                "--no-format",
                "comment.CommentReplaceCommand",
            ]
            + common,
        ]

        return commands


@dataclass
class ClearDocstring(CodemodArgs):
    """
    Describe how to clear the docstring in __init__.py to libcst.tool:main.
    """

    @override
    def _to_args(
        self, fork_builder: "ForkBuilder", working_directory: Path
    ) -> list[list[str]]:
        init_path = (
            working_directory
            / "ethereum"
            / fork_builder.new_fork
            / "__init__.py"
        )
        return [
            [
                "codemod",
                "-j1",
                "remove_docstring.RemoveDocstringCommand",
                "--no-format",
                str(init_path),
            ]
        ]


class ForkBuilder:
    """
    Takes a template fork and uses it to generate a new fork, applying source
    code transformations along the way.
    """

    before_template_fork: Final[Hardfork | None]
    """
    Fork immediately before `template_fork`, if one exists (else `None`).

    Necessary because some modules (notably `trie.py`) import types from the
    preceding fork, and those references need to be updated.
    """

    template_fork: Final[Hardfork]
    """
    Fork that is copied and modified into the new fork.
    """

    new_fork: Final[str]
    """
    Name of the new fork as a Python-friendly identifier.

    For example, `"spurious_dragon"` and not `"Spurious Dragon"`.
    """

    output: Path | None
    """
    Directory to place the new fork into, not including the fork itself.

    For example, to place `frontier` into `src/ethereum/frontier`, this value
    would be `src/ethereum`.

    Defaults to the parent directory of `template_fork` (or `None` if one
    cannot be found). Can be overwritten.
    """

    force: bool
    """
    Replace the destination if `True`, otherwise error if the destination
    already exists.
    """

    modifiers: list[CodemodArgs]
    """
    Ordered list of code modifiers to apply while creating the new fork.
    """

    fork_criteria: ForkCriteria
    """
    When the new fork is scheduled.
    """

    @property
    def new_fork_path(self) -> Path:
        """
        The output directory plus the new fork's short name.
        """
        output = self.output
        if output is None:
            raise ValueError(
                "no output directory found (set one with --output)"
            )
        return output / self.new_fork

    def __init__(
        self,
        template_fork: str,
        new_fork: str,
    ) -> None:
        self.force = False

        forks = Hardfork.discover()

        # Find the `Hardfork` object named by `template_fork`.
        before = None
        found = None
        for index, fork in enumerate(forks):
            if fork.short_name == template_fork:
                found = fork
                if index > 0:
                    before = forks[index - 1]
                break

        if found is None:
            raise ValueError(f"no fork named `{template_fork}` found")

        if before:
            assert before.short_name != new_fork

        self.before_template_fork = before
        self.template_fork = found
        self.new_fork = new_fork

        # Compute `self.output` based on `template_fork`'s location.
        self.output = None
        template_path = self.template_fork.path
        if template_path is not None:
            self.output = Path(template_path).parent

        # Try to make a sane guess for the activation criteria.
        if found is forks[-1] or isinstance(found.criteria, Unscheduled):
            order_index = 0

            # check template fork's criteria and bump order_index if needed
            if isinstance(found.criteria, Unscheduled):
                order_index = found.criteria._internal[1] + 1

            self.fork_criteria = Unscheduled(order_index=order_index)
        elif hasattr(found.criteria, "timestamp"):
            self.fork_criteria = ByTimestamp(
                U256(found.criteria.timestamp) + U256(1)
            )
        elif hasattr(found.criteria, "block_number"):
            self.fork_criteria = ByBlockNumber(
                Uint(found.criteria.block_number) + Uint(1)
            )
        else:
            raise Exception(f"unknown `FORK_CRITERIA` in `{template_fork}`")

        self.modifiers = [
            RenameFork(),
            SetForkCriteria(),
            ReplaceForkName(),
            ClearDocstring(),
        ]

    def _create_working_directory(self) -> TemporaryDirectory:
        """
        Create a temporary working directory so we don't end up in the state
        where this process ~~barfs~~ abnormally terminates and we leave a
        half-modified fork directory lying around.
        """
        output = self.new_fork_path.parent
        output.mkdir(parents=True, exist_ok=True)
        return TemporaryDirectory(dir=output, prefix=".tmp-fork-")

    def _commit(self, fork_directory: Path) -> None:
        if self.force:
            rmtree(self.new_fork_path, ignore_errors=True)
        fork_directory.rename(self.new_fork_path)

    def _copy(self, fork_directory: Path) -> None:
        template_path = self.template_fork.path
        if template_path is None:
            raise Exception(
                f"fork `{self.template_fork.short_name}` has no path"
            )

        # Skip `__pycache__`: copying compiled bytecode into a new fork is
        # pointless, and its transient `.pyc.<id>` files race with concurrent
        # bytecode writes, breaking `copytree` under parallel test runs.
        copytree(
            template_path,
            fork_directory,
            ignore=ignore_patterns("__pycache__", "*.pyc"),
            dirs_exist_ok=True,
        )

    def _write_config(
        self, config_path: str, working_directory: TemporaryDirectory
    ) -> None:
        config = {
            "generated_code_marker": "@generated",
            "blacklist_patterns": [],
            "formatter": ["cat", "-"],
            "modules": [
                "libcst.codemod.commands",
                "ethereum_spec_tools.new_fork.codemod",
            ],
            "repo_root": working_directory.name,
        }
        with open(Path(config_path) / ".libcst.codemod.yaml", "w") as f:
            json.dump(config, f)  # YAML is a superset of JSON

    def _modify(self, working_directory: TemporaryDirectory) -> None:
        for modifier in self.modifiers:
            for args in modifier._to_args(self, Path(working_directory.name)):
                with TemporaryDirectory() as config_directory:
                    with chdir(config_directory):
                        self._write_config(config_directory, working_directory)
                        exit_code = libcst_tool(
                            "<libcst_tool>",
                            args,
                        )
                        if exit_code != 0:
                            sys.exit(exit_code)

    def build(self) -> None:
        """
        Duplicate and transform the template fork into the new fork.
        """
        with ExitStack() as exit_stack:
            working_directory = self._create_working_directory()
            exit_stack.push(working_directory)

            package = Path(working_directory.name) / "ethereum" / self.new_fork
            package.mkdir(parents=True)

            self._copy(package)
            self._modify(working_directory)
            self._commit(package)

    def modify_target_blob_gas_per_block(
        self, blob_target_gas_per_block: U64
    ) -> None:
        """Append a `CodemodArgs` that sets `BLOB_TARGET_GAS_PER_BLOCK`."""
        self.modifiers.append(
            SetConstant(
                "vm.gas.GasCosts.BLOB_TARGET_GAS_PER_BLOCK",
                repr(blob_target_gas_per_block),
            )
        )

    def modify_gas_per_blob(self, gas_per_blob: U64) -> None:
        """Append a `CodemodArgs` that sets `PER_BLOB`."""
        self.modifiers.append(
            SetConstant(
                "vm.gas.GasCosts.PER_BLOB",
                repr(gas_per_blob),
            )
        )

    def modify_min_blob_gasprice(self, blob_min_gasprice: Uint) -> None:
        """Append a `CodemodArgs` that sets `BLOB_MIN_GASPRICE`."""
        self.modifiers.append(
            SetConstant(
                "vm.gas.GasCosts.BLOB_MIN_GASPRICE",
                repr(blob_min_gasprice),
            )
        )

    def modify_blob_base_fee_update_fraction(
        self, blob_base_fee_update_fraction: Uint
    ) -> None:
        """Append a `CodemodArgs` that sets `BLOB_BASE_FEE_UPDATE_FRACTION`."""
        self.modifiers.append(
            SetConstant(
                "vm.gas.GasCosts.BLOB_BASE_FEE_UPDATE_FRACTION",
                repr(blob_base_fee_update_fraction),
            )
        )

    def modify_max_blob_gas_per_block(
        self, max_blob_gas_per_block: U64
    ) -> None:
        """Append a `CodemodArgs` that sets `MAX_BLOB_GAS_PER_BLOCK`."""
        self.modifiers.append(
            SetMaxBlobGasPerBlock(repr(max_blob_gas_per_block))
        )

    def modify_blob_schedule_target(self, blob_schedule_target: U64) -> None:
        """Append a `CodemodArgs` that sets `BLOB_SCHEDULE_TARGET`."""
        self.modifiers.append(
            SetConstant(
                "vm.gas.GasCosts.BLOB_SCHEDULE_TARGET",
                repr(blob_schedule_target),
            )
        )

    def modify_blob_schedule_max(self, blob_schedule_max: U64) -> None:
        """Append a `CodemodArgs` that sets `BLOB_SCHEDULE_MAX`."""
        self.modifiers.append(
            SetConstant(
                "vm.gas.GasCosts.BLOB_SCHEDULE_MAX",
                repr(blob_schedule_max),
            )
        )
