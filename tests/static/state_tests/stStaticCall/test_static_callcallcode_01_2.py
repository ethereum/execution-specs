"""
Ported from:
tests/static/state_tests/stStaticCall/static_callcallcode_01_2Filler.json

callee code:
    push1 0x40
    push1 0x00
    push1 0x20
    push1 0x00
    push1 0x02
    push20 0x8ad8d964b0888c5016605939dd13e1bdcf679f05
    push3 0x03d090
    callcode
    stop

callee_1 code:
    push4 0x11223344
    push1 0x00
    mstore
    stop

callee_2 code:
    push4 0x11223344
    push1 0x00
    mstore
    stop

contract code:
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    calldataload
    gas
    callcode
    push1 0x00
    sstore
    push1 0x01
    push1 0x01
    sstore
    stop

callee_3 code:
    push1 0x40
    push1 0x00
    push1 0x20
    push1 0x00
    push20 0xf686a2e0e79c5fbb3407d5e53f3ab6b0ab21a51a
    push3 0x055730
    staticcall
    stop

callee_4 code:
    push1 0x00
    calldataload
    push1 0x00
    mstore
    push1 0x40
    push1 0x00
    push1 0x20
    push1 0x00
    push1 0x00
    push20 0x2fcc143c5267b6c6ce4e1abd936e84eedffd6a4e
    push3 0x03d090
    callcode
    stop

callee_5 code:
    push1 0x40
    push1 0x00
    push1 0x20
    push1 0x00
    push20 0x0c42c1601b039f8bb80a155b5b6afb4cffeb430a
    push3 0x055730
    staticcall
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
    ["tests/static/state_tests/stStaticCall/static_callcallcode_01_2Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex",
    [
        "000000000000000000000000fbe34b488c83765de2f7fefc646710b8f1dcb303",
        "000000000000000000000000c766dcc7257dd2af2b6a354fc922d43d3ad9a390",
    ],
    ids=['case0', 'case1'],
)
@pytest.mark.pre_alloc_mutable
def test_static_callcallcode_01_2(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xebaf50debf10e08302fe4280c32df010463ca297")
    contract = Address("0xaab59f13d96113334fab5c68e4e62b61f6cbf647")
    callee = Address("0x0c42c1601b039f8bb80a155b5b6afb4cffeb430a")
    callee_1 = Address("0x2fcc143c5267b6c6ce4e1abd936e84eedffd6a4e")
    callee_2 = Address("0x8ad8d964b0888c5016605939dd13e1bdcf679f05")
    callee_3 = Address("0xc766dcc7257dd2af2b6a354fc922d43d3ad9a390")
    callee_4 = Address("0xf686a2e0e79c5fbb3407d5e53f3ab6b0ab21a51a")
    callee_5 = Address("0xfbe34b488c83765de2f7fefc646710b8f1dcb303")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=30000000,
    )

    pre[callee] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0x40] + Op.PUSH1[0x0] + Op.PUSH1[0x20] + Op.PUSH1[0x0]
        + Op.PUSH1[0x2] + Op.PUSH20[0x8ad8d964b0888c5016605939dd13e1bdcf679f05]
        + Op.PUSH3[0x3d090] + Op.CALLCODE + Op.STOP
    ),
    )
    pre[callee_1] = Account(
        balance=0,
        nonce=0,
        code=Op.PUSH4[0x11223344] + Op.PUSH1[0x0] + Op.MSTORE + Op.STOP,
    )
    pre[callee_2] = Account(
        balance=0,
        nonce=0,
        code=Op.PUSH4[0x11223344] + Op.PUSH1[0x0] + Op.MSTORE + Op.STOP,
    )
    pre[contract] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.GAS + Op.CALLCODE
        + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE
        + Op.STOP
    ),
    )
    pre[callee_3] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0x40] + Op.PUSH1[0x0] + Op.PUSH1[0x20] + Op.PUSH1[0x0]
        + Op.PUSH20[0xf686a2e0e79c5fbb3407d5e53f3ab6b0ab21a51a] + Op.PUSH3[0x55730]
        + Op.STATICCALL + Op.STOP
    ),
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_4] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x40]
        + Op.PUSH1[0x0] + Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0x2fcc143c5267b6c6ce4e1abd936e84eedffd6a4e] + Op.PUSH3[0x3d090]
        + Op.CALLCODE + Op.STOP
    ),
    )
    pre[callee_5] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0x40] + Op.PUSH1[0x0] + Op.PUSH1[0x20] + Op.PUSH1[0x0]
        + Op.PUSH20[0xc42c1601b039f8bb80a155b5b6afb4cffeb430a] + Op.PUSH3[0x55730]
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
        gas_limit=3000000,
        gas_price=10,
        nonce=0,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
