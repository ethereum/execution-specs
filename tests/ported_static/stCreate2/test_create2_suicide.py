"""
CREATE2 suicide with/without value, CREATE2 suicide to itself   +  this...

Ported from:
tests/static/state_tests/stCreate2/CREATE2_SuicideFiller.json
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

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["tests/static/state_tests/stCreate2/CREATE2_SuicideFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex, expected_post",
    [
        ("626001ff60005260006003601d6000f500", {}),
        (
            "6a6130ff6000526002601ef36000526000600b60156000f5506000600060006000736cd0e5133771823da00d4cb545ec8cdab0e38203620249f0fa00",  # noqa: E501
            {},
        ),
        (
            "6a6130ff6000526002601ef36000526000600b60156001f5506000600060006000736cd0e5133771823da00d4cb545ec8cdab0e38203620249f0fa00",  # noqa: E501
            {},
        ),
        (
            "6b626001ff6000526003601df36000526000600c60146000f55060006000600060006000735649527a8464a86cae579719d347065f6eb27279620249f0f100",  # noqa: E501
            {},
        ),
        ("626001ff60005260006003601d6001f500", {}),
        (
            "6b626001ff6000526003601df36000526000600c60146001f55060006000600060006000735649527a8464a86cae579719d347065f6eb27279620249f0f100",  # noqa: E501
            {},
        ),
        ("6130ff60005260006002601e6000f500", {}),
        (
            "6a6130ff6000526002601ef36000526000600b60156000f55060006000600060006000736cd0e5133771823da00d4cb545ec8cdab0e38203620249f0f100",  # noqa: E501
            {},
        ),
        ("6130ff60005260006002601e6001f500", {}),
        (
            "6a6130ff6000526002601ef36000526000600b60156001f55060006000600060006000736cd0e5133771823da00d4cb545ec8cdab0e38203620249f0f100",  # noqa: E501
            {},
        ),
        (
            "6b626001ff6000526003601df36000526000600c60146000f5506000600060006000735649527a8464a86cae579719d347065f6eb27279620249f0fa00",  # noqa: E501
            {},
        ),
        (
            "6b626001ff6000526003601df36000526000600c60146001f5506000600060006000735649527a8464a86cae579719d347065f6eb27279620249f0fa00",  # noqa: E501
            {},
        ),
    ],
    ids=[
        "case0",
        "case1",
        "case2",
        "case3",
        "case4",
        "case5",
        "case6",
        "case7",
        "case8",
        "case9",
        "case10",
        "case11",
    ],
)
@pytest.mark.pre_alloc_mutable
def test_create2_suicide(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
    expected_post: dict,
) -> None:
    """CREATE2 suicide with/without value, CREATE2 suicide to itself   +..."""
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
        gas_limit=10000000,
    )

    pre[sender] = Account(balance=0xE8D4A51000)

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        sender=sender,
        to=None,
        data=tx_data,
        gas_limit=600000,
        value=10,
    )

    post = expected_post

    state_test(env=env, pre=pre, post=post, tx=tx)
