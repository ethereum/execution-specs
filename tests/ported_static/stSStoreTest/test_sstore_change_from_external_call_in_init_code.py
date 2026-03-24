"""
account already has storage X. create -> in init code change that account's...

Ported from:
tests/static/state_tests/stSStoreTest
sstore_changeFromExternalCallInInitCodeFiller.json
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
        "tests/static/state_tests/stSStoreTest/sstore_changeFromExternalCallInInitCodeFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex, expected_post",
    [
        (
            "6000600060006000600073bea0000000000000000000000000000000000000620186a0f100",  # noqa: E501
            {
                Address("0xbea0000000000000000000000000000000000000"): Account(
                    storage={0: 1, 1: 1}
                )
            },
        ),
        (
            "6000602380601860003960006000f55060006000fd0000fe600060006000600073bea0000000000000000000000000000000000000620186a0f400",  # noqa: E501
            {
                Address("0xbea0000000000000000000000000000000000000"): Account(
                    storage={1: 1}
                )
            },
        ),
        (
            "6000602380603860003960006000f5506000600060006000600073dea000000000000000000000000000000000000062030d40f1500000fe600060006000600073bea0000000000000000000000000000000000000620186a0f400",  # noqa: E501
            {
                Address("0xbea0000000000000000000000000000000000000"): Account(
                    storage={1: 1}
                ),
                Address("0xc07f1349a887643be65b34e234e1b3161f62dc30"): Account(
                    storage={0: 1, 1: 1}
                ),
            },
        ),
        (
            "600060006000600073bea0000000000000000000000000000000000000620186a0fa00",  # noqa: E501
            {
                Address("0xbea0000000000000000000000000000000000000"): Account(
                    storage={1: 1}
                )
            },
        ),
        (
            "6000602380601360003960006000f5500000fe600060006000600073bea0000000000000000000000000000000000000620186a0fa00",  # noqa: E501
            {
                Address("0xbea0000000000000000000000000000000000000"): Account(
                    storage={1: 1}
                )
            },
        ),
        (
            "6000602380601860003960006000f55060006000fd0000fe600060006000600073bea0000000000000000000000000000000000000620186a0fa00",  # noqa: E501
            {
                Address("0xbea0000000000000000000000000000000000000"): Account(
                    storage={1: 1}
                )
            },
        ),
        (
            "6000602380603860003960006000f5506000600060006000600073dea000000000000000000000000000000000000062030d40f1500000fe600060006000600073bea0000000000000000000000000000000000000620186a0fa00",  # noqa: E501
            {
                Address("0xbea0000000000000000000000000000000000000"): Account(
                    storage={1: 1}
                )
            },
        ),
        (
            "6000602580601360003960006000f5500000fe6000600060006000600073bea0000000000000000000000000000000000000620186a0f100",  # noqa: E501
            {
                Address("0xbea0000000000000000000000000000000000000"): Account(
                    storage={0: 1, 1: 1}
                )
            },
        ),
        (
            "6000602580601860003960006000f55060006000fd0000fe6000600060006000600073bea0000000000000000000000000000000000000620186a0f100",  # noqa: E501
            {
                Address("0xbea0000000000000000000000000000000000000"): Account(
                    storage={1: 1}
                )
            },
        ),
        (
            "6000602580603860003960006000f5506000600060006000600073dea000000000000000000000000000000000000062030d40f1500000fe6000600060006000600073bea0000000000000000000000000000000000000620186a0f100",  # noqa: E501
            {
                Address("0xbea0000000000000000000000000000000000000"): Account(
                    storage={0: 1, 1: 1}
                )
            },
        ),
        (
            "6000600060006000600073bea0000000000000000000000000000000000000620186a0f200",  # noqa: E501
            {
                Address("0x6295ee1b4f6dd65047762f924ecd367c17eabf8f"): Account(
                    storage={0: 1, 1: 1}
                ),
                Address("0xbea0000000000000000000000000000000000000"): Account(
                    storage={1: 1}
                ),
            },
        ),
        (
            "6000602580601360003960006000f5500000fe6000600060006000600073bea0000000000000000000000000000000000000620186a0f200",  # noqa: E501
            {
                Address("0x0f446e1bd7a5da68b5e3a305c7030e3aa8efc293"): Account(
                    storage={0: 1, 1: 1}
                ),
                Address("0xbea0000000000000000000000000000000000000"): Account(
                    storage={1: 1}
                ),
            },
        ),
        (
            "6000602580601860003960006000f55060006000fd0000fe6000600060006000600073bea0000000000000000000000000000000000000620186a0f200",  # noqa: E501
            {
                Address("0xbea0000000000000000000000000000000000000"): Account(
                    storage={1: 1}
                )
            },
        ),
        (
            "6000602580603860003960006000f5506000600060006000600073dea000000000000000000000000000000000000062030d40f1500000fe6000600060006000600073bea0000000000000000000000000000000000000620186a0f200",  # noqa: E501
            {
                Address("0x0f446e1bd7a5da68b5e3a305c7030e3aa8efc293"): Account(
                    storage={0: 1, 1: 1}
                ),
                Address("0xbea0000000000000000000000000000000000000"): Account(
                    storage={1: 1}
                ),
            },
        ),
        (
            "600060006000600073bea0000000000000000000000000000000000000620186a0f400",  # noqa: E501
            {
                Address("0x6295ee1b4f6dd65047762f924ecd367c17eabf8f"): Account(
                    storage={0: 1, 1: 1}
                ),
                Address("0xbea0000000000000000000000000000000000000"): Account(
                    storage={1: 1}
                ),
            },
        ),
        (
            "6000602380601360003960006000f5500000fe600060006000600073bea0000000000000000000000000000000000000620186a0f400",  # noqa: E501
            {
                Address("0xbea0000000000000000000000000000000000000"): Account(
                    storage={1: 1}
                ),
                Address("0xc07f1349a887643be65b34e234e1b3161f62dc30"): Account(
                    storage={0: 1, 1: 1}
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
        "case9",
        "case10",
        "case11",
        "case12",
        "case13",
        "case14",
        "case15",
    ],
)
@pytest.mark.pre_alloc_mutable
def test_sstore_change_from_external_call_in_init_code(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
    expected_post: dict,
) -> None:
    """Account already has storage X. create -> in init code change that..."""
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
    # Source: LLL
    # { (SSTORE 1 0) (SSTORE 1 1) (SSTORE 0 1) }
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x1, value=0x0)
            + Op.SSTORE(key=0x1, value=0x1)
            + Op.SSTORE(key=0x0, value=0x1)
            + Op.STOP
        ),
        storage={0x1: 0x1},
        nonce=0,
        address=Address("0xbea0000000000000000000000000000000000000"),  # noqa: E501
    )
    # Source: LLL
    # { [[1]] 1 [[1]] 0 [[2]] 1 [[2]] 0 [[3]] 1 [[3]] 0 [[4]] 1 [[4]] 0 [[5]] 1 [[5]] 0 [[6]] 1 [[6]] 0 [[7]] 1 [[7]] 0 [[8]] 1 [[8]] 0 [[9]] 1 [[9]] 0 [[10]] 1 [[10]] 0 [[11]] 1 [[11]] 0 [[12]] 1 [[12]] 0 [[13]] 1 [[13]] 0 [[14]] 1 [[14]] 0 [[15]] 1 [[15]] 0 [[16]] 1 [[16]] 0  [[1]] 1 }  # noqa: E501
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x1, value=0x1)
            + Op.SSTORE(key=0x1, value=0x0)
            + Op.SSTORE(key=0x2, value=0x1)
            + Op.SSTORE(key=0x2, value=0x0)
            + Op.SSTORE(key=0x3, value=0x1)
            + Op.SSTORE(key=0x3, value=0x0)
            + Op.SSTORE(key=0x4, value=0x1)
            + Op.SSTORE(key=0x4, value=0x0)
            + Op.SSTORE(key=0x5, value=0x1)
            + Op.SSTORE(key=0x5, value=0x0)
            + Op.SSTORE(key=0x6, value=0x1)
            + Op.SSTORE(key=0x6, value=0x0)
            + Op.SSTORE(key=0x7, value=0x1)
            + Op.SSTORE(key=0x7, value=0x0)
            + Op.SSTORE(key=0x8, value=0x1)
            + Op.SSTORE(key=0x8, value=0x0)
            + Op.SSTORE(key=0x9, value=0x1)
            + Op.SSTORE(key=0x9, value=0x0)
            + Op.SSTORE(key=0xA, value=0x1)
            + Op.SSTORE(key=0xA, value=0x0)
            + Op.SSTORE(key=0xB, value=0x1)
            + Op.SSTORE(key=0xB, value=0x0)
            + Op.SSTORE(key=0xC, value=0x1)
            + Op.SSTORE(key=0xC, value=0x0)
            + Op.SSTORE(key=0xD, value=0x1)
            + Op.SSTORE(key=0xD, value=0x0)
            + Op.SSTORE(key=0xE, value=0x1)
            + Op.SSTORE(key=0xE, value=0x0)
            + Op.SSTORE(key=0xF, value=0x1)
            + Op.SSTORE(key=0xF, value=0x0)
            + Op.SSTORE(key=0x10, value=0x1)
            + Op.SSTORE(key=0x10, value=0x0)
            + Op.SSTORE(key=0x1, value=0x1)
            + Op.STOP
        ),
        nonce=0,
        address=Address("0xdea0000000000000000000000000000000000000"),  # noqa: E501
    )

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        sender=sender,
        to=None,
        data=tx_data,
        gas_limit=200000,
    )

    post = expected_post

    state_test(env=env, pre=pre, post=post, tx=tx)
