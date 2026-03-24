"""
Tests for [EIP-7934: RLP Execution Block Size Limit](https://eips.ethereum.org/EIPS/eip-7934).
"""

from functools import lru_cache
from typing import Any, Callable, List, Sized, Tuple

import pytest
from execution_testing import (
    EOA,
    Address,
    Alloc,
    Block,
    BlockchainTestFiller,
    BlockException,
    Bytes,
    EIPChecklist,
    Environment,
    Fork,
    Op,
    Transaction,
    Withdrawal,
)
from execution_testing.base_types import (
    HexNumber,
    ZeroPaddedHexNumber,
)
from execution_testing.fixtures.blockchain import (
    FixtureBlockBase,
    FixtureWithdrawal,
)

from .spec import Spec, ref_spec_7934

REFERENCE_SPEC_GIT_PATH = ref_spec_7934.git_path
REFERENCE_SPEC_VERSION = ref_spec_7934.version

pytestmark = pytest.mark.xdist_group(name="bigmem")


HEADER_TIMESTAMP = 123456789
EXTRA_DATA_AT_LIMIT = b"\x00" * 15
# Max size adjustment extra_data can absorb
# reserves 1 byte so delta=-1 tests stay valid
EXTRA_DATA_TOLERANCE = len(EXTRA_DATA_AT_LIMIT) - 1
BLOCK_GAS_LIMIT = 100_000_000
BLOCK_GAS_LIMIT_MARGIN = 1_000_000


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


@lru_cache(maxsize=128)
def max_zero_calldata_bytes_for_gas(
    fork: Fork,
    gas_limit: int,
    *,
    max_len_hint: int,
) -> int:
    """Return the largest zero-calldata length whose intrinsic gas fits."""
    calculator = fork.transaction_intrinsic_cost_calculator()
    return _max_zero_calldata_bytes_for_gas(
        calculator, gas_limit, max_len_hint=max_len_hint
    )


def _max_zero_calldata_bytes_for_gas(
    calculator: Callable[..., int],
    gas_limit: int,
    *,
    max_len_hint: int,
    access_list: Any | None = None,
    authorization_list_or_count: Sized | int | None = None,
) -> int:
    """Return the largest zero-calldata length whose intrinsic gas fits."""
    if gas_limit <= 0:
        return 0

    kwargs: dict[str, object] = {}
    if access_list is not None:
        kwargs["access_list"] = access_list
    if authorization_list_or_count is not None:
        kwargs["authorization_list_or_count"] = authorization_list_or_count

    if calculator(calldata=b"", **kwargs) > gas_limit:
        return 0

    upper_bound = max(1, max_len_hint)
    lo = 0
    hi = 1

    while (
        hi < upper_bound
        and calculator(calldata=b"\x00" * hi, **kwargs) <= gas_limit
    ):
        lo = hi
        hi = min(hi * 2, upper_bound)

    if (
        hi == upper_bound
        and calculator(calldata=b"\x00" * hi, **kwargs) <= gas_limit
    ):
        return hi

    while lo + 1 < hi:
        mid = (lo + hi) // 2
        if calculator(calldata=b"\x00" * mid, **kwargs) <= gas_limit:
            lo = mid
        else:
            hi = mid

    return lo


@lru_cache(maxsize=128)
def calibrated_block_gas_limit(
    fork: Fork,
    block_size_limit: int,
    requested_gas_limit: int,
) -> int:
    """
    Return a block gas limit that can support building a block near the target
    RLP size under the fork's calldata pricing.
    """
    calculator = fork.transaction_intrinsic_cost_calculator()
    tx_gas_limit_cap = fork.transaction_gas_limit_cap()

    # Estimate calldata bytes required to approach the RLP limit and reserve a
    # small margin for RLP overhead variability.
    estimated_calldata_bytes = block_size_limit + 1024

    if tx_gas_limit_cap is not None:
        max_bytes_per_tx = max_zero_calldata_bytes_for_gas(
            fork,
            tx_gas_limit_cap,
            max_len_hint=estimated_calldata_bytes,
        )
        if max_bytes_per_tx > 0:
            max_tx_gas = calculator(calldata=b"\x00" * max_bytes_per_tx)
            tx_count = (
                estimated_calldata_bytes + max_bytes_per_tx - 1
            ) // max_bytes_per_tx
            estimated_required_gas = (
                tx_count * max_tx_gas + BLOCK_GAS_LIMIT_MARGIN
            )
        else:
            estimated_required_gas = BLOCK_GAS_LIMIT
    else:
        empty_calldata_cost = calculator(calldata=b"")
        one_zero_byte_cost = calculator(calldata=b"\x00")
        per_zero_byte_cost = max(one_zero_byte_cost - empty_calldata_cost, 1)
        estimated_required_gas = (
            empty_calldata_cost
            + estimated_calldata_bytes * per_zero_byte_cost
            + BLOCK_GAS_LIMIT_MARGIN
        )

    return max(
        requested_gas_limit,
        BLOCK_GAS_LIMIT,
        estimated_required_gas,
    )


