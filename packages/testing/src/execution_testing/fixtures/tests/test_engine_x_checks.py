"""Tests for the Engine X execution-consistency check."""

import json
from pathlib import Path
from typing import Any, Dict, List

import pytest

from execution_testing.base_types import Account, Address, Bytes, Hash
from execution_testing.fixtures.blockchain import (
    BlockchainEngineFixture,
    BlockchainEngineXFixture,
    FixtureConfig,
    FixtureEngineNewPayload,
    FixtureExecutionPayload,
    FixtureHeader,
)
from execution_testing.fixtures.engine_x_checks import (
    ENGINE_X_FIXTURES_DIR,
    SIBLING_FIXTURES_DIR,
    STATE_ROOT_DERIVED_FIELDS,
    EngineXCheckError,
    EngineXExecutionDriftError,
    verify_engine_x_execution,
)
from execution_testing.fixtures.pre_alloc_groups import PreAllocGroupBuilder
from execution_testing.forks import Prague
from execution_testing.forks.forks.eips.prague.eip_2935 import (
    HISTORY_STORAGE_ADDRESS,
)
from execution_testing.test_types import Alloc, AllocGroupHash, Environment
from execution_testing.test_types.block_access_list import (
    BalAccountChange,
    BalNonceChange,
    BalStorageChange,
    BalStorageSlot,
    BlockAccessList,
)

ENGINE_X_ID = (
    "tests/a.py::test_a[fork_Prague-blockchain_test_engine_x_from_state_test]"
)
SIBLING_ID = (
    "tests/a.py::test_a[fork_Prague-blockchain_test_engine_from_state_test]"
)
ENGINE_X_ID_B = ENGINE_X_ID.replace("test_a[", "test_b[")
SIBLING_ID_B = SIBLING_ID.replace("test_a[", "test_b[")

PRE_HASH = "0xf00df00df00df00d"

# One parent hash with no leading zero bytes and one with 31 of them:
# masking must be insensitive to the RLP canonical trimming of either.
SIBLING_PARENT_HASH = Hash(bytes.fromhex("aa" * 32))
ENGINE_X_PARENT_HASH = Hash(0xBB)

SENDER = Address(0xA)
UNDECLARED_ACCOUNT = Address(0x1000)
TEST_CONTRACT = Address(0xC0DE)


def _genesis_header() -> FixtureHeader:
    """Build a minimal valid Prague genesis header."""
    return FixtureHeader(
        fork=Prague,
        fee_recipient=Address(0),
        state_root=Hash(0),
        number=0,
        gas_limit=30_000_000,
        gas_used=0,
        timestamp=0,
        extra_data=b"\x00",
        base_fee_per_gas=7,
        withdrawals_root=Hash(0),
        blob_gas_used=0,
        excess_blob_gas=0,
        parent_beacon_block_root=Hash(0),
        requests_hash=Hash(0),
    )


def _payload(
    *,
    parent_hash: Hash,
    state_root: Hash,
    block_hash: Hash,
    gas_used: int,
    block_access_list: Bytes | None,
) -> FixtureEngineNewPayload:
    """Build a payload whose execution outputs are deterministic."""
    execution_payload = FixtureExecutionPayload(
        parent_hash=parent_hash,
        fee_recipient=Address(0),
        state_root=state_root,
        receipts_root=Hash(0x11),
        logs_bloom=b"\x00" * 256,
        number=1,
        gas_limit=30_000_000,
        gas_used=gas_used,
        timestamp=12,
        extra_data=b"",
        prev_randao=Hash(0),
        base_fee_per_gas=7,
        block_hash=block_hash,
        transactions=[Bytes(b"\x01")],
        block_access_list=block_access_list,
    )
    return FixtureEngineNewPayload(
        params=(execution_payload,),
        new_payload_version=1,
        forkchoice_updated_version=1,
    )


def _sibling_payload(
    *,
    gas_used: int = 21_000,
    block_access_list: Bytes | None = None,
) -> FixtureEngineNewPayload:
    """Build a payload as filled against the test's own genesis."""
    return _payload(
        parent_hash=SIBLING_PARENT_HASH,
        state_root=Hash(1),
        block_hash=Hash(2),
        gas_used=gas_used,
        block_access_list=block_access_list,
    )


