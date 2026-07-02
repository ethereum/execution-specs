"""
Test EIP-7623 calldata floor interaction with EIP-8037 state gas.

The calldata floor applies to the regular gas dimension only. It
does not affect state gas. Block gas accounting uses tx_regular_gas
(without the floor) for regular gas and tracks state gas separately.

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
    regular gas, but state gas for SSTORE is charged independently.
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
    Test calldata floor applies only to regular gas dimension.

    The calldata floor inflates regular gas used for block accounting
    but does not affect the state gas dimension. A transaction with
    high calldata and no state operations should succeed even when
    the floor exceeds actual execution gas.
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

    Even when calldata floor > actual regular gas used, state gas for
    SSTORE is charged normally from the reservoir or gas_left.
    """
    sstore_state_gas = Op.SSTORE(new_value=1).state_cost(fork)

    storage = Storage()
    contract = pre.deploy_contract(
        code=Op.SSTORE(storage.store_next(1), 1),
    )

    # Large calldata so floor dominates regular gas
    calldata = b"\x01" * 1024

    tx = Transaction(
        to=contract,
        data=calldata,
        state_gas_reservoir=sstore_state_gas,
        sender=pre.fund_eoa(),
    )

    post = {contract: Account(storage=storage)}
    state_test(pre=pre, post=post, tx=tx)


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

    EIP-8037 caps ``max(intrinsic_regular, calldata_floor)`` at
    ``TX_MAX_GAS_LIMIT``. When the EIP-7976 calldata floor crosses the cap
    the transaction must be rejected even though the regular intrinsic gas
    is within the cap. For the rejection case ``gas_limit`` is set above the
    floor so the sufficiency check ``max(intrinsic_total, floor) <= tx.gas``
    passes and the cap is the only reason for rejection — the exact shape a
    client with the sufficiency gate but no cap gate would wrongly execute.

    at_cap: tightest calldata floor that fits within the cap —
    transaction accepted.
    exceeds_cap: one byte more tips the floor over the cap —
    transaction rejected.
    """
    gas_costs = fork.gas_costs()
    cap = fork.transaction_gas_limit_cap()
    assert cap is not None
    floor_cost = fork.transaction_data_floor_cost_calculator()

    floor_token = gas_costs.TX_DATA_TOKEN_FLOOR
    tx_base = gas_costs.TX_BASE
    max_tokens = (cap - tx_base) // floor_token

    if fork.is_eip_enabled(7976):
        # EIP-7976: all bytes contribute 4 floor tokens regardless of
        # value, so the token count is len(data) * 4.
        tokens_per_byte = 4
        max_bytes = max_tokens // tokens_per_byte
        if exceeds_cap:
            max_bytes += 1
        calldata = b"\x01" * max_bytes
    else:
        # EIP-7623: non-zero bytes contribute 4 tokens, zero bytes 1.
        tokens_per_nonzero = 4
        nonzero_bytes = max_tokens // tokens_per_nonzero
        zero_bytes = max_tokens - nonzero_bytes * tokens_per_nonzero
        if exceeds_cap:
            zero_bytes += 1
        calldata = b"\x01" * nonzero_bytes + b"\x00" * zero_bytes

    contract = pre.deploy_contract(Op.STOP)
    floor = floor_cost(data=calldata)

    if exceeds_cap:
        intrinsic = fork.transaction_intrinsic_cost_calculator()
        regular = intrinsic(
            calldata=calldata,
            return_cost_deducted_prior_execution=True,
        )
        assert floor > cap, "calldata floor must exceed the cap"
        assert regular < cap, "regular intrinsic must stay below the cap"
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
    reservoir. The floor feeds only the receipt; the block accounts
    regular and state separately, so the header gas_used is the state
    dimension (not the floor).
    """
    storage = Storage()
    code = Op.SSTORE(storage.store_next(1), 1, new_value=1)
    state_cost = code.state_cost(fork)
    regular_cost = code.regular_cost(fork)

    # Sized so the floor binds while block-regular stays under storage_set.
    calldata = b"\x00" * 5000
    floor = fork.transaction_data_floor_cost_calculator()(data=calldata)
    assert floor > regular_cost + state_cost, (
        "calldata floor must exceed execution cost"
    )

    contract = pre.deploy_contract(code=code)

    tx = Transaction(
        to=contract,
        data=calldata,
        state_gas_reservoir=state_cost,
        sender=pre.fund_eoa(),
        expected_receipt=TransactionReceipt(gas_used=floor),
    )
    state_test(
        pre=pre,
        post={contract: Account(storage=storage)},
        tx=tx,
        blockchain_test_header_verify=Header(gas_used=state_cost),
    )
