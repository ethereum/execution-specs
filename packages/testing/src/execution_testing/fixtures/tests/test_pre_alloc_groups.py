"""Tests for conflict-aware packing of pre-allocation groups."""

import json
from pathlib import Path
from typing import Dict

import pytest

from execution_testing.base_types import Account, Address
from execution_testing.fixtures.pre_alloc_groups import (
    TEST_GROUP_INDEX_FILE,
    GroupIndexEntry,
    PreAllocGroupBuilder,
    pack_pre_alloc_groups,
    packed_group_hash_for_test,
    read_test_group_index,
)
from execution_testing.forks import Fork, Osaka, Prague
from execution_testing.test_types import Alloc, AllocGroupHash, Environment


def _write_group(
    folder: Path,
    stem: AllocGroupHash | int,
    test_id: str,
    pre: Dict[int, Account],
    *,
    environment: Environment,
    group_salt: str | None = None,
    fork: Fork = Prague,
) -> None:
    """Write a single fine-grained group file, as Phase 1 would."""
    builder = PreAllocGroupBuilder(
        test_ids=[test_id],
        environment=environment.set_fork_requirements(fork),
        fork=fork,
        group_salt=group_salt,
        group_hash=stem,
        pre=Alloc(
            {Address(address): account for address, account in pre.items()}
        ),
    )
    (folder / f"{builder.group_hash}.json").write_text(
        builder.model_dump_json(by_alias=True, exclude_none=True, indent=2)
    )


def _packed(folder: Path) -> Dict[AllocGroupHash, dict]:
    """Load the packed group files by stem."""
    return {
        AllocGroupHash(file.stem): json.loads(file.read_text())
        for file in folder.glob("*.json")
    }


def test_pack_merges_non_conflicting_groups(tmp_path: Path) -> None:
    """Two groups sharing a genesis but no address merge into one."""
    env = Environment()
    _write_group(
        tmp_path,
        1,
        "tests/a.py::test_a",
        {0x1000: Account(balance=1)},
        environment=env,
    )
    _write_group(
        tmp_path,
        2,
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
        1,
        "tests/a.py::test_a",
        {0x1000: Account(balance=1)},
        environment=env,
    )
    _write_group(
        tmp_path,
        2,
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
        1,
        "tests/a.py::test_a",
        {0x1000: shared, 0x2000: Account(balance=5)},
        environment=env,
    )
    _write_group(
        tmp_path,
        2,
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
        1,
        "tests/a.py::test_a",
        {0x1000: Account(balance=1)},
        environment=Environment(),
    )
    _write_group(
        tmp_path,
        2,
        "tests/b.py::test_b",
        {0x2000: Account(balance=2)},
        environment=Environment(gas_limit=0x1000000),
    )

    pack_pre_alloc_groups(tmp_path)

    assert len(_packed(tmp_path)) == 2


def test_pack_respects_group_salt(tmp_path: Path) -> None:
    """
    A group salted via the `pre_alloc_group` marker never merges with an
    unsalted group or a group carrying a different salt.
    """
    env = Environment()
    _write_group(
        tmp_path,
        1,
        "tests/a.py::test_a",
        {0x1000: Account(balance=1)},
        environment=env,
    )
    _write_group(
        tmp_path,
        2,
        "tests/b.py::test_b",
        {0x2000: Account(balance=2)},
        environment=env,
        group_salt="isolated",
    )
    _write_group(
        tmp_path,
        3,
        "tests/c.py::test_c",
        {0x3000: Account(balance=3)},
        environment=env,
        group_salt="other",
    )

    pack_pre_alloc_groups(tmp_path)

    packed = _packed(tmp_path)
    assert len(packed) == 3
    all_ids = sorted(
        tid for group in packed.values() for tid in group["testIds"]
    )
    assert all_ids == [
        "tests/a.py::test_a",
        "tests/b.py::test_b",
        "tests/c.py::test_c",
    ]


def test_pack_merges_groups_with_matching_salt(tmp_path: Path) -> None:
    """Groups sharing the same explicit salt still pack together."""
    env = Environment()
    _write_group(
        tmp_path,
        1,
        "tests/a.py::test_a",
        {0x1000: Account(balance=1)},
        environment=env,
        group_salt="shared",
    )
    _write_group(
        tmp_path,
        2,
        "tests/b.py::test_b",
        {0x2000: Account(balance=2)},
        environment=env,
        group_salt="shared",
    )

    pack_pre_alloc_groups(tmp_path)

    packed = _packed(tmp_path)
    assert len(packed) == 1
    (group,) = packed.values()
    assert group["groupSalt"] == "shared"


