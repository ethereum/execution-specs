"""
Ported from:
tests/static/state_tests/stWalletTest/multiOwnedRemoveOwnerFiller.json

contract code:
    push29 0x0100000000000000000000000000000000000000000000000000000000
    push1 0x00
    calldataload
    div
    push4 0x173825d9
    dup2
    eq
    push2 0x65
    jumpi
    dup1
    push4 0x2f54bf6e
    eq
    push2 0xb7
    jumpi
    dup1
    push4 0x7065cb48
    eq
    push2 0xe8
    jumpi
    dup1
    ... (1174 more instructions)
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
    ["tests/static/state_tests/stWalletTest/multiOwnedRemoveOwnerFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_multi_owned_remove_owner(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    contract = Address("0x6295ee1b4f6dd65047762f924ecd367c17eabf8f")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[contract] = Account(
        balance=100,
        nonce=0,
        code=(
        Op.PUSH29[0x100000000000000000000000000000000000000000000000000000000]
        + Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.DIV + Op.PUSH4[0x173825d9] + Op.DUP2
        + Op.EQ + Op.PUSH2[0x65] + Op.JUMPI + Op.DUP1 + Op.PUSH4[0x2f54bf6e] + Op.EQ
        + Op.PUSH2[0xb7] + Op.JUMPI + Op.DUP1 + Op.PUSH4[0x7065cb48] + Op.EQ
        + Op.PUSH2[0xe8] + Op.JUMPI + Op.DUP1 + Op.PUSH4[0xb75c7dc6] + Op.EQ
        + Op.PUSH2[0x105] + Op.JUMPI + Op.DUP1 + Op.PUSH4[0xba51a6df] + Op.EQ
        + Op.PUSH2[0x142] + Op.JUMPI + Op.DUP1 + Op.PUSH4[0xf00d4b5d] + Op.EQ
        + Op.PUSH2[0x15f] + Op.JUMPI + Op.STOP + Op.JUMPDEST + Op.PUSH2[0x181]
        + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x0] + Op.PUSH1[0x40]
        + Op.PUSH1[0x0] + Op.CALLDATASIZE + Op.DUP1 + Op.DUP3 + Op.DUP5
        + Op.CALLDATACOPY + Op.SWAP1 + Op.SWAP2 + Op.SHA3 + Op.SWAP1 + Op.POP
        + Op.PUSH2[0x46d] + Op.DUP2 + Op.JUMPDEST
        + Op.PUSH20[0xffffffffffffffffffffffffffffffffffffffff] + Op.CALLER + Op.AND
        + Op.PUSH1[0x0] + Op.SWAP1 + Op.DUP2 + Op.MSTORE + Op.PUSH2[0x102]
        + Op.PUSH1[0x20] + Op.MSTORE + Op.PUSH1[0x40] + Op.DUP2 + Op.SHA3 + Op.SLOAD
        + Op.DUP2 + Op.DUP1 + Op.DUP1 + Op.DUP4 + Op.DUP2 + Op.EQ + Op.ISZERO
        + Op.PUSH2[0x58f] + Op.JUMPI + Op.PUSH2[0x586] + Op.JUMP + Op.JUMPDEST
        + Op.PUSH2[0x187] + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.JUMPDEST
        + Op.PUSH20[0xffffffffffffffffffffffffffffffffffffffff] + Op.AND
        + Op.PUSH1[0x0] + Op.SWAP1 + Op.DUP2 + Op.MSTORE + Op.PUSH2[0x102]
        + Op.PUSH1[0x20] + Op.MSTORE + Op.PUSH1[0x40] + Op.DUP2 + Op.SHA3 + Op.SLOAD
        + Op.GT + Op.SWAP1 + Op.JUMP + Op.JUMPDEST + Op.PUSH2[0x181] + Op.PUSH1[0x4]
        + Op.CALLDATALOAD + Op.PUSH1[0x40] + Op.PUSH1[0x0] + Op.CALLDATASIZE + Op.DUP1
        + Op.DUP3 + Op.DUP5 + Op.CALLDATACOPY + Op.SWAP1 + Op.SWAP2 + Op.SHA3
        + Op.SWAP1 + Op.POP + Op.PUSH2[0x37c] + Op.DUP2 + Op.PUSH2[0x80] + Op.JUMP
        + Op.JUMPDEST + Op.PUSH2[0x181] + Op.PUSH1[0x4] + Op.CALLDATALOAD
        + Op.PUSH20[0xffffffffffffffffffffffffffffffffffffffff] + Op.CALLER + Op.AND
        + Op.PUSH1[0x0] + Op.SWAP1 + Op.DUP2 + Op.MSTORE + Op.PUSH2[0x102]
        + Op.PUSH1[0x20] + Op.MSTORE + Op.PUSH1[0x40] + Op.DUP2 + Op.SHA3 + Op.SLOAD
        + Op.SWAP1 + Op.DUP1 + Op.DUP1 + Op.DUP4 + Op.DUP2 + Op.EQ + Op.ISZERO
        + Op.PUSH2[0x191] + Op.JUMPI + Op.PUSH2[0x213] + Op.JUMP + Op.JUMPDEST
        + Op.PUSH2[0x181] + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x40]
        + Op.PUSH1[0x0] + Op.CALLDATASIZE + Op.DUP1 + Op.DUP3 + Op.DUP5
        + Op.CALLDATACOPY + Op.SWAP1 + Op.SWAP2 + Op.SHA3 + Op.SWAP1 + Op.POP
        + Op.PUSH2[0x533] + Op.DUP2 + Op.PUSH2[0x80] + Op.JUMP + Op.JUMPDEST
        + Op.PUSH2[0x181] + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x24]
        + Op.CALLDATALOAD + Op.PUSH1[0x0] + Op.PUSH1[0x40] + Op.PUSH1[0x0]
        + Op.CALLDATASIZE + Op.DUP1 + Op.DUP3 + Op.DUP5 + Op.CALLDATACOPY + Op.SWAP1
        + Op.SWAP2 + Op.SHA3 + Op.SWAP1 + Op.POP + Op.PUSH2[0x286] + Op.DUP2
        + Op.PUSH2[0x80] + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.RETURN + Op.JUMPDEST + Op.DUP1 + Op.PUSH1[0x0] + Op.MSTORE
        + Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.RETURN + Op.JUMPDEST + Op.POP + Op.POP
        + Op.POP + Op.PUSH1[0x0] + Op.DUP3 + Op.DUP2 + Op.MSTORE + Op.PUSH2[0x103]
        + Op.PUSH1[0x20] + Op.MSTORE + Op.PUSH1[0x40] + Op.DUP2 + Op.SHA3
        + Op.PUSH1[0x1] + Op.DUP2 + Op.ADD + Op.SLOAD + Op.PUSH1[0x2] + Op.DUP5
        + Op.SWAP1 + Op.EXP + Op.SWAP3 + Op.SWAP1 + Op.DUP4 + Op.AND + Op.DUP2
        + Op.SWAP1 + Op.GT + Op.ISZERO + Op.PUSH2[0x213] + Op.JUMPI + Op.DUP2
        + Op.SLOAD + Op.PUSH1[0x1] + Op.DUP1 + Op.DUP5 + Op.ADD + Op.DUP1 + Op.SLOAD
        + Op.SWAP2 + Op.SWAP1 + Op.SWAP3 + Op.ADD + Op.DUP5 + Op.SSTORE + Op.DUP5
        + Op.SWAP1 + Op.SUB + Op.SWAP1 + Op.SSTORE
        + Op.PUSH20[0xffffffffffffffffffffffffffffffffffffffff] + Op.CALLER + Op.AND
        + Op.PUSH1[0x40] + Op.SWAP1 + Op.DUP2 + Op.MSTORE + Op.PUSH1[0x60] + Op.DUP7
        + Op.SWAP1 + Op.MSTORE
        + Op.PUSH32[0xc7fb647e59b18047309aa15aad418e5d7ca96d173ad704f1031a2c3d7591734b]
        + Op.SWAP1 + Op.DUP1 + Op.LOG1 + Op.JUMPDEST + Op.POP + Op.POP + Op.POP
        + Op.POP + Op.POP + Op.JUMP + Op.JUMPDEST + Op.ADD + Op.SSTORE
        + Op.PUSH20[0xffffffffffffffffffffffffffffffffffffffff] + Op.DUP5 + Op.DUP2
        + Op.AND + Op.PUSH1[0x0] + Op.DUP2 + Op.DUP2 + Op.MSTORE + Op.PUSH2[0x102]
        + Op.PUSH1[0x20] + Op.MSTORE + Op.PUSH1[0x40] + Op.DUP1 + Op.DUP3 + Op.SHA3
        + Op.DUP3 + Op.SWAP1 + Op.SSTORE + Op.SWAP3 + Op.DUP7 + Op.AND + Op.DUP1
        + Op.DUP3 + Op.MSTORE + Op.SWAP1 + Op.DUP4 + Op.SWAP1 + Op.SHA3 + Op.DUP6
        + Op.SWAP1 + Op.SSTORE + Op.SWAP1 + Op.DUP3 + Op.MSTORE + Op.PUSH1[0x60]
        + Op.MSTORE
        + Op.PUSH32[0xb532073b38c83145e3e5135377a08bf9aab55bc0fd7c1179cd4fb995d2a5159c]
        + Op.SWAP1 + Op.DUP1 + Op.LOG1 + Op.JUMPDEST + Op.POP + Op.JUMPDEST + Op.POP
        + Op.POP + Op.POP + Op.JUMP + Op.JUMPDEST + Op.ISZERO + Op.PUSH2[0x27f]
        + Op.JUMPI + Op.PUSH2[0x294] + Op.DUP4 + Op.PUSH2[0xbe] + Op.JUMP
        + Op.JUMPDEST + Op.ISZERO + Op.PUSH2[0x29f] + Op.JUMPI + Op.POP
        + Op.PUSH2[0x281] + Op.JUMP + Op.JUMPDEST
        + Op.PUSH20[0xffffffffffffffffffffffffffffffffffffffff] + Op.DUP5 + Op.AND
        + Op.PUSH1[0x0] + Op.SWAP1 + Op.DUP2 + Op.MSTORE + Op.PUSH2[0x102]
        + Op.PUSH1[0x20] + Op.MSTORE + Op.PUSH1[0x40] + Op.DUP2 + Op.SHA3 + Op.SLOAD
        + Op.SWAP3 + Op.POP + Op.DUP3 + Op.EQ + Op.ISZERO + Op.PUSH2[0x2d5] + Op.JUMPI
        + Op.POP + Op.PUSH2[0x281] + Op.JUMP + Op.JUMPDEST + Op.PUSH2[0x2f7]
        + Op.JUMPDEST + Op.PUSH2[0x104] + Op.SLOAD + Op.PUSH1[0x0] + Op.JUMPDEST
        + Op.DUP2 + Op.DUP2 + Op.LT + Op.ISZERO + Op.PUSH2[0x80c] + Op.JUMPI
        + Op.PUSH2[0x104] + Op.DUP1 + Op.SLOAD + Op.DUP3 + Op.SWAP1 + Op.DUP2 + Op.LT
        + Op.PUSH2[0x854] + Op.JUMPI + Op.STOP + Op.JUMPDEST
        + Op.PUSH20[0xffffffffffffffffffffffffffffffffffffffff] + Op.DUP4 + Op.AND
        + Op.PUSH1[0x2] + Op.DUP4 + Op.PUSH2[0x100] + Op.DUP2 + Op.LT
        + Op.PUSH2[0x21a] + Op.JUMPI + Op.STOP + Op.JUMPDEST + Op.ADD + Op.SSTORE
        + Op.PUSH1[0x1] + Op.SLOAD
        + Op.PUSH20[0xffffffffffffffffffffffffffffffffffffffff] + Op.DUP4 + Op.AND
        + Op.PUSH1[0x0] + Op.DUP2 + Op.DUP2 + Op.MSTORE + Op.PUSH2[0x102]
        + Op.PUSH1[0x20] + Op.SWAP1 + Op.DUP2 + Op.MSTORE + Op.PUSH1[0x40] + Op.SWAP2
        + Op.DUP3 + Op.SWAP1 + Op.SHA3 + Op.SWAP4 + Op.SWAP1 + Op.SWAP4 + Op.SSTORE
        + Op.SWAP1 + Op.DUP2 + Op.MSTORE
        + Op.PUSH32[0x994a936646fe87ffe4f1e469d3d6aa417d6b855598397f323de5b449f765f0c3]
        + Op.SWAP2 + Op.SWAP1 + Op.LOG1 + Op.JUMPDEST + Op.POP + Op.JUMPDEST + Op.POP
        + Op.JUMP + Op.JUMPDEST + Op.ISZERO + Op.PUSH2[0x377] + Op.JUMPI
        + Op.PUSH2[0x38a] + Op.DUP3 + Op.PUSH2[0xbe] + Op.JUMP + Op.JUMPDEST
        + Op.ISZERO + Op.PUSH2[0x395] + Op.JUMPI + Op.POP + Op.PUSH2[0x379] + Op.JUMP
        + Op.JUMPDEST + Op.PUSH2[0x39d] + Op.PUSH2[0x2d9] + Op.JUMP + Op.JUMPDEST
        + Op.PUSH1[0x1] + Op.SLOAD + Op.PUSH1[0xfa] + Op.SWAP1 + Op.LT + Op.ISZERO
        + Op.ISZERO + Op.PUSH2[0x3b4] + Op.JUMPI + Op.PUSH2[0x3b2] + Op.PUSH2[0x3cb]
        + Op.JUMP + Op.JUMPDEST + Op.POP + Op.JUMPDEST + Op.PUSH1[0x1] + Op.SLOAD
        + Op.PUSH1[0xfa] + Op.SWAP1 + Op.LT + Op.ISZERO + Op.ISZERO + Op.PUSH2[0x3f5]
        + Op.JUMPI + Op.POP + Op.PUSH2[0x379] + Op.JUMP + Op.JUMPDEST
        + Op.PUSH2[0x425] + Op.JUMPDEST + Op.PUSH1[0x0] + Op.PUSH1[0x1] + Op.JUMPDEST
        + Op.PUSH1[0x1] + Op.SLOAD + Op.DUP2 + Op.LT + Op.ISZERO + Op.PUSH2[0x6f7]
        + Op.JUMPI + Op.JUMPDEST + Op.PUSH1[0x1] + Op.SLOAD + Op.DUP2 + Op.LT
        + Op.DUP1 + Op.ISZERO + Op.PUSH2[0x753] + Op.JUMPI + Op.POP + Op.PUSH1[0x2]
        + Op.DUP2 + Op.PUSH2[0x100] + Op.DUP2 + Op.LT + Op.PUSH2[0x74c] + Op.JUMPI
        + Op.STOP + Op.JUMPDEST + Op.PUSH1[0x1] + Op.DUP1 + Op.SLOAD + Op.DUP2
        + Op.ADD + Op.SWAP1 + Op.DUP2 + Op.SWAP1 + Op.SSTORE
        + Op.PUSH20[0xffffffffffffffffffffffffffffffffffffffff] + Op.DUP4 + Op.AND
        + Op.SWAP1 + Op.PUSH1[0x2] + Op.SWAP1 + Op.PUSH2[0x100] + Op.DUP2 + Op.LT
        + Op.PUSH2[0x31c] + Op.JUMPI + Op.STOP + Op.JUMPDEST + Op.POP
        + Op.PUSH20[0xffffffffffffffffffffffffffffffffffffffff] + Op.DUP4 + Op.AND
        + Op.PUSH1[0x40] + Op.SWAP1 + Op.DUP2 + Op.MSTORE
        + Op.PUSH32[0x58619076adf5bb0943d100ef88d52d7c3fd691b19d3a9071b555b651fbf418da]
        + Op.SWAP1 + Op.PUSH1[0x20] + Op.SWAP1 + Op.LOG1 + Op.POP + Op.POP + Op.POP
        + Op.JUMP + Op.JUMPDEST + Op.ISZERO + Op.PUSH2[0x281] + Op.JUMPI
        + Op.PUSH20[0xffffffffffffffffffffffffffffffffffffffff] + Op.DUP4 + Op.AND
        + Op.PUSH1[0x0] + Op.SWAP1 + Op.DUP2 + Op.MSTORE + Op.PUSH2[0x102]
        + Op.PUSH1[0x20] + Op.MSTORE + Op.PUSH1[0x40] + Op.DUP2 + Op.SHA3 + Op.SLOAD
        + Op.SWAP3 + Op.POP + Op.DUP3 + Op.EQ + Op.ISZERO + Op.PUSH2[0x4a8] + Op.JUMPI
        + Op.POP + Op.PUSH2[0x377] + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x1]
        + Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.POP + Op.SLOAD + Op.SUB + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.POP + Op.SLOAD + Op.GT + Op.ISZERO + Op.PUSH2[0x4c3]
        + Op.JUMPI + Op.POP + Op.PUSH2[0x377] + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x0]
        + Op.PUSH1[0x2] + Op.DUP4 + Op.PUSH2[0x100] + Op.DUP2 + Op.LT
        + Op.PUSH2[0x4d3] + Op.JUMPI + Op.STOP + Op.JUMPDEST + Op.ADD + Op.SSTORE
        + Op.PUSH20[0xffffffffffffffffffffffffffffffffffffffff] + Op.DUP4 + Op.AND
        + Op.PUSH1[0x0] + Op.SWAP1 + Op.DUP2 + Op.MSTORE + Op.PUSH2[0x102]
        + Op.PUSH1[0x20] + Op.MSTORE + Op.PUSH1[0x40] + Op.DUP2 + Op.SHA3 + Op.SSTORE
        + Op.PUSH2[0x3c7] + Op.PUSH2[0x2d9] + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x40]
        + Op.DUP3 + Op.DUP2 + Op.MSTORE
        + Op.PUSH32[0xacbdb084c721332ac59f9b8e392196c9eb0e4932862da8eb9beaf0dad4f550da]
        + Op.SWAP1 + Op.PUSH1[0x20] + Op.SWAP1 + Op.LOG1 + Op.POP + Op.POP + Op.JUMP
        + Op.JUMPDEST + Op.ISZERO + Op.PUSH2[0x377] + Op.JUMPI + Op.PUSH1[0x1]
        + Op.SLOAD + Op.DUP3 + Op.GT + Op.ISZERO + Op.PUSH2[0x548] + Op.JUMPI + Op.POP
        + Op.PUSH2[0x379] + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x0] + Op.DUP3 + Op.SWAP1
        + Op.SSTORE + Op.PUSH2[0x504] + Op.PUSH2[0x2d9] + Op.JUMP + Op.JUMPDEST
        + Op.DUP3 + Op.SLOAD
        + Op.PUSH32[0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff]
        + Op.ADD + Op.DUP4 + Op.SSTORE + Op.PUSH1[0x1] + Op.DUP4 + Op.ADD + Op.DUP1
        + Op.SLOAD + Op.DUP3 + Op.OR + Op.SWAP1 + Op.SSTORE + Op.JUMPDEST + Op.POP
        + Op.POP + Op.POP + Op.POP + Op.SWAP2 + Op.SWAP1 + Op.POP + Op.JUMP
        + Op.JUMPDEST + Op.PUSH1[0x0] + Op.DUP7 + Op.DUP2 + Op.MSTORE
        + Op.PUSH2[0x103] + Op.PUSH1[0x20] + Op.MSTORE + Op.PUSH1[0x40] + Op.DUP2
        + Op.SHA3 + Op.DUP1 + Op.SLOAD + Op.SWAP1 + Op.SWAP5 + Op.POP + Op.SWAP1
        + Op.SWAP3 + Op.POP + Op.DUP3 + Op.EQ + Op.ISZERO + Op.PUSH2[0x61a] + Op.JUMPI
        + Op.DUP2 + Op.SLOAD + Op.DUP4 + Op.SSTORE + Op.PUSH1[0x1] + Op.DUP4 + Op.DUP2
        + Op.ADD + Op.DUP4 + Op.SWAP1 + Op.SSTORE + Op.PUSH2[0x104] + Op.DUP1
        + Op.SLOAD + Op.SWAP2 + Op.DUP3 + Op.ADD + Op.DUP1 + Op.DUP3 + Op.SSTORE
        + Op.DUP3 + Op.DUP1 + Op.ISZERO + Op.DUP3 + Op.SWAP1 + Op.GT + Op.PUSH2[0x6a6]
        + Op.JUMPI + Op.DUP3 + Op.DUP7 + Op.MSTORE
        + Op.PUSH32[0x4c0be60200faa20559308cb7b5a1bb3255c16cb1cab91f525b5ae7a03d02fabe]
        + Op.SWAP1 + Op.DUP2 + Op.ADD + Op.SWAP1 + Op.DUP3 + Op.ADD + Op.JUMPDEST
        + Op.DUP1 + Op.DUP3 + Op.GT + Op.ISZERO + Op.PUSH2[0x6a4] + Op.JUMPI
        + Op.PUSH1[0x0] + Op.DUP2 + Op.SSTORE + Op.PUSH1[0x1] + Op.ADD
        + Op.PUSH2[0x5f9] + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x0] + Op.SWAP2 + Op.DUP3
        + Op.MSTORE + Op.PUSH1[0x20] + Op.SWAP1 + Op.SWAP2 + Op.SHA3 + Op.ADD
        + Op.SSTORE + Op.JUMPDEST + Op.POP + Op.PUSH1[0x1] + Op.DUP3 + Op.ADD
        + Op.SLOAD + Op.PUSH1[0x2] + Op.DUP5 + Op.SWAP1 + Op.EXP + Op.SWAP1 + Op.DUP2
        + Op.AND + Op.PUSH1[0x0] + Op.EQ + Op.ISZERO + Op.PUSH2[0x586] + Op.JUMPI
        + Op.PUSH20[0xffffffffffffffffffffffffffffffffffffffff] + Op.CALLER + Op.AND
        + Op.PUSH1[0x40] + Op.SWAP1 + Op.DUP2 + Op.MSTORE + Op.PUSH1[0x60] + Op.DUP8
        + Op.SWAP1 + Op.MSTORE
        + Op.PUSH32[0xe1c52dc63b719ade82e8bea94cc41a0d5d28e4aaf536adb5e9cccc9ff8c1aeda]
        + Op.SWAP1 + Op.DUP1 + Op.LOG1 + Op.DUP3 + Op.SLOAD + Op.PUSH1[0x1] + Op.SWAP1
        + Op.GT + Op.ISZERO + Op.ISZERO + Op.PUSH2[0x555] + Op.JUMPI + Op.PUSH1[0x0]
        + Op.DUP7 + Op.DUP2 + Op.MSTORE + Op.PUSH2[0x103] + Op.PUSH1[0x20] + Op.MSTORE
        + Op.PUSH2[0x104] + Op.DUP1 + Op.SLOAD + Op.PUSH1[0x40] + Op.SWAP1 + Op.SWAP3
        + Op.SHA3 + Op.PUSH1[0x2] + Op.ADD + Op.SLOAD + Op.SWAP1 + Op.SWAP2 + Op.DUP2
        + Op.LT + Op.PUSH2[0x6c0] + Op.JUMPI + Op.STOP + Op.JUMPDEST + Op.POP
        + Op.JUMPDEST + Op.POP + Op.POP + Op.POP + Op.PUSH1[0x2] + Op.DUP5 + Op.ADD
        + Op.DUP2 + Op.SWAP1 + Op.SSTORE + Op.PUSH2[0x104] + Op.DUP1 + Op.SLOAD
        + Op.DUP9 + Op.SWAP3 + Op.SWAP1 + Op.DUP2 + Op.LT + Op.PUSH2[0x60d] + Op.JUMPI
        + Op.STOP + Op.JUMPDEST + Op.PUSH1[0x0] + Op.SWAP2 + Op.DUP3 + Op.MSTORE
        + Op.PUSH1[0x20] + Op.DUP1 + Op.DUP4 + Op.SHA3 + Op.SWAP1 + Op.SWAP2 + Op.ADD
        + Op.DUP3 + Op.SWAP1 + Op.SSTORE + Op.DUP8 + Op.DUP3 + Op.MSTORE
        + Op.PUSH2[0x103] + Op.SWAP1 + Op.MSTORE + Op.PUSH1[0x40] + Op.DUP2 + Op.SHA3
        + Op.DUP2 + Op.DUP2 + Op.SSTORE + Op.PUSH1[0x1] + Op.DUP2 + Op.DUP2 + Op.ADD
        + Op.DUP4 + Op.SWAP1 + Op.SSTORE + Op.PUSH1[0x2] + Op.SWAP1 + Op.SWAP2
        + Op.ADD + Op.SWAP2 + Op.SWAP1 + Op.SWAP2 + Op.SSTORE + Op.SWAP5 + Op.POP
        + Op.PUSH2[0x586] + Op.JUMP + Op.JUMPDEST + Op.POP + Op.SWAP1 + Op.JUMP
        + Op.JUMPDEST + Op.ADD + Op.SLOAD + Op.PUSH1[0x0] + Op.EQ + Op.JUMPDEST
        + Op.ISZERO + Op.PUSH2[0x760] + Op.JUMPI + Op.PUSH1[0x1] + Op.DUP1 + Op.SLOAD
        + Op.PUSH32[0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff]
        + Op.ADD + Op.SWAP1 + Op.SSTORE + Op.JUMPDEST + Op.PUSH1[0x1] + Op.DUP1
        + Op.SLOAD + Op.GT + Op.DUP1 + Op.ISZERO + Op.PUSH2[0x701] + Op.JUMPI + Op.POP
        + Op.PUSH1[0x1] + Op.SLOAD + Op.PUSH1[0x2] + Op.SWAP1 + Op.PUSH2[0x100]
        + Op.DUP2 + Op.LT + Op.PUSH2[0x6fb] + Op.JUMPI + Op.STOP + Op.JUMPDEST
        + Op.ADD + Op.SLOAD + Op.PUSH1[0x0] + Op.EQ + Op.ISZERO + Op.JUMPDEST
        + Op.ISZERO + Op.PUSH2[0x72f] + Op.JUMPI + Op.PUSH1[0x1] + Op.ADD
        + Op.PUSH2[0x3db] + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x1] + Op.SLOAD + Op.DUP2
        + Op.LT + Op.DUP1 + Op.ISZERO + Op.PUSH2[0x784] + Op.JUMPI + Op.POP
        + Op.PUSH1[0x1] + Op.SLOAD + Op.PUSH1[0x2] + Op.SWAP1 + Op.PUSH2[0x100]
        + Op.DUP2 + Op.LT + Op.PUSH2[0x77d] + Op.JUMPI + Op.STOP + Op.JUMPDEST
        + Op.ADD + Op.SLOAD + Op.PUSH1[0x0] + Op.EQ + Op.ISZERO + Op.JUMPDEST
        + Op.DUP1 + Op.ISZERO + Op.PUSH2[0x79f] + Op.JUMPI + Op.POP + Op.PUSH1[0x2]
        + Op.DUP2 + Op.PUSH2[0x100] + Op.DUP2 + Op.LT + Op.PUSH2[0x799] + Op.JUMPI
        + Op.STOP + Op.JUMPDEST + Op.ADD + Op.SLOAD + Op.PUSH1[0x0] + Op.EQ
        + Op.JUMPDEST + Op.ISZERO + Op.PUSH2[0x7b8] + Op.JUMPI + Op.PUSH1[0x1]
        + Op.SLOAD + Op.PUSH1[0x2] + Op.SWAP1 + Op.PUSH2[0x100] + Op.DUP2 + Op.LT
        + Op.PUSH2[0x7bd] + Op.JUMPI + Op.STOP + Op.JUMPDEST + Op.ADD + Op.SSTORE
        + Op.JUMPDEST + Op.PUSH2[0x3d0] + Op.JUMP + Op.JUMPDEST + Op.ADD + Op.SLOAD
        + Op.PUSH1[0x2] + Op.DUP3 + Op.PUSH2[0x100] + Op.DUP2 + Op.LT
        + Op.PUSH2[0x7cd] + Op.JUMPI + Op.STOP + Op.JUMPDEST + Op.ADD + Op.SSTORE
        + Op.DUP1 + Op.PUSH2[0x102] + Op.PUSH1[0x0] + Op.PUSH1[0x2] + Op.DUP4
        + Op.PUSH2[0x100] + Op.DUP2 + Op.LT + Op.PUSH2[0x7e3] + Op.JUMPI + Op.STOP
        + Op.JUMPDEST + Op.ADD + Op.SLOAD + Op.DUP2 + Op.MSTORE + Op.PUSH1[0x20]
        + Op.DUP2 + Op.ADD + Op.SWAP2 + Op.SWAP1 + Op.SWAP2 + Op.MSTORE
        + Op.PUSH1[0x40] + Op.ADD + Op.PUSH1[0x0] + Op.SWAP1 + Op.DUP2 + Op.SHA3
        + Op.SWAP2 + Op.SWAP1 + Op.SWAP2 + Op.SSTORE + Op.PUSH1[0x1] + Op.SLOAD
        + Op.PUSH1[0x2] + Op.SWAP1 + Op.PUSH2[0x100] + Op.DUP2 + Op.LT
        + Op.PUSH2[0x7b5] + Op.JUMPI + Op.STOP + Op.JUMPDEST + Op.PUSH2[0x104]
        + Op.DUP1 + Op.SLOAD + Op.PUSH1[0x0] + Op.DUP1 + Op.DUP4 + Op.SSTORE
        + Op.SWAP2 + Op.SWAP1 + Op.SWAP2 + Op.MSTORE
        + Op.PUSH32[0x4c0be60200faa20559308cb7b5a1bb3255c16cb1cab91f525b5ae7a03d02fabe]
        + Op.SWAP1 + Op.DUP2 + Op.ADD + Op.SWAP1 + Op.JUMPDEST + Op.DUP1 + Op.DUP3
        + Op.GT + Op.ISZERO + Op.PUSH2[0x27f] + Op.JUMPI + Op.PUSH1[0x0] + Op.DUP2
        + Op.SSTORE + Op.PUSH1[0x1] + Op.ADD + Op.PUSH2[0x840] + Op.JUMP + Op.JUMPDEST
        + Op.PUSH1[0x0] + Op.SWAP2 + Op.DUP3 + Op.MSTORE + Op.PUSH1[0x20] + Op.DUP3
        + Op.SHA3 + Op.ADD + Op.SLOAD + Op.EQ + Op.ISZERO + Op.ISZERO
        + Op.PUSH2[0x8a6] + Op.JUMPI + Op.PUSH2[0x104] + Op.DUP1 + Op.SLOAD
        + Op.PUSH2[0x103] + Op.SWAP2 + Op.PUSH1[0x0] + Op.SWAP2 + Op.DUP5 + Op.SWAP1
        + Op.DUP2 + Op.LT + Op.PUSH2[0x87c] + Op.JUMPI + Op.STOP + Op.JUMPDEST
        + Op.PUSH1[0x0] + Op.SWAP2 + Op.DUP3 + Op.MSTORE + Op.PUSH1[0x20] + Op.DUP1
        + Op.DUP4 + Op.SHA3 + Op.SWAP1 + Op.SWAP2 + Op.ADD + Op.SLOAD + Op.DUP4
        + Op.MSTORE + Op.DUP3 + Op.ADD + Op.SWAP3 + Op.SWAP1 + Op.SWAP3 + Op.MSTORE
        + Op.PUSH1[0x40] + Op.ADD + Op.DUP2 + Op.SHA3 + Op.DUP2 + Op.DUP2 + Op.SSTORE
        + Op.PUSH1[0x1] + Op.DUP2 + Op.ADD + Op.DUP3 + Op.SWAP1 + Op.SSTORE
        + Op.PUSH1[0x2] + Op.ADD + Op.SSTORE + Op.JUMPDEST + Op.PUSH1[0x1] + Op.ADD
        + Op.PUSH2[0x2e0] + Op.JUMP
    ),
        storage={0x0: 0x1, 0x1: 0x2, 0x3: 0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b, 0x4: 0x3fb1cd2cd96c6d5c0b5eb3322d807b34482481d4, 0x6e369836487c234b9e553ef3f787c2d8865520739d340c67b3d251a33986e58d: 0x1, 0xd3e69d8c7f41f7aeaf8130ddc53047aeee8cb46a73d6bae86b7e7d6bf8312e6b: 0x2},
    )
    pre[sender] = Account(balance=0xde0b6b3a75ef08f, nonce=1)

    tx = Transaction(
        secret_key=Hash(
            "0x45a915e4d060149eb4365960e6a7a45f334393093061116b197e3240065ff2d8"
        ),
        to=contract,
        data=bytes.fromhex("173825d9000000000000000000000000a94f5374fce5edbc8e2a8697c15331677e6ebf0b"),
        gas_limit=10000000,
        gas_price=10,
        nonce=1,
        value=100,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
