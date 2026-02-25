"""
Ported from:
tests/static/state_tests/stMemoryStressTest/static_CALL_Bounds3Filler.json

contract code:
    push8 0xffffffffffffffff
    push1 0x00
    push8 0xffffffffffffffff
    push1 0x00
    push20 0xcc704d60c46b9c08aab4d15281184441ac7ed35c
    push8 0x07ffffffffffffff
    staticcall
    pop
    push16 0xffffffffffffffffffffffffffffffff
    push1 0x00
    push16 0xffffffffffffffffffffffffffffffff
    push1 0x00
    push20 0xcc704d60c46b9c08aab4d15281184441ac7ed35c
    push8 0x07ffffffffffffff
    staticcall
    pop
    push32 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff
    push1 0x00
    push32 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff
    push1 0x00
    ... (36 more instructions)

callee code:
    push1 0x00
    sload
    push1 0x01
    add
    push1 0x00
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
    ["tests/static/state_tests/stMemoryStressTest/static_CALL_Bounds3Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        150000,
        16777216,
    ],
    ids=['case0', 'case1'],
)
@pytest.mark.pre_alloc_mutable
def test_static_call_bounds3(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0x4d2e21bbf9a40a8303787a066285648f8013129a")
    contract = Address("0x83143406093d1f3560dd269416596d3406f1c991")
    callee = Address("0xcc704d60c46b9c08aab4d15281184441ac7ed35c")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=9223372036854775807,
    )

    pre[sender] = Account(balance=0xffffffffffffffffffffffffffffffffffffffffffffffffffffff, nonce=0)
    pre[contract] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH8[0xffffffffffffffff] + Op.PUSH1[0x0] + Op.PUSH8[0xffffffffffffffff]
        + Op.PUSH1[0x0] + Op.PUSH20[0xcc704d60c46b9c08aab4d15281184441ac7ed35c]
        + Op.PUSH8[0x7ffffffffffffff] + Op.STATICCALL + Op.POP
        + Op.PUSH16[0xffffffffffffffffffffffffffffffff] + Op.PUSH1[0x0]
        + Op.PUSH16[0xffffffffffffffffffffffffffffffff] + Op.PUSH1[0x0]
        + Op.PUSH20[0xcc704d60c46b9c08aab4d15281184441ac7ed35c]
        + Op.PUSH8[0x7ffffffffffffff] + Op.STATICCALL + Op.POP
        + Op.PUSH32[0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff]
        + Op.PUSH1[0x0]
        + Op.PUSH32[0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff]
        + Op.PUSH1[0x0] + Op.PUSH20[0xcc704d60c46b9c08aab4d15281184441ac7ed35c]
        + Op.PUSH8[0x7ffffffffffffff] + Op.STATICCALL + Op.POP + Op.PUSH4[0xffffffff]
        + Op.PUSH4[0xffffffff] + Op.PUSH4[0xffffffff] + Op.PUSH4[0xffffffff]
        + Op.PUSH20[0xcc704d60c46b9c08aab4d15281184441ac7ed35c]
        + Op.PUSH8[0x7ffffffffffffff] + Op.STATICCALL + Op.POP
        + Op.PUSH8[0xffffffffffffffff] + Op.PUSH8[0xffffffffffffffff]
        + Op.PUSH8[0xffffffffffffffff] + Op.PUSH8[0xffffffffffffffff]
        + Op.PUSH20[0xcc704d60c46b9c08aab4d15281184441ac7ed35c]
        + Op.PUSH8[0x7ffffffffffffff] + Op.STATICCALL + Op.POP
        + Op.PUSH16[0xffffffffffffffffffffffffffffffff]
        + Op.PUSH16[0xffffffffffffffffffffffffffffffff]
        + Op.PUSH16[0xffffffffffffffffffffffffffffffff]
        + Op.PUSH16[0xffffffffffffffffffffffffffffffff]
        + Op.PUSH20[0xcc704d60c46b9c08aab4d15281184441ac7ed35c]
        + Op.PUSH8[0x7ffffffffffffff] + Op.STATICCALL + Op.POP
        + Op.PUSH32[0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff]
        + Op.PUSH32[0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff]
        + Op.PUSH32[0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff]
        + Op.PUSH32[0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff]
        + Op.PUSH20[0xcc704d60c46b9c08aab4d15281184441ac7ed35c]
        + Op.PUSH8[0x7ffffffffffffff] + Op.STATICCALL + Op.STOP
    ),
    )
    pre[callee] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.SLOAD + Op.PUSH1[0x1] + Op.ADD + Op.PUSH1[0x0]
        + Op.MSTORE + Op.STOP
    ),
    )

    tx = Transaction(
        secret_key=Hash(
            "0xef111bbdab3a1622936afdfc9bbec4b5bc05b4fa4b1ef0ce2a55cef552f7650e"
        ),
        to=contract,
        data=b"",
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=0,
        value=1,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
