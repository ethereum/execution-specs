"""
Ported from:
tests/static/state_tests/stEIP150Specific/CallAskMoreGasOnDepth2ThenTransactionHasFiller.json

callee code:
    gas
    push1 0x08
    sstore
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0xf39d40eacb6d2c685ac10664e759d1cf8f775dff
    push3 0x0927c0
    call
    push1 0x09
    sstore
    stop

contract code:
    gas
    push1 0x08
    sstore
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0x25c370b55ec8467127bc4e13404915901d689098
    push3 0x030d40
    call
    push1 0x09
    sstore
    stop

callee_1 code:
    gas
    push1 0x08
    sstore
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
    ["tests/static/state_tests/stEIP150Specific/CallAskMoreGasOnDepth2ThenTransactionHasFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_call_ask_more_gas_on_depth2_then_transaction_has(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xfaa10b404ab607779993c016cd5da73ae1f29d7e")
    contract = Address("0x8553d06001d46f3b0b18a938acf8c552d87c5837")
    callee = Address("0x25c370b55ec8467127bc4e13404915901d689098")
    callee_1 = Address("0xf39d40eacb6d2c685ac10664e759d1cf8f775dff")

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
        code=(
        Op.GAS + Op.PUSH1[0x8] + Op.SSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0xf39d40eacb6d2c685ac10664e759d1cf8f775dff] + Op.PUSH3[0x927c0]
        + Op.CALL + Op.PUSH1[0x9] + Op.SSTORE + Op.STOP
    ),
    )
    pre[contract] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.GAS + Op.PUSH1[0x8] + Op.SSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0x25c370b55ec8467127bc4e13404915901d689098] + Op.PUSH3[0x30d40]
        + Op.CALL + Op.PUSH1[0x9] + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee_1] = Account(balance=0, nonce=0, code=Op.GAS + Op.PUSH1[0x8] + Op.SSTORE + Op.STOP)
    pre[sender] = Account(balance=0xe8d4a51000, nonce=0)

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
