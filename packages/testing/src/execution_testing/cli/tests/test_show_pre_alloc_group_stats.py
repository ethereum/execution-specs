"""Tests for the pre-allocation group statistics CLI."""

import json
from pathlib import Path

from click.testing import CliRunner

from execution_testing.cli.show_pre_alloc_group_stats import (
    analyze_pre_alloc_folder,
    main,
)


def _write_group(
    folder: Path,
    group_hash: str,
    *,
    test_ids: list[str],
    network: str = "Prague",
    chain_id: int = 1,
    environment: dict[str, str] | None = None,
    pre_accounts: int = 1,
    group_salt: str | None = None,
) -> None:
    """Write a minimal pre-alloc group fixture."""
    payload = {
        "testIds": test_ids,
        "environment": environment or {"currentNumber": "0x00"},
        "network": network,
        "chainId": chain_id,
        "pre": {
            f"0x{account:040x}": {
                "nonce": "0x00",
                "balance": "0x00",
                "code": "0x",
                "storage": {},
            }
            for account in range(pre_accounts)
        },
    }
    if group_salt is not None:
        payload["groupSalt"] = group_salt
    (folder / f"{group_hash}.json").write_text(json.dumps(payload))


def _write_genesis_format_group(
    folder: Path,
    group_hash: str,
    *,
    test_ids: list[str],
    network: str = "Prague",
    timestamp: str = "0x00",
    state_root: str = "0x00",
    pre_accounts: int = 1,
) -> None:
    """
    Write a group in the newer format: a derived ``genesis`` header (with
    pre-state dependent ``stateRoot`` and ``hash``) instead of the grouping
    ``environment``, and a zero-padded hex ``chainId``.
    """
    payload = {
        "testIds": test_ids,
        "network": network,
        "chainId": "0x01",
        "genesis": {
            "timestamp": timestamp,
            "gasLimit": "0x016345785d8a0000",
            "stateRoot": state_root,
            "hash": f"0xbeef{state_root[2:]}",
        },
        "pre": {
            f"0x{account:040x}": {
                "nonce": "0x00",
                "balance": "0x00",
                "code": "0x",
                "storage": {},
            }
            for account in range(pre_accounts)
        },
    }
    (folder / f"{group_hash}.json").write_text(json.dumps(payload))


def test_analyze_pre_alloc_folder_reports_low_count_candidate_buckets(
    tmp_path: Path,
) -> None:
    """Low-count groups sharing a genesis key are ranked as candidates."""
    shared_environment = {"currentNumber": "0x01"}
    _write_group(
        tmp_path,
        "0xaaa",
        test_ids=["tests/prague/foo/test_bar.py::test_case[fork_Prague-a]"],
        environment=shared_environment,
        pre_accounts=3,
    )
    _write_group(
        tmp_path,
        "0xbbb",
        test_ids=["tests/prague/foo/test_bar.py::test_case[fork_Prague-b]"],
        environment=shared_environment,
        pre_accounts=2,
    )
    _write_group(
        tmp_path,
        "0xccc",
        test_ids=[
            "tests/prague/foo/test_other.py::test_other[fork_Prague-a]",
            "tests/prague/foo/test_other.py::test_other[fork_Prague-b]",
            "tests/prague/foo/test_other.py::test_other[fork_Prague-c]",
        ],
        environment={"currentNumber": "0x02"},
        pre_accounts=1,
    )

    stats = analyze_pre_alloc_folder(
        tmp_path,
        low_test_count=1,
        limit=0,
        include_test_ids=True,
    )

    assert stats["total_groups"] == 3
    assert stats["singleton_group_count"] == 2
    assert stats["optimization"]["candidate_buckets_total"] == 1
    candidate = stats["optimization"]["candidate_buckets"][0]
    assert candidate["group_hashes"] == ["0xaaa", "0xbbb"]
    assert candidate["low_group_hashes"] == ["0xaaa", "0xbbb"]
    assert candidate["singleton_groups"] == 2
    assert candidate["test_ids"] == [
        "tests/prague/foo/test_bar.py::test_case[fork_Prague-a]",
        "tests/prague/foo/test_bar.py::test_case[fork_Prague-b]",
    ]