def test_pack_writes_test_group_index(tmp_path: Path) -> None:
    """
    Packing writes a test id -> group hash index that matches the packed
    files' ``testIds`` and is not picked up as a group file itself.
    """
    env = Environment()
    _write_group(
        tmp_path,
        1,
        "tests/a.py::test_a",
        {0x1000: Account(balance=1)},
        environment=env,
    )
    _write_group(
        tmp_path,
        2,
        "tests/b.py::test_b",
        {0x2000: Account(balance=2)},
        environment=env,
    )
    _write_group(
        tmp_path,
        3,
        "tests/c.py::test_c",
        {0x1000: Account(balance=3)},
        environment=env,
    )

    pack_pre_alloc_groups(tmp_path)

    assert (tmp_path / TEST_GROUP_INDEX_FILE).exists()
    packed = _packed(tmp_path)
    assert TEST_GROUP_INDEX_FILE not in packed
    index = read_test_group_index(tmp_path)
    assert sorted(index.root) == [
        "tests/a.py::test_a",
        "tests/b.py::test_b",
        "tests/c.py::test_c",
    ]
    for test_id, entry in index.items():
        assert test_id in packed[entry.group_hash]["testIds"]
    # Every entry records the test's fine-grained phase 1 hash.
    assert index["tests/a.py::test_a"].phase1_hash == AllocGroupHash(1)
    assert index["tests/b.py::test_b"].phase1_hash == AllocGroupHash(2)
    assert index["tests/c.py::test_c"].phase1_hash == AllocGroupHash(3)


def test_read_test_group_index_falls_back_to_scanning(
    tmp_path: Path,
) -> None:
    """A folder without an index file (unpacked/legacy) is scanned."""
    env = Environment()
    _write_group(
        tmp_path,
        1,
        "tests/a.py::test_a",
        {0x1000: Account(balance=1)},
        environment=env,
    )
    _write_group(
        tmp_path,
        2,
        "tests/b.py::test_b",
        {0x2000: Account(balance=2)},
        environment=env,
    )

    assert not (tmp_path / TEST_GROUP_INDEX_FILE).exists()
    assert read_test_group_index(tmp_path).root == {
        "tests/a.py::test_a": GroupIndexEntry(
            group_hash=AllocGroupHash(1), phase1_hash=None
        ),
        "tests/b.py::test_b": GroupIndexEntry(
            group_hash=AllocGroupHash(2), phase1_hash=None
        ),
    }


def test_packed_group_hash_lookup_validates_phase1_hash(
    tmp_path: Path,
) -> None:
    """
    A phase 2 lookup verifies the recomputed phase 1 hash against the
    index fingerprint, so a stale pre-alloc folder fails loudly instead
    of silently filling a changed test against its old genesis.
    """
    env = Environment()
    _write_group(
        tmp_path,
        1,
        "tests/a.py::test_a",
        {0x1000: Account(balance=1)},
        environment=env,
    )
    pack_pre_alloc_groups(tmp_path)
    index = read_test_group_index(tmp_path)

    packed_hash = packed_group_hash_for_test(
        index, "tests/a.py::test_a", phase1_hash=AllocGroupHash(1)
    )
    assert packed_hash == index["tests/a.py::test_a"].group_hash

    with pytest.raises(ValueError, match="stale"):
        packed_group_hash_for_test(
            index, "tests/a.py::test_a", phase1_hash=AllocGroupHash(0xFF)
        )
    with pytest.raises(ValueError, match="not assigned"):
        packed_group_hash_for_test(
            index, "tests/b.py::test_b", phase1_hash=AllocGroupHash(2)
        )


def test_packed_group_hash_lookup_without_fingerprint(
    tmp_path: Path,
) -> None:
    """A scanned (legacy) index has no fingerprints to validate against."""
    env = Environment()
    _write_group(
        tmp_path,
        1,
        "tests/a.py::test_a",
        {0x1000: Account(balance=1)},
        environment=env,
    )

    index = read_test_group_index(tmp_path)
    assert packed_group_hash_for_test(
        index, "tests/a.py::test_a", phase1_hash=AllocGroupHash(0xFF)
    ) == AllocGroupHash(1)


