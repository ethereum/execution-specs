"""
Legacy Test from Christoph. J

Ported from:
tests/static/state_tests/stCallCreateCallCodeTest/createNameRegistratorendowmentTooHighFiller.json

contract code:
    push29 0x601080600c6000396000f3006000355415600957005b60203560003555
    push1 0x00
    mstore
    push1 0x1d
    push1 0x03
    push8 0x0de0b6b3a7640001
    create
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
    ["tests/static/state_tests/stCallCreateCallCodeTest/createNameRegistratorendowmentTooHighFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_create_name_registratorendowment_too_high(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Legacy Test from Christoph. J."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xebaf50debf10e08302fe4280c32df010463ca297")
    contract = Address("0x84d56fc4fefc05a5bce6c569883a47ee499ee0da")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000,
    )

    pre[contract] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH29[0x601080600c6000396000f3006000355415600957005b60203560003555]
        + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x1d] + Op.PUSH1[0x3]
        + Op.PUSH8[0xde0b6b3a7640001] + Op.CREATE + Op.PUSH1[0x0] + Op.SSTORE
        + Op.STOP
    ),
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0xe04d1ac7ddda0c98397d56a0b501e960d4cd325a39286919ac23c1a07009a869"
        ),
        to=contract,
        data=b"",
        gas_limit=300000,
        gas_price=10,
        nonce=0,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
