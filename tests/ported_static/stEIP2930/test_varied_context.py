"""
Ori Pomerantz qbzzt1@gmail.com.

Ported from:
tests/static/state_tests/stEIP2930/variedContextFiller.yml
"""

import pytest
from execution_testing import (
    EOA,
    AccessList,
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
    ["tests/static/state_tests/stEIP2930/variedContextFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex, tx_access_list",
    [
        (
            "693c61390000000000000000000000000000000000000000000000000000000000000001",  # noqa: E501
            [
                AccessList(
                    address=Address(
                        "0x000000000000000000000000000000000000c057"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                        ),
                        Hash(
                            "0x00000000000000000000000000000000000000000000000000000000000060a7"  # noqa: E501
                        ),
                    ],
                )
            ],
        ),
        (
            "693c61390000000000000000000000000000000000000000000000000000000000000001",  # noqa: E501
            [
                AccessList(
                    address=Address(
                        "0x0000000000000000000000000000000000001001"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                        ),
                        Hash(
                            "0x00000000000000000000000000000000000000000000000000000000000060a7"  # noqa: E501
                        ),
                    ],
                )
            ],
        ),
        (
            "693c61390000000000000000000000000000000000000000000000000000000000000023",  # noqa: E501
            [
                AccessList(
                    address=Address(
                        "0x58fd03a2d731b2fb751e4a0f593d373ee77d39e6"
                    ),
                    storage_keys=[
                        Hash(
                            "0x000000000000000000000000000000000000000000000000000000000000ffff"  # noqa: E501
                        )
                    ],
                )
            ],
        ),
        (
            "693c61390000000000000000000000000000000000000000000000000000000000000023",  # noqa: E501
            [
                AccessList(
                    address=Address(
                        "0x530508498d2aa75d8e591612809fec3d37a45615"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                        )
                    ],
                )
            ],
        ),
        (
            "693c61390000000000000000000000000000000000000000000000000000000000000022",  # noqa: E501
            [
                AccessList(
                    address=Address(
                        "0x58fd03a2d731b2fb751e4a0f593d373ee77d39e6"
                    ),
                    storage_keys=[
                        Hash(
                            "0x000000000000000000000000000000000000000000000000000000000000ffff"  # noqa: E501
                        )
                    ],
                )
            ],
        ),
        (
            "693c61390000000000000000000000000000000000000000000000000000000000000022",  # noqa: E501
            [
                AccessList(
                    address=Address(
                        "0x58fd03a2d731b2fb751e4a0f593d373ee77d39e6"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                        )
                    ],
                )
            ],
        ),
        (
            "693c61390000000000000000000000000000000000000000000000000000000000000012",  # noqa: E501
            [
                AccessList(
                    address=Address(
                        "0x0000000000000000000000000000000000001012"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                        )
                    ],
                )
            ],
        ),
        (
            "693c61390000000000000000000000000000000000000000000000000000000000000012",  # noqa: E501
            [
                AccessList(
                    address=Address(
                        "0x00000000000000000000000000000000dead0112"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                        )
                    ],
                )
            ],
        ),
        (
            "693c61390000000000000000000000000000000000000000000000000000000000000010",  # noqa: E501
            [
                AccessList(
                    address=Address(
                        "0x0000000000000000000000000000000000001010"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                        ),
                        Hash(
                            "0x00000000000000000000000000000000000000000000000000000000000060a7"  # noqa: E501
                        ),
                    ],
                )
            ],
        ),
        (
            "693c61390000000000000000000000000000000000000000000000000000000000000010",  # noqa: E501
            [
                AccessList(
                    address=Address(
                        "0xcccccccccccccccccccccccccccccccccccccccc"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                        ),
                        Hash(
                            "0x00000000000000000000000000000000000000000000000000000000000060a7"  # noqa: E501
                        ),
                    ],
                )
            ],
        ),
        (
            "693c61390000000000000000000000000000000000000000000000000000000000000026",  # noqa: E501
            [
                AccessList(
                    address=Address(
                        "0x000000000000000000000000000000000000f126"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000020"  # noqa: E501
                        )
                    ],
                )
            ],
        ),
        (
            "693c61390000000000000000000000000000000000000000000000000000000000000026",  # noqa: E501
            [
                AccessList(
                    address=Address(
                        "0x000000000000000000000000000000000000f126"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                        )
                    ],
                )
            ],
        ),
        (
            "693c61390000000000000000000000000000000000000000000000000000000000000011",  # noqa: E501
            [
                AccessList(
                    address=Address(
                        "0x0000000000000000000000000000000000001011"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                        )
                    ],
                )
            ],
        ),
        (
            "693c61390000000000000000000000000000000000000000000000000000000000000011",  # noqa: E501
            [
                AccessList(
                    address=Address(
                        "0x00000000000000000000000000000000dead0111"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                        )
                    ],
                )
            ],
        ),
        (
            "693c61390000000000000000000000000000000000000000000000000000000000000002",  # noqa: E501
            [
                AccessList(
                    address=Address(
                        "0x000000000000000000000000000000000000c057"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                        ),
                        Hash(
                            "0x00000000000000000000000000000000000000000000000000000000000060a7"  # noqa: E501
                        ),
                    ],
                )
            ],
        ),
        (
            "693c61390000000000000000000000000000000000000000000000000000000000000002",  # noqa: E501
            [
                AccessList(
                    address=Address(
                        "0x0000000000000000000000000000000000001002"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                        ),
                        Hash(
                            "0x00000000000000000000000000000000000000000000000000000000000060a7"  # noqa: E501
                        ),
                    ],
                )
            ],
        ),
        (
            "693c61390000000000000000000000000000000000000000000000000000000000000025",  # noqa: E501
            [
                AccessList(
                    address=Address(
                        "0x58fd03a2d731b2fb751e4a0f593d373ee77d39e6"
                    ),
                    storage_keys=[
                        Hash(
                            "0x000000000000000000000000000000000000000000000000000000000000ffff"  # noqa: E501
                        )
                    ],
                )
            ],
        ),
        (
            "693c61390000000000000000000000000000000000000000000000000000000000000025",  # noqa: E501
            [
                AccessList(
                    address=Address(
                        "0x83fbdae70258ac0fa837b701cc63cedf48d4b6bf"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                        )
                    ],
                )
            ],
        ),
        (
            "693c61390000000000000000000000000000000000000000000000000000000000000021",  # noqa: E501
            [
                AccessList(
                    address=Address(
                        "0xf342e57f24e0333f3af34af08fdbbe9c72cbd37c"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                        )
                    ],
                )
            ],
        ),
        (
            "693c61390000000000000000000000000000000000000000000000000000000000000021",  # noqa: E501
            [
                AccessList(
                    address=Address(
                        "0xd82f21135ed7d7d833a9f2a0f1cf6c3da214b8e3"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                        )
                    ],
                )
            ],
        ),
        (
            "693c61390000000000000000000000000000000000000000000000000000000000000024",  # noqa: E501
            [
                AccessList(
                    address=Address(
                        "0x58fd03a2d731b2fb751e4a0f593d373ee77d39e6"
                    ),
                    storage_keys=[
                        Hash(
                            "0x000000000000000000000000000000000000000000000000000000000000ffff"  # noqa: E501
                        )
                    ],
                )
            ],
        ),
        (
            "693c61390000000000000000000000000000000000000000000000000000000000000024",  # noqa: E501
            [
                AccessList(
                    address=Address(
                        "0xb76ab2d646c4df221edd345957d0a396a2ab1b6d"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                        )
                    ],
                )
            ],
        ),
        (
            "693c61390000000000000000000000000000000000000000000000000000000000000020",  # noqa: E501
            [
                AccessList(
                    address=Address(
                        "0xf342e57f24e0333f3af34af08fdbbe9c72cbd37c"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000001"  # noqa: E501
                        )
                    ],
                )
            ],
        ),
        (
            "693c61390000000000000000000000000000000000000000000000000000000000000020",  # noqa: E501
            [
                AccessList(
                    address=Address(
                        "0xf342e57f24e0333f3af34af08fdbbe9c72cbd37c"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                        )
                    ],
                )
            ],
        ),
        (
            "693c61390000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
            [
                AccessList(
                    address=Address(
                        "0x000000000000000000000000000000000000c057"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                        ),
                        Hash(
                            "0x00000000000000000000000000000000000000000000000000000000000060a7"  # noqa: E501
                        ),
                    ],
                )
            ],
        ),
        (
            "693c61390000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
            [
                AccessList(
                    address=Address(
                        "0x0000000000000000000000000000000000001000"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                        ),
                        Hash(
                            "0x00000000000000000000000000000000000000000000000000000000000060a7"  # noqa: E501
                        ),
                    ],
                )
            ],
        ),
        (
            "693c61390000000000000000000000000000000000000000000000000000000000000015",  # noqa: E501
            [
                AccessList(
                    address=Address(
                        "0x0000000000000000000000000000000000001015"
                    ),
                    storage_keys=[
                        Hash(
                            "0x00000000000000000000000000000000000000000000000000000000000060a7"  # noqa: E501
                        )
                    ],
                )
            ],
        ),
        (
            "693c61390000000000000000000000000000000000000000000000000000000000000015",  # noqa: E501
            [
                AccessList(
                    address=Address(
                        "0x000000000000000000000000000000000000f115"
                    ),
                    storage_keys=[
                        Hash(
                            "0x00000000000000000000000000000000000000000000000000000000000060a7"  # noqa: E501
                        )
                    ],
                )
            ],
        ),
        (
            "693c61390000000000000000000000000000000000000000000000000000000000000016",  # noqa: E501
            [
                AccessList(
                    address=Address(
                        "0xf000000000000000000000000000000000000116"
                    ),
                    storage_keys=[
                        Hash(
                            "0x00000000000000000000000000000000000000000000000000000000000060a7"  # noqa: E501
                        ),
                        Hash(
                            "0x000000000000000000000000000000000000000000000000000000000000beef"  # noqa: E501
                        ),
                    ],
                )
            ],
        ),
        (
            "693c61390000000000000000000000000000000000000000000000000000000000000016",  # noqa: E501
            [
                AccessList(
                    address=Address(
                        "0x0000000000000000000000000000000000001016"
                    ),
                    storage_keys=[
                        Hash(
                            "0x00000000000000000000000000000000000000000000000000000000000060a7"  # noqa: E501
                        ),
                        Hash(
                            "0x000000000000000000000000000000000000000000000000000000000000beef"  # noqa: E501
                        ),
                        Hash(
                            "0x000000000000000000000000000000000000000000000000000000000000f000"  # noqa: E501
                        ),
                        Hash(
                            "0x000000000000000000000000000000000000000000000000000000000000f001"  # noqa: E501
                        ),
                        Hash(
                            "0x000000000000000000000000000000000000000000000000000000000000f002"  # noqa: E501
                        ),
                        Hash(
                            "0x000000000000000000000000000000000000000000000000000000000000f003"  # noqa: E501
                        ),
                        Hash(
                            "0x000000000000000000000000000000000000000000000000000000000000f004"  # noqa: E501
                        ),
                        Hash(
                            "0x000000000000000000000000000000000000000000000000000000000000f005"  # noqa: E501
                        ),
                        Hash(
                            "0x000000000000000000000000000000000000000000000000000000000000f006"  # noqa: E501
                        ),
                        Hash(
                            "0x000000000000000000000000000000000000000000000000000000000000f007"  # noqa: E501
                        ),
                        Hash(
                            "0x000000000000000000000000000000000000000000000000000000000000f008"  # noqa: E501
                        ),
                        Hash(
                            "0x000000000000000000000000000000000000000000000000000000000000f009"  # noqa: E501
                        ),
                        Hash(
                            "0x000000000000000000000000000000000000000000000000000000000000f00a"  # noqa: E501
                        ),
                        Hash(
                            "0x000000000000000000000000000000000000000000000000000000000000f00b"  # noqa: E501
                        ),
                        Hash(
                            "0x000000000000000000000000000000000000000000000000000000000000f00c"  # noqa: E501
                        ),
                        Hash(
                            "0x000000000000000000000000000000000000000000000000000000000000f00d"  # noqa: E501
                        ),
                        Hash(
                            "0x000000000000000000000000000000000000000000000000000000000000f00e"  # noqa: E501
                        ),
                        Hash(
                            "0x000000000000000000000000000000000000000000000000000000000000f00f"  # noqa: E501
                        ),
                        Hash(
                            "0x000000000000000000000000000000000000000000000000000000000000f010"  # noqa: E501
                        ),
                        Hash(
                            "0x000000000000000000000000000000000000000000000000000000000000f011"  # noqa: E501
                        ),
                        Hash(
                            "0x000000000000000000000000000000000000000000000000000000000000f012"  # noqa: E501
                        ),
                        Hash(
                            "0x000000000000000000000000000000000000000000000000000000000000f013"  # noqa: E501
                        ),
                        Hash(
                            "0x000000000000000000000000000000000000000000000000000000000000f014"  # noqa: E501
                        ),
                        Hash(
                            "0x000000000000000000000000000000000000000000000000000000000000f015"  # noqa: E501
                        ),
                        Hash(
                            "0x000000000000000000000000000000000000000000000000000000000000f016"  # noqa: E501
                        ),
                        Hash(
                            "0x000000000000000000000000000000000000000000000000000000000000f017"  # noqa: E501
                        ),
                        Hash(
                            "0x000000000000000000000000000000000000000000000000000000000000f018"  # noqa: E501
                        ),
                        Hash(
                            "0x000000000000000000000000000000000000000000000000000000000000f019"  # noqa: E501
                        ),
                        Hash(
                            "0x000000000000000000000000000000000000000000000000000000000000f01a"  # noqa: E501
                        ),
                        Hash(
                            "0x000000000000000000000000000000000000000000000000000000000000f01b"  # noqa: E501
                        ),
                        Hash(
                            "0x000000000000000000000000000000000000000000000000000000000000f01c"  # noqa: E501
                        ),
                        Hash(
                            "0x000000000000000000000000000000000000000000000000000000000000f01d"  # noqa: E501
                        ),
                        Hash(
                            "0x000000000000000000000000000000000000000000000000000000000000f01e"  # noqa: E501
                        ),
                        Hash(
                            "0x000000000000000000000000000000000000000000000000000000000000f01f"  # noqa: E501
                        ),
                    ],
                )
            ],
        ),
        (
            "693c61390000000000000000000000000000000000000000000000000000000000000013",  # noqa: E501
            [
                AccessList(
                    address=Address(
                        "0x0000000000000000000000000000000000000000"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                        )
                    ],
                )
            ],
        ),
        (
            "693c61390000000000000000000000000000000000000000000000000000000000000013",  # noqa: E501
            [
                AccessList(
                    address=Address(
                        "0x000000000000000000000000000000000000f113"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                        )
                    ],
                )
            ],
        ),
        (
            "693c61390000000000000000000000000000000000000000000000000000000000000003",  # noqa: E501
            [
                AccessList(
                    address=Address(
                        "0x00000000000000000000000000000000ead0c057"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                        ),
                        Hash(
                            "0x00000000000000000000000000000000000000000000000000000000000060a7"  # noqa: E501
                        ),
                    ],
                )
            ],
        ),
        (
            "693c61390000000000000000000000000000000000000000000000000000000000000003",  # noqa: E501
            [
                AccessList(
                    address=Address(
                        "0x0000000000000000000000000000000000001003"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                        ),
                        Hash(
                            "0x00000000000000000000000000000000000000000000000000000000000060a7"  # noqa: E501
                        ),
                    ],
                )
            ],
        ),
        (
            "693c61390000000000000000000000000000000000000000000000000000000000000014",  # noqa: E501
            [
                AccessList(
                    address=Address(
                        "0x0000000000000000000000000000000000001014"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                        )
                    ],
                )
            ],
        ),
        (
            "693c61390000000000000000000000000000000000000000000000000000000000000014",  # noqa: E501
            [
                AccessList(
                    address=Address(
                        "0x000000000000000000000000000000000000f114"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                        )
                    ],
                )
            ],
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
        "case24",
        "case25",
        "case26",
        "case27",
        "case28",
        "case29",
        "case30",
        "case31",
        "case32",
        "case33",
        "case34",
        "case35",
    ],
)
@pytest.mark.pre_alloc_mutable
def test_varied_context(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
    tx_access_list: list | None,
) -> None:
    """Ori Pomerantz qbzzt1@gmail.com."""
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
        gas_limit=71794957647893862,
    )

    pre.deploy_contract(
        code=(
            Op.DELEGATECALL(
                gas=Op.GAS,
                address=0xC057,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
            + Op.STOP
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001000"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.CALL(
                gas=Op.GAS,
                address=0xC057,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
            + Op.STOP
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001001"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.CALLCODE(
                gas=Op.GAS,
                address=0xC057,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
            + Op.STOP
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001002"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.POP(
                Op.STATICCALL(
                    gas=Op.GAS,
                    address=0xEAD0C057,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x20,
                ),
            )
            + Op.SSTORE(key=0x0, value=Op.MLOAD(offset=0x0))
            + Op.STOP
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001003"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x0, value=Op.GAS)
            + Op.SSTORE(key=0x0, value=0x2)
            + Op.MSTORE(
                offset=0x0,
                value=Op.SUB(Op.SUB(Op.MLOAD(offset=0x0), Op.GAS), 0x11),
            )
            + Op.MSTORE(offset=0x20, value=Op.GAS)
            + Op.MSTORE(offset=0x40, value=Op.SLOAD(key=0x60A7))
            + Op.MSTORE(
                offset=0x20,
                value=Op.SUB(Op.SUB(Op.MLOAD(offset=0x20), Op.GAS), 0x1A),
            )
            + Op.REVERT(offset=0x0, size=0x40)
            + Op.STOP
        ),
        storage={0x60A7: 0xBEEF},
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001010"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x0, value=Op.GAS)
            + Op.POP(
                Op.CALL(
                    gas=Op.GAS,
                    address=0xDEAD0111,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.SSTORE(
                key=0x0,
                value=Op.SUB(Op.SUB(Op.MLOAD(offset=0x0), Op.GAS), 0x7FE8),
            )
            + Op.STOP
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001011"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x0, value=Op.GAS)
            + Op.POP(
                Op.CALL(
                    gas=Op.GAS,
                    address=0xDEAD0112,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.SSTORE(
                key=0x0,
                value=Op.SUB(Op.SUB(Op.MLOAD(offset=0x0), Op.GAS), 0x7FE8),
            )
            + Op.STOP
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001012"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x0, value=0xBAD)
            + Op.POP(
                Op.STATICCALL(
                    gas=Op.GAS,
                    address=0xF113,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x20,
                ),
            )
            + Op.SSTORE(key=0x0, value=Op.MLOAD(offset=0x0))
            + Op.STOP
        ),
        storage={0x0: 0x60A7},
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001013"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.CALL(
                gas=0xB65,
                address=0xF114,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.STOP
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001014"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.CALL(
                gas=0x1800,
                address=0xF115,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.STOP
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001015"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.POP(Op.SLOAD(key=0x0))
            + Op.MSTORE(offset=0x0, value=Op.GAS)
            + Op.SSTORE(key=0xBEEF, value=0x2)
            + Op.MSTORE(
                offset=0x0,
                value=Op.SUB(Op.SUB(Op.MLOAD(offset=0x0), Op.GAS), 0x11),
            )
            + Op.MSTORE(offset=0x20, value=Op.GAS)
            + Op.MSTORE(offset=0xA0, value=Op.SLOAD(key=0x60A7))
            + Op.MSTORE(
                offset=0x20,
                value=Op.SUB(Op.SUB(Op.MLOAD(offset=0x20), Op.GAS), 0x23),
            )
            + Op.MSTORE(offset=0x40, value=Op.GAS)
            + Op.SSTORE(key=Op.ADD(0xF000, Op.SLOAD(key=0x0)), value=0xBEEF)
            + Op.MSTORE(
                offset=0x40,
                value=Op.SUB(Op.SUB(Op.MLOAD(offset=0x40), Op.GAS), 0x78),
            )
            + Op.MSTORE(offset=0x60, value=Op.GAS)
            + Op.POP(Op.SLOAD(key=Op.ADD(0xF010, Op.SLOAD(key=0x0))))
            + Op.MSTORE(
                offset=0x60,
                value=Op.SUB(Op.SUB(Op.MLOAD(offset=0x60), Op.GAS), 0x7A),
            )
            + Op.SSTORE(
                key=Op.ADD(0x100, Op.SLOAD(key=0x0)),
                value=Op.MLOAD(offset=0x0),
            )
            + Op.SSTORE(
                key=Op.ADD(0x200, Op.SLOAD(key=0x0)),
                value=Op.MLOAD(offset=0x20),
            )
            + Op.SSTORE(
                key=Op.ADD(0x300, Op.SLOAD(key=0x0)),
                value=Op.MLOAD(offset=0x40),
            )
            + Op.SSTORE(
                key=Op.ADD(0x400, Op.SLOAD(key=0x0)),
                value=Op.MLOAD(offset=0x60),
            )
            + Op.JUMPI(pc=0x9B, condition=Op.GT(Op.SLOAD(key=0x0), 0x0))
            + Op.PUSH1[0x0]
            + Op.JUMP(pc=0xB4)
            + Op.JUMPDEST
            + Op.SSTORE(key=0x0, value=Op.SUB(Op.SLOAD(key=0x0), 0x1))
            + Op.CALL(
                gas=Op.GAS,
                address=0x1016,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
            + Op.JUMPDEST
            + Op.STOP
        ),
        storage={0x0: 0xF, 0x60A7: 0xDEAD},
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001016"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.PUSH1[0x6]
            + Op.CODECOPY(dest_offset=0x100, offset=0x33, size=Op.DUP1)
            + Op.PUSH2[0x200]
            + Op.MSTORE
            + Op.PUSH1[0x21]
            + Op.CODECOPY(dest_offset=0x0, offset=0x39, size=Op.DUP1)
            + Op.PUSH2[0x220]
            + Op.MSTORE
            + Op.MSTORE(
                offset=0x240,
                value=Op.CREATE(
                    value=0x0,
                    offset=0x0,
                    size=Op.ADD(0x100, Op.MLOAD(offset=0x200)),
                ),
            )
            + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x240))
            + Op.STOP
            + Op.INVALID
            + Op.SSTORE(key=0x0, value=0xFF)
            + Op.STOP
            + Op.MSTORE(offset=0x0, value=Op.GAS)
            + Op.SSTORE(key=0x0, value=0xFFFF)
            + Op.SSTORE(key=0x1, value=Op.SUB(Op.MLOAD(offset=0x0), Op.GAS))
            + Op.CODECOPY(dest_offset=0x0, offset=0x100, size=0x100)
            + Op.RETURN(offset=0x0, size=0x10)
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001020"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.PUSH1[0x6]
            + Op.CODECOPY(dest_offset=0x100, offset=0x36, size=Op.DUP1)
            + Op.PUSH2[0x200]
            + Op.MSTORE
            + Op.PUSH1[0x21]
            + Op.CODECOPY(dest_offset=0x0, offset=0x3C, size=Op.DUP1)
            + Op.PUSH2[0x220]
            + Op.MSTORE
            + Op.MSTORE(
                offset=0x240,
                value=Op.CREATE2(
                    value=0x0,
                    offset=0x0,
                    size=Op.ADD(0x100, Op.MLOAD(offset=0x200)),
                    salt=0x5A17,
                ),
            )
            + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x240))
            + Op.STOP
            + Op.INVALID
            + Op.SSTORE(key=0x0, value=0xFF)
            + Op.STOP
            + Op.MSTORE(offset=0x0, value=Op.GAS)
            + Op.SSTORE(key=0x0, value=0xFFFF)
            + Op.SSTORE(key=0x1, value=Op.SUB(Op.MLOAD(offset=0x0), Op.GAS))
            + Op.CODECOPY(dest_offset=0x0, offset=0x100, size=0x100)
            + Op.RETURN(offset=0x0, size=0x10)
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001021"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.PUSH1[0x13]
            + Op.CODECOPY(dest_offset=0x100, offset=0x44, size=Op.DUP1)
            + Op.PUSH2[0x200]
            + Op.MSTORE
            + Op.PUSH1[0xF]
            + Op.CODECOPY(dest_offset=0x0, offset=0x57, size=Op.DUP1)
            + Op.PUSH2[0x220]
            + Op.MSTORE
            + Op.MSTORE(
                offset=0x240,
                value=Op.CREATE(
                    value=0x0,
                    offset=0x0,
                    size=Op.ADD(0x100, Op.MLOAD(offset=0x200)),
                ),
            )
            + Op.POP(
                Op.CALL(
                    gas=Op.GAS,
                    address=Op.MLOAD(offset=0x240),
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x240))
            + Op.STOP
            + Op.INVALID
            + Op.MSTORE(offset=0x0, value=Op.GAS)
            + Op.SSTORE(key=0x0, value=0xFFFF)
            + Op.SSTORE(key=0x1, value=Op.SUB(Op.MLOAD(offset=0x0), Op.GAS))
            + Op.STOP
            + Op.CODECOPY(dest_offset=0x0, offset=0x100, size=0x100)
            + Op.RETURN(offset=0x0, size=0x80)
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001022"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.PUSH1[0x13]
            + Op.CODECOPY(dest_offset=0x100, offset=0x47, size=Op.DUP1)
            + Op.PUSH2[0x200]
            + Op.MSTORE
            + Op.PUSH1[0xF]
            + Op.CODECOPY(dest_offset=0x0, offset=0x5A, size=Op.DUP1)
            + Op.PUSH2[0x220]
            + Op.MSTORE
            + Op.MSTORE(
                offset=0x240,
                value=Op.CREATE2(
                    value=0x0,
                    offset=0x0,
                    size=Op.ADD(0x100, Op.MLOAD(offset=0x200)),
                    salt=0x5A17,
                ),
            )
            + Op.POP(
                Op.CALL(
                    gas=Op.GAS,
                    address=Op.MLOAD(offset=0x240),
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x240))
            + Op.STOP
            + Op.INVALID
            + Op.MSTORE(offset=0x0, value=Op.GAS)
            + Op.SSTORE(key=0x0, value=0xFFFF)
            + Op.SSTORE(key=0x1, value=Op.SUB(Op.MLOAD(offset=0x0), Op.GAS))
            + Op.STOP
            + Op.CODECOPY(dest_offset=0x0, offset=0x100, size=0x100)
            + Op.RETURN(offset=0x0, size=0x80)
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001023"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.PUSH1[0x13]
            + Op.CODECOPY(dest_offset=0x100, offset=0x44, size=Op.DUP1)
            + Op.PUSH2[0x200]
            + Op.MSTORE
            + Op.PUSH1[0x21]
            + Op.CODECOPY(dest_offset=0x0, offset=0x57, size=Op.DUP1)
            + Op.PUSH2[0x220]
            + Op.MSTORE
            + Op.MSTORE(
                offset=0x240,
                value=Op.CREATE(
                    value=0x0,
                    offset=0x0,
                    size=Op.ADD(0x100, Op.MLOAD(offset=0x200)),
                ),
            )
            + Op.POP(
                Op.CALL(
                    gas=Op.GAS,
                    address=Op.MLOAD(offset=0x240),
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x240))
            + Op.STOP
            + Op.INVALID
            + Op.MSTORE(offset=0x0, value=Op.GAS)
            + Op.SSTORE(key=0x0, value=0xFFFF)
            + Op.SSTORE(key=0x2, value=Op.SUB(Op.MLOAD(offset=0x0), Op.GAS))
            + Op.STOP
            + Op.MSTORE(offset=0x0, value=Op.GAS)
            + Op.SSTORE(key=0x0, value=0xFFFF)
            + Op.SSTORE(key=0x1, value=Op.SUB(Op.MLOAD(offset=0x0), Op.GAS))
            + Op.CODECOPY(dest_offset=0x0, offset=0x100, size=0x100)
            + Op.RETURN(offset=0x0, size=0x80)
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001024"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.PUSH1[0x13]
            + Op.CODECOPY(dest_offset=0x100, offset=0x47, size=Op.DUP1)
            + Op.PUSH2[0x200]
            + Op.MSTORE
            + Op.PUSH1[0x21]
            + Op.CODECOPY(dest_offset=0x0, offset=0x5A, size=Op.DUP1)
            + Op.PUSH2[0x220]
            + Op.MSTORE
            + Op.MSTORE(
                offset=0x240,
                value=Op.CREATE2(
                    value=0x0,
                    offset=0x0,
                    size=Op.ADD(0x100, Op.MLOAD(offset=0x200)),
                    salt=0x5A17,
                ),
            )
            + Op.POP(
                Op.CALL(
                    gas=Op.GAS,
                    address=Op.MLOAD(offset=0x240),
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x240))
            + Op.STOP
            + Op.INVALID
            + Op.MSTORE(offset=0x0, value=Op.GAS)
            + Op.SSTORE(key=0x0, value=0xFFFF)
            + Op.SSTORE(key=0x2, value=Op.SUB(Op.MLOAD(offset=0x0), Op.GAS))
            + Op.STOP
            + Op.MSTORE(offset=0x0, value=Op.GAS)
            + Op.SSTORE(key=0x0, value=0xFFFF)
            + Op.SSTORE(key=0x1, value=Op.SUB(Op.MLOAD(offset=0x0), Op.GAS))
            + Op.CODECOPY(dest_offset=0x0, offset=0x100, size=0x100)
            + Op.RETURN(offset=0x0, size=0x80)
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001025"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.POP(
                Op.CALL(
                    gas=Op.GAS,
                    address=0xF126,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.CALL(
                gas=Op.GAS,
                address=0xF126,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001026"),  # noqa: E501
    )
    # Source: LLL
    # {
    #    ; 0xC057: DELEGATE_VALID DELEGATE_INVALID
    #    ;         CALL_INVALID CALL_VALID
    #    ;         CALLCODE_VALID CALLCODE_INVALID
    #
    #
    #  ; Write to [[0]], and see how much gas that cost. It should
    #  ; cost more when it is not declared storage
    #    [0]   (gas)
    #   [[0]]  0x02
    #    [0]   (- @0 (gas) 17)
    #   [[1]] @0
    #
    #  ; The 17 is the cost of the extra opcodes:
    #  ; PUSH1 0x00, MSTORE
    #  ; PUSH1 0x02, PUSH1 0x00, (and then comes the SSTORE we are measuring)
    #  ; GAS
    #
    #  ; Read [[0x60A7]], and see how much gas that cost. It should
    #  ; cost more when it is not declared storage
    #    [0]   (gas)
    #   [0x20] @@0x60A7
    #    [0]   (- @0 (gas) 16)
    #   [[2]] @0
    #
    #  ; The 16 is the cost of the extra opcodes
    # }
    pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x0, value=Op.GAS)
            + Op.SSTORE(key=0x0, value=0x2)
            + Op.MSTORE(
                offset=0x0,
                value=Op.SUB(Op.SUB(Op.MLOAD(offset=0x0), Op.GAS), 0x11),
            )
            + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x0))
            + Op.MSTORE(offset=0x0, value=Op.GAS)
            + Op.MSTORE(offset=0x20, value=Op.SLOAD(key=0x60A7))
            + Op.MSTORE(
                offset=0x0,
                value=Op.SUB(Op.SUB(Op.MLOAD(offset=0x0), Op.GAS), 0x10),
            )
            + Op.SSTORE(key=0x2, value=Op.MLOAD(offset=0x0))
            + Op.STOP
        ),
        storage={0x60A7: 0xDEAD},
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0x000000000000000000000000000000000000c057"),  # noqa: E501
    )
    # Source: LLL
    # {  ; STATIC_WRITE_VALID     STATIC_WRITE_INVALID
    #    [[0]] 0xDEAD60A7
    #
    #    ; If we get here, GOOD
    #    [0] 0x600D
    #    (return 0 0x20)
    # }
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0xDEAD60A7)
            + Op.MSTORE(offset=0x0, value=0x600D)
            + Op.RETURN(offset=0x0, size=0x20)
            + Op.STOP
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0x000000000000000000000000000000000000f113"),  # noqa: E501
    )
    # Source: LLL
    # {  ; WRITE_INVALID_OOG    WRITE_VALID_NO_OOG
    #
    #   [[0]] 0x600D
    # }
    pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=0x600D) + Op.STOP,
        storage={0x0: 0xBAD},
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0x000000000000000000000000000000000000f114"),  # noqa: E501
    )
    # Source: LLL
    # {  ; READ_INVALID_OOG    READ_VALID_NO_OOG
    #    [0] @@0x60A7
    #    [[0]] 0x600D
    # }
    pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x0, value=Op.SLOAD(key=0x60A7))
            + Op.SSTORE(key=0x0, value=0x600D)
            + Op.STOP
        ),
        storage={0x0: 0xBAD, 0x60A7: 0xDEAD},
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0x000000000000000000000000000000000000f115"),  # noqa: E501
    )
    # Source: LLL
    # {
    #   ; CALL_TWICE_VALID     CALL_TWICE_INVALID
    #   [0] (gas)
    #   [[0x00]] 0x60A7
    #   [0] (- @0 (gas))
    #
    #   ; If @@1 is empty, write to it. Otherwise, write to @@2
    #   (if (= @@1 0) {[[1]] @0} {[[2]] @0})
    #
    # }
    pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x0, value=Op.GAS)
            + Op.SSTORE(key=0x0, value=0x60A7)
            + Op.MSTORE(offset=0x0, value=Op.SUB(Op.MLOAD(offset=0x0), Op.GAS))
            + Op.JUMPI(pc=0x24, condition=Op.EQ(Op.SLOAD(key=0x1), 0x0))
            + Op.SSTORE(key=0x2, value=Op.MLOAD(offset=0x0))
            + Op.JUMP(pc=0x2B)
            + Op.JUMPDEST
            + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x0))
            + Op.JUMPDEST
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x000000000000000000000000000000000000f126"),  # noqa: E501
    )
    # Source: LLL
    # {
    #    ; CALL_WRITE_SUICIDE_VALID      CALL_WRITE_SUICIDE_INVALID
    #    [[0]] 0xDEAD
    #
    #    (selfdestruct 0)
    # }
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0xDEAD)
            + Op.SELFDESTRUCT(address=0x0)
            + Op.STOP
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0x00000000000000000000000000000000dead0111"),  # noqa: E501
    )
    # Source: LLL
    # {
    #    ; CALL_READ_SUICIDE_VALID      CALL_READ_SUICIDE_INVALID
    #    @@0
    #
    #    (selfdestruct 0)
    # }
    pre.deploy_contract(
        code=(
            Op.POP(Op.SLOAD(key=0x0)) + Op.SELFDESTRUCT(address=0x0) + Op.STOP
        ),
        storage={0x0: 0xDEAD0060A7},
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0x00000000000000000000000000000000dead0112"),  # noqa: E501
    )
    # Source: LLL
    # {
    #  ;   STATICCALL_VALID  STATICCALL_INVALID
    #
    #
    #  ; Read [[0x60A7]], and see how much gas that cost. It should
    #  ; cost more when it is not declared storage
    #    [0]   (gas)
    #  [0x20] @@0x60A7
    #    [0]   (- @0 (gas) 19)
    #  ; The 19 is the cost of the extra opcodes
    #
    #  (return 0x00 0x20) ; a.k.a. @0
    # }
    pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x0, value=Op.GAS)
            + Op.MSTORE(offset=0x20, value=Op.SLOAD(key=0x60A7))
            + Op.MSTORE(
                offset=0x0,
                value=Op.SUB(Op.SUB(Op.MLOAD(offset=0x0), Op.GAS), 0x13),
            )
            + Op.RETURN(offset=0x0, size=0x20)
            + Op.STOP
        ),
        storage={0x60A7: 0xDEAD},
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0x00000000000000000000000000000000ead0c057"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)
    # Source: LLL
    # {
    #     ; ccc...ccc  revert and suicide contract
    #     (call (gas) (+ 0x1000 $4) 0 0 0 0 0x40)
    #
    #     ; Write the returned results, if any
    #     [[0]] @0x00
    #     [[1]] @0x20
    # }
    contract = pre.deploy_contract(
        code=(
            Op.POP(
                Op.CALL(
                    gas=Op.GAS,
                    address=Op.ADD(0x1000, Op.CALLDATALOAD(offset=0x4)),
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x40,
                ),
            )
            + Op.SSTORE(key=0x0, value=Op.MLOAD(offset=0x0))
            + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x20))
            + Op.STOP
        ),
        nonce=0,
        address=Address("0xcccccccccccccccccccccccccccccccccccccccc"),  # noqa: E501
    )

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        sender=sender,
        to=contract,
        data=tx_data,
        gas_limit=16777216,
        value=100000,
        access_list=tx_access_list,
    )

    post = {
        Address("0x0000000000000000000000000000000000000512"): Account(
            storage={0: 2, 1: 20003, 2: 107},
        ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
