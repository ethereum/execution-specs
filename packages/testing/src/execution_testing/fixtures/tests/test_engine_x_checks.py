"""Tests for the Engine X execution-consistency check."""

import json
from pathlib import Path
from typing import Any, Dict, List

import pytest
from ethereum_rlp import rlp

from execution_testing.fixtures.engine_x_checks import (
    ENGINE_X_FIXTURES_DIR,
    SIBLING_FIXTURES_DIR,
    EngineXExecutionDriftError,
    verify_engine_x_execution,
)

ENGINE_X_ID = (
    "tests/a.py::test_a[fork_Prague-blockchain_test_engine_x_from_state_test]"
)
SIBLING_ID = (
    "tests/a.py::test_a[fork_Prague-blockchain_test_engine_from_state_test]"
)


def _payload(
    *,
    gas_used: str,
    state_root: str,
    block_hash: str,
    parent_hash: str = f"0x{'00' * 31}aa",
    block_access_list: str | None = None,
) -> Dict[str, Any]:
    """Build a single newPayload entry."""
    payload = {
        "parentHash": parent_hash,
        "stateRoot": state_root,
        "blockHash": block_hash,
        "gasUsed": gas_used,
        "receiptsRoot": f"0x{'11' * 32}",
        "logsBloom": f"0x{'00' * 256}",
        "transactions": ["0xf86b..."],
    }
    if block_access_list is not None:
        payload["blockAccessList"] = block_access_list
    return {
        "newPayloadVersion": "4",
        "forkchoiceUpdatedVersion": "3",
        "params": [
            payload,
            [],
            f"0x{'00' * 32}",
        ],
    }


def _write_fixture(
    folder: Path,
    fixture_dir: str,
    test_id: str,
    payloads: List[Dict[str, Any]],
) -> None:
    """Write a single-fixture file into a format tree."""
    file = folder / fixture_dir / "prague" / "module" / "test_a.json"
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text(json.dumps({test_id: {"engineNewPayloads": payloads}}))


def test_identical_execution_passes(tmp_path: Path) -> None:
    """State-root-derived differences alone do not trip the check."""
    _write_fixture(
        tmp_path,
        SIBLING_FIXTURES_DIR,
        SIBLING_ID,
        [_payload(gas_used="0x5208", state_root="0x01", block_hash="0x02")],
    )
    _write_fixture(
        tmp_path,
        ENGINE_X_FIXTURES_DIR,
        ENGINE_X_ID,
        [_payload(gas_used="0x5208", state_root="0xaa", block_hash="0xbb")],
    )

    result = verify_engine_x_execution(tmp_path)

    assert result is not None
    assert result.compared == 1
    assert "1 Engine X fixtures execute identically" in result.summary


def _bal(parent_hash: bytes, *extra: bytes) -> str:
    """
    Encode a minimal BAL-shaped RLP structure embedding a parent hash.

    Storage values are RLP-encoded with leading zeros trimmed, matching
    the EIP-2935 history write of the parent hash in a real BAL.
    """
    values = [parent_hash.lstrip(b"\x00"), *extra]
    return "0x" + rlp.encode([values, []]).hex()


def test_bal_embedded_parent_hash_passes(tmp_path: Path) -> None:
    """
    The EIP-2935 write embeds each side's own parent hash in its BAL; a BAL
    differing only by that embedded value does not trip the check, even
    when one side's hash is stored with its leading zero byte trimmed.
    """
    sibling_parent = bytes.fromhex("aa" * 32)
    engine_x_parent = bytes.fromhex("00" + "bb" * 31)
    _write_fixture(
        tmp_path,
        SIBLING_FIXTURES_DIR,
        SIBLING_ID,
        [
            _payload(
                gas_used="0x5208",
                state_root="0x01",
                block_hash="0x02",
                parent_hash="0x" + sibling_parent.hex(),
                block_access_list=_bal(sibling_parent),
            )
        ],
    )
    _write_fixture(
        tmp_path,
        ENGINE_X_FIXTURES_DIR,
        ENGINE_X_ID,
        [
            _payload(
                gas_used="0x5208",
                state_root="0xaa",
                block_hash="0xbb",
                parent_hash="0x" + engine_x_parent.hex(),
                block_access_list=_bal(engine_x_parent),
            )
        ],
    )

    result = verify_engine_x_execution(tmp_path)

    assert result is not None
    assert result.compared == 1