def _engine_x_payload(
    *,
    gas_used: int = 21_000,
    block_access_list: Bytes | None = None,
) -> FixtureEngineNewPayload:
    """Build the same payload as filled against the packed genesis."""
    return _payload(
        parent_hash=ENGINE_X_PARENT_HASH,
        state_root=Hash(3),
        block_hash=Hash(4),
        gas_used=gas_used,
        block_access_list=block_access_list,
    )


def _write_fixture_file(file: Path, fixtures: Dict[str, Any]) -> None:
    """Write (or extend) a fixture file with serialized fixtures."""
    file.parent.mkdir(parents=True, exist_ok=True)
    existing: Dict[str, Any] = {}
    if file.exists():
        existing = json.loads(file.read_text())
    existing.update(
        {
            test_id: fixture.json_dict_with_info()
            for test_id, fixture in fixtures.items()
        }
    )
    file.write_text(json.dumps(existing))


def _write_sibling(
    folder: Path,
    payloads: List[FixtureEngineNewPayload],
    *,
    test_id: str = SIBLING_ID,
    file_name: str = "test_a.json",
    pre: Alloc | None = None,
) -> None:
    """Write a sibling engine fixture into its format tree."""
    fixture = BlockchainEngineFixture(
        fork=Prague,
        last_block_hash=Hash(0),
        config=FixtureConfig(fork=Prague),
        pre=pre if pre is not None else Alloc({SENDER: Account(balance=1)}),
        post_state=Alloc({SENDER: Account(balance=1)}),
        genesis=_genesis_header(),
        payloads=payloads,
    )
    _write_fixture_file(
        folder / SIBLING_FIXTURES_DIR / "prague" / "module" / file_name,
        {test_id: fixture},
    )


def _write_engine_x(
    folder: Path,
    payloads: List[FixtureEngineNewPayload],
    *,
    test_id: str = ENGINE_X_ID,
    file_name: str = "test_a.json",
    pre_hash: str = PRE_HASH,
) -> None:
    """Write an Engine X fixture into its format tree."""
    fixture = BlockchainEngineXFixture(
        fork=Prague,
        last_block_hash=Hash(0),
        config=FixtureConfig(fork=Prague),
        pre_hash=pre_hash,
        post_state_diff=Alloc({}),
        payloads=payloads,
    )
    _write_fixture_file(
        folder / ENGINE_X_FIXTURES_DIR / "prague" / "module" / file_name,
        {test_id: fixture},
    )


def _write_group(
    folder: Path,
    accounts: Dict[Address, Account | None],
    test_ids: List[str],
    *,
    pre_hash: str = PRE_HASH,
) -> None:
    """Write a packed pre-alloc group file, as phase 1 would."""
    group_folder = folder / ENGINE_X_FIXTURES_DIR / "pre_alloc"
    group_folder.mkdir(parents=True, exist_ok=True)
    builder = PreAllocGroupBuilder(
        test_ids=test_ids,
        environment=Environment(
            base_fee_per_gas=7,
            excess_blob_gas=0,
            blob_gas_used=0,
            withdrawals=[],
            parent_beacon_block_root=Hash(0),
        ),
        fork=Prague,
        pre=Alloc(accounts),
        group_hash=AllocGroupHash(pre_hash),
    )
    (group_folder / f"{pre_hash}.json").write_text(
        builder.build().model_dump_json(by_alias=True, exclude_none=True)
    )


def _bal(*accounts: BalAccountChange) -> Bytes:
    """RLP-encode a BAL from account changes."""
    return BlockAccessList(list(accounts)).rlp


def _history_write(parent_hash: Hash) -> BalAccountChange:
    """Build the EIP-2935 system write of the block's parent hash."""
    return _storage_write(
        Address(HISTORY_STORAGE_ADDRESS),
        slot=0,
        value=int.from_bytes(parent_hash, "big"),
    )


def _storage_write(
    address: Address, *, slot: int, value: int
) -> BalAccountChange:
    """Build a single storage write of an account in a BAL."""
    return BalAccountChange(
        address=address,
        storage_changes=[
            BalStorageSlot(
                slot=slot,
                slot_changes=[
                    BalStorageChange(block_access_index=0, post_value=value)
                ],
            )
        ],
    )


