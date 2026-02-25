"""
Ported from:
tests/static/state_tests/stStaticCall/static_callcallcodecall_010_OOGMBeforeFiller.json

contract code:
    push1 0x00
    calldataload
    push1 0x00
    mstore
    push1 0x40
    push1 0x00
    push1 0x40
    push1 0x00
    push20 0xe7b982648e452964fb0ac2b867efa7c7b5b93d91
    push3 0x07a120
    staticcall
    push1 0x00
    sstore
    push1 0x01
    push1 0x01
    sstore
    stop

callee code:
    push1 0x01
    push1 0x03
    mstore
    stop

callee_1 code:
    push1 0x01
    push1 0x03
    sstore
    push1 0x40
    push1 0x00
    push1 0x40
    push1 0x00
    push20 0x335c5531b84765a7626e6e76688f18b81be5259c
    push3 0x01d4d4
    staticcall
    stop

callee_2 code:
    push1 0x40
    push1 0x00
    push1 0x40
    push1 0x00
    push1 0x00
    calldataload
    push3 0x061ad0
    delegatecall
    stop

callee_3 code:
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
    ... (8 more instructions)
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
    ["tests/static/state_tests/stStaticCall/static_callcallcodecall_010_OOGMBeforeFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex",
    [
        "000000000000000000000000c5b28f694c0e1befb55bdfbec30be55455897729",
        "000000000000000000000000f32619344056ad22a07f10433f70165ce82d9273",
    ],
    ids=['case0', 'case1'],
)
@pytest.mark.pre_alloc_mutable
def test_static_callcallcodecall_010_oogm_before(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xebaf50debf10e08302fe4280c32df010463ca297")
    contract = Address("0x33344ff747b678f9e86028b0c745d8ab0e0d1792")
    callee = Address("0x335c5531b84765a7626e6e76688f18b81be5259c")
    callee_1 = Address("0xc5b28f694c0e1befb55bdfbec30be55455897729")
    callee_2 = Address("0xe7b982648e452964fb0ac2b867efa7c7b5b93d91")
    callee_3 = Address("0xf32619344056ad22a07f10433f70165ce82d9273")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=30000000,
    )

    pre[contract] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x40]
        + Op.PUSH1[0x0] + Op.PUSH1[0x40] + Op.PUSH1[0x0]
        + Op.PUSH20[0xe7b982648e452964fb0ac2b867efa7c7b5b93d91] + Op.PUSH3[0x7a120]
        + Op.STATICCALL + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee] = Account(
        balance=0,
        nonce=0,
        code=Op.PUSH1[0x1] + Op.PUSH1[0x3] + Op.MSTORE + Op.STOP,
    )
    pre[callee_1] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x3] + Op.SSTORE + Op.PUSH1[0x40] + Op.PUSH1[0x0]
        + Op.PUSH1[0x40] + Op.PUSH1[0x0]
        + Op.PUSH20[0x335c5531b84765a7626e6e76688f18b81be5259c] + Op.PUSH3[0x1d4d4]
        + Op.STATICCALL + Op.STOP
    ),
    )
    pre[callee_2] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x40] + Op.PUSH1[0x0] + Op.PUSH1[0x40] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH3[0x61ad0] + Op.DELEGATECALL
        + Op.STOP
    ),
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_3] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.JUMPDEST + Op.PUSH2[0xc350] + Op.PUSH1[0x80] + Op.MLOAD + Op.LT
        + Op.ISZERO + Op.PUSH1[0x1c] + Op.JUMPI + Op.PUSH1[0x1] + Op.EXTCODESIZE
        + Op.POP + Op.PUSH1[0x1] + Op.PUSH1[0x80] + Op.MLOAD + Op.ADD + Op.PUSH1[0x80]
        + Op.MSTORE + Op.PUSH1[0x0] + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x40]
        + Op.PUSH1[0x0] + Op.PUSH1[0x40] + Op.PUSH1[0x0]
        + Op.PUSH20[0x335c5531b84765a7626e6e76688f18b81be5259c] + Op.PUSH2[0x4e34]
        + Op.STATICCALL + Op.STOP
    ),
    )

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        secret_key=Hash(
            "0xe04d1ac7ddda0c98397d56a0b501e960d4cd325a39286919ac23c1a07009a869"
        ),
        to=contract,
        data=tx_data,
        gas_limit=1720000,
        gas_price=10,
        nonce=0,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
