"""
Verify a contract-creation transaction whose init code runs out of gas (or
halts on invalid code) leaves no account behind, while a sufficient budget
creates it.

Ported from:
state_tests/stInitCodeTest/OutOfGasContractCreationFiller.json

@manually-enhanced: Do not overwrite. Both transaction budgets are derived
from the fork (intrinsic + the created account's top-frame state gas + the
init code's metadata-priced cost), so the insufficient arm keeps running
out mid-init-code and the sufficient arm keeps succeeding on every fork;
the success post pins the final storage value, not just the nonce.
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


def storage_writes_initcode() -> Bytecode:
    """Six stores to one slot: one cold set, then five dirty warm writes."""
    code = Op.SSTORE(
        key=0x1, value=0x1, key_warm=False, original_value=0, new_value=1
    )
    for value in range(2, 7):
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
        pytest.param(True, id="d0"),
        pytest.param(False, id="d1"),
    ],
)
@pytest.mark.parametrize(
    "enough_gas",
    [
        pytest.param(False, id="g0"),
        pytest.param(True, id="g1"),
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

    # The insufficient budget runs out midway through the init code; the
    # sufficient one covers it with margin. EIP-8037 charges the created
    # account's state gas to the creation transaction's top frame.
    overhead = fork.transaction_intrinsic_cost_calculator()(
        calldata=initcode,
        contract_creation=True,
    ) + fork.transaction_top_frame_state_gas(contract_creation=True)
    # The sufficient margin must exceed the EIP-2200 stipend (2300), or
    # the final SSTOREs of the init code fail their minimum-gas check.
    initcode_cost = storage_writes_initcode().gas_cost(fork)
    gas_limit = overhead + (
        initcode_cost + 5_000 if enough_gas else initcode_cost // 2
    )

    sender = pre.fund_eoa()
    tx = Transaction(
        sender=sender,
        to=None,
        data=initcode,
        gas_limit=gas_limit,
        value=1,
    )

    created = compute_create_address(address=sender, nonce=0)
    if enough_gas and not invalid_initcode:
        created_account: Account | type = Account(
            nonce=1, code=b"", storage={1: 6}, balance=1
        )
    else:
        # OOG / invalid init code: the creation is rolled back entirely.
        created_account = Account.NONEXISTENT
    post = {
        sender: Account(nonce=1),
        created: created_account,
    }

    state_test(pre=pre, post=post, tx=tx)
