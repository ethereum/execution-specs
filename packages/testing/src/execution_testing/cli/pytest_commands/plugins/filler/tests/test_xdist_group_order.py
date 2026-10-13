"""Test the order in which fill hands test groups to xdist workers."""

import re
import textwrap
from typing import Any, List

import pytest

GROUPS_MODULE = """\
import pytest

from execution_testing import Alloc, Block, BlockchainTestFiller


@pytest.mark.valid_at("Prague")
def test_another_group(
    pre: Alloc, blockchain_test: BlockchainTestFiller
) -> None:
    blockchain_test(pre=pre, blocks=[Block(txs=[])], post={})


@pytest.mark.valid_at("Prague")
@pytest.mark.xdist_group(name="large")
@pytest.mark.parametrize("case", range(3))
def test_large_group(
    pre: Alloc, blockchain_test: BlockchainTestFiller, case: int
) -> None:
    blockchain_test(pre=pre, blocks=[Block(txs=[])], post={})


@pytest.mark.valid_at("Prague")
@pytest.mark.slow
def test_slow_group(
    pre: Alloc, blockchain_test: BlockchainTestFiller
) -> None:
    blockchain_test(pre=pre, blocks=[Block(txs=[])], post={})
"""


def _run_order(lines: List[str]) -> List[str]:
    """Return the test functions in the order they ran, one per group."""
    order: List[str] = []
    for line in lines:
        match = re.search(r"::(test_\w+_group)\[", line)
        if match and "[gw0]" in line and match.group(1) not in order:
            order.append(match.group(1))
    return order


def test_xdist_runs_slow_then_large_groups_first(
    pytester: pytest.Pytester, capsys: Any
) -> None:
    """
    Hand slow groups to workers first, then larger groups.

    xdist sorts groups by size by default, which sent slow tests with few
    fixture formats out mid-run, so they finished minutes after every
    other worker.
    """
    test_dir = pytester.mkdir("tests") / "prague"
    test_dir.mkdir()
    test_module = test_dir / "test_group_order.py"
    test_module.write_text(textwrap.dedent(GROUPS_MODULE))
    pytester.copy_example(
        name=(
            "src/execution_testing/cli/pytest_commands/pytest_ini_files/"
            "pytest-fill.ini"
        )
    )
    result = pytester.runpytest_subprocess(
        "-c",
        "pytest-fill.ini",
        "--fork",
        "Prague",
        "-n",
        "1",
        "-v",
        "--no-html",
        "--output",
        str(pytester.path / "fixtures"),
        str(test_module.relative_to(pytester.path)),
    )
    capsys.readouterr()
    assert result.ret == pytest.ExitCode.OK
    assert _run_order(result.outlines) == [
        "test_slow_group",
        "test_large_group",
        "test_another_group",
    ]
