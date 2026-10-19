"""
Test the fill-time checks on block access list modifiers that can only run
once the transition tool has produced the list.

`override_rlp` commits the header to re-encoded bytes that only the engine
payload can carry. `fill` therefore refuses the RLP blockchain fixture
format for such a block, and refuses an explicit payload override that would
replace the committed bytes. The same block fills as an engine fixture.

A modifier that leaves both the list and its payload encoding unchanged is
refused as well, since it would label a valid block invalid.

The commitment tests pin what the block hash of a filled engine payload
commits to.
"""

import json
import textwrap
from pathlib import Path
from typing import Any

import pytest

from execution_testing.base_types import Bytes, EmptyTrieRoot
from execution_testing.fixtures.blockchain import FixtureHeader
from execution_testing.test_types.block_access_list import BlockAccessList

# BALs exist from Amsterdam; the fill needs a fork that emits one.
FORK = "Amsterdam"

TEST_MODULE_DIR = "tests/amsterdam/dummy_test_module"

ENGINE_ONLY_MARKER = "@pytest.mark.blockchain_test_engine_only"

MODULE_TEMPLATE = textwrap.dedent(
    """\
    import pytest

    from execution_testing import (
        Address,
        Alloc,
        Block,
        BlockAccessList,
        BlockAccessListExpectation,
        BlockchainTestFiller,
        BlockException,
        Bytes,
        Transaction,
    )
    from execution_testing.test_types.block_access_list.modifiers import (
        encode_scalar_non_minimally,
        override_rlp,
    )

    EMPTY_LIST = Bytes(b"\\xc0")
    # EIP-2935: written by the pre-execution system call of every block, so
    # even an empty block's list has a storage value to re-encode.
    HISTORY_STORAGE_ADDRESS = Address(
        0x0000F90827F1C53A10CB7A02335B175320002935
    )
    RE_ENCODE = encode_scalar_non_minimally(
        HISTORY_STORAGE_ADDRESS, "storage_value"
    )

    {markers}
    @pytest.mark.valid_at("{fork}")
    @pytest.mark.exception_test
    def test_case(blockchain_test: BlockchainTestFiller, pre: Alloc) -> None:
        tx = Transaction(to=pre.fund_eoa(amount=0), sender=pre.fund_eoa())
        blockchain_test(
            pre=pre,
            post={{}},
            blocks=[
                Block(
                    txs={txs},
                    exception=BlockException.INVALID_BLOCK_ACCESS_LIST,
                    expected_block_access_list=(
                        BlockAccessListExpectation(){modifier}
                    ),
                    {block_kwargs}
                )
            ],
        )
    """
)

OVERRIDE_RLP_WITH_EMPTY_LIST = ".modify(override_rlp(lambda _: EMPTY_LIST))"


def write_test_module(
    pytester: pytest.Pytester,
    *,
    modifier: str,
    markers: str = ENGINE_ONLY_MARKER,
    block_kwargs: str = "",
    txs: str = "[tx]",
) -> str:
    """
    Write a single-test module with the given BAL modifier chain and return
    its path relative to the pytester directory.
    """
    module_dir = pytester.path / TEST_MODULE_DIR
    module_dir.mkdir(parents=True)
    module = module_dir / "test_dummy.py"
    module.write_text(
        MODULE_TEMPLATE.format(
            markers=markers,
            fork=FORK,
            modifier=modifier,
            block_kwargs=block_kwargs,
            txs=txs,
        )
    )
    pytester.copy_example(
        name="src/execution_testing/cli/pytest_commands/pytest_ini_files/pytest-fill.ini"
    )
    return str(module.relative_to(pytester.path))


def run_fill(
    pytester: pytest.Pytester, module_path: str, fixture_format: str
) -> pytest.RunResult:
    """Fill the given module, generating only ``fixture_format``."""
    return pytester.runpytest(
        "-c",
        "pytest-fill.ini",
        "--fork",
        FORK,
        "-m",
        fixture_format,
        "--no-html",
        "--output",
        "fixtures",
        module_path,
    )


