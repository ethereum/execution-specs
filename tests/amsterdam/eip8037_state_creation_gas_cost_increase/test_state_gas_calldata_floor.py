"""
Test EIP-7623 calldata floor interaction with EIP-8037 state gas.

The calldata floor applies to the execution gas dimension only. It
does not affect state gas. Block gas accounting applies the floor to
the execution dimension (``max(pre_refund_gas - state_gas, floor)``),
so a transaction contributes at least the floor to the block's
execution gas while state gas is tracked separately.

Tests for [EIP-8037: State Creation Gas Cost Increase]
(https://eips.ethereum.org/EIPS/eip-8037).
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Block,
    BlockchainTestFiller,
    Fork,
    Header,
    Op,
    StateTestFiller,
    Storage,
    Transaction,
    TransactionException,
    TransactionReceipt,
)
from execution_testing.checklists import EIPChecklist

from .spec import ref_spec_8037

REFERENCE_SPEC_GIT_PATH = ref_spec_8037.git_path
REFERENCE_SPEC_VERSION = ref_spec_8037.version


@EIPChecklist.GasRefundsChanges.Test.CrossFunctional.CalldataCost()
@pytest.mark.valid_from("EIP8037")
def test_calldata_floor_with_sstore(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Test calldata floor does not affect state gas charging.

    A transaction with large calldata triggers the calldata floor for
    execution gas, but state gas for SSTORE is charged independently.
    """
    storage = Storage()
    contract = pre.deploy_contract(
        code=Op.SSTORE(storage.store_next(1), 1),
    )

    # Large calldata to trigger the calldata floor
    calldata = b"\x01" * 256

    tx = Transaction(
        to=contract,
        data=calldata,
        state_gas_reservoir=0,
        sender=pre.fund_eoa(),
    )

    post = {contract: Account(storage=storage)}
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("EIP8037")
def test_calldata_floor_independent_of_state_gas(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Test calldata floor applies only to execution gas dimension.

    The calldata floor applies only to the sender's bill and does not
    affect the state gas dimension. A transaction with high calldata
    and no state operations should succeed even when the floor exceeds
    actual execution gas.
    """
    contract = pre.deploy_contract(code=Op.STOP)

    # Large calldata so the floor exceeds actual execution gas
    calldata = b"\xff" * 512

    tx = Transaction(
        to=contract,
        data=calldata,
        state_gas_reservoir=0,
        sender=pre.fund_eoa(),
    )

    state_test(pre=pre, post={}, tx=tx)


@pytest.mark.valid_from("EIP8037")
def test_calldata_floor_higher_than_execution_with_state_ops(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test state gas is tracked separately when calldata floor dominates.

    Even when calldata floor > actual execution gas used, state gas for
    SSTORE is charged normally from the reservoir or gas_left.
    """
    sstore_state_gas = Op.SSTORE(new_value=1).state_cost(fork)

    storage = Storage()
    contract = pre.deploy_contract(
        code=Op.SSTORE(storage.store_next(1), 1),
    )

    # Large calldata so floor dominates execution gas
    calldata = b"\x01" * 1024

    tx = Transaction(
        to=contract,
        data=calldata,
        state_gas_reservoir=sstore_state_gas,
        sender=pre.fund_eoa(),
    )

    post = {contract: Account(storage=storage)}
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.inclusion_test
@pytest.mark.parametrize(
    "exceeds_cap",
    [
        pytest.param(False, id="at_cap"),
        pytest.param(True, id="exceeds_cap", marks=pytest.mark.exception_test),
    ],
)
@pytest.mark.valid_from("EIP8037")
def test_calldata_floor_exceeding_tx_gas_limit_cap(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    exceeds_cap: bool,
) -> None:
    """
    Reject a transaction whose calldata floor exceeds the cap, isolating
    the cap check from the sufficiency check.

    EIP-8037 caps ``max(intrinsic_execution, calldata_floor)`` at
    ``TX_MAX_GAS_LIMIT``. When the EIP-7976 calldata floor crosses the cap
    the transaction must be rejected even though the execution intrinsic gas
    is within the cap. For the rejection case ``gas_limit`` is set above the
    floor so the sufficiency check ``max(intrinsic_total, floor) <= tx.gas``
    passes and the cap is the only reason for rejection — the exact shape a
    client with the sufficiency gate but no cap gate would wrongly execute.

    at_cap: tightest calldata floor that fits within the cap —
    transaction accepted.
    exceeds_cap: one byte more tips the floor over the cap —
    transaction rejected.
    """
    cap = fork.transaction_gas_limit_cap()
    assert cap is not None
    floor_cost = fork.transaction_data_floor_cost_calculator()

    # Binary-search the largest all-nonzero calldata whose floor cost fits
    # within the gas cap; `exceeds_cap` adds one more byte to tip the floor
    # over. Driven by the floor calculator directly so it tracks the
    # per-byte token pricing across forks.
    def floor_fits(num_bytes: int) -> bool:
        return floor_cost(data=b"\x01" * num_bytes) <= cap

    high = 1
    while floor_fits(high):
        high *= 2
    low = high // 2
    while low < high:
        mid = (low + high + 1) // 2
        if floor_fits(mid):
            low = mid
        else:
            high = mid - 1
    max_bytes = low + 1 if exceeds_cap else low
    calldata = b"\x01" * max_bytes

    contract = pre.deploy_contract(Op.STOP)
    floor = floor_cost(data=calldata)

    if exceeds_cap:
        intrinsic = fork.transaction_intrinsic_cost_calculator()
        execution = intrinsic(
            calldata=calldata,
            return_cost_deducted_prior_execution=True,
        )
        assert floor > cap, "calldata floor must exceed the cap"
        assert execution < cap, "execution intrinsic must stay below the cap"
        # Fund the floor in full so the sufficiency check cannot reject the
        # transaction first; only the cap check can.
        gas_limit = floor + 1_000_000
    else:
        assert floor <= cap
        gas_limit = cap

    tx = Transaction(
        to=contract,
        data=calldata,
        gas_limit=gas_limit,
        sender=pre.fund_eoa(),
        error=TransactionException.INTRINSIC_GAS_TOO_LOW
        if exceeds_cap
        else None,
    )

    post = {contract: Account(code=Op.STOP)} if not exceeds_cap else {}
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("EIP8037")
def test_calldata_floor_applied_to_sender_refund(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Verify the calldata floor is applied to the sender gas refund.

    With a STOP callee and large all-nonzero calldata, execution gas
    falls below the calldata floor. The sender must be charged
    `calldata_floor * gas_price`, so the final balance reflects the
    floor-applied value, not the pre-floor execution cost.
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    calldata = b"\xff" * 1024
    calldata_floor = fork.transaction_intrinsic_cost_calculator()(
        calldata=calldata,
    )
    gas_price = 10**9
    initial = gas_limit_cap * gas_price

    contract = pre.deploy_contract(code=Op.STOP)
    sender = pre.fund_eoa(amount=initial)

    tx = Transaction(
        to=contract,
        data=calldata,
        gas_limit=gas_limit_cap,
        gas_price=gas_price,
        sender=sender,
    )

    blockchain_test(
        pre=pre,
        blocks=[Block(txs=[tx])],
        post={sender: Account(balance=initial - calldata_floor * gas_price)},
    )


@pytest.mark.valid_from("EIP8037")
def test_calldata_floor_binds_with_reservoir(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Bind the calldata floor while an over-cap reservoir funds state gas.

    Large calldata makes the EIP-7976 floor the sender's bill, while an
    over-cap `gas_limit` puts the SSTORE-set state charge in the
    reservoir. The floor binds the receipt and the block's execution
    dimension alike, so the header gas_used is the floor (not the
    state dimension).
    """
    storage = Storage()
    code = Op.SSTORE(storage.store_next(1), 1, new_value=1)
    state_cost = code.state_cost(fork)
    execution_cost = code.execution_cost(fork)

    # Sized so the floor binds while block-execution stays under storage_set.
    calldata = b"\x00" * 5000
    floor = fork.transaction_data_floor_cost_calculator()(data=calldata)
    intrinsic = fork.transaction_intrinsic_cost_calculator()(
        calldata=calldata,
        return_cost_deducted_prior_execution=True,
    )
    tx_execution = intrinsic + execution_cost
    assert floor > tx_execution + state_cost, (
        "calldata floor must exceed the sender's pre-floor bill"
    )
    assert tx_execution < state_cost, (
        "block-execution must stay under the state dimension"
    )

    contract = pre.deploy_contract(code=code)

    tx = Transaction(
        to=contract,
        data=calldata,
        state_gas_reservoir=state_cost,
        sender=pre.fund_eoa(),
        expected_receipt=TransactionReceipt(cumulative_gas_used=floor),
    )
    state_test(
        pre=pre,
        post={contract: Account(storage=storage)},
        tx=tx,
        blockchain_test_header_verify=Header(gas_used=floor),
    )


@pytest.mark.valid_from("EIP8037")
def test_calldata_floor_counts_toward_block_gas(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Verify the calldata floor is charged to the block's execution gas.

    With a STOP callee and large zero-byte calldata the floor exceeds
    the actual execution gas charge, so the transaction contributes the
    floor (not the pre-floor charge) to the header gas_used.
    """
    calldata = b"\x00" * 1024
    floor = fork.transaction_data_floor_cost_calculator()(data=calldata)
    charge = fork.transaction_intrinsic_cost_calculator()(
        calldata=calldata,
        return_cost_deducted_prior_execution=True,
    )
    assert charge < floor, "calldata floor must bind"

    contract = pre.deploy_contract(code=Op.STOP)

    tx = Transaction(
        to=contract,
        data=calldata,
        sender=pre.fund_eoa(),
        expected_receipt=TransactionReceipt(cumulative_gas_used=floor),
    )
    state_test(
        pre=pre,
        post={},
        tx=tx,
        blockchain_test_header_verify=Header(gas_used=floor),
    )


@pytest.mark.valid_from("EIP8037")
def test_calldata_floor_not_discounted_by_state_gas(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Verify state gas spending does not discount the block-level floor.

    Calldata is sized so the floor sits between the transaction's
    execution-gas portion and its total gas used
    (``tx_execution < floor < tx_execution + state``). The sender's bill is
    the pre-floor total, yet the block's execution dimension must still
    charge the full floor: the floor is compared against the execution
    portion alone, so state gas cannot absorb it. An implementation
    that instead floors the transaction total before deducting state
    gas (or skips the floor entirely) would report the state dimension
    in the header; the correct header gas_used is the floor.
    """
    storage = Storage()
    code = Op.SSTORE(storage.store_next(1), 1, new_value=1)
    state_cost = code.state_cost(fork)
    execution_cost = code.execution_cost(fork)
    floor_cost = fork.transaction_data_floor_cost_calculator()

    # Smallest zero-byte calldata whose floor exceeds the state
    # dimension; the floor then also dominates the header.
    size = 0
    while floor_cost(data=b"\x00" * size) <= state_cost:
        size += 32
    calldata = b"\x00" * size
    floor = floor_cost(data=calldata)

    intrinsic = fork.transaction_intrinsic_cost_calculator()(
        calldata=calldata,
        return_cost_deducted_prior_execution=True,
    )
    tx_execution = intrinsic + execution_cost
    tx_total = tx_execution + state_cost
    assert tx_execution < floor < tx_total, (
        "floor must bind the execution portion but not the total"
    )

    contract = pre.deploy_contract(code=code)

    tx = Transaction(
        to=contract,
        data=calldata,
        state_gas_reservoir=state_cost,
        sender=pre.fund_eoa(),
        expected_receipt=TransactionReceipt(cumulative_gas_used=tx_total),
    )
    state_test(
        pre=pre,
        post={contract: Account(storage=storage)},
        tx=tx,
        blockchain_test_header_verify=Header(gas_used=floor),
    )
