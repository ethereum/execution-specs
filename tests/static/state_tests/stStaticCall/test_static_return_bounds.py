"""
Ported from:
tests/static/state_tests/stStaticCall/static_RETURN_BoundsFiller.json

callee code:
    push4 0x0fffffff
    push4 0x0fffffff
    return
    stop

callee_1 code:
    push8 0xffffffffffffffff
    push1 0x00
    return
    stop

callee_2 code:
    push14 0x0fffffffffffffffffffffffffff
    push14 0x0fffffffffffffffffffffffffff
    return
    stop

callee_3 code:
    push32 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff
    push1 0x00
    return
    stop

callee_4 code:
    push4 0xffffffff
    push1 0x00
    return
    stop

callee_5 code:
    push8 0xffffffffffffffff
    push8 0xffffffffffffffff
    return
    stop

callee_6 code:
    push1 0x00
    push32 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff
    return
    stop

callee_7 code:
    push1 0x00
    push1 0x00
    return
    stop

callee_8 code:
    push4 0x0fffffff
    push1 0x00
    return
    stop

callee_9 code:
    push32 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff
    push32 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff
    return
    stop

callee_10 code:
    push1 0x00
    push14 0x0fffffffffffffffffffffffffff
    return
    stop

callee_11 code:
    push1 0x00
    push8 0xffffffffffffffff
    return
    stop

callee_12 code:
    push4 0xffffffff
    push4 0xffffffff
    return
    stop

callee_13 code:
    push1 0x00
    push4 0x0fffffff
    return
    stop

contract code:
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0x5efbf04d8e1cc5b6b3719b16b5744a09bacfc18b
    push8 0x07ffffffffffffff
    staticcall
    push1 0x01
    sstore
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0xc7aa750fe05c7e38475a49fe98a301024d0c1d54
    push8 0x07ffffffffffffff
    staticcall
    push1 0x02
    sstore
    push1 0x00
    push1 0x00
    ... (125 more instructions)

callee_14 code:
    push14 0x0fffffffffffffffffffffffffff
    push1 0x00
    return
    stop

callee_15 code:
    push1 0x00
    push4 0xffffffff
    return
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
    ["tests/static/state_tests/stStaticCall/static_RETURN_BoundsFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_static_return_bounds(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xa99635038e8d9ab237a31179dd5c9087713f723a")
    contract = Address("0xdaaed08adba0dd97804c34dd17b55766d54fc392")
    callee = Address("0x07084994c5891b1467d74bedb0477da4909e4c0e")
    callee_1 = Address("0x0b09ca4308585f026b8d02be147fea0739ec463a")
    callee_2 = Address("0x2548bda95a3831abcd613f4d24e4634615a71cca")
    callee_3 = Address("0x28463490948d21efc49949b4d394989bf52c57f1")
    callee_4 = Address("0x2ceb88d6c420e5c65593d9ebed9a25600ab9e113")
    callee_5 = Address("0x416408c1d7fda274ddeb45ffe4817068808121ca")
    callee_6 = Address("0x4912bc7b66a3bf27adfa54ab049e90e8c9c4dc63")
    callee_7 = Address("0x5efbf04d8e1cc5b6b3719b16b5744a09bacfc18b")
    callee_8 = Address("0x7266f1c07958d55ce36de0592604f1a915bdf1c2")
    callee_9 = Address("0x76006c948f3a0529479c6d18a6f95908426e8092")
    callee_10 = Address("0x7a4461ac9f9cd13f40f9514a7c60e23a71c1dff3")
    callee_11 = Address("0x7bbcf24c83493c4e733cb54079b51873d3211ad2")
    callee_12 = Address("0xad7754a8a56cc5ad4e319fa94194e435628dee67")
    callee_13 = Address("0xc7aa750fe05c7e38475a49fe98a301024d0c1d54")
    callee_14 = Address("0xf519de4dcb9aaa53f8f0db9b18c715c928caade8")
    callee_15 = Address("0xff6b6d23be161344e86eb7b174acedd4b1dc6dc7")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=9223372036854775807,
    )

    pre[callee] = Account(
        balance=0,
        nonce=0,
        code=Op.PUSH4[0xfffffff] + Op.PUSH4[0xfffffff] + Op.RETURN + Op.STOP,
    )
    pre[callee_1] = Account(
        balance=0,
        nonce=0,
        code=Op.PUSH8[0xffffffffffffffff] + Op.PUSH1[0x0] + Op.RETURN + Op.STOP,
    )
    pre[callee_2] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH14[0xfffffffffffffffffffffffffff]
        + Op.PUSH14[0xfffffffffffffffffffffffffff] + Op.RETURN + Op.STOP
    ),
    )
    pre[callee_3] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH32[0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff]
        + Op.PUSH1[0x0] + Op.RETURN + Op.STOP
    ),
    )
    pre[callee_4] = Account(
        balance=0,
        nonce=0,
        code=Op.PUSH4[0xffffffff] + Op.PUSH1[0x0] + Op.RETURN + Op.STOP,
    )
    pre[callee_5] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH8[0xffffffffffffffff] + Op.PUSH8[0xffffffffffffffff] + Op.RETURN
        + Op.STOP
    ),
    )
    pre[callee_6] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x0]
        + Op.PUSH32[0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff]
        + Op.RETURN + Op.STOP
    ),
    )
    pre[callee_7] = Account(
        balance=0,
        nonce=0,
        code=Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.RETURN + Op.STOP,
    )
    pre[callee_8] = Account(
        balance=0,
        nonce=0,
        code=Op.PUSH4[0xfffffff] + Op.PUSH1[0x0] + Op.RETURN + Op.STOP,
    )
    pre[callee_9] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH32[0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff]
        + Op.PUSH32[0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff]
        + Op.RETURN + Op.STOP
    ),
    )
    pre[callee_10] = Account(
        balance=0,
        nonce=0,
        code=Op.PUSH1[0x0] + Op.PUSH14[0xfffffffffffffffffffffffffff] + Op.RETURN + Op.STOP,
    )
    pre[callee_11] = Account(
        balance=0,
        nonce=0,
        code=Op.PUSH1[0x0] + Op.PUSH8[0xffffffffffffffff] + Op.RETURN + Op.STOP,
    )
    pre[sender] = Account(
        balance=0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff,
        nonce=0,
    )
    pre[callee_12] = Account(
        balance=0,
        nonce=0,
        code=Op.PUSH4[0xffffffff] + Op.PUSH4[0xffffffff] + Op.RETURN + Op.STOP,
    )
    pre[callee_13] = Account(
        balance=0,
        nonce=0,
        code=Op.PUSH1[0x0] + Op.PUSH4[0xfffffff] + Op.RETURN + Op.STOP,
    )
    pre[contract] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0x5efbf04d8e1cc5b6b3719b16b5744a09bacfc18b]
        + Op.PUSH8[0x7ffffffffffffff] + Op.STATICCALL + Op.PUSH1[0x1] + Op.SSTORE
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0xc7aa750fe05c7e38475a49fe98a301024d0c1d54]
        + Op.PUSH8[0x7ffffffffffffff] + Op.STATICCALL + Op.PUSH1[0x2] + Op.SSTORE
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0xff6b6d23be161344e86eb7b174acedd4b1dc6dc7]
        + Op.PUSH8[0x7ffffffffffffff] + Op.STATICCALL + Op.PUSH1[0x3] + Op.SSTORE
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0x7bbcf24c83493c4e733cb54079b51873d3211ad2]
        + Op.PUSH8[0x7ffffffffffffff] + Op.STATICCALL + Op.PUSH1[0x4] + Op.SSTORE
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0x7a4461ac9f9cd13f40f9514a7c60e23a71c1dff3]
        + Op.PUSH8[0x7ffffffffffffff] + Op.STATICCALL + Op.PUSH1[0x5] + Op.SSTORE
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0x4912bc7b66a3bf27adfa54ab049e90e8c9c4dc63]
        + Op.PUSH8[0x7ffffffffffffff] + Op.STATICCALL + Op.PUSH1[0x6] + Op.SSTORE
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0x4912bc7b66a3bf27adfa54ab049e90e8c9c4dc63]
        + Op.PUSH8[0x7ffffffffffffff] + Op.STATICCALL + Op.PUSH1[0x7] + Op.SSTORE
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0x4912bc7b66a3bf27adfa54ab049e90e8c9c4dc63]
        + Op.PUSH8[0x7ffffffffffffff] + Op.STATICCALL + Op.PUSH1[0x8] + Op.SSTORE
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0x4912bc7b66a3bf27adfa54ab049e90e8c9c4dc63]
        + Op.PUSH8[0x7ffffffffffffff] + Op.STATICCALL + Op.PUSH1[0x9] + Op.SSTORE
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0x4912bc7b66a3bf27adfa54ab049e90e8c9c4dc63]
        + Op.PUSH8[0x7ffffffffffffff] + Op.STATICCALL + Op.PUSH1[0xa] + Op.SSTORE
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0x4912bc7b66a3bf27adfa54ab049e90e8c9c4dc63]
        + Op.PUSH8[0x7ffffffffffffff] + Op.STATICCALL + Op.PUSH1[0xb] + Op.SSTORE
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0x4912bc7b66a3bf27adfa54ab049e90e8c9c4dc63]
        + Op.PUSH8[0x7ffffffffffffff] + Op.STATICCALL + Op.PUSH1[0xc] + Op.SSTORE
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0x4912bc7b66a3bf27adfa54ab049e90e8c9c4dc63]
        + Op.PUSH8[0x7ffffffffffffff] + Op.STATICCALL + Op.PUSH1[0xd] + Op.SSTORE
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0x4912bc7b66a3bf27adfa54ab049e90e8c9c4dc63]
        + Op.PUSH8[0x7ffffffffffffff] + Op.STATICCALL + Op.PUSH1[0xe] + Op.SSTORE
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0x4912bc7b66a3bf27adfa54ab049e90e8c9c4dc63]
        + Op.PUSH8[0x7ffffffffffffff] + Op.STATICCALL + Op.PUSH1[0xf] + Op.SSTORE
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0x4912bc7b66a3bf27adfa54ab049e90e8c9c4dc63]
        + Op.PUSH8[0x7ffffffffffffff] + Op.STATICCALL + Op.PUSH1[0x10] + Op.SSTORE
        + Op.STOP
    ),
    )
    pre[callee_14] = Account(
        balance=0,
        nonce=0,
        code=Op.PUSH14[0xfffffffffffffffffffffffffff] + Op.PUSH1[0x0] + Op.RETURN + Op.STOP,
    )
    pre[callee_15] = Account(
        balance=0,
        nonce=0,
        code=Op.PUSH1[0x0] + Op.PUSH4[0xffffffff] + Op.RETURN + Op.STOP,
    )

    tx = Transaction(
        secret_key=Hash(
            "0x50eadfb1030587ab3a993a6ecc073041fc3b45e119daa31a13d78c7e209631a5"
        ),
        to=contract,
        data=b"",
        gas_limit=15000000,
        gas_price=10,
        nonce=0,
        value=1,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
