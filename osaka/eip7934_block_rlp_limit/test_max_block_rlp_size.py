"""
abstract: Test [EIP-7934: RLP Execution Block Size Limit](https://eips.ethereum.org/EIPS/eip-7934)
    Tests for [EIP-7934: RLP Execution Block Size Limit](https://eips.ethereum.org/EIPS/eip-7934).
"""

from functools import lru_cache
from typing import List, Tuple

import pytest

from ethereum_test_base_types import ZeroPaddedHexNumber
from ethereum_test_fixtures.blockchain import (
    FixtureBlockBase,
    FixtureHeader,
)
from ethereum_test_forks import Fork
from ethereum_test_tools import (
    Alloc,
    Block,
    BlockchainTestFiller,
    BlockException,
    Bytes,
    Transaction,
)
from ethereum_test_types import EOA, Environment

from .spec import Spec, ref_spec_7934

REFERENCE_SPEC_GIT_PATH = ref_spec_7934.git_path
REFERENCE_SPEC_VERSION = ref_spec_7934.version

pytestmark = pytest.mark.valid_from("Osaka")


HEADER_TIMESTAMP = 123456789
EXTRA_DATA_AT_LIMIT = b"\x00\x00\x00"
BLOCK_GAS_LIMIT = 100_000_000


@pytest.fixture
def block_size_limit(fork: Fork) -> int:
    """Get the fork-specific block RLP size limit."""
    limit = fork.block_rlp_size_limit()
    if limit is None:
        raise ValueError("Fork does not implement block RLP size limit")
    assert limit == Spec.MAX_RLP_BLOCK_SIZE, (
        f"Expected block RLP size limit to be {Spec.MAX_RLP_BLOCK_SIZE}, "
        f"but got {limit} for fork {fork.name}"
    )
    return limit


@pytest.fixture
def block_errors() -> List[BlockException]:
    """Block exceptions expected for blocks that exceed the `MAX_RLP_BLOCK_SIZE`."""
    return [BlockException.RLP_BLOCK_LIMIT_EXCEEDED]


