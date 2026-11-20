"""
CALLCODE or DELEGATECALL inside contract init code.

Ported from:
state_tests/stCallCodes/callcodeInInitcodeToEmptyContractFiller.json
state_tests/stCallCodes/callcodeInInitcodeToExistingContractFiller.json
state_tests/stCallCodes/callcodeInInitcodeToExisContractWithVTransferNEMoneyFiller.json
state_tests/stDelegatecallTestHomestead/delegatecallInInitcodeToEmptyContractFiller.json
state_tests/stDelegatecallTestHomestead/delegatecallInInitcodeToExistingContractFiller.json
state_tests/stDelegatecallTestHomestead/delegatecallInInitcodeToExistingContractOOGFiller.json

@manually-enhanced: Do not overwrite. Six fillers merged, addresses unpinned.
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Fork,
    StateTestFiller,
    Transaction,
    compute_create_address,
)
from execution_testing import Macros as Om
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

CREATOR_BALANCE = 10
# A gas ask above anything available; EIP-150 caps it to 63/64.
OVERSIZED_GAS_ASK = 2**32

CALL_RESULT_SLOT = 0x1
CALLEE_WRITE_SLOT = 0x2
CALLEE_CALLER_SLOT = 0xB
INITCODE_CALLER_SLOT = 0xC
INITCODE_DONE_SLOT = 0xD
CALLEE_VALUE_SLOT = 0xE


@pytest.mark.ported_from(
    [
        "state_tests/stCallCodes/callcodeInInitcodeToEmptyContractFiller.json",  # noqa: E501
        "state_tests/stCallCodes/callcodeInInitcodeToExistingContractFiller.json",  # noqa: E501
        "state_tests/stCallCodes/callcodeInInitcodeToExisContractWithVTransferNEMoneyFiller.json",  # noqa: E501
        "state_tests/stDelegatecallTestHomestead/delegatecallInInitcodeToEmptyContractFiller.json",  # noqa: E501
        "state_tests/stDelegatecallTestHomestead/delegatecallInInitcodeToExistingContractFiller.json",  # noqa: E501
        "state_tests/stDelegatecallTestHomestead/delegatecallInInitcodeToExistingContractOOGFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("TangerineWhistle")
@pytest.mark.parametrize(
    "opcode, callee_exists, endowment, call_value, gas_ask",
    [
        pytest.param(
            Op.CALLCODE,
            False,
            1,
            1,
            None,
            id="callcode_in_initcode_to_empty_contract",
        ),
        pytest.param(
            Op.CALLCODE,
            True,
            1,
            1,
            None,
            id="callcode_in_initcode_to_existing_contract",
        ),
        pytest.param(
            Op.CALLCODE,
            True,
            0,
            0,
            None,
            id="callcode_in_initcode_to_existing_contract_zero_value",
        ),
        pytest.param(
            Op.CALLCODE,
            True,
            0,
            1,
            None,
            id="callcode_in_initcode_to_exis_contract_with_v_transfer_ne_money",
        ),
        pytest.param(
            Op.DELEGATECALL,
            False,
            1,
            0,
            None,
            id="delegatecall_in_initcode_to_empty_contract",
        ),
        pytest.param(
            Op.DELEGATECALL,
            True,
            1,
            0,
            None,
            id="delegatecall_in_initcode_to_existing_contract",
        ),
        pytest.param(
            Op.DELEGATECALL,
            True,
            5,
            0,
            OVERSIZED_GAS_ASK,
            id="delegatecall_in_initcode_to_existing_contract_oog",
        ),
    ],
)
@pytest.mark.with_all_create_opcodes
def test_callcode_in_initcode(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    opcode: Op,
    callee_exists: bool,
    endowment: int,
    call_value: int,
    gas_ask: int | None,
    create_opcode: Op,
) -> None:
    """
    Create a contract whose init code calls into an empty or existing one.

    The callee's code runs in the created account's context, so its
    storage writes land there and its own storage stays untouched.
    CALLCODE fails when its value exceeds the created account's
    endowment.
    """
    callee: Address
    if callee_exists:
        callee = pre.deploy_contract(
            code=Op.SSTORE(CALLEE_WRITE_SLOT, 1)
            + Op.SSTORE(CALLEE_CALLER_SLOT, Op.CALLER)
            + Op.SSTORE(CALLEE_VALUE_SLOT, Op.CALLVALUE)
            + Op.STOP,
        )
    else:
        callee = pre.nonexistent_account()

    gas = Op.GAS if gas_ask is None else gas_ask
    if opcode == Op.CALLCODE:
        call = Op.CALLCODE(gas=gas, address=callee, value=call_value)
        call_succeeds = endowment >= call_value
        callee_value = call_value
    else:
        call = Op.DELEGATECALL(gas=gas, address=callee)
        call_succeeds = True
        callee_value = endowment

    initcode = (
        Op.SSTORE(CALL_RESULT_SLOT, call)
        + Op.SSTORE(INITCODE_CALLER_SLOT, Op.CALLER)
        + Op.SSTORE(INITCODE_DONE_SLOT, 1)
        + Op.STOP
    )
    creator = pre.deploy_contract(
        code=Om.MSTORE(initcode, 0)
        + create_opcode(value=endowment, offset=0, size=len(initcode))
        + Op.STOP,
        balance=CREATOR_BALANCE,
    )
    created = compute_create_address(
        address=creator, nonce=1, initcode=initcode, opcode=create_opcode
    )

    tx = Transaction(
        sender=pre.fund_eoa(),
        to=creator,
        protected=fork.supports_protected_txs(),
    )

    storage = {
        CALL_RESULT_SLOT: int(call_succeeds),
        INITCODE_CALLER_SLOT: creator,
        INITCODE_DONE_SLOT: 1,
    }
    if call_succeeds and callee_exists:
        storage[CALLEE_WRITE_SLOT] = 1
        storage[CALLEE_CALLER_SLOT] = (
            created if opcode == Op.CALLCODE else creator
        )
        storage[CALLEE_VALUE_SLOT] = callee_value
    post = {
        created: Account(
            code=b"",
            nonce=1 if fork.is_eip_enabled(161) else 0,
            balance=endowment,
            storage=storage,
        ),
        creator: Account(
            nonce=2, balance=CREATOR_BALANCE - endowment, storage={}
        ),
    }
    if callee_exists:
        post[callee] = Account(storage={}, balance=0)

    state_test(pre=pre, post=post, tx=tx)
