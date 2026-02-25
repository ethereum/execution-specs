"""
Ported from:
tests/static/state_tests/stMemExpandingEIP150Calls/NewGasPriceForCodesWithMemExpandingCallsFiller.json

contract code:
    push20 0x6b6af3c6e1714081c8c3085acbac8c2b21fadf0b
    extcodesize
    push1 0x01
    sstore
    push1 0x14
    push1 0x00
    push1 0x00
    push20 0x6b6af3c6e1714081c8c3085acbac8c2b21fadf0b
    extcodecopy
    push1 0x00
    mload
    push1 0x02
    sstore
    push1 0x00
    sload
    push1 0x04
    sstore
    push1 0xff
    push1 0xff
    push1 0xff
    ... (43 more instructions)

callee_1 code:
    push1 0x11
    push1 0x64
    sstore
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
    ["tests/static/state_tests/stMemExpandingEIP150Calls/NewGasPriceForCodesWithMemExpandingCallsFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_new_gas_price_for_codes_with_mem_expanding_calls(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xf1100237a29f570cbf8b107ba3cb5bf2db42bd3f")
    contract = Address("0x23a2ec54f5f8589778da7c2199caf3b179a24cb9")
    callee = Address("0x6b6af3c6e1714081c8c3085acbac8c2b21fadf0b")
    callee_1 = Address("0x7b8c83e74cc8dfadb03138c2743c70588ace4222")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    pre[contract] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH20[0x6b6af3c6e1714081c8c3085acbac8c2b21fadf0b] + Op.EXTCODESIZE
        + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x14] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0x6b6af3c6e1714081c8c3085acbac8c2b21fadf0b] + Op.EXTCODECOPY
        + Op.PUSH1[0x0] + Op.MLOAD + Op.PUSH1[0x2] + Op.SSTORE + Op.PUSH1[0x0]
        + Op.SLOAD + Op.PUSH1[0x4] + Op.SSTORE + Op.PUSH1[0xff] + Op.PUSH1[0xff]
        + Op.PUSH1[0xff] + Op.PUSH1[0xff] + Op.PUSH1[0x1]
        + Op.PUSH20[0x7b8c83e74cc8dfadb03138c2743c70588ace4222] + Op.PUSH2[0x7530]
        + Op.CALL + Op.PUSH1[0x5] + Op.SSTORE + Op.PUSH1[0xff] + Op.PUSH1[0xff]
        + Op.PUSH1[0xff] + Op.PUSH1[0xff] + Op.PUSH1[0x1]
        + Op.PUSH20[0x7b8c83e74cc8dfadb03138c2743c70588ace4222] + Op.PUSH2[0x7530]
        + Op.CALLCODE + Op.PUSH1[0x6] + Op.SSTORE + Op.PUSH1[0xff] + Op.PUSH1[0xff]
        + Op.PUSH1[0xff] + Op.PUSH1[0xff]
        + Op.PUSH20[0x7b8c83e74cc8dfadb03138c2743c70588ace4222] + Op.PUSH2[0x7530]
        + Op.DELEGATECALL + Op.PUSH1[0x7] + Op.SSTORE + Op.PUSH1[0xff]
        + Op.PUSH1[0xff] + Op.PUSH1[0xff] + Op.PUSH1[0xff] + Op.PUSH1[0x0]
        + Op.PUSH20[0x1000000000000000000000000000000000000013] + Op.PUSH2[0x7530]
        + Op.CALL + Op.PUSH1[0x8] + Op.SSTORE
        + Op.PUSH20[0xf1100237a29f570cbf8b107ba3cb5bf2db42bd3f] + Op.BALANCE
        + Op.PUSH1[0x3] + Op.SSTORE + Op.GAS + Op.PUSH1[0xa] + Op.SSTORE
    ),
        storage={0x0: 0x12},
    )
    pre[callee] = Account(
        balance=111,
        nonce=0,
        code=bytes.fromhex("1122334455667788991011121314151617181920212223242526272829303132"),
    )
    pre[callee_1] = Account(balance=0, nonce=0, code=Op.PUSH1[0x11] + Op.PUSH1[0x64] + Op.SSTORE)
    pre[sender] = Account(balance=0xe8d4a5100000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x03956fc06bd55836acdb92da0e38a15f2e568c088022cf2278180477f3f7702a"
        ),
        to=contract,
        data=b"",
        gas_limit=600000,
        gas_price=10,
        nonce=0,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