def output_of(result: pytest.RunResult) -> str:
    """Return the combined output of a fill run."""
    return "\n".join(result.outlines + result.errlines)


def only_fixture(fixtures_dir: Path) -> dict[str, Any]:
    """Return the single fixture a fill of the dummy module produced."""
    files = [p for p in fixtures_dir.rglob("*.json") if ".meta" not in p.parts]
    assert len(files) == 1, files
    fixtures = json.loads(files[0].read_text())
    assert len(fixtures) == 1, list(fixtures)
    return next(iter(fixtures.values()))


def rebuilt_block_hash(fixture: dict[str, Any], bal_hash: Bytes) -> str:
    """
    Recompute the block hash of the fixture's only payload with the header's
    BAL hash replaced by ``bal_hash``.

    The block is empty, so its transaction and withdrawal roots are the empty
    trie root and its requests hash is the genesis one.
    """
    payload = fixture["engineNewPayloads"][0]
    execution_payload = payload["params"][0]
    genesis = FixtureHeader.model_validate(fixture["genesisBlockHeader"])
    header = genesis.copy(
        parent_hash=execution_payload["parentHash"],
        fee_recipient=execution_payload["feeRecipient"],
        state_root=execution_payload["stateRoot"],
        transactions_trie=EmptyTrieRoot,
        receipts_root=execution_payload["receiptsRoot"],
        logs_bloom=execution_payload["logsBloom"],
        number=execution_payload["blockNumber"],
        gas_limit=execution_payload["gasLimit"],
        gas_used=execution_payload["gasUsed"],
        timestamp=execution_payload["timestamp"],
        extra_data=execution_payload["extraData"],
        prev_randao=execution_payload["prevRandao"],
        base_fee_per_gas=execution_payload["baseFeePerGas"],
        withdrawals_root=EmptyTrieRoot,
        blob_gas_used=execution_payload["blobGasUsed"],
        excess_blob_gas=execution_payload["excessBlobGas"],
        parent_beacon_block_root=payload["params"][2],
        slot_number=execution_payload["slotNumber"],
        block_access_list_hash=bal_hash,
    )
    return str(header.block_hash)


def test_engine_format_fills_override_rlp(pytester: pytest.Pytester) -> None:
    """Positive control: the engine payload can carry the re-encoding."""
    module_path = write_test_module(
        pytester, modifier=OVERRIDE_RLP_WITH_EMPTY_LIST
    )

    result = run_fill(pytester, module_path, "blockchain_test_engine")

    result.assert_outcomes(passed=1, failed=0)


def test_rlp_format_refuses_override_rlp(pytester: pytest.Pytester) -> None:
    """Block RLP never carries the list, so the fixture cannot deliver it."""
    module_path = write_test_module(
        pytester, modifier=OVERRIDE_RLP_WITH_EMPTY_LIST, markers=""
    )

    result = run_fill(pytester, module_path, "blockchain_test")

    result.assert_outcomes(passed=0, failed=1)
    output = output_of(result)
    assert "cannot deliver the re-encoded bytes" in output, output
    assert "Mark the test `blockchain_test_engine_only`" in output, output


@pytest.mark.parametrize(
    "modifier,block_kwargs",
    [
        pytest.param(
            OVERRIDE_RLP_WITH_EMPTY_LIST,
            'engine_new_payload_block_access_list=Bytes(b"\\x80"),',
            id="explicit_payload_bal",
        ),
        pytest.param(
            OVERRIDE_RLP_WITH_EMPTY_LIST
            + ".modify_rlp(lambda _: Bytes(b'\\x80'))",
            "",
            id="modify_rlp",
        ),
    ],
)
def test_second_payload_writer_after_override_rlp_is_refused(
    pytester: pytest.Pytester, modifier: str, block_kwargs: str
) -> None:
    """A second writer of the payload bytes would break the commitment."""
    module_path = write_test_module(
        pytester, modifier=modifier, block_kwargs=block_kwargs
    )

    result = run_fill(pytester, module_path, "blockchain_test_engine")

    result.assert_outcomes(passed=0, failed=1)
    output = output_of(result)
    assert "would not carry what the header commits to" in output, output
    assert "Keep one" in output, output


