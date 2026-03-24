"""
create2 fails with not enough cash (endowment of a new account) + inside...

Ported from:
tests/static/state_tests/stCreate2/create2noCashFiller.json
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
    ["tests/static/state_tests/stCreate2/create2noCashFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex, expected_post",
    [
        (
            "6000600060006000600073e2b35478fdd26477cc576dd906e6277761246a3c620249f0f100",  # noqa: E501
            {},
        ),
        (
            "6000600060006000600173e2b35478fdd26477cc576dd906e6277761246a3c620249f0f100",  # noqa: E501
            {},
        ),
        (
            "600060006000600073e2b35478fdd26477cc576dd906e6277761246a3c620249f0fa00",  # noqa: E501
            {},
        ),
    ],
    ids=["case0", "case1", "case2"],
)
@pytest.mark.pre_alloc_mutable
def test_create2no_cash(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
    expected_post: dict,
) -> None:
    """Create2 fails with not enough cash (endowment of a new account) +..."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000,
    )

    pre[sender] = Account(balance=0xDE0B6B3A7640000)
    # Source: LLL
    # { (CREATE2 101 0 0 0) }
    pre.deploy_contract(
        code=Op.CREATE2(value=0x65, offset=0x0, size=0x0, salt=0x0) + Op.STOP,
        balance=100,
        nonce=0,
        address=Address("0xe2b35478fdd26477cc576dd906e6277761246a3c"),  # noqa: E501
    )

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        sender=sender,
        to=None,
        data=tx_data,
        gas_limit=400000,
        value=1,
    )

    post = expected_post

    state_test(env=env, pre=pre, post=post, tx=tx)
