"""
Tests for [EIP-7934: RLP Execution Block Size Limit](https://eips.ethereum.org/EIPS/eip-7934).
"""

from functools import lru_cache
from typing import List, Tuple

import pytest
from ethereum_test_base_types import Address, HexNumber, ZeroPaddedHexNumber
from ethereum_test_checklists import EIPChecklist
from ethereum_test_fixtures.blockchain import (
    FixtureBlockBase,
    FixtureHeader,
    FixtureWithdrawal,
)
from ethereum_test_forks import Fork
from ethereum_test_tools import (
    Alloc,
    Block,
    BlockchainTestFiller,
    BlockException,
    Bytes,
    Transaction,
    Withdrawal,
)
from ethereum_test_tools import Opcodes as Op
from ethereum_test_types import EOA, Environment

from .spec import Spec, ref_spec_7934

REFERENCE_SPEC_GIT_PATH = ref_spec_7934.git_path
REFERENCE_SPEC_VERSION = ref_spec_7934.version

pytestmark = [
    pytest.mark.pre_alloc_group(
        "block_rlp_limit_tests",
        reason="Block RLP size tests require exact calculations",
    ),
    pytest.mark.xdist_group(name="bigmem"),
]


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
    """
    Block exceptions expected for blocks that exceed the `MAX_RLP_BLOCK_SIZE`.
    """
    return [BlockException.RLP_BLOCK_LIMIT_EXCEEDED]


