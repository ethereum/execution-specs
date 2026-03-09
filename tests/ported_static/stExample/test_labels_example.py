"""
An example how to use labels in expect section.

Ported from:
tests/static/state_tests/stExample/labelsExampleFiller.yml
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
    ["tests/static/state_tests/stExample/labelsExampleFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex, expected_post",
    [
        (
            "01",
            {
                Address("0xa054bc58f204030cbc0ec558a5b88ac9bd5aded2"): Account(
                    storage={
                        0: 0x100000000000000000000000000000000000000000000000000000000000000  # noqa: E501
                    }
                )
            },
        ),
        (
            "02",
            {
                Address("0xa054bc58f204030cbc0ec558a5b88ac9bd5aded2"): Account(
                    storage={
                        0: 0x200000000000000000000000000000000000000000000000000000000000000  # noqa: E501
                    }
                )
            },
        ),
        (
            "03",
            {
                Address("0xa054bc58f204030cbc0ec558a5b88ac9bd5aded2"): Account(
                    storage={
                        0: 0x300000000000000000000000000000000000000000000000000000000000000  # noqa: E501
                    }
                )
            },
        ),
        (
            "03",
            {
                Address("0xa054bc58f204030cbc0ec558a5b88ac9bd5aded2"): Account(
                    storage={
                        0: 0x300000000000000000000000000000000000000000000000000000000000000  # noqa: E501
                    }
                )
            },
        ),
    ],
    ids=["case0", "case1", "case2", "case3"],
)
@pytest.mark.pre_alloc_mutable
def test_labels_example(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
    expected_post: dict,
) -> None:
    """An example how to use labels in expect section."""
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
        gas_limit=400000,
        value=100000,
    )

    post = expected_post

    state_test(env=env, pre=pre, post=post, tx=tx)
