"""
Ori Pomerantz   qbzzt1@gmail.com

Ported from:
tests/static/state_tests/stEIP1559/baseFeeDiffPlacesFiller.yml

callee code:
    basefee
    push1 0x00
    mstore
    push1 0x00
    mload
    push1 0x40
    mstore
    push1 0x21
    push1 0x3f
    return

callee_1 code:
    basefee
    push1 0x00
    mstore
    push1 0x20
    push1 0x00
    return

callee_2 code:
    basefee
    push1 0x00
    mstore
    push1 0x00
    mload
    push1 0x00
    sstore
    invalid

callee_3 code:
    basefee
    push1 0x00
    mstore
    push1 0x20
    push1 0x00
    return

callee_4 code:
    basefee
    push1 0x00
    mstore
    push1 0x00
    mload
    push1 0x00
    sstore
    push1 0x20
    push1 0x00
    revert

callee_5 code:
    push1 0x00
    push3 0x20c0de
    dup2
    dup2
    extcodesize
    swap3
    dup4
    swap3
    extcodecopy
    push1 0x00
    return

callee_6 code:
    push1 0x20
    push1 0x00
    dup1
    dup1
    dup1
    push2 0xca11
    gas
    call
    iszero
    push1 0x15
    jumpi
    push1 0x20
    push1 0x00
    return
    jumpdest
    push1 0x20
    push1 0x00
    revert

callee_7 code:
    push1 0x20
    push1 0x00
    dup1
    dup1
    dup1
    push2 0xca11
    gas
    callcode
    iszero
    push1 0x15
    jumpi
    push1 0x20
    push1 0x00
    return
    jumpdest
    push1 0x20
    push1 0x00
    revert

callee_8 code:
    push1 0x20
    push1 0x00
    dup1
    dup1
    push2 0xca11
    gas
    delegatecall
    iszero
    push1 0x14
    jumpi
    push1 0x20
    push1 0x00
    return
    jumpdest
    push1 0x20
    push1 0x00
    revert

callee_9 code:
    push1 0x20
    push1 0x00
    dup1
    dup1
    push2 0xca11
    gas
    staticcall
    iszero
    push1 0x14
    jumpi
    push1 0x20
    push1 0x00
    return
    jumpdest
    push1 0x20
    push1 0x00
    revert

callee_10 code:
    push1 0x00
    selfdestruct

callee_11 code:
    push1 0x00
    calldataload
    dup1
    iszero
    push1 0x2d
    jumpi
    push1 0x01
    swap1
    sub
    push1 0x00
    mstore
    push1 0x20
    push1 0x00
    dup2
    dup2
    dup1
    push5 0x60baccfa57
    gas
    call
    iszero
    ... (16 more instructions)

contract code:
    push2 0x60a7
    push1 0x00
    mstore
    push1 0x01
    dup1
    push1 0x04
    calldataload
    push4 0xc0dec0de
    extcodesize
    push1 0x20
    push2 0xc0de
    extcodesize
    dup4
    iszero
    push2 0x058a
    jumpi
    dup4
    push1 0xf1
    eq
    push2 0x0574
    ... (872 more instructions)
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
    ["tests/static/state_tests/stEIP1559/baseFeeDiffPlacesFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Prague")
@pytest.mark.parametrize(
    "tx_data_hex",
    [
        "693c6139000000000000000000000000000000000000000000000000000000000000f2f2",
        "693c6139000000000000000000000000000000000000000000000000000000000000f4f2",
        "693c6139000000000000000000000000000000000000000000000000000000000000faf2",
        "693c6139000000000000000000000000000000000000000000000000000000000000f1f4",
        "693c6139000000000000000000000000000000000000000000000000000000000000f2f4",
        "693c6139000000000000000000000000000000000000000000000000000000000000f4f4",
        "693c6139000000000000000000000000000000000000000000000000000000000000faf4",
        "693c6139000000000000000000000000000000000000000000000000000000000000f1fa",
        "693c6139000000000000000000000000000000000000000000000000000000000000f2fa",
        "693c6139000000000000000000000000000000000000000000000000000000000000f4fa",
        "693c6139000000000000000000000000000000000000000000000000000000000000fafa",
        "693c613900000000000000000000000000000000000000000000000000000000000000fd",
        "693c613900000000000000000000000000000000000000000000000000000000000000fe",
        "693c613900000000000000000000000000000000000000000000000000000000000000ff",
        "693c613900000000000000000000000000000000000000000000000000000000000000f0",
        "693c613900000000000000000000000000000000000000000000000000000000000000f5",
        "693c6139000000000000000000000000000000000000000000000000000000000000f0f1",
        "693c6139000000000000000000000000000000000000000000000000000000000000f5f1",
        "693c6139000000000000000000000000000000000000000000000000000000000000f0f2",
        "693c6139000000000000000000000000000000000000000000000000000000000000f5f2",
        "693c6139000000000000000000000000000000000000000000000000000000000000f0f4",
        "693c6139000000000000000000000000000000000000000000000000000000000000f5f4",
        "693c6139000000000000000000000000000000000000000000000000000000000000f0fa",
        "693c6139000000000000000000000000000000000000000000000000000000000000f5fa",
        "693c613900000000000000000000000000000000000000000000000000000060baccfa57",
        "693c613900000000000000000000000000000000000000000000000000000000000000f4",
        "693c613900000000000000000000000000000000000000000000000000000000000000fa",
        "693c6139000000000000000000000000000000000000000000000000000000000000f1f1",
        "693c6139000000000000000000000000000000000000000000000000000000000000f2f1",
        "693c6139000000000000000000000000000000000000000000000000000000000000f4f1",
        "693c6139000000000000000000000000000000000000000000000000000000000000faf1",
        "693c6139000000000000000000000000000000000000000000000000000000000000f1f2",
        "693c613900000000000000000000000000000000000000000000000000000000000000f1",
        "693c613900000000000000000000000000000000000000000000000000000000000000f2",
        "693c61390000000000000000000000000000000000000000000000000000000000000000",
    ],
    ids=['case0', 'case1', 'case2', 'case3', 'case4', 'case5', 'case6', 'case7', 'case8', 'case9', 'case10', 'case11', 'case12', 'case13', 'case14', 'case15', 'case16', 'case17', 'case18', 'case19', 'case20', 'case21', 'case22', 'case23', 'case24', 'case25', 'case26', 'case27', 'case28', 'case29', 'case30', 'case31', 'case32', 'case33', 'case34'],
)
@pytest.mark.pre_alloc_mutable
def test_base_fee_diff_places(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
) -> None:
    """Ori Pomerantz   qbzzt1@gmail.com."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    contract = Address("0xcccccccccccccccccccccccccccccccccccccccc")
    callee = Address("0x000000000000000000000000000000000000c0de")
    callee_1 = Address("0x000000000000000000000000000000000000ca11")
    callee_2 = Address("0x0000000000000000000000000000000000060006")
    callee_3 = Address("0x000000000000000000000000000000000020c0de")
    callee_4 = Address("0x000000000000000000000000000000000060bacc")
    callee_5 = Address("0x00000000000000000000000000000000c0dec0de")
    callee_6 = Address("0x00000000000000000000000000000000ca1100f1")
    callee_7 = Address("0x00000000000000000000000000000000ca1100f2")
    callee_8 = Address("0x00000000000000000000000000000000ca1100f4")
    callee_9 = Address("0x00000000000000000000000000000000ca1100fa")
    callee_10 = Address("0x00000000000000000000000000000000deaddead")
    callee_11 = Address("0x00000000000000000000000000000060baccfa57")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=4503599627370496,
    )

    pre[callee] = Account(
        balance=0xde0b6b3a7640000,
        nonce=1,
        code=(
        Op.BASEFEE + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x0] + Op.MLOAD
        + Op.PUSH1[0x40] + Op.MSTORE + Op.PUSH1[0x21] + Op.PUSH1[0x3f] + Op.RETURN
    ),
    )
    pre[callee_1] = Account(
        balance=0xde0b6b3a7640000,
        nonce=1,
        code=(
        Op.BASEFEE + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x20] + Op.PUSH1[0x0]
        + Op.RETURN
    ),
    )
    pre[callee_2] = Account(
        balance=0xde0b6b3a7640000,
        nonce=1,
        code=(
        Op.BASEFEE + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x0] + Op.MLOAD
        + Op.PUSH1[0x0] + Op.SSTORE + Op.INVALID
    ),
        storage={0x0: 0x60a7},
    )
    pre[callee_3] = Account(
        balance=0xde0b6b3a7640000,
        nonce=1,
        code=(
        Op.BASEFEE + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x20] + Op.PUSH1[0x0]
        + Op.RETURN
    ),
    )
    pre[callee_4] = Account(
        balance=0xde0b6b3a7640000,
        nonce=1,
        code=(
        Op.BASEFEE + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x0] + Op.MLOAD
        + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.REVERT
    ),
        storage={0x0: 0x60a7},
    )
    pre[callee_5] = Account(
        balance=0xde0b6b3a7640000,
        nonce=1,
        code=(
        Op.PUSH1[0x0] + Op.PUSH3[0x20c0de] + Op.DUP2 + Op.DUP2 + Op.EXTCODESIZE
        + Op.SWAP3 + Op.DUP4 + Op.SWAP3 + Op.EXTCODECOPY + Op.PUSH1[0x0] + Op.RETURN
    ),
    )
    pre[callee_6] = Account(
        balance=0xde0b6b3a7640000,
        nonce=1,
        code=(
        Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.DUP1 + Op.DUP1 + Op.DUP1
        + Op.PUSH2[0xca11] + Op.GAS + Op.CALL + Op.ISZERO + Op.PUSH1[0x15] + Op.JUMPI
        + Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.RETURN + Op.JUMPDEST + Op.PUSH1[0x20]
        + Op.PUSH1[0x0] + Op.REVERT
    ),
    )
    pre[callee_7] = Account(
        balance=0xde0b6b3a7640000,
        nonce=1,
        code=(
        Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.DUP1 + Op.DUP1 + Op.DUP1
        + Op.PUSH2[0xca11] + Op.GAS + Op.CALLCODE + Op.ISZERO + Op.PUSH1[0x15]
        + Op.JUMPI + Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.RETURN + Op.JUMPDEST
        + Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.REVERT
    ),
    )
    pre[callee_8] = Account(
        balance=0xde0b6b3a7640000,
        nonce=1,
        code=(
        Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.DUP1 + Op.DUP1 + Op.PUSH2[0xca11]
        + Op.GAS + Op.DELEGATECALL + Op.ISZERO + Op.PUSH1[0x14] + Op.JUMPI
        + Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.RETURN + Op.JUMPDEST + Op.PUSH1[0x20]
        + Op.PUSH1[0x0] + Op.REVERT
    ),
    )
    pre[callee_9] = Account(
        balance=0xde0b6b3a7640000,
        nonce=1,
        code=(
        Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.DUP1 + Op.DUP1 + Op.PUSH2[0xca11]
        + Op.GAS + Op.STATICCALL + Op.ISZERO + Op.PUSH1[0x14] + Op.JUMPI
        + Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.RETURN + Op.JUMPDEST + Op.PUSH1[0x20]
        + Op.PUSH1[0x0] + Op.REVERT
    ),
    )
    pre[callee_10] = Account(
        balance=0xde0b6b3a7640000,
        nonce=1,
        code=Op.PUSH1[0x0] + Op.SELFDESTRUCT,
    )
    pre[callee_11] = Account(
        balance=0xde0b6b3a7640000,
        nonce=1,
        code=(
        Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.DUP1 + Op.ISZERO + Op.PUSH1[0x2d]
        + Op.JUMPI + Op.PUSH1[0x1] + Op.SWAP1 + Op.SUB + Op.PUSH1[0x0] + Op.MSTORE
        + Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.DUP2 + Op.DUP2 + Op.DUP1
        + Op.PUSH5[0x60baccfa57] + Op.GAS + Op.CALL + Op.ISZERO + Op.PUSH1[0x27]
        + Op.JUMPI + Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.RETURN + Op.JUMPDEST
        + Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.REVERT + Op.JUMPDEST + Op.BASEFEE
        + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.RETURN
    ),
    )
    pre[sender] = Account(balance=0x3635c9adc5dea00000, nonce=1)
    pre[contract] = Account(
        balance=0xde0b6b3a7640000,
        nonce=1,
        code=(
        Op.PUSH2[0x60a7] + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x1] + Op.DUP1
        + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH4[0xc0dec0de] + Op.EXTCODESIZE
        + Op.PUSH1[0x20] + Op.PUSH2[0xc0de] + Op.EXTCODESIZE + Op.DUP4 + Op.ISZERO
        + Op.PUSH2[0x58a] + Op.JUMPI + Op.DUP4 + Op.PUSH1[0xf1] + Op.EQ
        + Op.PUSH2[0x574] + Op.JUMPI + Op.DUP4 + Op.PUSH1[0xf2] + Op.EQ
        + Op.PUSH2[0x55e] + Op.JUMPI + Op.DUP4 + Op.PUSH1[0xf4] + Op.EQ
        + Op.PUSH2[0x549] + Op.JUMPI + Op.DUP4 + Op.PUSH1[0xfa] + Op.EQ
        + Op.PUSH2[0x534] + Op.JUMPI + Op.DUP4 + Op.PUSH2[0xf1f1] + Op.EQ
        + Op.PUSH2[0x51c] + Op.JUMPI + Op.DUP4 + Op.PUSH2[0xf2f1] + Op.EQ
        + Op.PUSH2[0x504] + Op.JUMPI + Op.DUP4 + Op.PUSH2[0xf4f1] + Op.EQ
        + Op.PUSH2[0x4ed] + Op.JUMPI + Op.DUP4 + Op.PUSH2[0xfaf1] + Op.EQ
        + Op.PUSH2[0x4d6] + Op.JUMPI + Op.DUP4 + Op.PUSH2[0xf1f2] + Op.EQ
        + Op.PUSH2[0x4be] + Op.JUMPI + Op.DUP4 + Op.PUSH2[0xf2f2] + Op.EQ
        + Op.PUSH2[0x4a6] + Op.JUMPI + Op.DUP4 + Op.PUSH2[0xf4f2] + Op.EQ
        + Op.PUSH2[0x48f] + Op.JUMPI + Op.DUP4 + Op.PUSH2[0xfaf2] + Op.EQ
        + Op.PUSH2[0x478] + Op.JUMPI + Op.DUP4 + Op.PUSH2[0xf1f4] + Op.EQ
        + Op.PUSH2[0x460] + Op.JUMPI + Op.DUP4 + Op.PUSH2[0xf2f4] + Op.EQ
        + Op.PUSH2[0x448] + Op.JUMPI + Op.DUP4 + Op.PUSH2[0xf4f4] + Op.EQ
        + Op.PUSH2[0x431] + Op.JUMPI + Op.DUP4 + Op.PUSH2[0xfaf4] + Op.EQ
        + Op.PUSH2[0x41a] + Op.JUMPI + Op.DUP4 + Op.PUSH2[0xf1fa] + Op.EQ
        + Op.PUSH2[0x402] + Op.JUMPI + Op.DUP4 + Op.PUSH2[0xf2fa] + Op.EQ
        + Op.PUSH2[0x3ea] + Op.JUMPI + Op.DUP4 + Op.PUSH2[0xf4fa] + Op.EQ
        + Op.PUSH2[0x3d3] + Op.JUMPI + Op.DUP4 + Op.PUSH2[0xfafa] + Op.EQ
        + Op.PUSH2[0x3bc] + Op.JUMPI + Op.DUP4 + Op.PUSH1[0xfd] + Op.EQ
        + Op.PUSH2[0x384] + Op.JUMPI + Op.DUP4 + Op.PUSH1[0xfe] + Op.EQ
        + Op.PUSH2[0x34a] + Op.JUMPI + Op.DUP4 + Op.PUSH1[0xff] + Op.EQ
        + Op.PUSH2[0x311] + Op.JUMPI + Op.DUP4 + Op.PUSH1[0xf0] + Op.EQ
        + Op.PUSH2[0x2eb] + Op.JUMPI + Op.DUP4 + Op.PUSH1[0xf5] + Op.EQ
        + Op.PUSH2[0x2c1] + Op.JUMPI + Op.POP + Op.DUP3 + Op.PUSH2[0xf0f1] + Op.EQ
        + Op.PUSH2[0x297] + Op.JUMPI + Op.DUP3 + Op.PUSH2[0xf5f1] + Op.EQ
        + Op.PUSH2[0x26b] + Op.JUMPI + Op.DUP3 + Op.PUSH2[0xf0f2] + Op.EQ
        + Op.PUSH2[0x248] + Op.JUMPI + Op.DUP3 + Op.PUSH2[0xf5f2] + Op.EQ
        + Op.PUSH2[0x223] + Op.JUMPI + Op.DUP3 + Op.PUSH2[0xf0f4] + Op.EQ
        + Op.PUSH2[0x201] + Op.JUMPI + Op.DUP3 + Op.PUSH2[0xf5f4] + Op.EQ
        + Op.PUSH2[0x1dd] + Op.JUMPI + Op.DUP3 + Op.PUSH2[0xf0fa] + Op.EQ
        + Op.PUSH2[0x1b4] + Op.JUMPI + Op.DUP3 + Op.PUSH2[0xf5fa] + Op.EQ
        + Op.PUSH2[0x189] + Op.JUMPI + Op.POP + Op.POP + Op.PUSH5[0x60baccfa57]
        + Op.EQ + Op.PUSH2[0x16e] + Op.JUMPI + Op.PUSH6[0xbad0bad0bad0]
        + Op.PUSH1[0x0] + Op.MSTORE + Op.JUMPDEST + Op.ISZERO + Op.PUSH2[0x168]
        + Op.JUMPI + Op.ISZERO + Op.PUSH2[0x168] + Op.JUMPI + Op.PUSH1[0x0] + Op.MLOAD
        + Op.PUSH1[0x0] + Op.SSTORE + Op.STOP + Op.JUMPDEST + Op.PUSH1[0x20]
        + Op.PUSH1[0x0] + Op.REVERT + Op.JUMPDEST + Op.POP + Op.PUSH2[0x3ff]
        + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.DUP2
        + Op.DUP2 + Op.DUP1 + Op.PUSH5[0x60baccfa57] + Op.GAS + Op.CALL
        + Op.PUSH2[0x156] + Op.JUMP + Op.JUMPDEST + Op.SWAP2 + Op.POP
        + Op.PUSH2[0x5a17] + Op.SWAP4 + Op.POP + Op.DUP1 + Op.SWAP3 + Op.POP
        + Op.PUSH1[0x0] + Op.DUP3 + Op.PUSH4[0xc0dec0de] + Op.EXTCODECOPY
        + Op.PUSH8[0xde0b6b3a7640000] + Op.CREATE2 + Op.PUSH1[0x20] + Op.PUSH1[0x0]
        + Op.DUP1 + Op.DUP1 + Op.DUP5 + Op.GAS + Op.STATICCALL + Op.PUSH2[0x156]
        + Op.JUMP + Op.JUMPDEST + Op.DUP2 + Op.SWAP5 + Op.POP + Op.DUP1 + Op.SWAP4
        + Op.POP + Op.PUSH1[0x0] + Op.SWAP2 + Op.SWAP3 + Op.POP + Op.PUSH4[0xc0dec0de]
        + Op.EXTCODECOPY + Op.PUSH8[0xde0b6b3a7640000] + Op.CREATE + Op.PUSH1[0x20]
        + Op.PUSH1[0x0] + Op.DUP1 + Op.DUP1 + Op.DUP5 + Op.GAS + Op.STATICCALL
        + Op.PUSH2[0x156] + Op.JUMP + Op.JUMPDEST + Op.SWAP2 + Op.POP
        + Op.PUSH2[0x5a17] + Op.SWAP4 + Op.POP + Op.DUP1 + Op.SWAP3 + Op.POP
        + Op.PUSH1[0x0] + Op.DUP3 + Op.PUSH4[0xc0dec0de] + Op.EXTCODECOPY
        + Op.PUSH1[0x0] + Op.CREATE2 + Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.DUP1
        + Op.DUP1 + Op.DUP5 + Op.GAS + Op.DELEGATECALL + Op.PUSH2[0x156] + Op.JUMP
        + Op.JUMPDEST + Op.DUP2 + Op.SWAP5 + Op.POP + Op.DUP1 + Op.SWAP4 + Op.POP
        + Op.PUSH1[0x0] + Op.SWAP2 + Op.SWAP3 + Op.POP + Op.PUSH4[0xc0dec0de]
        + Op.EXTCODECOPY + Op.PUSH1[0x0] + Op.CREATE + Op.PUSH1[0x20] + Op.PUSH1[0x0]
        + Op.DUP1 + Op.DUP1 + Op.DUP5 + Op.GAS + Op.DELEGATECALL + Op.PUSH2[0x156]
        + Op.JUMP + Op.JUMPDEST + Op.SWAP2 + Op.POP + Op.PUSH2[0x5a17] + Op.SWAP4
        + Op.POP + Op.DUP1 + Op.SWAP3 + Op.POP + Op.PUSH1[0x0] + Op.DUP3
        + Op.PUSH4[0xc0dec0de] + Op.EXTCODECOPY + Op.PUSH1[0x0] + Op.CREATE2
        + Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.DUP1 + Op.DUP1 + Op.DUP1 + Op.DUP6
        + Op.GAS + Op.CALLCODE + Op.PUSH2[0x156] + Op.JUMP + Op.JUMPDEST + Op.DUP2
        + Op.SWAP5 + Op.POP + Op.DUP1 + Op.SWAP4 + Op.POP + Op.PUSH1[0x0] + Op.SWAP2
        + Op.SWAP3 + Op.POP + Op.PUSH4[0xc0dec0de] + Op.EXTCODECOPY + Op.PUSH1[0x0]
        + Op.CREATE + Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.DUP1 + Op.DUP1 + Op.DUP1
        + Op.DUP6 + Op.GAS + Op.CALLCODE + Op.PUSH2[0x156] + Op.JUMP + Op.JUMPDEST
        + Op.SWAP2 + Op.POP + Op.PUSH2[0x5a17] + Op.SWAP4 + Op.POP + Op.DUP1
        + Op.SWAP3 + Op.POP + Op.PUSH1[0x0] + Op.DUP3 + Op.PUSH4[0xc0dec0de]
        + Op.EXTCODECOPY + Op.PUSH8[0xde0b6b3a7640000] + Op.CREATE2 + Op.PUSH1[0x20]
        + Op.PUSH1[0x0] + Op.DUP1 + Op.DUP1 + Op.DUP1 + Op.DUP6 + Op.GAS + Op.CALL
        + Op.PUSH2[0x156] + Op.JUMP + Op.JUMPDEST + Op.DUP2 + Op.SWAP5 + Op.POP
        + Op.DUP1 + Op.SWAP4 + Op.POP + Op.PUSH1[0x0] + Op.SWAP2 + Op.SWAP3 + Op.POP
        + Op.PUSH4[0xc0dec0de] + Op.EXTCODECOPY + Op.PUSH8[0xde0b6b3a7640000]
        + Op.CREATE + Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.DUP1 + Op.DUP1 + Op.DUP1
        + Op.DUP6 + Op.GAS + Op.CALL + Op.PUSH2[0x156] + Op.JUMP + Op.JUMPDEST
        + Op.SWAP3 + Op.POP + Op.SWAP1 + Op.POP + Op.PUSH2[0x5a17] + Op.SWAP3
        + Op.SWAP4 + Op.POP + Op.DUP2 + Op.PUSH1[0x0] + Op.DUP3 + Op.PUSH2[0xc0de]
        + Op.EXTCODECOPY + Op.PUSH8[0xde0b6b3a7640000] + Op.CREATE2 + Op.SWAP1
        + Op.PUSH1[0x20] + Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.DUP5 + Op.EXTCODECOPY
        + Op.PUSH2[0x156] + Op.JUMP + Op.JUMPDEST + Op.SWAP4 + Op.SWAP5 + Op.POP
        + Op.SWAP2 + Op.POP + Op.POP + Op.DUP2 + Op.PUSH1[0x0] + Op.DUP3
        + Op.PUSH2[0xc0de] + Op.EXTCODECOPY + Op.PUSH8[0xde0b6b3a7640000] + Op.CREATE
        + Op.SWAP1 + Op.PUSH1[0x20] + Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.DUP5
        + Op.EXTCODECOPY + Op.PUSH2[0x156] + Op.JUMP + Op.JUMPDEST + Op.POP + Op.POP
        + Op.POP + Op.POP + Op.BASEFEE + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x0]
        + Op.MLOAD + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x0] + Op.DUP1 + Op.DUP1
        + Op.DUP1 + Op.DUP1 + Op.PUSH4[0xdeaddead] + Op.GAS + Op.CALL + Op.POP
        + Op.BASEFEE + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x0] + Op.MLOAD
        + Op.PUSH1[0x0] + Op.SLOAD + Op.EQ + Op.PUSH2[0x156] + Op.JUMPI
        + Op.PUSH5[0xbadbadbad] + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH2[0x156]
        + Op.JUMP + Op.JUMPDEST + Op.POP + Op.POP + Op.POP + Op.POP + Op.BASEFEE
        + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x0] + Op.MLOAD + Op.PUSH1[0x0]
        + Op.SSTORE + Op.PUSH1[0x0] + Op.DUP1 + Op.DUP1 + Op.DUP1 + Op.DUP1
        + Op.PUSH3[0x60006] + Op.PUSH2[0x61a8] + Op.CALL + Op.POP + Op.BASEFEE
        + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x0] + Op.MLOAD + Op.PUSH1[0x0]
        + Op.SLOAD + Op.EQ + Op.PUSH2[0x156] + Op.JUMPI + Op.PUSH5[0xbadbadbad]
        + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH2[0x156] + Op.JUMP + Op.JUMPDEST + Op.POP
        + Op.POP + Op.POP + Op.POP + Op.BASEFEE + Op.PUSH1[0x0] + Op.MSTORE
        + Op.PUSH1[0x0] + Op.MLOAD + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x0]
        + Op.DUP1 + Op.DUP1 + Op.DUP1 + Op.DUP1 + Op.PUSH3[0x60bacc] + Op.GAS
        + Op.CALL + Op.POP + Op.BASEFEE + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x0]
        + Op.MLOAD + Op.PUSH1[0x0] + Op.SLOAD + Op.EQ + Op.PUSH2[0x156] + Op.JUMPI
        + Op.PUSH5[0xbadbadbad] + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH2[0x156]
        + Op.JUMP + Op.JUMPDEST + Op.POP + Op.POP + Op.POP + Op.POP + Op.POP
        + Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.DUP1 + Op.DUP1 + Op.PUSH4[0xca1100fa]
        + Op.GAS + Op.STATICCALL + Op.PUSH2[0x156] + Op.JUMP + Op.JUMPDEST + Op.POP
        + Op.POP + Op.POP + Op.POP + Op.POP + Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.DUP1
        + Op.DUP1 + Op.PUSH4[0xca1100fa] + Op.GAS + Op.DELEGATECALL + Op.PUSH2[0x156]
        + Op.JUMP + Op.JUMPDEST + Op.POP + Op.POP + Op.POP + Op.POP + Op.POP
        + Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.DUP1 + Op.DUP1 + Op.DUP1
        + Op.PUSH4[0xca1100fa] + Op.GAS + Op.CALLCODE + Op.PUSH2[0x156] + Op.JUMP
        + Op.JUMPDEST + Op.POP + Op.POP + Op.POP + Op.POP + Op.POP + Op.PUSH1[0x20]
        + Op.PUSH1[0x0] + Op.DUP1 + Op.DUP1 + Op.DUP1 + Op.PUSH4[0xca1100fa] + Op.GAS
        + Op.CALL + Op.PUSH2[0x156] + Op.JUMP + Op.JUMPDEST + Op.POP + Op.POP + Op.POP
        + Op.POP + Op.POP + Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.DUP1 + Op.DUP1
        + Op.PUSH4[0xca1100f4] + Op.GAS + Op.STATICCALL + Op.PUSH2[0x156] + Op.JUMP
        + Op.JUMPDEST + Op.POP + Op.POP + Op.POP + Op.POP + Op.POP + Op.PUSH1[0x20]
        + Op.PUSH1[0x0] + Op.DUP1 + Op.DUP1 + Op.PUSH4[0xca1100f4] + Op.GAS
        + Op.DELEGATECALL + Op.PUSH2[0x156] + Op.JUMP + Op.JUMPDEST + Op.POP + Op.POP
        + Op.POP + Op.POP + Op.POP + Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.DUP1
        + Op.DUP1 + Op.DUP1 + Op.PUSH4[0xca1100f4] + Op.GAS + Op.CALLCODE
        + Op.PUSH2[0x156] + Op.JUMP + Op.JUMPDEST + Op.POP + Op.POP + Op.POP + Op.POP
        + Op.POP + Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.DUP1 + Op.DUP1 + Op.DUP1
        + Op.PUSH4[0xca1100f4] + Op.GAS + Op.CALL + Op.PUSH2[0x156] + Op.JUMP
        + Op.JUMPDEST + Op.POP + Op.POP + Op.POP + Op.POP + Op.POP + Op.PUSH1[0x20]
        + Op.PUSH1[0x0] + Op.DUP1 + Op.DUP1 + Op.PUSH4[0xca1100f2] + Op.GAS
        + Op.STATICCALL + Op.PUSH2[0x156] + Op.JUMP + Op.JUMPDEST + Op.POP + Op.POP
        + Op.POP + Op.POP + Op.POP + Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.DUP1
        + Op.DUP1 + Op.PUSH4[0xca1100f2] + Op.GAS + Op.DELEGATECALL + Op.PUSH2[0x156]
        + Op.JUMP + Op.JUMPDEST + Op.POP + Op.POP + Op.POP + Op.POP + Op.POP
        + Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.DUP1 + Op.DUP1 + Op.DUP1
        + Op.PUSH4[0xca1100f2] + Op.GAS + Op.CALLCODE + Op.PUSH2[0x156] + Op.JUMP
        + Op.JUMPDEST + Op.POP + Op.POP + Op.POP + Op.POP + Op.POP + Op.PUSH1[0x20]
        + Op.PUSH1[0x0] + Op.DUP1 + Op.DUP1 + Op.DUP1 + Op.PUSH4[0xca1100f2] + Op.GAS
        + Op.CALL + Op.PUSH2[0x156] + Op.JUMP + Op.JUMPDEST + Op.POP + Op.POP + Op.POP
        + Op.POP + Op.POP + Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.DUP1 + Op.DUP1
        + Op.PUSH4[0xca1100f1] + Op.GAS + Op.STATICCALL + Op.PUSH2[0x156] + Op.JUMP
        + Op.JUMPDEST + Op.POP + Op.POP + Op.POP + Op.POP + Op.POP + Op.PUSH1[0x20]
        + Op.PUSH1[0x0] + Op.DUP1 + Op.DUP1 + Op.PUSH4[0xca1100f1] + Op.GAS
        + Op.DELEGATECALL + Op.PUSH2[0x156] + Op.JUMP + Op.JUMPDEST + Op.POP + Op.POP
        + Op.POP + Op.POP + Op.POP + Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.DUP1
        + Op.DUP1 + Op.DUP1 + Op.PUSH4[0xca1100f1] + Op.GAS + Op.CALLCODE
        + Op.PUSH2[0x156] + Op.JUMP + Op.JUMPDEST + Op.POP + Op.POP + Op.POP + Op.POP
        + Op.POP + Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.DUP1 + Op.DUP1 + Op.DUP1
        + Op.PUSH4[0xca1100f1] + Op.GAS + Op.CALL + Op.PUSH2[0x156] + Op.JUMP
        + Op.JUMPDEST + Op.POP + Op.POP + Op.POP + Op.POP + Op.POP + Op.PUSH1[0x20]
        + Op.PUSH1[0x0] + Op.DUP1 + Op.DUP1 + Op.PUSH2[0xca11] + Op.GAS
        + Op.STATICCALL + Op.PUSH2[0x156] + Op.JUMP + Op.JUMPDEST + Op.POP + Op.POP
        + Op.POP + Op.POP + Op.POP + Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.DUP1
        + Op.DUP1 + Op.PUSH2[0xca11] + Op.GAS + Op.DELEGATECALL + Op.PUSH2[0x156]
        + Op.JUMP + Op.JUMPDEST + Op.POP + Op.POP + Op.POP + Op.POP + Op.POP
        + Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.DUP1 + Op.DUP1 + Op.DUP1
        + Op.PUSH2[0xca11] + Op.GAS + Op.CALLCODE + Op.PUSH2[0x156] + Op.JUMP
        + Op.JUMPDEST + Op.POP + Op.POP + Op.POP + Op.POP + Op.POP + Op.PUSH1[0x20]
        + Op.PUSH1[0x0] + Op.DUP1 + Op.DUP1 + Op.DUP1 + Op.PUSH2[0xca11] + Op.GAS
        + Op.CALL + Op.PUSH2[0x156] + Op.JUMP + Op.JUMPDEST + Op.POP + Op.POP + Op.POP
        + Op.POP + Op.BASEFEE + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH2[0x156] + Op.JUMP
    ),
        storage={0x0: 0x60a7},
    )

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        secret_key=Hash(
            "0x45a915e4d060149eb4365960e6a7a45f334393093061116b197e3240065ff2d8"
        ),
        to=contract,
        data=tx_data,
        gas_limit=4503599627370496,
        gas_price=2000,
        nonce=1,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
