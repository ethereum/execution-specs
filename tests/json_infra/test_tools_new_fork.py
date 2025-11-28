"""
Tests for the ethereum-spec-new-fork CLI tool.
"""

from pathlib import Path
from tempfile import TemporaryDirectory

import libcst as cst
import pytest
from libcst.codemod import CodemodContext

from ethereum_spec_tools.forks import Hardfork
from ethereum_spec_tools.new_fork.cli import main as new_fork
from ethereum_spec_tools.new_fork.codemod.remove_docstring import (
    RemoveDocstringCommand,
)


@pytest.mark.parametrize(
    "template_fork",
    [
        Hardfork.discover()[-1].short_name,
        "osaka",
    ],
    ids=lambda tf: f"{tf}",
)
def test_end_to_end(template_fork: str) -> None:
    """
    Test that the ethereum-spec-new-fork CLI tool creates a fork from a
    template, correctly modifying names, blob parameters, and imports.
    """
    with TemporaryDirectory() as base_dir:
        output_dir = Path(base_dir) / "ethereum"
        fork_dir = output_dir / "e2e_fork"

        new_fork(
            [
                "--new-fork",
                "e2e_fork",
                "--template-fork",
                template_fork,
                "--target-blob-gas-per-block",
                "199",
                "--blob-base-fee-update-fraction",
                "750",
                "--min-blob-gasprice",
                "2",
                "--gas-per-blob",
                "1",
                "--at-timestamp",
                "7",
                "--max-blob-gas-per-block",
                "99",
                "--blob-schedule-target",
                "88",
                "--output",
                str(output_dir),
            ]
        )

        with (fork_dir / "__init__.py").open("r") as f:
            source = f.read()

            assert '"""' not in source[:20]
            assert "FORK_CRITERIA: ForkCriteria = ByTimestamp(7)" in source
            assert template_fork.capitalize() not in source

        with (fork_dir / "utils" / "hexadecimal.py").open("r") as f:
            source = f.read()
            assert "E2E Fork" in source

        with (fork_dir / "vm" / "gas.py").open("r") as f:
            source = f.read()

            expected = [
                "TARGET_BLOB_GAS_PER_BLOCK = U64(199)",
                "GAS_PER_BLOB = U64(1)",
                "MIN_BLOB_GASPRICE = Uint(2)",
                "BLOB_BASE_FEE_UPDATE_FRACTION = Uint(750)",
                "BLOB_SCHEDULE_TARGET = U64(88)",
            ]

            for needle in expected:
                assert needle in source

        with (fork_dir / "fork.py").open("r") as f:
            assert "MAX_BLOB_GAS_PER_BLOCK = U64(99)" in f.read()

        with (fork_dir / "trie.py").open("r") as f:
            assert (
                "from ethereum.forks.paris import trie as previous_trie"
                in f.read()
            )


def has_module_docstring(file_path: Path) -> bool:
    """Return True if the file starts with a module-level doc-string."""
    tree = cst.parse_module(file_path.read_text())
    if not tree.body:
        return False
    first = tree.body[0]
    if not isinstance(first, cst.SimpleStatementLine):
        return False
    if len(first.body) != 1:
        return False
    expr = first.body[0]
    return isinstance(expr, cst.Expr) and isinstance(
        expr.value, cst.SimpleString
    )


def test_remove_docstring_command() -> None:
    """Test that RemoveDocstringCommand removes module docstrings."""
    source = '"""Module docstring."""\n\nsome_var = 123\n'
    module = cst.parse_module(source)
    context = CodemodContext()
    command = RemoveDocstringCommand(context)

    new_module = command.transform_module(module)
    result = new_module.code

    assert '"""Module docstring."""' not in result
    assert "some_var = 123" in result


def test_remove_docstring_preserves_other_docstrings() -> None:
    """Test that function/class docstrings are preserved."""
    source = '''"""Module docstring."""

def foo():
    """Function docstring."""
    pass
'''
    module = cst.parse_module(source)
    context = CodemodContext()
    command = RemoveDocstringCommand(context)

    new_module = command.transform_module(module)
    result = new_module.code

    assert not result.startswith('"""Module docstring."""')
    assert '"""Function docstring."""' in result


def test_remove_docstring_handles_files_without_docstrings() -> None:
    """Test that files without docstrings remain unchanged."""
    source_without_docstring = "some_var = 123\n\ndef foo():\n    pass\n"
    module = cst.parse_module(source_without_docstring)
    context = CodemodContext()
    command = RemoveDocstringCommand(context)

    new_module = command.transform_module(module)

    assert new_module.code == source_without_docstring


def test_remove_docstring_handles_empty_files() -> None:
    """Test that empty files remain empty."""
    source_empty = ""
    module = cst.parse_module(source_empty)
    context = CodemodContext()
    command = RemoveDocstringCommand(context)

    new_module = command.transform_module(module)

    assert new_module.code == source_empty