def test_bal_drift_raises(tmp_path: Path) -> None:
    """A BAL difference beyond the embedded parent hash fails loudly."""
    sibling_parent = bytes.fromhex("aa" * 32)
    engine_x_parent = bytes.fromhex("bb" * 32)
    _write_fixture(
        tmp_path,
        SIBLING_FIXTURES_DIR,
        SIBLING_ID,
        [
            _payload(
                gas_used="0x5208",
                state_root="0x01",
                block_hash="0x02",
                parent_hash="0x" + sibling_parent.hex(),
                block_access_list=_bal(sibling_parent),
            )
        ],
    )
    _write_fixture(
        tmp_path,
        ENGINE_X_FIXTURES_DIR,
        ENGINE_X_ID,
        [
            _payload(
                gas_used="0x5208",
                state_root="0xaa",
                block_hash="0xbb",
                parent_hash="0x" + engine_x_parent.hex(),
                block_access_list=_bal(engine_x_parent, b"\x01"),
            )
        ],
    )

    with pytest.raises(EngineXExecutionDriftError) as exc_info:
        verify_engine_x_execution(tmp_path)

    assert "blockAccessList" in str(exc_info.value)


def test_malformed_bal_compared_verbatim(tmp_path: Path) -> None:
    """An undecodable BAL (negative test) is compared verbatim."""
    _write_fixture(
        tmp_path,
        SIBLING_FIXTURES_DIR,
        SIBLING_ID,
        [
            _payload(
                gas_used="0x5208",
                state_root="0x01",
                block_hash="0x02",
                block_access_list="0xdeadbeef",
            )
        ],
    )
    _write_fixture(
        tmp_path,
        ENGINE_X_FIXTURES_DIR,
        ENGINE_X_ID,
        [
            _payload(
                gas_used="0x5208",
                state_root="0xaa",
                block_hash="0xbb",
                block_access_list="0xdeadbeef",
            )
        ],
    )

    result = verify_engine_x_execution(tmp_path)

    assert result is not None
    assert result.compared == 1


def test_execution_drift_raises(tmp_path: Path) -> None:
    """A gas difference (a leaked account changed execution) fails loudly."""
    _write_fixture(
        tmp_path,
        SIBLING_FIXTURES_DIR,
        SIBLING_ID,
        [_payload(gas_used="0x5208", state_root="0x01", block_hash="0x02")],
    )
    _write_fixture(
        tmp_path,
        ENGINE_X_FIXTURES_DIR,
        ENGINE_X_ID,
        [_payload(gas_used="0xbeef", state_root="0xaa", block_hash="0xbb")],
    )

    with pytest.raises(EngineXExecutionDriftError) as exc_info:
        verify_engine_x_execution(tmp_path)

    message = str(exc_info.value)
    assert ENGINE_X_ID in message
    assert "gasUsed" in message


def test_payload_count_drift_raises(tmp_path: Path) -> None:
    """A different number of payloads fails loudly."""
    payload = _payload(gas_used="0x5208", state_root="0x01", block_hash="0x02")
    _write_fixture(tmp_path, SIBLING_FIXTURES_DIR, SIBLING_ID, [payload])
    _write_fixture(
        tmp_path, ENGINE_X_FIXTURES_DIR, ENGINE_X_ID, [payload, payload]
    )

    with pytest.raises(EngineXExecutionDriftError) as exc_info:
        verify_engine_x_execution(tmp_path)

    assert "payload count" in str(exc_info.value)


