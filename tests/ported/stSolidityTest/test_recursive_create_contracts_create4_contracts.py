"""
Ported from:
tests/static/state_tests/stSolidityTest/RecursiveCreateContractsCreate4ContractsFiller.json

contract code:
    push1 0x00
    calldataload
    push1 0xe0
    push1 0x02
    exp
    swap1
    div
    dup1
    push4 0x820b13f6
    eq
    push2 0x21
    jumpi
    dup1
    push4 0xa444f5e9
    eq
    push2 0x32
    jumpi
    stop
    jumpdest
    push2 0x2c
    ... (336 more instructions)
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
    ["tests/static/state_tests/stSolidityTest/RecursiveCreateContractsCreate4ContractsFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_recursive_create_contracts_create4_contracts(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    contract = Address("0x095e7baea6a6c7c4c2dfeb977efac326af552d87")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[contract] = Account(
        balance=0x314dc6448d9338c15b0a00000000,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH1[0xe0] + Op.PUSH1[0x2] + Op.EXP
        + Op.SWAP1 + Op.DIV + Op.DUP1 + Op.PUSH4[0x820b13f6] + Op.EQ + Op.PUSH2[0x21]
        + Op.JUMPI + Op.DUP1 + Op.PUSH4[0xa444f5e9] + Op.EQ + Op.PUSH2[0x32]
        + Op.JUMPI + Op.STOP + Op.JUMPDEST + Op.PUSH2[0x2c] + Op.PUSH1[0x4]
        + Op.CALLDATALOAD + Op.PUSH2[0x93] + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.RETURN + Op.JUMPDEST + Op.PUSH2[0x3d] + Op.PUSH1[0x4]
        + Op.CALLDATALOAD + Op.PUSH2[0x43] + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.RETURN + Op.JUMPDEST + Op.PUSH1[0x0]
        + Op.PUSH20[0x95e7baea6a6c7c4c2dfeb977efac326af552d87] + Op.PUSH1[0x0]
        + Op.DUP2 + Op.SWAP1 + Op.SSTORE + Op.POP + Op.DUP2 + Op.PUSH1[0x1] + Op.DUP2
        + Op.SWAP1 + Op.SSTORE + Op.POP + Op.PUSH1[0x6b] + Op.PUSH2[0x1ad]
        + Op.PUSH1[0x0] + Op.CODECOPY + Op.PUSH1[0x6b] + Op.PUSH1[0x0] + Op.SLOAD
        + Op.PUSH1[0x1] + Op.PUSH1[0xa0] + Op.PUSH1[0x2] + Op.EXP + Op.SUB + Op.AND
        + Op.DUP2 + Op.MSTORE + Op.PUSH1[0x20] + Op.ADD + Op.DUP3 + Op.DUP2
        + Op.MSTORE + Op.PUSH1[0x20] + Op.ADD + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.CREATE + Op.SWAP1 + Op.POP + Op.POP + Op.POP + Op.JUMP + Op.JUMPDEST
        + Op.PUSH1[0x0] + Op.PUSH1[0xc8] + Op.PUSH2[0xe5] + Op.PUSH1[0x0]
        + Op.CODECOPY + Op.PUSH1[0xc8] + Op.PUSH1[0x0] + Op.SLOAD + Op.PUSH1[0x1]
        + Op.PUSH1[0xa0] + Op.PUSH1[0x2] + Op.EXP + Op.SUB + Op.AND + Op.DUP2
        + Op.MSTORE + Op.PUSH1[0x20] + Op.ADD + Op.DUP3 + Op.DUP2 + Op.MSTORE
        + Op.PUSH1[0x20] + Op.ADD + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.CREATE
        + Op.SWAP1 + Op.POP + Op.DUP1 + Op.PUSH1[0x1] + Op.PUSH1[0xa0] + Op.PUSH1[0x2]
        + Op.EXP + Op.SUB + Op.AND + Op.PUSH1[0x0] + Op.PUSH1[0x2] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.DUP5 + Op.DUP8 + Op.DUP8
        + Op.CALL + Op.PUSH2[0xdd] + Op.JUMPI + Op.STOP + Op.JUMPDEST + Op.POP
        + Op.POP + Op.POP + Op.POP + Op.POP + Op.JUMP + Op.STOP + Op.PUSH1[0x40]
        + Op.PUSH1[0xc8] + Op.PUSH1[0x4] + Op.CODECOPY + Op.PUSH1[0x4] + Op.MLOAD
        + Op.PUSH1[0x24] + Op.MLOAD + Op.PUSH1[0x0] + Op.PUSH1[0x1] + Op.DUP3 + Op.SUB
        + Op.SWAP2 + Op.POP + Op.DUP2 + Op.PUSH1[0x0] + Op.DUP2 + Op.SWAP1 + Op.SSTORE
        + Op.POP + Op.PUSH1[0x0] + Op.DUP3 + Op.GT + Op.PUSH1[0x26] + Op.JUMPI
        + Op.PUSH1[0x4c] + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x6b] + Op.PUSH1[0x5d]
        + Op.PUSH1[0x0] + Op.CODECOPY + Op.PUSH1[0x6b] + Op.DUP4 + Op.PUSH1[0x1]
        + Op.PUSH1[0xa0] + Op.PUSH1[0x2] + Op.EXP + Op.SUB + Op.AND + Op.DUP2
        + Op.MSTORE + Op.PUSH1[0x20] + Op.ADD + Op.DUP3 + Op.DUP2 + Op.MSTORE
        + Op.PUSH1[0x20] + Op.ADD + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.CREATE
        + Op.SWAP1 + Op.POP + Op.JUMPDEST + Op.POP + Op.POP + Op.POP + Op.PUSH1[0x1]
        + Op.DUP1 + Op.PUSH1[0x5c] + Op.PUSH1[0x0] + Op.CODECOPY + Op.PUSH1[0x0]
        + Op.RETURN + Op.STOP + Op.STOP + Op.PUSH1[0x40] + Op.PUSH1[0x6b]
        + Op.PUSH1[0x4] + Op.CODECOPY + Op.PUSH1[0x4] + Op.MLOAD + Op.PUSH1[0x24]
        + Op.MLOAD + Op.PUSH1[0x1] + Op.DUP2 + Op.SUB + Op.SWAP1 + Op.POP + Op.DUP1
        + Op.PUSH1[0x0] + Op.DUP2 + Op.SWAP1 + Op.SSTORE + Op.POP + Op.PUSH1[0x0]
        + Op.DUP2 + Op.GT + Op.PUSH1[0x24] + Op.JUMPI + Op.PUSH1[0x5b] + Op.JUMP
        + Op.JUMPDEST + Op.DUP2 + Op.PUSH1[0x1] + Op.PUSH1[0xa0] + Op.PUSH1[0x2]
        + Op.EXP + Op.SUB + Op.AND + Op.PUSH4[0x820b13f6] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.DUP3 + Op.PUSH1[0xe0] + Op.PUSH1[0x2] + Op.EXP + Op.MUL
        + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x4] + Op.DUP6 + Op.DUP2 + Op.MSTORE
        + Op.PUSH1[0x20] + Op.ADD + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.DUP7
        + Op.PUSH1[0x32] + Op.GAS + Op.SUB + Op.CALL + Op.PUSH1[0x58] + Op.JUMPI
        + Op.STOP + Op.JUMPDEST + Op.POP + Op.POP + Op.JUMPDEST + Op.POP + Op.POP
        + Op.PUSH1[0x1] + Op.DUP1 + Op.PUSH1[0x6a] + Op.PUSH1[0x0] + Op.CODECOPY
        + Op.PUSH1[0x0] + Op.RETURN + Op.STOP + Op.STOP + Op.PUSH1[0x40]
        + Op.PUSH1[0x6b] + Op.PUSH1[0x4] + Op.CODECOPY + Op.PUSH1[0x4] + Op.MLOAD
        + Op.PUSH1[0x24] + Op.MLOAD + Op.PUSH1[0x1] + Op.DUP2 + Op.SUB + Op.SWAP1
        + Op.POP + Op.DUP1 + Op.PUSH1[0x0] + Op.DUP2 + Op.SWAP1 + Op.SSTORE + Op.POP
        + Op.PUSH1[0x0] + Op.DUP2 + Op.GT + Op.PUSH1[0x24] + Op.JUMPI + Op.PUSH1[0x5b]
        + Op.JUMP + Op.JUMPDEST + Op.DUP2 + Op.PUSH1[0x1] + Op.PUSH1[0xa0]
        + Op.PUSH1[0x2] + Op.EXP + Op.SUB + Op.AND + Op.PUSH4[0x820b13f6]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.DUP3 + Op.PUSH1[0xe0] + Op.PUSH1[0x2]
        + Op.EXP + Op.MUL + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x4] + Op.DUP6
        + Op.DUP2 + Op.MSTORE + Op.PUSH1[0x20] + Op.ADD + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.DUP7 + Op.PUSH1[0x32] + Op.GAS + Op.SUB + Op.CALL
        + Op.PUSH1[0x58] + Op.JUMPI + Op.STOP + Op.JUMPDEST + Op.POP + Op.POP
        + Op.JUMPDEST + Op.POP + Op.POP + Op.PUSH1[0x1] + Op.DUP1 + Op.PUSH1[0x6a]
        + Op.PUSH1[0x0] + Op.CODECOPY + Op.PUSH1[0x0] + Op.RETURN + Op.STOP + Op.STOP
    ),
    )
    pre[sender] = Account(balance=0x1dcd6500, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x45a915e4d060149eb4365960e6a7a45f334393093061116b197e3240065ff2d8"
        ),
        to=contract,
        data=bytes.fromhex("a444f5e90000000000000000000000000000000000000000000000000000000000000004"),
        gas_limit=300000,
        gas_price=10,
        nonce=0,
        value=1,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