def create_test_header(gas_used: int) -> FixtureHeader:
    """Create a standard test header for RLP size calculations."""
    return FixtureHeader(  # type: ignore
        difficulty="0x0",
        number="0x1",
        gas_limit=hex(BLOCK_GAS_LIMIT),
        timestamp=hex(HEADER_TIMESTAMP),
        coinbase="0x" + "00" * 20,
        parent_hash="0x" + "00" * 32,
        uncle_hash="0x1dcc4de8dec75d7aab85b567b6ccd41ad312451b948a7413f0a142fd40d49347",
        state_root="0x56e81f171bcc55a6ff8345e692c0f86e5b48e01b996cadc001622fb5e363b421",
        transactions_trie="0x56e81f171bcc55a6ff8345e692c0f86e5b48e01b996cadc001622fb5e363b421",
        receiptTrie="0x56e81f171bcc55a6ff8345e692c0f86e5b48e01b996cadc001622fb5e363b421",
        bloom="0x" + "00" * 256,
        gas_used=hex(gas_used),
        extra_data=EXTRA_DATA_AT_LIMIT.hex(),
        mix_hash="0x" + "00" * 32,
        nonce="0x0000000000000042",
        base_fee_per_gas="0x0",
        withdrawals_root="0x" + "00" * 32,
        blob_gas_used="0x0",
        excess_blob_gas="0x0",
        parent_beacon_block_root="0x" + "00" * 32,
        requests_hash="0xe3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    )


def get_block_rlp_size(transactions: List[Transaction], gas_used: int) -> int:
    """Calculate the RLP size of a block with given transactions."""
    header = create_test_header(gas_used)
    total_gas = sum((tx.gas_limit or 21000) for tx in transactions)
    header.gas_used = ZeroPaddedHexNumber(total_gas)
    test_block = FixtureBlockBase(blockHeader=header, withdrawals=[])  # type: ignore
    return len(test_block.with_rlp(txs=transactions).rlp)


@pytest.fixture
def exact_size_transactions(
    sender: EOA, block_size_limit: int, fork: Fork
) -> Tuple[List[Transaction], int]:
    """
    Generate transactions that fill a block to exactly the RLP size limit.

    The calculation uses caching to avoid recalculating the same block rlp for each
    fork. Calculate the block and fill with real sender for testing.
    """
    stubbed_transactions, gas_used = _exact_size_transactions_calculation(block_size_limit, fork)
    test_transactions = [
        Transaction(
            sender=sender,
            nonce=tx.nonce,
            max_fee_per_gas=tx.max_fee_per_gas,
            max_priority_fee_per_gas=tx.max_priority_fee_per_gas,
            gas_limit=tx.gas_limit,
            data=tx.data,
        )
        for tx in stubbed_transactions
    ]
    return test_transactions, gas_used


@lru_cache(maxsize=128)
def _exact_size_transactions_calculation(
    block_size_limit: int, fork: Fork
) -> Tuple[List[Transaction], int]:
    """Generate transactions that fill a block to exactly the RLP size limit."""
    transactions = []
    sender = EOA("0x" + "00" * 20, key=123)  # stub account to fill the block
    nonce = 0
    total_gas_used = 0
    max_block_gas = 100_000_000

    calculator = fork.transaction_intrinsic_cost_calculator()

    data_large = b"\x00" * 500_000
    gas_limit_large = calculator(calldata=data_large)

    # block with 16 transactions + large calldata remains safely below the limit
    for _ in range(16):
        tx = Transaction(
            sender=sender,
            nonce=nonce,
            max_fee_per_gas=10**11,
            max_priority_fee_per_gas=10**11,
            gas_limit=gas_limit_large,
            data=data_large,
        )

        transactions.append(tx)
        total_gas_used += gas_limit_large
        nonce += 1

    current_size = get_block_rlp_size(transactions, gas_used=total_gas_used)
    remaining_bytes = block_size_limit - current_size
    remaining_gas = max_block_gas - total_gas_used

    if remaining_bytes > 0 and remaining_gas > 50_000:
        # create an empty transaction to measure base contribution
        empty_tx = Transaction(
            sender=sender,
            nonce=nonce,
            max_fee_per_gas=10**11,
            max_priority_fee_per_gas=10**11,
            gas_limit=calculator(calldata=b""),
            data=b"",
        )

        empty_block_size = get_block_rlp_size(
            transactions + [empty_tx], gas_used=total_gas_used + empty_tx.gas_limit
        )
        empty_contribution = empty_block_size - current_size

        calldata_bytes_needed = remaining_bytes - empty_contribution
        estimated_calldata = max(0, calldata_bytes_needed - 5)

        target_calldata = b"\x00" * estimated_calldata
        target_gas = calculator(calldata=target_calldata)

        if target_gas <= remaining_gas:
            test_tx = Transaction(
                sender=sender,
                nonce=nonce,
                max_fee_per_gas=10**11,
                max_priority_fee_per_gas=10**11,
                gas_limit=target_gas,
                data=target_calldata,
            )

            test_size = get_block_rlp_size(
                transactions + [test_tx], gas_used=total_gas_used + target_gas
            )

            if test_size == block_size_limit:
                # if exact match, use the transaction
                transactions.append(test_tx)
            else:
                # search for the best adjustment
                diff = block_size_limit - test_size
                best_diff = abs(diff)

                search_range = min(abs(diff) + 50, 1000)

                for adjustment in range(-search_range, search_range + 1):
                    adjusted_size = estimated_calldata + adjustment
                    if adjusted_size < 0:
                        continue

                    adjusted_calldata = b"\x00" * adjusted_size
                    adjusted_gas = calculator(calldata=adjusted_calldata)

                    if adjusted_gas <= remaining_gas:
                        adjusted_tx = Transaction(
                            sender=sender,
                            nonce=nonce,
                            max_fee_per_gas=10**11,
                            max_priority_fee_per_gas=10**11,
                            gas_limit=adjusted_gas,
                            data=adjusted_calldata,
                        )

                        adjusted_test_size = get_block_rlp_size(
                            transactions + [adjusted_tx],
                            gas_used=total_gas_used + adjusted_gas,
                        )

                        if adjusted_test_size == block_size_limit:
                            # exact match
                            transactions.append(adjusted_tx)
                            break

                        adjusted_diff = abs(block_size_limit - adjusted_test_size)
                        if adjusted_diff < best_diff:
                            best_diff = adjusted_diff
                else:
                    raise RuntimeError(
                        "Failed to find a transaction that matches the target size."
                    )
        else:
            transactions.append(empty_tx)

    final_size = get_block_rlp_size(
        transactions, gas_used=sum(tx.gas_limit for tx in transactions)
    )
    final_gas = sum(tx.gas_limit for tx in transactions)

    assert final_size == block_size_limit, (
        f"Size mismatch: got {final_size}, expected {block_size_limit}"
    )
    return transactions, final_gas


@pytest.mark.parametrize(
    "delta",
    [
        pytest.param(-1, id="max_rlp_size_minus_1_byte"),
        pytest.param(0, id="max_rlp_size"),
        pytest.param(1, id="max_rlp_size_plus_1_byte", marks=pytest.mark.exception_test),
    ],
)
def test_block_at_rlp_size_limit_boundary(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    post: Alloc,
    block_size_limit: int,
    env: Environment,
    exact_size_transactions,
    delta: int,
):
    """
    Test the block rlp size limit.

    - At the limit - 1 byte, the block is valid
    - At the limit, the block is valid
    - At the limit + 1 byte, the block is invalid
    """
    transactions, gas_used = exact_size_transactions
    block_rlp_size = get_block_rlp_size(transactions, gas_used=gas_used)
    assert block_rlp_size == block_size_limit, (
        f"Block RLP size {block_rlp_size} does not exactly match limit {block_size_limit}, "
        f"difference: {block_rlp_size - block_size_limit} bytes"
    )

    block = Block(
        txs=transactions,
        exception=BlockException.RLP_BLOCK_LIMIT_EXCEEDED if delta > 0 else None,
    )

    if delta < 0:
        block.extra_data = Bytes(EXTRA_DATA_AT_LIMIT[: -abs(delta)])
    elif delta == 0:
        block.extra_data = Bytes(EXTRA_DATA_AT_LIMIT)
    else:  # delta > 0
        block.extra_data = Bytes(EXTRA_DATA_AT_LIMIT + b"\x00" * delta)

    block.timestamp = ZeroPaddedHexNumber(HEADER_TIMESTAMP)
    blockchain_test(
        genesis_environment=env,
        pre=pre,
        post=post,
        blocks=[block],
        verify_sync=False if delta > 0 else True,
    )
