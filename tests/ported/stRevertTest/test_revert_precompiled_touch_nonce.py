"""
Ported from:
tests/static/state_tests/stRevertTest/RevertPrecompiledTouch_nonceFiller.json

callee_1 code:
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x01
    push2 0xc350
    staticcall
    pop
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x02
    push2 0xc350
    staticcall
    pop
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    ... (54 more instructions)

callee_2 code:
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x01
    push2 0xc350
    delegatecall
    pop
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x02
    push2 0xc350
    delegatecall
    pop
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    ... (54 more instructions)

callee_5 code:
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x01
    push2 0xc350
    call
    pop
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x02
    push2 0xc350
    call
    pop
    push1 0x00
    push1 0x00
    ... (62 more instructions)

callee_9 code:
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x01
    push2 0xc350
    callcode
    pop
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x02
    push2 0xc350
    callcode
    pop
    push1 0x00
    push1 0x00
    ... (62 more instructions)

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
    ["tests/static/state_tests/stRevertTest/RevertPrecompiledTouch_nonceFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex",
    [
        "00000000000000000000000087aaeb9e422487283b0b008ef445e32acb9dd1ae",
        "00000000000000000000000031f52a66cf9d94c60f089a2ca9c4e784261c57fa",
        "000000000000000000000000de1200b7ecaea2d15b57d0f331ad5ade8e924255",
        "00000000000000000000000010ef6d6218ada53728683cec4d5160c8c72159bd",
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_revert_precompiled_touch_nonce(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x68795c4aa09d6f4ed3e5deddf8c2ad3049a601da")
    sender = Address("0xadd22153059388891d82c6c8e08d80845352bbb0")
    contract = Address("0xe7c596de24ccc387daa5c017066aeb25ea8d2f3f")
    callee = Address("0x05a4faf1ede8e96aae92ae51915074e42787f868")
    callee_1 = Address("0x10ef6d6218ada53728683cec4d5160c8c72159bd")
    callee_2 = Address("0x31f52a66cf9d94c60f089a2ca9c4e784261c57fa")
    callee_3 = Address("0x4ba6259bb96e9d7822a5fb3a1f8037bc68a08d43")
    callee_4 = Address("0x6a22458e937f487e2daffa193b9c5fb610dc4789")
    callee_5 = Address("0x87aaeb9e422487283b0b008ef445e32acb9dd1ae")
    callee_6 = Address("0x8d1d883976df004b96c383782a828dc5bc82ef9d")
    callee_7 = Address("0xb478e245708be95c33c6c35dea161c0429d02dd2")
    callee_8 = Address("0xbeb47e021a70649b079c4bdf150108c0d8c6accb")
    callee_9 = Address("0xde1200b7ecaea2d15b57d0f331ad5ade8e924255")
    callee_10 = Address("0xeb201d2887816e041f6e807e804f64f3a7a226fe")
    callee_11 = Address("0xf8f0aec70f4bbdadce829783a0afff43f384c640")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=4012015,
    )

    pre[callee] = Account(balance=0, nonce=1)
    pre[callee_1] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x1] + Op.PUSH2[0xc350] + Op.STATICCALL + Op.POP + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x2]
        + Op.PUSH2[0xc350] + Op.STATICCALL + Op.POP + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x3] + Op.PUSH2[0xc350]
        + Op.STATICCALL + Op.POP + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x4] + Op.PUSH2[0xc350] + Op.STATICCALL + Op.POP
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x5] + Op.PUSH2[0xc350] + Op.STATICCALL + Op.POP + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x6]
        + Op.PUSH2[0xc350] + Op.STATICCALL + Op.POP + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x7] + Op.PUSH2[0xc350]
        + Op.STATICCALL + Op.POP + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x8] + Op.PUSH2[0xc350] + Op.STATICCALL + Op.POP
        + Op.GAS + Op.PUSH1[0x1] + Op.SSTORE + Op.GAS + Op.PUSH1[0x2] + Op.SSTORE
        + Op.GAS + Op.PUSH1[0x3] + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee_2] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x1] + Op.PUSH2[0xc350] + Op.DELEGATECALL + Op.POP + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x2]
        + Op.PUSH2[0xc350] + Op.DELEGATECALL + Op.POP + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x3] + Op.PUSH2[0xc350]
        + Op.DELEGATECALL + Op.POP + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x4] + Op.PUSH2[0xc350] + Op.DELEGATECALL + Op.POP
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x5] + Op.PUSH2[0xc350] + Op.DELEGATECALL + Op.POP + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x6]
        + Op.PUSH2[0xc350] + Op.DELEGATECALL + Op.POP + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x7] + Op.PUSH2[0xc350]
        + Op.DELEGATECALL + Op.POP + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x8] + Op.PUSH2[0xc350] + Op.DELEGATECALL + Op.POP
        + Op.GAS + Op.PUSH1[0x1] + Op.SSTORE + Op.GAS + Op.PUSH1[0x2] + Op.SSTORE
        + Op.GAS + Op.PUSH1[0x3] + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee_3] = Account(balance=0, nonce=1)
    pre[callee_4] = Account(balance=0, nonce=1)
    pre[callee_5] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x1] + Op.PUSH2[0xc350] + Op.CALL + Op.POP
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x2] + Op.PUSH2[0xc350] + Op.CALL + Op.POP
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x3] + Op.PUSH2[0xc350] + Op.CALL + Op.POP
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x4] + Op.PUSH2[0xc350] + Op.CALL + Op.POP
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x5] + Op.PUSH2[0xc350] + Op.CALL + Op.POP
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x6] + Op.PUSH2[0xc350] + Op.CALL + Op.POP
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x7] + Op.PUSH2[0xc350] + Op.CALL + Op.POP
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x8] + Op.PUSH2[0xc350] + Op.CALL + Op.POP + Op.GAS
        + Op.PUSH1[0x1] + Op.SSTORE + Op.GAS + Op.PUSH1[0x2] + Op.SSTORE + Op.GAS
        + Op.PUSH1[0x3] + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee_6] = Account(balance=0, nonce=1)
    pre[sender] = Account(balance=0xde0b6b3a7640000, nonce=1)
    pre[callee_7] = Account(balance=0, nonce=1)
    pre[callee_8] = Account(balance=0, nonce=1)
    pre[callee_9] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x1] + Op.PUSH2[0xc350] + Op.CALLCODE + Op.POP
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x2] + Op.PUSH2[0xc350] + Op.CALLCODE + Op.POP
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x3] + Op.PUSH2[0xc350] + Op.CALLCODE + Op.POP
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x4] + Op.PUSH2[0xc350] + Op.CALLCODE + Op.POP
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x5] + Op.PUSH2[0xc350] + Op.CALLCODE + Op.POP
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x6] + Op.PUSH2[0xc350] + Op.CALLCODE + Op.POP
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x7] + Op.PUSH2[0xc350] + Op.CALLCODE + Op.POP
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x8] + Op.PUSH2[0xc350] + Op.CALLCODE + Op.POP
        + Op.GAS + Op.PUSH1[0x1] + Op.SSTORE + Op.GAS + Op.PUSH1[0x2] + Op.SSTORE
        + Op.GAS + Op.PUSH1[0x3] + Op.SSTORE + Op.STOP
    ),
    )
    pre[contract] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.GAS + Op.CALLCODE
        + Op.STOP
    ),
    )
    pre[callee_10] = Account(balance=0, nonce=1)
    pre[callee_11] = Account(balance=0, nonce=1)

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        secret_key=Hash(
            "0x0ff8d58222f34f6890ddaa468c023b77d6691ed7d3c4dcddae38336212faf54b"
        ),
        to=contract,
        data=tx_data,
        gas_limit=100000,
        gas_price=10,
        nonce=1,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
