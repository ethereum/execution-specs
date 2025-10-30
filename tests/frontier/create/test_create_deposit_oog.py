"""
The test CREATE's behavior when running out of gas for code deposit.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Environment,
    Fork,
    Op,
    StateTestFiller,
    Storage,
    Transaction,
    compute_create_address,
)
from execution_testing.forks import Byzantium, Frontier, Homestead

SLOT_CREATE_RESULT = 1
SLOT_CREATE_RESULT_PRE = 0xDEADBEEF


@pytest.mark.valid_from("Frontier")
@pytest.mark.with_all_create_opcodes
def test_create_deposit_oog(
    state_test: StateTestFiller,
    fork: Fork,
    pre: Alloc,
    create_opcode: Op,
) -> None:
    """Run create deploys with a lot of deposited code."""
    deposited_len = 10_000
    initcode = Op.RETURN(0, deposited_len)
    tx_gas_limit = 1_000_000
    assert tx_gas_limit < deposited_len * fork.gas_costs().G_CODE_DEPOSIT_BYTE

    sender = pre.fund_eoa()
    expect_post = Storage()

    code = pre.deploy_contract(
        code=Op.MSTORE(0, Op.PUSH32(bytes(initcode)))
        + Op.SSTORE(
            SLOT_CREATE_RESULT,
            create_opcode(offset=32 - len(initcode), size=len(initcode)),
        )
        + Op.STOP,
        nonce=1,
        storage={SLOT_CREATE_RESULT: SLOT_CREATE_RESULT_PRE},
    )

    new_address = compute_create_address(
        address=code, nonce=1, initcode=initcode, salt=0, opcode=create_opcode
    )

    if fork == Frontier:
        expect_post[SLOT_CREATE_RESULT] = new_address
    elif fork == Homestead:
        # Before the introduction of the 63/64th rule there is no
        # gas left for SSTOREing the return value.
        expect_post[SLOT_CREATE_RESULT] = SLOT_CREATE_RESULT_PRE
    else:
        expect_post[SLOT_CREATE_RESULT] = 0

    tx = Transaction(
        gas_limit=tx_gas_limit,
        to=code,
        sender=sender,
        protected=fork >= Byzantium,
    )

    post = {
        code: Account(storage=expect_post),
        new_address: Account(code=b"", nonce=0) if fork == Frontier else None,
    }
    state_test(env=Environment(), pre=pre, post=post, tx=tx)
