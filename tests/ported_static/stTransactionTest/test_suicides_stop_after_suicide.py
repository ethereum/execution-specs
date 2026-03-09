"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stTransactionTest/SuicidesStopAfterSuicideFiller.json
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
        "tests/static/state_tests/stTransactionTest/SuicidesStopAfterSuicideFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_suicides_stop_after_suicide(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    sender = EOA(
        key=0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000,
    )

    # Source: LLL
    # {(SELFDESTRUCT 0x0000000000000000000000000000000000000001)}
    pre.deploy_contract(
        code=Op.SELFDESTRUCT(address=0x1) + Op.STOP,
        balance=1110,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000000000"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x7459280)
    # Source: LLL
    # {(SELFDESTRUCT 0) (CALL 30000 0x0000000000000000000000000000000000000000 0 0 0 0 0) }  # noqa: E501
    contract = pre.deploy_contract(
        code=(
            Op.SELFDESTRUCT(address=0x0)
            + Op.CALL(
                gas=0x7530,
                address=0x0,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
            + Op.STOP
        ),
        balance=0x2710,
        nonce=0,
        address=Address("0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b"),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=83700,
        value=10,
    )

    post: dict = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
