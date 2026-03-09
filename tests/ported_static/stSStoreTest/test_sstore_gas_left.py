"""
Checks EIP-1706/EIP-2200 out of gas requirement for non-mutating SSTOREs.

Ported from:
tests/static/state_tests/stSStoreTest/sstore_gasLeftFiller.json
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
    ["tests/static/state_tests/stSStoreTest/sstore_gasLeftFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex, expected_post",
    [
        (
            "6000600060006000600073b0409d84ab61455cb8bec14b94f635146ab55613610901f115604b5760006000600060006000734092b3905cfea2485ea53222f41eb26e67587802617530f1505b00",  # noqa: E501
            {
                Address("0xb0409d84ab61455cb8bec14b94f635146ab55613"): Account(
                    storage={1: 1}
                )
            },
        ),
        (
            "6000600060006000600073b0409d84ab61455cb8bec14b94f635146ab55613610902f115604b5760006000600060006000734092b3905cfea2485ea53222f41eb26e67587802617530f1505b00",  # noqa: E501
            {
                Address("0xb0409d84ab61455cb8bec14b94f635146ab55613"): Account(
                    storage={1: 1}
                )
            },
        ),
        (
            "6000600060006000600073b0409d84ab61455cb8bec14b94f635146ab55613610903f115604b5760006000600060006000734092b3905cfea2485ea53222f41eb26e67587802617530f1505b00",  # noqa: E501
            {
                Address("0x4092b3905cfea2485ea53222f41eb26e67587802"): Account(
                    storage={1: 1}
                ),
                Address("0xb0409d84ab61455cb8bec14b94f635146ab55613"): Account(
                    storage={1: 1}
                ),
            },
        ),
        (
            "60016001556000600060006000600073b0409d84ab61455cb8bec14b94f635146ab55613610901f21560505760006000600060006000734092b3905cfea2485ea53222f41eb26e67587802617530f1505b00",  # noqa: E501
            {
                Address("0x21b8a1d7e6f995ece38f302d2981ac0793c37fbd"): Account(
                    storage={1: 1}
                ),
                Address("0xb0409d84ab61455cb8bec14b94f635146ab55613"): Account(
                    storage={1: 1}
                ),
            },
        ),
        (
            "60016001556000600060006000600073b0409d84ab61455cb8bec14b94f635146ab55613610902f21560505760006000600060006000734092b3905cfea2485ea53222f41eb26e67587802617530f1505b00",  # noqa: E501
            {
                Address("0x21b8a1d7e6f995ece38f302d2981ac0793c37fbd"): Account(
                    storage={1: 1}
                ),
                Address("0xb0409d84ab61455cb8bec14b94f635146ab55613"): Account(
                    storage={1: 1}
                ),
            },
        ),
        (
            "60016001556000600060006000600073b0409d84ab61455cb8bec14b94f635146ab55613610903f21560505760006000600060006000734092b3905cfea2485ea53222f41eb26e67587802617530f1505b00",  # noqa: E501
            {
                Address("0x21b8a1d7e6f995ece38f302d2981ac0793c37fbd"): Account(
                    storage={1: 1}
                ),
                Address("0x4092b3905cfea2485ea53222f41eb26e67587802"): Account(
                    storage={1: 1}
                ),
                Address("0xb0409d84ab61455cb8bec14b94f635146ab55613"): Account(
                    storage={1: 1}
                ),
            },
        ),
        (
            "6001600155600060006000600073b0409d84ab61455cb8bec14b94f635146ab55613610901f415604e5760006000600060006000734092b3905cfea2485ea53222f41eb26e67587802617530f1505b00",  # noqa: E501
            {
                Address("0x21b8a1d7e6f995ece38f302d2981ac0793c37fbd"): Account(
                    storage={1: 1}
                ),
                Address("0xb0409d84ab61455cb8bec14b94f635146ab55613"): Account(
                    storage={1: 1}
                ),
            },
        ),
        (
            "6001600155600060006000600073b0409d84ab61455cb8bec14b94f635146ab55613610902f415604e5760006000600060006000734092b3905cfea2485ea53222f41eb26e67587802617530f1505b00",  # noqa: E501
            {
                Address("0x21b8a1d7e6f995ece38f302d2981ac0793c37fbd"): Account(
                    storage={1: 1}
                ),
                Address("0xb0409d84ab61455cb8bec14b94f635146ab55613"): Account(
                    storage={1: 1}
                ),
            },
        ),
        (
            "6001600155600060006000600073b0409d84ab61455cb8bec14b94f635146ab55613610903f415604e5760006000600060006000734092b3905cfea2485ea53222f41eb26e67587802617530f1505b00",  # noqa: E501
            {
                Address("0x21b8a1d7e6f995ece38f302d2981ac0793c37fbd"): Account(
                    storage={1: 1}
                ),
                Address("0x4092b3905cfea2485ea53222f41eb26e67587802"): Account(
                    storage={1: 1}
                ),
                Address("0xb0409d84ab61455cb8bec14b94f635146ab55613"): Account(
                    storage={1: 1}
                ),
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
    ],
)
@pytest.mark.pre_alloc_mutable
def test_sstore_gas_left(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
    expected_post: dict,
) -> None:
    """Checks EIP-1706/EIP-2200 out of gas requirement for non-mutating..."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x4F31B3206FBF0E0E598B9B1A7D8AC86302A0FF1D8930738F1BEBAE9B67173E52
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    pre.deploy_contract(
        code=Op.SSTORE(key=0x1, value=0x1) + Op.STOP,
        nonce=0,
        address=Address("0x4092b3905cfea2485ea53222f41eb26e67587802"),  # noqa: E501
    )
    pre.deploy_contract(
        code=Op.SSTORE(key=0x1, value=0x1) + Op.STOP,
        storage={0x1: 0x1},
        nonce=0,
        address=Address("0xb0409d84ab61455cb8bec14b94f635146ab55613"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xE8D4A51000)

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        sender=sender,
        to=None,
        data=tx_data,
        gas_limit=200000,
        value=1,
    )

    post = expected_post

    state_test(env=env, pre=pre, post=post, tx=tx)
