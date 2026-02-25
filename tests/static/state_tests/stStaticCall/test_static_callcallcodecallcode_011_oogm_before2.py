"""
Ported from:
tests/static/state_tests/stStaticCall/static_callcallcodecallcode_011_OOGMBefore2Filler.json

callee code:
    jumpdest
    push2 0xc350
    push1 0x80
    mload
    lt
    iszero
    push1 0x1c
    jumpi
    push1 0x01
    extcodesize
    pop
    push1 0x01
    push1 0x80
    mload
    add
    push1 0x80
    mstore
    push1 0x00
    jump
    jumpdest
    ... (13 more instructions)

contract code:
    push1 0x00
    calldataload
    push1 0x00
    mstore
    push1 0x40
    push1 0x00
    push1 0x40
    push1 0x00
    push20 0x8bde6a10a1792232fd09b528800d9ac2a6835424
    push3 0x0249f0
    staticcall
    push1 0x00
    sstore
    push1 0x01
    push1 0x01
    sstore
    stop

callee_1 code:
    push1 0x01
    push1 0x03
    sstore
    push1 0x40
    push1 0x00
    push1 0x40
    push1 0x00
    push1 0x00
    push20 0xd4286ac3fcac436406bc95f5b0176ad49aed7f7c
    push2 0x4e34
    callcode
    pop
    push1 0x01
    push1 0x20
    mstore
    stop

callee_2 code:
    push1 0x01
    push1 0x20
    mstore
    push1 0x40
    push1 0x00
    push1 0x40
    push1 0x00
    push1 0x00
    push1 0x00
    calldataload
    push2 0x9c90
    callcode
    pop
    push1 0x01
    push1 0x20
    mstore
    stop

callee_3 code:
    push1 0x40
    push1 0x00
    push1 0x40
    push1 0x00
    push1 0x01
    push20 0xd4286ac3fcac436406bc95f5b0176ad49aed7f7c
    push2 0x4e34
    callcode
    pop
    push1 0x01
    push1 0x20
    mstore
    stop

callee_4 code:
    push1 0x01
    push1 0x20
    mstore
    stop
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
    ["tests/static/state_tests/stStaticCall/static_callcallcodecallcode_011_OOGMBefore2Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex",
    [
        "00000000000000000000000087f0bb05316a8d8146646a151a64f38ae9d25176",
        "0000000000000000000000001dffdbfbe33709f17b6e90137242c109917a994b",
        "00000000000000000000000094c82267a4e8333afb80073fbaed3fe5973adc7c",
    ],
    ids=['case0', 'case1', 'case2'],
)
@pytest.mark.pre_alloc_mutable
def test_static_callcallcodecallcode_011_oogm_before2(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xebaf50debf10e08302fe4280c32df010463ca297")
    contract = Address("0x6e143211e9d36eaeebe65f6ed69d6c28500040d6")
    callee = Address("0x1dffdbfbe33709f17b6e90137242c109917a994b")
    callee_1 = Address("0x87f0bb05316a8d8146646a151a64f38ae9d25176")
    callee_2 = Address("0x8bde6a10a1792232fd09b528800d9ac2a6835424")
    callee_3 = Address("0x94c82267a4e8333afb80073fbaed3fe5973adc7c")
    callee_4 = Address("0xd4286ac3fcac436406bc95f5b0176ad49aed7f7c")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=30000000,
    )

    pre[callee] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.JUMPDEST + Op.PUSH2[0xc350] + Op.PUSH1[0x80] + Op.MLOAD + Op.LT
        + Op.ISZERO + Op.PUSH1[0x1c] + Op.JUMPI + Op.PUSH1[0x1] + Op.EXTCODESIZE
        + Op.POP + Op.PUSH1[0x1] + Op.PUSH1[0x80] + Op.MLOAD + Op.ADD + Op.PUSH1[0x80]
        + Op.MSTORE + Op.PUSH1[0x0] + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x40]
        + Op.PUSH1[0x0] + Op.PUSH1[0x40] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0xd4286ac3fcac436406bc95f5b0176ad49aed7f7c] + Op.PUSH2[0x4e34]
        + Op.CALLCODE + Op.POP + Op.PUSH1[0x1] + Op.PUSH1[0x20] + Op.MSTORE + Op.STOP
    ),
    )
    pre[contract] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x40]
        + Op.PUSH1[0x0] + Op.PUSH1[0x40] + Op.PUSH1[0x0]
        + Op.PUSH20[0x8bde6a10a1792232fd09b528800d9ac2a6835424] + Op.PUSH3[0x249f0]
        + Op.STATICCALL + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee_1] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x3] + Op.SSTORE + Op.PUSH1[0x40] + Op.PUSH1[0x0]
        + Op.PUSH1[0x40] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0xd4286ac3fcac436406bc95f5b0176ad49aed7f7c] + Op.PUSH2[0x4e34]
        + Op.CALLCODE + Op.POP + Op.PUSH1[0x1] + Op.PUSH1[0x20] + Op.MSTORE + Op.STOP
    ),
    )
    pre[callee_2] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x20] + Op.MSTORE + Op.PUSH1[0x40] + Op.PUSH1[0x0]
        + Op.PUSH1[0x40] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.CALLDATALOAD + Op.PUSH2[0x9c90] + Op.CALLCODE + Op.POP + Op.PUSH1[0x1]
        + Op.PUSH1[0x20] + Op.MSTORE + Op.STOP
    ),
    )
    pre[callee_3] = Account(
        balance=10,
        nonce=0,
        code=(
        Op.PUSH1[0x40] + Op.PUSH1[0x0] + Op.PUSH1[0x40] + Op.PUSH1[0x0]
        + Op.PUSH1[0x1] + Op.PUSH20[0xd4286ac3fcac436406bc95f5b0176ad49aed7f7c]
        + Op.PUSH2[0x4e34] + Op.CALLCODE + Op.POP + Op.PUSH1[0x1] + Op.PUSH1[0x20]
        + Op.MSTORE + Op.STOP
    ),
    )
    pre[callee_4] = Account(
        balance=0,
        nonce=0,
        code=Op.PUSH1[0x1] + Op.PUSH1[0x20] + Op.MSTORE + Op.STOP,
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        secret_key=Hash(
            "0xe04d1ac7ddda0c98397d56a0b501e960d4cd325a39286919ac23c1a07009a869"
        ),
        to=contract,
        data=tx_data,
        gas_limit=172000,
        gas_price=10,
        nonce=0,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