def test_analyze_pre_alloc_folder_buckets_genesis_format_groups(
    tmp_path: Path,
) -> None:
    """
    Groups in the newer genesis-header format bucket on the genesis header
    minus its pre-state dependent fields, and hex chain IDs parse as ints.
    """
    _write_genesis_format_group(
        tmp_path,
        "0xaaa",
        test_ids=["tests/prague/foo/test_bar.py::test_case[fork_Prague-a]"],
        state_root="0x01",
    )
    _write_genesis_format_group(
        tmp_path,
        "0xbbb",
        test_ids=["tests/prague/foo/test_bar.py::test_case[fork_Prague-b]"],
        state_root="0x02",
    )
    _write_genesis_format_group(
        tmp_path,
        "0xccc",
        test_ids=["tests/prague/foo/test_other.py::test_other[fork_Prague]"],
        timestamp="0x0c",
        state_root="0x03",
    )

    stats = analyze_pre_alloc_folder(tmp_path, low_test_count=1, limit=0)

    assert stats["total_groups"] == 3
    assert stats["optimization"]["candidate_buckets_total"] == 1
    candidate = stats["optimization"]["candidate_buckets"][0]
    assert candidate["chain_id"] == 1
    assert candidate["group_hashes"] == ["0xaaa", "0xbbb"]


def test_groupstats_json_output_is_machine_readable(tmp_path: Path) -> None:
    """The CLI should emit JSON without rich console markup."""
    _write_group(
        tmp_path,
        "0xaaa",
        test_ids=["tests/prague/foo/test_bar.py::test_case[fork_Prague-a]"],
    )

    result = CliRunner().invoke(
        main,
        [
            str(tmp_path),
            "--output",
            "json",
            "--low-test-count",
            "1",
            "--include-test-ids",
            "--compact",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["parameters"]["include_test_ids"] is True
    assert payload["parameters"]["compact"] is True
    assert payload["group_details"] == []
    assert payload["optimization"]["low_groups"][0]["test_ids"] == [
        "tests/prague/foo/test_bar.py::test_case[fork_Prague-a]"
    ]
    assert "[bold" not in result.output


def test_analyze_pre_alloc_folder_excludes_test_id_substrings(
    tmp_path: Path,
) -> None:
    """Substring filters should remove tests before stats are computed."""
    _write_group(
        tmp_path,
        "0xaaa",
        test_ids=[
            "tests/prague/foo/test_bar.py::test_keep[fork_Prague]",
            "tests/prague/foo/test_bar.py::test_drop[fork_Prague]",
        ],
    )

    stats = analyze_pre_alloc_folder(
        tmp_path,
        low_test_count=1,
        exclude_test_id_substrings=("test_drop",),
    )

    assert stats["total_tests"] == 1
    assert stats["low_group_count"] == 1
    assert stats["filters"]["excluded_tests"] == 1
    assert stats["filters"]["groups_with_exclusions"] == 1
    assert stats["filters"]["dropped_groups"] == 0


def test_analyze_pre_alloc_folder_matches_test_id_substrings(
    tmp_path: Path,
) -> None:
    """Substring match filters should keep only matching tests."""
    _write_group(
        tmp_path,
        "0xaaa",
        test_ids=[
            "tests/ported_static/foo/test_bar.py::test_keep[fork_Prague]",
            "tests/prague/foo/test_bar.py::test_drop[fork_Prague]",
        ],
    )

    stats = analyze_pre_alloc_folder(
        tmp_path,
        low_test_count=1,
        match_test_id_substrings=("ported_static",),
    )

    assert stats["total_tests"] == 1
    assert stats["low_group_count"] == 1
    assert stats["filters"]["matched_tests"] == 1
    assert stats["filters"]["unmatched_tests"] == 1
    assert stats["filters"]["dropped_groups"] == 0
    assert stats["optimization"]["low_groups"][0]["modules"] == [
        "tests/ported_static/foo/test_bar.py"
    ]


def test_groupstats_rich_output_reports_regex_exclusions(
    tmp_path: Path,
) -> None:
    """Regex match and exclude filters should apply to rich mode output."""
    _write_group(
        tmp_path,
        "0xaaa",
        test_ids=[
            "tests/ported_static/foo/test_bar.py::test_drop[fork_Prague]"
        ],
    )
    _write_group(
        tmp_path,
        "0xbbb",
        test_ids=[
            "tests/ported_static/foo/test_bar.py::test_keep[fork_Prague]"
        ],
    )
    _write_group(
        tmp_path,
        "0xccc",
        test_ids=["tests/prague/foo/test_bar.py::test_other[fork_Prague]"],
    )

    result = CliRunner().invoke(
        main,
        [
            str(tmp_path),
            "--low-test-count",
            "1",
            "--match-test-id",
            "ported_static",
            "--exclude-test-id-regex",
            "test_drop",
        ],
    )

    assert result.exit_code == 0, result.output
    assert "Total groups: 1" in result.output
    assert "Total tests: 1" in result.output
    assert "Matched tests: 1" in result.output
    assert "Excluded tests: 1" in result.output
