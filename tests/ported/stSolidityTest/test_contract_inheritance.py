"""
Ported from:
tests/static/state_tests/stSolidityTest/ContractInheritanceFiller.json

contract code:
    push29 0x0100000000000000000000000000000000000000000000000000000000
    push1 0x00
    calldataload
    div
    push4 0x3e0bca3b
    dup2
    eq
    push2 0x39
    jumpi
    dup1
    push4 0xc0406226
    eq
    push2 0xa8
    jumpi
    stop
    jumpdest
    push2 0xb5
    jumpdest
    push1 0x01
    push1 0x00
    ... (203 more instructions)
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Environment,
    Hash,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["tests/static/state_tests/stSolidityTest/ContractInheritanceFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Prague")
@pytest.mark.pre_alloc_mutable
def test_contract_inheritance(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0x73c241c3bc4fdf83b6ff3ae73735fddf7c9d711d")
    contract = Address("0x3809b123c157b2d0d3b998255f35b5f8b8ae4789")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=9223372036854775807,
    )

    pre[contract] = Account(
        balance=0x186a0,
        nonce=0,
        code=(
        Op.PUSH29[0x100000000000000000000000000000000000000000000000000000000]
        + Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.DIV + Op.PUSH4[0x3e0bca3b] + Op.DUP2
        + Op.EQ + Op.PUSH2[0x39] + Op.JUMPI + Op.DUP1 + Op.PUSH4[0xc0406226] + Op.EQ
        + Op.PUSH2[0xa8] + Op.JUMPI + Op.STOP + Op.JUMPDEST + Op.PUSH2[0xb5]
        + Op.JUMPDEST + Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.DUP1 + Op.PUSH1[0x45]
        + Op.PUSH2[0x1ec] + Op.DUP4 + Op.CODECOPY + Op.PUSH1[0x45] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.CREATE + Op.SWAP2 + Op.POP + Op.DUP2
        + Op.PUSH20[0xffffffffffffffffffffffffffffffffffffffff] + Op.AND
        + Op.PUSH4[0x81bda09b] + Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.DUP3
        + Op.PUSH29[0x100000000000000000000000000000000000000000000000000000000]
        + Op.MUL + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x4] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.DUP7 + Op.PUSH2[0x61da] + Op.GAS + Op.SUB + Op.CALL
        + Op.PUSH2[0x119] + Op.JUMPI + Op.STOP + Op.JUMPDEST + Op.PUSH2[0xbf]
        + Op.PUSH1[0x0] + Op.PUSH2[0xc9] + Op.PUSH2[0x3d] + Op.JUMP + Op.JUMPDEST
        + Op.DUP1 + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x20] + Op.PUSH1[0x0]
        + Op.RETURN + Op.JUMPDEST + Op.DUP1 + Op.PUSH1[0x0] + Op.MSTORE
        + Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.RETURN + Op.JUMPDEST + Op.PUSH1[0x0]
        + Op.DUP1 + Op.SLOAD
        + Op.PUSH32[0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff00]
        + Op.AND + Op.SWAP2 + Op.SWAP1 + Op.SWAP2 + Op.OR + Op.SWAP1 + Op.DUP2
        + Op.SWAP1 + Op.SSTORE + Op.PUSH1[0xff] + Op.AND + Op.SWAP2 + Op.SWAP1
        + Op.POP + Op.JUMP + Op.JUMPDEST + Op.POP + Op.POP + Op.PUSH1[0x0] + Op.MLOAD
        + Op.PUSH4[0xffffffff] + Op.AND + Op.PUSH1[0x2] + Op.EQ + Op.ISZERO
        + Op.PUSH2[0x19d] + Op.JUMPI + Op.JUMPDEST + Op.JUMPDEST + Op.POP + Op.POP
        + Op.SWAP1 + Op.JUMP + Op.JUMPDEST + Op.POP + Op.POP + Op.PUSH1[0x0]
        + Op.MLOAD + Op.PUSH4[0xffffffff] + Op.AND + Op.PUSH1[0x1] + Op.EQ + Op.ISZERO
        + Op.PUSH2[0x194] + Op.JUMPI + Op.JUMPDEST + Op.PUSH1[0x45] + Op.PUSH2[0x1a7]
        + Op.PUSH1[0x0] + Op.CODECOPY + Op.PUSH1[0x45] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.CREATE + Op.SWAP1 + Op.POP + Op.DUP1
        + Op.PUSH20[0xffffffffffffffffffffffffffffffffffffffff] + Op.AND
        + Op.PUSH4[0x81bda09b] + Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.DUP3
        + Op.PUSH29[0x100000000000000000000000000000000000000000000000000000000]
        + Op.MUL + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x4] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.DUP7 + Op.PUSH2[0x61da] + Op.GAS + Op.SUB + Op.CALL
        + Op.PUSH2[0xff] + Op.JUMPI + Op.STOP + Op.JUMPDEST + Op.PUSH1[0x0] + Op.SWAP3
        + Op.POP + Op.PUSH2[0x114] + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x0] + Op.SWAP3
        + Op.POP + Op.PUSH2[0x114] + Op.JUMP + Op.STOP + Op.PUSH1[0x39] + Op.DUP1
        + Op.PUSH1[0xc] + Op.PUSH1[0x0] + Op.CODECOPY + Op.PUSH1[0x0] + Op.RETURN
        + Op.STOP
        + Op.PUSH29[0x100000000000000000000000000000000000000000000000000000000]
        + Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.DIV + Op.PUSH4[0x81bda09b] + Op.DUP2
        + Op.EQ + Op.PUSH1[0x2d] + Op.JUMPI + Op.STOP + Op.JUMPDEST + Op.PUSH1[0x2]
        + Op.PUSH1[0x0] + Op.DUP2 + Op.DUP2 + Op.MSTORE + Op.PUSH1[0x20] + Op.SWAP1
        + Op.RETURN + Op.PUSH1[0x39] + Op.DUP1 + Op.PUSH1[0xc] + Op.PUSH1[0x0]
        + Op.CODECOPY + Op.PUSH1[0x0] + Op.RETURN + Op.STOP
        + Op.PUSH29[0x100000000000000000000000000000000000000000000000000000000]
        + Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.DIV + Op.PUSH4[0x81bda09b] + Op.DUP2
        + Op.EQ + Op.PUSH1[0x2d] + Op.JUMPI + Op.STOP + Op.JUMPDEST + Op.PUSH1[0x1]
        + Op.PUSH1[0x0] + Op.DUP2 + Op.DUP2 + Op.MSTORE + Op.PUSH1[0x20] + Op.SWAP1
        + Op.RETURN
    ),
    )
    pre[sender] = Account(balance=0x12a05f200, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0xa9ae12cb2700c0214f86b9796881bc03a1fd5605d0e76d2da2ca592e62d53e52"
        ),
        to=contract,
        data=bytes.fromhex("c0406226"),
        gas_limit=35000000,
        gas_price=10,
        nonce=0,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