def _nonce_touch(address: Address) -> BalAccountChange:
    """Build a minimal appearance of an account in a BAL."""
    return BalAccountChange(
        address=address,
        nonce_changes=[BalNonceChange(block_access_index=0, post_nonce=1)],
    )


def test_identical_execution_passes(tmp_path: Path) -> None:
    """State-root-derived differences alone do not trip the check."""
    _write_sibling(tmp_path, [_sibling_payload()])
    _write_engine_x(tmp_path, [_engine_x_payload()])

    result = verify_engine_x_execution(tmp_path)

    assert result.compared == 1
    assert result.skipped == 0
    assert result.skip_reason is None
    assert "1 Engine X fixtures execute identically" in result.summary


def test_bal_embedded_parent_hash_passes(tmp_path: Path) -> None:
    """
    The EIP-2935 write embeds each side's own parent hash in its BAL; a
    BAL differing only by that history-contract write does not trip the
    check, whatever the leading-zero shape of either hash.
    """
    _write_sibling(
        tmp_path,
        [
            _sibling_payload(
                block_access_list=_bal(_history_write(SIBLING_PARENT_HASH)),
            )
        ],
    )
    _write_engine_x(
        tmp_path,
        [
            _engine_x_payload(
                block_access_list=_bal(_history_write(ENGINE_X_PARENT_HASH)),
            )
        ],
    )

    result = verify_engine_x_execution(tmp_path)

    assert result.compared == 1


def test_bal_leaked_account_raises(tmp_path: Path) -> None:
    """An account appearing only in the packed BAL fails loudly."""
    _write_sibling(
        tmp_path,
        [
            _sibling_payload(
                block_access_list=_bal(_history_write(SIBLING_PARENT_HASH)),
            )
        ],
    )
    _write_engine_x(
        tmp_path,
        [
            _engine_x_payload(
                block_access_list=_bal(
                    _nonce_touch(UNDECLARED_ACCOUNT),
                    _history_write(ENGINE_X_PARENT_HASH),
                ),
            )
        ],
    )

    with pytest.raises(EngineXExecutionDriftError) as exc_info:
        verify_engine_x_execution(tmp_path)

    message = str(exc_info.value).lower()
    assert str(UNDECLARED_ACCOUNT).lower() in message
    assert "packed fixture's bal only" in message


def test_bal_leak_is_attributed_to_the_group(tmp_path: Path) -> None:
    """A leaked account is traced to its packed pre-alloc group."""
    _write_sibling(
        tmp_path,
        [
            _sibling_payload(
                block_access_list=_bal(_history_write(SIBLING_PARENT_HASH)),
            )
        ],
    )
    _write_engine_x(
        tmp_path,
        [
            _engine_x_payload(
                block_access_list=_bal(
                    _nonce_touch(UNDECLARED_ACCOUNT),
                    _history_write(ENGINE_X_PARENT_HASH),
                ),
            )
        ],
    )
    _write_group(
        tmp_path,
        accounts={
            SENDER: Account(balance=1),
            UNDECLARED_ACCOUNT: Account(balance=1),
        },
        test_ids=["tests/b.py::test_leaker[fork_Prague-foo]"],
    )

    with pytest.raises(EngineXExecutionDriftError) as exc_info:
        verify_engine_x_execution(tmp_path)

    message = str(exc_info.value)
    assert PRE_HASH in message
    assert "test_leaker" in message
    assert 'pre_alloc_group("separate")' in message


def test_parent_hash_write_outside_history_contract_raises(
    tmp_path: Path,
) -> None:
    """
    A test storing its block's parent hash in its own contract is drift:
    only the EIP-2935 history-contract write is masked.
    """
    _write_sibling(
        tmp_path,
        [
            _sibling_payload(
                block_access_list=_bal(
                    _storage_write(
                        TEST_CONTRACT,
                        slot=1,
                        value=int.from_bytes(SIBLING_PARENT_HASH, "big"),
                    ),
                ),
            )
        ],
    )
    _write_engine_x(
        tmp_path,
        [
            _engine_x_payload(
                block_access_list=_bal(
                    _storage_write(
                        TEST_CONTRACT,
                        slot=1,
                        value=int.from_bytes(ENGINE_X_PARENT_HASH, "big"),
                    ),
                ),
            )
        ],
    )

    with pytest.raises(EngineXExecutionDriftError) as exc_info:
        verify_engine_x_execution(tmp_path)

    message = str(exc_info.value)
    assert "writes its block's parent hash" in message
    assert "BLOCKHASH" in message


