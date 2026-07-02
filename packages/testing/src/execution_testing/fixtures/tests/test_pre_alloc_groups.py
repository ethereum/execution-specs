"""Tests for conflict-aware packing of pre-allocation groups."""

import json
from pathlib import Path
from typing import Dict

from execution_testing.base_types import Account, Address
from execution_testing.fixtures.pre_alloc_groups import (
    PreAllocGroupBuilder,
    pack_pre_alloc_groups,
)
from execution_testing.forks import Prague
from execution_testing.test_types import Alloc, Environment


def _write_group(
    folder: Path,
    stem: str,
    test_id: str,
    pre: Dict[int, Account],
    *,
    environment: Environment,
) -> None:
    """Write a single fine-grained group file, as Phase 1 would."""
    builder = PreAllocGroupBuilder(
        test_ids=[test_id],
        environment=environment,
        fork=Prague,
        pre=Alloc(
            {Address(address): account for address, account in pre.items()}
        ),
    )
    (folder / f"{stem}.json").write_text(
        builder.model_dump_json(by_alias=True, exclude_none=True, indent=2)
    )


def _packed(folder: Path) -> Dict[str, dict]:
    """Load the packed group files by stem."""
    return {
        file.stem: json.loads(file.read_text())
        for file in folder.glob("*.json")
    }


def test_pack_merges_non_conflicting_groups(tmp_path: Path) -> None:
    """Two groups sharing a genesis but no address merge into one."""
    env = Environment()
    _write_group(
        tmp_path,
        "0x01",
        "tests/a.py::test_a",
        {0x1000: Account(balance=1)},
        environment=env,
    )
    _write_group(
        tmp_path,
        "0x02",
        "tests/b.py::test_b",
        {0x2000: Account(balance=2)},
        environment=env,
    )

    pack_pre_alloc_groups(tmp_path)

    packed = _packed(tmp_path)
    assert len(packed) == 1
    (group,) = packed.values()
    assert sorted(group["testIds"]) == [
        "tests/a.py::test_a",
        "tests/b.py::test_b",
    ]
    assert set(group["pre"]) == {
        "0x0000000000000000000000000000000000001000",
        "0x0000000000000000000000000000000000002000",
    }


def test_pack_keeps_conflicting_groups_apart(tmp_path: Path) -> None:
    """The same address with different accounts cannot be merged."""
    env = Environment()
    _write_group(
        tmp_path,
        "0x01",
        "tests/a.py::test_a",
        {0x1000: Account(balance=1)},
        environment=env,
    )
    _write_group(
        tmp_path,
        "0x02",
        "tests/b.py::test_b",
        {0x1000: Account(balance=2)},
        environment=env,
    )

    pack_pre_alloc_groups(tmp_path)

    packed = _packed(tmp_path)
    assert len(packed) == 2
    # Every test is still represented exactly once.
    all_ids = sorted(
        tid for group in packed.values() for tid in group["testIds"]
    )
    assert all_ids == ["tests/a.py::test_a", "tests/b.py::test_b"]


def test_pack_merges_identical_account_at_shared_address(
    tmp_path: Path,
) -> None:
    """
    A shared address with the *same* account (e.g. a system contract) is
    not a conflict.
    """
    env = Environment()
    shared = Account(balance=1, nonce=1)
    _write_group(
        tmp_path,
        "0x01",
        "tests/a.py::test_a",
        {0x1000: shared, 0x2000: Account(balance=5)},
        environment=env,
    )
    _write_group(
        tmp_path,
        "0x02",
        "tests/b.py::test_b",
        {0x1000: shared, 0x3000: Account(balance=6)},
        environment=env,
    )

    pack_pre_alloc_groups(tmp_path)

    assert len(_packed(tmp_path)) == 1


def test_pack_separates_distinct_environments(tmp_path: Path) -> None:
    """Groups with different genesis environments never merge."""
    _write_group(
        tmp_path,
        "0x01",
        "tests/a.py::test_a",
        {0x1000: Account(balance=1)},
        environment=Environment(),
    )
    _write_group(
        tmp_path,
        "0x02",
        "tests/b.py::test_b",
        {0x2000: Account(balance=2)},
        environment=Environment(gas_limit=0x1000000),
    )

    pack_pre_alloc_groups(tmp_path)

    assert len(_packed(tmp_path)) == 2


def test_pack_is_deterministic(tmp_path: Path) -> None:
    """Packing the same inputs twice yields the same group ids."""

    def build(folder: Path) -> None:
        folder.mkdir()
        env = Environment()
        for i in range(6):
            _write_group(
                folder,
                f"0x0{i}",
                f"tests/t{i}.py::test_{i}",
                {0x1000 + i: Account(balance=i)},
                environment=env,
            )

    first, second = tmp_path / "first", tmp_path / "second"
    build(first)
    build(second)
    pack_pre_alloc_groups(first)
    pack_pre_alloc_groups(second)

    assert set(_packed(first)) == set(_packed(second))