def test_pack_is_deterministic(tmp_path: Path) -> None:
    """Packing the same inputs twice yields the same group ids."""

    def build(folder: Path) -> None:
        folder.mkdir()
        env = Environment()
        for i in range(6):
            _write_group(
                folder,
                i,
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


def test_pack_isolates_funded_precompile(tmp_path: Path) -> None:
    """
    A precompile funded by one test is never merged into a test that
    assumes it empty (precompiles are in the reserved range).
    """
    env = Environment()
    _write_group(
        tmp_path,
        1,
        "tests/a.py::test_a",
        {0x02: Account(balance=1), 0x9000: Account(balance=1)},
        environment=env,
    )
    _write_group(
        tmp_path,
        2,
        "tests/b.py::test_b",
        {0x9001: Account(balance=2)},
        environment=env,
    )

    pack_pre_alloc_groups(tmp_path)

    packed = _packed(tmp_path)
    assert len(packed) == 2
    with_precompile = [
        g
        for g in packed.values()
        if "0x0000000000000000000000000000000000000002" in g["pre"]
    ]
    assert len(with_precompile) == 1
    assert with_precompile[0]["testIds"] == ["tests/a.py::test_a"]


def test_pack_isolates_fork_precompile_above_blanket_range(
    tmp_path: Path,
) -> None:
    """
    An account pinned at a fork precompile address above the blanket
    reserved range (P256VERIFY at ``0x100``, EIP-7951) keeps its group
    isolated on a fork that has the precompile; on an earlier fork the
    same address is plain scratch space and the groups merge.
    """
    env = Environment()
    for fork, expected_group_count in ((Prague, 1), (Osaka, 2)):
        folder = tmp_path / fork.name()
        folder.mkdir()
        _write_group(
            folder,
            1,
            "tests/a.py::test_a",
            {0x100: Account(balance=1)},
            environment=env,
            fork=fork,
        )
        _write_group(
            folder,
            2,
            "tests/b.py::test_b",
            {0x2000: Account(balance=2)},
            environment=env,
            fork=fork,
        )

        pack_pre_alloc_groups(folder)

        assert len(_packed(folder)) == expected_group_count, fork.name()


def test_pack_merges_when_shared_address_agrees(tmp_path: Path) -> None:
    """
    Groups that agree on a shared (canonical) address and differ only in
    test-private addresses still merge into one.
    """
    env = Environment()
    shared = Account(balance=1, nonce=1)
    for stem, test_id, private in [
        (1, "tests/a.py::test_a", 0xA000),
        (2, "tests/b.py::test_b", 0xB000),
        (3, "tests/c.py::test_c", 0xC000),
    ]:
        _write_group(
            tmp_path,
            stem,
            test_id,
            {0x9000: shared, private: Account(balance=2)},
            environment=env,
        )

    pack_pre_alloc_groups(tmp_path)

    assert len(_packed(tmp_path)) == 1


def test_pack_isolates_disagreeing_shared_address(tmp_path: Path) -> None:
    """
    A shared address present in some groups but absent from others keeps
    them apart, so it is never leaked into a test that omits it.
    """
    env = Environment()
    shared = Account(balance=1, nonce=1)
    _write_group(
        tmp_path,
        1,
        "tests/a.py::test_a",
        {0x9000: shared, 0xA000: Account(balance=2)},
        environment=env,
    )
    _write_group(
        tmp_path,
        2,
        "tests/b.py::test_b",
        {0x9000: shared, 0xB000: Account(balance=2)},
        environment=env,
    )
    _write_group(
        tmp_path,
        3,
        "tests/c.py::test_c",
        {0xC000: Account(balance=2)},
        environment=env,
    )

    pack_pre_alloc_groups(tmp_path)

    packed = _packed(tmp_path)
    assert len(packed) == 2
    all_ids = sorted(
        tid for group in packed.values() for tid in group["testIds"]
    )
    assert all_ids == [
        "tests/a.py::test_a",
        "tests/b.py::test_b",
        "tests/c.py::test_c",
    ]
