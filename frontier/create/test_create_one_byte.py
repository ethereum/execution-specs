"""
The test calls CREATE in a loop deploying 1-byte contracts with all possible byte values,
records in storage the values that failed to deploy.
"""

import pytest

from ethereum_test_forks import Byzantium, Fork, London
from ethereum_test_tools import (
    Account,
    Address,
    Alloc,
    Bytecode,
    Environment,
    StateTestFiller,
    Storage,
    Transaction,
)
from ethereum_test_tools import Opcodes as Op
from ethereum_test_types import compute_create_address


@pytest.mark.valid_from("Frontier")
@pytest.mark.with_all_create_opcodes
def test_create_one_byte(
    state_test: StateTestFiller,
    fork: Fork,
    pre: Alloc,
    create_opcode: Op,
):
    """Run create deploys with single bytes for each byte."""
    initcode: dict[int, Bytecode] = {}
    for byte in range(256):
        initcode[byte] = Op.MSTORE8(0, byte) + Op.RETURN(0, 1)
    initcode_length = 10

    sender = pre.fund_eoa()
    expect_post = Storage()

    # make a subcontract that deploys code, because deploy 0xef eats ALL gas
    create_contract = pre.deploy_contract(
        code=Op.MSTORE(0, Op.CALLDATALOAD(0))
        + Op.MSTORE(32, create_opcode(offset=32 - initcode_length, salt=0, size=initcode_length))
        + Op.RETURN(32, 32)
    )
    code = pre.deploy_contract(
        nonce=1,
        code=Op.MSTORE(0, Op.PUSH32(bytes(initcode[0])))
        + sum(
            [
                Op.MSTORE8(23, opcode)  # correct the deploy byte
                + Op.CALL(
                    gas=50_000,
                    address=create_contract,
                    args_size=32,
                    ret_offset=32,
                    ret_size=32,
                )
                + Op.POP  # remove call result from stack for vm trace files
                + Op.SSTORE(
                    opcode,
                    Op.MLOAD(32),
                )
                for opcode, _ in initcode.items()
            ],
        )
        + Op.SSTORE(256, 1),
    )

    created_accounts: dict[int, Address] = {}
    for opcode, opcode_init in initcode.items():
        ef_exception = opcode == 239 and fork >= London
        created_accounts[opcode] = compute_create_address(
            address=create_contract,
            salt=0,
            nonce=opcode + 1,
            initcode=opcode_init,
            opcode=create_opcode,
        )
        if not ef_exception:
            expect_post[opcode] = created_accounts[opcode]
    expect_post[256] = 1

    tx = Transaction(
        gas_limit=14_000_000,
        to=code,
        data=b"",
        nonce=0,
        sender=sender,
        protected=fork >= Byzantium,
    )

    post = {
        code: Account(storage=expect_post),
    }
    for opcode, _ in initcode.items():
        ef_exception = opcode == 239 and fork >= London
        if not ef_exception:
            post[created_accounts[opcode]] = Account(code=bytes.fromhex(f"{opcode:02x}"))

    state_test(env=Environment(), pre=pre, post=post, tx=tx)