@pytest.fixture(autouse=True)
def calibrate_gas_limit(
    env: Environment,
    fork: Fork,
    block_size_limit: int,
) -> None:
    """Calibrate block gas limit for fork-specific calldata pricing."""
    env.gas_limit = ZeroPaddedHexNumber(
        calibrated_block_gas_limit(
            fork=fork,
            block_size_limit=block_size_limit,
            requested_gas_limit=env.gas_limit,
        )
    )


def get_block_rlp_size(
    fork: Fork,
    transactions: List[Transaction],
    block_gas_limit: int,
    withdrawals: List[Withdrawal] | None = None,
) -> int:
    """
    Calculate the RLP size of a block with given transactions
    and withdrawals.
    """
    header = fork.build_default_block_header(
        block_number=1,
        timestamp=HEADER_TIMESTAMP,
    )
    header.gas_limit = ZeroPaddedHexNumber(block_gas_limit)
    header.extra_data = Bytes(EXTRA_DATA_AT_LIMIT)

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
    test_block = FixtureBlockBase(header=header, withdrawals=block_withdrawals)
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

    Due to RLP encoding boundaries, certain exact block sizes may be
    unachievable (±1 byte). The returned extra_data_len compensates for
    any gap so the final block hits the exact target.

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

    Returns:
        Tuple of (transactions, extra_data_len) where extra_data_len is
        the number of extra_data bytes needed to hit the exact target
        block size.

    """
    effective_block_gas_limit = calibrated_block_gas_limit(
        fork=fork,
        block_size_limit=block_size_limit,
        requested_gas_limit=gas_limit,
    )

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
        transactions, extra_data_len = _exact_size_transactions_cached(
            block_size_limit,
            fork,
            effective_block_gas_limit,
            sender,
            emit_logs_contract=log_contract,
        )
    else:
        # Direct calculation, no cache, since `Transaction` / `Withdrawal`
        # are not hashable
        transactions, extra_data_len = _exact_size_transactions_impl(
            block_size_limit,
            fork,
            effective_block_gas_limit,
            sender,
            specific_transaction_to_include=specific_transaction_to_include,
            emit_logs_contract=log_contract,
            withdrawals=withdrawals,
        )

    return transactions, extra_data_len


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

    Returns:
        Tuple of (transactions, extra_data_len) where extra_data_len is
        the number of extra_data bytes needed to hit the exact target
        block size.

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
    tx_gas_limit_cap = fork.transaction_gas_limit_cap()
    per_tx_gas_budget = (
        block_gas_limit
        if tx_gas_limit_cap is None
        else min(tx_gas_limit_cap, block_gas_limit)
    )

    max_data_len = 500_000
    if tx_gas_limit_cap is not None:
        while (
            max_data_len > 0
            and calculator(calldata=b"\x00" * max_data_len) > tx_gas_limit_cap
        ):
            max_data_len //= 2

    data_large = Bytes(b"\x00" * max_data_len)
    gas_limit_large = calculator(calldata=data_large)
    if gas_limit_large > per_tx_gas_budget:
        raise ValueError(
            "Unable to build calldata transaction within gas limits"
        )
    empty_tx_gas_limit = calculator(calldata=b"")

    not_all_generic_txs = any(
        kwarg is not None
        for kwarg in [specific_transaction_to_include, emit_logs_contract]
    )

    sample_base_size = get_block_rlp_size(
        fork,
        [],
        block_gas_limit=block_gas_limit,
        withdrawals=withdrawals,
    )
    sample_generic_tx = Transaction(
        sender=sender,
        nonce=0,
        max_fee_per_gas=10**11,
        max_priority_fee_per_gas=10**11,
        gas_limit=gas_limit_large,
        data=data_large,
    )
    generic_tx_contribution = (
        get_block_rlp_size(
            fork,
            [sample_generic_tx],
            block_gas_limit=block_gas_limit,
            withdrawals=withdrawals,
        )
        - sample_base_size
    )

    special_tx_contribution = 0
    special_tx_gas_limit = 0
    special_tx_dict = None
    special_tx_data = None

    if not_all_generic_txs:
        if specific_transaction_to_include is not None:
            special_tx_dict = specific_transaction_to_include.model_dump(
                exclude_unset=True
            )
            authorization_count = len(
                special_tx_dict.get("authorization_list", [])
            )
            max_special_data_len = _max_zero_calldata_bytes_for_gas(
                calculator,
                per_tx_gas_budget,
                max_len_hint=200_000,
                access_list=specific_transaction_to_include.access_list,
                authorization_list_or_count=authorization_count,
            )
            special_tx_data = Bytes(b"\x00" * max_special_data_len)
            special_tx_gas_limit = int(
                calculator(
                    calldata=special_tx_data,
                    access_list=specific_transaction_to_include.access_list,
                    authorization_list_or_count=authorization_count,
                )
            )
            sample_special_tx = Transaction(
                **{
                    **special_tx_dict,
                    "sender": sender,
                    "nonce": 0,
                    "data": special_tx_data,
                    "gas_limit": HexNumber(special_tx_gas_limit),
                }
            )
        elif emit_logs_contract is not None:
            special_tx_gas_limit = empty_tx_gas_limit
            sample_special_tx = Transaction(
                sender=sender,
                nonce=0,
                max_fee_per_gas=10**11,
                max_priority_fee_per_gas=10**11,
                gas_limit=special_tx_gas_limit,
                to=emit_logs_contract,
            )
        else:
            raise ValueError(
                "Either specific_transaction_to_include or "
                "emit_logs_contract must be provided."
            )

        special_tx_contribution = (
            get_block_rlp_size(
                fork,
                [sample_special_tx],
                block_gas_limit=block_gas_limit,
                withdrawals=withdrawals,
            )
            - sample_base_size
        )

    gas_for_generics = max(
        block_gas_limit - special_tx_gas_limit - empty_tx_gas_limit,
        0,
    )
    max_generic_by_gas = gas_for_generics // gas_limit_large
    size_for_generics = max(
        block_size_limit
        - EXTRA_DATA_TOLERANCE
        - sample_base_size
        - special_tx_contribution,
        0,
    )
    max_generic_by_size = size_for_generics // max(generic_tx_contribution, 1)
    generic_tx_num = min(max_generic_by_gas, max_generic_by_size)

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

    if not_all_generic_txs:
        if specific_transaction_to_include is not None:
            assert special_tx_dict is not None
            assert special_tx_data is not None
            tx_dict = dict(special_tx_dict)
            tx_dict["sender"] = sender
            tx_dict["nonce"] = nonce
            tx_dict["data"] = special_tx_data
            tx_dict["gas_limit"] = HexNumber(special_tx_gas_limit)
            last_tx = Transaction(**tx_dict)
        elif emit_logs_contract is not None:
            last_tx = Transaction(
                sender=sender,
                nonce=nonce,
                max_fee_per_gas=10**11,
                max_priority_fee_per_gas=10**11,
                gas_limit=special_tx_gas_limit,
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
        fork,
        transactions,
        block_gas_limit=block_gas_limit,
        withdrawals=withdrawals,
    )
    remaining_bytes = block_size_limit - current_size
    remaining_gas = block_gas_limit - total_gas_used

    topoff_gas_budget = (
        remaining_gas
        if tx_gas_limit_cap is None
        else min(remaining_gas, tx_gas_limit_cap)
    )
    if remaining_bytes > 0 and topoff_gas_budget > 50_000:
        # create an empty transaction to measure base contribution
        empty_tx = Transaction(
            sender=sender,
            nonce=nonce,
            max_fee_per_gas=10**11,
            max_priority_fee_per_gas=10**11,
            gas_limit=empty_tx_gas_limit,
            data=b"",
        )

        empty_block_size = get_block_rlp_size(
            fork,
            transactions + [empty_tx],
            block_gas_limit=block_gas_limit,
            withdrawals=withdrawals,
        )
        empty_contribution = empty_block_size - current_size

        calldata_bytes_needed = remaining_bytes - empty_contribution
        estimated_calldata = max(0, calldata_bytes_needed - 5)

        max_topoff_calldata = max_zero_calldata_bytes_for_gas(
            fork,
            topoff_gas_budget,
            max_len_hint=max(estimated_calldata, 1),
        )
        target_calldata = b"\x00" * min(
            estimated_calldata, max_topoff_calldata
        )
        target_gas = calculator(calldata=target_calldata)

        if target_gas <= topoff_gas_budget:
            test_tx = Transaction(
                sender=sender,
                nonce=nonce,
                max_fee_per_gas=10**11,
                max_priority_fee_per_gas=10**11,
                gas_limit=target_gas,
                data=target_calldata,
            )
            transactions.append(test_tx)
        else:
            transactions.append(empty_tx)

    final_size = get_block_rlp_size(
        fork,
        transactions,
        block_gas_limit=block_gas_limit,
        withdrawals=withdrawals,
    )
    # Compute the extra_data length that compensates for any size gap.
    size_diff = final_size - block_size_limit
    assert abs(size_diff) <= EXTRA_DATA_TOLERANCE, (
        f"Size mismatch: got {final_size}, "
        f"expected {block_size_limit} "
        f"({size_diff} bytes diff, exceeds ±{EXTRA_DATA_TOLERANCE} tolerance)"
    )
    extra_data_len = len(EXTRA_DATA_AT_LIMIT) - size_diff
    return transactions, extra_data_len


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
    transactions, extra_data_len = exact_size_transactions(
        sender,
        block_size_limit,
        fork,
        pre,
        env.gas_limit,
    )

    block = Block(
        txs=transactions,
        exception=BlockException.RLP_BLOCK_LIMIT_EXCEEDED
        if delta > 0
        else None,
    )

    target_extra_data_len = max(extra_data_len + delta, 0)
    block.extra_data = Bytes(b"\x00" * target_extra_data_len)

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
@pytest.mark.json_loader
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
    transactions, extra_data_len = exact_size_transactions(
        sender,
        block_size_limit,
        fork,
        pre,
        env.gas_limit,
        specific_transaction_to_include=typed_transaction,
    )

    block = Block(txs=transactions)
    block.extra_data = Bytes(b"\x00" * extra_data_len)
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
    transactions, extra_data_len = exact_size_transactions(
        sender,
        block_size_limit,
        fork,
        pre,
        env.gas_limit,
        emit_logs=True,
    )

    block = Block(txs=transactions)
    block.extra_data = Bytes(b"\x00" * extra_data_len)
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

    transactions, extra_data_len = exact_size_transactions(
        sender,
        block_size_limit,
        fork,
        pre,
        env.gas_limit,
        withdrawals=withdrawals,
    )

    block = Block(
        txs=transactions,
        withdrawals=withdrawals,
        extra_data=Bytes(b"\x00" * extra_data_len),
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

    transactions_before, extra_data_len_before = exact_size_transactions(
        sender_before_fork,
        block_size_limit,
        fork,
        pre,
        env.gas_limit,
    )

    transactions_at_fork, extra_data_len_at_fork = exact_size_transactions(
        sender_at_fork,
        block_size_limit,
        fork,
        pre,
        env.gas_limit,
    )

    # HEADER_TIMESTAMP (123456789) used in calculation takes 4 bytes in RLP
    # encoding. Transition timestamps (14_999 and 15_000) take 2 bytes.
    # Add the difference to extra_data to keep block at the limit.
    timestamp_byte_savings = 2

    extra_data_before = extra_data_len_before + timestamp_byte_savings
    extra_data_at_fork = extra_data_len_at_fork + timestamp_byte_savings

    blocks = [
        # before fork, block at limit +1 should be accepted
        Block(
            timestamp=14_999,
            txs=transactions_before,
            # +1 to exceed limit
            extra_data=Bytes(b"\x00" * (extra_data_before + 1)),
        )
    ]

    # At fork (timestamp 15000): Test behavior with and without exceeding limit
    if exceeds_limit_at_fork:
        blocks.append(
            Block(
                timestamp=15_000,
                txs=transactions_at_fork,
                # +1 to exceed limit, should be rejected
                extra_data=Bytes(b"\x00" * (extra_data_at_fork + 1)),
                exception=BlockException.RLP_BLOCK_LIMIT_EXCEEDED,
            )
        )
    else:
        blocks.append(
            Block(
                timestamp=15_000,
                txs=transactions_at_fork,
                # exact limit should be accepted
                extra_data=Bytes(b"\x00" * extra_data_at_fork),
            )
        )

    blockchain_test(
        genesis_environment=env,
        pre=pre,
        post={},
        blocks=blocks,
    )
