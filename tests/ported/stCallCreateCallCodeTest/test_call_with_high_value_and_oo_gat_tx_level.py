"""
call with value. call takes more gas then tx has, and more value than account has

Ported from:
tests/static/state_tests/stCallCreateCallCodeTest/callWithHighValueAndOOGatTxLevelFiller.json

callee code:
    push1 0x01
    push1 0x01
    sstore
    push1 0x37
    push1 0x00
    mstore8
    push1 0x02
    push1 0x00
    return

contract code:
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push3 0x0186a1
    push20 0x0896f13e800125c0ccec44f3c434335f0a97bc1b
    push3 0x2dc6c1
    call
    push1 0x00
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
    ["tests/static/state_tests/stCallCreateCallCodeTest/callWithHighValueAndOOGatTxLevelFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_value",
    [
        0,
        1,
    ],
    ids=['case0', 'case1'],
)
@pytest.mark.pre_alloc_mutable
def test_call_with_high_value_and_oo_gat_tx_level(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_value: int,
) -> None:
    """call with value. call takes more gas then tx has, and more value than account has."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xebaf50debf10e08302fe4280c32df010463ca297")
    contract = Address("0x9001fa64dbba07e3eb711a42cf25b34ccee2bd2b")
    callee = Address("0x0896f13e800125c0ccec44f3c434335f0a97bc1b")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=30000000,
    )

    pre[callee] = Account(
        balance=23,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x37] + Op.PUSH1[0x0]
        + Op.MSTORE8 + Op.PUSH1[0x2] + Op.PUSH1[0x0] + Op.RETURN
    ),
    )
    pre[contract] = Account(
        balance=0x186a0,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH3[0x186a1] + Op.PUSH20[0x896f13e800125c0ccec44f3c434335f0a97bc1b]
        + Op.PUSH3[0x2dc6c1] + Op.CALL + Op.PUSH1[0x0] + Op.SSTORE + Op.STOP
    ),
        storage={0x0: 0x5},
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0xe04d1ac7ddda0c98397d56a0b501e960d4cd325a39286919ac23c1a07009a869"
        ),
        to=contract,
        data=b"",
        gas_limit=3000000,
        gas_price=10,
        nonce=0,
        value=tx_value,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
