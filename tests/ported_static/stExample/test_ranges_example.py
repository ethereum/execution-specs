"""
An example how to use ranges in expect section.

Ported from:
tests/static/state_tests/stExample/rangesExampleFiller.yml
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
    ["tests/static/state_tests/stExample/rangesExampleFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex, tx_gas_limit, tx_value, expected_post",
    [
        (
            "01",
            400000,
            100000,
            {
                Address("0xa054bc58f204030cbc0ec558a5b88ac9bd5aded2"): Account(
                    storage={
                        0: 0x100000000000000000000000000000000000000000000000000000000000000  # noqa: E501
                    }
                )
            },
        ),
        (
            "01",
            400000,
            200000,
            {
                Address("0xa054bc58f204030cbc0ec558a5b88ac9bd5aded2"): Account(
                    storage={
                        0: 0x100000000000000000000000000000000000000000000000000000000000000  # noqa: E501
                    }
                )
            },
        ),
        (
            "01",
            1400000,
            100000,
            {
                Address("0xa054bc58f204030cbc0ec558a5b88ac9bd5aded2"): Account(
                    storage={
                        0: 0x100000000000000000000000000000000000000000000000000000000000000  # noqa: E501
                    }
                )
            },
        ),
        (
            "01",
            1400000,
            200000,
            {
                Address("0xa054bc58f204030cbc0ec558a5b88ac9bd5aded2"): Account(
                    storage={
                        0: 0x100000000000000000000000000000000000000000000000000000000000000  # noqa: E501
                    }
                )
            },
        ),
        (
            "01",
            2400000,
            100000,
            {
                Address("0xa054bc58f204030cbc0ec558a5b88ac9bd5aded2"): Account(
                    storage={
                        0: 0x100000000000000000000000000000000000000000000000000000000000000  # noqa: E501
                    }
                )
            },
        ),
        (
            "01",
            2400000,
            200000,
            {
                Address("0xa054bc58f204030cbc0ec558a5b88ac9bd5aded2"): Account(
                    storage={
                        0: 0x100000000000000000000000000000000000000000000000000000000000000  # noqa: E501
                    }
                )
            },
        ),
        (
            "01",
            400000,
            100000,
            {
                Address("0xa054bc58f204030cbc0ec558a5b88ac9bd5aded2"): Account(
                    storage={
                        0: 0x100000000000000000000000000000000000000000000000000000000000000  # noqa: E501
                    }
                )
            },
        ),
        (
            "01",
            400000,
            200000,
            {
                Address("0xa054bc58f204030cbc0ec558a5b88ac9bd5aded2"): Account(
                    storage={
                        0: 0x100000000000000000000000000000000000000000000000000000000000000  # noqa: E501
                    }
                )
            },
        ),
        (
            "01",
            1400000,
            100000,
            {
                Address("0xa054bc58f204030cbc0ec558a5b88ac9bd5aded2"): Account(
                    storage={
                        0: 0x100000000000000000000000000000000000000000000000000000000000000  # noqa: E501
                    }
                )
            },
        ),
        (
            "01",
            1400000,
            200000,
            {
                Address("0xa054bc58f204030cbc0ec558a5b88ac9bd5aded2"): Account(
                    storage={
                        0: 0x100000000000000000000000000000000000000000000000000000000000000  # noqa: E501
                    }
                )
            },
        ),
        (
            "01",
            2400000,
            100000,
            {
                Address("0xa054bc58f204030cbc0ec558a5b88ac9bd5aded2"): Account(
                    storage={
                        0: 0x100000000000000000000000000000000000000000000000000000000000000  # noqa: E501
                    }
                )
            },
        ),
        (
            "01",
            2400000,
            200000,
            {
                Address("0xa054bc58f204030cbc0ec558a5b88ac9bd5aded2"): Account(
                    storage={
                        0: 0x100000000000000000000000000000000000000000000000000000000000000  # noqa: E501
                    }
                )
            },
        ),
        (
            "04",
            400000,
            100000,
            {
                Address("0xa054bc58f204030cbc0ec558a5b88ac9bd5aded2"): Account(
                    storage={
                        0: 0x400000000000000000000000000000000000000000000000000000000000000  # noqa: E501
                    }
                )
            },
        ),
        (
            "04",
            400000,
            200000,
            {
                Address("0xa054bc58f204030cbc0ec558a5b88ac9bd5aded2"): Account(
                    storage={
                        0: 0x400000000000000000000000000000000000000000000000000000000000000  # noqa: E501
                    }
                )
            },
        ),
        (
            "04",
            1400000,
            100000,
            {
                Address("0xa054bc58f204030cbc0ec558a5b88ac9bd5aded2"): Account(
                    storage={
                        0: 0x400000000000000000000000000000000000000000000000000000000000000  # noqa: E501
                    }
                )
            },
        ),
        (
            "04",
            1400000,
            200000,
            {
                Address("0xa054bc58f204030cbc0ec558a5b88ac9bd5aded2"): Account(
                    storage={
                        0: 0x400000000000000000000000000000000000000000000000000000000000000  # noqa: E501
                    }
                )
            },
        ),
        (
            "04",
            2400000,
            100000,
            {
                Address("0xa054bc58f204030cbc0ec558a5b88ac9bd5aded2"): Account(
                    storage={
                        0: 0x400000000000000000000000000000000000000000000000000000000000000  # noqa: E501
                    }
                )
            },
        ),
        (
            "04",
            2400000,
            200000,
            {
                Address("0xa054bc58f204030cbc0ec558a5b88ac9bd5aded2"): Account(
                    storage={
                        0: 0x400000000000000000000000000000000000000000000000000000000000000  # noqa: E501
                    }
                )
            },
        ),
        (
            "01",
            400000,
            100000,
            {
                Address("0xa054bc58f204030cbc0ec558a5b88ac9bd5aded2"): Account(
                    storage={
                        0: 0x100000000000000000000000000000000000000000000000000000000000000  # noqa: E501
                    }
                )
            },
        ),
        (
            "01",
            400000,
            200000,
            {
                Address("0xa054bc58f204030cbc0ec558a5b88ac9bd5aded2"): Account(
                    storage={
                        0: 0x100000000000000000000000000000000000000000000000000000000000000  # noqa: E501
                    }
                )
            },
        ),
        (
            "01",
            1400000,
            100000,
            {
                Address("0xa054bc58f204030cbc0ec558a5b88ac9bd5aded2"): Account(
                    storage={
                        0: 0x100000000000000000000000000000000000000000000000000000000000000  # noqa: E501
                    }
                )
            },
        ),
        (
            "01",
            1400000,
            200000,
            {
                Address("0xa054bc58f204030cbc0ec558a5b88ac9bd5aded2"): Account(
                    storage={
                        0: 0x100000000000000000000000000000000000000000000000000000000000000  # noqa: E501
                    }
                )
            },
        ),
        (
            "01",
            2400000,
            100000,
            {
                Address("0xa054bc58f204030cbc0ec558a5b88ac9bd5aded2"): Account(
                    storage={
                        0: 0x100000000000000000000000000000000000000000000000000000000000000  # noqa: E501
                    }
                )
            },
        ),
        (
            "01",
            2400000,
            200000,
            {
                Address("0xa054bc58f204030cbc0ec558a5b88ac9bd5aded2"): Account(
                    storage={
                        0: 0x100000000000000000000000000000000000000000000000000000000000000  # noqa: E501
                    }
                )
            },
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
        "case12",
        "case13",
        "case14",
        "case15",
        "case16",
        "case17",
        "case18",
        "case19",
        "case20",
        "case21",
        "case22",
        "case23",
    ],
)
@pytest.mark.pre_alloc_mutable
def test_ranges_example(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
    tx_gas_limit: int,
    tx_value: int,
    expected_post: dict,
) -> None:
    """An example how to use ranges in expect section."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0xB1F4CBC3A50042184425A6F9E996D0910F7BA879457CE5DAC5C71E498AD3C005
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=71794957647893862,
    )

    pre[sender] = Account(balance=0xDE0B6B3A7640000)
    # Source: LLL
    # {
    #    [[0]] (CALLDATALOAD 0)
    # }
    contract = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.CALLDATALOAD(offset=0x0)) + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0xa054bc58f204030cbc0ec558a5b88ac9bd5aded2"),  # noqa: E501
    )

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        sender=sender,
        to=contract,
        data=tx_data,
        gas_limit=tx_gas_limit,
        value=tx_value,
    )

    post = expected_post

    state_test(env=env, pre=pre, post=post, tx=tx)
