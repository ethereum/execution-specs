"""
Ported from:
tests/static/state_tests/stStaticCall/static_callcallcallcode_001Filler.json

callee code:
    push1 0x01
    push1 0x03
    mstore
    stop

callee_1 code:
    push1 0x01
    push1 0x03
    mstore
    push1 0x40
    push1 0x00
    push1 0x40
    push1 0x00
    push20 0x82d1fd8c6ed53a58bd8b065074a6b572a7ca89fa
    push3 0x0493e0
    staticcall
    pop
    push1 0x01
    push1 0x03
    mstore
    stop

callee_2 code:
    push1 0x01
    push1 0x03
    mstore
    push1 0x40
    push1 0x00
    push1 0x40
    push1 0x00
    push20 0xf18dde9381a558c4be0b84b0f3a17e22b3f9ffce
    push3 0x0493e0
    staticcall
    pop
    push1 0x01
    push1 0x03
    mstore
    stop

callee_3 code:
    push1 0x01
    push1 0x03
    sstore
    caller
    push1 0x04
    sstore
    callvalue
    push1 0x07
    sstore
    address
    push2 0x014a
    sstore
    origin
    push2 0x014c
    sstore
    calldatasize
    push2 0x0150
    sstore
    codesize
    push2 0x0152
    ... (5 more instructions)

callee_4 code:
    push1 0x01
    push1 0x03
    mstore
    push1 0x40
    push1 0x00
    push1 0x40
    push1 0x00
    push20 0x7e63847aad8ca50fb7c04777dce6871a6bf8de0c
    push3 0x03d090
    delegatecall
    pop
    push1 0x01
    push1 0x03
    mstore
    stop

callee_5 code:
    push1 0x40
    push1 0x00
    push1 0x40
    push1 0x00
    push20 0x5ccb387ab81f41f0b490664795e7004d5d14bf91
    push3 0x055730
    staticcall
    push1 0x00
    sstore
    push1 0x01
    push1 0x03
    mstore
    stop

callee_6 code:
    push1 0x40
    push1 0x00
    push1 0x40
    push1 0x00
    push20 0x69ce59f2414271f3e079542ef3893a021d7d68ea
    push3 0x055730
    staticcall
    push1 0x00
    sstore
    stop

contract code:
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    callvalue
    push1 0x00
    calldataload
    gas
    call
    push1 0x00
    sstore
    push1 0x01
    push1 0x01
    sstore
    stop

callee_7 code:
    push1 0x01
    push1 0x03
    mstore
    push1 0x40
    push1 0x00
    push1 0x40
    push1 0x00
    push20 0x335c5531b84765a7626e6e76688f18b81be5259c
    push3 0x03d090
    delegatecall
    pop
    push1 0x01
    push1 0x03
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
    ["tests/static/state_tests/stStaticCall/static_callcallcallcode_001Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex",
    [
        "0000000000000000000000009121e482add3986513a14639db36d5ec5ae41fb8",
        "000000000000000000000000bf23f3306533431b2ee5e4ca95e0a0834c090105",
    ],
    ids=['case0', 'case1'],
)
@pytest.mark.pre_alloc_mutable
def test_static_callcallcallcode_001(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xebaf50debf10e08302fe4280c32df010463ca297")
    contract = Address("0xc0e4183389eb57f779a986d8c878f89b9401dc8e")
    callee = Address("0x335c5531b84765a7626e6e76688f18b81be5259c")
    callee_1 = Address("0x5ccb387ab81f41f0b490664795e7004d5d14bf91")
    callee_2 = Address("0x69ce59f2414271f3e079542ef3893a021d7d68ea")
    callee_3 = Address("0x7e63847aad8ca50fb7c04777dce6871a6bf8de0c")
    callee_4 = Address("0x82d1fd8c6ed53a58bd8b065074a6b572a7ca89fa")
    callee_5 = Address("0x9121e482add3986513a14639db36d5ec5ae41fb8")
    callee_6 = Address("0xbf23f3306533431b2ee5e4ca95e0a0834c090105")
    callee_7 = Address("0xf18dde9381a558c4be0b84b0f3a17e22b3f9ffce")

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
        code=Op.PUSH1[0x1] + Op.PUSH1[0x3] + Op.MSTORE + Op.STOP,
    )
    pre[callee_1] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x3] + Op.MSTORE + Op.PUSH1[0x40] + Op.PUSH1[0x0]
        + Op.PUSH1[0x40] + Op.PUSH1[0x0]
        + Op.PUSH20[0x82d1fd8c6ed53a58bd8b065074a6b572a7ca89fa] + Op.PUSH3[0x493e0]
        + Op.STATICCALL + Op.POP + Op.PUSH1[0x1] + Op.PUSH1[0x3] + Op.MSTORE + Op.STOP
    ),
    )
    pre[callee_2] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x3] + Op.MSTORE + Op.PUSH1[0x40] + Op.PUSH1[0x0]
        + Op.PUSH1[0x40] + Op.PUSH1[0x0]
        + Op.PUSH20[0xf18dde9381a558c4be0b84b0f3a17e22b3f9ffce] + Op.PUSH3[0x493e0]
        + Op.STATICCALL + Op.POP + Op.PUSH1[0x1] + Op.PUSH1[0x3] + Op.MSTORE + Op.STOP
    ),
    )
    pre[callee_3] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x3] + Op.SSTORE + Op.CALLER + Op.PUSH1[0x4]
        + Op.SSTORE + Op.CALLVALUE + Op.PUSH1[0x7] + Op.SSTORE + Op.ADDRESS
        + Op.PUSH2[0x14a] + Op.SSTORE + Op.ORIGIN + Op.PUSH2[0x14c] + Op.SSTORE
        + Op.CALLDATASIZE + Op.PUSH2[0x150] + Op.SSTORE + Op.CODESIZE
        + Op.PUSH2[0x152] + Op.SSTORE + Op.GASPRICE + Op.PUSH2[0x154] + Op.SSTORE
        + Op.STOP
    ),
    )
    pre[callee_4] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x3] + Op.MSTORE + Op.PUSH1[0x40] + Op.PUSH1[0x0]
        + Op.PUSH1[0x40] + Op.PUSH1[0x0]
        + Op.PUSH20[0x7e63847aad8ca50fb7c04777dce6871a6bf8de0c] + Op.PUSH3[0x3d090]
        + Op.DELEGATECALL + Op.POP + Op.PUSH1[0x1] + Op.PUSH1[0x3] + Op.MSTORE
        + Op.STOP
    ),
    )
    pre[callee_5] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0x40] + Op.PUSH1[0x0] + Op.PUSH1[0x40] + Op.PUSH1[0x0]
        + Op.PUSH20[0x5ccb387ab81f41f0b490664795e7004d5d14bf91] + Op.PUSH3[0x55730]
        + Op.STATICCALL + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x3]
        + Op.MSTORE + Op.STOP
    ),
    )
    pre[callee_6] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0x40] + Op.PUSH1[0x0] + Op.PUSH1[0x40] + Op.PUSH1[0x0]
        + Op.PUSH20[0x69ce59f2414271f3e079542ef3893a021d7d68ea] + Op.PUSH3[0x55730]
        + Op.STATICCALL + Op.PUSH1[0x0] + Op.SSTORE + Op.STOP
    ),
    )
    pre[contract] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.CALLVALUE
        + Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.GAS + Op.CALL + Op.PUSH1[0x0]
        + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.STOP
    ),
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_7] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x3] + Op.MSTORE + Op.PUSH1[0x40] + Op.PUSH1[0x0]
        + Op.PUSH1[0x40] + Op.PUSH1[0x0]
        + Op.PUSH20[0x335c5531b84765a7626e6e76688f18b81be5259c] + Op.PUSH3[0x3d090]
        + Op.DELEGATECALL + Op.POP + Op.PUSH1[0x1] + Op.PUSH1[0x3] + Op.MSTORE
        + Op.STOP
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


@pytest.mark.ported_from(
    ["tests/static/state_tests/stStaticCall/static_callcallcallcode_001_2Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex",
    [
        "0000000000000000000000002f9ec0afcb4edcd7d38c6a48f5e36038263ca3cd",
        "000000000000000000000000bf23f3306533431b2ee5e4ca95e0a0834c090105",
    ],
    ids=['case0', 'case1'],
)
@pytest.mark.pre_alloc_mutable
def test_static_callcallcallcode_001_2(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xebaf50debf10e08302fe4280c32df010463ca297")
    contract = Address("0xe4552fdc3736d39144e64ad1a1e8253017b0c974")
    callee = Address("0x0ffffaeb931552e5f094ca96a70be612da56b887")
    callee_1 = Address("0x2881a083ea775f78057a93f73110241fdb7398a9")
    callee_2 = Address("0x2f9ec0afcb4edcd7d38c6a48f5e36038263ca3cd")
    callee_3 = Address("0x335c5531b84765a7626e6e76688f18b81be5259c")
    callee_4 = Address("0x52bc8086d7f6ac48937cf1b98dfc6f4be0f75112")
    callee_5 = Address("0x5517c40699ceb16c4eb71f2b0d841078c198560e")
    callee_6 = Address("0xb4631a307a08abc5d5a582549b23cb98a7c5beb2")
    callee_7 = Address("0xbf23f3306533431b2ee5e4ca95e0a0834c090105")

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
        Op.PUSH1[0x40] + Op.PUSH1[0x0] + Op.PUSH1[0x40] + Op.PUSH1[0x0]
        + Op.PUSH1[0x3] + Op.PUSH20[0x2881a083ea775f78057a93f73110241fdb7398a9]
        + Op.PUSH3[0x3d090] + Op.CALLCODE + Op.PUSH1[0x2] + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee_1] = Account(
        balance=0,
        nonce=0,
        code=Op.PUSH4[0x11223344] + Op.PUSH1[0x1] + Op.MSTORE + Op.STOP,
    )
    pre[callee_2] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0x40] + Op.PUSH1[0x0] + Op.PUSH1[0x40] + Op.PUSH1[0x0]
        + Op.PUSH20[0x52bc8086d7f6ac48937cf1b98dfc6f4be0f75112] + Op.PUSH3[0x55730]
        + Op.STATICCALL + Op.PUSH1[0x0] + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee_3] = Account(
        balance=0,
        nonce=0,
        code=Op.PUSH1[0x1] + Op.PUSH1[0x3] + Op.MSTORE + Op.STOP,
    )
    pre[callee_4] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0x40] + Op.PUSH1[0x0] + Op.PUSH1[0x40] + Op.PUSH1[0x0]
        + Op.PUSH20[0xffffaeb931552e5f094ca96a70be612da56b887] + Op.PUSH3[0x493e0]
        + Op.STATICCALL + Op.POP + Op.PUSH1[0x1] + Op.PUSH1[0x3] + Op.MSTORE + Op.STOP
    ),
    )
    pre[callee_5] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x4] + Op.MSTORE + Op.PUSH1[0x40] + Op.PUSH1[0x0]
        + Op.PUSH1[0x40] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0x335c5531b84765a7626e6e76688f18b81be5259c] + Op.PUSH3[0x3d090]
        + Op.CALLCODE + Op.POP + Op.PUSH1[0x1] + Op.PUSH1[0x6] + Op.MSTORE + Op.STOP
    ),
    )
    pre[callee_6] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0x40] + Op.PUSH1[0x0] + Op.PUSH1[0x40] + Op.PUSH1[0x0]
        + Op.PUSH20[0x5517c40699ceb16c4eb71f2b0d841078c198560e] + Op.PUSH3[0x493e0]
        + Op.STATICCALL + Op.POP + Op.PUSH1[0x1] + Op.PUSH1[0x3] + Op.MSTORE + Op.STOP
    ),
    )
    pre[callee_7] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0x40] + Op.PUSH1[0x0] + Op.PUSH1[0x40] + Op.PUSH1[0x0]
        + Op.PUSH20[0xb4631a307a08abc5d5a582549b23cb98a7c5beb2] + Op.PUSH3[0x55730]
        + Op.STATICCALL + Op.PUSH1[0x0] + Op.SSTORE + Op.STOP
    ),
    )
    pre[contract] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.CALLVALUE
        + Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.GAS + Op.CALL + Op.PUSH1[0x0]
        + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.STOP
    ),
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000, nonce=0)

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
