"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stSystemOperationsTest/suicideOriginFiller.json
"""

import pytest
from execution_testing import (
    EOA,
    Account,
    Address,
    Alloc,
    Environment,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    [
        "tests/static/state_tests/stSystemOperationsTest/suicideOriginFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_suicide_origin(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0xE04D1AC7DDDA0C98397D56A0B501E960D4CD325A39286919AC23C1A07009A869
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    # Source: LLL
    # { [[0]] (ORIGIN) (SELFDESTRUCT (ORIGIN))}
    contract = pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=Op.ORIGIN)
            + Op.SELFDESTRUCT(address=Op.ORIGIN)
            + Op.STOP
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0x8a448e5835bbdd139b8a2053ee6fe895522048a1"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=1000000,
        value=100000,
    )

    post = {
        contract: Account(
            storage={0: 0xEBAF50DEBF10E08302FE4280C32DF010463CA297},
        ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
