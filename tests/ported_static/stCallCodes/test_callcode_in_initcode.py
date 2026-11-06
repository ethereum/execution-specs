"""
CALLCODE or DELEGATECALL inside contract init code.

Ported from:
state_tests/stCallCodes/callcodeInInitcodeToEmptyContractFiller.json
state_tests/stCallCodes/callcodeInInitcodeToExistingContractFiller.json
state_tests/stCallCodes/callcodeInInitcodeToExisContractWithVTransferNEMoneyFiller.json
state_tests/stDelegatecallTestHomestead/delegatecallInInitcodeToEmptyContractFiller.json
state_tests/stDelegatecallTestHomestead/delegatecallInInitcodeToExistingContractFiller.json
state_tests/stDelegatecallTestHomestead/delegatecallInInitcodeToExistingContractOOGFiller.json
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    StateTestFiller,
    Transaction,
    compute_create2_address,
    compute_create_address,
)
from execution_testing import Macros as Om
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

SALT = 0
# A gas ask above anything available; EIP-150 caps it to 63/64.
OVERSIZED_GAS_ASK = 2**32


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
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "opcode, callee_exists, endowment, gas_ask",
    [
        pytest.param(
            Op.CALLCODE,
            False,
            0,
            None,
            id="callcode_in_initcode_to_empty_contract",
        ),
        pytest.param(
            Op.CALLCODE,
            True,
            1,
            None,
            id="callcode_in_initcode_to_existing_contract",
        ),
        pytest.param(
            Op.CALLCODE,
            True,
            0,
            None,
            id="callcode_in_initcode_to_exis_contract_with_v_transfer_ne_money",
        ),
        pytest.param(
            Op.DELEGATECALL,
            False,
            1,
            None,
            id="delegatecall_in_initcode_to_empty_contract",
        ),
        pytest.param(
            Op.DELEGATECALL,
            True,
            1,
            None,
            id="delegatecall_in_initcode_to_existing_contract",
        ),
        pytest.param(
            Op.DELEGATECALL,
            True,
            5,
            OVERSIZED_GAS_ASK,
            id="delegatecall_in_initcode_to_existing_contract_oog",
        ),
    ],
)
@pytest.mark.parametrize(
    "create_opcode", [Op.CREATE, Op.CREATE2], ids=["create", "create2"]
)
def test_callcode_in_initcode(
    state_test: StateTestFiller,
    pre: Alloc,
    opcode: Op,
    callee_exists: bool,
    endowment: int,
    gas_ask: int | None,
    create_opcode: Op,
) -> None:
    """
    Create a contract whose init code calls into an empty or existing one.

    CALLCODE sends 1 wei, which fails when the new contract was created
    without an endowment.
    """
    sender = pre.fund_eoa()

    callee: Address
    if callee_exists:
        # Source: lll
        # { (SSTORE 2 1) [[ 11 ]] (CALLER) }
        callee = pre.deploy_contract(
            code=Op.SSTORE(0x2, 1) + Op.SSTORE(0xB, Op.CALLER) + Op.STOP,
        )
    else:
        callee = pre.nonexistent_account()

    gas = Op.GAS if gas_ask is None else gas_ask
    if opcode == Op.CALLCODE:
        call = Op.CALLCODE(gas=gas, address=callee, value=1)
        call_succeeds = endowment >= 1
    else:
        call = Op.DELEGATECALL(gas=gas, address=callee)
        call_succeeds = True

    # Source: lll
    # (lll (seq  [[1]] (CALLCODE 50000 0x1000000000000000000000000000000000000001 1 0 0 0 0)) 0)  # noqa: E501
    initcode = (
        Op.SSTORE(0x1, call)
        + Op.SSTORE(0xC, Op.CALLER)
        + Op.SSTORE(0xD, 1)
        + Op.STOP
    )
    if create_opcode == Op.CREATE:
        create = Op.CREATE(endowment, 0, len(initcode))
    else:
        create = Op.CREATE2(endowment, 0, len(initcode), SALT)
    creator = pre.deploy_contract(
        code=Om.MSTORE(initcode, 0) + create + Op.STOP,
        balance=10,
    )
    if create_opcode == Op.CREATE:
        created = compute_create_address(address=creator, nonce=1)
    else:
        created = compute_create2_address(creator, SALT, initcode)

    tx = Transaction(sender=sender, to=creator)

    storage = {0x1: int(call_succeeds), 0xC: creator, 0xD: 1}
    if call_succeeds and callee_exists:
        storage[0x2] = 1
        storage[0xB] = created if opcode == Op.CALLCODE else creator
    post = {
        created: Account(code=b"", storage=storage, balance=endowment),
        creator: Account(balance=10 - endowment),
    }
    if callee_exists:
        post[callee] = Account(storage={}, balance=0)

    state_test(pre=pre, post=post, tx=tx)
