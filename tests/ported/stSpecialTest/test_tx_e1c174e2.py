"""
Ported from:
tests/static/state_tests/stSpecialTest/tx_e1c174e2Filler.json

contract code:
    push1 0x00
    push2 0x155f
    mstore8
    push29 0x0100000000000000000000000000000000000000000000000000000000
    push1 0x00
    calldataload
    div
    push4 0x55f10aaf
    dup2
    eq
    iszero
    push2 0x65
    jumpi
    push1 0x04
    calldataload
    push1 0x40
    mstore
    push1 0x00
    callvalue
    sgt
    ... (5770 more instructions)
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
    ["tests/static/state_tests/stSpecialTest/tx_e1c174e2Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_tx_e1c174e2(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x68795c4aa09d6f4ed3e5deddf8c2ad3049a601da")
    sender = Address("0x57e3080b624809c72f75eae38de87b9d75c9a073")
    contract = Address("0xf47bacb0d8f13fa44d31623c3d5ae72907d241c1")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=3141592,
    )

    pre[sender] = Account(balance=0xde0b6b3a7640000, nonce=24)
    pre[contract] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH2[0x155f] + Op.MSTORE8
        + Op.PUSH29[0x100000000000000000000000000000000000000000000000000000000]
        + Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.DIV + Op.PUSH4[0x55f10aaf] + Op.DUP2
        + Op.EQ + Op.ISZERO + Op.PUSH2[0x65] + Op.JUMPI + Op.PUSH1[0x4]
        + Op.CALLDATALOAD + Op.PUSH1[0x40] + Op.MSTORE + Op.PUSH1[0x0] + Op.CALLVALUE
        + Op.SGT + Op.ISZERO + Op.PUSH2[0x52] + Op.JUMPI + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.CALLVALUE + Op.CALLER
        + Op.PUSH2[0x1388] + Op.CALL + Op.POP + Op.JUMPDEST + Op.PUSH1[0xc]
        + Op.PUSH1[0x40] + Op.MLOAD + Op.MUL + Op.PUSH1[0x7] + Op.ADD + Op.SLOAD
        + Op.PUSH1[0x60] + Op.MSTORE + Op.PUSH1[0x20] + Op.PUSH1[0x60] + Op.RETURN
        + Op.JUMPDEST + Op.PUSH4[0x69e0998b] + Op.DUP2 + Op.EQ + Op.ISZERO
        + Op.PUSH2[0x53f] + Op.JUMPI + Op.PUSH1[0x4] + Op.CALLDATALOAD
        + Op.PUSH1[0x80] + Op.MSTORE + Op.PUSH1[0x24] + Op.CALLDATALOAD
        + Op.PUSH1[0xa0] + Op.MSTORE + Op.PUSH1[0x44] + Op.CALLDATALOAD
        + Op.PUSH1[0x40] + Op.MSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x80] + Op.MLOAD
        + Op.SGT + Op.ISZERO + Op.ISZERO + Op.PUSH2[0x9a] + Op.JUMPI + Op.PUSH1[0x2]
        + Op.PUSH1[0xc0] + Op.MSTORE + Op.PUSH1[0x20] + Op.PUSH1[0xc0] + Op.RETURN
        + Op.JUMPDEST + Op.PUSH1[0x0] + Op.PUSH1[0xa0] + Op.MLOAD + Op.SGT + Op.ISZERO
        + Op.ISZERO + Op.PUSH2[0xb1] + Op.JUMPI + Op.PUSH1[0x3] + Op.PUSH1[0xe0]
        + Op.MSTORE + Op.PUSH1[0x20] + Op.PUSH1[0xe0] + Op.RETURN + Op.JUMPDEST
        + Op.PUSH1[0x0] + Op.PUSH1[0x40] + Op.MLOAD + Op.SGT + Op.ISZERO + Op.ISZERO
        + Op.PUSH2[0xca] + Op.JUMPI + Op.PUSH1[0x4] + Op.PUSH2[0x100] + Op.MSTORE
        + Op.PUSH1[0x20] + Op.PUSH2[0x100] + Op.RETURN + Op.JUMPDEST
        + Op.PUSH8[0xde0b6b3a7640000] + Op.PUSH1[0xc] + Op.PUSH1[0x40] + Op.MLOAD
        + Op.MUL + Op.PUSH1[0x3] + Op.ADD + Op.SLOAD + Op.PUSH1[0xa] + Op.EXP
        + Op.PUSH1[0xc] + Op.PUSH1[0x40] + Op.MLOAD + Op.MUL + Op.PUSH1[0x4] + Op.ADD
        + Op.SLOAD + Op.MUL + Op.PUSH1[0xa0] + Op.MLOAD + Op.PUSH1[0x80] + Op.MLOAD
        + Op.MUL + Op.SDIV + Op.MUL + Op.PUSH2[0x120] + Op.MSTORE + Op.PUSH1[0xc]
        + Op.PUSH1[0x40] + Op.MLOAD + Op.MUL + Op.PUSH1[0x5] + Op.ADD + Op.SLOAD
        + Op.CALLVALUE + Op.SLT + Op.ISZERO + Op.PUSH2[0x12f] + Op.JUMPI
        + Op.PUSH1[0x0] + Op.CALLVALUE + Op.SGT + Op.ISZERO + Op.PUSH2[0x122]
        + Op.JUMPI + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.CALLVALUE + Op.CALLER + Op.PUSH2[0x1388] + Op.CALL + Op.POP + Op.JUMPDEST
        + Op.PUSH1[0xb] + Op.PUSH2[0x140] + Op.MSTORE + Op.PUSH1[0x20]
        + Op.PUSH2[0x140] + Op.RETURN + Op.JUMPDEST + Op.PUSH2[0x120] + Op.MLOAD
        + Op.CALLVALUE + Op.SLT + Op.ISZERO + Op.PUSH2[0x160] + Op.JUMPI
        + Op.PUSH1[0x0] + Op.CALLVALUE + Op.SGT + Op.ISZERO + Op.PUSH2[0x153]
        + Op.JUMPI + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.CALLVALUE + Op.CALLER + Op.PUSH2[0x1388] + Op.CALL + Op.POP + Op.JUMPDEST
        + Op.PUSH1[0x14] + Op.PUSH2[0x160] + Op.MSTORE + Op.PUSH1[0x20]
        + Op.PUSH2[0x160] + Op.RETURN + Op.JUMPDEST + Op.PUSH2[0x120] + Op.MLOAD
        + Op.CALLVALUE + Op.SGT + Op.ISZERO + Op.PUSH2[0x180] + Op.JUMPI
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH2[0x120] + Op.MLOAD + Op.CALLVALUE + Op.SUB + Op.CALLER
        + Op.PUSH2[0x1388] + Op.CALL + Op.POP + Op.JUMPDEST + Op.PUSH1[0xe0]
        + Op.MSIZE + Op.SWAP1 + Op.MSIZE + Op.ADD + Op.PUSH1[0x0] + Op.SWAP1
        + Op.MSTORE + Op.PUSH1[0x6] + Op.DUP2 + Op.MSTORE + Op.PUSH1[0x1]
        + Op.PUSH1[0x20] + Op.DUP3 + Op.ADD + Op.MSTORE + Op.PUSH1[0x40] + Op.MLOAD
        + Op.PUSH1[0x40] + Op.DUP3 + Op.ADD + Op.MSTORE + Op.PUSH1[0x80] + Op.MLOAD
        + Op.PUSH1[0x60] + Op.DUP3 + Op.ADD + Op.MSTORE + Op.PUSH1[0xa0] + Op.MLOAD
        + Op.PUSH1[0x80] + Op.DUP3 + Op.ADD + Op.MSTORE + Op.CALLER + Op.PUSH1[0xa0]
        + Op.DUP3 + Op.ADD + Op.MSTORE + Op.NUMBER + Op.PUSH1[0xc0] + Op.DUP3 + Op.ADD
        + Op.MSTORE + Op.PUSH1[0x20] + Op.DUP2 + Op.ADD + Op.SWAP1 + Op.POP
        + Op.PUSH2[0x180] + Op.MSTORE + Op.PUSH2[0x180] + Op.MLOAD + Op.PUSH1[0x20]
        + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB + Op.MLOAD + Op.MUL + Op.DUP2 + Op.SHA3
        + Op.SWAP1 + Op.POP + Op.PUSH2[0x1c0] + Op.MSTORE + Op.PUSH1[0x8]
        + Op.PUSH2[0x1c0] + Op.MLOAD + Op.MUL
        + Op.PUSH21[0xe0000000000000000000000000000000000000000] + Op.ADD + Op.SLOAD
        + Op.ISZERO + Op.ISZERO + Op.PUSH2[0x4be] + Op.JUMPI + Op.PUSH2[0x1c0]
        + Op.MLOAD + Op.PUSH1[0x8] + Op.PUSH2[0x1c0] + Op.MLOAD + Op.MUL
        + Op.PUSH21[0xe0000000000000000000000000000000000000000] + Op.ADD + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x8] + Op.PUSH2[0x1c0] + Op.MLOAD + Op.MUL
        + Op.PUSH21[0xe0000000000000000000000000000000000000001] + Op.ADD + Op.SSTORE
        + Op.PUSH1[0x40] + Op.MLOAD + Op.PUSH1[0x8] + Op.PUSH2[0x1c0] + Op.MLOAD
        + Op.MUL + Op.PUSH21[0xe0000000000000000000000000000000000000002] + Op.ADD
        + Op.SSTORE + Op.PUSH1[0x80] + Op.MLOAD + Op.PUSH1[0x8] + Op.PUSH2[0x1c0]
        + Op.MLOAD + Op.MUL + Op.PUSH21[0xe0000000000000000000000000000000000000003]
        + Op.ADD + Op.SSTORE + Op.PUSH1[0xa0] + Op.MLOAD + Op.PUSH1[0x8]
        + Op.PUSH2[0x1c0] + Op.MLOAD + Op.MUL
        + Op.PUSH21[0xe0000000000000000000000000000000000000004] + Op.ADD + Op.SSTORE
        + Op.CALLER + Op.PUSH1[0x8] + Op.PUSH2[0x1c0] + Op.MLOAD + Op.MUL
        + Op.PUSH21[0xe0000000000000000000000000000000000000005] + Op.ADD + Op.SSTORE
        + Op.NUMBER + Op.PUSH1[0x8] + Op.PUSH2[0x1c0] + Op.MLOAD + Op.MUL
        + Op.PUSH21[0xe0000000000000000000000000000000000000006] + Op.ADD + Op.SSTORE
        + Op.PUSH1[0x8] + Op.PUSH2[0x1c0] + Op.MLOAD + Op.MUL
        + Op.PUSH21[0xe0000000000000000000000000000000000000000] + Op.ADD
        + Op.PUSH1[0x8] + Op.PUSH2[0x1c0] + Op.MLOAD + Op.MUL
        + Op.PUSH21[0xe0000000000000000000000000000000000000007] + Op.ADD + Op.SSTORE
        + Op.PUSH1[0xc] + Op.PUSH1[0x40] + Op.MLOAD + Op.MUL + Op.PUSH1[0xb] + Op.ADD
        + Op.SLOAD + Op.PUSH2[0x200] + Op.MSTORE + Op.PUSH2[0x1c0] + Op.MLOAD
        + Op.PUSH1[0xa0] + Op.PUSH1[0xa0] + Op.MSIZE + Op.SWAP1 + Op.MSIZE + Op.ADD
        + Op.PUSH1[0x0] + Op.SWAP1 + Op.MSTORE + Op.PUSH1[0x0] + Op.DUP2 + Op.MSTORE
        + Op.PUSH1[0x40] + Op.MLOAD + Op.DUP2 + Op.PUSH1[0x20] + Op.ADD + Op.MSTORE
        + Op.PUSH1[0xc] + Op.DUP2 + Op.PUSH1[0x40] + Op.ADD + Op.MSTORE
        + Op.PUSH2[0x200] + Op.MLOAD + Op.DUP2 + Op.PUSH1[0x60] + Op.ADD + Op.MSTORE
        + Op.PUSH1[0x1] + Op.DUP2 + Op.PUSH1[0x80] + Op.ADD + Op.MSTORE + Op.DUP1
        + Op.SWAP1 + Op.POP + Op.SHA3 + Op.SSTORE + Op.PUSH2[0x200] + Op.MLOAD
        + Op.PUSH1[0xa0] + Op.PUSH1[0xa0] + Op.MSIZE + Op.SWAP1 + Op.MSIZE + Op.ADD
        + Op.PUSH1[0x0] + Op.SWAP1 + Op.MSTORE + Op.PUSH1[0x0] + Op.DUP2 + Op.MSTORE
        + Op.PUSH1[0x40] + Op.MLOAD + Op.DUP2 + Op.PUSH1[0x20] + Op.ADD + Op.MSTORE
        + Op.PUSH1[0xc] + Op.DUP2 + Op.PUSH1[0x40] + Op.ADD + Op.MSTORE
        + Op.PUSH2[0x1c0] + Op.MLOAD + Op.DUP2 + Op.PUSH1[0x60] + Op.ADD + Op.MSTORE
        + Op.PUSH1[0x2] + Op.DUP2 + Op.PUSH1[0x80] + Op.ADD + Op.MSTORE + Op.DUP1
        + Op.SWAP1 + Op.POP + Op.SHA3 + Op.SSTORE + Op.PUSH2[0x1c0] + Op.MLOAD
        + Op.PUSH1[0xa0] + Op.PUSH1[0xa0] + Op.MSIZE + Op.SWAP1 + Op.MSIZE + Op.ADD
        + Op.PUSH1[0x0] + Op.SWAP1 + Op.MSTORE + Op.PUSH1[0x0] + Op.DUP2 + Op.MSTORE
        + Op.PUSH1[0x40] + Op.MLOAD + Op.DUP2 + Op.PUSH1[0x20] + Op.ADD + Op.MSTORE
        + Op.PUSH1[0xc] + Op.DUP2 + Op.PUSH1[0x40] + Op.ADD + Op.MSTORE
        + Op.PUSH2[0x1c0] + Op.MLOAD + Op.DUP2 + Op.PUSH1[0x60] + Op.ADD + Op.MSTORE
        + Op.PUSH1[0x0] + Op.DUP2 + Op.PUSH1[0x80] + Op.ADD + Op.MSTORE + Op.DUP1
        + Op.SWAP1 + Op.POP + Op.SHA3 + Op.SSTORE + Op.PUSH2[0x1c0] + Op.MLOAD
        + Op.PUSH1[0xc] + Op.PUSH1[0x40] + Op.MLOAD + Op.MUL + Op.PUSH1[0xb] + Op.ADD
        + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0xc] + Op.PUSH1[0x40] + Op.MLOAD
        + Op.MUL + Op.PUSH1[0xa] + Op.ADD + Op.SLOAD + Op.ADD + Op.PUSH1[0xc]
        + Op.PUSH1[0x40] + Op.MLOAD + Op.MUL + Op.PUSH1[0xa] + Op.ADD + Op.SSTORE
        + Op.PUSH1[0x2] + Op.PUSH1[0x1] + Op.EQ + Op.ISZERO + Op.PUSH2[0x4b9]
        + Op.JUMPI + Op.PUSH1[0x80] + Op.MLOAD + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.MSIZE + Op.SWAP1 + Op.MSIZE + Op.ADD + Op.PUSH1[0x0] + Op.SWAP1
        + Op.MSTORE + Op.PUSH1[0x4] + Op.DUP2 + Op.MSTORE + Op.CALLER + Op.DUP2
        + Op.PUSH1[0x20] + Op.ADD + Op.MSTORE + Op.PUSH1[0x40] + Op.MLOAD + Op.DUP2
        + Op.PUSH1[0x40] + Op.ADD + Op.MSTORE + Op.PUSH1[0x0] + Op.DUP2
        + Op.PUSH1[0x60] + Op.ADD + Op.MSTORE + Op.DUP1 + Op.SWAP1 + Op.POP + Op.SHA3
        + Op.SLOAD + Op.SUB + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.MSIZE + Op.SWAP1
        + Op.MSIZE + Op.ADD + Op.PUSH1[0x0] + Op.SWAP1 + Op.MSTORE + Op.PUSH1[0x4]
        + Op.DUP2 + Op.MSTORE + Op.CALLER + Op.DUP2 + Op.PUSH1[0x20] + Op.ADD
        + Op.MSTORE + Op.PUSH1[0x40] + Op.MLOAD + Op.DUP2 + Op.PUSH1[0x40] + Op.ADD
        + Op.MSTORE + Op.PUSH1[0x0] + Op.DUP2 + Op.PUSH1[0x60] + Op.ADD + Op.MSTORE
        + Op.DUP1 + Op.SWAP1 + Op.POP + Op.SHA3 + Op.SSTORE + Op.PUSH1[0x80]
        + Op.MLOAD + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.MSIZE + Op.SWAP1 + Op.MSIZE
        + Op.ADD + Op.PUSH1[0x0] + Op.SWAP1 + Op.MSTORE + Op.PUSH1[0x4] + Op.DUP2
        + Op.MSTORE + Op.CALLER + Op.DUP2 + Op.PUSH1[0x20] + Op.ADD + Op.MSTORE
        + Op.PUSH1[0x40] + Op.MLOAD + Op.DUP2 + Op.PUSH1[0x40] + Op.ADD + Op.MSTORE
        + Op.PUSH1[0x1] + Op.DUP2 + Op.PUSH1[0x60] + Op.ADD + Op.MSTORE + Op.DUP1
        + Op.SWAP1 + Op.POP + Op.SHA3 + Op.SLOAD + Op.ADD + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.MSIZE + Op.SWAP1 + Op.MSIZE + Op.ADD + Op.PUSH1[0x0]
        + Op.SWAP1 + Op.MSTORE + Op.PUSH1[0x4] + Op.DUP2 + Op.MSTORE + Op.CALLER
        + Op.DUP2 + Op.PUSH1[0x20] + Op.ADD + Op.MSTORE + Op.PUSH1[0x40] + Op.MLOAD
        + Op.DUP2 + Op.PUSH1[0x40] + Op.ADD + Op.MSTORE + Op.PUSH1[0x1] + Op.DUP2
        + Op.PUSH1[0x60] + Op.ADD + Op.MSTORE + Op.DUP1 + Op.SWAP1 + Op.POP + Op.SHA3
        + Op.SSTORE + Op.JUMPDEST + Op.PUSH2[0x4cb] + Op.JUMP + Op.JUMPDEST
        + Op.PUSH1[0x15] + Op.PUSH2[0x300] + Op.MSTORE + Op.PUSH1[0x20]
        + Op.PUSH2[0x300] + Op.RETURN + Op.JUMPDEST + Op.PUSH1[0x1c] + Op.PUSH1[0xc0]
        + Op.MSIZE + Op.SWAP1 + Op.MSIZE + Op.ADD + Op.PUSH1[0x0] + Op.SWAP1
        + Op.MSTORE + Op.ADD + Op.CALLER + Op.DUP2 + Op.MSTORE + Op.PUSH1[0x1]
        + Op.PUSH1[0x20] + Op.DUP3 + Op.ADD + Op.MSTORE + Op.PUSH1[0xa0] + Op.MLOAD
        + Op.PUSH1[0x40] + Op.DUP3 + Op.ADD + Op.MSTORE + Op.PUSH1[0x80] + Op.MLOAD
        + Op.PUSH1[0x60] + Op.DUP3 + Op.ADD + Op.MSTORE + Op.PUSH2[0x1c0] + Op.MLOAD
        + Op.PUSH1[0x80] + Op.DUP3 + Op.ADD + Op.MSTORE + Op.PUSH1[0x40] + Op.MLOAD
        + Op.PUSH32[0x9463d1cc4aa2db0dc624c996b1846f028d43c48cfc8b9f427f13336e4a732264]
        + Op.PUSH1[0xa0] + Op.DUP4 + Op.LOG2 + Op.POP + Op.PUSH2[0x1c0] + Op.MLOAD
        + Op.PUSH2[0x340] + Op.MSTORE + Op.PUSH1[0x20] + Op.PUSH2[0x340] + Op.RETURN
        + Op.PUSH1[0x0] + Op.PUSH2[0x360] + Op.MSTORE + Op.PUSH1[0x20]
        + Op.PUSH2[0x360] + Op.RETURN + Op.JUMPDEST + Op.PUSH4[0x909f073] + Op.DUP2
        + Op.EQ + Op.ISZERO + Op.PUSH2[0xa0c] + Op.JUMPI + Op.PUSH1[0x4]
        + Op.CALLDATALOAD + Op.PUSH1[0x80] + Op.MSTORE + Op.PUSH1[0x24]
        + Op.CALLDATALOAD + Op.PUSH1[0xa0] + Op.MSTORE + Op.PUSH1[0x44]
        + Op.CALLDATALOAD + Op.PUSH1[0x40] + Op.MSTORE + Op.PUSH1[0x0]
        + Op.PUSH1[0x80] + Op.MLOAD + Op.SGT + Op.ISZERO + Op.ISZERO + Op.PUSH2[0x576]
        + Op.JUMPI + Op.PUSH1[0x2] + Op.PUSH2[0x380] + Op.MSTORE + Op.PUSH1[0x20]
        + Op.PUSH2[0x380] + Op.RETURN + Op.JUMPDEST + Op.PUSH1[0x0] + Op.PUSH1[0xa0]
        + Op.MLOAD + Op.SGT + Op.ISZERO + Op.ISZERO + Op.PUSH2[0x58f] + Op.JUMPI
        + Op.PUSH1[0x3] + Op.PUSH2[0x3a0] + Op.MSTORE + Op.PUSH1[0x20]
        + Op.PUSH2[0x3a0] + Op.RETURN + Op.JUMPDEST + Op.PUSH1[0x0] + Op.PUSH1[0x40]
        + Op.MLOAD + Op.SGT + Op.ISZERO + Op.ISZERO + Op.PUSH2[0x5a8] + Op.JUMPI
        + Op.PUSH1[0x4] + Op.PUSH2[0x3c0] + Op.MSTORE + Op.PUSH1[0x20]
        + Op.PUSH2[0x3c0] + Op.RETURN + Op.JUMPDEST + Op.PUSH8[0xde0b6b3a7640000]
        + Op.PUSH1[0xc] + Op.PUSH1[0x40] + Op.MLOAD + Op.MUL + Op.PUSH1[0x3] + Op.ADD
        + Op.SLOAD + Op.PUSH1[0xa] + Op.EXP + Op.PUSH1[0xc] + Op.PUSH1[0x40]
        + Op.MLOAD + Op.MUL + Op.PUSH1[0x4] + Op.ADD + Op.SLOAD + Op.MUL
        + Op.PUSH1[0xa0] + Op.MLOAD + Op.PUSH1[0x80] + Op.MLOAD + Op.MUL + Op.SDIV
        + Op.MUL + Op.PUSH2[0x120] + Op.MSTORE + Op.PUSH1[0xc] + Op.PUSH1[0x40]
        + Op.MLOAD + Op.MUL + Op.PUSH1[0x5] + Op.ADD + Op.SLOAD + Op.PUSH2[0x120]
        + Op.MLOAD + Op.SLT + Op.ISZERO + Op.PUSH2[0x610] + Op.JUMPI + Op.PUSH1[0x0]
        + Op.CALLVALUE + Op.SGT + Op.ISZERO + Op.PUSH2[0x603] + Op.JUMPI
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.CALLVALUE
        + Op.CALLER + Op.PUSH2[0x1388] + Op.CALL + Op.POP + Op.JUMPDEST
        + Op.PUSH1[0xb] + Op.PUSH2[0x3e0] + Op.MSTORE + Op.PUSH1[0x20]
        + Op.PUSH2[0x3e0] + Op.RETURN + Op.JUMPDEST + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.MSIZE + Op.SWAP1 + Op.MSIZE + Op.ADD + Op.PUSH1[0x0] + Op.SWAP1
        + Op.MSTORE + Op.PUSH1[0x4] + Op.DUP2 + Op.MSTORE + Op.CALLER + Op.DUP2
        + Op.PUSH1[0x20] + Op.ADD + Op.MSTORE + Op.PUSH1[0x40] + Op.MLOAD + Op.DUP2
        + Op.PUSH1[0x40] + Op.ADD + Op.MSTORE + Op.PUSH1[0x0] + Op.DUP2
        + Op.PUSH1[0x60] + Op.ADD + Op.MSTORE + Op.DUP1 + Op.SWAP1 + Op.POP + Op.SHA3
        + Op.SLOAD + Op.PUSH2[0x400] + Op.MSTORE + Op.PUSH1[0x80] + Op.MLOAD
        + Op.PUSH2[0x400] + Op.MLOAD + Op.SLT + Op.ISZERO + Op.ISZERO
        + Op.PUSH2[0x9ff] + Op.JUMPI + Op.PUSH1[0xe0] + Op.MSIZE + Op.SWAP1 + Op.MSIZE
        + Op.ADD + Op.PUSH1[0x0] + Op.SWAP1 + Op.MSTORE + Op.PUSH1[0x6] + Op.DUP2
        + Op.MSTORE + Op.PUSH1[0x2] + Op.PUSH1[0x20] + Op.DUP3 + Op.ADD + Op.MSTORE
        + Op.PUSH1[0x40] + Op.MLOAD + Op.PUSH1[0x40] + Op.DUP3 + Op.ADD + Op.MSTORE
        + Op.PUSH1[0x80] + Op.MLOAD + Op.PUSH1[0x60] + Op.DUP3 + Op.ADD + Op.MSTORE
        + Op.PUSH1[0xa0] + Op.MLOAD + Op.PUSH1[0x80] + Op.DUP3 + Op.ADD + Op.MSTORE
        + Op.CALLER + Op.PUSH1[0xa0] + Op.DUP3 + Op.ADD + Op.MSTORE + Op.NUMBER
        + Op.PUSH1[0xc0] + Op.DUP3 + Op.ADD + Op.MSTORE + Op.PUSH1[0x20] + Op.DUP2
        + Op.ADD + Op.SWAP1 + Op.POP + Op.PUSH2[0x180] + Op.MSTORE + Op.PUSH2[0x180]
        + Op.MLOAD + Op.PUSH1[0x20] + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB + Op.MLOAD
        + Op.MUL + Op.DUP2 + Op.SHA3 + Op.SWAP1 + Op.POP + Op.PUSH2[0x1c0] + Op.MSTORE
        + Op.PUSH1[0x8] + Op.PUSH2[0x1c0] + Op.MLOAD + Op.MUL
        + Op.PUSH21[0xe0000000000000000000000000000000000000000] + Op.ADD + Op.SLOAD
        + Op.ISZERO + Op.ISZERO + Op.PUSH2[0x98a] + Op.JUMPI + Op.PUSH2[0x1c0]
        + Op.MLOAD + Op.PUSH1[0x8] + Op.PUSH2[0x1c0] + Op.MLOAD + Op.MUL
        + Op.PUSH21[0xe0000000000000000000000000000000000000000] + Op.ADD + Op.SSTORE
        + Op.PUSH1[0x2] + Op.PUSH1[0x8] + Op.PUSH2[0x1c0] + Op.MLOAD + Op.MUL
        + Op.PUSH21[0xe0000000000000000000000000000000000000001] + Op.ADD + Op.SSTORE
        + Op.PUSH1[0x40] + Op.MLOAD + Op.PUSH1[0x8] + Op.PUSH2[0x1c0] + Op.MLOAD
        + Op.MUL + Op.PUSH21[0xe0000000000000000000000000000000000000002] + Op.ADD
        + Op.SSTORE + Op.PUSH1[0x80] + Op.MLOAD + Op.PUSH1[0x8] + Op.PUSH2[0x1c0]
        + Op.MLOAD + Op.MUL + Op.PUSH21[0xe0000000000000000000000000000000000000003]
        + Op.ADD + Op.SSTORE + Op.PUSH1[0xa0] + Op.MLOAD + Op.PUSH1[0x8]
        + Op.PUSH2[0x1c0] + Op.MLOAD + Op.MUL
        + Op.PUSH21[0xe0000000000000000000000000000000000000004] + Op.ADD + Op.SSTORE
        + Op.CALLER + Op.PUSH1[0x8] + Op.PUSH2[0x1c0] + Op.MLOAD + Op.MUL
        + Op.PUSH21[0xe0000000000000000000000000000000000000005] + Op.ADD + Op.SSTORE
        + Op.NUMBER + Op.PUSH1[0x8] + Op.PUSH2[0x1c0] + Op.MLOAD + Op.MUL
        + Op.PUSH21[0xe0000000000000000000000000000000000000006] + Op.ADD + Op.SSTORE
        + Op.PUSH1[0x8] + Op.PUSH2[0x1c0] + Op.MLOAD + Op.MUL
        + Op.PUSH21[0xe0000000000000000000000000000000000000000] + Op.ADD
        + Op.PUSH1[0x8] + Op.PUSH2[0x1c0] + Op.MLOAD + Op.MUL
        + Op.PUSH21[0xe0000000000000000000000000000000000000007] + Op.ADD + Op.SSTORE
        + Op.PUSH1[0xc] + Op.PUSH1[0x40] + Op.MLOAD + Op.MUL + Op.PUSH1[0xb] + Op.ADD
        + Op.SLOAD + Op.PUSH2[0x200] + Op.MSTORE + Op.PUSH2[0x1c0] + Op.MLOAD
        + Op.PUSH1[0xa0] + Op.PUSH1[0xa0] + Op.MSIZE + Op.SWAP1 + Op.MSIZE + Op.ADD
        + Op.PUSH1[0x0] + Op.SWAP1 + Op.MSTORE + Op.PUSH1[0x0] + Op.DUP2 + Op.MSTORE
        + Op.PUSH1[0x40] + Op.MLOAD + Op.DUP2 + Op.PUSH1[0x20] + Op.ADD + Op.MSTORE
        + Op.PUSH1[0xc] + Op.DUP2 + Op.PUSH1[0x40] + Op.ADD + Op.MSTORE
        + Op.PUSH2[0x200] + Op.MLOAD + Op.DUP2 + Op.PUSH1[0x60] + Op.ADD + Op.MSTORE
        + Op.PUSH1[0x1] + Op.DUP2 + Op.PUSH1[0x80] + Op.ADD + Op.MSTORE + Op.DUP1
        + Op.SWAP1 + Op.POP + Op.SHA3 + Op.SSTORE + Op.PUSH2[0x200] + Op.MLOAD
        + Op.PUSH1[0xa0] + Op.PUSH1[0xa0] + Op.MSIZE + Op.SWAP1 + Op.MSIZE + Op.ADD
        + Op.PUSH1[0x0] + Op.SWAP1 + Op.MSTORE + Op.PUSH1[0x0] + Op.DUP2 + Op.MSTORE
        + Op.PUSH1[0x40] + Op.MLOAD + Op.DUP2 + Op.PUSH1[0x20] + Op.ADD + Op.MSTORE
        + Op.PUSH1[0xc] + Op.DUP2 + Op.PUSH1[0x40] + Op.ADD + Op.MSTORE
        + Op.PUSH2[0x1c0] + Op.MLOAD + Op.DUP2 + Op.PUSH1[0x60] + Op.ADD + Op.MSTORE
        + Op.PUSH1[0x2] + Op.DUP2 + Op.PUSH1[0x80] + Op.ADD + Op.MSTORE + Op.DUP1
        + Op.SWAP1 + Op.POP + Op.SHA3 + Op.SSTORE + Op.PUSH2[0x1c0] + Op.MLOAD
        + Op.PUSH1[0xa0] + Op.PUSH1[0xa0] + Op.MSIZE + Op.SWAP1 + Op.MSIZE + Op.ADD
        + Op.PUSH1[0x0] + Op.SWAP1 + Op.MSTORE + Op.PUSH1[0x0] + Op.DUP2 + Op.MSTORE
        + Op.PUSH1[0x40] + Op.MLOAD + Op.DUP2 + Op.PUSH1[0x20] + Op.ADD + Op.MSTORE
        + Op.PUSH1[0xc] + Op.DUP2 + Op.PUSH1[0x40] + Op.ADD + Op.MSTORE
        + Op.PUSH2[0x1c0] + Op.MLOAD + Op.DUP2 + Op.PUSH1[0x60] + Op.ADD + Op.MSTORE
        + Op.PUSH1[0x0] + Op.DUP2 + Op.PUSH1[0x80] + Op.ADD + Op.MSTORE + Op.DUP1
        + Op.SWAP1 + Op.POP + Op.SHA3 + Op.SSTORE + Op.PUSH2[0x1c0] + Op.MLOAD
        + Op.PUSH1[0xc] + Op.PUSH1[0x40] + Op.MLOAD + Op.MUL + Op.PUSH1[0xb] + Op.ADD
        + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0xc] + Op.PUSH1[0x40] + Op.MLOAD
        + Op.MUL + Op.PUSH1[0xa] + Op.ADD + Op.SLOAD + Op.ADD + Op.PUSH1[0xc]
        + Op.PUSH1[0x40] + Op.MLOAD + Op.MUL + Op.PUSH1[0xa] + Op.ADD + Op.SSTORE
        + Op.PUSH1[0x2] + Op.PUSH1[0x2] + Op.EQ + Op.ISZERO + Op.PUSH2[0x985]
        + Op.JUMPI + Op.PUSH1[0x80] + Op.MLOAD + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.MSIZE + Op.SWAP1 + Op.MSIZE + Op.ADD + Op.PUSH1[0x0] + Op.SWAP1
        + Op.MSTORE + Op.PUSH1[0x4] + Op.DUP2 + Op.MSTORE + Op.CALLER + Op.DUP2
        + Op.PUSH1[0x20] + Op.ADD + Op.MSTORE + Op.PUSH1[0x40] + Op.MLOAD + Op.DUP2
        + Op.PUSH1[0x40] + Op.ADD + Op.MSTORE + Op.PUSH1[0x0] + Op.DUP2
        + Op.PUSH1[0x60] + Op.ADD + Op.MSTORE + Op.DUP1 + Op.SWAP1 + Op.POP + Op.SHA3
        + Op.SLOAD + Op.SUB + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.MSIZE + Op.SWAP1
        + Op.MSIZE + Op.ADD + Op.PUSH1[0x0] + Op.SWAP1 + Op.MSTORE + Op.PUSH1[0x4]
        + Op.DUP2 + Op.MSTORE + Op.CALLER + Op.DUP2 + Op.PUSH1[0x20] + Op.ADD
        + Op.MSTORE + Op.PUSH1[0x40] + Op.MLOAD + Op.DUP2 + Op.PUSH1[0x40] + Op.ADD
        + Op.MSTORE + Op.PUSH1[0x0] + Op.DUP2 + Op.PUSH1[0x60] + Op.ADD + Op.MSTORE
        + Op.DUP1 + Op.SWAP1 + Op.POP + Op.SHA3 + Op.SSTORE + Op.PUSH1[0x80]
        + Op.MLOAD + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.MSIZE + Op.SWAP1 + Op.MSIZE
        + Op.ADD + Op.PUSH1[0x0] + Op.SWAP1 + Op.MSTORE + Op.PUSH1[0x4] + Op.DUP2
        + Op.MSTORE + Op.CALLER + Op.DUP2 + Op.PUSH1[0x20] + Op.ADD + Op.MSTORE
        + Op.PUSH1[0x40] + Op.MLOAD + Op.DUP2 + Op.PUSH1[0x40] + Op.ADD + Op.MSTORE
        + Op.PUSH1[0x1] + Op.DUP2 + Op.PUSH1[0x60] + Op.ADD + Op.MSTORE + Op.DUP1
        + Op.SWAP1 + Op.POP + Op.SHA3 + Op.SLOAD + Op.ADD + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.MSIZE + Op.SWAP1 + Op.MSIZE + Op.ADD + Op.PUSH1[0x0]
        + Op.SWAP1 + Op.MSTORE + Op.PUSH1[0x4] + Op.DUP2 + Op.MSTORE + Op.CALLER
        + Op.DUP2 + Op.PUSH1[0x20] + Op.ADD + Op.MSTORE + Op.PUSH1[0x40] + Op.MLOAD
        + Op.DUP2 + Op.PUSH1[0x40] + Op.ADD + Op.MSTORE + Op.PUSH1[0x1] + Op.DUP2
        + Op.PUSH1[0x60] + Op.ADD + Op.MSTORE + Op.DUP1 + Op.SWAP1 + Op.POP + Op.SHA3
        + Op.SSTORE + Op.JUMPDEST + Op.PUSH2[0x997] + Op.JUMP + Op.JUMPDEST
        + Op.PUSH1[0x15] + Op.PUSH2[0x560] + Op.MSTORE + Op.PUSH1[0x20]
        + Op.PUSH2[0x560] + Op.RETURN + Op.JUMPDEST + Op.PUSH1[0x1c] + Op.PUSH1[0xc0]
        + Op.MSIZE + Op.SWAP1 + Op.MSIZE + Op.ADD + Op.PUSH1[0x0] + Op.SWAP1
        + Op.MSTORE + Op.ADD + Op.CALLER + Op.DUP2 + Op.MSTORE + Op.PUSH1[0x2]
        + Op.PUSH1[0x20] + Op.DUP3 + Op.ADD + Op.MSTORE + Op.PUSH1[0xa0] + Op.MLOAD
        + Op.PUSH1[0x40] + Op.DUP3 + Op.ADD + Op.MSTORE + Op.PUSH1[0x80] + Op.MLOAD
        + Op.PUSH1[0x60] + Op.DUP3 + Op.ADD + Op.MSTORE + Op.PUSH2[0x1c0] + Op.MLOAD
        + Op.PUSH1[0x80] + Op.DUP3 + Op.ADD + Op.MSTORE + Op.PUSH1[0x40] + Op.MLOAD
        + Op.PUSH32[0x9463d1cc4aa2db0dc624c996b1846f028d43c48cfc8b9f427f13336e4a732264]
        + Op.PUSH1[0xa0] + Op.DUP4 + Op.LOG2 + Op.POP + Op.PUSH2[0x1c0] + Op.MLOAD
        + Op.PUSH2[0x580] + Op.MSTORE + Op.PUSH1[0x20] + Op.PUSH2[0x580] + Op.RETURN
        + Op.JUMPDEST + Op.PUSH1[0x0] + Op.PUSH2[0x5a0] + Op.MSTORE + Op.PUSH1[0x20]
        + Op.PUSH2[0x5a0] + Op.RETURN + Op.JUMPDEST + Op.PUSH4[0x9998bd00] + Op.DUP2
        + Op.EQ + Op.ISZERO + Op.PUSH2[0x1733] + Op.JUMPI + Op.CALLDATASIZE + Op.MSIZE
        + Op.SWAP1 + Op.MSIZE + Op.ADD + Op.PUSH1[0x0] + Op.SWAP1 + Op.MSTORE
        + Op.CALLDATASIZE + Op.PUSH1[0x4] + Op.DUP3 + Op.CALLDATACOPY + Op.PUSH1[0x4]
        + Op.CALLDATALOAD + Op.PUSH2[0x5e0] + Op.MSTORE + Op.PUSH1[0x24]
        + Op.CALLDATALOAD + Op.PUSH1[0x20] + Op.DUP3 + Op.ADD + Op.ADD
        + Op.PUSH2[0x600] + Op.MSTORE + Op.POP + Op.CALLVALUE + Op.PUSH2[0x620]
        + Op.MSTORE + Op.PUSH1[0x0] + Op.PUSH2[0x640] + Op.MSTORE + Op.JUMPDEST
        + Op.PUSH1[0x20] + Op.PUSH2[0x600] + Op.MLOAD + Op.SUB + Op.MLOAD
        + Op.PUSH2[0x640] + Op.MLOAD + Op.SLT + Op.ISZERO + Op.PUSH2[0x170a]
        + Op.JUMPI + Op.PUSH2[0x640] + Op.MLOAD + Op.PUSH1[0x20] + Op.MUL
        + Op.PUSH2[0x600] + Op.MLOAD + Op.ADD + Op.MLOAD + Op.PUSH2[0x1c0] + Op.MSTORE
        + Op.PUSH1[0x8] + Op.PUSH2[0x1c0] + Op.MLOAD + Op.MUL
        + Op.PUSH21[0xe0000000000000000000000000000000000000006] + Op.ADD + Op.SLOAD
        + Op.NUMBER + Op.SGT + Op.ISZERO + Op.ISZERO + Op.PUSH2[0xa9d] + Op.JUMPI
        + Op.PUSH1[0x16] + Op.PUSH2[0x660] + Op.MSTORE + Op.PUSH1[0x20]
        + Op.PUSH2[0x660] + Op.RETURN + Op.JUMPDEST + Op.PUSH1[0x8] + Op.PUSH2[0x1c0]
        + Op.MLOAD + Op.MUL + Op.PUSH21[0xe0000000000000000000000000000000000000002]
        + Op.ADD + Op.SLOAD + Op.PUSH1[0x40] + Op.MSTORE + Op.PUSH1[0xc]
        + Op.PUSH1[0x40] + Op.MLOAD + Op.MUL + Op.PUSH1[0x2] + Op.ADD + Op.SLOAD
        + Op.PUSH2[0x680] + Op.MSTORE + Op.PUSH1[0xc] + Op.PUSH1[0x40] + Op.MLOAD
        + Op.MUL + Op.PUSH1[0x3] + Op.ADD + Op.SLOAD + Op.PUSH2[0x6a0] + Op.MSTORE
        + Op.PUSH1[0xc] + Op.PUSH1[0x40] + Op.MLOAD + Op.MUL + Op.PUSH1[0x4] + Op.ADD
        + Op.SLOAD + Op.PUSH2[0x6c0] + Op.MSTORE + Op.PUSH1[0xc] + Op.PUSH1[0x40]
        + Op.MLOAD + Op.MUL + Op.PUSH1[0x5] + Op.ADD + Op.SLOAD + Op.PUSH2[0x6e0]
        + Op.MSTORE + Op.PUSH1[0x8] + Op.PUSH2[0x1c0] + Op.MLOAD + Op.MUL
        + Op.PUSH21[0xe0000000000000000000000000000000000000001] + Op.ADD + Op.SLOAD
        + Op.PUSH2[0x700] + Op.MSTORE + Op.PUSH1[0x8] + Op.PUSH2[0x1c0] + Op.MLOAD
        + Op.MUL + Op.PUSH21[0xe0000000000000000000000000000000000000003] + Op.ADD
        + Op.SLOAD + Op.PUSH1[0x80] + Op.MSTORE + Op.PUSH1[0x8] + Op.PUSH2[0x1c0]
        + Op.MLOAD + Op.MUL + Op.PUSH21[0xe0000000000000000000000000000000000000004]
        + Op.ADD + Op.SLOAD + Op.PUSH1[0xa0] + Op.MSTORE + Op.PUSH1[0x8]
        + Op.PUSH2[0x1c0] + Op.MLOAD + Op.MUL
        + Op.PUSH21[0xe0000000000000000000000000000000000000005] + Op.ADD + Op.SLOAD
        + Op.PUSH2[0x720] + Op.MSTORE + Op.PUSH1[0x1] + Op.PUSH2[0x700] + Op.MLOAD
        + Op.EQ + Op.ISZERO + Op.PUSH2[0x110e] + Op.JUMPI + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.MSIZE + Op.SWAP1 + Op.MSIZE + Op.ADD + Op.PUSH1[0x0]
        + Op.SWAP1 + Op.MSTORE + Op.PUSH1[0x4] + Op.DUP2 + Op.MSTORE + Op.CALLER
        + Op.DUP2 + Op.PUSH1[0x20] + Op.ADD + Op.MSTORE + Op.PUSH1[0x40] + Op.MLOAD
        + Op.DUP2 + Op.PUSH1[0x40] + Op.ADD + Op.MSTORE + Op.PUSH1[0x0] + Op.DUP2
        + Op.PUSH1[0x60] + Op.ADD + Op.MSTORE + Op.DUP1 + Op.SWAP1 + Op.POP + Op.SHA3
        + Op.SLOAD + Op.PUSH2[0x400] + Op.MSTORE + Op.PUSH1[0x0] + Op.PUSH2[0x400]
        + Op.MLOAD + Op.SGT + Op.ISZERO + Op.PUSH2[0x10fc] + Op.JUMPI + Op.PUSH1[0x80]
        + Op.MLOAD + Op.PUSH2[0x400] + Op.MLOAD + Op.PUSH2[0x5e0] + Op.MLOAD + Op.DUP1
        + Op.DUP3 + Op.SLT + Op.ISZERO + Op.PUSH2[0xbe0] + Op.JUMPI + Op.DUP2
        + Op.PUSH2[0xbe2] + Op.JUMP + Op.JUMPDEST + Op.DUP1 + Op.JUMPDEST + Op.SWAP1
        + Op.POP + Op.SWAP1 + Op.POP + Op.DUP1 + Op.DUP3 + Op.SLT + Op.ISZERO
        + Op.PUSH2[0xbf4] + Op.JUMPI + Op.DUP2 + Op.PUSH2[0xbf6] + Op.JUMP
        + Op.JUMPDEST + Op.DUP1 + Op.JUMPDEST + Op.SWAP1 + Op.POP + Op.SWAP1 + Op.POP
        + Op.PUSH2[0x760] + Op.MSTORE + Op.PUSH2[0x6a0] + Op.MLOAD + Op.PUSH1[0xa]
        + Op.EXP + Op.PUSH2[0x6c0] + Op.MLOAD + Op.MUL + Op.PUSH8[0xde0b6b3a7640000]
        + Op.PUSH1[0xa0] + Op.MLOAD + Op.PUSH2[0x760] + Op.MLOAD + Op.MUL + Op.MUL
        + Op.SDIV + Op.PUSH2[0x120] + Op.MSTORE + Op.PUSH2[0x6e0] + Op.MLOAD
        + Op.PUSH2[0x120] + Op.MLOAD + Op.SLT + Op.ISZERO + Op.PUSH2[0xc5b] + Op.JUMPI
        + Op.PUSH1[0x0] + Op.PUSH2[0x620] + Op.MLOAD + Op.SGT + Op.ISZERO
        + Op.PUSH2[0xc4e] + Op.JUMPI + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH2[0x620] + Op.MLOAD + Op.CALLER + Op.PUSH2[0x1388]
        + Op.CALL + Op.POP + Op.JUMPDEST + Op.PUSH1[0xc] + Op.PUSH2[0x800] + Op.MSTORE
        + Op.PUSH1[0x20] + Op.PUSH2[0x800] + Op.RETURN + Op.JUMPDEST + Op.PUSH1[0x80]
        + Op.MLOAD + Op.PUSH2[0x760] + Op.MLOAD + Op.SLT + Op.ISZERO + Op.PUSH2[0xcb0]
        + Op.JUMPI + Op.PUSH2[0x760] + Op.MLOAD + Op.PUSH1[0x8] + Op.PUSH2[0x1c0]
        + Op.MLOAD + Op.MUL + Op.PUSH21[0xe0000000000000000000000000000000000000003]
        + Op.ADD + Op.SLOAD + Op.SUB + Op.PUSH1[0x8] + Op.PUSH2[0x1c0] + Op.MLOAD
        + Op.MUL + Op.PUSH21[0xe0000000000000000000000000000000000000003] + Op.ADD
        + Op.SSTORE + Op.PUSH2[0xfd4] + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x0]
        + Op.PUSH1[0x8] + Op.PUSH2[0x1c0] + Op.MLOAD + Op.MUL
        + Op.PUSH21[0xe0000000000000000000000000000000000000000] + Op.ADD + Op.SSTORE
        + Op.PUSH1[0x0] + Op.PUSH1[0x8] + Op.PUSH2[0x1c0] + Op.MLOAD + Op.MUL
        + Op.PUSH21[0xe0000000000000000000000000000000000000001] + Op.ADD + Op.SSTORE
        + Op.PUSH1[0x0] + Op.PUSH1[0x8] + Op.PUSH2[0x1c0] + Op.MLOAD + Op.MUL
        + Op.PUSH21[0xe0000000000000000000000000000000000000002] + Op.ADD + Op.SSTORE
        + Op.PUSH1[0x0] + Op.PUSH1[0x8] + Op.PUSH2[0x1c0] + Op.MLOAD + Op.MUL
        + Op.PUSH21[0xe0000000000000000000000000000000000000003] + Op.ADD + Op.SSTORE
        + Op.PUSH1[0x0] + Op.PUSH1[0x8] + Op.PUSH2[0x1c0] + Op.MLOAD + Op.MUL
        + Op.PUSH21[0xe0000000000000000000000000000000000000004] + Op.ADD + Op.SSTORE
        + Op.PUSH1[0x0] + Op.PUSH1[0x8] + Op.PUSH2[0x1c0] + Op.MLOAD + Op.MUL
        + Op.PUSH21[0xe0000000000000000000000000000000000000005] + Op.ADD + Op.SSTORE
        + Op.PUSH1[0x0] + Op.PUSH1[0x8] + Op.PUSH2[0x1c0] + Op.MLOAD + Op.MUL
        + Op.PUSH21[0xe0000000000000000000000000000000000000006] + Op.ADD + Op.SSTORE
        + Op.PUSH1[0x0] + Op.PUSH1[0x8] + Op.PUSH2[0x1c0] + Op.MLOAD + Op.MUL
        + Op.PUSH21[0xe0000000000000000000000000000000000000007] + Op.ADD + Op.SSTORE
        + Op.PUSH1[0xa0] + Op.PUSH1[0xa0] + Op.MSIZE + Op.SWAP1 + Op.MSIZE + Op.ADD
        + Op.PUSH1[0x0] + Op.SWAP1 + Op.MSTORE + Op.PUSH1[0x0] + Op.DUP2 + Op.MSTORE
        + Op.PUSH1[0x40] + Op.MLOAD + Op.DUP2 + Op.PUSH1[0x20] + Op.ADD + Op.MSTORE
        + Op.PUSH1[0xc] + Op.DUP2 + Op.PUSH1[0x40] + Op.ADD + Op.MSTORE
        + Op.PUSH2[0x1c0] + Op.MLOAD + Op.DUP2 + Op.PUSH1[0x60] + Op.ADD + Op.MSTORE
        + Op.PUSH1[0x2] + Op.DUP2 + Op.PUSH1[0x80] + Op.ADD + Op.MSTORE + Op.DUP1
        + Op.SWAP1 + Op.POP + Op.SHA3 + Op.SLOAD + Op.PUSH2[0x820] + Op.MSTORE
        + Op.PUSH1[0xa0] + Op.PUSH1[0xa0] + Op.MSIZE + Op.SWAP1 + Op.MSIZE + Op.ADD
        + Op.PUSH1[0x0] + Op.SWAP1 + Op.MSTORE + Op.PUSH1[0x0] + Op.DUP2 + Op.MSTORE
        + Op.PUSH1[0x40] + Op.MLOAD + Op.DUP2 + Op.PUSH1[0x20] + Op.ADD + Op.MSTORE
        + Op.PUSH1[0xc] + Op.DUP2 + Op.PUSH1[0x40] + Op.ADD + Op.MSTORE
        + Op.PUSH2[0x1c0] + Op.MLOAD + Op.DUP2 + Op.PUSH1[0x60] + Op.ADD + Op.MSTORE
        + Op.PUSH1[0x1] + Op.DUP2 + Op.PUSH1[0x80] + Op.ADD + Op.MSTORE + Op.DUP1
        + Op.SWAP1 + Op.POP + Op.SHA3 + Op.SLOAD + Op.PUSH2[0x860] + Op.MSTORE
        + Op.PUSH2[0x820] + Op.MLOAD + Op.ISZERO + Op.PUSH2[0xe3a] + Op.JUMPI
        + Op.PUSH2[0x860] + Op.MLOAD + Op.PUSH2[0xe3d] + Op.JUMP + Op.JUMPDEST
        + Op.PUSH1[0x0] + Op.JUMPDEST + Op.ISZERO + Op.PUSH2[0xeb7] + Op.JUMPI
        + Op.PUSH2[0x860] + Op.MLOAD + Op.PUSH1[0xa0] + Op.PUSH1[0xa0] + Op.MSIZE
        + Op.SWAP1 + Op.MSIZE + Op.ADD + Op.PUSH1[0x0] + Op.SWAP1 + Op.MSTORE
        + Op.PUSH1[0x0] + Op.DUP2 + Op.MSTORE + Op.PUSH1[0x40] + Op.MLOAD + Op.DUP2
        + Op.PUSH1[0x20] + Op.ADD + Op.MSTORE + Op.PUSH1[0xc] + Op.DUP2
        + Op.PUSH1[0x40] + Op.ADD + Op.MSTORE + Op.PUSH2[0x820] + Op.MLOAD + Op.DUP2
        + Op.PUSH1[0x60] + Op.ADD + Op.MSTORE + Op.PUSH1[0x1] + Op.DUP2
        + Op.PUSH1[0x80] + Op.ADD + Op.MSTORE + Op.DUP1 + Op.SWAP1 + Op.POP + Op.SHA3
        + Op.SSTORE + Op.PUSH2[0x820] + Op.MLOAD + Op.PUSH1[0xa0] + Op.PUSH1[0xa0]
        + Op.MSIZE + Op.SWAP1 + Op.MSIZE + Op.ADD + Op.PUSH1[0x0] + Op.SWAP1
        + Op.MSTORE + Op.PUSH1[0x0] + Op.DUP2 + Op.MSTORE + Op.PUSH1[0x40] + Op.MLOAD
        + Op.DUP2 + Op.PUSH1[0x20] + Op.ADD + Op.MSTORE + Op.PUSH1[0xc] + Op.DUP2
        + Op.PUSH1[0x40] + Op.ADD + Op.MSTORE + Op.PUSH2[0x860] + Op.MLOAD + Op.DUP2
        + Op.PUSH1[0x60] + Op.ADD + Op.MSTORE + Op.PUSH1[0x2] + Op.DUP2
        + Op.PUSH1[0x80] + Op.ADD + Op.MSTORE + Op.DUP1 + Op.SWAP1 + Op.POP + Op.SHA3
        + Op.SSTORE + Op.PUSH2[0xf06] + Op.JUMP + Op.JUMPDEST + Op.PUSH2[0x820]
        + Op.MLOAD + Op.ISZERO + Op.PUSH2[0xf05] + Op.JUMPI + Op.PUSH2[0x820]
        + Op.MLOAD + Op.PUSH1[0xc] + Op.PUSH1[0x40] + Op.MLOAD + Op.MUL
        + Op.PUSH1[0xb] + Op.ADD + Op.SSTORE + Op.PUSH1[0x0] + Op.PUSH1[0xa0]
        + Op.PUSH1[0xa0] + Op.MSIZE + Op.SWAP1 + Op.MSIZE + Op.ADD + Op.PUSH1[0x0]
        + Op.SWAP1 + Op.MSTORE + Op.PUSH1[0x0] + Op.DUP2 + Op.MSTORE + Op.PUSH1[0x40]
        + Op.MLOAD + Op.DUP2 + Op.PUSH1[0x20] + Op.ADD + Op.MSTORE + Op.PUSH1[0xc]
        + Op.DUP2 + Op.PUSH1[0x40] + Op.ADD + Op.MSTORE + Op.PUSH2[0x820] + Op.MLOAD
        + Op.DUP2 + Op.PUSH1[0x60] + Op.ADD + Op.MSTORE + Op.PUSH1[0x1] + Op.DUP2
        + Op.PUSH1[0x80] + Op.ADD + Op.MSTORE + Op.DUP1 + Op.SWAP1 + Op.POP + Op.SHA3
        + Op.SSTORE + Op.JUMPDEST + Op.JUMPDEST + Op.PUSH2[0x860] + Op.MLOAD
        + Op.ISZERO + Op.PUSH2[0xf46] + Op.JUMPI + Op.PUSH1[0x0] + Op.PUSH1[0xa0]
        + Op.PUSH1[0xa0] + Op.MSIZE + Op.SWAP1 + Op.MSIZE + Op.ADD + Op.PUSH1[0x0]
        + Op.SWAP1 + Op.MSTORE + Op.PUSH1[0x0] + Op.DUP2 + Op.MSTORE + Op.PUSH1[0x40]
        + Op.MLOAD + Op.DUP2 + Op.PUSH1[0x20] + Op.ADD + Op.MSTORE + Op.PUSH1[0xc]
        + Op.DUP2 + Op.PUSH1[0x40] + Op.ADD + Op.MSTORE + Op.PUSH2[0x1c0] + Op.MLOAD
        + Op.DUP2 + Op.PUSH1[0x60] + Op.ADD + Op.MSTORE + Op.PUSH1[0x1] + Op.DUP2
        + Op.PUSH1[0x80] + Op.ADD + Op.MSTORE + Op.DUP1 + Op.SWAP1 + Op.POP + Op.SHA3
        + Op.SSTORE + Op.JUMPDEST + Op.PUSH2[0x820] + Op.MLOAD + Op.ISZERO
        + Op.PUSH2[0xf86] + Op.JUMPI + Op.PUSH1[0x0] + Op.PUSH1[0xa0] + Op.PUSH1[0xa0]
        + Op.MSIZE + Op.SWAP1 + Op.MSIZE + Op.ADD + Op.PUSH1[0x0] + Op.SWAP1
        + Op.MSTORE + Op.PUSH1[0x0] + Op.DUP2 + Op.MSTORE + Op.PUSH1[0x40] + Op.MLOAD
        + Op.DUP2 + Op.PUSH1[0x20] + Op.ADD + Op.MSTORE + Op.PUSH1[0xc] + Op.DUP2
        + Op.PUSH1[0x40] + Op.ADD + Op.MSTORE + Op.PUSH2[0x1c0] + Op.MLOAD + Op.DUP2
        + Op.PUSH1[0x60] + Op.ADD + Op.MSTORE + Op.PUSH1[0x2] + Op.DUP2
        + Op.PUSH1[0x80] + Op.ADD + Op.MSTORE + Op.DUP1 + Op.SWAP1 + Op.POP + Op.SHA3
        + Op.SSTORE + Op.JUMPDEST + Op.PUSH1[0x0] + Op.PUSH1[0xa0] + Op.PUSH1[0xa0]
        + Op.MSIZE + Op.SWAP1 + Op.MSIZE + Op.ADD + Op.PUSH1[0x0] + Op.SWAP1
        + Op.MSTORE + Op.PUSH1[0x0] + Op.DUP2 + Op.MSTORE + Op.PUSH1[0x40] + Op.MLOAD
        + Op.DUP2 + Op.PUSH1[0x20] + Op.ADD + Op.MSTORE + Op.PUSH1[0xc] + Op.DUP2
        + Op.PUSH1[0x40] + Op.ADD + Op.MSTORE + Op.PUSH2[0x1c0] + Op.MLOAD + Op.DUP2
        + Op.PUSH1[0x60] + Op.ADD + Op.MSTORE + Op.PUSH1[0x0] + Op.DUP2
        + Op.PUSH1[0x80] + Op.ADD + Op.MSTORE + Op.DUP1 + Op.SWAP1 + Op.POP + Op.SHA3
        + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0xc] + Op.PUSH1[0x40] + Op.MLOAD
        + Op.MUL + Op.PUSH1[0xa] + Op.ADD + Op.SLOAD + Op.SUB + Op.PUSH1[0xc]
        + Op.PUSH1[0x40] + Op.MLOAD + Op.MUL + Op.PUSH1[0xa] + Op.ADD + Op.SSTORE
        + Op.JUMPDEST + Op.PUSH2[0x760] + Op.MLOAD + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.MSIZE + Op.SWAP1 + Op.MSIZE + Op.ADD + Op.PUSH1[0x0] + Op.SWAP1
        + Op.MSTORE + Op.PUSH1[0x4] + Op.DUP2 + Op.MSTORE + Op.CALLER + Op.DUP2
        + Op.PUSH1[0x20] + Op.ADD + Op.MSTORE + Op.PUSH1[0x40] + Op.MLOAD + Op.DUP2
        + Op.PUSH1[0x40] + Op.ADD + Op.MSTORE + Op.PUSH1[0x0] + Op.DUP2
        + Op.PUSH1[0x60] + Op.ADD + Op.MSTORE + Op.DUP1 + Op.SWAP1 + Op.POP + Op.SHA3
        + Op.SLOAD + Op.SUB + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.MSIZE + Op.SWAP1
        + Op.MSIZE + Op.ADD + Op.PUSH1[0x0] + Op.SWAP1 + Op.MSTORE + Op.PUSH1[0x4]
        + Op.DUP2 + Op.MSTORE + Op.CALLER + Op.DUP2 + Op.PUSH1[0x20] + Op.ADD
        + Op.MSTORE + Op.PUSH1[0x40] + Op.MLOAD + Op.DUP2 + Op.PUSH1[0x40] + Op.ADD
        + Op.MSTORE + Op.PUSH1[0x0] + Op.DUP2 + Op.PUSH1[0x60] + Op.ADD + Op.MSTORE
        + Op.DUP1 + Op.SWAP1 + Op.POP + Op.SHA3 + Op.SSTORE + Op.PUSH2[0x760]
        + Op.MLOAD + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.MSIZE + Op.SWAP1 + Op.MSIZE
        + Op.ADD + Op.PUSH1[0x0] + Op.SWAP1 + Op.MSTORE + Op.PUSH1[0x4] + Op.DUP2
        + Op.MSTORE + Op.PUSH2[0x720] + Op.MLOAD + Op.DUP2 + Op.PUSH1[0x20] + Op.ADD
        + Op.MSTORE + Op.PUSH1[0x40] + Op.MLOAD + Op.DUP2 + Op.PUSH1[0x40] + Op.ADD
        + Op.MSTORE + Op.PUSH1[0x0] + Op.DUP2 + Op.PUSH1[0x60] + Op.ADD + Op.MSTORE
        + Op.DUP1 + Op.SWAP1 + Op.POP + Op.SHA3 + Op.SLOAD + Op.ADD + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.MSIZE + Op.SWAP1 + Op.MSIZE + Op.ADD + Op.PUSH1[0x0]
        + Op.SWAP1 + Op.MSTORE + Op.PUSH1[0x4] + Op.DUP2 + Op.MSTORE + Op.PUSH2[0x720]
        + Op.MLOAD + Op.DUP2 + Op.PUSH1[0x20] + Op.ADD + Op.MSTORE + Op.PUSH1[0x40]
        + Op.MLOAD + Op.DUP2 + Op.PUSH1[0x40] + Op.ADD + Op.MSTORE + Op.PUSH1[0x0]
        + Op.DUP2 + Op.PUSH1[0x60] + Op.ADD + Op.MSTORE + Op.DUP1 + Op.SWAP1 + Op.POP
        + Op.SHA3 + Op.SSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH2[0x120] + Op.MLOAD + Op.CALLER + Op.PUSH2[0x1388]
        + Op.CALL + Op.POP + Op.PUSH1[0x1c] + Op.PUSH1[0xa0] + Op.MSIZE + Op.SWAP1
        + Op.MSIZE + Op.ADD + Op.PUSH1[0x0] + Op.SWAP1 + Op.MSTORE + Op.ADD
        + Op.PUSH1[0x2] + Op.DUP2 + Op.MSTORE + Op.PUSH1[0xa0] + Op.MLOAD
        + Op.PUSH1[0x20] + Op.DUP3 + Op.ADD + Op.MSTORE + Op.PUSH2[0x760] + Op.MLOAD
        + Op.PUSH1[0x40] + Op.DUP3 + Op.ADD + Op.MSTORE + Op.PUSH2[0x1c0] + Op.MLOAD
        + Op.PUSH1[0x60] + Op.DUP3 + Op.ADD + Op.MSTORE + Op.PUSH2[0x720] + Op.MLOAD
        + Op.CALLER + Op.PUSH1[0x40] + Op.MLOAD
        + Op.PUSH32[0xf9fe89f83633cc2eca9b17e1f77422f037cb026eaca4e6a5337fa1595f50a81]
        + Op.PUSH1[0x80] + Op.DUP6 + Op.LOG4 + Op.POP + Op.PUSH2[0x1109] + Op.JUMP
        + Op.JUMPDEST + Op.PUSH1[0xa] + Op.PUSH2[0x9e0] + Op.MSTORE + Op.PUSH1[0x20]
        + Op.PUSH2[0x9e0] + Op.RETURN + Op.JUMPDEST + Op.PUSH2[0x1680] + Op.JUMP
        + Op.JUMPDEST + Op.PUSH1[0x2] + Op.PUSH2[0x700] + Op.MLOAD + Op.EQ + Op.ISZERO
        + Op.PUSH2[0x167f] + Op.JUMPI + Op.PUSH1[0x0] + Op.PUSH2[0x620] + Op.MLOAD
        + Op.SGT + Op.ISZERO + Op.PUSH2[0x1671] + Op.JUMPI + Op.PUSH2[0x6e0]
        + Op.MLOAD + Op.PUSH2[0x620] + Op.MLOAD + Op.SLT + Op.ISZERO
        + Op.PUSH2[0x1160] + Op.JUMPI + Op.PUSH1[0x0] + Op.PUSH2[0x620] + Op.MLOAD
        + Op.SGT + Op.ISZERO + Op.PUSH2[0x1153] + Op.JUMPI + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH2[0x620] + Op.MLOAD
        + Op.CALLER + Op.PUSH2[0x1388] + Op.CALL + Op.POP + Op.JUMPDEST
        + Op.PUSH1[0xc] + Op.PUSH2[0xa00] + Op.MSTORE + Op.PUSH1[0x20]
        + Op.PUSH2[0xa00] + Op.RETURN + Op.JUMPDEST + Op.PUSH2[0x6a0] + Op.MLOAD
        + Op.PUSH1[0xa] + Op.EXP + Op.PUSH2[0x6c0] + Op.MLOAD + Op.MUL
        + Op.PUSH8[0xde0b6b3a7640000] + Op.PUSH1[0xa0] + Op.MLOAD + Op.PUSH1[0x80]
        + Op.MLOAD + Op.MUL + Op.MUL + Op.SDIV + Op.PUSH2[0xa20] + Op.MSTORE
        + Op.PUSH2[0x620] + Op.MLOAD + Op.PUSH2[0xa20] + Op.MLOAD + Op.DUP1 + Op.DUP3
        + Op.SLT + Op.ISZERO + Op.PUSH2[0x1198] + Op.JUMPI + Op.DUP2
        + Op.PUSH2[0x119a] + Op.JUMP + Op.JUMPDEST + Op.DUP1 + Op.JUMPDEST + Op.SWAP1
        + Op.POP + Op.SWAP1 + Op.POP + Op.PUSH2[0x120] + Op.MSTORE + Op.PUSH2[0xa20]
        + Op.MLOAD + Op.PUSH2[0x120] + Op.MLOAD + Op.SLT + Op.ISZERO
        + Op.PUSH2[0x121b] + Op.JUMPI + Op.PUSH8[0xde0b6b3a7640000] + Op.PUSH1[0xa0]
        + Op.MLOAD + Op.PUSH2[0x6a0] + Op.MLOAD + Op.PUSH1[0xa] + Op.EXP
        + Op.PUSH2[0x6c0] + Op.MLOAD + Op.MUL + Op.PUSH2[0x120] + Op.MLOAD + Op.MUL
        + Op.SDIV + Op.SDIV + Op.PUSH2[0x760] + Op.MSTORE + Op.PUSH2[0x760] + Op.MLOAD
        + Op.PUSH1[0x8] + Op.PUSH2[0x1c0] + Op.MLOAD + Op.MUL
        + Op.PUSH21[0xe0000000000000000000000000000000000000003] + Op.ADD + Op.SLOAD
        + Op.SUB + Op.PUSH1[0x8] + Op.PUSH2[0x1c0] + Op.MLOAD + Op.MUL
        + Op.PUSH21[0xe0000000000000000000000000000000000000003] + Op.ADD + Op.SSTORE
        + Op.PUSH2[0x1546] + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x80] + Op.MLOAD
        + Op.PUSH2[0x760] + Op.MSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x8]
        + Op.PUSH2[0x1c0] + Op.MLOAD + Op.MUL
        + Op.PUSH21[0xe0000000000000000000000000000000000000000] + Op.ADD + Op.SSTORE
        + Op.PUSH1[0x0] + Op.PUSH1[0x8] + Op.PUSH2[0x1c0] + Op.MLOAD + Op.MUL
        + Op.PUSH21[0xe0000000000000000000000000000000000000001] + Op.ADD + Op.SSTORE
        + Op.PUSH1[0x0] + Op.PUSH1[0x8] + Op.PUSH2[0x1c0] + Op.MLOAD + Op.MUL
        + Op.PUSH21[0xe0000000000000000000000000000000000000002] + Op.ADD + Op.SSTORE
        + Op.PUSH1[0x0] + Op.PUSH1[0x8] + Op.PUSH2[0x1c0] + Op.MLOAD + Op.MUL
        + Op.PUSH21[0xe0000000000000000000000000000000000000003] + Op.ADD + Op.SSTORE
        + Op.PUSH1[0x0] + Op.PUSH1[0x8] + Op.PUSH2[0x1c0] + Op.MLOAD + Op.MUL
        + Op.PUSH21[0xe0000000000000000000000000000000000000004] + Op.ADD + Op.SSTORE
        + Op.PUSH1[0x0] + Op.PUSH1[0x8] + Op.PUSH2[0x1c0] + Op.MLOAD + Op.MUL
        + Op.PUSH21[0xe0000000000000000000000000000000000000005] + Op.ADD + Op.SSTORE
        + Op.PUSH1[0x0] + Op.PUSH1[0x8] + Op.PUSH2[0x1c0] + Op.MLOAD + Op.MUL
        + Op.PUSH21[0xe0000000000000000000000000000000000000006] + Op.ADD + Op.SSTORE
        + Op.PUSH1[0x0] + Op.PUSH1[0x8] + Op.PUSH2[0x1c0] + Op.MLOAD + Op.MUL
        + Op.PUSH21[0xe0000000000000000000000000000000000000007] + Op.ADD + Op.SSTORE
        + Op.PUSH1[0xa0] + Op.PUSH1[0xa0] + Op.MSIZE + Op.SWAP1 + Op.MSIZE + Op.ADD
        + Op.PUSH1[0x0] + Op.SWAP1 + Op.MSTORE + Op.PUSH1[0x0] + Op.DUP2 + Op.MSTORE
        + Op.PUSH1[0x40] + Op.MLOAD + Op.DUP2 + Op.PUSH1[0x20] + Op.ADD + Op.MSTORE
        + Op.PUSH1[0xc] + Op.DUP2 + Op.PUSH1[0x40] + Op.ADD + Op.MSTORE
        + Op.PUSH2[0x1c0] + Op.MLOAD + Op.DUP2 + Op.PUSH1[0x60] + Op.ADD + Op.MSTORE
        + Op.PUSH1[0x2] + Op.DUP2 + Op.PUSH1[0x80] + Op.ADD + Op.MSTORE + Op.DUP1
        + Op.SWAP1 + Op.POP + Op.SHA3 + Op.SLOAD + Op.PUSH2[0x820] + Op.MSTORE
        + Op.PUSH1[0xa0] + Op.PUSH1[0xa0] + Op.MSIZE + Op.SWAP1 + Op.MSIZE + Op.ADD
        + Op.PUSH1[0x0] + Op.SWAP1 + Op.MSTORE + Op.PUSH1[0x0] + Op.DUP2 + Op.MSTORE
        + Op.PUSH1[0x40] + Op.MLOAD + Op.DUP2 + Op.PUSH1[0x20] + Op.ADD + Op.MSTORE
        + Op.PUSH1[0xc] + Op.DUP2 + Op.PUSH1[0x40] + Op.ADD + Op.MSTORE
        + Op.PUSH2[0x1c0] + Op.MLOAD + Op.DUP2 + Op.PUSH1[0x60] + Op.ADD + Op.MSTORE
        + Op.PUSH1[0x1] + Op.DUP2 + Op.PUSH1[0x80] + Op.ADD + Op.MSTORE + Op.DUP1
        + Op.SWAP1 + Op.POP + Op.SHA3 + Op.SLOAD + Op.PUSH2[0x860] + Op.MSTORE
        + Op.PUSH2[0x820] + Op.MLOAD + Op.ISZERO + Op.PUSH2[0x13ac] + Op.JUMPI
        + Op.PUSH2[0x860] + Op.MLOAD + Op.PUSH2[0x13af] + Op.JUMP + Op.JUMPDEST
        + Op.PUSH1[0x0] + Op.JUMPDEST + Op.ISZERO + Op.PUSH2[0x1429] + Op.JUMPI
        + Op.PUSH2[0x860] + Op.MLOAD + Op.PUSH1[0xa0] + Op.PUSH1[0xa0] + Op.MSIZE
        + Op.SWAP1 + Op.MSIZE + Op.ADD + Op.PUSH1[0x0] + Op.SWAP1 + Op.MSTORE
        + Op.PUSH1[0x0] + Op.DUP2 + Op.MSTORE + Op.PUSH1[0x40] + Op.MLOAD + Op.DUP2
        + Op.PUSH1[0x20] + Op.ADD + Op.MSTORE + Op.PUSH1[0xc] + Op.DUP2
        + Op.PUSH1[0x40] + Op.ADD + Op.MSTORE + Op.PUSH2[0x820] + Op.MLOAD + Op.DUP2
        + Op.PUSH1[0x60] + Op.ADD + Op.MSTORE + Op.PUSH1[0x1] + Op.DUP2
        + Op.PUSH1[0x80] + Op.ADD + Op.MSTORE + Op.DUP1 + Op.SWAP1 + Op.POP + Op.SHA3
        + Op.SSTORE + Op.PUSH2[0x820] + Op.MLOAD + Op.PUSH1[0xa0] + Op.PUSH1[0xa0]
        + Op.MSIZE + Op.SWAP1 + Op.MSIZE + Op.ADD + Op.PUSH1[0x0] + Op.SWAP1
        + Op.MSTORE + Op.PUSH1[0x0] + Op.DUP2 + Op.MSTORE + Op.PUSH1[0x40] + Op.MLOAD
        + Op.DUP2 + Op.PUSH1[0x20] + Op.ADD + Op.MSTORE + Op.PUSH1[0xc] + Op.DUP2
        + Op.PUSH1[0x40] + Op.ADD + Op.MSTORE + Op.PUSH2[0x860] + Op.MLOAD + Op.DUP2
        + Op.PUSH1[0x60] + Op.ADD + Op.MSTORE + Op.PUSH1[0x2] + Op.DUP2
        + Op.PUSH1[0x80] + Op.ADD + Op.MSTORE + Op.DUP1 + Op.SWAP1 + Op.POP + Op.SHA3
        + Op.SSTORE + Op.PUSH2[0x1478] + Op.JUMP + Op.JUMPDEST + Op.PUSH2[0x820]
        + Op.MLOAD + Op.ISZERO + Op.PUSH2[0x1477] + Op.JUMPI + Op.PUSH2[0x820]
        + Op.MLOAD + Op.PUSH1[0xc] + Op.PUSH1[0x40] + Op.MLOAD + Op.MUL
        + Op.PUSH1[0xb] + Op.ADD + Op.SSTORE + Op.PUSH1[0x0] + Op.PUSH1[0xa0]
        + Op.PUSH1[0xa0] + Op.MSIZE + Op.SWAP1 + Op.MSIZE + Op.ADD + Op.PUSH1[0x0]
        + Op.SWAP1 + Op.MSTORE + Op.PUSH1[0x0] + Op.DUP2 + Op.MSTORE + Op.PUSH1[0x40]
        + Op.MLOAD + Op.DUP2 + Op.PUSH1[0x20] + Op.ADD + Op.MSTORE + Op.PUSH1[0xc]
        + Op.DUP2 + Op.PUSH1[0x40] + Op.ADD + Op.MSTORE + Op.PUSH2[0x820] + Op.MLOAD
        + Op.DUP2 + Op.PUSH1[0x60] + Op.ADD + Op.MSTORE + Op.PUSH1[0x1] + Op.DUP2
        + Op.PUSH1[0x80] + Op.ADD + Op.MSTORE + Op.DUP1 + Op.SWAP1 + Op.POP + Op.SHA3
        + Op.SSTORE + Op.JUMPDEST + Op.JUMPDEST + Op.PUSH2[0x860] + Op.MLOAD
        + Op.ISZERO + Op.PUSH2[0x14b8] + Op.JUMPI + Op.PUSH1[0x0] + Op.PUSH1[0xa0]
        + Op.PUSH1[0xa0] + Op.MSIZE + Op.SWAP1 + Op.MSIZE + Op.ADD + Op.PUSH1[0x0]
        + Op.SWAP1 + Op.MSTORE + Op.PUSH1[0x0] + Op.DUP2 + Op.MSTORE + Op.PUSH1[0x40]
        + Op.MLOAD + Op.DUP2 + Op.PUSH1[0x20] + Op.ADD + Op.MSTORE + Op.PUSH1[0xc]
        + Op.DUP2 + Op.PUSH1[0x40] + Op.ADD + Op.MSTORE + Op.PUSH2[0x1c0] + Op.MLOAD
        + Op.DUP2 + Op.PUSH1[0x60] + Op.ADD + Op.MSTORE + Op.PUSH1[0x1] + Op.DUP2
        + Op.PUSH1[0x80] + Op.ADD + Op.MSTORE + Op.DUP1 + Op.SWAP1 + Op.POP + Op.SHA3
        + Op.SSTORE + Op.JUMPDEST + Op.PUSH2[0x820] + Op.MLOAD + Op.ISZERO
        + Op.PUSH2[0x14f8] + Op.JUMPI + Op.PUSH1[0x0] + Op.PUSH1[0xa0]
        + Op.PUSH1[0xa0] + Op.MSIZE + Op.SWAP1 + Op.MSIZE + Op.ADD + Op.PUSH1[0x0]
        + Op.SWAP1 + Op.MSTORE + Op.PUSH1[0x0] + Op.DUP2 + Op.MSTORE + Op.PUSH1[0x40]
        + Op.MLOAD + Op.DUP2 + Op.PUSH1[0x20] + Op.ADD + Op.MSTORE + Op.PUSH1[0xc]
        + Op.DUP2 + Op.PUSH1[0x40] + Op.ADD + Op.MSTORE + Op.PUSH2[0x1c0] + Op.MLOAD
        + Op.DUP2 + Op.PUSH1[0x60] + Op.ADD + Op.MSTORE + Op.PUSH1[0x2] + Op.DUP2
        + Op.PUSH1[0x80] + Op.ADD + Op.MSTORE + Op.DUP1 + Op.SWAP1 + Op.POP + Op.SHA3
        + Op.SSTORE + Op.JUMPDEST + Op.PUSH1[0x0] + Op.PUSH1[0xa0] + Op.PUSH1[0xa0]
        + Op.MSIZE + Op.SWAP1 + Op.MSIZE + Op.ADD + Op.PUSH1[0x0] + Op.SWAP1
        + Op.MSTORE + Op.PUSH1[0x0] + Op.DUP2 + Op.MSTORE + Op.PUSH1[0x40] + Op.MLOAD
        + Op.DUP2 + Op.PUSH1[0x20] + Op.ADD + Op.MSTORE + Op.PUSH1[0xc] + Op.DUP2
        + Op.PUSH1[0x40] + Op.ADD + Op.MSTORE + Op.PUSH2[0x1c0] + Op.MLOAD + Op.DUP2
        + Op.PUSH1[0x60] + Op.ADD + Op.MSTORE + Op.PUSH1[0x0] + Op.DUP2
        + Op.PUSH1[0x80] + Op.ADD + Op.MSTORE + Op.DUP1 + Op.SWAP1 + Op.POP + Op.SHA3
        + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0xc] + Op.PUSH1[0x40] + Op.MLOAD
        + Op.MUL + Op.PUSH1[0xa] + Op.ADD + Op.SLOAD + Op.SUB + Op.PUSH1[0xc]
        + Op.PUSH1[0x40] + Op.MLOAD + Op.MUL + Op.PUSH1[0xa] + Op.ADD + Op.SSTORE
        + Op.JUMPDEST + Op.PUSH2[0x760] + Op.MLOAD + Op.PUSH1[0x80] + Op.PUSH1[0x80]
        + Op.MSIZE + Op.SWAP1 + Op.MSIZE + Op.ADD + Op.PUSH1[0x0] + Op.SWAP1
        + Op.MSTORE + Op.PUSH1[0x4] + Op.DUP2 + Op.MSTORE + Op.PUSH2[0x720] + Op.MLOAD
        + Op.DUP2 + Op.PUSH1[0x20] + Op.ADD + Op.MSTORE + Op.PUSH1[0x40] + Op.MLOAD
        + Op.DUP2 + Op.PUSH1[0x40] + Op.ADD + Op.MSTORE + Op.PUSH1[0x1] + Op.DUP2
        + Op.PUSH1[0x60] + Op.ADD + Op.MSTORE + Op.DUP1 + Op.SWAP1 + Op.POP + Op.SHA3
        + Op.SLOAD + Op.SUB + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.MSIZE + Op.SWAP1
        + Op.MSIZE + Op.ADD + Op.PUSH1[0x0] + Op.SWAP1 + Op.MSTORE + Op.PUSH1[0x4]
        + Op.DUP2 + Op.MSTORE + Op.PUSH2[0x720] + Op.MLOAD + Op.DUP2 + Op.PUSH1[0x20]
        + Op.ADD + Op.MSTORE + Op.PUSH1[0x40] + Op.MLOAD + Op.DUP2 + Op.PUSH1[0x40]
        + Op.ADD + Op.MSTORE + Op.PUSH1[0x1] + Op.DUP2 + Op.PUSH1[0x60] + Op.ADD
        + Op.MSTORE + Op.DUP1 + Op.SWAP1 + Op.POP + Op.SHA3 + Op.SSTORE
        + Op.PUSH2[0x760] + Op.MLOAD + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.MSIZE
        + Op.SWAP1 + Op.MSIZE + Op.ADD + Op.PUSH1[0x0] + Op.SWAP1 + Op.MSTORE
        + Op.PUSH1[0x4] + Op.DUP2 + Op.MSTORE + Op.CALLER + Op.DUP2 + Op.PUSH1[0x20]
        + Op.ADD + Op.MSTORE + Op.PUSH1[0x40] + Op.MLOAD + Op.DUP2 + Op.PUSH1[0x40]
        + Op.ADD + Op.MSTORE + Op.PUSH1[0x0] + Op.DUP2 + Op.PUSH1[0x60] + Op.ADD
        + Op.MSTORE + Op.DUP1 + Op.SWAP1 + Op.POP + Op.SHA3 + Op.SLOAD + Op.ADD
        + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.MSIZE + Op.SWAP1 + Op.MSIZE + Op.ADD
        + Op.PUSH1[0x0] + Op.SWAP1 + Op.MSTORE + Op.PUSH1[0x4] + Op.DUP2 + Op.MSTORE
        + Op.CALLER + Op.DUP2 + Op.PUSH1[0x20] + Op.ADD + Op.MSTORE + Op.PUSH1[0x40]
        + Op.MLOAD + Op.DUP2 + Op.PUSH1[0x40] + Op.ADD + Op.MSTORE + Op.PUSH1[0x0]
        + Op.DUP2 + Op.PUSH1[0x60] + Op.ADD + Op.MSTORE + Op.DUP1 + Op.SWAP1 + Op.POP
        + Op.SHA3 + Op.SSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH2[0x120] + Op.MLOAD + Op.PUSH2[0x720] + Op.MLOAD
        + Op.PUSH2[0x1388] + Op.CALL + Op.POP + Op.PUSH1[0x1c] + Op.PUSH1[0xa0]
        + Op.MSIZE + Op.SWAP1 + Op.MSIZE + Op.ADD + Op.PUSH1[0x0] + Op.SWAP1
        + Op.MSTORE + Op.ADD + Op.PUSH1[0x1] + Op.DUP2 + Op.MSTORE + Op.PUSH1[0xa0]
        + Op.MLOAD + Op.PUSH1[0x20] + Op.DUP3 + Op.ADD + Op.MSTORE + Op.PUSH2[0x760]
        + Op.MLOAD + Op.PUSH1[0x40] + Op.DUP3 + Op.ADD + Op.MSTORE + Op.PUSH2[0x1c0]
        + Op.MLOAD + Op.PUSH1[0x60] + Op.DUP3 + Op.ADD + Op.MSTORE + Op.PUSH2[0x720]
        + Op.MLOAD + Op.CALLER + Op.PUSH1[0x40] + Op.MLOAD
        + Op.PUSH32[0xf9fe89f83633cc2eca9b17e1f77422f037cb026eaca4e6a5337fa1595f50a81]
        + Op.PUSH1[0x80] + Op.DUP6 + Op.LOG4 + Op.POP + Op.PUSH2[0x167e] + Op.JUMP
        + Op.JUMPDEST + Op.PUSH1[0xa] + Op.PUSH2[0xc00] + Op.MSTORE + Op.PUSH1[0x20]
        + Op.PUSH2[0xc00] + Op.RETURN + Op.JUMPDEST + Op.JUMPDEST + Op.JUMPDEST
        + Op.PUSH1[0xa0] + Op.MLOAD + Op.PUSH1[0xc] + Op.PUSH1[0x40] + Op.MLOAD
        + Op.MUL + Op.PUSH1[0x7] + Op.ADD + Op.SSTORE + Op.PUSH1[0x1c]
        + Op.PUSH1[0xa0] + Op.MSIZE + Op.SWAP1 + Op.MSIZE + Op.ADD + Op.PUSH1[0x0]
        + Op.SWAP1 + Op.MSTORE + Op.ADD + Op.PUSH2[0x700] + Op.MLOAD + Op.DUP2
        + Op.MSTORE + Op.PUSH1[0xa0] + Op.MLOAD + Op.PUSH1[0x20] + Op.DUP3 + Op.ADD
        + Op.MSTORE + Op.PUSH2[0x760] + Op.MLOAD + Op.PUSH1[0x40] + Op.DUP3 + Op.ADD
        + Op.MSTORE + Op.TIMESTAMP + Op.PUSH1[0x60] + Op.DUP3 + Op.ADD + Op.MSTORE
        + Op.PUSH1[0x40] + Op.MLOAD
        + Op.PUSH32[0x50944f09ce56f9f0e2cb67683c9b451049c39f60452b850b169148f3daa51ed6]
        + Op.PUSH1[0x80] + Op.DUP4 + Op.LOG2 + Op.POP + Op.PUSH2[0x760] + Op.MLOAD
        + Op.PUSH2[0x5e0] + Op.MLOAD + Op.SUB + Op.PUSH2[0x5e0] + Op.MSTORE
        + Op.PUSH2[0x120] + Op.MLOAD + Op.PUSH2[0x620] + Op.MLOAD + Op.SUB
        + Op.PUSH2[0x620] + Op.MSTORE + Op.PUSH1[0x1] + Op.PUSH2[0x640] + Op.MLOAD
        + Op.ADD + Op.PUSH2[0x640] + Op.MSTORE + Op.PUSH2[0xa46] + Op.JUMP
        + Op.JUMPDEST + Op.PUSH2[0x620] + Op.MLOAD + Op.ISZERO + Op.PUSH2[0x1726]
        + Op.JUMPI + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH2[0x620] + Op.MLOAD + Op.CALLER + Op.PUSH2[0x1388] + Op.CALL + Op.POP
        + Op.JUMPDEST + Op.PUSH1[0x1] + Op.PUSH2[0xc20] + Op.MSTORE + Op.PUSH1[0x20]
        + Op.PUSH2[0xc20] + Op.RETURN + Op.JUMPDEST + Op.PUSH4[0x34a501c7] + Op.DUP2
        + Op.EQ + Op.ISZERO + Op.PUSH2[0x185b] + Op.JUMPI + Op.PUSH1[0x4]
        + Op.CALLDATALOAD + Op.PUSH1[0x80] + Op.MSTORE + Op.PUSH1[0x24]
        + Op.CALLDATALOAD + Op.PUSH1[0x40] + Op.MSTORE + Op.PUSH1[0x1c]
        + Op.PUSH1[0x84] + Op.MSIZE + Op.SWAP1 + Op.MSIZE + Op.ADD + Op.PUSH1[0x0]
        + Op.SWAP1 + Op.MSTORE + Op.ADD + Op.PUSH4[0x27f08b00] + Op.PUSH1[0x1c]
        + Op.DUP3 + Op.SUB + Op.MSTORE + Op.CALLER + Op.PUSH1[0x4] + Op.DUP3 + Op.ADD
        + Op.MSTORE + Op.ADDRESS + Op.PUSH1[0x24] + Op.DUP3 + Op.ADD + Op.MSTORE
        + Op.PUSH1[0x80] + Op.MLOAD + Op.PUSH1[0x44] + Op.DUP3 + Op.ADD + Op.MSTORE
        + Op.PUSH1[0x20] + Op.PUSH2[0xc40] + Op.PUSH1[0x64] + Op.DUP4 + Op.PUSH1[0x0]
        + Op.PUSH1[0xc] + Op.PUSH1[0x40] + Op.MLOAD + Op.MUL + Op.PUSH1[0x2] + Op.ADD
        + Op.SLOAD + Op.PUSH1[0x2d] + Op.GAS + Op.SUB + Op.CALL + Op.POP
        + Op.PUSH2[0xc40] + Op.MLOAD + Op.SWAP1 + Op.POP + Op.ISZERO
        + Op.PUSH2[0x184e] + Op.JUMPI + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.MSIZE
        + Op.SWAP1 + Op.MSIZE + Op.ADD + Op.PUSH1[0x0] + Op.SWAP1 + Op.MSTORE
        + Op.PUSH1[0x4] + Op.DUP2 + Op.MSTORE + Op.CALLER + Op.DUP2 + Op.PUSH1[0x20]
        + Op.ADD + Op.MSTORE + Op.PUSH1[0x40] + Op.MLOAD + Op.DUP2 + Op.PUSH1[0x40]
        + Op.ADD + Op.MSTORE + Op.PUSH1[0x0] + Op.DUP2 + Op.PUSH1[0x60] + Op.ADD
        + Op.MSTORE + Op.DUP1 + Op.SWAP1 + Op.POP + Op.SHA3 + Op.SLOAD
        + Op.PUSH2[0x400] + Op.MSTORE + Op.PUSH1[0x80] + Op.MLOAD + Op.PUSH2[0x400]
        + Op.MLOAD + Op.ADD + Op.PUSH2[0xc80] + Op.MSTORE + Op.PUSH2[0xc80] + Op.MLOAD
        + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.MSIZE + Op.SWAP1 + Op.MSIZE + Op.ADD
        + Op.PUSH1[0x0] + Op.SWAP1 + Op.MSTORE + Op.PUSH1[0x4] + Op.DUP2 + Op.MSTORE
        + Op.CALLER + Op.DUP2 + Op.PUSH1[0x20] + Op.ADD + Op.MSTORE + Op.PUSH1[0x40]
        + Op.MLOAD + Op.DUP2 + Op.PUSH1[0x40] + Op.ADD + Op.MSTORE + Op.PUSH1[0x0]
        + Op.DUP2 + Op.PUSH1[0x60] + Op.ADD + Op.MSTORE + Op.DUP1 + Op.SWAP1 + Op.POP
        + Op.SHA3 + Op.SSTORE + Op.PUSH1[0x1c] + Op.PUSH1[0x40] + Op.MSIZE + Op.SWAP1
        + Op.MSIZE + Op.ADD + Op.PUSH1[0x0] + Op.SWAP1 + Op.MSTORE + Op.ADD
        + Op.PUSH1[0x80] + Op.MLOAD + Op.DUP2 + Op.MSTORE + Op.CALLER + Op.PUSH1[0x40]
        + Op.MLOAD
        + Op.PUSH32[0x301cd746dbb5e7f9ade2bcd9e8a849b968bfcc222de48d2086ba200184acc83d]
        + Op.PUSH1[0x20] + Op.DUP5 + Op.LOG3 + Op.POP + Op.PUSH2[0xc80] + Op.MLOAD
        + Op.PUSH2[0xcc0] + Op.MSTORE + Op.PUSH1[0x20] + Op.PUSH2[0xcc0] + Op.RETURN
        + Op.JUMPDEST + Op.PUSH1[0x0] + Op.PUSH2[0xce0] + Op.MSTORE + Op.PUSH1[0x20]
        + Op.PUSH2[0xce0] + Op.RETURN + Op.JUMPDEST + Op.PUSH4[0xe1ed3ad3] + Op.DUP2
        + Op.EQ + Op.ISZERO + Op.PUSH2[0x1982] + Op.JUMPI + Op.PUSH1[0x4]
        + Op.CALLDATALOAD + Op.PUSH1[0x80] + Op.MSTORE + Op.PUSH1[0x24]
        + Op.CALLDATALOAD + Op.PUSH1[0x40] + Op.MSTORE + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.MSIZE + Op.SWAP1 + Op.MSIZE + Op.ADD + Op.PUSH1[0x0]
        + Op.SWAP1 + Op.MSTORE + Op.PUSH1[0x4] + Op.DUP2 + Op.MSTORE + Op.CALLER
        + Op.DUP2 + Op.PUSH1[0x20] + Op.ADD + Op.MSTORE + Op.PUSH1[0x40] + Op.MLOAD
        + Op.DUP2 + Op.PUSH1[0x40] + Op.ADD + Op.MSTORE + Op.PUSH1[0x0] + Op.DUP2
        + Op.PUSH1[0x60] + Op.ADD + Op.MSTORE + Op.DUP1 + Op.SWAP1 + Op.POP + Op.SHA3
        + Op.SLOAD + Op.PUSH2[0x400] + Op.MSTORE + Op.PUSH1[0x80] + Op.MLOAD
        + Op.PUSH2[0x400] + Op.MLOAD + Op.SLT + Op.ISZERO + Op.ISZERO
        + Op.PUSH2[0x1975] + Op.JUMPI + Op.PUSH1[0x80] + Op.MLOAD + Op.PUSH2[0x400]
        + Op.MLOAD + Op.SUB + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.MSIZE + Op.SWAP1
        + Op.MSIZE + Op.ADD + Op.PUSH1[0x0] + Op.SWAP1 + Op.MSTORE + Op.PUSH1[0x4]
        + Op.DUP2 + Op.MSTORE + Op.CALLER + Op.DUP2 + Op.PUSH1[0x20] + Op.ADD
        + Op.MSTORE + Op.PUSH1[0x40] + Op.MLOAD + Op.DUP2 + Op.PUSH1[0x40] + Op.ADD
        + Op.MSTORE + Op.PUSH1[0x0] + Op.DUP2 + Op.PUSH1[0x60] + Op.ADD + Op.MSTORE
        + Op.DUP1 + Op.SWAP1 + Op.POP + Op.SHA3 + Op.SSTORE + Op.PUSH1[0x1c]
        + Op.PUSH1[0x64] + Op.MSIZE + Op.SWAP1 + Op.MSIZE + Op.ADD + Op.PUSH1[0x0]
        + Op.SWAP1 + Op.MSTORE + Op.ADD + Op.PUSH4[0x86744558] + Op.PUSH1[0x1c]
        + Op.DUP3 + Op.SUB + Op.MSTORE + Op.CALLER + Op.PUSH1[0x4] + Op.DUP3 + Op.ADD
        + Op.MSTORE + Op.PUSH1[0x80] + Op.MLOAD + Op.PUSH1[0x24] + Op.DUP3 + Op.ADD
        + Op.MSTORE + Op.PUSH1[0x20] + Op.PUSH2[0xd60] + Op.PUSH1[0x44] + Op.DUP4
        + Op.PUSH1[0x0] + Op.PUSH1[0xc] + Op.PUSH1[0x40] + Op.MLOAD + Op.MUL
        + Op.PUSH1[0x2] + Op.ADD + Op.SLOAD + Op.PUSH1[0x2d] + Op.GAS + Op.SUB
        + Op.CALL + Op.POP + Op.PUSH2[0xd60] + Op.MLOAD + Op.SWAP1 + Op.POP
        + Op.PUSH2[0xd40] + Op.MSTORE + Op.PUSH1[0x1c] + Op.PUSH1[0x40] + Op.MSIZE
        + Op.SWAP1 + Op.MSIZE + Op.ADD + Op.PUSH1[0x0] + Op.SWAP1 + Op.MSTORE + Op.ADD
        + Op.PUSH1[0x80] + Op.MLOAD + Op.DUP2 + Op.MSTORE + Op.CALLER + Op.PUSH1[0x40]
        + Op.MLOAD
        + Op.PUSH32[0xfa4460934f383b326d79dcd4f1e59a17ac8ee9a87312169933e7f68b85c1a8ce]
        + Op.PUSH1[0x20] + Op.DUP5 + Op.LOG3 + Op.POP + Op.PUSH2[0xd40] + Op.MLOAD
        + Op.PUSH2[0xd80] + Op.MSTORE + Op.PUSH1[0x20] + Op.PUSH2[0xd80] + Op.RETURN
        + Op.JUMPDEST + Op.PUSH1[0x0] + Op.PUSH2[0xda0] + Op.MSTORE + Op.PUSH1[0x20]
        + Op.PUSH2[0xda0] + Op.RETURN + Op.JUMPDEST + Op.PUSH4[0x327a22f1] + Op.DUP2
        + Op.EQ + Op.ISZERO + Op.PUSH2[0x1f08] + Op.JUMPI + Op.PUSH1[0x4]
        + Op.CALLDATALOAD + Op.PUSH2[0x1c0] + Op.MSTORE + Op.PUSH1[0x8]
        + Op.PUSH2[0x1c0] + Op.MLOAD + Op.MUL
        + Op.PUSH21[0xe0000000000000000000000000000000000000001] + Op.ADD + Op.SLOAD
        + Op.PUSH2[0x700] + Op.MSTORE + Op.PUSH1[0x8] + Op.PUSH2[0x1c0] + Op.MLOAD
        + Op.MUL + Op.PUSH21[0xe0000000000000000000000000000000000000003] + Op.ADD
        + Op.SLOAD + Op.PUSH1[0x80] + Op.MSTORE + Op.PUSH1[0x8] + Op.PUSH2[0x1c0]
        + Op.MLOAD + Op.MUL + Op.PUSH21[0xe0000000000000000000000000000000000000004]
        + Op.ADD + Op.SLOAD + Op.PUSH1[0xa0] + Op.MSTORE + Op.PUSH1[0x8]
        + Op.PUSH2[0x1c0] + Op.MLOAD + Op.MUL
        + Op.PUSH21[0xe0000000000000000000000000000000000000005] + Op.ADD + Op.SLOAD
        + Op.PUSH2[0x720] + Op.MSTORE + Op.PUSH1[0x8] + Op.PUSH2[0x1c0] + Op.MLOAD
        + Op.MUL + Op.PUSH21[0xe0000000000000000000000000000000000000002] + Op.ADD
        + Op.SLOAD + Op.PUSH1[0x40] + Op.MSTORE + Op.PUSH1[0xc] + Op.PUSH1[0x40]
        + Op.MLOAD + Op.MUL + Op.PUSH1[0x2] + Op.ADD + Op.SLOAD + Op.PUSH2[0x680]
        + Op.MSTORE + Op.PUSH1[0xc] + Op.PUSH1[0x40] + Op.MLOAD + Op.MUL
        + Op.PUSH1[0x3] + Op.ADD + Op.SLOAD + Op.PUSH2[0x6a0] + Op.MSTORE
        + Op.PUSH1[0xc] + Op.PUSH1[0x40] + Op.MLOAD + Op.MUL + Op.PUSH1[0x4] + Op.ADD
        + Op.SLOAD + Op.PUSH2[0x6c0] + Op.MSTORE + Op.PUSH2[0x720] + Op.MLOAD
        + Op.CALLER + Op.EQ + Op.ISZERO + Op.PUSH2[0x1efb] + Op.JUMPI + Op.PUSH1[0x0]
        + Op.PUSH1[0x8] + Op.PUSH2[0x1c0] + Op.MLOAD + Op.MUL
        + Op.PUSH21[0xe0000000000000000000000000000000000000000] + Op.ADD + Op.SSTORE
        + Op.PUSH1[0x0] + Op.PUSH1[0x8] + Op.PUSH2[0x1c0] + Op.MLOAD + Op.MUL
        + Op.PUSH21[0xe0000000000000000000000000000000000000001] + Op.ADD + Op.SSTORE
        + Op.PUSH1[0x0] + Op.PUSH1[0x8] + Op.PUSH2[0x1c0] + Op.MLOAD + Op.MUL
        + Op.PUSH21[0xe0000000000000000000000000000000000000002] + Op.ADD + Op.SSTORE
        + Op.PUSH1[0x0] + Op.PUSH1[0x8] + Op.PUSH2[0x1c0] + Op.MLOAD + Op.MUL
        + Op.PUSH21[0xe0000000000000000000000000000000000000003] + Op.ADD + Op.SSTORE
        + Op.PUSH1[0x0] + Op.PUSH1[0x8] + Op.PUSH2[0x1c0] + Op.MLOAD + Op.MUL
        + Op.PUSH21[0xe0000000000000000000000000000000000000004] + Op.ADD + Op.SSTORE
        + Op.PUSH1[0x0] + Op.PUSH1[0x8] + Op.PUSH2[0x1c0] + Op.MLOAD + Op.MUL
        + Op.PUSH21[0xe0000000000000000000000000000000000000005] + Op.ADD + Op.SSTORE
        + Op.PUSH1[0x0] + Op.PUSH1[0x8] + Op.PUSH2[0x1c0] + Op.MLOAD + Op.MUL
        + Op.PUSH21[0xe0000000000000000000000000000000000000006] + Op.ADD + Op.SSTORE
        + Op.PUSH1[0x0] + Op.PUSH1[0x8] + Op.PUSH2[0x1c0] + Op.MLOAD + Op.MUL
        + Op.PUSH21[0xe0000000000000000000000000000000000000007] + Op.ADD + Op.SSTORE
        + Op.PUSH1[0xa0] + Op.PUSH1[0xa0] + Op.MSIZE + Op.SWAP1 + Op.MSIZE + Op.ADD
        + Op.PUSH1[0x0] + Op.SWAP1 + Op.MSTORE + Op.PUSH1[0x0] + Op.DUP2 + Op.MSTORE
        + Op.PUSH1[0x40] + Op.MLOAD + Op.DUP2 + Op.PUSH1[0x20] + Op.ADD + Op.MSTORE
        + Op.PUSH1[0xc] + Op.DUP2 + Op.PUSH1[0x40] + Op.ADD + Op.MSTORE
        + Op.PUSH2[0x1c0] + Op.MLOAD + Op.DUP2 + Op.PUSH1[0x60] + Op.ADD + Op.MSTORE
        + Op.PUSH1[0x2] + Op.DUP2 + Op.PUSH1[0x80] + Op.ADD + Op.MSTORE + Op.DUP1
        + Op.SWAP1 + Op.POP + Op.SHA3 + Op.SLOAD + Op.PUSH2[0x820] + Op.MSTORE
        + Op.PUSH1[0xa0] + Op.PUSH1[0xa0] + Op.MSIZE + Op.SWAP1 + Op.MSIZE + Op.ADD
        + Op.PUSH1[0x0] + Op.SWAP1 + Op.MSTORE + Op.PUSH1[0x0] + Op.DUP2 + Op.MSTORE
        + Op.PUSH1[0x40] + Op.MLOAD + Op.DUP2 + Op.PUSH1[0x20] + Op.ADD + Op.MSTORE
        + Op.PUSH1[0xc] + Op.DUP2 + Op.PUSH1[0x40] + Op.ADD + Op.MSTORE
        + Op.PUSH2[0x1c0] + Op.MLOAD + Op.DUP2 + Op.PUSH1[0x60] + Op.ADD + Op.MSTORE
        + Op.PUSH1[0x1] + Op.DUP2 + Op.PUSH1[0x80] + Op.ADD + Op.MSTORE + Op.DUP1
        + Op.SWAP1 + Op.POP + Op.SHA3 + Op.SLOAD + Op.PUSH2[0x860] + Op.MSTORE
        + Op.PUSH2[0x820] + Op.MLOAD + Op.ISZERO + Op.PUSH2[0x1c00] + Op.JUMPI
        + Op.PUSH2[0x860] + Op.MLOAD + Op.PUSH2[0x1c03] + Op.JUMP + Op.JUMPDEST
        + Op.PUSH1[0x0] + Op.JUMPDEST + Op.ISZERO + Op.PUSH2[0x1c7d] + Op.JUMPI
        + Op.PUSH2[0x860] + Op.MLOAD + Op.PUSH1[0xa0] + Op.PUSH1[0xa0] + Op.MSIZE
        + Op.SWAP1 + Op.MSIZE + Op.ADD + Op.PUSH1[0x0] + Op.SWAP1 + Op.MSTORE
        + Op.PUSH1[0x0] + Op.DUP2 + Op.MSTORE + Op.PUSH1[0x40] + Op.MLOAD + Op.DUP2
        + Op.PUSH1[0x20] + Op.ADD + Op.MSTORE + Op.PUSH1[0xc] + Op.DUP2
        + Op.PUSH1[0x40] + Op.ADD + Op.MSTORE + Op.PUSH2[0x820] + Op.MLOAD + Op.DUP2
        + Op.PUSH1[0x60] + Op.ADD + Op.MSTORE + Op.PUSH1[0x1] + Op.DUP2
        + Op.PUSH1[0x80] + Op.ADD + Op.MSTORE + Op.DUP1 + Op.SWAP1 + Op.POP + Op.SHA3
        + Op.SSTORE + Op.PUSH2[0x820] + Op.MLOAD + Op.PUSH1[0xa0] + Op.PUSH1[0xa0]
        + Op.MSIZE + Op.SWAP1 + Op.MSIZE + Op.ADD + Op.PUSH1[0x0] + Op.SWAP1
        + Op.MSTORE + Op.PUSH1[0x0] + Op.DUP2 + Op.MSTORE + Op.PUSH1[0x40] + Op.MLOAD
        + Op.DUP2 + Op.PUSH1[0x20] + Op.ADD + Op.MSTORE + Op.PUSH1[0xc] + Op.DUP2
        + Op.PUSH1[0x40] + Op.ADD + Op.MSTORE + Op.PUSH2[0x860] + Op.MLOAD + Op.DUP2
        + Op.PUSH1[0x60] + Op.ADD + Op.MSTORE + Op.PUSH1[0x2] + Op.DUP2
        + Op.PUSH1[0x80] + Op.ADD + Op.MSTORE + Op.DUP1 + Op.SWAP1 + Op.POP + Op.SHA3
        + Op.SSTORE + Op.PUSH2[0x1ccc] + Op.JUMP + Op.JUMPDEST + Op.PUSH2[0x820]
        + Op.MLOAD + Op.ISZERO + Op.PUSH2[0x1ccb] + Op.JUMPI + Op.PUSH2[0x820]
        + Op.MLOAD + Op.PUSH1[0xc] + Op.PUSH1[0x40] + Op.MLOAD + Op.MUL
        + Op.PUSH1[0xb] + Op.ADD + Op.SSTORE + Op.PUSH1[0x0] + Op.PUSH1[0xa0]
        + Op.PUSH1[0xa0] + Op.MSIZE + Op.SWAP1 + Op.MSIZE + Op.ADD + Op.PUSH1[0x0]
        + Op.SWAP1 + Op.MSTORE + Op.PUSH1[0x0] + Op.DUP2 + Op.MSTORE + Op.PUSH1[0x40]
        + Op.MLOAD + Op.DUP2 + Op.PUSH1[0x20] + Op.ADD + Op.MSTORE + Op.PUSH1[0xc]
        + Op.DUP2 + Op.PUSH1[0x40] + Op.ADD + Op.MSTORE + Op.PUSH2[0x820] + Op.MLOAD
        + Op.DUP2 + Op.PUSH1[0x60] + Op.ADD + Op.MSTORE + Op.PUSH1[0x1] + Op.DUP2
        + Op.PUSH1[0x80] + Op.ADD + Op.MSTORE + Op.DUP1 + Op.SWAP1 + Op.POP + Op.SHA3
        + Op.SSTORE + Op.JUMPDEST + Op.JUMPDEST + Op.PUSH2[0x860] + Op.MLOAD
        + Op.ISZERO + Op.PUSH2[0x1d0c] + Op.JUMPI + Op.PUSH1[0x0] + Op.PUSH1[0xa0]
        + Op.PUSH1[0xa0] + Op.MSIZE + Op.SWAP1 + Op.MSIZE + Op.ADD + Op.PUSH1[0x0]
        + Op.SWAP1 + Op.MSTORE + Op.PUSH1[0x0] + Op.DUP2 + Op.MSTORE + Op.PUSH1[0x40]
        + Op.MLOAD + Op.DUP2 + Op.PUSH1[0x20] + Op.ADD + Op.MSTORE + Op.PUSH1[0xc]
        + Op.DUP2 + Op.PUSH1[0x40] + Op.ADD + Op.MSTORE + Op.PUSH2[0x1c0] + Op.MLOAD
        + Op.DUP2 + Op.PUSH1[0x60] + Op.ADD + Op.MSTORE + Op.PUSH1[0x1] + Op.DUP2
        + Op.PUSH1[0x80] + Op.ADD + Op.MSTORE + Op.DUP1 + Op.SWAP1 + Op.POP + Op.SHA3
        + Op.SSTORE + Op.JUMPDEST + Op.PUSH2[0x820] + Op.MLOAD + Op.ISZERO
        + Op.PUSH2[0x1d4c] + Op.JUMPI + Op.PUSH1[0x0] + Op.PUSH1[0xa0]
        + Op.PUSH1[0xa0] + Op.MSIZE + Op.SWAP1 + Op.MSIZE + Op.ADD + Op.PUSH1[0x0]
        + Op.SWAP1 + Op.MSTORE + Op.PUSH1[0x0] + Op.DUP2 + Op.MSTORE + Op.PUSH1[0x40]
        + Op.MLOAD + Op.DUP2 + Op.PUSH1[0x20] + Op.ADD + Op.MSTORE + Op.PUSH1[0xc]
        + Op.DUP2 + Op.PUSH1[0x40] + Op.ADD + Op.MSTORE + Op.PUSH2[0x1c0] + Op.MLOAD
        + Op.DUP2 + Op.PUSH1[0x60] + Op.ADD + Op.MSTORE + Op.PUSH1[0x2] + Op.DUP2
        + Op.PUSH1[0x80] + Op.ADD + Op.MSTORE + Op.DUP1 + Op.SWAP1 + Op.POP + Op.SHA3
        + Op.SSTORE + Op.JUMPDEST + Op.PUSH1[0x0] + Op.PUSH1[0xa0] + Op.PUSH1[0xa0]
        + Op.MSIZE + Op.SWAP1 + Op.MSIZE + Op.ADD + Op.PUSH1[0x0] + Op.SWAP1
        + Op.MSTORE + Op.PUSH1[0x0] + Op.DUP2 + Op.MSTORE + Op.PUSH1[0x40] + Op.MLOAD
        + Op.DUP2 + Op.PUSH1[0x20] + Op.ADD + Op.MSTORE + Op.PUSH1[0xc] + Op.DUP2
        + Op.PUSH1[0x40] + Op.ADD + Op.MSTORE + Op.PUSH2[0x1c0] + Op.MLOAD + Op.DUP2
        + Op.PUSH1[0x60] + Op.ADD + Op.MSTORE + Op.PUSH1[0x0] + Op.DUP2
        + Op.PUSH1[0x80] + Op.ADD + Op.MSTORE + Op.DUP1 + Op.SWAP1 + Op.POP + Op.SHA3
        + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0xc] + Op.PUSH1[0x40] + Op.MLOAD
        + Op.MUL + Op.PUSH1[0xa] + Op.ADD + Op.SLOAD + Op.SUB + Op.PUSH1[0xc]
        + Op.PUSH1[0x40] + Op.MLOAD + Op.MUL + Op.PUSH1[0xa] + Op.ADD + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH2[0x700] + Op.MLOAD + Op.EQ + Op.ISZERO
        + Op.PUSH2[0x1dde] + Op.JUMPI + Op.PUSH8[0xde0b6b3a7640000] + Op.PUSH2[0x6a0]
        + Op.MLOAD + Op.PUSH1[0xa] + Op.EXP + Op.PUSH2[0x6c0] + Op.MLOAD + Op.MUL
        + Op.PUSH1[0xa0] + Op.MLOAD + Op.PUSH1[0x80] + Op.MLOAD + Op.MUL + Op.SDIV
        + Op.MUL + Op.PUSH2[0x120] + Op.MSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH2[0x120] + Op.MLOAD + Op.CALLER
        + Op.PUSH2[0x1388] + Op.CALL + Op.POP + Op.PUSH2[0x1e9c] + Op.JUMP
        + Op.JUMPDEST + Op.PUSH1[0x2] + Op.PUSH2[0x700] + Op.MLOAD + Op.EQ + Op.ISZERO
        + Op.PUSH2[0x1e9b] + Op.JUMPI + Op.PUSH1[0x80] + Op.MLOAD + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.MSIZE + Op.SWAP1 + Op.MSIZE + Op.ADD + Op.PUSH1[0x0]
        + Op.SWAP1 + Op.MSTORE + Op.PUSH1[0x4] + Op.DUP2 + Op.MSTORE + Op.CALLER
        + Op.DUP2 + Op.PUSH1[0x20] + Op.ADD + Op.MSTORE + Op.PUSH1[0x40] + Op.MLOAD
        + Op.DUP2 + Op.PUSH1[0x40] + Op.ADD + Op.MSTORE + Op.PUSH1[0x1] + Op.DUP2
        + Op.PUSH1[0x60] + Op.ADD + Op.MSTORE + Op.DUP1 + Op.SWAP1 + Op.POP + Op.SHA3
        + Op.SLOAD + Op.SUB + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.MSIZE + Op.SWAP1
        + Op.MSIZE + Op.ADD + Op.PUSH1[0x0] + Op.SWAP1 + Op.MSTORE + Op.PUSH1[0x4]
        + Op.DUP2 + Op.MSTORE + Op.CALLER + Op.DUP2 + Op.PUSH1[0x20] + Op.ADD
        + Op.MSTORE + Op.PUSH1[0x40] + Op.MLOAD + Op.DUP2 + Op.PUSH1[0x40] + Op.ADD
        + Op.MSTORE + Op.PUSH1[0x1] + Op.DUP2 + Op.PUSH1[0x60] + Op.ADD + Op.MSTORE
        + Op.DUP1 + Op.SWAP1 + Op.POP + Op.SHA3 + Op.SSTORE + Op.PUSH1[0x80]
        + Op.MLOAD + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.MSIZE + Op.SWAP1 + Op.MSIZE
        + Op.ADD + Op.PUSH1[0x0] + Op.SWAP1 + Op.MSTORE + Op.PUSH1[0x4] + Op.DUP2
        + Op.MSTORE + Op.CALLER + Op.DUP2 + Op.PUSH1[0x20] + Op.ADD + Op.MSTORE
        + Op.PUSH1[0x40] + Op.MLOAD + Op.DUP2 + Op.PUSH1[0x40] + Op.ADD + Op.MSTORE
        + Op.PUSH1[0x0] + Op.DUP2 + Op.PUSH1[0x60] + Op.ADD + Op.MSTORE + Op.DUP1
        + Op.SWAP1 + Op.POP + Op.SHA3 + Op.SLOAD + Op.ADD + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.MSIZE + Op.SWAP1 + Op.MSIZE + Op.ADD + Op.PUSH1[0x0]
        + Op.SWAP1 + Op.MSTORE + Op.PUSH1[0x4] + Op.DUP2 + Op.MSTORE + Op.CALLER
        + Op.DUP2 + Op.PUSH1[0x20] + Op.ADD + Op.MSTORE + Op.PUSH1[0x40] + Op.MLOAD
        + Op.DUP2 + Op.PUSH1[0x40] + Op.ADD + Op.MSTORE + Op.PUSH1[0x0] + Op.DUP2
        + Op.PUSH1[0x60] + Op.ADD + Op.MSTORE + Op.DUP1 + Op.SWAP1 + Op.POP + Op.SHA3
        + Op.SSTORE + Op.JUMPDEST + Op.JUMPDEST + Op.PUSH1[0x1c] + Op.PUSH1[0xa0]
        + Op.MSIZE + Op.SWAP1 + Op.MSIZE + Op.ADD + Op.PUSH1[0x0] + Op.SWAP1
        + Op.MSTORE + Op.ADD + Op.CALLER + Op.DUP2 + Op.MSTORE + Op.PUSH1[0xa0]
        + Op.MLOAD + Op.PUSH1[0x20] + Op.DUP3 + Op.ADD + Op.MSTORE + Op.PUSH1[0x80]
        + Op.MLOAD + Op.PUSH1[0x40] + Op.DUP3 + Op.ADD + Op.MSTORE + Op.PUSH2[0x1c0]
        + Op.MLOAD + Op.PUSH1[0x60] + Op.DUP3 + Op.ADD + Op.MSTORE + Op.PUSH1[0x40]
        + Op.MLOAD
        + Op.PUSH32[0xac6333455d304288767a0f1039d666d16882d10b6ea83693d2556e4c8098001]
        + Op.PUSH1[0x80] + Op.DUP4 + Op.LOG2 + Op.POP + Op.PUSH1[0x1]
        + Op.PUSH2[0xf40] + Op.MSTORE + Op.PUSH1[0x20] + Op.PUSH2[0xf40] + Op.RETURN
        + Op.JUMPDEST + Op.PUSH1[0x0] + Op.PUSH2[0xf60] + Op.MSTORE + Op.PUSH1[0x20]
        + Op.PUSH2[0xf60] + Op.RETURN + Op.JUMPDEST + Op.PUSH4[0xd91e22f4] + Op.DUP2
        + Op.EQ + Op.ISZERO + Op.PUSH2[0x22f0] + Op.JUMPI + Op.PUSH1[0x4]
        + Op.CALLDATALOAD + Op.PUSH2[0xf80] + Op.MSTORE + Op.PUSH1[0x24]
        + Op.CALLDATALOAD + Op.PUSH2[0x680] + Op.MSTORE + Op.PUSH1[0x44]
        + Op.CALLDATALOAD + Op.PUSH2[0x6a0] + Op.MSTORE + Op.PUSH1[0x64]
        + Op.CALLDATALOAD + Op.PUSH2[0x6c0] + Op.MSTORE + Op.PUSH1[0x84]
        + Op.CALLDATALOAD + Op.PUSH2[0x6e0] + Op.MSTORE + Op.PUSH1[0xa4]
        + Op.CALLDATALOAD + Op.PUSH2[0xfa0] + Op.MSTORE + Op.PUSH1[0x1]
        + Op.PUSH21[0x160000000000000000000000000000000000000000] + Op.SLOAD + Op.ADD
        + Op.PUSH2[0xfc0] + Op.MSTORE + Op.PUSH1[0x0] + Op.PUSH2[0xf80] + Op.MLOAD
        + Op.SGT + Op.ISZERO + Op.ISZERO + Op.PUSH2[0x1f76] + Op.JUMPI
        + Op.PUSH1[0x1e] + Op.PUSH2[0xfe0] + Op.MSTORE + Op.PUSH1[0x20]
        + Op.PUSH2[0xfe0] + Op.RETURN + Op.JUMPDEST + Op.PUSH2[0xf80] + Op.MLOAD
        + Op.PUSH21[0xd0000000000000000000000000000000000000000] + Op.ADD + Op.SLOAD
        + Op.ISZERO + Op.PUSH2[0x1fa4] + Op.JUMPI + Op.PUSH1[0x1f] + Op.PUSH2[0x1000]
        + Op.MSTORE + Op.PUSH1[0x20] + Op.PUSH2[0x1000] + Op.RETURN + Op.JUMPDEST
        + Op.PUSH1[0x0] + Op.PUSH2[0x680] + Op.MLOAD + Op.SGT + Op.ISZERO + Op.ISZERO
        + Op.PUSH2[0x1fbe] + Op.JUMPI + Op.PUSH1[0x20] + Op.PUSH2[0x1020] + Op.MSTORE
        + Op.PUSH1[0x20] + Op.PUSH2[0x1020] + Op.RETURN + Op.JUMPDEST + Op.PUSH1[0x0]
        + Op.PUSH2[0xfa0] + Op.MLOAD + Op.SLT + Op.ISZERO + Op.PUSH2[0x1fd7]
        + Op.JUMPI + Op.PUSH1[0x21] + Op.PUSH2[0x1040] + Op.MSTORE + Op.PUSH1[0x20]
        + Op.PUSH2[0x1040] + Op.RETURN + Op.JUMPDEST + Op.PUSH1[0x0] + Op.PUSH2[0x6a0]
        + Op.MLOAD + Op.SLT + Op.ISZERO + Op.PUSH2[0x1ff0] + Op.JUMPI + Op.PUSH1[0x22]
        + Op.PUSH2[0x1060] + Op.MSTORE + Op.PUSH1[0x20] + Op.PUSH2[0x1060] + Op.RETURN
        + Op.JUMPDEST + Op.PUSH1[0x0] + Op.PUSH2[0x6c0] + Op.MLOAD + Op.SLT
        + Op.ISZERO + Op.PUSH2[0x2009] + Op.JUMPI + Op.PUSH1[0x23] + Op.PUSH2[0x1080]
        + Op.MSTORE + Op.PUSH1[0x20] + Op.PUSH2[0x1080] + Op.RETURN + Op.JUMPDEST
        + Op.PUSH1[0x0] + Op.PUSH2[0x6e0] + Op.MLOAD + Op.SLT + Op.ISZERO
        + Op.PUSH2[0x2022] + Op.JUMPI + Op.PUSH1[0x24] + Op.PUSH2[0x10a0] + Op.MSTORE
        + Op.PUSH1[0x20] + Op.PUSH2[0x10a0] + Op.RETURN + Op.JUMPDEST + Op.PUSH1[0x0]
        + Op.PUSH1[0x1c] + Op.PUSH1[0x64] + Op.MSIZE + Op.SWAP1 + Op.MSIZE + Op.ADD
        + Op.PUSH1[0x0] + Op.SWAP1 + Op.MSTORE + Op.ADD + Op.PUSH4[0xc32d01a1]
        + Op.PUSH1[0x1c] + Op.DUP3 + Op.SUB + Op.MSTORE + Op.CALLER + Op.PUSH1[0x4]
        + Op.DUP3 + Op.ADD + Op.MSTORE + Op.ADDRESS + Op.PUSH1[0x24] + Op.DUP3
        + Op.ADD + Op.MSTORE + Op.PUSH1[0x20] + Op.PUSH2[0x10c0] + Op.PUSH1[0x44]
        + Op.DUP4 + Op.PUSH1[0x0] + Op.PUSH2[0x680] + Op.MLOAD + Op.PUSH1[0x2d]
        + Op.GAS + Op.SUB + Op.CALL + Op.POP + Op.PUSH2[0x10c0] + Op.MLOAD + Op.SWAP1
        + Op.POP + Op.EQ + Op.ISZERO + Op.ISZERO + Op.PUSH2[0x2075] + Op.JUMPI
        + Op.PUSH1[0x28] + Op.PUSH2[0x10e0] + Op.MSTORE + Op.PUSH1[0x20]
        + Op.PUSH2[0x10e0] + Op.RETURN + Op.JUMPDEST + Op.PUSH1[0x1] + Op.PUSH1[0x1c]
        + Op.PUSH1[0x64] + Op.MSIZE + Op.SWAP1 + Op.MSIZE + Op.ADD + Op.PUSH1[0x0]
        + Op.SWAP1 + Op.MSTORE + Op.ADD + Op.PUSH4[0x83b58638] + Op.PUSH1[0x1c]
        + Op.DUP3 + Op.SUB + Op.MSTORE + Op.ADDRESS + Op.PUSH1[0x4] + Op.DUP3 + Op.ADD
        + Op.MSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x24] + Op.DUP3 + Op.ADD + Op.MSTORE
        + Op.PUSH1[0x20] + Op.PUSH2[0x1100] + Op.PUSH1[0x44] + Op.DUP4 + Op.PUSH1[0x0]
        + Op.PUSH2[0x680] + Op.MLOAD + Op.PUSH1[0x2d] + Op.GAS + Op.SUB + Op.CALL
        + Op.POP + Op.PUSH2[0x1100] + Op.MLOAD + Op.SWAP1 + Op.POP + Op.EQ + Op.ISZERO
        + Op.ISZERO + Op.PUSH2[0x20c9] + Op.JUMPI + Op.PUSH1[0x29] + Op.PUSH2[0x1120]
        + Op.MSTORE + Op.PUSH1[0x20] + Op.PUSH2[0x1120] + Op.RETURN + Op.JUMPDEST
        + Op.PUSH1[0x0] + Op.PUSH1[0x1c] + Op.PUSH1[0x44] + Op.MSIZE + Op.SWAP1
        + Op.MSIZE + Op.ADD + Op.PUSH1[0x0] + Op.SWAP1 + Op.MSTORE + Op.ADD
        + Op.PUSH4[0x26690247] + Op.PUSH1[0x1c] + Op.DUP3 + Op.SUB + Op.MSTORE
        + Op.ADDRESS + Op.PUSH1[0x4] + Op.DUP3 + Op.ADD + Op.MSTORE + Op.PUSH1[0x20]
        + Op.PUSH2[0x1140] + Op.PUSH1[0x24] + Op.DUP4 + Op.PUSH1[0x0]
        + Op.PUSH2[0x680] + Op.MLOAD + Op.PUSH1[0x2d] + Op.GAS + Op.SUB + Op.CALL
        + Op.POP + Op.PUSH2[0x1140] + Op.MLOAD + Op.SWAP1 + Op.POP + Op.EQ + Op.ISZERO
        + Op.ISZERO + Op.PUSH2[0x2116] + Op.JUMPI + Op.PUSH1[0x2a] + Op.PUSH2[0x1160]
        + Op.MSTORE + Op.PUSH1[0x20] + Op.PUSH2[0x1160] + Op.RETURN + Op.JUMPDEST
        + Op.PUSH1[0x0] + Op.PUSH1[0x1c] + Op.PUSH1[0x64] + Op.MSIZE + Op.SWAP1
        + Op.MSIZE + Op.ADD + Op.PUSH1[0x0] + Op.SWAP1 + Op.MSTORE + Op.ADD
        + Op.PUSH4[0x86744558] + Op.PUSH1[0x1c] + Op.DUP3 + Op.SUB + Op.MSTORE
        + Op.CALLER + Op.PUSH1[0x4] + Op.DUP3 + Op.ADD + Op.MSTORE + Op.PUSH1[0x0]
        + Op.PUSH1[0x24] + Op.DUP3 + Op.ADD + Op.MSTORE + Op.PUSH1[0x20]
        + Op.PUSH2[0x1180] + Op.PUSH1[0x44] + Op.DUP4 + Op.PUSH1[0x0]
        + Op.PUSH2[0x680] + Op.MLOAD + Op.PUSH1[0x2d] + Op.GAS + Op.SUB + Op.CALL
        + Op.POP + Op.PUSH2[0x1180] + Op.MLOAD + Op.SWAP1 + Op.POP + Op.EQ + Op.ISZERO
        + Op.ISZERO + Op.PUSH2[0x216a] + Op.JUMPI + Op.PUSH1[0x2b] + Op.PUSH2[0x11a0]
        + Op.MSTORE + Op.PUSH1[0x20] + Op.PUSH2[0x11a0] + Op.RETURN + Op.JUMPDEST
        + Op.PUSH1[0x0] + Op.PUSH1[0x1c] + Op.PUSH1[0x84] + Op.MSIZE + Op.SWAP1
        + Op.MSIZE + Op.ADD + Op.PUSH1[0x0] + Op.SWAP1 + Op.MSTORE + Op.ADD
        + Op.PUSH4[0x27f08b00] + Op.PUSH1[0x1c] + Op.DUP3 + Op.SUB + Op.MSTORE
        + Op.ADDRESS + Op.PUSH1[0x4] + Op.DUP3 + Op.ADD + Op.MSTORE + Op.CALLER
        + Op.PUSH1[0x24] + Op.DUP3 + Op.ADD + Op.MSTORE + Op.PUSH1[0x0]
        + Op.PUSH1[0x44] + Op.DUP3 + Op.ADD + Op.MSTORE + Op.PUSH1[0x20]
        + Op.PUSH2[0x11c0] + Op.PUSH1[0x64] + Op.DUP4 + Op.PUSH1[0x0]
        + Op.PUSH2[0x680] + Op.MLOAD + Op.PUSH1[0x2d] + Op.GAS + Op.SUB + Op.CALL
        + Op.POP + Op.PUSH2[0x11c0] + Op.MLOAD + Op.SWAP1 + Op.POP + Op.EQ + Op.ISZERO
        + Op.ISZERO + Op.PUSH2[0x21c4] + Op.JUMPI + Op.PUSH1[0x2c] + Op.PUSH2[0x11e0]
        + Op.MSTORE + Op.PUSH1[0x20] + Op.PUSH2[0x11e0] + Op.RETURN + Op.JUMPDEST
        + Op.PUSH2[0xfc0] + Op.MLOAD + Op.PUSH1[0xc] + Op.PUSH2[0xfc0] + Op.MLOAD
        + Op.MUL + Op.SSTORE + Op.PUSH2[0xf80] + Op.MLOAD + Op.PUSH1[0xc]
        + Op.PUSH2[0xfc0] + Op.MLOAD + Op.MUL + Op.PUSH1[0x1] + Op.ADD + Op.SSTORE
        + Op.PUSH2[0x680] + Op.MLOAD + Op.PUSH1[0xc] + Op.PUSH2[0xfc0] + Op.MLOAD
        + Op.MUL + Op.PUSH1[0x2] + Op.ADD + Op.SSTORE + Op.PUSH2[0xfa0] + Op.MLOAD
        + Op.PUSH1[0xc] + Op.PUSH2[0xfc0] + Op.MLOAD + Op.MUL + Op.PUSH1[0x6] + Op.ADD
        + Op.SSTORE + Op.PUSH2[0x6a0] + Op.MLOAD + Op.PUSH1[0xc] + Op.PUSH2[0xfc0]
        + Op.MLOAD + Op.MUL + Op.PUSH1[0x3] + Op.ADD + Op.SSTORE + Op.PUSH2[0x6c0]
        + Op.MLOAD + Op.PUSH1[0xc] + Op.PUSH2[0xfc0] + Op.MLOAD + Op.MUL
        + Op.PUSH1[0x4] + Op.ADD + Op.SSTORE + Op.PUSH2[0x6e0] + Op.MLOAD
        + Op.PUSH1[0xc] + Op.PUSH2[0xfc0] + Op.MLOAD + Op.MUL + Op.PUSH1[0x5] + Op.ADD
        + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0xc] + Op.PUSH2[0xfc0] + Op.MLOAD
        + Op.MUL + Op.PUSH1[0x7] + Op.ADD + Op.SSTORE + Op.CALLER + Op.PUSH1[0xc]
        + Op.PUSH2[0xfc0] + Op.MLOAD + Op.MUL + Op.PUSH1[0x8] + Op.ADD + Op.SSTORE
        + Op.NUMBER + Op.PUSH1[0xc] + Op.PUSH2[0xfc0] + Op.MLOAD + Op.MUL
        + Op.PUSH1[0x9] + Op.ADD + Op.SSTORE + Op.PUSH2[0xfc0] + Op.MLOAD
        + Op.PUSH2[0x680] + Op.MLOAD
        + Op.PUSH21[0xc0000000000000000000000000000000000000000] + Op.ADD + Op.SSTORE
        + Op.PUSH2[0xfc0] + Op.MLOAD + Op.PUSH2[0xf80] + Op.MLOAD
        + Op.PUSH21[0xd0000000000000000000000000000000000000000] + Op.ADD + Op.SSTORE
        + Op.PUSH2[0xfc0] + Op.MLOAD
        + Op.PUSH21[0x160000000000000000000000000000000000000000] + Op.SSTORE
        + Op.PUSH1[0x1c] + Op.PUSH1[0x40] + Op.MSIZE + Op.SWAP1 + Op.MSIZE + Op.ADD
        + Op.PUSH1[0x0] + Op.SWAP1 + Op.MSTORE + Op.ADD + Op.PUSH2[0xfc0] + Op.MLOAD
        + Op.DUP2 + Op.MSTORE
        + Op.PUSH32[0x1238fe6d44cf796960d61b74766b3a383110e472d849f5ca16ae50215bc05e58]
        + Op.PUSH1[0x20] + Op.DUP3 + Op.LOG1 + Op.POP + Op.PUSH1[0x1]
        + Op.PUSH2[0x1200] + Op.MSTORE + Op.PUSH1[0x20] + Op.PUSH2[0x1200] + Op.RETURN
        + Op.JUMPDEST + Op.PUSH4[0x41569661] + Op.DUP2 + Op.EQ + Op.ISZERO
        + Op.PUSH2[0x232a] + Op.JUMPI + Op.PUSH1[0x4] + Op.CALLDATALOAD
        + Op.PUSH2[0x1220] + Op.MSTORE + Op.PUSH2[0x1220] + Op.MLOAD
        + Op.PUSH21[0xc0000000000000000000000000000000000000000] + Op.ADD + Op.SLOAD
        + Op.PUSH2[0x1240] + Op.MSTORE + Op.PUSH1[0x20] + Op.PUSH2[0x1240] + Op.RETURN
        + Op.JUMPDEST + Op.PUSH4[0xfcde9f78] + Op.DUP2 + Op.EQ + Op.ISZERO
        + Op.PUSH2[0x2364] + Op.JUMPI + Op.PUSH1[0x4] + Op.CALLDATALOAD
        + Op.PUSH2[0xf80] + Op.MSTORE + Op.PUSH2[0xf80] + Op.MLOAD
        + Op.PUSH21[0xd0000000000000000000000000000000000000000] + Op.ADD + Op.SLOAD
        + Op.PUSH2[0x1260] + Op.MSTORE + Op.PUSH1[0x20] + Op.PUSH2[0x1260] + Op.RETURN
        + Op.JUMPDEST + Op.PUSH4[0x6e5b4343] + Op.DUP2 + Op.EQ + Op.ISZERO
        + Op.PUSH2[0x2392] + Op.JUMPI
        + Op.PUSH21[0x160000000000000000000000000000000000000000] + Op.SLOAD
        + Op.PUSH2[0x1280] + Op.MSTORE + Op.PUSH1[0x20] + Op.PUSH2[0x1280] + Op.RETURN
        + Op.JUMPDEST + Op.PUSH4[0xfafa69c2] + Op.DUP2 + Op.EQ + Op.ISZERO
        + Op.PUSH2[0x24e6] + Op.JUMPI + Op.PUSH1[0x4] + Op.CALLDATALOAD
        + Op.PUSH2[0xfc0] + Op.MSTORE + Op.PUSH2[0x180] + Op.MSIZE + Op.SWAP1
        + Op.MSIZE + Op.ADD + Op.PUSH1[0x0] + Op.SWAP1 + Op.MSTORE + Op.PUSH1[0xb]
        + Op.DUP2 + Op.MSTORE + Op.PUSH1[0x20] + Op.DUP2 + Op.ADD + Op.SWAP1 + Op.POP
        + Op.PUSH2[0x12a0] + Op.MSTORE + Op.PUSH1[0xc] + Op.PUSH2[0xfc0] + Op.MLOAD
        + Op.MUL + Op.SLOAD + Op.PUSH2[0x12a0] + Op.MLOAD + Op.MSTORE + Op.PUSH1[0xc]
        + Op.PUSH2[0xfc0] + Op.MLOAD + Op.MUL + Op.PUSH1[0x1] + Op.ADD + Op.SLOAD
        + Op.PUSH1[0x20] + Op.PUSH2[0x12a0] + Op.MLOAD + Op.ADD + Op.MSTORE
        + Op.PUSH1[0xc] + Op.PUSH2[0xfc0] + Op.MLOAD + Op.MUL + Op.PUSH1[0x2] + Op.ADD
        + Op.SLOAD + Op.PUSH1[0x40] + Op.PUSH2[0x12a0] + Op.MLOAD + Op.ADD + Op.MSTORE
        + Op.PUSH1[0xc] + Op.PUSH2[0xfc0] + Op.MLOAD + Op.MUL + Op.PUSH1[0x3] + Op.ADD
        + Op.SLOAD + Op.PUSH1[0x60] + Op.PUSH2[0x12a0] + Op.MLOAD + Op.ADD + Op.MSTORE
        + Op.PUSH1[0xc] + Op.PUSH2[0xfc0] + Op.MLOAD + Op.MUL + Op.PUSH1[0x4] + Op.ADD
        + Op.SLOAD + Op.PUSH1[0x80] + Op.PUSH2[0x12a0] + Op.MLOAD + Op.ADD + Op.MSTORE
        + Op.PUSH1[0xc] + Op.PUSH2[0xfc0] + Op.MLOAD + Op.MUL + Op.PUSH1[0x5] + Op.ADD
        + Op.SLOAD + Op.PUSH1[0xa0] + Op.PUSH2[0x12a0] + Op.MLOAD + Op.ADD + Op.MSTORE
        + Op.PUSH1[0xc] + Op.PUSH2[0xfc0] + Op.MLOAD + Op.MUL + Op.PUSH1[0x7] + Op.ADD
        + Op.SLOAD + Op.PUSH1[0xc0] + Op.PUSH2[0x12a0] + Op.MLOAD + Op.ADD + Op.MSTORE
        + Op.PUSH1[0xc] + Op.PUSH2[0xfc0] + Op.MLOAD + Op.MUL + Op.PUSH1[0x8] + Op.ADD
        + Op.SLOAD + Op.PUSH1[0xe0] + Op.PUSH2[0x12a0] + Op.MLOAD + Op.ADD + Op.MSTORE
        + Op.PUSH1[0xc] + Op.PUSH2[0xfc0] + Op.MLOAD + Op.MUL + Op.PUSH1[0x9] + Op.ADD
        + Op.SLOAD + Op.PUSH2[0x100] + Op.PUSH2[0x12a0] + Op.MLOAD + Op.ADD
        + Op.MSTORE + Op.PUSH1[0xc] + Op.PUSH2[0xfc0] + Op.MLOAD + Op.MUL
        + Op.PUSH1[0xa] + Op.ADD + Op.SLOAD + Op.PUSH2[0x120] + Op.PUSH2[0x12a0]
        + Op.MLOAD + Op.ADD + Op.MSTORE + Op.PUSH1[0xc] + Op.PUSH2[0xfc0] + Op.MLOAD
        + Op.MUL + Op.PUSH1[0x6] + Op.ADD + Op.SLOAD + Op.PUSH2[0x140]
        + Op.PUSH2[0x12a0] + Op.MLOAD + Op.ADD + Op.MSTORE + Op.PUSH2[0x12a0]
        + Op.MLOAD + Op.ISZERO + Op.PUSH2[0x24b2] + Op.JUMPI + Op.PUSH2[0x12a0]
        + Op.MLOAD + Op.PUSH1[0x20] + Op.PUSH1[0x40] + Op.DUP3 + Op.SUB + Op.MSTORE
        + Op.PUSH1[0x20] + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB + Op.MLOAD + Op.MUL
        + Op.PUSH1[0x40] + Op.ADD + Op.PUSH1[0x40] + Op.DUP3 + Op.SUB + Op.RETURN
        + Op.POP + Op.JUMPDEST + Op.PUSH1[0x40] + Op.MSIZE + Op.SWAP1 + Op.MSIZE
        + Op.ADD + Op.PUSH1[0x0] + Op.SWAP1 + Op.MSTORE + Op.PUSH1[0x1] + Op.DUP2
        + Op.MSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x20] + Op.DUP3 + Op.ADD + Op.MSTORE
        + Op.PUSH1[0x20] + Op.DUP2 + Op.ADD + Op.SWAP1 + Op.POP + Op.PUSH1[0x20]
        + Op.PUSH1[0x40] + Op.DUP3 + Op.SUB + Op.MSTORE + Op.PUSH1[0x20]
        + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB + Op.MLOAD + Op.MUL + Op.PUSH1[0x40]
        + Op.ADD + Op.PUSH1[0x40] + Op.DUP3 + Op.SUB + Op.RETURN + Op.POP
        + Op.JUMPDEST + Op.PUSH4[0x9cfc1535] + Op.DUP2 + Op.EQ + Op.ISZERO
        + Op.PUSH2[0x262e] + Op.JUMPI + Op.PUSH1[0x4] + Op.CALLDATALOAD
        + Op.PUSH1[0x40] + Op.MSTORE + Op.PUSH1[0xc] + Op.PUSH1[0x40] + Op.MLOAD
        + Op.MUL + Op.PUSH1[0xa] + Op.ADD + Op.SLOAD + Op.PUSH2[0x1340] + Op.MSTORE
        + Op.PUSH1[0xc] + Op.PUSH1[0x40] + Op.MLOAD + Op.MUL + Op.PUSH1[0xb] + Op.ADD
        + Op.SLOAD + Op.PUSH2[0x1c0] + Op.MSTORE + Op.PUSH2[0x1340] + Op.MLOAD
        + Op.DUP1 + Op.PUSH1[0x20] + Op.MUL + Op.PUSH1[0x20] + Op.ADD + Op.MSIZE
        + Op.SWAP1 + Op.MSIZE + Op.ADD + Op.PUSH1[0x0] + Op.SWAP1 + Op.MSTORE
        + Op.DUP2 + Op.DUP2 + Op.MSTORE + Op.PUSH1[0x20] + Op.DUP2 + Op.ADD + Op.SWAP1
        + Op.POP + Op.SWAP1 + Op.POP + Op.PUSH2[0x600] + Op.MSTORE + Op.PUSH1[0x0]
        + Op.PUSH2[0x13a0] + Op.MSTORE + Op.JUMPDEST + Op.PUSH2[0x1340] + Op.MLOAD
        + Op.PUSH2[0x13a0] + Op.MLOAD + Op.SLT + Op.ISZERO + Op.PUSH2[0x25d4]
        + Op.JUMPI + Op.PUSH1[0xa0] + Op.PUSH1[0xa0] + Op.MSIZE + Op.SWAP1 + Op.MSIZE
        + Op.ADD + Op.PUSH1[0x0] + Op.SWAP1 + Op.MSTORE + Op.PUSH1[0x0] + Op.DUP2
        + Op.MSTORE + Op.PUSH1[0x40] + Op.MLOAD + Op.DUP2 + Op.PUSH1[0x20] + Op.ADD
        + Op.MSTORE + Op.PUSH1[0xc] + Op.DUP2 + Op.PUSH1[0x40] + Op.ADD + Op.MSTORE
        + Op.PUSH2[0x1c0] + Op.MLOAD + Op.DUP2 + Op.PUSH1[0x60] + Op.ADD + Op.MSTORE
        + Op.PUSH1[0x0] + Op.DUP2 + Op.PUSH1[0x80] + Op.ADD + Op.MSTORE + Op.DUP1
        + Op.SWAP1 + Op.POP + Op.SHA3 + Op.SLOAD + Op.PUSH2[0x13a0] + Op.MLOAD
        + Op.PUSH1[0x20] + Op.MUL + Op.PUSH2[0x600] + Op.MLOAD + Op.ADD + Op.MSTORE
        + Op.PUSH1[0xa0] + Op.PUSH1[0xa0] + Op.MSIZE + Op.SWAP1 + Op.MSIZE + Op.ADD
        + Op.PUSH1[0x0] + Op.SWAP1 + Op.MSTORE + Op.PUSH1[0x0] + Op.DUP2 + Op.MSTORE
        + Op.PUSH1[0x40] + Op.MLOAD + Op.DUP2 + Op.PUSH1[0x20] + Op.ADD + Op.MSTORE
        + Op.PUSH1[0xc] + Op.DUP2 + Op.PUSH1[0x40] + Op.ADD + Op.MSTORE
        + Op.PUSH2[0x1c0] + Op.MLOAD + Op.DUP2 + Op.PUSH1[0x60] + Op.ADD + Op.MSTORE
        + Op.PUSH1[0x2] + Op.DUP2 + Op.PUSH1[0x80] + Op.ADD + Op.MSTORE + Op.DUP1
        + Op.SWAP1 + Op.POP + Op.SHA3 + Op.SLOAD + Op.PUSH2[0x1c0] + Op.MSTORE
        + Op.PUSH1[0x1] + Op.PUSH2[0x13a0] + Op.MLOAD + Op.ADD + Op.PUSH2[0x13a0]
        + Op.MSTORE + Op.PUSH2[0x253d] + Op.JUMP + Op.JUMPDEST + Op.PUSH2[0x600]
        + Op.MLOAD + Op.ISZERO + Op.PUSH2[0x25fa] + Op.JUMPI + Op.PUSH2[0x600]
        + Op.MLOAD + Op.PUSH1[0x20] + Op.PUSH1[0x40] + Op.DUP3 + Op.SUB + Op.MSTORE
        + Op.PUSH1[0x20] + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB + Op.MLOAD + Op.MUL
        + Op.PUSH1[0x40] + Op.ADD + Op.PUSH1[0x40] + Op.DUP3 + Op.SUB + Op.RETURN
        + Op.POP + Op.JUMPDEST + Op.PUSH1[0x40] + Op.MSIZE + Op.SWAP1 + Op.MSIZE
        + Op.ADD + Op.PUSH1[0x0] + Op.SWAP1 + Op.MSTORE + Op.PUSH1[0x1] + Op.DUP2
        + Op.MSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x20] + Op.DUP3 + Op.ADD + Op.MSTORE
        + Op.PUSH1[0x20] + Op.DUP2 + Op.ADD + Op.SWAP1 + Op.POP + Op.PUSH1[0x20]
        + Op.PUSH1[0x40] + Op.DUP3 + Op.SUB + Op.MSTORE + Op.PUSH1[0x20]
        + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB + Op.MLOAD + Op.MUL + Op.PUSH1[0x40]
        + Op.ADD + Op.PUSH1[0x40] + Op.DUP3 + Op.SUB + Op.RETURN + Op.POP
        + Op.JUMPDEST + Op.PUSH4[0xf718190] + Op.DUP2 + Op.EQ + Op.ISZERO
        + Op.PUSH2[0x27e9] + Op.JUMPI + Op.PUSH1[0x4] + Op.CALLDATALOAD
        + Op.PUSH2[0xfc0] + Op.MSTORE + Op.PUSH2[0x120] + Op.MSIZE + Op.SWAP1
        + Op.MSIZE + Op.ADD + Op.PUSH1[0x0] + Op.SWAP1 + Op.MSTORE + Op.PUSH1[0x8]
        + Op.DUP2 + Op.MSTORE + Op.PUSH1[0x20] + Op.DUP2 + Op.ADD + Op.SWAP1 + Op.POP
        + Op.PUSH2[0x180] + Op.MSTORE + Op.PUSH1[0x8] + Op.PUSH2[0xfc0] + Op.MLOAD
        + Op.MUL + Op.PUSH21[0xe0000000000000000000000000000000000000000] + Op.ADD
        + Op.SLOAD + Op.PUSH2[0x180] + Op.MLOAD + Op.MSTORE + Op.PUSH1[0x8]
        + Op.PUSH2[0xfc0] + Op.MLOAD + Op.MUL
        + Op.PUSH21[0xe0000000000000000000000000000000000000001] + Op.ADD + Op.SLOAD
        + Op.PUSH1[0x20] + Op.PUSH2[0x180] + Op.MLOAD + Op.ADD + Op.MSTORE
        + Op.PUSH1[0x8] + Op.PUSH2[0xfc0] + Op.MLOAD + Op.MUL
        + Op.PUSH21[0xe0000000000000000000000000000000000000002] + Op.ADD + Op.SLOAD
        + Op.PUSH1[0x40] + Op.PUSH2[0x180] + Op.MLOAD + Op.ADD + Op.MSTORE
        + Op.PUSH1[0x8] + Op.PUSH2[0xfc0] + Op.MLOAD + Op.MUL
        + Op.PUSH21[0xe0000000000000000000000000000000000000003] + Op.ADD + Op.SLOAD
        + Op.PUSH1[0x60] + Op.PUSH2[0x180] + Op.MLOAD + Op.ADD + Op.MSTORE
        + Op.PUSH1[0x8] + Op.PUSH2[0xfc0] + Op.MLOAD + Op.MUL
        + Op.PUSH21[0xe0000000000000000000000000000000000000004] + Op.ADD + Op.SLOAD
        + Op.PUSH1[0x80] + Op.PUSH2[0x180] + Op.MLOAD + Op.ADD + Op.MSTORE
        + Op.PUSH1[0x8] + Op.PUSH2[0xfc0] + Op.MLOAD + Op.MUL
        + Op.PUSH21[0xe0000000000000000000000000000000000000005] + Op.ADD + Op.SLOAD
        + Op.PUSH1[0xa0] + Op.PUSH2[0x180] + Op.MLOAD + Op.ADD + Op.MSTORE
        + Op.PUSH1[0x8] + Op.PUSH2[0xfc0] + Op.MLOAD + Op.MUL
        + Op.PUSH21[0xe0000000000000000000000000000000000000006] + Op.ADD + Op.SLOAD
        + Op.PUSH1[0xc0] + Op.PUSH2[0x180] + Op.MLOAD + Op.ADD + Op.MSTORE
        + Op.PUSH1[0x8] + Op.PUSH2[0xfc0] + Op.MLOAD + Op.MUL
        + Op.PUSH21[0xe0000000000000000000000000000000000000007] + Op.ADD + Op.SLOAD
        + Op.PUSH1[0xe0] + Op.PUSH2[0x180] + Op.MLOAD + Op.ADD + Op.MSTORE
        + Op.PUSH2[0x180] + Op.MLOAD + Op.ISZERO + Op.PUSH2[0x27b5] + Op.JUMPI
        + Op.PUSH2[0x180] + Op.MLOAD + Op.PUSH1[0x20] + Op.PUSH1[0x40] + Op.DUP3
        + Op.SUB + Op.MSTORE + Op.PUSH1[0x20] + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.MLOAD + Op.MUL + Op.PUSH1[0x40] + Op.ADD + Op.PUSH1[0x40] + Op.DUP3
        + Op.SUB + Op.RETURN + Op.POP + Op.JUMPDEST + Op.PUSH1[0x40] + Op.MSIZE
        + Op.SWAP1 + Op.MSIZE + Op.ADD + Op.PUSH1[0x0] + Op.SWAP1 + Op.MSTORE
        + Op.PUSH1[0x1] + Op.DUP2 + Op.MSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x20]
        + Op.DUP3 + Op.ADD + Op.MSTORE + Op.PUSH1[0x20] + Op.DUP2 + Op.ADD + Op.SWAP1
        + Op.POP + Op.PUSH1[0x20] + Op.PUSH1[0x40] + Op.DUP3 + Op.SUB + Op.MSTORE
        + Op.PUSH1[0x20] + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB + Op.MLOAD + Op.MUL
        + Op.PUSH1[0x40] + Op.ADD + Op.PUSH1[0x40] + Op.DUP3 + Op.SUB + Op.RETURN
        + Op.POP + Op.JUMPDEST + Op.PUSH4[0x1c9aa4b6] + Op.DUP2 + Op.EQ + Op.ISZERO
        + Op.PUSH2[0x2893] + Op.JUMPI + Op.PUSH1[0x4] + Op.CALLDATALOAD
        + Op.PUSH2[0x1220] + Op.MSTORE + Op.PUSH1[0x24] + Op.CALLDATALOAD
        + Op.PUSH1[0x40] + Op.MSTORE + Op.PUSH1[0x60] + Op.MSIZE + Op.SWAP1 + Op.MSIZE
        + Op.ADD + Op.PUSH1[0x0] + Op.SWAP1 + Op.MSTORE + Op.PUSH1[0x2] + Op.DUP2
        + Op.MSTORE + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.MSIZE + Op.SWAP1 + Op.MSIZE
        + Op.ADD + Op.PUSH1[0x0] + Op.SWAP1 + Op.MSTORE + Op.PUSH1[0x4] + Op.DUP2
        + Op.MSTORE + Op.PUSH2[0x1220] + Op.MLOAD + Op.DUP2 + Op.PUSH1[0x20] + Op.ADD
        + Op.MSTORE + Op.PUSH1[0x40] + Op.MLOAD + Op.DUP2 + Op.PUSH1[0x40] + Op.ADD
        + Op.MSTORE + Op.PUSH1[0x0] + Op.DUP2 + Op.PUSH1[0x60] + Op.ADD + Op.MSTORE
        + Op.DUP1 + Op.SWAP1 + Op.POP + Op.SHA3 + Op.SLOAD + Op.PUSH1[0x20] + Op.DUP3
        + Op.ADD + Op.MSTORE + Op.PUSH1[0x80] + Op.PUSH1[0x80] + Op.MSIZE + Op.SWAP1
        + Op.MSIZE + Op.ADD + Op.PUSH1[0x0] + Op.SWAP1 + Op.MSTORE + Op.PUSH1[0x4]
        + Op.DUP2 + Op.MSTORE + Op.PUSH2[0x1220] + Op.MLOAD + Op.DUP2 + Op.PUSH1[0x20]
        + Op.ADD + Op.MSTORE + Op.PUSH1[0x40] + Op.MLOAD + Op.DUP2 + Op.PUSH1[0x40]
        + Op.ADD + Op.MSTORE + Op.PUSH1[0x1] + Op.DUP2 + Op.PUSH1[0x60] + Op.ADD
        + Op.MSTORE + Op.DUP1 + Op.SWAP1 + Op.POP + Op.SHA3 + Op.SLOAD
        + Op.PUSH1[0x40] + Op.DUP3 + Op.ADD + Op.MSTORE + Op.PUSH1[0x20] + Op.DUP2
        + Op.ADD + Op.SWAP1 + Op.POP + Op.PUSH1[0x20] + Op.PUSH1[0x40] + Op.DUP3
        + Op.SUB + Op.MSTORE + Op.PUSH1[0x20] + Op.PUSH1[0x20] + Op.DUP3 + Op.SUB
        + Op.MLOAD + Op.MUL + Op.PUSH1[0x40] + Op.ADD + Op.PUSH1[0x40] + Op.DUP3
        + Op.SUB + Op.RETURN + Op.POP + Op.JUMPDEST + Op.POP
    ),
        storage={0xd0000000000000000000000000000000000505347: 0x0, 0x160000000000000000000000000000000000000000: 0x1},
    )

    tx = Transaction(
        secret_key=Hash(
            "0x98d5e7375843784f7eb2606a693bab39ebac533561559e372dc3017f30519535"
        ),
        to=contract,
        data=bytes.fromhex(
            "d91e22f40000000000000000000000000000000000000000000000000000000000505347"
            "000000000000000000000000000000000000000000000000000000002450534700000000"
            "000000000000000000000000000000000000000000000000000000010000000000000000"
            "000000000000000000000000000000000000000005f5e100000000000000000000000000"
            "000000000000000000000000002386f26fc1000000000000000000000000000000000000"
            "00000000000000000000000000000001"
        ),
        gas_limit=500000,
        gas_price=52637211012,
        nonce=24,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