def test_malformed_bal_compared_verbatim(tmp_path: Path) -> None:
    """An undecodable BAL (negative test) is compared verbatim."""
    garbage = Bytes(b"\xde\xad\xbe\xef")
    _write_sibling(tmp_path, [_sibling_payload(block_access_list=garbage)])
    _write_engine_x(tmp_path, [_engine_x_payload(block_access_list=garbage)])

    result = verify_engine_x_execution(tmp_path)

    assert result.compared == 1


def test_malformed_bal_drift_raises(tmp_path: Path) -> None:
    """Differing undecodable BALs fail loudly."""
    _write_sibling(
        tmp_path,
        [_sibling_payload(block_access_list=Bytes(b"\xde\xad\xbe\xef"))],
    )
    _write_engine_x(
        tmp_path,
        [_engine_x_payload(block_access_list=Bytes(b"\xde\xad\xbe\xee"))],
    )

    with pytest.raises(EngineXExecutionDriftError) as exc_info:
        verify_engine_x_execution(tmp_path)

    assert "undecodable" in str(exc_info.value)


def test_execution_drift_raises(tmp_path: Path) -> None:
    """A gas difference fails loudly and shows both values."""
    _write_sibling(tmp_path, [_sibling_payload()])
    _write_engine_x(tmp_path, [_engine_x_payload(gas_used=0xBEEF)])

    with pytest.raises(EngineXExecutionDriftError) as exc_info:
        verify_engine_x_execution(tmp_path)

    message = str(exc_info.value)
    assert ENGINE_X_ID in message
    assert "gasUsed" in message
    assert "0x5208" in message
    assert "0xbeef" in message


def test_payload_count_drift_raises(tmp_path: Path) -> None:
    """A different number of payloads fails loudly."""
    _write_sibling(tmp_path, [_sibling_payload()])
    _write_engine_x(tmp_path, [_engine_x_payload(), _engine_x_payload()])

    with pytest.raises(EngineXExecutionDriftError) as exc_info:
        verify_engine_x_execution(tmp_path)

    assert "payload count differs" in str(exc_info.value)


def test_same_cause_drifts_aggregate(tmp_path: Path) -> None:
    """Drifts with the same cause collapse into one diagnosis."""
    _write_sibling(tmp_path, [_sibling_payload()])
    _write_sibling(
        tmp_path,
        [_sibling_payload()],
        test_id=SIBLING_ID_B,
        file_name="test_b.json",
    )
    _write_engine_x(tmp_path, [_engine_x_payload(gas_used=0xBEEF)])
    _write_engine_x(
        tmp_path,
        [_engine_x_payload(gas_used=0xBEEF)],
        test_id=ENGINE_X_ID_B,
        file_name="test_b.json",
    )

    with pytest.raises(EngineXExecutionDriftError) as exc_info:
        verify_engine_x_execution(tmp_path)

    message = str(exc_info.value)
    assert "2 of 2" in message
    assert "1 distinct cause" in message
    assert "[2x]" in message
    assert ENGINE_X_ID in message
    assert ENGINE_X_ID_B in message


def test_no_sibling_tree_sets_skip_reason(tmp_path: Path) -> None:
    """An Engine X only fill (no sibling format tree) skips the check."""
    _write_engine_x(tmp_path, [_engine_x_payload()])

    result = verify_engine_x_execution(tmp_path)

    assert result.compared == 0
    assert result.skip_reason is not None
    assert f"generated no {SIBLING_FIXTURES_DIR}" in result.skip_reason


