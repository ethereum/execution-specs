"""
call(oog during init) ->  code 

Ported from:
tests/static/state_tests/stCallCodes/call_OOG_additionalGasCosts1Filler.json

callee code:
    push1 0x00

contract code:
    push1 0x40
    push1 0x00
    push1 0x40
    push1 0x00
    push1 0x00
    push20 0xd0735f094c16e509e8d76999d9ee2e4fd5166c2e
    push2 0x1770
    call
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
    ["tests/static/state_tests/stCallCodes/call_OOG_additionalGasCosts1Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_call_oog_additional_gas_costs1(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """call(oog during init) ->  code ."""
    coinbase = Address("0xeb201d2887816e041f6e807e804f64f3a7a226fe")
    sender = Address("0xebaf50debf10e08302fe4280c32df010463ca297")
    contract = Address("0xef8dd89dea93dc2bff0ce3a1196188496e6c28dc")
    callee = Address("0xd0735f094c16e509e8d76999d9ee2e4fd5166c2e")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=3000000000,
    )

    pre[callee] = Account(balance=0xde0b6b3a7640000, nonce=0, code=Op.PUSH1[0x0])
    pre[coinbase] = Account(balance=0, nonce=1)
    pre[sender] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[contract] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0x40] + Op.PUSH1[0x0] + Op.PUSH1[0x40] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH20[0xd0735f094c16e509e8d76999d9ee2e4fd5166c2e]
        + Op.PUSH2[0x1770] + Op.CALL + Op.STOP
    ),
    )

    tx = Transaction(
        secret_key=Hash(
            "0xe04d1ac7ddda0c98397d56a0b501e960d4cd325a39286919ac23c1a07009a869"
        ),
        to=contract,
        data=b"",
        gas_limit=30000,
        gas_price=10,
        nonce=0,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
