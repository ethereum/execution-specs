"""
Ported from:
tests/static/state_tests/stSolidityTest/TestCryptographicFunctionsFiller.json

contract code:
    push1 0x00
    calldataload
    push29 0x0100000000000000000000000000000000000000000000000000000000
    swap1
    div
    dup1
    push4 0xc0406226
    eq
    push2 0x3a
    jumpi
    dup1
    push4 0xe0a9fd28
    eq
    push2 0x4c
    jumpi
    stop
    jumpdest
    push2 0x42
    push2 0x5e
    jump
    ... (237 more instructions)
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
    ["tests/static/state_tests/stSolidityTest/TestCryptographicFunctionsFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Prague")
@pytest.mark.pre_alloc_mutable
def test_test_cryptographic_functions(
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
        gas_limit=9223372036854775807,
    )

    pre[contract] = Account(
        balance=0x186a0,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.CALLDATALOAD
        + Op.PUSH29[0x100000000000000000000000000000000000000000000000000000000]
        + Op.SWAP1 + Op.DIV + Op.DUP1 + Op.PUSH4[0xc0406226] + Op.EQ + Op.PUSH2[0x3a]
        + Op.JUMPI + Op.DUP1 + Op.PUSH4[0xe0a9fd28] + Op.EQ + Op.PUSH2[0x4c]
        + Op.JUMPI + Op.STOP + Op.JUMPDEST + Op.PUSH2[0x42] + Op.PUSH2[0x5e] + Op.JUMP
        + Op.JUMPDEST + Op.DUP1 + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x20]
        + Op.PUSH1[0x0] + Op.RETURN + Op.JUMPDEST + Op.PUSH2[0x54] + Op.PUSH2[0x99]
        + Op.JUMP + Op.JUMPDEST + Op.DUP1 + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x20]
        + Op.PUSH1[0x0] + Op.RETURN + Op.JUMPDEST + Op.PUSH1[0x0] + Op.PUSH2[0x68]
        + Op.PUSH2[0x99] + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH2[0x100] + Op.EXP + Op.DUP2 + Op.SLOAD + Op.DUP2 + Op.PUSH1[0xff]
        + Op.MUL + Op.NOT + Op.AND + Op.SWAP1 + Op.DUP4 + Op.MUL + Op.OR + Op.SWAP1
        + Op.SSTORE + Op.POP + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.SWAP1 + Op.SLOAD
        + Op.SWAP1 + Op.PUSH2[0x100] + Op.EXP + Op.SWAP1 + Op.DIV + Op.PUSH1[0xff]
        + Op.AND + Op.SWAP1 + Op.POP + Op.PUSH2[0x96] + Op.JUMP + Op.JUMPDEST
        + Op.SWAP1 + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x0] + Op.PUSH1[0x1] + Op.SWAP1
        + Op.POP + Op.DUP1 + Op.POP
        + Op.PUSH32[0x43c4b4524adb81e4e9a5c4648a98e9d320e3908ac5b6c889144b642cd08ae16d]
        + Op.PUSH1[0x1] + Op.MUL + Op.PUSH1[0x40]
        + Op.PUSH32[0x74657374737472696e6700000000000000000000000000000000000000000000]
        + Op.DUP2 + Op.MSTORE + Op.PUSH1[0xa] + Op.ADD + Op.PUSH1[0x40] + Op.SWAP1
        + Op.SUB + Op.PUSH1[0x40] + Op.SHA3 + Op.EQ + Op.ISZERO + Op.PUSH2[0xff]
        + Op.JUMPI + Op.PUSH2[0x108] + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x0]
        + Op.SWAP1 + Op.POP + Op.PUSH2[0x2ec] + Op.JUMP + Op.JUMPDEST
        + Op.PUSH32[0x3c8727e019a42b444667a587b6001251becadabbb36bfed8087a92c18882d111]
        + Op.PUSH1[0x1] + Op.MUL + Op.PUSH1[0x2] + Op.PUSH1[0x20] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0]
        + Op.PUSH32[0x74657374737472696e6700000000000000000000000000000000000000000000]
        + Op.DUP2 + Op.MSTORE + Op.PUSH1[0xa] + Op.ADD + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.DUP6 + Op.PUSH2[0x61da] + Op.GAS + Op.SUB + Op.CALL + Op.PUSH2[0x16b]
        + Op.JUMPI + Op.STOP + Op.JUMPDEST + Op.POP + Op.PUSH1[0x0] + Op.MLOAD + Op.EQ
        + Op.ISZERO + Op.PUSH2[0x17a] + Op.JUMPI + Op.PUSH2[0x183] + Op.JUMP
        + Op.JUMPDEST + Op.PUSH1[0x0] + Op.SWAP1 + Op.POP + Op.PUSH2[0x2ec] + Op.JUMP
        + Op.JUMPDEST + Op.PUSH20[0xcd566972b5e50104011a92b59fa8e0b1234851ae]
        + Op.PUSH13[0x1000000000000000000000000] + Op.MUL + Op.PUSH1[0x3]
        + Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH32[0x74657374737472696e6700000000000000000000000000000000000000000000]
        + Op.DUP2 + Op.MSTORE + Op.PUSH1[0xa] + Op.ADD + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.DUP6 + Op.PUSH2[0x61da] + Op.GAS + Op.SUB + Op.CALL + Op.PUSH2[0x1e6]
        + Op.JUMPI + Op.STOP + Op.JUMPDEST + Op.POP + Op.PUSH1[0x0] + Op.MLOAD
        + Op.PUSH13[0x1000000000000000000000000] + Op.MUL + Op.EQ + Op.ISZERO
        + Op.PUSH2[0x204] + Op.JUMPI + Op.PUSH2[0x20d] + Op.JUMP + Op.JUMPDEST
        + Op.PUSH1[0x0] + Op.SWAP1 + Op.POP + Op.PUSH2[0x2ec] + Op.JUMP + Op.JUMPDEST
        + Op.PUSH20[0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b] + Op.PUSH1[0x1]
        + Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH32[0x18c547e4f7b0f325ad1e56f57e26c745b09a3e503d86e00e5255ff7f715d3d1c]
        + Op.PUSH1[0x1] + Op.MUL + Op.DUP2 + Op.MSTORE + Op.PUSH1[0x20] + Op.ADD
        + Op.PUSH1[0x1c] + Op.DUP2 + Op.MSTORE + Op.PUSH1[0x20] + Op.ADD
        + Op.PUSH32[0x73b1693892219d736caba55bdb67216e485557ea6b6af75f37096c9aa6a5a75f]
        + Op.PUSH1[0x1] + Op.MUL + Op.DUP2 + Op.MSTORE + Op.PUSH1[0x20] + Op.ADD
        + Op.PUSH32[0xeeb940b1d03b21e36b0e47e79769f095fe2ab855bd91e3a38756b7d75a9c4549]
        + Op.PUSH1[0x1] + Op.MUL + Op.DUP2 + Op.MSTORE + Op.PUSH1[0x20] + Op.ADD
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.DUP6 + Op.PUSH2[0x61da] + Op.GAS + Op.SUB
        + Op.CALL + Op.PUSH2[0x2bd] + Op.JUMPI + Op.STOP + Op.JUMPDEST + Op.POP
        + Op.PUSH1[0x0] + Op.MLOAD
        + Op.PUSH20[0xffffffffffffffffffffffffffffffffffffffff] + Op.AND + Op.EQ
        + Op.ISZERO + Op.PUSH2[0x2e2] + Op.JUMPI + Op.PUSH2[0x2eb] + Op.JUMP
        + Op.JUMPDEST + Op.PUSH1[0x0] + Op.SWAP1 + Op.POP + Op.PUSH2[0x2ec] + Op.JUMP
        + Op.JUMPDEST + Op.JUMPDEST + Op.SWAP1 + Op.JUMP
    ),
    )
    pre[sender] = Account(balance=0x12a05f200, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x45a915e4d060149eb4365960e6a7a45f334393093061116b197e3240065ff2d8"
        ),
        to=contract,
        data=bytes.fromhex("c0406226"),
        gas_limit=35000000,
        gas_price=10,
        nonce=0,
        value=100,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
