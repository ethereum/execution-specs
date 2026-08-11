"""
Verify a contract-creation transaction whose init code runs out of gas (or
halts on invalid code) leaves no account behind, while a sufficient budget
creates it.

Ported from:
state_tests/stInitCodeTest/OutOfGasContractCreationFiller.json

@manually-enhanced: Do not overwrite. The two budgets sit one gas apart on
a boundary derived entirely from the fork: the intrinsic actually deducted
before execution, the created account's top-frame state gas, the init
code's metadata-priced cost, and the headroom EIP-2200's minimum-gas gate
demands of the last store. The success post pins the final storage value,
not just the nonce.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytecode,
    Fork,
    StateTestFiller,
    Transaction,
    compute_create_address,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

TX_VALUE = 1
MAX_VALUE_SSTORED = 6


def storage_writes_initcode() -> Bytecode:
    """Return init code that sets one slot, then rewrites it while dirty."""
    code = Op.SSTORE(
        key=0x1, value=0x1, key_warm=False, original_value=0, new_value=1
    )
    for value in range(2, MAX_VALUE_SSTORED + 1):
        code += Op.SSTORE(
            key=0x1,
            value=value,
            key_warm=True,
            original_value=0,
            current_value=value - 1,
            new_value=value,
        )
    return code


def stack_underflow_initcode() -> Bytecode:
    """The ported junk init code: CALLCODE underflows the stack."""
    return (
        Op.PUSH1[0xA]
        + Op.CODECOPY(dest_offset=0x0, offset=0xC, size=Op.DUP1)
        + Op.PUSH1[0x0]
        + Op.CALLCODE
        + Op.STOP
        + Op.PUSH1[0x1]
        + Op.PUSH1[0x0]
        + Op.BYTE(Op.DUP2, Op.CALLDATALOAD(offset=Op.DUP1))
        + Op.DUP2
        + Op.STOP
    )


@pytest.mark.ported_from(
    ["state_tests/stInitCodeTest/OutOfGasContractCreationFiller.json"],
)
@pytest.mark.valid_from("Berlin")
@pytest.mark.parametrize(
    "invalid_initcode",
    [
        pytest.param(True, id="invalid_initcode"),
        pytest.param(False, id="valid_initcode"),
    ],
)
@pytest.mark.parametrize(
    "enough_gas",
    [
        pytest.param(False, id="insufficient_gas"),
        pytest.param(True, id="sufficient_gas"),
    ],
)
def test_out_of_gas_contract_creation(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    invalid_initcode: bool,
    enough_gas: bool,
) -> None:
    """An under-budgeted or invalid init code creates no account."""
    if invalid_initcode:
        initcode = stack_underflow_initcode()
    else:
        initcode = storage_writes_initcode()

    # EIP-8037 charges the created account's state gas to the creation
    # transaction's top frame. The intrinsic is asked for what is deducted
    # before execution, since the default folds in the calldata floor, which
    # is only compared against once the transaction is already done.
    overhead = fork.transaction_intrinsic_cost_calculator()(
        calldata=initcode,
        contract_creation=True,
        sends_value=TX_VALUE > 0,
        return_cost_deducted_prior_execution=True,
    ) + fork.transaction_top_frame_state_gas(
        contract_creation=True, sends_value=TX_VALUE > 0
    )
    initcode_cost = storage_writes_initcode().gas_cost(fork)
    # EIP-2200 halts any SSTORE that runs with `CALL_STIPEND` gas or less
    # still available -- a gate, not a charge, so it is not part of
    # `gas_cost`. The init code's last store is the one that runs closest to
    # empty, so the budget has to hold more than the stipend at that point:
    # its own charge plus one gas over. A bare SSTORE with no operands
    # prices that charge on its own.
    last_store_charge = Op.SSTORE(
        key_warm=True,
        original_value=0,
        current_value=MAX_VALUE_SSTORED - 1,
        new_value=MAX_VALUE_SSTORED,
    ).gas_cost(fork)
    stipend_headroom = fork.gas_costs().CALL_STIPEND - last_store_charge + 1
    gas_limit = overhead + initcode_cost + stipend_headroom
    if not enough_gas:
        gas_limit -= 1

    sender = pre.fund_eoa()
    tx = Transaction(
        sender=sender,
        to=None,
        data=initcode,
        gas_limit=gas_limit,
        value=TX_VALUE,
    )

    created = compute_create_address(address=sender, nonce=0)
    if enough_gas and not invalid_initcode:
        created_account: Account | None = Account(
            nonce=1, code=b"", storage={1: MAX_VALUE_SSTORED}, balance=1
        )
    else:
        # OOG / invalid init code: the creation is rolled back entirely.
        created_account = Account.NONEXISTENT
    post = {
        sender: Account(nonce=1),
        created: created_account,
    }

    state_test(pre=pre, post=post, tx=tx)