def create_test_header(gas_used: int) -> FixtureHeader:
    """Create a standard test header for RLP size calculations."""
    return FixtureHeader(
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


def get_block_rlp_size(
    transactions: List[Transaction],
    gas_used: int,
    withdrawals: List[Withdrawal] | None = None,
) -> int:
    """
    Calculate the RLP size of a block with given transactions
    and withdrawals.
    """
    header = create_test_header(gas_used)
    total_gas = sum((tx.gas_limit or 21000) for tx in transactions)
    header.gas_used = ZeroPaddedHexNumber(total_gas)

    # Calculate blob gas used if there are blob transactions
    blob_gas_used = 0
    for tx in transactions:
        if hasattr(tx, "blob_versioned_hashes") and tx.blob_versioned_hashes:
            blob_gas_used += len(tx.blob_versioned_hashes) * (2**17)

    if blob_gas_used > 0:
        header.blob_gas_used = ZeroPaddedHexNumber(blob_gas_used)

    # Convert withdrawals to FixtureWithdrawal if provided
    block_withdrawals = []
    if withdrawals is not None:
        block_withdrawals = [
            FixtureWithdrawal(
                index=w.index,
                validator_index=w.validator_index,
                address=w.address,
                amount=w.amount,
            )
            for w in withdrawals
        ]
    test_block = FixtureBlockBase(
        blockHeader=header, withdrawals=block_withdrawals
    )
    return len(test_block.with_rlp(txs=transactions).rlp)


def exact_size_transactions(
    sender: EOA,
    block_size_limit: int,
    fork: Fork,
    pre: Alloc,
    gas_limit: int,
    emit_logs: bool = False,
    specific_transaction_to_include: Transaction | None = None,
    withdrawals: List[Withdrawal] | None = None,
) -> Tuple[List[Transaction], int]:
    """
    Generate transactions that fill a block to exactly the RLP size limit.

    The calculation uses caching to avoid recalculating the same block rlp for
    each fork. Calculate the block and fill with real sender for testing.

    Args:
        sender: The sender account
        block_size_limit: The target block RLP size limit
        fork: The fork to generate transactions for
        pre: Required if emit_logs is True, used to deploy the log contract
        gas_limit: The gas limit for the block
        emit_logs: If True, transactions will call a contract that emits logs
        specific_transaction_to_include: If provided, this transaction will
            be included
        withdrawals: Optional list of withdrawals to include in the block

    """
    log_contract = None
    if emit_logs:
        if pre is None:
            raise ValueError("pre is required when emit_logs is True")
        # Deploy a contract that emits logs
        log_contract_code = Op.SSTORE(1, 1)
        # Emit multiple LOG4 events with maximum data and topics
        for _ in range(3):
            log_contract_code += Op.PUSH32(
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
            )  # topic 4
            log_contract_code += Op.PUSH32(
                0xEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEE
            )  # topic 3
            log_contract_code += Op.PUSH32(
                0xDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD
            )  # topic 2
            log_contract_code += Op.PUSH32(
                0xCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC
            )  # topic 1
            log_contract_code += Op.PUSH1(32)  # size
            log_contract_code += Op.PUSH1(0)  # offset
            log_contract_code += Op.LOG4
        log_contract = pre.deploy_contract(log_contract_code)

    if not specific_transaction_to_include and not withdrawals:
        # use cached version when possible for performance
        transactions, gas_used = _exact_size_transactions_cached(
            block_size_limit,
            fork,
            gas_limit,
            sender,
            emit_logs_contract=log_contract,
        )
    else:
        # Direct calculation, no cache, since `Transaction` / `Withdrawal`
        # are not hashable
        transactions, gas_used = _exact_size_transactions_impl(
            block_size_limit,
            fork,
            gas_limit,
            sender,
            specific_transaction_to_include=specific_transaction_to_include,
            emit_logs_contract=log_contract,
            withdrawals=withdrawals,
        )

    return transactions, gas_used


@lru_cache(maxsize=128)
def _exact_size_transactions_cached(
    block_size_limit: int,
    fork: Fork,
    gas_limit: int,
    sender: EOA,
    emit_logs_contract: Address | None = None,
) -> Tuple[List[Transaction], int]:
    """
    Generate transactions that fill a block to exactly the RLP size limit.
    Abstracted with hashable arguments for caching block calculations.
    """
    return _exact_size_transactions_impl(
        block_size_limit,
        fork,
        gas_limit,
        sender,
        None,
        emit_logs_contract,
        None,
    )


def _exact_size_transactions_impl(
    block_size_limit: int,
    fork: Fork,
    block_gas_limit: int,
    sender: EOA,
    specific_transaction_to_include: Transaction | None = None,
    emit_logs_contract: Address | None = None,
    withdrawals: List[Withdrawal] | None = None,
) -> Tuple[List[Transaction], int]:
    """
    Calculate the exact size of transactions to be included. Shared by both
    cached and non-cached paths.
    """
    transactions = []
    nonce = 0
    total_gas_used = 0

    calculator = fork.transaction_intrinsic_cost_calculator()

    data_large = Bytes(b"\x00" * 500_000)
    gas_limit_large = calculator(calldata=data_large)

    # block with 16 transactions + large calldata remains safely below the
    # limit add 15 generic transactions to fill the block and one typed
    # transaction if tx_type is specified, otherwise just add 16 generic
    # transactions
    not_all_generic_txs = any(
        kwarg is not None
        for kwarg in [specific_transaction_to_include, emit_logs_contract]
    )

    generic_tx_num = 15 if not_all_generic_txs else 16
    for _ in range(generic_tx_num):
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

    # append a typed transaction to fill the block
    if not_all_generic_txs:
        if specific_transaction_to_include is not None:
            tx_dict = specific_transaction_to_include.model_dump(
                exclude_unset=True
            )
            data = Bytes(b"\x00" * 200_000)
            gas_limit = HexNumber(
                calculator(
                    calldata=data,
                    access_list=specific_transaction_to_include.access_list,
                    authorization_list_or_count=len(
                        tx_dict.get("authorization_list", [])
                    ),
                )
            )
            tx_dict["sender"] = sender
            tx_dict["nonce"] = nonce
            tx_dict["data"] = data
            tx_dict["gas_limit"] = gas_limit
            last_tx = Transaction(**tx_dict)
        elif emit_logs_contract is not None:
            last_tx = Transaction(
                sender=sender,
                nonce=nonce,
                max_fee_per_gas=10**11,
                max_priority_fee_per_gas=10**11,
                gas_limit=calculator(calldata=b""),
                to=emit_logs_contract,
            )
        else:
            raise ValueError(
                "Either specific_transaction_to_include or "
                "emit_logs_contract must be provided."
            )

        transactions.append(last_tx)
        nonce += 1
        total_gas_used += last_tx.gas_limit

    current_size = get_block_rlp_size(
        transactions, gas_used=total_gas_used, withdrawals=withdrawals
    )
    remaining_bytes = block_size_limit - current_size
    remaining_gas = block_gas_limit - total_gas_used

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
            transactions + [empty_tx],
            gas_used=total_gas_used + empty_tx.gas_limit,
            withdrawals=withdrawals,
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
                transactions + [test_tx],
                gas_used=total_gas_used + target_gas,
                withdrawals=withdrawals,
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
                            withdrawals=withdrawals,
                        )

                        if adjusted_test_size == block_size_limit:
                            # exact match
                            transactions.append(adjusted_tx)
                            break

                        adjusted_diff = abs(
                            block_size_limit - adjusted_test_size
                        )
                        if adjusted_diff < best_diff:
                            best_diff = adjusted_diff
                else:
                    raise RuntimeError(
                        "Failed to find a transaction that matches "
                        "the target size."
                    )
        else:
            transactions.append(empty_tx)

    final_size = get_block_rlp_size(
        transactions,
        gas_used=sum(tx.gas_limit for tx in transactions),
        withdrawals=withdrawals,
    )
    final_gas = sum(tx.gas_limit for tx in transactions)

    assert final_size == block_size_limit, (
        f"Size mismatch: got {final_size}, "
        f"expected {block_size_limit} "
        f"({final_size - block_size_limit} bytes diff)"
    )
    return transactions, final_gas


