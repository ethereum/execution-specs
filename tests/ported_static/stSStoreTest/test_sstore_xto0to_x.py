"""
change X -> 0 -> X.

Ported from:
tests/static/state_tests/stSStoreTest/sstore_Xto0toXFiller.json
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
    ["tests/static/state_tests/stSStoreTest/sstore_Xto0toXFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex, tx_gas_limit, expected_post",
    [
        (
            "6000600060006000600073b000000000000000000000000000000000000000620493e0f1506000600060006000600073dea0000000000000000000000000000000000000620927c0f100",  # noqa: E501
            1000000,
            {
                Address("0xb000000000000000000000000000000000000000"): Account(
                    storage={1: 1}
                ),
                Address("0xc000000000000000000000000000000000000000"): Account(
                    storage={1: 1}
                ),
                Address("0xdea0000000000000000000000000000000000000"): Account(
                    storage={1: 1}
                ),
            },
        ),
        (
            "6000600060006000600073b000000000000000000000000000000000000000620493e0f1506000600060006000600073dea0000000000000000000000000000000000000620927c0f100",  # noqa: E501
            400000,
            {
                Address("0xb000000000000000000000000000000000000000"): Account(
                    storage={1: 1}
                ),
                Address("0xc000000000000000000000000000000000000000"): Account(
                    storage={1: 1}
                ),
            },
        ),
        (
            "6000600060006000600073b000000000000000000000000000000000000000620493e0f2506000600060006000600073dea0000000000000000000000000000000000000620927c0f100",  # noqa: E501
            1000000,
            {
                Address("0x6295ee1b4f6dd65047762f924ecd367c17eabf8f"): Account(
                    storage={1: 1}
                ),
                Address("0xb000000000000000000000000000000000000000"): Account(
                    storage={1: 1}
                ),
                Address("0xc000000000000000000000000000000000000000"): Account(
                    storage={1: 1}
                ),
                Address("0xdea0000000000000000000000000000000000000"): Account(
                    storage={1: 1}
                ),
            },
        ),
        (
            "6000600060006000600073b000000000000000000000000000000000000000620493e0f2506000600060006000600073dea0000000000000000000000000000000000000620927c0f100",  # noqa: E501
            400000,
            {
                Address("0x6295ee1b4f6dd65047762f924ecd367c17eabf8f"): Account(
                    storage={1: 1}
                ),
                Address("0xb000000000000000000000000000000000000000"): Account(
                    storage={1: 1}
                ),
                Address("0xc000000000000000000000000000000000000000"): Account(
                    storage={1: 1}
                ),
            },
        ),
        (
            "600060006000600073b000000000000000000000000000000000000000620493e0f4506000600060006000600073dea0000000000000000000000000000000000000620927c0f100",  # noqa: E501
            1000000,
            {
                Address("0x6295ee1b4f6dd65047762f924ecd367c17eabf8f"): Account(
                    storage={1: 1}
                ),
                Address("0xb000000000000000000000000000000000000000"): Account(
                    storage={1: 1}
                ),
                Address("0xc000000000000000000000000000000000000000"): Account(
                    storage={1: 1}
                ),
                Address("0xdea0000000000000000000000000000000000000"): Account(
                    storage={1: 1}
                ),
            },
        ),
        (
            "600060006000600073b000000000000000000000000000000000000000620493e0f4506000600060006000600073dea0000000000000000000000000000000000000620927c0f100",  # noqa: E501
            400000,
            {
                Address("0x6295ee1b4f6dd65047762f924ecd367c17eabf8f"): Account(
                    storage={1: 1}
                ),
                Address("0xb000000000000000000000000000000000000000"): Account(
                    storage={1: 1}
                ),
                Address("0xc000000000000000000000000000000000000000"): Account(
                    storage={1: 1}
                ),
            },
        ),
        (
            "600060006000600073c000000000000000000000000000000000000000620493e0fa506000600060006000600073dea0000000000000000000000000000000000000620927c0f100",  # noqa: E501
            1000000,
            {
                Address("0xb000000000000000000000000000000000000000"): Account(
                    storage={1: 1}
                ),
                Address("0xc000000000000000000000000000000000000000"): Account(
                    storage={1: 1}
                ),
                Address("0xdea0000000000000000000000000000000000000"): Account(
                    storage={1: 1}
                ),
            },
        ),
        (
            "600060006000600073c000000000000000000000000000000000000000620493e0fa506000600060006000600073dea0000000000000000000000000000000000000620927c0f100",  # noqa: E501
            400000,
            {
                Address("0xb000000000000000000000000000000000000000"): Account(
                    storage={1: 1}
                ),
                Address("0xc000000000000000000000000000000000000000"): Account(
                    storage={1: 1}
                ),
            },
        ),
        (
            "6000601580603860003960006000f5506000600060006000600073dea0000000000000000000000000000000000000620927c0f1500000fe600160005560006000556001600055600160015500",  # noqa: E501
            1000000,
            {
                Address("0xb000000000000000000000000000000000000000"): Account(
                    storage={1: 1}
                ),
                Address("0xc000000000000000000000000000000000000000"): Account(
                    storage={1: 1}
                ),
                Address("0xdea0000000000000000000000000000000000000"): Account(
                    storage={1: 1}
                ),
                Address("0xeedfcf2cf4289ff428de4801d7cb0554e27809f3"): Account(
                    storage={0: 1, 1: 1}
                ),
            },
        ),
        (
            "6000601580603860003960006000f5506000600060006000600073dea0000000000000000000000000000000000000620927c0f1500000fe600160005560006000556001600055600160015500",  # noqa: E501
            400000,
            {
                Address("0xb000000000000000000000000000000000000000"): Account(
                    storage={1: 1}
                ),
                Address("0xc000000000000000000000000000000000000000"): Account(
                    storage={1: 1}
                ),
                Address("0xeedfcf2cf4289ff428de4801d7cb0554e27809f3"): Account(
                    storage={0: 1, 1: 1}
                ),
            },
        ),
        (
            "6000600060006000600073b000000000000000000000000000000000000000620493e0f1506000600060006000600073dea0000000000000000000000000000000000000620927c0f15060206000fd00",  # noqa: E501
            1000000,
            {
                Address("0xb000000000000000000000000000000000000000"): Account(
                    storage={1: 1}
                ),
                Address("0xc000000000000000000000000000000000000000"): Account(
                    storage={1: 1}
                ),
            },
        ),
        (
            "6000600060006000600073b000000000000000000000000000000000000000620493e0f1506000600060006000600073dea0000000000000000000000000000000000000620927c0f15060206000fd00",  # noqa: E501
            400000,
            {
                Address("0xb000000000000000000000000000000000000000"): Account(
                    storage={1: 1}
                ),
                Address("0xc000000000000000000000000000000000000000"): Account(
                    storage={1: 1}
                ),
            },
        ),
        (
            "6000600060006000600073b000000000000000000000000000000000000000620493e0f2506000600060006000600073dea0000000000000000000000000000000000000620927c0f15060206000fd00",  # noqa: E501
            1000000,
            {
                Address("0xb000000000000000000000000000000000000000"): Account(
                    storage={1: 1}
                ),
                Address("0xc000000000000000000000000000000000000000"): Account(
                    storage={1: 1}
                ),
            },
        ),
        (
            "6000600060006000600073b000000000000000000000000000000000000000620493e0f2506000600060006000600073dea0000000000000000000000000000000000000620927c0f15060206000fd00",  # noqa: E501
            400000,
            {
                Address("0xb000000000000000000000000000000000000000"): Account(
                    storage={1: 1}
                ),
                Address("0xc000000000000000000000000000000000000000"): Account(
                    storage={1: 1}
                ),
            },
        ),
        (
            "600060006000600073b000000000000000000000000000000000000000620493e0f4506000600060006000600073dea0000000000000000000000000000000000000620927c0f15060206000fd00",  # noqa: E501
            1000000,
            {
                Address("0xb000000000000000000000000000000000000000"): Account(
                    storage={1: 1}
                ),
                Address("0xc000000000000000000000000000000000000000"): Account(
                    storage={1: 1}
                ),
            },
        ),
        (
            "600060006000600073b000000000000000000000000000000000000000620493e0f4506000600060006000600073dea0000000000000000000000000000000000000620927c0f15060206000fd00",  # noqa: E501
            400000,
            {
                Address("0xb000000000000000000000000000000000000000"): Account(
                    storage={1: 1}
                ),
                Address("0xc000000000000000000000000000000000000000"): Account(
                    storage={1: 1}
                ),
            },
        ),
        (
            "600060006000600073c000000000000000000000000000000000000000620493e0fa506000600060006000600073dea0000000000000000000000000000000000000620927c0f15060206000fd00",  # noqa: E501
            1000000,
            {
                Address("0xb000000000000000000000000000000000000000"): Account(
                    storage={1: 1}
                ),
                Address("0xc000000000000000000000000000000000000000"): Account(
                    storage={1: 1}
                ),
            },
        ),
        (
            "600060006000600073c000000000000000000000000000000000000000620493e0fa506000600060006000600073dea0000000000000000000000000000000000000620927c0f15060206000fd00",  # noqa: E501
            400000,
            {
                Address("0xb000000000000000000000000000000000000000"): Account(
                    storage={1: 1}
                ),
                Address("0xc000000000000000000000000000000000000000"): Account(
                    storage={1: 1}
                ),
            },
        ),
        (
            "6000601580603d60003960006000f5506000600060006000600073dea0000000000000000000000000000000000000620927c0f15060206000fd0000fe600160005560006000556001600055600160015500",  # noqa: E501
            1000000,
            {
                Address("0xb000000000000000000000000000000000000000"): Account(
                    storage={1: 1}
                ),
                Address("0xc000000000000000000000000000000000000000"): Account(
                    storage={1: 1}
                ),
            },
        ),
        (
            "6000601580603d60003960006000f5506000600060006000600073dea0000000000000000000000000000000000000620927c0f15060206000fd0000fe600160005560006000556001600055600160015500",  # noqa: E501
            400000,
            {
                Address("0xb000000000000000000000000000000000000000"): Account(
                    storage={1: 1}
                ),
                Address("0xc000000000000000000000000000000000000000"): Account(
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
    ],
)
@pytest.mark.pre_alloc_mutable
def test_sstore_xto0to_x(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
    tx_gas_limit: int,
    expected_post: dict,
) -> None:
    """Change X -> 0 -> X."""
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
    # { [[1]] 0 [[1]] 1 }
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x1, value=0x0)
            + Op.SSTORE(key=0x1, value=0x1)
            + Op.STOP
        ),
        storage={0x1: 0x1},
        nonce=0,
        address=Address("0xb000000000000000000000000000000000000000"),  # noqa: E501
    )
    # Source: LLL
    # { [[1]] 0 [[1]] 1 }
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x1, value=0x0)
            + Op.SSTORE(key=0x1, value=0x1)
            + Op.STOP
        ),
        storage={0x1: 0x1},
        nonce=0,
        address=Address("0xc000000000000000000000000000000000000000"),  # noqa: E501
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
        gas_limit=tx_gas_limit,
        value=1,
    )

    post = expected_post

    state_test(env=env, pre=pre, post=post, tx=tx)