def test_no_sibling_fixtures_skips_check(tmp_path: Path) -> None:
    """An Engine X only fill (no sibling format tree) skips the check."""
    _write_fixture(
        tmp_path,
        ENGINE_X_FIXTURES_DIR,
        ENGINE_X_ID,
        [_payload(gas_used="0x5208", state_root="0x01", block_hash="0x02")],
    )

    assert verify_engine_x_execution(tmp_path) is None


def test_no_engine_x_fixtures_skips_check(tmp_path: Path) -> None:
    """A fill without Engine X fixtures skips the check."""
    _write_fixture(
        tmp_path,
        SIBLING_FIXTURES_DIR,
        SIBLING_ID,
        [_payload(gas_used="0x5208", state_root="0x01", block_hash="0x02")],
    )

    assert verify_engine_x_execution(tmp_path) is None


def test_single_fixture_per_file_sibling_lookup(tmp_path: Path) -> None:
    """
    A `--single-fixture-per-file` fill embeds the fixture format name in
    every file name; the sibling is still found under its own basename.
    """
    payload = _payload(gas_used="0x5208", state_root="0x01", block_hash="0x02")
    sibling_file = (
        tmp_path
        / SIBLING_FIXTURES_DIR
        / "prague"
        / "module"
        / "a__fork_Prague_blockchain_test_engine_from_state_test.json"
    )
    sibling_file.parent.mkdir(parents=True, exist_ok=True)
    sibling_file.write_text(
        json.dumps({SIBLING_ID: {"engineNewPayloads": [payload]}})
    )
    engine_x_file = (
        tmp_path
        / ENGINE_X_FIXTURES_DIR
        / "prague"
        / "module"
        / "a__fork_Prague_blockchain_test_engine_x_from_state_test.json"
    )
    engine_x_file.parent.mkdir(parents=True, exist_ok=True)
    engine_x_file.write_text(
        json.dumps({ENGINE_X_ID: {"engineNewPayloads": [payload]}})
    )

    result = verify_engine_x_execution(tmp_path)

    assert result is not None
    assert result.compared == 1
    assert result.skipped == 0


def test_missing_sibling_fixture_is_skipped(tmp_path: Path) -> None:
    """A test filtered from the sibling format is skipped, not failed."""
    payload = _payload(gas_used="0x5208", state_root="0x01", block_hash="0x02")
    _write_fixture(tmp_path, SIBLING_FIXTURES_DIR, SIBLING_ID, [payload])
    other_engine_x_id = ENGINE_X_ID.replace("test_a[", "test_b[")
    _write_fixture(tmp_path, ENGINE_X_FIXTURES_DIR, ENGINE_X_ID, [payload])
    file = (
        tmp_path / ENGINE_X_FIXTURES_DIR / "prague" / "module" / "test_b.json"
    )
    file.write_text(
        json.dumps({other_engine_x_id: {"engineNewPayloads": [payload]}})
    )

    result = verify_engine_x_execution(tmp_path)

    assert result is not None
    assert result.compared == 1
    assert result.skipped == 1
    assert "1 skipped" in result.summary


def test_no_matching_siblings_reports_skip_count(tmp_path: Path) -> None:
    """
    Sibling fixtures exist but none match: The check reports the skip
    count instead of pretending no siblings were generated.
    """
    payload = _payload(gas_used="0x5208", state_root="0x01", block_hash="0x02")
    other_sibling_id = SIBLING_ID.replace("test_a[", "test_b[")
    _write_fixture(tmp_path, SIBLING_FIXTURES_DIR, other_sibling_id, [payload])
    _write_fixture(tmp_path, ENGINE_X_FIXTURES_DIR, ENGINE_X_ID, [payload])

    result = verify_engine_x_execution(tmp_path)

    assert result is not None
    assert result.compared == 0
    assert result.skipped == 1