def test_no_engine_x_fixtures_is_silent(tmp_path: Path) -> None:
    """A fill without Engine X fixtures has nothing to check or warn."""
    _write_sibling(tmp_path, [_sibling_payload()])

    result = verify_engine_x_execution(tmp_path)

    assert result.compared == 0
    assert result.skipped == 0
    assert result.skip_reason is None


def test_single_fixture_per_file_sibling_lookup(tmp_path: Path) -> None:
    """
    A `--single-fixture-per-file` fill embeds the fixture format name in
    every file name; the sibling is still found under its own basename.
    """
    _write_sibling(
        tmp_path,
        [_sibling_payload()],
        file_name=(
            "a__fork_Prague_blockchain_test_engine_from_state_test.json"
        ),
    )
    _write_engine_x(
        tmp_path,
        [_engine_x_payload()],
        file_name=(
            "a__fork_Prague_blockchain_test_engine_x_from_state_test.json"
        ),
    )

    result = verify_engine_x_execution(tmp_path)

    assert result.compared == 1
    assert result.skipped == 0


def test_missing_sibling_fixture_is_skipped(tmp_path: Path) -> None:
    """A test filtered from the sibling format is skipped, not failed."""
    _write_sibling(tmp_path, [_sibling_payload()])
    _write_engine_x(tmp_path, [_engine_x_payload()])
    _write_engine_x(
        tmp_path,
        [_engine_x_payload()],
        test_id=ENGINE_X_ID_B,
        file_name="test_b.json",
    )

    result = verify_engine_x_execution(tmp_path)

    assert result.compared == 1
    assert result.skipped == 1
    assert "1 skipped" in result.summary


def test_no_matching_siblings_sets_skip_reason(tmp_path: Path) -> None:
    """
    Sibling fixtures exist but none match: the check reports the skip
    count instead of pretending no siblings were generated.
    """
    _write_sibling(
        tmp_path,
        [_sibling_payload()],
        test_id=SIBLING_ID_B,
        file_name="test_b.json",
    )
    _write_engine_x(tmp_path, [_engine_x_payload()])

    result = verify_engine_x_execution(tmp_path)

    assert result.compared == 0
    assert result.skipped == 1
    assert result.skip_reason is not None
    assert "none of the 1" in result.skip_reason


def test_unparseable_fixture_raises(tmp_path: Path) -> None:
    """A fixture that fails typed validation is a loud error."""
    _write_sibling(tmp_path, [_sibling_payload()])
    file = (
        tmp_path / ENGINE_X_FIXTURES_DIR / "prague" / "module" / "test_a.json"
    )
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text(json.dumps({ENGINE_X_ID: {"engineNewPayloads": []}}))

    with pytest.raises(EngineXCheckError, match="cannot parse"):
        verify_engine_x_execution(tmp_path)


def test_non_fixture_files_are_ignored(tmp_path: Path) -> None:
    """`pre_alloc` group files and `.meta` files are not fixtures."""
    _write_sibling(tmp_path, [_sibling_payload()])
    _write_engine_x(tmp_path, [_engine_x_payload()])
    _write_group(
        tmp_path,
        accounts={SENDER: Account(balance=1)},
        test_ids=[ENGINE_X_ID],
    )
    meta = tmp_path / ENGINE_X_FIXTURES_DIR / ".meta"
    meta.mkdir(parents=True)
    (meta / "index.json").write_text('{"not": "a fixture"}')

    result = verify_engine_x_execution(tmp_path)

    assert result.compared == 1
    assert result.skipped == 0


def test_state_root_derived_fields_exist_on_the_payload_model() -> None:
    """The exclusion set must track `FixtureExecutionPayload` renames."""
    model_fields = set(FixtureExecutionPayload.model_fields)
    assert STATE_ROOT_DERIVED_FIELDS <= model_fields
    assert "block_access_list" in model_fields


def test_bal_dump_keys_match_the_masking_walk() -> None:
    """The BAL mask walks these keys; they must track the BAL models."""
    account = _history_write(SIBLING_PARENT_HASH).model_dump(mode="json")
    assert {"address", "storage_changes"} <= set(account)
    slot = account["storage_changes"][0]
    assert {"slot", "slot_changes"} <= set(slot)
    assert {"block_access_index", "post_value"} <= set(slot["slot_changes"][0])