@pytest.mark.parametrize(
    "modifier",
    [
        pytest.param(".modify(lambda bal: bal)", id="identity_contents"),
        pytest.param(
            ".modify_rlp(lambda bal: bal.rlp)", id="identity_encoding"
        ),
        pytest.param(
            ".modify(override_rlp(lambda bal: bal.rlp))",
            id="identity_override",
        ),
    ],
)
def test_unchanged_bal_is_refused(
    pytester: pytest.Pytester, modifier: str
) -> None:
    """An unchanged list or encoding is caught once the t8n has run."""
    module_path = write_test_module(pytester, modifier=modifier)

    result = run_fill(pytester, module_path, "blockchain_test_engine")

    result.assert_outcomes(passed=0, failed=1)
    output = output_of(result)
    assert "left the list unchanged" in output, output
    assert "drop it along with the exception" in output, output


@pytest.mark.parametrize(
    "modifier",
    [
        pytest.param(
            ".modify(lambda _: BlockAccessList([]))", id="contents_change"
        ),
        pytest.param(
            ".modify_rlp(lambda _: EMPTY_LIST)", id="encoding_change"
        ),
    ],
)
def test_changed_bal_fills(pytester: pytest.Pytester, modifier: str) -> None:
    """A modifier that changes the list or its encoding is accepted."""
    module_path = write_test_module(pytester, modifier=modifier)

    result = run_fill(pytester, module_path, "blockchain_test_engine")

    result.assert_outcomes(passed=1, failed=0)


@pytest.mark.parametrize(
    "modifier,header_commits_to,payload_encoding",
    [
        pytest.param(
            ".modify_rlp(RE_ENCODE)",
            "canonical_rlp",
            "re_encoded",
            id="modify_rlp",
        ),
        pytest.param(
            ".modify(override_rlp(RE_ENCODE))",
            "payload_rlp",
            "re_encoded",
            id="override_rlp",
        ),
        pytest.param(
            ".modify(lambda _: BlockAccessList([]))",
            "payload_rlp",
            "empty_list",
            id="contents",
        ),
    ],
)
def test_header_commitment(
    pytester: pytest.Pytester,
    modifier: str,
    header_commits_to: str,
    payload_encoding: str,
) -> None:
    """
    The payload RLP is checked against what the block hash commits to,
    rebuilt from the fixture itself.
    """
    module_path = write_test_module(pytester, modifier=modifier, txs="[]")

    result = run_fill(pytester, module_path, "blockchain_test_engine")

    result.assert_outcomes(passed=1, failed=0)
    fixture = only_fixture(pytester.path / "fixtures")
    execution_payload = fixture["engineNewPayloads"][0]["params"][0]
    payload_rlp = Bytes(execution_payload["blockAccessList"])
    canonical_rlp = BlockAccessList.from_rlp(payload_rlp).rlp
    if payload_encoding == "re_encoded":
        assert payload_rlp != canonical_rlp, (
            "re-encoding did not reach the payload"
        )
    elif payload_encoding == "empty_list":
        assert payload_rlp == Bytes(b"\xc0")
    else:
        raise ValueError(f"Unhandled payload encoding: {payload_encoding}")
    if header_commits_to == "canonical_rlp":
        committed, other = canonical_rlp, payload_rlp
    elif header_commits_to == "payload_rlp":
        committed, other = payload_rlp, canonical_rlp
    else:
        raise ValueError(f"Unhandled commitment: {header_commits_to}")

    block_hash = execution_payload["blockHash"]
    assert rebuilt_block_hash(fixture, committed.keccak256()) == block_hash
    if other != committed:
        assert rebuilt_block_hash(fixture, other.keccak256()) != block_hash
