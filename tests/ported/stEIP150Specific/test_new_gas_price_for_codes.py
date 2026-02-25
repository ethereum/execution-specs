"""
Ported from:
tests/static/state_tests/stEIP150Specific/NewGasPriceForCodesFiller.json

callee code:
    push1 0x11
    push1 0x64
    sstore
    stop

contract code:
    gas
    push2 0x03e7
    mstore
    push20 0xc572a70afaab9d01d0a2afb855bfbafb47c8211b
    extcodesize
    push1 0x01
    sstore
    push1 0x14
    push1 0x00
    push1 0x00
    push20 0xc572a70afaab9d01d0a2afb855bfbafb47c8211b
    extcodecopy
    push1 0x00
    mload
    push1 0x02
    sstore
    push1 0x00
    sload
    push1 0x04
    sstore
    ... (50 more instructions)
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
    ["tests/static/state_tests/stEIP150Specific/NewGasPriceForCodesFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_new_gas_price_for_codes(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xfaa10b404ab607779993c016cd5da73ae1f29d7e")
    contract = Address("0xfd9afc8315a88141164e2a753157ea3e0f72c707")
    callee = Address("0xad9d325b811cb0701839c07c6f139f3799476798")
    callee_1 = Address("0xc572a70afaab9d01d0a2afb855bfbafb47c8211b")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    pre[callee] = Account(
        balance=0,
        nonce=0,
        code=Op.PUSH1[0x11] + Op.PUSH1[0x64] + Op.SSTORE + Op.STOP,
    )
    pre[callee_1] = Account(
        balance=111,
        nonce=0,
        code=bytes.fromhex("1122334455667788991011121314151617181920212223242526272829303132"),
    )
    pre[sender] = Account(balance=0xe8d4a51000, nonce=0)
    pre[contract] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.GAS + Op.PUSH2[0x3e7] + Op.MSTORE
        + Op.PUSH20[0xc572a70afaab9d01d0a2afb855bfbafb47c8211b] + Op.EXTCODESIZE
        + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x14] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0xc572a70afaab9d01d0a2afb855bfbafb47c8211b] + Op.EXTCODECOPY
        + Op.PUSH1[0x0] + Op.MLOAD + Op.PUSH1[0x2] + Op.SSTORE + Op.PUSH1[0x0]
        + Op.SLOAD + Op.PUSH1[0x4] + Op.SSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x1]
        + Op.PUSH20[0xad9d325b811cb0701839c07c6f139f3799476798] + Op.PUSH2[0x7530]
        + Op.CALL + Op.PUSH1[0x5] + Op.SSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x1]
        + Op.PUSH20[0xad9d325b811cb0701839c07c6f139f3799476798] + Op.PUSH2[0x7530]
        + Op.CALLCODE + Op.PUSH1[0x6] + Op.SSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0xad9d325b811cb0701839c07c6f139f3799476798] + Op.PUSH2[0x7530]
        + Op.DELEGATECALL + Op.PUSH1[0x7] + Op.SSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0x1000000000000000000000000000000000000013] + Op.PUSH2[0x7530]
        + Op.CALL + Op.PUSH1[0x8] + Op.SSTORE
        + Op.PUSH20[0xfaa10b404ab607779993c016cd5da73ae1f29d7e] + Op.BALANCE
        + Op.PUSH1[0x3] + Op.SSTORE + Op.GAS + Op.PUSH2[0x3e7] + Op.MLOAD + Op.SUB
        + Op.PUSH1[0xa] + Op.SSTORE + Op.STOP
    ),
        storage={0x0: 0x12},
    )

    tx = Transaction(
        secret_key=Hash(
            "0x4f31b3206fbf0e0e598b9b1a7d8ac86302a0ff1d8930738f1bebae9b67173e52"
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