@EIPChecklist.BlockLevelConstraint.Test.Boundary.Under()
@EIPChecklist.BlockLevelConstraint.Test.Boundary.Exact()
@EIPChecklist.BlockLevelConstraint.Test.Boundary.Over()
@pytest.mark.parametrize(
    "delta",
    [
        pytest.param(
            -1, id="max_rlp_size_minus_1_byte", marks=pytest.mark.verify_sync
        ),
        pytest.param(0, id="max_rlp_size", marks=pytest.mark.verify_sync),
        pytest.param(
            1, id="max_rlp_size_plus_1_byte", marks=pytest.mark.exception_test
        ),
    ],
)
@pytest.mark.valid_from("Osaka")
def test_block_at_rlp_size_limit_boundary(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    post: Alloc,
    env: Environment,
    sender: EOA,
    fork: Fork,
    block_size_limit: int,
    delta: int,
) -> None:
    """
    Test the block rlp size limit.

    - At the limit - 1 byte, the block is valid
    - At the limit, the block is valid
    - At the limit + 1 byte, the block is invalid
    """
    transactions, gas_used = exact_size_transactions(
        sender,
        block_size_limit,
        fork,
        pre,
        env.gas_limit,
    )
    block_rlp_size = get_block_rlp_size(transactions, gas_used=gas_used)
    assert block_rlp_size == block_size_limit, (
        f"Block RLP size {block_rlp_size} does not exactly match "
        f"limit {block_size_limit}, difference: "
        f"{block_rlp_size - block_size_limit} bytes"
    )

    block = Block(
        txs=transactions,
        exception=BlockException.RLP_BLOCK_LIMIT_EXCEEDED
        if delta > 0
        else None,
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
    )


@EIPChecklist.BlockLevelConstraint.Test.Content.TransactionTypes()
@pytest.mark.with_all_typed_transactions
@pytest.mark.verify_sync
@pytest.mark.valid_from("Osaka")
def test_block_rlp_size_at_limit_with_all_typed_transactions(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    post: Alloc,
    fork: Fork,
    sender: EOA,
    block_size_limit: int,
    env: Environment,
    typed_transaction: Transaction,
) -> None:
    """Test the block RLP size limit with all transaction types."""
    transactions, gas_used = exact_size_transactions(
        sender,
        block_size_limit,
        fork,
        pre,
        env.gas_limit,
        specific_transaction_to_include=typed_transaction,
    )
    block_rlp_size = get_block_rlp_size(transactions, gas_used=gas_used)
    assert block_rlp_size == block_size_limit, (
        f"Block RLP size {block_rlp_size} does not exactly match limit "
        f"{block_size_limit}, difference: {block_rlp_size - block_size_limit} "
        "bytes"
    )

    block = Block(txs=transactions)
    block.extra_data = Bytes(EXTRA_DATA_AT_LIMIT)
    block.timestamp = ZeroPaddedHexNumber(HEADER_TIMESTAMP)

    blockchain_test(
        genesis_environment=env,
        pre=pre,
        post=post,
        blocks=[block],
    )


@EIPChecklist.BlockLevelConstraint.Test.Content.Logs()
@pytest.mark.verify_sync
@pytest.mark.valid_from("Osaka")
def test_block_at_rlp_limit_with_logs(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    post: Alloc,
    env: Environment,
    sender: EOA,
    fork: Fork,
    block_size_limit: int,
) -> None:
    """
    Test that a block at the RLP size limit is valid even when transactions
    emit logs.
    """
    transactions, gas_used = exact_size_transactions(
        sender,
        block_size_limit,
        fork,
        pre,
        env.gas_limit,
        emit_logs=True,
    )

    block_rlp_size = get_block_rlp_size(transactions, gas_used=gas_used)
    assert block_rlp_size == block_size_limit, (
        f"Block RLP size {block_rlp_size} does not exactly match limit "
        f"{block_size_limit}, difference: {block_rlp_size - block_size_limit} "
        "bytes"
    )

    block = Block(txs=transactions)
    block.extra_data = Bytes(EXTRA_DATA_AT_LIMIT)
    block.timestamp = ZeroPaddedHexNumber(HEADER_TIMESTAMP)

    blockchain_test(
        genesis_environment=env,
        pre=pre,
        post=post,
        blocks=[block],
    )


