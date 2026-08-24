"""
Test the EIP-8368 recalibrated cost per state byte.

EIP-8368 re-derives EIP-8037's `cost_per_state_byte` for a new
reference block gas limit, leaving every other EIP-8037 mechanism
unchanged. Each test bills a state creation primitive against the
value derived in `spec.py` and pins the exact charge.

Tests for [EIP-8368: CPSB Recalibration for New Gas Limit]
(https://eips.ethereum.org/EIPS/eip-8368).
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Fork,
    Op,
    StateTestFiller,
    Transaction,
    TransactionReceipt,
    compute_create_address,
)
from execution_testing.checklists import EIPChecklist

from .spec import Spec, ref_spec_8368

REFERENCE_SPEC_GIT_PATH = ref_spec_8368.git_path
REFERENCE_SPEC_VERSION = ref_spec_8368.version


@EIPChecklist.GasCostChanges.Test.GasUpdatesMeasurement()
@EIPChecklist.GasCostChanges.Test.OutOfGas()
@pytest.mark.parametrize(
    "gas_delta",
    [pytest.param(0, id="exact_fit"), pytest.param(-1, id="one_short")],
)
@pytest.mark.valid_from("EIP8368")
def test_storage_set_exact_fit_boundary(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_delta: int,
) -> None:
    """
    Pin a fresh storage set at the recalibrated cost per state byte:
    the transaction fits exactly at the derived charge and runs out of
    gas one unit short of it.
    """
    assert fork.cost_per_state_byte() == Spec.COST_PER_STATE_BYTE, (
        "fork cost per state byte does not match the EIP-8368 derivation"
    )

    code = Op.SSTORE(0, 1)
    contract = pre.deploy_contract(code=code)

    intrinsic = fork.transaction_intrinsic_cost_calculator()()
    exact_fit_gas = (
        intrinsic
        + code.execution_cost(fork)
        + Spec.STATE_BYTES_PER_STORAGE_SET * Spec.COST_PER_STATE_BYTE
    )
    gas_limit = exact_fit_gas + gas_delta

    if gas_delta == 0:
        receipt_gas = exact_fit_gas
        post = {contract: Account(storage={0: 1})}
    else:
        # The spilled state charge is refilled into gas_left and burnt
        # by the halt, billing the whole gas limit.
        receipt_gas = gas_limit
        post = {contract: Account(storage={0: 0})}

    tx = Transaction(
        to=contract,
        gas_limit=gas_limit,
        sender=pre.fund_eoa(),
        expected_receipt=TransactionReceipt(cumulative_gas_used=receipt_gas),
    )
    state_test(pre=pre, post=post, tx=tx)


@EIPChecklist.GasCostChanges.Test.GasUpdatesMeasurement()
@pytest.mark.valid_from("EIP8368")
def test_new_account_charge(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Pin the account footprint of a value-bearing CALL to a fresh
    address at the recalibrated cost per state byte via the receipt.
    """
    target = pre.fund_eoa(amount=0)

    code = (
        Op.POP(
            Op.CALL(
                gas=0,
                address=target,
                value=1,
                value_transfer=True,
                account_new=True,
            )
        )
        + Op.STOP
    )
    caller = pre.deploy_contract(code=code, balance=1)

    intrinsic = fork.transaction_intrinsic_cost_calculator()()
    # The codeless callee returns its whole unused stipend, which
    # `execution_cost` bills gross.
    expected_gas = (
        intrinsic
        + code.execution_cost(fork)
        - fork.call_value_stipend()
        + Spec.STATE_BYTES_PER_NEW_ACCOUNT * Spec.COST_PER_STATE_BYTE
    )

    tx = Transaction(
        to=caller,
        gas_limit=expected_gas + 20_000,
        sender=pre.fund_eoa(),
        expected_receipt=TransactionReceipt(cumulative_gas_used=expected_gas),
    )
    state_test(pre=pre, post={target: Account(balance=1)}, tx=tx)


@EIPChecklist.GasCostChanges.Test.GasUpdatesMeasurement()
@pytest.mark.valid_from("EIP8368")
def test_code_deposit_charge(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Pin a contract creation at the recalibrated cost per state byte:
    the created account footprint plus one state byte per deposited
    code byte, via the receipt.
    """
    code_size = 256
    init_code = Op.RETURN(
        0, code_size, code_deposit_size=code_size, new_memory_size=code_size
    )

    intrinsic_execution = fork.transaction_intrinsic_cost_calculator()(
        calldata=bytes(init_code),
        contract_creation=True,
        return_cost_deducted_prior_execution=True,
    )
    expected_gas = (
        intrinsic_execution
        + init_code.execution_cost(fork)
        + (Spec.STATE_BYTES_PER_NEW_ACCOUNT + code_size)
        * Spec.COST_PER_STATE_BYTE
    )

    sender = pre.fund_eoa()
    created = compute_create_address(address=sender, nonce=0)

    tx = Transaction(
        to=None,
        data=init_code,
        gas_limit=expected_gas + 20_000,
        sender=sender,
        expected_receipt=TransactionReceipt(cumulative_gas_used=expected_gas),
    )
    state_test(
        pre=pre,
        post={created: Account(code=b"\x00" * code_size)},
        tx=tx,
    )
