"""
Test CREATE's behavior when running out of gas for code deposit.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Fork,
    Op,
    StateTestFiller,
    Transaction,
    compute_create_address,
)
from execution_testing.forks import Frontier, TangerineWhistle

SLOT_CREATE_RESULT = 1
SLOT_CREATE_RESULT_PRE = 0xDEADBEEF


@pytest.mark.valid_from("Frontier")
@pytest.mark.parametrize("enough_gas", [True, False])
@pytest.mark.with_all_create_opcodes
def test_create_deposit_oog(
    state_test: StateTestFiller,
    fork: Fork,
    pre: Alloc,
    create_opcode: Op,
    enough_gas: bool,
) -> None:
    """Run create deploys with a lot of deposited code."""
    deposited_len = 32
    expand_memory_code = Op.MSTORE8(
        # Expand memory first
        offset=deposited_len - 1,
        value=0,
        new_memory_size=deposited_len,  # For gas accounting
    )
    return_code = Op.RETURN(
        offset=0,
        size=deposited_len,
        code_deposit_size=deposited_len,  # For gas accounting
    )
    initcode = expand_memory_code + return_code

    sender = pre.fund_eoa()

    factory_memory_expansion_code = Op.MSTORE(
        0,
        Op.PUSH32(bytes(initcode)),
        new_memory_size=32,  # For gas accounting
    )
    factory_create_code = create_opcode(
        offset=32 - len(initcode),
        size=len(initcode),
        init_code_size=len(initcode),  # For gas accounting
    )
    factory_code = (
        factory_memory_expansion_code + factory_create_code + Op.STOP
    )

    factory_address = pre.deploy_contract(code=factory_code)
    create_gas = return_code.gas_cost(fork) + expand_memory_code.gas_cost(fork)
    if not enough_gas:
        create_gas -= 1
    if fork >= TangerineWhistle:
        # Increment the gas for the 63/64 rule
        create_gas = (create_gas * 64) // 63
    call_gas = create_gas + factory_code.gas_cost(fork)
    caller_address = pre.deploy_contract(
        code=Op.CALL(
            gas=call_gas, address=factory_address, ret_offset=0, ret_size=32
        )
        + Op.STOP,
    )

    new_address = compute_create_address(
        address=factory_address,
        nonce=1,
        initcode=initcode,
        salt=0,
        opcode=create_opcode,
    )

    tx = Transaction(
        gas_limit=10_000_000,
        to=caller_address,
        sender=sender,
        protected=fork.supports_protected_txs(),
    )

    created_account: Account | None = Account(code=b"\x00" * deposited_len)
    if not enough_gas:
        if fork > Frontier:
            created_account = None
        else:
            # At Frontier, OOG on return yields an empty account.
            created_account = Account()

    post = {
        factory_address: Account(nonce=2),
        caller_address: Account(nonce=1),
        new_address: created_account,
    }
    state_test(pre=pre, post=post, tx=tx)