@EIPChecklist.BlockLevelConstraint.Test.Content.Withdrawals()
@pytest.mark.verify_sync
@pytest.mark.valid_from("Osaka")
def test_block_at_rlp_limit_with_withdrawals(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    post: Alloc,
    env: Environment,
    sender: EOA,
    fork: Fork,
    block_size_limit: int,
) -> None:
    """
    Test that a block at the RLP size limit is valid even when the block
    contains withdrawals.
    """
    withdrawals = [
        Withdrawal(
            index=0,
            validator_index=0,
            address=pre.fund_eoa(),
            amount=1,
        ),
        Withdrawal(
            index=1,
            validator_index=1,
            address=pre.fund_eoa(),
            amount=1,
        ),
    ]

    transactions, gas_used = exact_size_transactions(
        sender,
        block_size_limit,
        fork,
        pre,
        env.gas_limit,
        withdrawals=withdrawals,
    )

    block_rlp_size = get_block_rlp_size(
        transactions, gas_used=gas_used, withdrawals=withdrawals
    )
    assert block_rlp_size == block_size_limit, (
        f"Block RLP size {block_rlp_size} does not exactly match limit "
        f"{block_size_limit}, difference: {block_rlp_size - block_size_limit} "
        "bytes"
    )

    block = Block(
        txs=transactions,
        withdrawals=withdrawals,
        extra_data=Bytes(EXTRA_DATA_AT_LIMIT),
        timestamp=ZeroPaddedHexNumber(HEADER_TIMESTAMP),
    )

    blockchain_test(
        genesis_environment=env,
        pre=pre,
        post=post,
        blocks=[block],
    )


@EIPChecklist.BlockLevelConstraint.Test.ForkTransition.AcceptedBeforeFork()
@EIPChecklist.BlockLevelConstraint.Test.ForkTransition.AcceptedAfterFork()
@EIPChecklist.BlockLevelConstraint.Test.ForkTransition.RejectedAfterFork()
@pytest.mark.parametrize(
    "exceeds_limit_at_fork",
    [
        pytest.param(False, id="at_fork_within_limit"),
        pytest.param(
            True, marks=pytest.mark.exception_test, id="at_fork_exceeds_limit"
        ),
    ],
)
@pytest.mark.valid_at_transition_to("Osaka")
def test_fork_transition_block_rlp_limit(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    env: Environment,
    fork: Fork,
    exceeds_limit_at_fork: bool,
    block_size_limit: int,
) -> None:
    """
    Test block RLP size limit at fork transition boundary.

    - Before fork (timestamp 14999): Block at limit +1 should be accepted
    - At fork (timestamp 15000): Block at limit should be accepted
    - At fork (timestamp 15000): Block at limit +1 should be rejected
    """
    sender_before_fork = pre.fund_eoa()
    sender_at_fork = pre.fund_eoa()

    transactions_before, gas_used_before = exact_size_transactions(
        sender_before_fork,
        block_size_limit,
        fork,
        pre,
        env.gas_limit,
    )

    transactions_at_fork, gas_used_at_fork = exact_size_transactions(
        sender_at_fork,
        block_size_limit,
        fork,
        pre,
        env.gas_limit,
    )

    for fork_block_rlp_size in [
        get_block_rlp_size(transactions_before, gas_used=gas_used_before),
        get_block_rlp_size(transactions_at_fork, gas_used=gas_used_at_fork),
    ]:
        assert fork_block_rlp_size == block_size_limit, (
            f"Block RLP size {fork_block_rlp_size} does not exactly match "
            f"limit {block_size_limit}, difference: "
            f"{fork_block_rlp_size - block_size_limit} bytes"
        )

    # HEADER_TIMESTAMP (123456789) used in calculation takes 4 bytes in RLP
    # encoding. Transition timestamps (14_999 and 15_000) take 2 bytes
    # Re-define `_extradata_at_limit` accounting for this difference
    timestamp_byte_savings = 2
    _extradata_at_limit = EXTRA_DATA_AT_LIMIT + (
        b"\x00" * timestamp_byte_savings
    )

    blocks = [
        # before fork, block at limit +1 should be accepted
        Block(
            timestamp=14_999,
            txs=transactions_before,
            # +1 to exceed limit
            extra_data=Bytes(_extradata_at_limit + b"\x00"),
        )
    ]

    # At fork (timestamp 15000): Test behavior with and without exceeding limit
    if exceeds_limit_at_fork:
        blocks.append(
            Block(
                timestamp=15_000,
                txs=transactions_at_fork,
                # +1 to exceed limit, should be rejected
                extra_data=Bytes(_extradata_at_limit + b"\x00"),
                exception=BlockException.RLP_BLOCK_LIMIT_EXCEEDED,
            )
        )
    else:
        blocks.append(
            Block(
                timestamp=15_000,
                txs=transactions_at_fork,
                # exact limit should be accepted
                extra_data=Bytes(EXTRA_DATA_AT_LIMIT),
            )
        )

    blockchain_test(
        genesis_environment=env,
        pre=pre,
        post={},
        blocks=blocks,
    )
