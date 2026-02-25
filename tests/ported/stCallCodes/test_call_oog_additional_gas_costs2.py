"""
call(oog during init) ->  code 

Ported from:
tests/static/state_tests/stCallCodes/call_OOG_additionalGasCosts2Filler.json

callee code:
    push1 0x00

contract code:
    push1 0x40
    push1 0x00
    push1 0x40
    push1 0x00
    push1 0x01
    push20 0x89cd1cb7ad11c6949bec0c8c7533dc073960c54f
    push2 0x1770
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
    ["tests/static/state_tests/stCallCodes/call_OOG_additionalGasCosts2Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_call_oog_additional_gas_costs2(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """call(oog during init) ->  code ."""
    coinbase = Address("0xeb201d2887816e041f6e807e804f64f3a7a226fe")
    sender = Address("0xebaf50debf10e08302fe4280c32df010463ca297")
    contract = Address("0xc1f36f15e971b13f8178b8c0c5c4f5e6b1b2b2c3")
    callee = Address("0x89cd1cb7ad11c6949bec0c8c7533dc073960c54f")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=3000000000,
    )

    pre[callee] = Account(balance=0, nonce=0, code=Op.PUSH1[0x0])
    pre[contract] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0x40] + Op.PUSH1[0x0] + Op.PUSH1[0x40] + Op.PUSH1[0x0]
        + Op.PUSH1[0x1] + Op.PUSH20[0x89cd1cb7ad11c6949bec0c8c7533dc073960c54f]
        + Op.PUSH2[0x1770] + Op.CALL + Op.PUSH1[0x0] + Op.SSTORE + Op.STOP
    ),
        storage={0x0: 0x2},
    )
    pre[coinbase] = Account(balance=0, nonce=1)
    pre[sender] = Account(balance=0xde0b6b3a7640000, nonce=0)

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
