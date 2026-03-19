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
from execution_testing.forks import Fork
from execution_testing.specs.static_state.expect_section import (
    resolve_expect_post,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

TX_DATA = [
    "693c61390000000000000000000000000000000000000000000000000000000000000001",
    "693c61390000000000000000000000000000000000000000000000000000000000000001",
    "693c61390000000000000000000000000000000000000000000000000000000000000023",
    "693c61390000000000000000000000000000000000000000000000000000000000000023",
    "693c61390000000000000000000000000000000000000000000000000000000000000022",
    "693c61390000000000000000000000000000000000000000000000000000000000000022",
    "693c61390000000000000000000000000000000000000000000000000000000000000012",
    "693c61390000000000000000000000000000000000000000000000000000000000000012",
    "693c61390000000000000000000000000000000000000000000000000000000000000010",
    "693c61390000000000000000000000000000000000000000000000000000000000000010",
    "693c61390000000000000000000000000000000000000000000000000000000000000026",
    "693c61390000000000000000000000000000000000000000000000000000000000000026",
    "693c61390000000000000000000000000000000000000000000000000000000000000011",
    "693c61390000000000000000000000000000000000000000000000000000000000000011",
    "693c61390000000000000000000000000000000000000000000000000000000000000002",
    "693c61390000000000000000000000000000000000000000000000000000000000000002",
    "693c61390000000000000000000000000000000000000000000000000000000000000025",
    "693c61390000000000000000000000000000000000000000000000000000000000000025",
    "693c61390000000000000000000000000000000000000000000000000000000000000021",
    "693c61390000000000000000000000000000000000000000000000000000000000000021",
    "693c61390000000000000000000000000000000000000000000000000000000000000024",
    "693c61390000000000000000000000000000000000000000000000000000000000000024",
    "693c61390000000000000000000000000000000000000000000000000000000000000020",
    "693c61390000000000000000000000000000000000000000000000000000000000000020",
    "693c61390000000000000000000000000000000000000000000000000000000000000000",
    "693c61390000000000000000000000000000000000000000000000000000000000000000",
    "693c61390000000000000000000000000000000000000000000000000000000000000015",
    "693c61390000000000000000000000000000000000000000000000000000000000000015",
    "693c61390000000000000000000000000000000000000000000000000000000000000016",
    "693c61390000000000000000000000000000000000000000000000000000000000000016",
    "693c61390000000000000000000000000000000000000000000000000000000000000013",
    "693c61390000000000000000000000000000000000000000000000000000000000000013",
    "693c61390000000000000000000000000000000000000000000000000000000000000003",
    "693c61390000000000000000000000000000000000000000000000000000000000000003",
    "693c61390000000000000000000000000000000000000000000000000000000000000014",
    "693c61390000000000000000000000000000000000000000000000000000000000000014",
]

TX_GAS = [16777216]

TX_VALUE = [100000]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d]) if TX_DATA[d] else b""


@pytest.mark.ported_from(
    ["tests/static/state_tests/stEIP2930/variedContextFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v, tx_access_list",
    [
        pytest.param(
            0,
            0,
            0,
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
            id="case0",
        ),
        pytest.param(
            1,
            0,
            0,
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
            id="case1",
        ),
        pytest.param(
            2,
            0,
            0,
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
            id="case2",
        ),
        pytest.param(
            3,
            0,
            0,
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
            id="case3",
        ),
        pytest.param(
            4,
            0,
            0,
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
            id="case4",
        ),
        pytest.param(
            5,
            0,
            0,
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
            id="case5",
        ),
        pytest.param(
            6,
            0,
            0,
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
            id="case6",
        ),
        pytest.param(
            7,
            0,
            0,
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
            id="case7",
        ),
        pytest.param(
            8,
            0,
            0,
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
            id="case8",
        ),
        pytest.param(
            9,
            0,
            0,
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
            id="case9",
        ),
        pytest.param(
            10,
            0,
            0,
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
            id="case10",
        ),
        pytest.param(
            11,
            0,
            0,
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
            id="case11",
        ),
        pytest.param(
            12,
            0,
            0,
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
            id="case12",
        ),
        pytest.param(
            13,
            0,
            0,
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
            id="case13",
        ),
        pytest.param(
            14,
            0,
            0,
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
            id="case14",
        ),
        pytest.param(
            15,
            0,
            0,
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
            id="case15",
        ),
        pytest.param(
            16,
            0,
            0,
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
            id="case16",
        ),
        pytest.param(
            17,
            0,
            0,
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
            id="case17",
        ),
        pytest.param(
            18,
            0,
            0,
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
            id="case18",
        ),
        pytest.param(
            19,
            0,
            0,
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
            id="case19",
        ),
        pytest.param(
            20,
            0,
            0,
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
            id="case20",
        ),
        pytest.param(
            21,
            0,
            0,
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
            id="case21",
        ),
        pytest.param(
            22,
            0,
            0,
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
            id="case22",
        ),
        pytest.param(
            23,
            0,
            0,
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
            id="case23",
        ),
        pytest.param(
            24,
            0,
            0,
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
            id="case24",
        ),
        pytest.param(
            25,
            0,
            0,
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
            id="case25",
        ),
        pytest.param(
            26,
            0,
            0,
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
            id="case26",
        ),
        pytest.param(
            27,
            0,
            0,
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
            id="case27",
        ),
        pytest.param(
            28,
            0,
            0,
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
            id="case28",
        ),
        pytest.param(
            29,
            0,
            0,
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
            id="case29",
        ),
        pytest.param(
            30,
            0,
            0,
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
            id="case30",
        ),
        pytest.param(
            31,
            0,
            0,
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
            id="case31",
        ),
        pytest.param(
            32,
            0,
            0,
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
            id="case32",
        ),
        pytest.param(
            33,
            0,
            0,
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
            id="case33",
        ),
        pytest.param(
            34,
            0,
            0,
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
            id="case34",
        ),
        pytest.param(
            35,
            0,
            0,
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
            id="case35",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_varied_context(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
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

    callee = pre.deploy_contract(
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
    callee_1 = pre.deploy_contract(
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
    callee_2 = pre.deploy_contract(
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
    callee_3 = pre.deploy_contract(
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
    callee_4 = pre.deploy_contract(
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
    callee_5 = pre.deploy_contract(
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
    callee_6 = pre.deploy_contract(
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
    callee_7 = pre.deploy_contract(
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
    callee_8 = pre.deploy_contract(
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
    callee_9 = pre.deploy_contract(
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
    callee_10 = pre.deploy_contract(
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
    callee_11 = pre.deploy_contract(
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
    callee_12 = pre.deploy_contract(
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
    callee_13 = pre.deploy_contract(
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
    callee_14 = pre.deploy_contract(
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
    callee_15 = pre.deploy_contract(
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
    callee_16 = pre.deploy_contract(
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
    callee_17 = pre.deploy_contract(
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
    callee_18 = pre.deploy_contract(
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
    callee_19 = pre.deploy_contract(
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
    callee_20 = pre.deploy_contract(
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
    callee_21 = pre.deploy_contract(
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
    callee_22 = pre.deploy_contract(
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
    callee_23 = pre.deploy_contract(
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
    callee_24 = pre.deploy_contract(
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
    callee_25 = pre.deploy_contract(
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

    EXPECT_ENTRIES: list[dict] = [
        {
            "indexes": {"data": 0, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex("600060006000600061c0575af400")
                ),
                callee_1: Account(
                    code=bytes.fromhex("6000600060006000600061c0575af100")
                ),
                callee_2: Account(
                    code=bytes.fromhex("6000600060006000600061c0575af200")
                ),
                callee_3: Account(
                    code=bytes.fromhex(
                        "602060006000600063ead0c0575afa5060005160005500"
                    )
                ),
                callee_4: Account(
                    storage={24743: 48879},
                    code=bytes.fromhex(
                        "5a600052600260005560115a60005103036000525a6020526160a754604052601a5a602051030360205260406000fd00"  # noqa: E501
                    ),
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "5a6000526000600060006000600063dead01115af150617fe85a600051030360005500"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "5a6000526000600060006000600063dead01125af150617fe85a600051030360005500"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "610bad600052602060006000600061f1135afa5060005160005500"  # noqa: E501
                    ),
                ),
                callee_8: Account(
                    code=bytes.fromhex("6020600060006000600061f114610b65f100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6020600060006000600061f115611800f100")
                ),
                callee_10: Account(
                    storage={0: 15, 24743: 57005},
                    code=bytes.fromhex(
                        "600054505a600052600261beef5560115a60005103036000525a6020526160a75460a05260235a60205103036020525a60405261beef60005461f000015560785a60405103036040525a60605260005461f010015450607a5a60605103036060526000516000546101000155602051600054610200015560405160005461030001556060516000546104000155600060005411609b57600060b4565b600160005403600055600060006000600060006110165af15b00"  # noqa: E501
                    ),
                ),
                callee_11: Account(
                    code=bytes.fromhex(
                        "60068060336101003961020052602180603960003961022052610200516101000160006000f0610240526102405160015500fe60ff600055005a60005261ffff6000555a6000510360015561010061010060003960106000f300"  # noqa: E501
                    )
                ),
                callee_12: Account(
                    code=bytes.fromhex(
                        "60068060366101003961020052602180603c60003961022052615a17610200516101000160006000f5610240526102405160015500fe60ff600055005a60005261ffff6000555a6000510360015561010061010060003960106000f300"  # noqa: E501
                    )
                ),
                callee_13: Account(
                    code=bytes.fromhex(
                        "60138060446101003961020052600f80605760003961022052610200516101000160006000f06102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a600051036001550061010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_14: Account(
                    code=bytes.fromhex(
                        "60138060476101003961020052600f80605a60003961022052615a17610200516101000160006000f56102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a600051036001550061010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_15: Account(
                    code=bytes.fromhex(
                        "60138060446101003961020052602180605760003961022052610200516101000160006000f06102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a60005103600255005a60005261ffff6000555a6000510360015561010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_16: Account(
                    code=bytes.fromhex(
                        "60138060476101003961020052602180605a60003961022052615a17610200516101000160006000f56102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a60005103600255005a60005261ffff6000555a6000510360015561010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_17: Account(
                    code=bytes.fromhex(
                        "6000600060006000600061f1265af1506000600060006000600061f1265af100"  # noqa: E501
                    )
                ),
                callee_18: Account(
                    storage={0: 2, 1: 20003, 2: 107, 24743: 57005},
                    code=bytes.fromhex(
                        "5a600052600260005560115a60005103036000526000516001555a6000526160a75460205260105a600051030360005260005160025500"  # noqa: E501
                    ),
                ),
                callee_19: Account(
                    code=bytes.fromhex(
                        "63dead60a760005561600d60005260206000f300"
                    )
                ),
                callee_20: Account(
                    storage={0: 2989}, code=bytes.fromhex("61600d60005500")
                ),
                callee_21: Account(
                    storage={0: 2989, 24743: 57005},
                    code=bytes.fromhex("6160a75460005261600d60005500"),
                ),
                callee_22: Account(
                    code=bytes.fromhex(
                        "5a6000526160a76000555a60005103600052600060015414602457600051600255602b565b6000516001555b00"  # noqa: E501
                    )
                ),
                callee_23: Account(code=bytes.fromhex("61dead6000556000ff00")),
                callee_24: Account(
                    storage={0: 0xDEAD0060A7},
                    code=bytes.fromhex("600054506000ff00"),
                ),
                callee_25: Account(
                    storage={24743: 57005},
                    code=bytes.fromhex(
                        "5a6000526160a75460205260135a600051030360005260206000f300"  # noqa: E501
                    ),
                ),
                contract: Account(
                    code=bytes.fromhex(
                        "60406000600060006000600435611000015af15060005160005560205160015500"  # noqa: E501
                    )
                ),
            },
        },
        {
            "indexes": {"data": 1, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex("600060006000600061c0575af400")
                ),
                callee_1: Account(
                    code=bytes.fromhex("6000600060006000600061c0575af100")
                ),
                callee_2: Account(
                    code=bytes.fromhex("6000600060006000600061c0575af200")
                ),
                callee_3: Account(
                    code=bytes.fromhex(
                        "602060006000600063ead0c0575afa5060005160005500"
                    )
                ),
                callee_4: Account(
                    storage={24743: 48879},
                    code=bytes.fromhex(
                        "5a600052600260005560115a60005103036000525a6020526160a754604052601a5a602051030360205260406000fd00"  # noqa: E501
                    ),
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "5a6000526000600060006000600063dead01115af150617fe85a600051030360005500"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "5a6000526000600060006000600063dead01125af150617fe85a600051030360005500"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "610bad600052602060006000600061f1135afa5060005160005500"  # noqa: E501
                    ),
                ),
                callee_8: Account(
                    code=bytes.fromhex("6020600060006000600061f114610b65f100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6020600060006000600061f115611800f100")
                ),
                callee_10: Account(
                    storage={0: 15, 24743: 57005},
                    code=bytes.fromhex(
                        "600054505a600052600261beef5560115a60005103036000525a6020526160a75460a05260235a60205103036020525a60405261beef60005461f000015560785a60405103036040525a60605260005461f010015450607a5a60605103036060526000516000546101000155602051600054610200015560405160005461030001556060516000546104000155600060005411609b57600060b4565b600160005403600055600060006000600060006110165af15b00"  # noqa: E501
                    ),
                ),
                callee_11: Account(
                    code=bytes.fromhex(
                        "60068060336101003961020052602180603960003961022052610200516101000160006000f0610240526102405160015500fe60ff600055005a60005261ffff6000555a6000510360015561010061010060003960106000f300"  # noqa: E501
                    )
                ),
                callee_12: Account(
                    code=bytes.fromhex(
                        "60068060366101003961020052602180603c60003961022052615a17610200516101000160006000f5610240526102405160015500fe60ff600055005a60005261ffff6000555a6000510360015561010061010060003960106000f300"  # noqa: E501
                    )
                ),
                callee_13: Account(
                    code=bytes.fromhex(
                        "60138060446101003961020052600f80605760003961022052610200516101000160006000f06102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a600051036001550061010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_14: Account(
                    code=bytes.fromhex(
                        "60138060476101003961020052600f80605a60003961022052615a17610200516101000160006000f56102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a600051036001550061010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_15: Account(
                    code=bytes.fromhex(
                        "60138060446101003961020052602180605760003961022052610200516101000160006000f06102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a60005103600255005a60005261ffff6000555a6000510360015561010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_16: Account(
                    code=bytes.fromhex(
                        "60138060476101003961020052602180605a60003961022052615a17610200516101000160006000f56102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a60005103600255005a60005261ffff6000555a6000510360015561010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_17: Account(
                    code=bytes.fromhex(
                        "6000600060006000600061f1265af1506000600060006000600061f1265af100"  # noqa: E501
                    )
                ),
                callee_18: Account(
                    storage={0: 2, 1: 22103, 2: 2107, 24743: 57005},
                    code=bytes.fromhex(
                        "5a600052600260005560115a60005103036000526000516001555a6000526160a75460205260105a600051030360005260005160025500"  # noqa: E501
                    ),
                ),
                callee_19: Account(
                    code=bytes.fromhex(
                        "63dead60a760005561600d60005260206000f300"
                    )
                ),
                callee_20: Account(
                    storage={0: 2989}, code=bytes.fromhex("61600d60005500")
                ),
                callee_21: Account(
                    storage={0: 2989, 24743: 57005},
                    code=bytes.fromhex("6160a75460005261600d60005500"),
                ),
                callee_22: Account(
                    code=bytes.fromhex(
                        "5a6000526160a76000555a60005103600052600060015414602457600051600255602b565b6000516001555b00"  # noqa: E501
                    )
                ),
                callee_23: Account(code=bytes.fromhex("61dead6000556000ff00")),
                callee_24: Account(
                    storage={0: 0xDEAD0060A7},
                    code=bytes.fromhex("600054506000ff00"),
                ),
                callee_25: Account(
                    storage={24743: 57005},
                    code=bytes.fromhex(
                        "5a6000526160a75460205260135a600051030360005260206000f300"  # noqa: E501
                    ),
                ),
                contract: Account(
                    code=bytes.fromhex(
                        "60406000600060006000600435611000015af15060005160005560205160015500"  # noqa: E501
                    )
                ),
            },
        },
        {
            "indexes": {"data": 2, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex("600060006000600061c0575af400")
                ),
                callee_1: Account(
                    code=bytes.fromhex("6000600060006000600061c0575af100")
                ),
                callee_2: Account(
                    code=bytes.fromhex("6000600060006000600061c0575af200")
                ),
                callee_3: Account(
                    code=bytes.fromhex(
                        "602060006000600063ead0c0575afa5060005160005500"
                    )
                ),
                callee_4: Account(
                    storage={24743: 48879},
                    code=bytes.fromhex(
                        "5a600052600260005560115a60005103036000525a6020526160a754604052601a5a602051030360205260406000fd00"  # noqa: E501
                    ),
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "5a6000526000600060006000600063dead01115af150617fe85a600051030360005500"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "5a6000526000600060006000600063dead01125af150617fe85a600051030360005500"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "610bad600052602060006000600061f1135afa5060005160005500"  # noqa: E501
                    ),
                ),
                callee_8: Account(
                    code=bytes.fromhex("6020600060006000600061f114610b65f100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6020600060006000600061f115611800f100")
                ),
                callee_10: Account(
                    storage={0: 15, 24743: 57005},
                    code=bytes.fromhex(
                        "600054505a600052600261beef5560115a60005103036000525a6020526160a75460a05260235a60205103036020525a60405261beef60005461f000015560785a60405103036040525a60605260005461f010015450607a5a60605103036060526000516000546101000155602051600054610200015560405160005461030001556060516000546104000155600060005411609b57600060b4565b600160005403600055600060006000600060006110165af15b00"  # noqa: E501
                    ),
                ),
                callee_11: Account(
                    code=bytes.fromhex(
                        "60068060336101003961020052602180603960003961022052610200516101000160006000f0610240526102405160015500fe60ff600055005a60005261ffff6000555a6000510360015561010061010060003960106000f300"  # noqa: E501
                    )
                ),
                callee_12: Account(
                    code=bytes.fromhex(
                        "60068060366101003961020052602180603c60003961022052615a17610200516101000160006000f5610240526102405160015500fe60ff600055005a60005261ffff6000555a6000510360015561010061010060003960106000f300"  # noqa: E501
                    )
                ),
                callee_13: Account(
                    code=bytes.fromhex(
                        "60138060446101003961020052600f80605760003961022052610200516101000160006000f06102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a600051036001550061010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_14: Account(
                    storage={1: 0x530508498D2AA75D8E591612809FEC3D37A45615},
                    code=bytes.fromhex(
                        "60138060476101003961020052600f80605a60003961022052615a17610200516101000160006000f56102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a600051036001550061010061010060003960806000f300"  # noqa: E501
                    ),
                ),
                callee_15: Account(
                    code=bytes.fromhex(
                        "60138060446101003961020052602180605760003961022052610200516101000160006000f06102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a60005103600255005a60005261ffff6000555a6000510360015561010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_16: Account(
                    code=bytes.fromhex(
                        "60138060476101003961020052602180605a60003961022052615a17610200516101000160006000f56102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a60005103600255005a60005261ffff6000555a6000510360015561010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_17: Account(
                    code=bytes.fromhex(
                        "6000600060006000600061f1265af1506000600060006000600061f1265af100"  # noqa: E501
                    )
                ),
                callee_18: Account(
                    storage={24743: 57005},
                    code=bytes.fromhex(
                        "5a600052600260005560115a60005103036000526000516001555a6000526160a75460205260105a600051030360005260005160025500"  # noqa: E501
                    ),
                ),
                callee_19: Account(
                    code=bytes.fromhex(
                        "63dead60a760005561600d60005260206000f300"
                    )
                ),
                callee_20: Account(
                    storage={0: 2989}, code=bytes.fromhex("61600d60005500")
                ),
                callee_21: Account(
                    storage={0: 2989, 24743: 57005},
                    code=bytes.fromhex("6160a75460005261600d60005500"),
                ),
                callee_22: Account(
                    code=bytes.fromhex(
                        "5a6000526160a76000555a60005103600052600060015414602457600051600255602b565b6000516001555b00"  # noqa: E501
                    )
                ),
                callee_23: Account(code=bytes.fromhex("61dead6000556000ff00")),
                callee_24: Account(
                    storage={0: 0xDEAD0060A7},
                    code=bytes.fromhex("600054506000ff00"),
                ),
                callee_25: Account(
                    storage={24743: 57005},
                    code=bytes.fromhex(
                        "5a6000526160a75460205260135a600051030360005260206000f300"  # noqa: E501
                    ),
                ),
                Address("0x530508498d2aa75d8e591612809fec3d37a45615"): Account(
                    storage={0: 65535, 1: 22117},
                    code=bytes.fromhex(
                        "5a60005261ffff6000555a600051036001550000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                    ),
                ),
                contract: Account(
                    code=bytes.fromhex(
                        "60406000600060006000600435611000015af15060005160005560205160015500"  # noqa: E501
                    )
                ),
            },
        },
        {
            "indexes": {"data": 3, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex("600060006000600061c0575af400")
                ),
                callee_1: Account(
                    code=bytes.fromhex("6000600060006000600061c0575af100")
                ),
                callee_2: Account(
                    code=bytes.fromhex("6000600060006000600061c0575af200")
                ),
                callee_3: Account(
                    code=bytes.fromhex(
                        "602060006000600063ead0c0575afa5060005160005500"
                    )
                ),
                callee_4: Account(
                    storage={24743: 48879},
                    code=bytes.fromhex(
                        "5a600052600260005560115a60005103036000525a6020526160a754604052601a5a602051030360205260406000fd00"  # noqa: E501
                    ),
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "5a6000526000600060006000600063dead01115af150617fe85a600051030360005500"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "5a6000526000600060006000600063dead01125af150617fe85a600051030360005500"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "610bad600052602060006000600061f1135afa5060005160005500"  # noqa: E501
                    ),
                ),
                callee_8: Account(
                    code=bytes.fromhex("6020600060006000600061f114610b65f100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6020600060006000600061f115611800f100")
                ),
                callee_10: Account(
                    storage={0: 15, 24743: 57005},
                    code=bytes.fromhex(
                        "600054505a600052600261beef5560115a60005103036000525a6020526160a75460a05260235a60205103036020525a60405261beef60005461f000015560785a60405103036040525a60605260005461f010015450607a5a60605103036060526000516000546101000155602051600054610200015560405160005461030001556060516000546104000155600060005411609b57600060b4565b600160005403600055600060006000600060006110165af15b00"  # noqa: E501
                    ),
                ),
                callee_11: Account(
                    code=bytes.fromhex(
                        "60068060336101003961020052602180603960003961022052610200516101000160006000f0610240526102405160015500fe60ff600055005a60005261ffff6000555a6000510360015561010061010060003960106000f300"  # noqa: E501
                    )
                ),
                callee_12: Account(
                    code=bytes.fromhex(
                        "60068060366101003961020052602180603c60003961022052615a17610200516101000160006000f5610240526102405160015500fe60ff600055005a60005261ffff6000555a6000510360015561010061010060003960106000f300"  # noqa: E501
                    )
                ),
                callee_13: Account(
                    code=bytes.fromhex(
                        "60138060446101003961020052600f80605760003961022052610200516101000160006000f06102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a600051036001550061010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_14: Account(
                    storage={1: 0x530508498D2AA75D8E591612809FEC3D37A45615},
                    code=bytes.fromhex(
                        "60138060476101003961020052600f80605a60003961022052615a17610200516101000160006000f56102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a600051036001550061010061010060003960806000f300"  # noqa: E501
                    ),
                ),
                callee_15: Account(
                    code=bytes.fromhex(
                        "60138060446101003961020052602180605760003961022052610200516101000160006000f06102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a60005103600255005a60005261ffff6000555a6000510360015561010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_16: Account(
                    code=bytes.fromhex(
                        "60138060476101003961020052602180605a60003961022052615a17610200516101000160006000f56102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a60005103600255005a60005261ffff6000555a6000510360015561010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_17: Account(
                    code=bytes.fromhex(
                        "6000600060006000600061f1265af1506000600060006000600061f1265af100"  # noqa: E501
                    )
                ),
                callee_18: Account(
                    storage={24743: 57005},
                    code=bytes.fromhex(
                        "5a600052600260005560115a60005103036000526000516001555a6000526160a75460205260105a600051030360005260005160025500"  # noqa: E501
                    ),
                ),
                callee_19: Account(
                    code=bytes.fromhex(
                        "63dead60a760005561600d60005260206000f300"
                    )
                ),
                callee_20: Account(
                    storage={0: 2989}, code=bytes.fromhex("61600d60005500")
                ),
                callee_21: Account(
                    storage={0: 2989, 24743: 57005},
                    code=bytes.fromhex("6160a75460005261600d60005500"),
                ),
                callee_22: Account(
                    code=bytes.fromhex(
                        "5a6000526160a76000555a60005103600052600060015414602457600051600255602b565b6000516001555b00"  # noqa: E501
                    )
                ),
                callee_23: Account(code=bytes.fromhex("61dead6000556000ff00")),
                callee_24: Account(
                    storage={0: 0xDEAD0060A7},
                    code=bytes.fromhex("600054506000ff00"),
                ),
                callee_25: Account(
                    storage={24743: 57005},
                    code=bytes.fromhex(
                        "5a6000526160a75460205260135a600051030360005260206000f300"  # noqa: E501
                    ),
                ),
                Address("0x530508498d2aa75d8e591612809fec3d37a45615"): Account(
                    storage={0: 65535, 1: 20017},
                    code=bytes.fromhex(
                        "5a60005261ffff6000555a600051036001550000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                    ),
                ),
                contract: Account(
                    code=bytes.fromhex(
                        "60406000600060006000600435611000015af15060005160005560205160015500"  # noqa: E501
                    )
                ),
            },
        },
        {
            "indexes": {"data": 4, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex("600060006000600061c0575af400")
                ),
                callee_1: Account(
                    code=bytes.fromhex("6000600060006000600061c0575af100")
                ),
                callee_2: Account(
                    code=bytes.fromhex("6000600060006000600061c0575af200")
                ),
                callee_3: Account(
                    code=bytes.fromhex(
                        "602060006000600063ead0c0575afa5060005160005500"
                    )
                ),
                callee_4: Account(
                    storage={24743: 48879},
                    code=bytes.fromhex(
                        "5a600052600260005560115a60005103036000525a6020526160a754604052601a5a602051030360205260406000fd00"  # noqa: E501
                    ),
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "5a6000526000600060006000600063dead01115af150617fe85a600051030360005500"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "5a6000526000600060006000600063dead01125af150617fe85a600051030360005500"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "610bad600052602060006000600061f1135afa5060005160005500"  # noqa: E501
                    ),
                ),
                callee_8: Account(
                    code=bytes.fromhex("6020600060006000600061f114610b65f100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6020600060006000600061f115611800f100")
                ),
                callee_10: Account(
                    storage={0: 15, 24743: 57005},
                    code=bytes.fromhex(
                        "600054505a600052600261beef5560115a60005103036000525a6020526160a75460a05260235a60205103036020525a60405261beef60005461f000015560785a60405103036040525a60605260005461f010015450607a5a60605103036060526000516000546101000155602051600054610200015560405160005461030001556060516000546104000155600060005411609b57600060b4565b600160005403600055600060006000600060006110165af15b00"  # noqa: E501
                    ),
                ),
                callee_11: Account(
                    code=bytes.fromhex(
                        "60068060336101003961020052602180603960003961022052610200516101000160006000f0610240526102405160015500fe60ff600055005a60005261ffff6000555a6000510360015561010061010060003960106000f300"  # noqa: E501
                    )
                ),
                callee_12: Account(
                    code=bytes.fromhex(
                        "60068060366101003961020052602180603c60003961022052615a17610200516101000160006000f5610240526102405160015500fe60ff600055005a60005261ffff6000555a6000510360015561010061010060003960106000f300"  # noqa: E501
                    )
                ),
                callee_13: Account(
                    storage={1: 0x58FD03A2D731B2FB751E4A0F593D373EE77D39E6},
                    code=bytes.fromhex(
                        "60138060446101003961020052600f80605760003961022052610200516101000160006000f06102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a600051036001550061010061010060003960806000f300"  # noqa: E501
                    ),
                ),
                callee_14: Account(
                    code=bytes.fromhex(
                        "60138060476101003961020052600f80605a60003961022052615a17610200516101000160006000f56102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a600051036001550061010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_15: Account(
                    code=bytes.fromhex(
                        "60138060446101003961020052602180605760003961022052610200516101000160006000f06102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a60005103600255005a60005261ffff6000555a6000510360015561010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_16: Account(
                    code=bytes.fromhex(
                        "60138060476101003961020052602180605a60003961022052615a17610200516101000160006000f56102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a60005103600255005a60005261ffff6000555a6000510360015561010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_17: Account(
                    code=bytes.fromhex(
                        "6000600060006000600061f1265af1506000600060006000600061f1265af100"  # noqa: E501
                    )
                ),
                callee_18: Account(
                    storage={24743: 57005},
                    code=bytes.fromhex(
                        "5a600052600260005560115a60005103036000526000516001555a6000526160a75460205260105a600051030360005260005160025500"  # noqa: E501
                    ),
                ),
                callee_19: Account(
                    code=bytes.fromhex(
                        "63dead60a760005561600d60005260206000f300"
                    )
                ),
                callee_20: Account(
                    storage={0: 2989}, code=bytes.fromhex("61600d60005500")
                ),
                callee_21: Account(
                    storage={0: 2989, 24743: 57005},
                    code=bytes.fromhex("6160a75460005261600d60005500"),
                ),
                callee_22: Account(
                    code=bytes.fromhex(
                        "5a6000526160a76000555a60005103600052600060015414602457600051600255602b565b6000516001555b00"  # noqa: E501
                    )
                ),
                callee_23: Account(code=bytes.fromhex("61dead6000556000ff00")),
                callee_24: Account(
                    storage={0: 0xDEAD0060A7},
                    code=bytes.fromhex("600054506000ff00"),
                ),
                callee_25: Account(
                    storage={24743: 57005},
                    code=bytes.fromhex(
                        "5a6000526160a75460205260135a600051030360005260206000f300"  # noqa: E501
                    ),
                ),
                Address("0x58fd03a2d731b2fb751e4a0f593d373ee77d39e6"): Account(
                    storage={0: 65535, 1: 22117},
                    code=bytes.fromhex(
                        "5a60005261ffff6000555a600051036001550000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                    ),
                ),
                contract: Account(
                    code=bytes.fromhex(
                        "60406000600060006000600435611000015af15060005160005560205160015500"  # noqa: E501
                    )
                ),
            },
        },
        {
            "indexes": {"data": 5, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex("600060006000600061c0575af400")
                ),
                callee_1: Account(
                    code=bytes.fromhex("6000600060006000600061c0575af100")
                ),
                callee_2: Account(
                    code=bytes.fromhex("6000600060006000600061c0575af200")
                ),
                callee_3: Account(
                    code=bytes.fromhex(
                        "602060006000600063ead0c0575afa5060005160005500"
                    )
                ),
                callee_4: Account(
                    storage={24743: 48879},
                    code=bytes.fromhex(
                        "5a600052600260005560115a60005103036000525a6020526160a754604052601a5a602051030360205260406000fd00"  # noqa: E501
                    ),
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "5a6000526000600060006000600063dead01115af150617fe85a600051030360005500"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "5a6000526000600060006000600063dead01125af150617fe85a600051030360005500"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "610bad600052602060006000600061f1135afa5060005160005500"  # noqa: E501
                    ),
                ),
                callee_8: Account(
                    code=bytes.fromhex("6020600060006000600061f114610b65f100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6020600060006000600061f115611800f100")
                ),
                callee_10: Account(
                    storage={0: 15, 24743: 57005},
                    code=bytes.fromhex(
                        "600054505a600052600261beef5560115a60005103036000525a6020526160a75460a05260235a60205103036020525a60405261beef60005461f000015560785a60405103036040525a60605260005461f010015450607a5a60605103036060526000516000546101000155602051600054610200015560405160005461030001556060516000546104000155600060005411609b57600060b4565b600160005403600055600060006000600060006110165af15b00"  # noqa: E501
                    ),
                ),
                callee_11: Account(
                    code=bytes.fromhex(
                        "60068060336101003961020052602180603960003961022052610200516101000160006000f0610240526102405160015500fe60ff600055005a60005261ffff6000555a6000510360015561010061010060003960106000f300"  # noqa: E501
                    )
                ),
                callee_12: Account(
                    code=bytes.fromhex(
                        "60068060366101003961020052602180603c60003961022052615a17610200516101000160006000f5610240526102405160015500fe60ff600055005a60005261ffff6000555a6000510360015561010061010060003960106000f300"  # noqa: E501
                    )
                ),
                callee_13: Account(
                    storage={1: 0x58FD03A2D731B2FB751E4A0F593D373EE77D39E6},
                    code=bytes.fromhex(
                        "60138060446101003961020052600f80605760003961022052610200516101000160006000f06102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a600051036001550061010061010060003960806000f300"  # noqa: E501
                    ),
                ),
                callee_14: Account(
                    code=bytes.fromhex(
                        "60138060476101003961020052600f80605a60003961022052615a17610200516101000160006000f56102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a600051036001550061010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_15: Account(
                    code=bytes.fromhex(
                        "60138060446101003961020052602180605760003961022052610200516101000160006000f06102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a60005103600255005a60005261ffff6000555a6000510360015561010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_16: Account(
                    code=bytes.fromhex(
                        "60138060476101003961020052602180605a60003961022052615a17610200516101000160006000f56102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a60005103600255005a60005261ffff6000555a6000510360015561010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_17: Account(
                    code=bytes.fromhex(
                        "6000600060006000600061f1265af1506000600060006000600061f1265af100"  # noqa: E501
                    )
                ),
                callee_18: Account(
                    storage={24743: 57005},
                    code=bytes.fromhex(
                        "5a600052600260005560115a60005103036000526000516001555a6000526160a75460205260105a600051030360005260005160025500"  # noqa: E501
                    ),
                ),
                callee_19: Account(
                    code=bytes.fromhex(
                        "63dead60a760005561600d60005260206000f300"
                    )
                ),
                callee_20: Account(
                    storage={0: 2989}, code=bytes.fromhex("61600d60005500")
                ),
                callee_21: Account(
                    storage={0: 2989, 24743: 57005},
                    code=bytes.fromhex("6160a75460005261600d60005500"),
                ),
                callee_22: Account(
                    code=bytes.fromhex(
                        "5a6000526160a76000555a60005103600052600060015414602457600051600255602b565b6000516001555b00"  # noqa: E501
                    )
                ),
                callee_23: Account(code=bytes.fromhex("61dead6000556000ff00")),
                callee_24: Account(
                    storage={0: 0xDEAD0060A7},
                    code=bytes.fromhex("600054506000ff00"),
                ),
                callee_25: Account(
                    storage={24743: 57005},
                    code=bytes.fromhex(
                        "5a6000526160a75460205260135a600051030360005260206000f300"  # noqa: E501
                    ),
                ),
                Address("0x58fd03a2d731b2fb751e4a0f593d373ee77d39e6"): Account(
                    storage={0: 65535, 1: 20017},
                    code=bytes.fromhex(
                        "5a60005261ffff6000555a600051036001550000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                    ),
                ),
                contract: Account(
                    code=bytes.fromhex(
                        "60406000600060006000600435611000015af15060005160005560205160015500"  # noqa: E501
                    )
                ),
            },
        },
        {
            "indexes": {"data": 6, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex("600060006000600061c0575af400")
                ),
                callee_1: Account(
                    code=bytes.fromhex("6000600060006000600061c0575af100")
                ),
                callee_2: Account(
                    code=bytes.fromhex("6000600060006000600061c0575af200")
                ),
                callee_3: Account(
                    code=bytes.fromhex(
                        "602060006000600063ead0c0575afa5060005160005500"
                    )
                ),
                callee_4: Account(
                    storage={24743: 48879},
                    code=bytes.fromhex(
                        "5a600052600260005560115a60005103036000525a6020526160a754604052601a5a602051030360205260406000fd00"  # noqa: E501
                    ),
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "5a6000526000600060006000600063dead01115af150617fe85a600051030360005500"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    storage={0: 4600},
                    code=bytes.fromhex(
                        "5a6000526000600060006000600063dead01125af150617fe85a600051030360005500"  # noqa: E501
                    ),
                ),
                callee_7: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "610bad600052602060006000600061f1135afa5060005160005500"  # noqa: E501
                    ),
                ),
                callee_8: Account(
                    code=bytes.fromhex("6020600060006000600061f114610b65f100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6020600060006000600061f115611800f100")
                ),
                callee_10: Account(
                    storage={0: 15, 24743: 57005},
                    code=bytes.fromhex(
                        "600054505a600052600261beef5560115a60005103036000525a6020526160a75460a05260235a60205103036020525a60405261beef60005461f000015560785a60405103036040525a60605260005461f010015450607a5a60605103036060526000516000546101000155602051600054610200015560405160005461030001556060516000546104000155600060005411609b57600060b4565b600160005403600055600060006000600060006110165af15b00"  # noqa: E501
                    ),
                ),
                callee_11: Account(
                    code=bytes.fromhex(
                        "60068060336101003961020052602180603960003961022052610200516101000160006000f0610240526102405160015500fe60ff600055005a60005261ffff6000555a6000510360015561010061010060003960106000f300"  # noqa: E501
                    )
                ),
                callee_12: Account(
                    code=bytes.fromhex(
                        "60068060366101003961020052602180603c60003961022052615a17610200516101000160006000f5610240526102405160015500fe60ff600055005a60005261ffff6000555a6000510360015561010061010060003960106000f300"  # noqa: E501
                    )
                ),
                callee_13: Account(
                    code=bytes.fromhex(
                        "60138060446101003961020052600f80605760003961022052610200516101000160006000f06102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a600051036001550061010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_14: Account(
                    code=bytes.fromhex(
                        "60138060476101003961020052600f80605a60003961022052615a17610200516101000160006000f56102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a600051036001550061010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_15: Account(
                    code=bytes.fromhex(
                        "60138060446101003961020052602180605760003961022052610200516101000160006000f06102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a60005103600255005a60005261ffff6000555a6000510360015561010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_16: Account(
                    code=bytes.fromhex(
                        "60138060476101003961020052602180605a60003961022052615a17610200516101000160006000f56102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a60005103600255005a60005261ffff6000555a6000510360015561010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_17: Account(
                    code=bytes.fromhex(
                        "6000600060006000600061f1265af1506000600060006000600061f1265af100"  # noqa: E501
                    )
                ),
                callee_18: Account(
                    storage={24743: 57005},
                    code=bytes.fromhex(
                        "5a600052600260005560115a60005103036000526000516001555a6000526160a75460205260105a600051030360005260005160025500"  # noqa: E501
                    ),
                ),
                callee_19: Account(
                    code=bytes.fromhex(
                        "63dead60a760005561600d60005260206000f300"
                    )
                ),
                callee_20: Account(
                    storage={0: 2989}, code=bytes.fromhex("61600d60005500")
                ),
                callee_21: Account(
                    storage={0: 2989, 24743: 57005},
                    code=bytes.fromhex("6160a75460005261600d60005500"),
                ),
                callee_22: Account(
                    code=bytes.fromhex(
                        "5a6000526160a76000555a60005103600052600060015414602457600051600255602b565b6000516001555b00"  # noqa: E501
                    )
                ),
                callee_23: Account(code=bytes.fromhex("61dead6000556000ff00")),
                callee_24: Account(
                    storage={0: 0xDEAD0060A7},
                    code=bytes.fromhex("600054506000ff00"),
                ),
                callee_25: Account(
                    storage={24743: 57005},
                    code=bytes.fromhex(
                        "5a6000526160a75460205260135a600051030360005260206000f300"  # noqa: E501
                    ),
                ),
                contract: Account(
                    code=bytes.fromhex(
                        "60406000600060006000600435611000015af15060005160005560205160015500"  # noqa: E501
                    )
                ),
            },
        },
        {
            "indexes": {"data": 7, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex("600060006000600061c0575af400")
                ),
                callee_1: Account(
                    code=bytes.fromhex("6000600060006000600061c0575af100")
                ),
                callee_2: Account(
                    code=bytes.fromhex("6000600060006000600061c0575af200")
                ),
                callee_3: Account(
                    code=bytes.fromhex(
                        "602060006000600063ead0c0575afa5060005160005500"
                    )
                ),
                callee_4: Account(
                    storage={24743: 48879},
                    code=bytes.fromhex(
                        "5a600052600260005560115a60005103036000525a6020526160a754604052601a5a602051030360205260406000fd00"  # noqa: E501
                    ),
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "5a6000526000600060006000600063dead01115af150617fe85a600051030360005500"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    storage={0: 100},
                    code=bytes.fromhex(
                        "5a6000526000600060006000600063dead01125af150617fe85a600051030360005500"  # noqa: E501
                    ),
                ),
                callee_7: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "610bad600052602060006000600061f1135afa5060005160005500"  # noqa: E501
                    ),
                ),
                callee_8: Account(
                    code=bytes.fromhex("6020600060006000600061f114610b65f100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6020600060006000600061f115611800f100")
                ),
                callee_10: Account(
                    storage={0: 15, 24743: 57005},
                    code=bytes.fromhex(
                        "600054505a600052600261beef5560115a60005103036000525a6020526160a75460a05260235a60205103036020525a60405261beef60005461f000015560785a60405103036040525a60605260005461f010015450607a5a60605103036060526000516000546101000155602051600054610200015560405160005461030001556060516000546104000155600060005411609b57600060b4565b600160005403600055600060006000600060006110165af15b00"  # noqa: E501
                    ),
                ),
                callee_11: Account(
                    code=bytes.fromhex(
                        "60068060336101003961020052602180603960003961022052610200516101000160006000f0610240526102405160015500fe60ff600055005a60005261ffff6000555a6000510360015561010061010060003960106000f300"  # noqa: E501
                    )
                ),
                callee_12: Account(
                    code=bytes.fromhex(
                        "60068060366101003961020052602180603c60003961022052615a17610200516101000160006000f5610240526102405160015500fe60ff600055005a60005261ffff6000555a6000510360015561010061010060003960106000f300"  # noqa: E501
                    )
                ),
                callee_13: Account(
                    code=bytes.fromhex(
                        "60138060446101003961020052600f80605760003961022052610200516101000160006000f06102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a600051036001550061010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_14: Account(
                    code=bytes.fromhex(
                        "60138060476101003961020052600f80605a60003961022052615a17610200516101000160006000f56102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a600051036001550061010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_15: Account(
                    code=bytes.fromhex(
                        "60138060446101003961020052602180605760003961022052610200516101000160006000f06102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a60005103600255005a60005261ffff6000555a6000510360015561010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_16: Account(
                    code=bytes.fromhex(
                        "60138060476101003961020052602180605a60003961022052615a17610200516101000160006000f56102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a60005103600255005a60005261ffff6000555a6000510360015561010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_17: Account(
                    code=bytes.fromhex(
                        "6000600060006000600061f1265af1506000600060006000600061f1265af100"  # noqa: E501
                    )
                ),
                callee_18: Account(
                    storage={24743: 57005},
                    code=bytes.fromhex(
                        "5a600052600260005560115a60005103036000526000516001555a6000526160a75460205260105a600051030360005260005160025500"  # noqa: E501
                    ),
                ),
                callee_19: Account(
                    code=bytes.fromhex(
                        "63dead60a760005561600d60005260206000f300"
                    )
                ),
                callee_20: Account(
                    storage={0: 2989}, code=bytes.fromhex("61600d60005500")
                ),
                callee_21: Account(
                    storage={0: 2989, 24743: 57005},
                    code=bytes.fromhex("6160a75460005261600d60005500"),
                ),
                callee_22: Account(
                    code=bytes.fromhex(
                        "5a6000526160a76000555a60005103600052600060015414602457600051600255602b565b6000516001555b00"  # noqa: E501
                    )
                ),
                callee_23: Account(code=bytes.fromhex("61dead6000556000ff00")),
                callee_24: Account(
                    storage={0: 0xDEAD0060A7},
                    code=bytes.fromhex("600054506000ff00"),
                ),
                callee_25: Account(
                    storage={24743: 57005},
                    code=bytes.fromhex(
                        "5a6000526160a75460205260135a600051030360005260206000f300"  # noqa: E501
                    ),
                ),
                contract: Account(
                    code=bytes.fromhex(
                        "60406000600060006000600435611000015af15060005160005560205160015500"  # noqa: E501
                    )
                ),
            },
        },
        {
            "indexes": {"data": 8, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex("600060006000600061c0575af400")
                ),
                callee_1: Account(
                    code=bytes.fromhex("6000600060006000600061c0575af100")
                ),
                callee_2: Account(
                    code=bytes.fromhex("6000600060006000600061c0575af200")
                ),
                callee_3: Account(
                    code=bytes.fromhex(
                        "602060006000600063ead0c0575afa5060005160005500"
                    )
                ),
                callee_4: Account(
                    storage={24743: 48879},
                    code=bytes.fromhex(
                        "5a600052600260005560115a60005103036000525a6020526160a754604052601a5a602051030360205260406000fd00"  # noqa: E501
                    ),
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "5a6000526000600060006000600063dead01115af150617fe85a600051030360005500"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "5a6000526000600060006000600063dead01125af150617fe85a600051030360005500"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "610bad600052602060006000600061f1135afa5060005160005500"  # noqa: E501
                    ),
                ),
                callee_8: Account(
                    code=bytes.fromhex("6020600060006000600061f114610b65f100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6020600060006000600061f115611800f100")
                ),
                callee_10: Account(
                    storage={0: 15, 24743: 57005},
                    code=bytes.fromhex(
                        "600054505a600052600261beef5560115a60005103036000525a6020526160a75460a05260235a60205103036020525a60405261beef60005461f000015560785a60405103036040525a60605260005461f010015450607a5a60605103036060526000516000546101000155602051600054610200015560405160005461030001556060516000546104000155600060005411609b57600060b4565b600160005403600055600060006000600060006110165af15b00"  # noqa: E501
                    ),
                ),
                callee_11: Account(
                    code=bytes.fromhex(
                        "60068060336101003961020052602180603960003961022052610200516101000160006000f0610240526102405160015500fe60ff600055005a60005261ffff6000555a6000510360015561010061010060003960106000f300"  # noqa: E501
                    )
                ),
                callee_12: Account(
                    code=bytes.fromhex(
                        "60068060366101003961020052602180603c60003961022052615a17610200516101000160006000f5610240526102405160015500fe60ff600055005a60005261ffff6000555a6000510360015561010061010060003960106000f300"  # noqa: E501
                    )
                ),
                callee_13: Account(
                    code=bytes.fromhex(
                        "60138060446101003961020052600f80605760003961022052610200516101000160006000f06102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a600051036001550061010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_14: Account(
                    code=bytes.fromhex(
                        "60138060476101003961020052600f80605a60003961022052615a17610200516101000160006000f56102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a600051036001550061010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_15: Account(
                    code=bytes.fromhex(
                        "60138060446101003961020052602180605760003961022052610200516101000160006000f06102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a60005103600255005a60005261ffff6000555a6000510360015561010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_16: Account(
                    code=bytes.fromhex(
                        "60138060476101003961020052602180605a60003961022052615a17610200516101000160006000f56102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a60005103600255005a60005261ffff6000555a6000510360015561010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_17: Account(
                    code=bytes.fromhex(
                        "6000600060006000600061f1265af1506000600060006000600061f1265af100"  # noqa: E501
                    )
                ),
                callee_18: Account(
                    storage={24743: 57005},
                    code=bytes.fromhex(
                        "5a600052600260005560115a60005103036000526000516001555a6000526160a75460205260105a600051030360005260005160025500"  # noqa: E501
                    ),
                ),
                callee_19: Account(
                    code=bytes.fromhex(
                        "63dead60a760005561600d60005260206000f300"
                    )
                ),
                callee_20: Account(
                    storage={0: 2989}, code=bytes.fromhex("61600d60005500")
                ),
                callee_21: Account(
                    storage={0: 2989, 24743: 57005},
                    code=bytes.fromhex("6160a75460005261600d60005500"),
                ),
                callee_22: Account(
                    code=bytes.fromhex(
                        "5a6000526160a76000555a60005103600052600060015414602457600051600255602b565b6000516001555b00"  # noqa: E501
                    )
                ),
                callee_23: Account(code=bytes.fromhex("61dead6000556000ff00")),
                callee_24: Account(
                    storage={0: 0xDEAD0060A7},
                    code=bytes.fromhex("600054506000ff00"),
                ),
                callee_25: Account(
                    storage={24743: 57005},
                    code=bytes.fromhex(
                        "5a6000526160a75460205260135a600051030360005260206000f300"  # noqa: E501
                    ),
                ),
                contract: Account(
                    storage={0: 20003, 1: 100},
                    code=bytes.fromhex(
                        "60406000600060006000600435611000015af15060005160005560205160015500"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 9, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex("600060006000600061c0575af400")
                ),
                callee_1: Account(
                    code=bytes.fromhex("6000600060006000600061c0575af100")
                ),
                callee_2: Account(
                    code=bytes.fromhex("6000600060006000600061c0575af200")
                ),
                callee_3: Account(
                    code=bytes.fromhex(
                        "602060006000600063ead0c0575afa5060005160005500"
                    )
                ),
                callee_4: Account(
                    storage={24743: 48879},
                    code=bytes.fromhex(
                        "5a600052600260005560115a60005103036000525a6020526160a754604052601a5a602051030360205260406000fd00"  # noqa: E501
                    ),
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "5a6000526000600060006000600063dead01115af150617fe85a600051030360005500"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "5a6000526000600060006000600063dead01125af150617fe85a600051030360005500"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "610bad600052602060006000600061f1135afa5060005160005500"  # noqa: E501
                    ),
                ),
                callee_8: Account(
                    code=bytes.fromhex("6020600060006000600061f114610b65f100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6020600060006000600061f115611800f100")
                ),
                callee_10: Account(
                    storage={0: 15, 24743: 57005},
                    code=bytes.fromhex(
                        "600054505a600052600261beef5560115a60005103036000525a6020526160a75460a05260235a60205103036020525a60405261beef60005461f000015560785a60405103036040525a60605260005461f010015450607a5a60605103036060526000516000546101000155602051600054610200015560405160005461030001556060516000546104000155600060005411609b57600060b4565b600160005403600055600060006000600060006110165af15b00"  # noqa: E501
                    ),
                ),
                callee_11: Account(
                    code=bytes.fromhex(
                        "60068060336101003961020052602180603960003961022052610200516101000160006000f0610240526102405160015500fe60ff600055005a60005261ffff6000555a6000510360015561010061010060003960106000f300"  # noqa: E501
                    )
                ),
                callee_12: Account(
                    code=bytes.fromhex(
                        "60068060366101003961020052602180603c60003961022052615a17610200516101000160006000f5610240526102405160015500fe60ff600055005a60005261ffff6000555a6000510360015561010061010060003960106000f300"  # noqa: E501
                    )
                ),
                callee_13: Account(
                    code=bytes.fromhex(
                        "60138060446101003961020052600f80605760003961022052610200516101000160006000f06102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a600051036001550061010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_14: Account(
                    code=bytes.fromhex(
                        "60138060476101003961020052600f80605a60003961022052615a17610200516101000160006000f56102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a600051036001550061010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_15: Account(
                    code=bytes.fromhex(
                        "60138060446101003961020052602180605760003961022052610200516101000160006000f06102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a60005103600255005a60005261ffff6000555a6000510360015561010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_16: Account(
                    code=bytes.fromhex(
                        "60138060476101003961020052602180605a60003961022052615a17610200516101000160006000f56102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a60005103600255005a60005261ffff6000555a6000510360015561010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_17: Account(
                    code=bytes.fromhex(
                        "6000600060006000600061f1265af1506000600060006000600061f1265af100"  # noqa: E501
                    )
                ),
                callee_18: Account(
                    storage={24743: 57005},
                    code=bytes.fromhex(
                        "5a600052600260005560115a60005103036000526000516001555a6000526160a75460205260105a600051030360005260005160025500"  # noqa: E501
                    ),
                ),
                callee_19: Account(
                    code=bytes.fromhex(
                        "63dead60a760005561600d60005260206000f300"
                    )
                ),
                callee_20: Account(
                    storage={0: 2989}, code=bytes.fromhex("61600d60005500")
                ),
                callee_21: Account(
                    storage={0: 2989, 24743: 57005},
                    code=bytes.fromhex("6160a75460005261600d60005500"),
                ),
                callee_22: Account(
                    code=bytes.fromhex(
                        "5a6000526160a76000555a60005103600052600060015414602457600051600255602b565b6000516001555b00"  # noqa: E501
                    )
                ),
                callee_23: Account(code=bytes.fromhex("61dead6000556000ff00")),
                callee_24: Account(
                    storage={0: 0xDEAD0060A7},
                    code=bytes.fromhex("600054506000ff00"),
                ),
                callee_25: Account(
                    storage={24743: 57005},
                    code=bytes.fromhex(
                        "5a6000526160a75460205260135a600051030360005260206000f300"  # noqa: E501
                    ),
                ),
                contract: Account(
                    storage={0: 22103, 1: 2100},
                    code=bytes.fromhex(
                        "60406000600060006000600435611000015af15060005160005560205160015500"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 10, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex("600060006000600061c0575af400")
                ),
                callee_1: Account(
                    code=bytes.fromhex("6000600060006000600061c0575af100")
                ),
                callee_2: Account(
                    code=bytes.fromhex("6000600060006000600061c0575af200")
                ),
                callee_3: Account(
                    code=bytes.fromhex(
                        "602060006000600063ead0c0575afa5060005160005500"
                    )
                ),
                callee_4: Account(
                    storage={24743: 48879},
                    code=bytes.fromhex(
                        "5a600052600260005560115a60005103036000525a6020526160a754604052601a5a602051030360205260406000fd00"  # noqa: E501
                    ),
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "5a6000526000600060006000600063dead01115af150617fe85a600051030360005500"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "5a6000526000600060006000600063dead01125af150617fe85a600051030360005500"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "610bad600052602060006000600061f1135afa5060005160005500"  # noqa: E501
                    ),
                ),
                callee_8: Account(
                    code=bytes.fromhex("6020600060006000600061f114610b65f100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6020600060006000600061f115611800f100")
                ),
                callee_10: Account(
                    storage={0: 15, 24743: 57005},
                    code=bytes.fromhex(
                        "600054505a600052600261beef5560115a60005103036000525a6020526160a75460a05260235a60205103036020525a60405261beef60005461f000015560785a60405103036040525a60605260005461f010015450607a5a60605103036060526000516000546101000155602051600054610200015560405160005461030001556060516000546104000155600060005411609b57600060b4565b600160005403600055600060006000600060006110165af15b00"  # noqa: E501
                    ),
                ),
                callee_11: Account(
                    code=bytes.fromhex(
                        "60068060336101003961020052602180603960003961022052610200516101000160006000f0610240526102405160015500fe60ff600055005a60005261ffff6000555a6000510360015561010061010060003960106000f300"  # noqa: E501
                    )
                ),
                callee_12: Account(
                    code=bytes.fromhex(
                        "60068060366101003961020052602180603c60003961022052615a17610200516101000160006000f5610240526102405160015500fe60ff600055005a60005261ffff6000555a6000510360015561010061010060003960106000f300"  # noqa: E501
                    )
                ),
                callee_13: Account(
                    code=bytes.fromhex(
                        "60138060446101003961020052600f80605760003961022052610200516101000160006000f06102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a600051036001550061010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_14: Account(
                    code=bytes.fromhex(
                        "60138060476101003961020052600f80605a60003961022052615a17610200516101000160006000f56102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a600051036001550061010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_15: Account(
                    code=bytes.fromhex(
                        "60138060446101003961020052602180605760003961022052610200516101000160006000f06102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a60005103600255005a60005261ffff6000555a6000510360015561010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_16: Account(
                    code=bytes.fromhex(
                        "60138060476101003961020052602180605a60003961022052615a17610200516101000160006000f56102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a60005103600255005a60005261ffff6000555a6000510360015561010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_17: Account(
                    code=bytes.fromhex(
                        "6000600060006000600061f1265af1506000600060006000600061f1265af100"  # noqa: E501
                    )
                ),
                callee_18: Account(
                    storage={24743: 57005},
                    code=bytes.fromhex(
                        "5a600052600260005560115a60005103036000526000516001555a6000526160a75460205260105a600051030360005260005160025500"  # noqa: E501
                    ),
                ),
                callee_19: Account(
                    code=bytes.fromhex(
                        "63dead60a760005561600d60005260206000f300"
                    )
                ),
                callee_20: Account(
                    storage={0: 2989}, code=bytes.fromhex("61600d60005500")
                ),
                callee_21: Account(
                    storage={0: 2989, 24743: 57005},
                    code=bytes.fromhex("6160a75460005261600d60005500"),
                ),
                callee_22: Account(
                    storage={0: 24743, 1: 22117, 2: 117},
                    code=bytes.fromhex(
                        "5a6000526160a76000555a60005103600052600060015414602457600051600255602b565b6000516001555b00"  # noqa: E501
                    ),
                ),
                callee_23: Account(code=bytes.fromhex("61dead6000556000ff00")),
                callee_24: Account(
                    storage={0: 0xDEAD0060A7},
                    code=bytes.fromhex("600054506000ff00"),
                ),
                callee_25: Account(
                    storage={24743: 57005},
                    code=bytes.fromhex(
                        "5a6000526160a75460205260135a600051030360005260206000f300"  # noqa: E501
                    ),
                ),
                contract: Account(
                    code=bytes.fromhex(
                        "60406000600060006000600435611000015af15060005160005560205160015500"  # noqa: E501
                    )
                ),
            },
        },
        {
            "indexes": {"data": 11, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex("600060006000600061c0575af400")
                ),
                callee_1: Account(
                    code=bytes.fromhex("6000600060006000600061c0575af100")
                ),
                callee_2: Account(
                    code=bytes.fromhex("6000600060006000600061c0575af200")
                ),
                callee_3: Account(
                    code=bytes.fromhex(
                        "602060006000600063ead0c0575afa5060005160005500"
                    )
                ),
                callee_4: Account(
                    storage={24743: 48879},
                    code=bytes.fromhex(
                        "5a600052600260005560115a60005103036000525a6020526160a754604052601a5a602051030360205260406000fd00"  # noqa: E501
                    ),
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "5a6000526000600060006000600063dead01115af150617fe85a600051030360005500"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "5a6000526000600060006000600063dead01125af150617fe85a600051030360005500"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "610bad600052602060006000600061f1135afa5060005160005500"  # noqa: E501
                    ),
                ),
                callee_8: Account(
                    code=bytes.fromhex("6020600060006000600061f114610b65f100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6020600060006000600061f115611800f100")
                ),
                callee_10: Account(
                    storage={0: 15, 24743: 57005},
                    code=bytes.fromhex(
                        "600054505a600052600261beef5560115a60005103036000525a6020526160a75460a05260235a60205103036020525a60405261beef60005461f000015560785a60405103036040525a60605260005461f010015450607a5a60605103036060526000516000546101000155602051600054610200015560405160005461030001556060516000546104000155600060005411609b57600060b4565b600160005403600055600060006000600060006110165af15b00"  # noqa: E501
                    ),
                ),
                callee_11: Account(
                    code=bytes.fromhex(
                        "60068060336101003961020052602180603960003961022052610200516101000160006000f0610240526102405160015500fe60ff600055005a60005261ffff6000555a6000510360015561010061010060003960106000f300"  # noqa: E501
                    )
                ),
                callee_12: Account(
                    code=bytes.fromhex(
                        "60068060366101003961020052602180603c60003961022052615a17610200516101000160006000f5610240526102405160015500fe60ff600055005a60005261ffff6000555a6000510360015561010061010060003960106000f300"  # noqa: E501
                    )
                ),
                callee_13: Account(
                    code=bytes.fromhex(
                        "60138060446101003961020052600f80605760003961022052610200516101000160006000f06102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a600051036001550061010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_14: Account(
                    code=bytes.fromhex(
                        "60138060476101003961020052600f80605a60003961022052615a17610200516101000160006000f56102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a600051036001550061010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_15: Account(
                    code=bytes.fromhex(
                        "60138060446101003961020052602180605760003961022052610200516101000160006000f06102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a60005103600255005a60005261ffff6000555a6000510360015561010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_16: Account(
                    code=bytes.fromhex(
                        "60138060476101003961020052602180605a60003961022052615a17610200516101000160006000f56102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a60005103600255005a60005261ffff6000555a6000510360015561010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_17: Account(
                    code=bytes.fromhex(
                        "6000600060006000600061f1265af1506000600060006000600061f1265af100"  # noqa: E501
                    )
                ),
                callee_18: Account(
                    storage={24743: 57005},
                    code=bytes.fromhex(
                        "5a600052600260005560115a60005103036000526000516001555a6000526160a75460205260105a600051030360005260005160025500"  # noqa: E501
                    ),
                ),
                callee_19: Account(
                    code=bytes.fromhex(
                        "63dead60a760005561600d60005260206000f300"
                    )
                ),
                callee_20: Account(
                    storage={0: 2989}, code=bytes.fromhex("61600d60005500")
                ),
                callee_21: Account(
                    storage={0: 2989, 24743: 57005},
                    code=bytes.fromhex("6160a75460005261600d60005500"),
                ),
                callee_22: Account(
                    storage={0: 24743, 1: 20017, 2: 117},
                    code=bytes.fromhex(
                        "5a6000526160a76000555a60005103600052600060015414602457600051600255602b565b6000516001555b00"  # noqa: E501
                    ),
                ),
                callee_23: Account(code=bytes.fromhex("61dead6000556000ff00")),
                callee_24: Account(
                    storage={0: 0xDEAD0060A7},
                    code=bytes.fromhex("600054506000ff00"),
                ),
                callee_25: Account(
                    storage={24743: 57005},
                    code=bytes.fromhex(
                        "5a6000526160a75460205260135a600051030360005260206000f300"  # noqa: E501
                    ),
                ),
                contract: Account(
                    code=bytes.fromhex(
                        "60406000600060006000600435611000015af15060005160005560205160015500"  # noqa: E501
                    )
                ),
            },
        },
        {
            "indexes": {"data": 12, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex("600060006000600061c0575af400")
                ),
                callee_1: Account(
                    code=bytes.fromhex("6000600060006000600061c0575af100")
                ),
                callee_2: Account(
                    code=bytes.fromhex("6000600060006000600061c0575af200")
                ),
                callee_3: Account(
                    code=bytes.fromhex(
                        "602060006000600063ead0c0575afa5060005160005500"
                    )
                ),
                callee_4: Account(
                    storage={24743: 48879},
                    code=bytes.fromhex(
                        "5a600052600260005560115a60005103036000525a6020526160a754604052601a5a602051030360205260406000fd00"  # noqa: E501
                    ),
                ),
                callee_5: Account(
                    storage={0: 24601},
                    code=bytes.fromhex(
                        "5a6000526000600060006000600063dead01115af150617fe85a600051030360005500"  # noqa: E501
                    ),
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "5a6000526000600060006000600063dead01125af150617fe85a600051030360005500"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "610bad600052602060006000600061f1135afa5060005160005500"  # noqa: E501
                    ),
                ),
                callee_8: Account(
                    code=bytes.fromhex("6020600060006000600061f114610b65f100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6020600060006000600061f115611800f100")
                ),
                callee_10: Account(
                    storage={0: 15, 24743: 57005},
                    code=bytes.fromhex(
                        "600054505a600052600261beef5560115a60005103036000525a6020526160a75460a05260235a60205103036020525a60405261beef60005461f000015560785a60405103036040525a60605260005461f010015450607a5a60605103036060526000516000546101000155602051600054610200015560405160005461030001556060516000546104000155600060005411609b57600060b4565b600160005403600055600060006000600060006110165af15b00"  # noqa: E501
                    ),
                ),
                callee_11: Account(
                    code=bytes.fromhex(
                        "60068060336101003961020052602180603960003961022052610200516101000160006000f0610240526102405160015500fe60ff600055005a60005261ffff6000555a6000510360015561010061010060003960106000f300"  # noqa: E501
                    )
                ),
                callee_12: Account(
                    code=bytes.fromhex(
                        "60068060366101003961020052602180603c60003961022052615a17610200516101000160006000f5610240526102405160015500fe60ff600055005a60005261ffff6000555a6000510360015561010061010060003960106000f300"  # noqa: E501
                    )
                ),
                callee_13: Account(
                    code=bytes.fromhex(
                        "60138060446101003961020052600f80605760003961022052610200516101000160006000f06102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a600051036001550061010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_14: Account(
                    code=bytes.fromhex(
                        "60138060476101003961020052600f80605a60003961022052615a17610200516101000160006000f56102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a600051036001550061010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_15: Account(
                    code=bytes.fromhex(
                        "60138060446101003961020052602180605760003961022052610200516101000160006000f06102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a60005103600255005a60005261ffff6000555a6000510360015561010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_16: Account(
                    code=bytes.fromhex(
                        "60138060476101003961020052602180605a60003961022052615a17610200516101000160006000f56102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a60005103600255005a60005261ffff6000555a6000510360015561010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_17: Account(
                    code=bytes.fromhex(
                        "6000600060006000600061f1265af1506000600060006000600061f1265af100"  # noqa: E501
                    )
                ),
                callee_18: Account(
                    storage={24743: 57005},
                    code=bytes.fromhex(
                        "5a600052600260005560115a60005103036000526000516001555a6000526160a75460205260105a600051030360005260005160025500"  # noqa: E501
                    ),
                ),
                callee_19: Account(
                    code=bytes.fromhex(
                        "63dead60a760005561600d60005260206000f300"
                    )
                ),
                callee_20: Account(
                    storage={0: 2989}, code=bytes.fromhex("61600d60005500")
                ),
                callee_21: Account(
                    storage={0: 2989, 24743: 57005},
                    code=bytes.fromhex("6160a75460005261600d60005500"),
                ),
                callee_22: Account(
                    code=bytes.fromhex(
                        "5a6000526160a76000555a60005103600052600060015414602457600051600255602b565b6000516001555b00"  # noqa: E501
                    )
                ),
                callee_23: Account(
                    storage={0: 57005},
                    code=bytes.fromhex("61dead6000556000ff00"),
                ),
                callee_24: Account(
                    storage={0: 0xDEAD0060A7},
                    code=bytes.fromhex("600054506000ff00"),
                ),
                callee_25: Account(
                    storage={24743: 57005},
                    code=bytes.fromhex(
                        "5a6000526160a75460205260135a600051030360005260206000f300"  # noqa: E501
                    ),
                ),
                contract: Account(
                    code=bytes.fromhex(
                        "60406000600060006000600435611000015af15060005160005560205160015500"  # noqa: E501
                    )
                ),
            },
        },
        {
            "indexes": {"data": 13, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex("600060006000600061c0575af400")
                ),
                callee_1: Account(
                    code=bytes.fromhex("6000600060006000600061c0575af100")
                ),
                callee_2: Account(
                    code=bytes.fromhex("6000600060006000600061c0575af200")
                ),
                callee_3: Account(
                    code=bytes.fromhex(
                        "602060006000600063ead0c0575afa5060005160005500"
                    )
                ),
                callee_4: Account(
                    storage={24743: 48879},
                    code=bytes.fromhex(
                        "5a600052600260005560115a60005103036000525a6020526160a754604052601a5a602051030360205260406000fd00"  # noqa: E501
                    ),
                ),
                callee_5: Account(
                    storage={0: 20001},
                    code=bytes.fromhex(
                        "5a6000526000600060006000600063dead01115af150617fe85a600051030360005500"  # noqa: E501
                    ),
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "5a6000526000600060006000600063dead01125af150617fe85a600051030360005500"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "610bad600052602060006000600061f1135afa5060005160005500"  # noqa: E501
                    ),
                ),
                callee_8: Account(
                    code=bytes.fromhex("6020600060006000600061f114610b65f100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6020600060006000600061f115611800f100")
                ),
                callee_10: Account(
                    storage={0: 15, 24743: 57005},
                    code=bytes.fromhex(
                        "600054505a600052600261beef5560115a60005103036000525a6020526160a75460a05260235a60205103036020525a60405261beef60005461f000015560785a60405103036040525a60605260005461f010015450607a5a60605103036060526000516000546101000155602051600054610200015560405160005461030001556060516000546104000155600060005411609b57600060b4565b600160005403600055600060006000600060006110165af15b00"  # noqa: E501
                    ),
                ),
                callee_11: Account(
                    code=bytes.fromhex(
                        "60068060336101003961020052602180603960003961022052610200516101000160006000f0610240526102405160015500fe60ff600055005a60005261ffff6000555a6000510360015561010061010060003960106000f300"  # noqa: E501
                    )
                ),
                callee_12: Account(
                    code=bytes.fromhex(
                        "60068060366101003961020052602180603c60003961022052615a17610200516101000160006000f5610240526102405160015500fe60ff600055005a60005261ffff6000555a6000510360015561010061010060003960106000f300"  # noqa: E501
                    )
                ),
                callee_13: Account(
                    code=bytes.fromhex(
                        "60138060446101003961020052600f80605760003961022052610200516101000160006000f06102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a600051036001550061010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_14: Account(
                    code=bytes.fromhex(
                        "60138060476101003961020052600f80605a60003961022052615a17610200516101000160006000f56102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a600051036001550061010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_15: Account(
                    code=bytes.fromhex(
                        "60138060446101003961020052602180605760003961022052610200516101000160006000f06102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a60005103600255005a60005261ffff6000555a6000510360015561010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_16: Account(
                    code=bytes.fromhex(
                        "60138060476101003961020052602180605a60003961022052615a17610200516101000160006000f56102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a60005103600255005a60005261ffff6000555a6000510360015561010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_17: Account(
                    code=bytes.fromhex(
                        "6000600060006000600061f1265af1506000600060006000600061f1265af100"  # noqa: E501
                    )
                ),
                callee_18: Account(
                    storage={24743: 57005},
                    code=bytes.fromhex(
                        "5a600052600260005560115a60005103036000526000516001555a6000526160a75460205260105a600051030360005260005160025500"  # noqa: E501
                    ),
                ),
                callee_19: Account(
                    code=bytes.fromhex(
                        "63dead60a760005561600d60005260206000f300"
                    )
                ),
                callee_20: Account(
                    storage={0: 2989}, code=bytes.fromhex("61600d60005500")
                ),
                callee_21: Account(
                    storage={0: 2989, 24743: 57005},
                    code=bytes.fromhex("6160a75460005261600d60005500"),
                ),
                callee_22: Account(
                    code=bytes.fromhex(
                        "5a6000526160a76000555a60005103600052600060015414602457600051600255602b565b6000516001555b00"  # noqa: E501
                    )
                ),
                callee_23: Account(
                    storage={0: 57005},
                    code=bytes.fromhex("61dead6000556000ff00"),
                ),
                callee_24: Account(
                    storage={0: 0xDEAD0060A7},
                    code=bytes.fromhex("600054506000ff00"),
                ),
                callee_25: Account(
                    storage={24743: 57005},
                    code=bytes.fromhex(
                        "5a6000526160a75460205260135a600051030360005260206000f300"  # noqa: E501
                    ),
                ),
                contract: Account(
                    code=bytes.fromhex(
                        "60406000600060006000600435611000015af15060005160005560205160015500"  # noqa: E501
                    )
                ),
            },
        },
        {
            "indexes": {"data": 14, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex("600060006000600061c0575af400")
                ),
                callee_1: Account(
                    code=bytes.fromhex("6000600060006000600061c0575af100")
                ),
                callee_2: Account(
                    storage={0: 2, 1: 22103, 2: 2107},
                    code=bytes.fromhex("6000600060006000600061c0575af200"),
                ),
                callee_3: Account(
                    code=bytes.fromhex(
                        "602060006000600063ead0c0575afa5060005160005500"
                    )
                ),
                callee_4: Account(
                    storage={24743: 48879},
                    code=bytes.fromhex(
                        "5a600052600260005560115a60005103036000525a6020526160a754604052601a5a602051030360205260406000fd00"  # noqa: E501
                    ),
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "5a6000526000600060006000600063dead01115af150617fe85a600051030360005500"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "5a6000526000600060006000600063dead01125af150617fe85a600051030360005500"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "610bad600052602060006000600061f1135afa5060005160005500"  # noqa: E501
                    ),
                ),
                callee_8: Account(
                    code=bytes.fromhex("6020600060006000600061f114610b65f100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6020600060006000600061f115611800f100")
                ),
                callee_10: Account(
                    storage={0: 15, 24743: 57005},
                    code=bytes.fromhex(
                        "600054505a600052600261beef5560115a60005103036000525a6020526160a75460a05260235a60205103036020525a60405261beef60005461f000015560785a60405103036040525a60605260005461f010015450607a5a60605103036060526000516000546101000155602051600054610200015560405160005461030001556060516000546104000155600060005411609b57600060b4565b600160005403600055600060006000600060006110165af15b00"  # noqa: E501
                    ),
                ),
                callee_11: Account(
                    code=bytes.fromhex(
                        "60068060336101003961020052602180603960003961022052610200516101000160006000f0610240526102405160015500fe60ff600055005a60005261ffff6000555a6000510360015561010061010060003960106000f300"  # noqa: E501
                    )
                ),
                callee_12: Account(
                    code=bytes.fromhex(
                        "60068060366101003961020052602180603c60003961022052615a17610200516101000160006000f5610240526102405160015500fe60ff600055005a60005261ffff6000555a6000510360015561010061010060003960106000f300"  # noqa: E501
                    )
                ),
                callee_13: Account(
                    code=bytes.fromhex(
                        "60138060446101003961020052600f80605760003961022052610200516101000160006000f06102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a600051036001550061010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_14: Account(
                    code=bytes.fromhex(
                        "60138060476101003961020052600f80605a60003961022052615a17610200516101000160006000f56102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a600051036001550061010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_15: Account(
                    code=bytes.fromhex(
                        "60138060446101003961020052602180605760003961022052610200516101000160006000f06102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a60005103600255005a60005261ffff6000555a6000510360015561010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_16: Account(
                    code=bytes.fromhex(
                        "60138060476101003961020052602180605a60003961022052615a17610200516101000160006000f56102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a60005103600255005a60005261ffff6000555a6000510360015561010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_17: Account(
                    code=bytes.fromhex(
                        "6000600060006000600061f1265af1506000600060006000600061f1265af100"  # noqa: E501
                    )
                ),
                callee_18: Account(
                    storage={24743: 57005},
                    code=bytes.fromhex(
                        "5a600052600260005560115a60005103036000526000516001555a6000526160a75460205260105a600051030360005260005160025500"  # noqa: E501
                    ),
                ),
                callee_19: Account(
                    code=bytes.fromhex(
                        "63dead60a760005561600d60005260206000f300"
                    )
                ),
                callee_20: Account(
                    storage={0: 2989}, code=bytes.fromhex("61600d60005500")
                ),
                callee_21: Account(
                    storage={0: 2989, 24743: 57005},
                    code=bytes.fromhex("6160a75460005261600d60005500"),
                ),
                callee_22: Account(
                    code=bytes.fromhex(
                        "5a6000526160a76000555a60005103600052600060015414602457600051600255602b565b6000516001555b00"  # noqa: E501
                    )
                ),
                callee_23: Account(code=bytes.fromhex("61dead6000556000ff00")),
                callee_24: Account(
                    storage={0: 0xDEAD0060A7},
                    code=bytes.fromhex("600054506000ff00"),
                ),
                callee_25: Account(
                    storage={24743: 57005},
                    code=bytes.fromhex(
                        "5a6000526160a75460205260135a600051030360005260206000f300"  # noqa: E501
                    ),
                ),
                contract: Account(
                    code=bytes.fromhex(
                        "60406000600060006000600435611000015af15060005160005560205160015500"  # noqa: E501
                    )
                ),
            },
        },
        {
            "indexes": {"data": 15, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex("600060006000600061c0575af400")
                ),
                callee_1: Account(
                    code=bytes.fromhex("6000600060006000600061c0575af100")
                ),
                callee_2: Account(
                    storage={0: 2, 1: 20003, 2: 107},
                    code=bytes.fromhex("6000600060006000600061c0575af200"),
                ),
                callee_3: Account(
                    code=bytes.fromhex(
                        "602060006000600063ead0c0575afa5060005160005500"
                    )
                ),
                callee_4: Account(
                    storage={24743: 48879},
                    code=bytes.fromhex(
                        "5a600052600260005560115a60005103036000525a6020526160a754604052601a5a602051030360205260406000fd00"  # noqa: E501
                    ),
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "5a6000526000600060006000600063dead01115af150617fe85a600051030360005500"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "5a6000526000600060006000600063dead01125af150617fe85a600051030360005500"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "610bad600052602060006000600061f1135afa5060005160005500"  # noqa: E501
                    ),
                ),
                callee_8: Account(
                    code=bytes.fromhex("6020600060006000600061f114610b65f100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6020600060006000600061f115611800f100")
                ),
                callee_10: Account(
                    storage={0: 15, 24743: 57005},
                    code=bytes.fromhex(
                        "600054505a600052600261beef5560115a60005103036000525a6020526160a75460a05260235a60205103036020525a60405261beef60005461f000015560785a60405103036040525a60605260005461f010015450607a5a60605103036060526000516000546101000155602051600054610200015560405160005461030001556060516000546104000155600060005411609b57600060b4565b600160005403600055600060006000600060006110165af15b00"  # noqa: E501
                    ),
                ),
                callee_11: Account(
                    code=bytes.fromhex(
                        "60068060336101003961020052602180603960003961022052610200516101000160006000f0610240526102405160015500fe60ff600055005a60005261ffff6000555a6000510360015561010061010060003960106000f300"  # noqa: E501
                    )
                ),
                callee_12: Account(
                    code=bytes.fromhex(
                        "60068060366101003961020052602180603c60003961022052615a17610200516101000160006000f5610240526102405160015500fe60ff600055005a60005261ffff6000555a6000510360015561010061010060003960106000f300"  # noqa: E501
                    )
                ),
                callee_13: Account(
                    code=bytes.fromhex(
                        "60138060446101003961020052600f80605760003961022052610200516101000160006000f06102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a600051036001550061010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_14: Account(
                    code=bytes.fromhex(
                        "60138060476101003961020052600f80605a60003961022052615a17610200516101000160006000f56102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a600051036001550061010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_15: Account(
                    code=bytes.fromhex(
                        "60138060446101003961020052602180605760003961022052610200516101000160006000f06102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a60005103600255005a60005261ffff6000555a6000510360015561010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_16: Account(
                    code=bytes.fromhex(
                        "60138060476101003961020052602180605a60003961022052615a17610200516101000160006000f56102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a60005103600255005a60005261ffff6000555a6000510360015561010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_17: Account(
                    code=bytes.fromhex(
                        "6000600060006000600061f1265af1506000600060006000600061f1265af100"  # noqa: E501
                    )
                ),
                callee_18: Account(
                    storage={24743: 57005},
                    code=bytes.fromhex(
                        "5a600052600260005560115a60005103036000526000516001555a6000526160a75460205260105a600051030360005260005160025500"  # noqa: E501
                    ),
                ),
                callee_19: Account(
                    code=bytes.fromhex(
                        "63dead60a760005561600d60005260206000f300"
                    )
                ),
                callee_20: Account(
                    storage={0: 2989}, code=bytes.fromhex("61600d60005500")
                ),
                callee_21: Account(
                    storage={0: 2989, 24743: 57005},
                    code=bytes.fromhex("6160a75460005261600d60005500"),
                ),
                callee_22: Account(
                    code=bytes.fromhex(
                        "5a6000526160a76000555a60005103600052600060015414602457600051600255602b565b6000516001555b00"  # noqa: E501
                    )
                ),
                callee_23: Account(code=bytes.fromhex("61dead6000556000ff00")),
                callee_24: Account(
                    storage={0: 0xDEAD0060A7},
                    code=bytes.fromhex("600054506000ff00"),
                ),
                callee_25: Account(
                    storage={24743: 57005},
                    code=bytes.fromhex(
                        "5a6000526160a75460205260135a600051030360005260206000f300"  # noqa: E501
                    ),
                ),
                contract: Account(
                    code=bytes.fromhex(
                        "60406000600060006000600435611000015af15060005160005560205160015500"  # noqa: E501
                    )
                ),
            },
        },
        {
            "indexes": {"data": 16, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex("600060006000600061c0575af400")
                ),
                callee_1: Account(
                    code=bytes.fromhex("6000600060006000600061c0575af100")
                ),
                callee_2: Account(
                    code=bytes.fromhex("6000600060006000600061c0575af200")
                ),
                callee_3: Account(
                    code=bytes.fromhex(
                        "602060006000600063ead0c0575afa5060005160005500"
                    )
                ),
                callee_4: Account(
                    storage={24743: 48879},
                    code=bytes.fromhex(
                        "5a600052600260005560115a60005103036000525a6020526160a754604052601a5a602051030360205260406000fd00"  # noqa: E501
                    ),
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "5a6000526000600060006000600063dead01115af150617fe85a600051030360005500"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "5a6000526000600060006000600063dead01125af150617fe85a600051030360005500"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "610bad600052602060006000600061f1135afa5060005160005500"  # noqa: E501
                    ),
                ),
                callee_8: Account(
                    code=bytes.fromhex("6020600060006000600061f114610b65f100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6020600060006000600061f115611800f100")
                ),
                callee_10: Account(
                    storage={0: 15, 24743: 57005},
                    code=bytes.fromhex(
                        "600054505a600052600261beef5560115a60005103036000525a6020526160a75460a05260235a60205103036020525a60405261beef60005461f000015560785a60405103036040525a60605260005461f010015450607a5a60605103036060526000516000546101000155602051600054610200015560405160005461030001556060516000546104000155600060005411609b57600060b4565b600160005403600055600060006000600060006110165af15b00"  # noqa: E501
                    ),
                ),
                callee_11: Account(
                    code=bytes.fromhex(
                        "60068060336101003961020052602180603960003961022052610200516101000160006000f0610240526102405160015500fe60ff600055005a60005261ffff6000555a6000510360015561010061010060003960106000f300"  # noqa: E501
                    )
                ),
                callee_12: Account(
                    code=bytes.fromhex(
                        "60068060366101003961020052602180603c60003961022052615a17610200516101000160006000f5610240526102405160015500fe60ff600055005a60005261ffff6000555a6000510360015561010061010060003960106000f300"  # noqa: E501
                    )
                ),
                callee_13: Account(
                    code=bytes.fromhex(
                        "60138060446101003961020052600f80605760003961022052610200516101000160006000f06102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a600051036001550061010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_14: Account(
                    code=bytes.fromhex(
                        "60138060476101003961020052600f80605a60003961022052615a17610200516101000160006000f56102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a600051036001550061010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_15: Account(
                    code=bytes.fromhex(
                        "60138060446101003961020052602180605760003961022052610200516101000160006000f06102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a60005103600255005a60005261ffff6000555a6000510360015561010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_16: Account(
                    storage={1: 0x83FBDAE70258AC0FA837B701CC63CEDF48D4B6BF},
                    code=bytes.fromhex(
                        "60138060476101003961020052602180605a60003961022052615a17610200516101000160006000f56102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a60005103600255005a60005261ffff6000555a6000510360015561010061010060003960806000f300"  # noqa: E501
                    ),
                ),
                callee_17: Account(
                    code=bytes.fromhex(
                        "6000600060006000600061f1265af1506000600060006000600061f1265af100"  # noqa: E501
                    )
                ),
                callee_18: Account(
                    storage={24743: 57005},
                    code=bytes.fromhex(
                        "5a600052600260005560115a60005103036000526000516001555a6000526160a75460205260105a600051030360005260005160025500"  # noqa: E501
                    ),
                ),
                callee_19: Account(
                    code=bytes.fromhex(
                        "63dead60a760005561600d60005260206000f300"
                    )
                ),
                callee_20: Account(
                    storage={0: 2989}, code=bytes.fromhex("61600d60005500")
                ),
                callee_21: Account(
                    storage={0: 2989, 24743: 57005},
                    code=bytes.fromhex("6160a75460005261600d60005500"),
                ),
                callee_22: Account(
                    code=bytes.fromhex(
                        "5a6000526160a76000555a60005103600052600060015414602457600051600255602b565b6000516001555b00"  # noqa: E501
                    )
                ),
                callee_23: Account(code=bytes.fromhex("61dead6000556000ff00")),
                callee_24: Account(
                    storage={0: 0xDEAD0060A7},
                    code=bytes.fromhex("600054506000ff00"),
                ),
                callee_25: Account(
                    storage={24743: 57005},
                    code=bytes.fromhex(
                        "5a6000526160a75460205260135a600051030360005260206000f300"  # noqa: E501
                    ),
                ),
                Address("0x83fbdae70258ac0fa837b701cc63cedf48d4b6bf"): Account(
                    storage={0: 65535, 1: 22117, 2: 117},
                    code=bytes.fromhex(
                        "5a60005261ffff6000555a600051036002550000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                    ),
                ),
                contract: Account(
                    code=bytes.fromhex(
                        "60406000600060006000600435611000015af15060005160005560205160015500"  # noqa: E501
                    )
                ),
            },
        },
        {
            "indexes": {"data": 17, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex("600060006000600061c0575af400")
                ),
                callee_1: Account(
                    code=bytes.fromhex("6000600060006000600061c0575af100")
                ),
                callee_2: Account(
                    code=bytes.fromhex("6000600060006000600061c0575af200")
                ),
                callee_3: Account(
                    code=bytes.fromhex(
                        "602060006000600063ead0c0575afa5060005160005500"
                    )
                ),
                callee_4: Account(
                    storage={24743: 48879},
                    code=bytes.fromhex(
                        "5a600052600260005560115a60005103036000525a6020526160a754604052601a5a602051030360205260406000fd00"  # noqa: E501
                    ),
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "5a6000526000600060006000600063dead01115af150617fe85a600051030360005500"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "5a6000526000600060006000600063dead01125af150617fe85a600051030360005500"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "610bad600052602060006000600061f1135afa5060005160005500"  # noqa: E501
                    ),
                ),
                callee_8: Account(
                    code=bytes.fromhex("6020600060006000600061f114610b65f100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6020600060006000600061f115611800f100")
                ),
                callee_10: Account(
                    storage={0: 15, 24743: 57005},
                    code=bytes.fromhex(
                        "600054505a600052600261beef5560115a60005103036000525a6020526160a75460a05260235a60205103036020525a60405261beef60005461f000015560785a60405103036040525a60605260005461f010015450607a5a60605103036060526000516000546101000155602051600054610200015560405160005461030001556060516000546104000155600060005411609b57600060b4565b600160005403600055600060006000600060006110165af15b00"  # noqa: E501
                    ),
                ),
                callee_11: Account(
                    code=bytes.fromhex(
                        "60068060336101003961020052602180603960003961022052610200516101000160006000f0610240526102405160015500fe60ff600055005a60005261ffff6000555a6000510360015561010061010060003960106000f300"  # noqa: E501
                    )
                ),
                callee_12: Account(
                    code=bytes.fromhex(
                        "60068060366101003961020052602180603c60003961022052615a17610200516101000160006000f5610240526102405160015500fe60ff600055005a60005261ffff6000555a6000510360015561010061010060003960106000f300"  # noqa: E501
                    )
                ),
                callee_13: Account(
                    code=bytes.fromhex(
                        "60138060446101003961020052600f80605760003961022052610200516101000160006000f06102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a600051036001550061010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_14: Account(
                    code=bytes.fromhex(
                        "60138060476101003961020052600f80605a60003961022052615a17610200516101000160006000f56102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a600051036001550061010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_15: Account(
                    code=bytes.fromhex(
                        "60138060446101003961020052602180605760003961022052610200516101000160006000f06102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a60005103600255005a60005261ffff6000555a6000510360015561010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_16: Account(
                    storage={1: 0x83FBDAE70258AC0FA837B701CC63CEDF48D4B6BF},
                    code=bytes.fromhex(
                        "60138060476101003961020052602180605a60003961022052615a17610200516101000160006000f56102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a60005103600255005a60005261ffff6000555a6000510360015561010061010060003960806000f300"  # noqa: E501
                    ),
                ),
                callee_17: Account(
                    code=bytes.fromhex(
                        "6000600060006000600061f1265af1506000600060006000600061f1265af100"  # noqa: E501
                    )
                ),
                callee_18: Account(
                    storage={24743: 57005},
                    code=bytes.fromhex(
                        "5a600052600260005560115a60005103036000526000516001555a6000526160a75460205260105a600051030360005260005160025500"  # noqa: E501
                    ),
                ),
                callee_19: Account(
                    code=bytes.fromhex(
                        "63dead60a760005561600d60005260206000f300"
                    )
                ),
                callee_20: Account(
                    storage={0: 2989}, code=bytes.fromhex("61600d60005500")
                ),
                callee_21: Account(
                    storage={0: 2989, 24743: 57005},
                    code=bytes.fromhex("6160a75460005261600d60005500"),
                ),
                callee_22: Account(
                    code=bytes.fromhex(
                        "5a6000526160a76000555a60005103600052600060015414602457600051600255602b565b6000516001555b00"  # noqa: E501
                    )
                ),
                callee_23: Account(code=bytes.fromhex("61dead6000556000ff00")),
                callee_24: Account(
                    storage={0: 0xDEAD0060A7},
                    code=bytes.fromhex("600054506000ff00"),
                ),
                callee_25: Account(
                    storage={24743: 57005},
                    code=bytes.fromhex(
                        "5a6000526160a75460205260135a600051030360005260206000f300"  # noqa: E501
                    ),
                ),
                Address("0x83fbdae70258ac0fa837b701cc63cedf48d4b6bf"): Account(
                    storage={0: 65535, 1: 20017, 2: 117},
                    code=bytes.fromhex(
                        "5a60005261ffff6000555a600051036002550000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                    ),
                ),
                contract: Account(
                    code=bytes.fromhex(
                        "60406000600060006000600435611000015af15060005160005560205160015500"  # noqa: E501
                    )
                ),
            },
        },
        {
            "indexes": {"data": 18, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex("600060006000600061c0575af400")
                ),
                callee_1: Account(
                    code=bytes.fromhex("6000600060006000600061c0575af100")
                ),
                callee_2: Account(
                    code=bytes.fromhex("6000600060006000600061c0575af200")
                ),
                callee_3: Account(
                    code=bytes.fromhex(
                        "602060006000600063ead0c0575afa5060005160005500"
                    )
                ),
                callee_4: Account(
                    storage={24743: 48879},
                    code=bytes.fromhex(
                        "5a600052600260005560115a60005103036000525a6020526160a754604052601a5a602051030360205260406000fd00"  # noqa: E501
                    ),
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "5a6000526000600060006000600063dead01115af150617fe85a600051030360005500"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "5a6000526000600060006000600063dead01125af150617fe85a600051030360005500"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "610bad600052602060006000600061f1135afa5060005160005500"  # noqa: E501
                    ),
                ),
                callee_8: Account(
                    code=bytes.fromhex("6020600060006000600061f114610b65f100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6020600060006000600061f115611800f100")
                ),
                callee_10: Account(
                    storage={0: 15, 24743: 57005},
                    code=bytes.fromhex(
                        "600054505a600052600261beef5560115a60005103036000525a6020526160a75460a05260235a60205103036020525a60405261beef60005461f000015560785a60405103036040525a60605260005461f010015450607a5a60605103036060526000516000546101000155602051600054610200015560405160005461030001556060516000546104000155600060005411609b57600060b4565b600160005403600055600060006000600060006110165af15b00"  # noqa: E501
                    ),
                ),
                callee_11: Account(
                    code=bytes.fromhex(
                        "60068060336101003961020052602180603960003961022052610200516101000160006000f0610240526102405160015500fe60ff600055005a60005261ffff6000555a6000510360015561010061010060003960106000f300"  # noqa: E501
                    )
                ),
                callee_12: Account(
                    storage={1: 0xD82F21135ED7D7D833A9F2A0F1CF6C3DA214B8E3},
                    code=bytes.fromhex(
                        "60068060366101003961020052602180603c60003961022052615a17610200516101000160006000f5610240526102405160015500fe60ff600055005a60005261ffff6000555a6000510360015561010061010060003960106000f300"  # noqa: E501
                    ),
                ),
                callee_13: Account(
                    code=bytes.fromhex(
                        "60138060446101003961020052600f80605760003961022052610200516101000160006000f06102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a600051036001550061010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_14: Account(
                    code=bytes.fromhex(
                        "60138060476101003961020052600f80605a60003961022052615a17610200516101000160006000f56102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a600051036001550061010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_15: Account(
                    code=bytes.fromhex(
                        "60138060446101003961020052602180605760003961022052610200516101000160006000f06102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a60005103600255005a60005261ffff6000555a6000510360015561010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_16: Account(
                    code=bytes.fromhex(
                        "60138060476101003961020052602180605a60003961022052615a17610200516101000160006000f56102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a60005103600255005a60005261ffff6000555a6000510360015561010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_17: Account(
                    code=bytes.fromhex(
                        "6000600060006000600061f1265af1506000600060006000600061f1265af100"  # noqa: E501
                    )
                ),
                callee_18: Account(
                    storage={24743: 57005},
                    code=bytes.fromhex(
                        "5a600052600260005560115a60005103036000526000516001555a6000526160a75460205260105a600051030360005260005160025500"  # noqa: E501
                    ),
                ),
                callee_19: Account(
                    code=bytes.fromhex(
                        "63dead60a760005561600d60005260206000f300"
                    )
                ),
                callee_20: Account(
                    storage={0: 2989}, code=bytes.fromhex("61600d60005500")
                ),
                callee_21: Account(
                    storage={0: 2989, 24743: 57005},
                    code=bytes.fromhex("6160a75460005261600d60005500"),
                ),
                callee_22: Account(
                    code=bytes.fromhex(
                        "5a6000526160a76000555a60005103600052600060015414602457600051600255602b565b6000516001555b00"  # noqa: E501
                    )
                ),
                callee_23: Account(code=bytes.fromhex("61dead6000556000ff00")),
                callee_24: Account(
                    storage={0: 0xDEAD0060A7},
                    code=bytes.fromhex("600054506000ff00"),
                ),
                callee_25: Account(
                    storage={24743: 57005},
                    code=bytes.fromhex(
                        "5a6000526160a75460205260135a600051030360005260206000f300"  # noqa: E501
                    ),
                ),
                contract: Account(
                    code=bytes.fromhex(
                        "60406000600060006000600435611000015af15060005160005560205160015500"  # noqa: E501
                    )
                ),
                Address("0xd82f21135ed7d7d833a9f2a0f1cf6c3da214b8e3"): Account(
                    storage={0: 65535, 1: 22117},
                    code=bytes.fromhex("60ff6000550000000000000000000000"),
                ),
            },
        },
        {
            "indexes": {"data": 19, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex("600060006000600061c0575af400")
                ),
                callee_1: Account(
                    code=bytes.fromhex("6000600060006000600061c0575af100")
                ),
                callee_2: Account(
                    code=bytes.fromhex("6000600060006000600061c0575af200")
                ),
                callee_3: Account(
                    code=bytes.fromhex(
                        "602060006000600063ead0c0575afa5060005160005500"
                    )
                ),
                callee_4: Account(
                    storage={24743: 48879},
                    code=bytes.fromhex(
                        "5a600052600260005560115a60005103036000525a6020526160a754604052601a5a602051030360205260406000fd00"  # noqa: E501
                    ),
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "5a6000526000600060006000600063dead01115af150617fe85a600051030360005500"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "5a6000526000600060006000600063dead01125af150617fe85a600051030360005500"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "610bad600052602060006000600061f1135afa5060005160005500"  # noqa: E501
                    ),
                ),
                callee_8: Account(
                    code=bytes.fromhex("6020600060006000600061f114610b65f100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6020600060006000600061f115611800f100")
                ),
                callee_10: Account(
                    storage={0: 15, 24743: 57005},
                    code=bytes.fromhex(
                        "600054505a600052600261beef5560115a60005103036000525a6020526160a75460a05260235a60205103036020525a60405261beef60005461f000015560785a60405103036040525a60605260005461f010015450607a5a60605103036060526000516000546101000155602051600054610200015560405160005461030001556060516000546104000155600060005411609b57600060b4565b600160005403600055600060006000600060006110165af15b00"  # noqa: E501
                    ),
                ),
                callee_11: Account(
                    code=bytes.fromhex(
                        "60068060336101003961020052602180603960003961022052610200516101000160006000f0610240526102405160015500fe60ff600055005a60005261ffff6000555a6000510360015561010061010060003960106000f300"  # noqa: E501
                    )
                ),
                callee_12: Account(
                    storage={1: 0xD82F21135ED7D7D833A9F2A0F1CF6C3DA214B8E3},
                    code=bytes.fromhex(
                        "60068060366101003961020052602180603c60003961022052615a17610200516101000160006000f5610240526102405160015500fe60ff600055005a60005261ffff6000555a6000510360015561010061010060003960106000f300"  # noqa: E501
                    ),
                ),
                callee_13: Account(
                    code=bytes.fromhex(
                        "60138060446101003961020052600f80605760003961022052610200516101000160006000f06102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a600051036001550061010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_14: Account(
                    code=bytes.fromhex(
                        "60138060476101003961020052600f80605a60003961022052615a17610200516101000160006000f56102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a600051036001550061010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_15: Account(
                    code=bytes.fromhex(
                        "60138060446101003961020052602180605760003961022052610200516101000160006000f06102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a60005103600255005a60005261ffff6000555a6000510360015561010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_16: Account(
                    code=bytes.fromhex(
                        "60138060476101003961020052602180605a60003961022052615a17610200516101000160006000f56102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a60005103600255005a60005261ffff6000555a6000510360015561010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_17: Account(
                    code=bytes.fromhex(
                        "6000600060006000600061f1265af1506000600060006000600061f1265af100"  # noqa: E501
                    )
                ),
                callee_18: Account(
                    storage={24743: 57005},
                    code=bytes.fromhex(
                        "5a600052600260005560115a60005103036000526000516001555a6000526160a75460205260105a600051030360005260005160025500"  # noqa: E501
                    ),
                ),
                callee_19: Account(
                    code=bytes.fromhex(
                        "63dead60a760005561600d60005260206000f300"
                    )
                ),
                callee_20: Account(
                    storage={0: 2989}, code=bytes.fromhex("61600d60005500")
                ),
                callee_21: Account(
                    storage={0: 2989, 24743: 57005},
                    code=bytes.fromhex("6160a75460005261600d60005500"),
                ),
                callee_22: Account(
                    code=bytes.fromhex(
                        "5a6000526160a76000555a60005103600052600060015414602457600051600255602b565b6000516001555b00"  # noqa: E501
                    )
                ),
                callee_23: Account(code=bytes.fromhex("61dead6000556000ff00")),
                callee_24: Account(
                    storage={0: 0xDEAD0060A7},
                    code=bytes.fromhex("600054506000ff00"),
                ),
                callee_25: Account(
                    storage={24743: 57005},
                    code=bytes.fromhex(
                        "5a6000526160a75460205260135a600051030360005260206000f300"  # noqa: E501
                    ),
                ),
                contract: Account(
                    code=bytes.fromhex(
                        "60406000600060006000600435611000015af15060005160005560205160015500"  # noqa: E501
                    )
                ),
                Address("0xd82f21135ed7d7d833a9f2a0f1cf6c3da214b8e3"): Account(
                    storage={0: 65535, 1: 20017},
                    code=bytes.fromhex("60ff6000550000000000000000000000"),
                ),
            },
        },
        {
            "indexes": {"data": 20, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex("600060006000600061c0575af400")
                ),
                callee_1: Account(
                    code=bytes.fromhex("6000600060006000600061c0575af100")
                ),
                callee_2: Account(
                    code=bytes.fromhex("6000600060006000600061c0575af200")
                ),
                callee_3: Account(
                    code=bytes.fromhex(
                        "602060006000600063ead0c0575afa5060005160005500"
                    )
                ),
                callee_4: Account(
                    storage={24743: 48879},
                    code=bytes.fromhex(
                        "5a600052600260005560115a60005103036000525a6020526160a754604052601a5a602051030360205260406000fd00"  # noqa: E501
                    ),
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "5a6000526000600060006000600063dead01115af150617fe85a600051030360005500"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "5a6000526000600060006000600063dead01125af150617fe85a600051030360005500"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "610bad600052602060006000600061f1135afa5060005160005500"  # noqa: E501
                    ),
                ),
                callee_8: Account(
                    code=bytes.fromhex("6020600060006000600061f114610b65f100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6020600060006000600061f115611800f100")
                ),
                callee_10: Account(
                    storage={0: 15, 24743: 57005},
                    code=bytes.fromhex(
                        "600054505a600052600261beef5560115a60005103036000525a6020526160a75460a05260235a60205103036020525a60405261beef60005461f000015560785a60405103036040525a60605260005461f010015450607a5a60605103036060526000516000546101000155602051600054610200015560405160005461030001556060516000546104000155600060005411609b57600060b4565b600160005403600055600060006000600060006110165af15b00"  # noqa: E501
                    ),
                ),
                callee_11: Account(
                    code=bytes.fromhex(
                        "60068060336101003961020052602180603960003961022052610200516101000160006000f0610240526102405160015500fe60ff600055005a60005261ffff6000555a6000510360015561010061010060003960106000f300"  # noqa: E501
                    )
                ),
                callee_12: Account(
                    code=bytes.fromhex(
                        "60068060366101003961020052602180603c60003961022052615a17610200516101000160006000f5610240526102405160015500fe60ff600055005a60005261ffff6000555a6000510360015561010061010060003960106000f300"  # noqa: E501
                    )
                ),
                callee_13: Account(
                    code=bytes.fromhex(
                        "60138060446101003961020052600f80605760003961022052610200516101000160006000f06102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a600051036001550061010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_14: Account(
                    code=bytes.fromhex(
                        "60138060476101003961020052600f80605a60003961022052615a17610200516101000160006000f56102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a600051036001550061010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_15: Account(
                    storage={1: 0xB76AB2D646C4DF221EDD345957D0A396A2AB1B6D},
                    code=bytes.fromhex(
                        "60138060446101003961020052602180605760003961022052610200516101000160006000f06102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a60005103600255005a60005261ffff6000555a6000510360015561010061010060003960806000f300"  # noqa: E501
                    ),
                ),
                callee_16: Account(
                    code=bytes.fromhex(
                        "60138060476101003961020052602180605a60003961022052615a17610200516101000160006000f56102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a60005103600255005a60005261ffff6000555a6000510360015561010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_17: Account(
                    code=bytes.fromhex(
                        "6000600060006000600061f1265af1506000600060006000600061f1265af100"  # noqa: E501
                    )
                ),
                callee_18: Account(
                    storage={24743: 57005},
                    code=bytes.fromhex(
                        "5a600052600260005560115a60005103036000526000516001555a6000526160a75460205260105a600051030360005260005160025500"  # noqa: E501
                    ),
                ),
                callee_19: Account(
                    code=bytes.fromhex(
                        "63dead60a760005561600d60005260206000f300"
                    )
                ),
                callee_20: Account(
                    storage={0: 2989}, code=bytes.fromhex("61600d60005500")
                ),
                callee_21: Account(
                    storage={0: 2989, 24743: 57005},
                    code=bytes.fromhex("6160a75460005261600d60005500"),
                ),
                callee_22: Account(
                    code=bytes.fromhex(
                        "5a6000526160a76000555a60005103600052600060015414602457600051600255602b565b6000516001555b00"  # noqa: E501
                    )
                ),
                callee_23: Account(code=bytes.fromhex("61dead6000556000ff00")),
                callee_24: Account(
                    storage={0: 0xDEAD0060A7},
                    code=bytes.fromhex("600054506000ff00"),
                ),
                callee_25: Account(
                    storage={24743: 57005},
                    code=bytes.fromhex(
                        "5a6000526160a75460205260135a600051030360005260206000f300"  # noqa: E501
                    ),
                ),
                Address("0xb76ab2d646c4df221edd345957d0a396a2ab1b6d"): Account(
                    storage={0: 65535, 1: 22117, 2: 117},
                    code=bytes.fromhex(
                        "5a60005261ffff6000555a600051036002550000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                    ),
                ),
                contract: Account(
                    code=bytes.fromhex(
                        "60406000600060006000600435611000015af15060005160005560205160015500"  # noqa: E501
                    )
                ),
            },
        },
        {
            "indexes": {"data": 21, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex("600060006000600061c0575af400")
                ),
                callee_1: Account(
                    code=bytes.fromhex("6000600060006000600061c0575af100")
                ),
                callee_2: Account(
                    code=bytes.fromhex("6000600060006000600061c0575af200")
                ),
                callee_3: Account(
                    code=bytes.fromhex(
                        "602060006000600063ead0c0575afa5060005160005500"
                    )
                ),
                callee_4: Account(
                    storage={24743: 48879},
                    code=bytes.fromhex(
                        "5a600052600260005560115a60005103036000525a6020526160a754604052601a5a602051030360205260406000fd00"  # noqa: E501
                    ),
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "5a6000526000600060006000600063dead01115af150617fe85a600051030360005500"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "5a6000526000600060006000600063dead01125af150617fe85a600051030360005500"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "610bad600052602060006000600061f1135afa5060005160005500"  # noqa: E501
                    ),
                ),
                callee_8: Account(
                    code=bytes.fromhex("6020600060006000600061f114610b65f100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6020600060006000600061f115611800f100")
                ),
                callee_10: Account(
                    storage={0: 15, 24743: 57005},
                    code=bytes.fromhex(
                        "600054505a600052600261beef5560115a60005103036000525a6020526160a75460a05260235a60205103036020525a60405261beef60005461f000015560785a60405103036040525a60605260005461f010015450607a5a60605103036060526000516000546101000155602051600054610200015560405160005461030001556060516000546104000155600060005411609b57600060b4565b600160005403600055600060006000600060006110165af15b00"  # noqa: E501
                    ),
                ),
                callee_11: Account(
                    code=bytes.fromhex(
                        "60068060336101003961020052602180603960003961022052610200516101000160006000f0610240526102405160015500fe60ff600055005a60005261ffff6000555a6000510360015561010061010060003960106000f300"  # noqa: E501
                    )
                ),
                callee_12: Account(
                    code=bytes.fromhex(
                        "60068060366101003961020052602180603c60003961022052615a17610200516101000160006000f5610240526102405160015500fe60ff600055005a60005261ffff6000555a6000510360015561010061010060003960106000f300"  # noqa: E501
                    )
                ),
                callee_13: Account(
                    code=bytes.fromhex(
                        "60138060446101003961020052600f80605760003961022052610200516101000160006000f06102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a600051036001550061010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_14: Account(
                    code=bytes.fromhex(
                        "60138060476101003961020052600f80605a60003961022052615a17610200516101000160006000f56102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a600051036001550061010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_15: Account(
                    storage={1: 0xB76AB2D646C4DF221EDD345957D0A396A2AB1B6D},
                    code=bytes.fromhex(
                        "60138060446101003961020052602180605760003961022052610200516101000160006000f06102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a60005103600255005a60005261ffff6000555a6000510360015561010061010060003960806000f300"  # noqa: E501
                    ),
                ),
                callee_16: Account(
                    code=bytes.fromhex(
                        "60138060476101003961020052602180605a60003961022052615a17610200516101000160006000f56102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a60005103600255005a60005261ffff6000555a6000510360015561010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_17: Account(
                    code=bytes.fromhex(
                        "6000600060006000600061f1265af1506000600060006000600061f1265af100"  # noqa: E501
                    )
                ),
                callee_18: Account(
                    storage={24743: 57005},
                    code=bytes.fromhex(
                        "5a600052600260005560115a60005103036000526000516001555a6000526160a75460205260105a600051030360005260005160025500"  # noqa: E501
                    ),
                ),
                callee_19: Account(
                    code=bytes.fromhex(
                        "63dead60a760005561600d60005260206000f300"
                    )
                ),
                callee_20: Account(
                    storage={0: 2989}, code=bytes.fromhex("61600d60005500")
                ),
                callee_21: Account(
                    storage={0: 2989, 24743: 57005},
                    code=bytes.fromhex("6160a75460005261600d60005500"),
                ),
                callee_22: Account(
                    code=bytes.fromhex(
                        "5a6000526160a76000555a60005103600052600060015414602457600051600255602b565b6000516001555b00"  # noqa: E501
                    )
                ),
                callee_23: Account(code=bytes.fromhex("61dead6000556000ff00")),
                callee_24: Account(
                    storage={0: 0xDEAD0060A7},
                    code=bytes.fromhex("600054506000ff00"),
                ),
                callee_25: Account(
                    storage={24743: 57005},
                    code=bytes.fromhex(
                        "5a6000526160a75460205260135a600051030360005260206000f300"  # noqa: E501
                    ),
                ),
                Address("0xb76ab2d646c4df221edd345957d0a396a2ab1b6d"): Account(
                    storage={0: 65535, 1: 20017, 2: 117},
                    code=bytes.fromhex(
                        "5a60005261ffff6000555a600051036002550000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                    ),
                ),
                contract: Account(
                    code=bytes.fromhex(
                        "60406000600060006000600435611000015af15060005160005560205160015500"  # noqa: E501
                    )
                ),
            },
        },
        {
            "indexes": {"data": 22, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex("600060006000600061c0575af400")
                ),
                callee_1: Account(
                    code=bytes.fromhex("6000600060006000600061c0575af100")
                ),
                callee_2: Account(
                    code=bytes.fromhex("6000600060006000600061c0575af200")
                ),
                callee_3: Account(
                    code=bytes.fromhex(
                        "602060006000600063ead0c0575afa5060005160005500"
                    )
                ),
                callee_4: Account(
                    storage={24743: 48879},
                    code=bytes.fromhex(
                        "5a600052600260005560115a60005103036000525a6020526160a754604052601a5a602051030360205260406000fd00"  # noqa: E501
                    ),
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "5a6000526000600060006000600063dead01115af150617fe85a600051030360005500"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "5a6000526000600060006000600063dead01125af150617fe85a600051030360005500"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "610bad600052602060006000600061f1135afa5060005160005500"  # noqa: E501
                    ),
                ),
                callee_8: Account(
                    code=bytes.fromhex("6020600060006000600061f114610b65f100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6020600060006000600061f115611800f100")
                ),
                callee_10: Account(
                    storage={0: 15, 24743: 57005},
                    code=bytes.fromhex(
                        "600054505a600052600261beef5560115a60005103036000525a6020526160a75460a05260235a60205103036020525a60405261beef60005461f000015560785a60405103036040525a60605260005461f010015450607a5a60605103036060526000516000546101000155602051600054610200015560405160005461030001556060516000546104000155600060005411609b57600060b4565b600160005403600055600060006000600060006110165af15b00"  # noqa: E501
                    ),
                ),
                callee_11: Account(
                    storage={1: 0xF342E57F24E0333F3AF34AF08FDBBE9C72CBD37C},
                    code=bytes.fromhex(
                        "60068060336101003961020052602180603960003961022052610200516101000160006000f0610240526102405160015500fe60ff600055005a60005261ffff6000555a6000510360015561010061010060003960106000f300"  # noqa: E501
                    ),
                ),
                callee_12: Account(
                    code=bytes.fromhex(
                        "60068060366101003961020052602180603c60003961022052615a17610200516101000160006000f5610240526102405160015500fe60ff600055005a60005261ffff6000555a6000510360015561010061010060003960106000f300"  # noqa: E501
                    )
                ),
                callee_13: Account(
                    code=bytes.fromhex(
                        "60138060446101003961020052600f80605760003961022052610200516101000160006000f06102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a600051036001550061010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_14: Account(
                    code=bytes.fromhex(
                        "60138060476101003961020052600f80605a60003961022052615a17610200516101000160006000f56102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a600051036001550061010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_15: Account(
                    code=bytes.fromhex(
                        "60138060446101003961020052602180605760003961022052610200516101000160006000f06102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a60005103600255005a60005261ffff6000555a6000510360015561010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_16: Account(
                    code=bytes.fromhex(
                        "60138060476101003961020052602180605a60003961022052615a17610200516101000160006000f56102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a60005103600255005a60005261ffff6000555a6000510360015561010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_17: Account(
                    code=bytes.fromhex(
                        "6000600060006000600061f1265af1506000600060006000600061f1265af100"  # noqa: E501
                    )
                ),
                callee_18: Account(
                    storage={24743: 57005},
                    code=bytes.fromhex(
                        "5a600052600260005560115a60005103036000526000516001555a6000526160a75460205260105a600051030360005260005160025500"  # noqa: E501
                    ),
                ),
                callee_19: Account(
                    code=bytes.fromhex(
                        "63dead60a760005561600d60005260206000f300"
                    )
                ),
                callee_20: Account(
                    storage={0: 2989}, code=bytes.fromhex("61600d60005500")
                ),
                callee_21: Account(
                    storage={0: 2989, 24743: 57005},
                    code=bytes.fromhex("6160a75460005261600d60005500"),
                ),
                callee_22: Account(
                    code=bytes.fromhex(
                        "5a6000526160a76000555a60005103600052600060015414602457600051600255602b565b6000516001555b00"  # noqa: E501
                    )
                ),
                callee_23: Account(code=bytes.fromhex("61dead6000556000ff00")),
                callee_24: Account(
                    storage={0: 0xDEAD0060A7},
                    code=bytes.fromhex("600054506000ff00"),
                ),
                callee_25: Account(
                    storage={24743: 57005},
                    code=bytes.fromhex(
                        "5a6000526160a75460205260135a600051030360005260206000f300"  # noqa: E501
                    ),
                ),
                contract: Account(
                    code=bytes.fromhex(
                        "60406000600060006000600435611000015af15060005160005560205160015500"  # noqa: E501
                    )
                ),
                Address("0xf342e57f24e0333f3af34af08fdbbe9c72cbd37c"): Account(
                    storage={0: 65535, 1: 22117},
                    code=bytes.fromhex("60ff6000550000000000000000000000"),
                ),
            },
        },
        {
            "indexes": {"data": 23, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex("600060006000600061c0575af400")
                ),
                callee_1: Account(
                    code=bytes.fromhex("6000600060006000600061c0575af100")
                ),
                callee_2: Account(
                    code=bytes.fromhex("6000600060006000600061c0575af200")
                ),
                callee_3: Account(
                    code=bytes.fromhex(
                        "602060006000600063ead0c0575afa5060005160005500"
                    )
                ),
                callee_4: Account(
                    storage={24743: 48879},
                    code=bytes.fromhex(
                        "5a600052600260005560115a60005103036000525a6020526160a754604052601a5a602051030360205260406000fd00"  # noqa: E501
                    ),
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "5a6000526000600060006000600063dead01115af150617fe85a600051030360005500"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "5a6000526000600060006000600063dead01125af150617fe85a600051030360005500"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "610bad600052602060006000600061f1135afa5060005160005500"  # noqa: E501
                    ),
                ),
                callee_8: Account(
                    code=bytes.fromhex("6020600060006000600061f114610b65f100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6020600060006000600061f115611800f100")
                ),
                callee_10: Account(
                    storage={0: 15, 24743: 57005},
                    code=bytes.fromhex(
                        "600054505a600052600261beef5560115a60005103036000525a6020526160a75460a05260235a60205103036020525a60405261beef60005461f000015560785a60405103036040525a60605260005461f010015450607a5a60605103036060526000516000546101000155602051600054610200015560405160005461030001556060516000546104000155600060005411609b57600060b4565b600160005403600055600060006000600060006110165af15b00"  # noqa: E501
                    ),
                ),
                callee_11: Account(
                    storage={1: 0xF342E57F24E0333F3AF34AF08FDBBE9C72CBD37C},
                    code=bytes.fromhex(
                        "60068060336101003961020052602180603960003961022052610200516101000160006000f0610240526102405160015500fe60ff600055005a60005261ffff6000555a6000510360015561010061010060003960106000f300"  # noqa: E501
                    ),
                ),
                callee_12: Account(
                    code=bytes.fromhex(
                        "60068060366101003961020052602180603c60003961022052615a17610200516101000160006000f5610240526102405160015500fe60ff600055005a60005261ffff6000555a6000510360015561010061010060003960106000f300"  # noqa: E501
                    )
                ),
                callee_13: Account(
                    code=bytes.fromhex(
                        "60138060446101003961020052600f80605760003961022052610200516101000160006000f06102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a600051036001550061010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_14: Account(
                    code=bytes.fromhex(
                        "60138060476101003961020052600f80605a60003961022052615a17610200516101000160006000f56102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a600051036001550061010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_15: Account(
                    code=bytes.fromhex(
                        "60138060446101003961020052602180605760003961022052610200516101000160006000f06102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a60005103600255005a60005261ffff6000555a6000510360015561010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_16: Account(
                    code=bytes.fromhex(
                        "60138060476101003961020052602180605a60003961022052615a17610200516101000160006000f56102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a60005103600255005a60005261ffff6000555a6000510360015561010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_17: Account(
                    code=bytes.fromhex(
                        "6000600060006000600061f1265af1506000600060006000600061f1265af100"  # noqa: E501
                    )
                ),
                callee_18: Account(
                    storage={24743: 57005},
                    code=bytes.fromhex(
                        "5a600052600260005560115a60005103036000526000516001555a6000526160a75460205260105a600051030360005260005160025500"  # noqa: E501
                    ),
                ),
                callee_19: Account(
                    code=bytes.fromhex(
                        "63dead60a760005561600d60005260206000f300"
                    )
                ),
                callee_20: Account(
                    storage={0: 2989}, code=bytes.fromhex("61600d60005500")
                ),
                callee_21: Account(
                    storage={0: 2989, 24743: 57005},
                    code=bytes.fromhex("6160a75460005261600d60005500"),
                ),
                callee_22: Account(
                    code=bytes.fromhex(
                        "5a6000526160a76000555a60005103600052600060015414602457600051600255602b565b6000516001555b00"  # noqa: E501
                    )
                ),
                callee_23: Account(code=bytes.fromhex("61dead6000556000ff00")),
                callee_24: Account(
                    storage={0: 0xDEAD0060A7},
                    code=bytes.fromhex("600054506000ff00"),
                ),
                callee_25: Account(
                    storage={24743: 57005},
                    code=bytes.fromhex(
                        "5a6000526160a75460205260135a600051030360005260206000f300"  # noqa: E501
                    ),
                ),
                contract: Account(
                    code=bytes.fromhex(
                        "60406000600060006000600435611000015af15060005160005560205160015500"  # noqa: E501
                    )
                ),
                Address("0xf342e57f24e0333f3af34af08fdbbe9c72cbd37c"): Account(
                    storage={0: 65535, 1: 20017},
                    code=bytes.fromhex("60ff6000550000000000000000000000"),
                ),
            },
        },
        {
            "indexes": {"data": 24, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    storage={0: 2, 1: 22103, 2: 2107},
                    code=bytes.fromhex("600060006000600061c0575af400"),
                ),
                callee_1: Account(
                    code=bytes.fromhex("6000600060006000600061c0575af100")
                ),
                callee_2: Account(
                    code=bytes.fromhex("6000600060006000600061c0575af200")
                ),
                callee_3: Account(
                    code=bytes.fromhex(
                        "602060006000600063ead0c0575afa5060005160005500"
                    )
                ),
                callee_4: Account(
                    storage={24743: 48879},
                    code=bytes.fromhex(
                        "5a600052600260005560115a60005103036000525a6020526160a754604052601a5a602051030360205260406000fd00"  # noqa: E501
                    ),
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "5a6000526000600060006000600063dead01115af150617fe85a600051030360005500"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "5a6000526000600060006000600063dead01125af150617fe85a600051030360005500"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "610bad600052602060006000600061f1135afa5060005160005500"  # noqa: E501
                    ),
                ),
                callee_8: Account(
                    code=bytes.fromhex("6020600060006000600061f114610b65f100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6020600060006000600061f115611800f100")
                ),
                callee_10: Account(
                    storage={0: 15, 24743: 57005},
                    code=bytes.fromhex(
                        "600054505a600052600261beef5560115a60005103036000525a6020526160a75460a05260235a60205103036020525a60405261beef60005461f000015560785a60405103036040525a60605260005461f010015450607a5a60605103036060526000516000546101000155602051600054610200015560405160005461030001556060516000546104000155600060005411609b57600060b4565b600160005403600055600060006000600060006110165af15b00"  # noqa: E501
                    ),
                ),
                callee_11: Account(
                    code=bytes.fromhex(
                        "60068060336101003961020052602180603960003961022052610200516101000160006000f0610240526102405160015500fe60ff600055005a60005261ffff6000555a6000510360015561010061010060003960106000f300"  # noqa: E501
                    )
                ),
                callee_12: Account(
                    code=bytes.fromhex(
                        "60068060366101003961020052602180603c60003961022052615a17610200516101000160006000f5610240526102405160015500fe60ff600055005a60005261ffff6000555a6000510360015561010061010060003960106000f300"  # noqa: E501
                    )
                ),
                callee_13: Account(
                    code=bytes.fromhex(
                        "60138060446101003961020052600f80605760003961022052610200516101000160006000f06102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a600051036001550061010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_14: Account(
                    code=bytes.fromhex(
                        "60138060476101003961020052600f80605a60003961022052615a17610200516101000160006000f56102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a600051036001550061010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_15: Account(
                    code=bytes.fromhex(
                        "60138060446101003961020052602180605760003961022052610200516101000160006000f06102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a60005103600255005a60005261ffff6000555a6000510360015561010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_16: Account(
                    code=bytes.fromhex(
                        "60138060476101003961020052602180605a60003961022052615a17610200516101000160006000f56102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a60005103600255005a60005261ffff6000555a6000510360015561010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_17: Account(
                    code=bytes.fromhex(
                        "6000600060006000600061f1265af1506000600060006000600061f1265af100"  # noqa: E501
                    )
                ),
                callee_18: Account(
                    storage={24743: 57005},
                    code=bytes.fromhex(
                        "5a600052600260005560115a60005103036000526000516001555a6000526160a75460205260105a600051030360005260005160025500"  # noqa: E501
                    ),
                ),
                callee_19: Account(
                    code=bytes.fromhex(
                        "63dead60a760005561600d60005260206000f300"
                    )
                ),
                callee_20: Account(
                    storage={0: 2989}, code=bytes.fromhex("61600d60005500")
                ),
                callee_21: Account(
                    storage={0: 2989, 24743: 57005},
                    code=bytes.fromhex("6160a75460005261600d60005500"),
                ),
                callee_22: Account(
                    code=bytes.fromhex(
                        "5a6000526160a76000555a60005103600052600060015414602457600051600255602b565b6000516001555b00"  # noqa: E501
                    )
                ),
                callee_23: Account(code=bytes.fromhex("61dead6000556000ff00")),
                callee_24: Account(
                    storage={0: 0xDEAD0060A7},
                    code=bytes.fromhex("600054506000ff00"),
                ),
                callee_25: Account(
                    storage={24743: 57005},
                    code=bytes.fromhex(
                        "5a6000526160a75460205260135a600051030360005260206000f300"  # noqa: E501
                    ),
                ),
                contract: Account(
                    code=bytes.fromhex(
                        "60406000600060006000600435611000015af15060005160005560205160015500"  # noqa: E501
                    )
                ),
            },
        },
        {
            "indexes": {"data": 25, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    storage={0: 2, 1: 20003, 2: 107},
                    code=bytes.fromhex("600060006000600061c0575af400"),
                ),
                callee_1: Account(
                    code=bytes.fromhex("6000600060006000600061c0575af100")
                ),
                callee_2: Account(
                    code=bytes.fromhex("6000600060006000600061c0575af200")
                ),
                callee_3: Account(
                    code=bytes.fromhex(
                        "602060006000600063ead0c0575afa5060005160005500"
                    )
                ),
                callee_4: Account(
                    storage={24743: 48879},
                    code=bytes.fromhex(
                        "5a600052600260005560115a60005103036000525a6020526160a754604052601a5a602051030360205260406000fd00"  # noqa: E501
                    ),
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "5a6000526000600060006000600063dead01115af150617fe85a600051030360005500"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "5a6000526000600060006000600063dead01125af150617fe85a600051030360005500"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "610bad600052602060006000600061f1135afa5060005160005500"  # noqa: E501
                    ),
                ),
                callee_8: Account(
                    code=bytes.fromhex("6020600060006000600061f114610b65f100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6020600060006000600061f115611800f100")
                ),
                callee_10: Account(
                    storage={0: 15, 24743: 57005},
                    code=bytes.fromhex(
                        "600054505a600052600261beef5560115a60005103036000525a6020526160a75460a05260235a60205103036020525a60405261beef60005461f000015560785a60405103036040525a60605260005461f010015450607a5a60605103036060526000516000546101000155602051600054610200015560405160005461030001556060516000546104000155600060005411609b57600060b4565b600160005403600055600060006000600060006110165af15b00"  # noqa: E501
                    ),
                ),
                callee_11: Account(
                    code=bytes.fromhex(
                        "60068060336101003961020052602180603960003961022052610200516101000160006000f0610240526102405160015500fe60ff600055005a60005261ffff6000555a6000510360015561010061010060003960106000f300"  # noqa: E501
                    )
                ),
                callee_12: Account(
                    code=bytes.fromhex(
                        "60068060366101003961020052602180603c60003961022052615a17610200516101000160006000f5610240526102405160015500fe60ff600055005a60005261ffff6000555a6000510360015561010061010060003960106000f300"  # noqa: E501
                    )
                ),
                callee_13: Account(
                    code=bytes.fromhex(
                        "60138060446101003961020052600f80605760003961022052610200516101000160006000f06102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a600051036001550061010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_14: Account(
                    code=bytes.fromhex(
                        "60138060476101003961020052600f80605a60003961022052615a17610200516101000160006000f56102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a600051036001550061010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_15: Account(
                    code=bytes.fromhex(
                        "60138060446101003961020052602180605760003961022052610200516101000160006000f06102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a60005103600255005a60005261ffff6000555a6000510360015561010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_16: Account(
                    code=bytes.fromhex(
                        "60138060476101003961020052602180605a60003961022052615a17610200516101000160006000f56102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a60005103600255005a60005261ffff6000555a6000510360015561010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_17: Account(
                    code=bytes.fromhex(
                        "6000600060006000600061f1265af1506000600060006000600061f1265af100"  # noqa: E501
                    )
                ),
                callee_18: Account(
                    storage={24743: 57005},
                    code=bytes.fromhex(
                        "5a600052600260005560115a60005103036000526000516001555a6000526160a75460205260105a600051030360005260005160025500"  # noqa: E501
                    ),
                ),
                callee_19: Account(
                    code=bytes.fromhex(
                        "63dead60a760005561600d60005260206000f300"
                    )
                ),
                callee_20: Account(
                    storage={0: 2989}, code=bytes.fromhex("61600d60005500")
                ),
                callee_21: Account(
                    storage={0: 2989, 24743: 57005},
                    code=bytes.fromhex("6160a75460005261600d60005500"),
                ),
                callee_22: Account(
                    code=bytes.fromhex(
                        "5a6000526160a76000555a60005103600052600060015414602457600051600255602b565b6000516001555b00"  # noqa: E501
                    )
                ),
                callee_23: Account(code=bytes.fromhex("61dead6000556000ff00")),
                callee_24: Account(
                    storage={0: 0xDEAD0060A7},
                    code=bytes.fromhex("600054506000ff00"),
                ),
                callee_25: Account(
                    storage={24743: 57005},
                    code=bytes.fromhex(
                        "5a6000526160a75460205260135a600051030360005260206000f300"  # noqa: E501
                    ),
                ),
                contract: Account(
                    code=bytes.fromhex(
                        "60406000600060006000600435611000015af15060005160005560205160015500"  # noqa: E501
                    )
                ),
            },
        },
        {
            "indexes": {"data": 26, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex("600060006000600061c0575af400")
                ),
                callee_1: Account(
                    code=bytes.fromhex("6000600060006000600061c0575af100")
                ),
                callee_2: Account(
                    code=bytes.fromhex("6000600060006000600061c0575af200")
                ),
                callee_3: Account(
                    code=bytes.fromhex(
                        "602060006000600063ead0c0575afa5060005160005500"
                    )
                ),
                callee_4: Account(
                    storage={24743: 48879},
                    code=bytes.fromhex(
                        "5a600052600260005560115a60005103036000525a6020526160a754604052601a5a602051030360205260406000fd00"  # noqa: E501
                    ),
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "5a6000526000600060006000600063dead01115af150617fe85a600051030360005500"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "5a6000526000600060006000600063dead01125af150617fe85a600051030360005500"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "610bad600052602060006000600061f1135afa5060005160005500"  # noqa: E501
                    ),
                ),
                callee_8: Account(
                    code=bytes.fromhex("6020600060006000600061f114610b65f100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6020600060006000600061f115611800f100")
                ),
                callee_10: Account(
                    storage={0: 15, 24743: 57005},
                    code=bytes.fromhex(
                        "600054505a600052600261beef5560115a60005103036000525a6020526160a75460a05260235a60205103036020525a60405261beef60005461f000015560785a60405103036040525a60605260005461f010015450607a5a60605103036060526000516000546101000155602051600054610200015560405160005461030001556060516000546104000155600060005411609b57600060b4565b600160005403600055600060006000600060006110165af15b00"  # noqa: E501
                    ),
                ),
                callee_11: Account(
                    code=bytes.fromhex(
                        "60068060336101003961020052602180603960003961022052610200516101000160006000f0610240526102405160015500fe60ff600055005a60005261ffff6000555a6000510360015561010061010060003960106000f300"  # noqa: E501
                    )
                ),
                callee_12: Account(
                    code=bytes.fromhex(
                        "60068060366101003961020052602180603c60003961022052615a17610200516101000160006000f5610240526102405160015500fe60ff600055005a60005261ffff6000555a6000510360015561010061010060003960106000f300"  # noqa: E501
                    )
                ),
                callee_13: Account(
                    code=bytes.fromhex(
                        "60138060446101003961020052600f80605760003961022052610200516101000160006000f06102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a600051036001550061010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_14: Account(
                    code=bytes.fromhex(
                        "60138060476101003961020052600f80605a60003961022052615a17610200516101000160006000f56102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a600051036001550061010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_15: Account(
                    code=bytes.fromhex(
                        "60138060446101003961020052602180605760003961022052610200516101000160006000f06102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a60005103600255005a60005261ffff6000555a6000510360015561010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_16: Account(
                    code=bytes.fromhex(
                        "60138060476101003961020052602180605a60003961022052615a17610200516101000160006000f56102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a60005103600255005a60005261ffff6000555a6000510360015561010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_17: Account(
                    code=bytes.fromhex(
                        "6000600060006000600061f1265af1506000600060006000600061f1265af100"  # noqa: E501
                    )
                ),
                callee_18: Account(
                    storage={24743: 57005},
                    code=bytes.fromhex(
                        "5a600052600260005560115a60005103036000526000516001555a6000526160a75460205260105a600051030360005260005160025500"  # noqa: E501
                    ),
                ),
                callee_19: Account(
                    code=bytes.fromhex(
                        "63dead60a760005561600d60005260206000f300"
                    )
                ),
                callee_20: Account(
                    storage={0: 2989}, code=bytes.fromhex("61600d60005500")
                ),
                callee_21: Account(
                    storage={0: 2989, 24743: 57005},
                    code=bytes.fromhex("6160a75460005261600d60005500"),
                ),
                callee_22: Account(
                    code=bytes.fromhex(
                        "5a6000526160a76000555a60005103600052600060015414602457600051600255602b565b6000516001555b00"  # noqa: E501
                    )
                ),
                callee_23: Account(code=bytes.fromhex("61dead6000556000ff00")),
                callee_24: Account(
                    storage={0: 0xDEAD0060A7},
                    code=bytes.fromhex("600054506000ff00"),
                ),
                callee_25: Account(
                    storage={24743: 57005},
                    code=bytes.fromhex(
                        "5a6000526160a75460205260135a600051030360005260206000f300"  # noqa: E501
                    ),
                ),
                contract: Account(
                    code=bytes.fromhex(
                        "60406000600060006000600435611000015af15060005160005560205160015500"  # noqa: E501
                    )
                ),
            },
        },
        {
            "indexes": {"data": 27, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex("600060006000600061c0575af400")
                ),
                callee_1: Account(
                    code=bytes.fromhex("6000600060006000600061c0575af100")
                ),
                callee_2: Account(
                    code=bytes.fromhex("6000600060006000600061c0575af200")
                ),
                callee_3: Account(
                    code=bytes.fromhex(
                        "602060006000600063ead0c0575afa5060005160005500"
                    )
                ),
                callee_4: Account(
                    storage={24743: 48879},
                    code=bytes.fromhex(
                        "5a600052600260005560115a60005103036000525a6020526160a754604052601a5a602051030360205260406000fd00"  # noqa: E501
                    ),
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "5a6000526000600060006000600063dead01115af150617fe85a600051030360005500"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "5a6000526000600060006000600063dead01125af150617fe85a600051030360005500"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "610bad600052602060006000600061f1135afa5060005160005500"  # noqa: E501
                    ),
                ),
                callee_8: Account(
                    code=bytes.fromhex("6020600060006000600061f114610b65f100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6020600060006000600061f115611800f100")
                ),
                callee_10: Account(
                    storage={0: 15, 24743: 57005},
                    code=bytes.fromhex(
                        "600054505a600052600261beef5560115a60005103036000525a6020526160a75460a05260235a60205103036020525a60405261beef60005461f000015560785a60405103036040525a60605260005461f010015450607a5a60605103036060526000516000546101000155602051600054610200015560405160005461030001556060516000546104000155600060005411609b57600060b4565b600160005403600055600060006000600060006110165af15b00"  # noqa: E501
                    ),
                ),
                callee_11: Account(
                    code=bytes.fromhex(
                        "60068060336101003961020052602180603960003961022052610200516101000160006000f0610240526102405160015500fe60ff600055005a60005261ffff6000555a6000510360015561010061010060003960106000f300"  # noqa: E501
                    )
                ),
                callee_12: Account(
                    code=bytes.fromhex(
                        "60068060366101003961020052602180603c60003961022052615a17610200516101000160006000f5610240526102405160015500fe60ff600055005a60005261ffff6000555a6000510360015561010061010060003960106000f300"  # noqa: E501
                    )
                ),
                callee_13: Account(
                    code=bytes.fromhex(
                        "60138060446101003961020052600f80605760003961022052610200516101000160006000f06102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a600051036001550061010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_14: Account(
                    code=bytes.fromhex(
                        "60138060476101003961020052600f80605a60003961022052615a17610200516101000160006000f56102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a600051036001550061010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_15: Account(
                    code=bytes.fromhex(
                        "60138060446101003961020052602180605760003961022052610200516101000160006000f06102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a60005103600255005a60005261ffff6000555a6000510360015561010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_16: Account(
                    code=bytes.fromhex(
                        "60138060476101003961020052602180605a60003961022052615a17610200516101000160006000f56102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a60005103600255005a60005261ffff6000555a6000510360015561010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_17: Account(
                    code=bytes.fromhex(
                        "6000600060006000600061f1265af1506000600060006000600061f1265af100"  # noqa: E501
                    )
                ),
                callee_18: Account(
                    storage={24743: 57005},
                    code=bytes.fromhex(
                        "5a600052600260005560115a60005103036000526000516001555a6000526160a75460205260105a600051030360005260005160025500"  # noqa: E501
                    ),
                ),
                callee_19: Account(
                    code=bytes.fromhex(
                        "63dead60a760005561600d60005260206000f300"
                    )
                ),
                callee_20: Account(
                    storage={0: 2989}, code=bytes.fromhex("61600d60005500")
                ),
                callee_21: Account(
                    storage={0: 24589, 24743: 57005},
                    code=bytes.fromhex("6160a75460005261600d60005500"),
                ),
                callee_22: Account(
                    code=bytes.fromhex(
                        "5a6000526160a76000555a60005103600052600060015414602457600051600255602b565b6000516001555b00"  # noqa: E501
                    )
                ),
                callee_23: Account(code=bytes.fromhex("61dead6000556000ff00")),
                callee_24: Account(
                    storage={0: 0xDEAD0060A7},
                    code=bytes.fromhex("600054506000ff00"),
                ),
                callee_25: Account(
                    storage={24743: 57005},
                    code=bytes.fromhex(
                        "5a6000526160a75460205260135a600051030360005260206000f300"  # noqa: E501
                    ),
                ),
                contract: Account(
                    code=bytes.fromhex(
                        "60406000600060006000600435611000015af15060005160005560205160015500"  # noqa: E501
                    )
                ),
            },
        },
        {
            "indexes": {"data": 28, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex("600060006000600061c0575af400")
                ),
                callee_1: Account(
                    code=bytes.fromhex("6000600060006000600061c0575af100")
                ),
                callee_2: Account(
                    code=bytes.fromhex("6000600060006000600061c0575af200")
                ),
                callee_3: Account(
                    code=bytes.fromhex(
                        "602060006000600063ead0c0575afa5060005160005500"
                    )
                ),
                callee_4: Account(
                    storage={24743: 48879},
                    code=bytes.fromhex(
                        "5a600052600260005560115a60005103036000525a6020526160a754604052601a5a602051030360205260406000fd00"  # noqa: E501
                    ),
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "5a6000526000600060006000600063dead01115af150617fe85a600051030360005500"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "5a6000526000600060006000600063dead01125af150617fe85a600051030360005500"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "610bad600052602060006000600061f1135afa5060005160005500"  # noqa: E501
                    ),
                ),
                callee_8: Account(
                    code=bytes.fromhex("6020600060006000600061f114610b65f100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6020600060006000600061f115611800f100")
                ),
                callee_10: Account(
                    storage={
                        256: 103,
                        257: 103,
                        258: 103,
                        259: 103,
                        260: 103,
                        261: 103,
                        262: 103,
                        263: 103,
                        264: 103,
                        265: 103,
                        266: 103,
                        267: 103,
                        268: 103,
                        269: 103,
                        270: 103,
                        271: 22103,
                        512: 100,
                        513: 100,
                        514: 100,
                        515: 100,
                        516: 100,
                        517: 100,
                        518: 100,
                        519: 100,
                        520: 100,
                        521: 100,
                        522: 100,
                        523: 100,
                        524: 100,
                        525: 100,
                        526: 100,
                        527: 2100,
                        768: 22103,
                        769: 22103,
                        770: 22103,
                        771: 22103,
                        772: 22103,
                        773: 22103,
                        774: 22103,
                        775: 22103,
                        776: 22103,
                        777: 22103,
                        778: 22103,
                        779: 22103,
                        780: 22103,
                        781: 22103,
                        782: 22103,
                        783: 22103,
                        1024: 2100,
                        1025: 2100,
                        1026: 2100,
                        1027: 2100,
                        1028: 2100,
                        1029: 2100,
                        1030: 2100,
                        1031: 2100,
                        1032: 2100,
                        1033: 2100,
                        1034: 2100,
                        1035: 2100,
                        1036: 2100,
                        1037: 2100,
                        1038: 2100,
                        1039: 2100,
                        24743: 57005,
                        48879: 2,
                        61440: 48879,
                        61441: 48879,
                        61442: 48879,
                        61443: 48879,
                        61444: 48879,
                        61445: 48879,
                        61446: 48879,
                        61447: 48879,
                        61448: 48879,
                        61449: 48879,
                        61450: 48879,
                        61451: 48879,
                        61452: 48879,
                        61453: 48879,
                        61454: 48879,
                        61455: 48879,
                    },
                    code=bytes.fromhex(
                        "600054505a600052600261beef5560115a60005103036000525a6020526160a75460a05260235a60205103036020525a60405261beef60005461f000015560785a60405103036040525a60605260005461f010015450607a5a60605103036060526000516000546101000155602051600054610200015560405160005461030001556060516000546104000155600060005411609b57600060b4565b600160005403600055600060006000600060006110165af15b00"  # noqa: E501
                    ),
                ),
                callee_11: Account(
                    code=bytes.fromhex(
                        "60068060336101003961020052602180603960003961022052610200516101000160006000f0610240526102405160015500fe60ff600055005a60005261ffff6000555a6000510360015561010061010060003960106000f300"  # noqa: E501
                    )
                ),
                callee_12: Account(
                    code=bytes.fromhex(
                        "60068060366101003961020052602180603c60003961022052615a17610200516101000160006000f5610240526102405160015500fe60ff600055005a60005261ffff6000555a6000510360015561010061010060003960106000f300"  # noqa: E501
                    )
                ),
                callee_13: Account(
                    code=bytes.fromhex(
                        "60138060446101003961020052600f80605760003961022052610200516101000160006000f06102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a600051036001550061010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_14: Account(
                    code=bytes.fromhex(
                        "60138060476101003961020052600f80605a60003961022052615a17610200516101000160006000f56102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a600051036001550061010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_15: Account(
                    code=bytes.fromhex(
                        "60138060446101003961020052602180605760003961022052610200516101000160006000f06102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a60005103600255005a60005261ffff6000555a6000510360015561010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_16: Account(
                    code=bytes.fromhex(
                        "60138060476101003961020052602180605a60003961022052615a17610200516101000160006000f56102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a60005103600255005a60005261ffff6000555a6000510360015561010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_17: Account(
                    code=bytes.fromhex(
                        "6000600060006000600061f1265af1506000600060006000600061f1265af100"  # noqa: E501
                    )
                ),
                callee_18: Account(
                    storage={24743: 57005},
                    code=bytes.fromhex(
                        "5a600052600260005560115a60005103036000526000516001555a6000526160a75460205260105a600051030360005260005160025500"  # noqa: E501
                    ),
                ),
                callee_19: Account(
                    code=bytes.fromhex(
                        "63dead60a760005561600d60005260206000f300"
                    )
                ),
                callee_20: Account(
                    storage={0: 2989}, code=bytes.fromhex("61600d60005500")
                ),
                callee_21: Account(
                    storage={0: 2989, 24743: 57005},
                    code=bytes.fromhex("6160a75460005261600d60005500"),
                ),
                callee_22: Account(
                    code=bytes.fromhex(
                        "5a6000526160a76000555a60005103600052600060015414602457600051600255602b565b6000516001555b00"  # noqa: E501
                    )
                ),
                callee_23: Account(code=bytes.fromhex("61dead6000556000ff00")),
                callee_24: Account(
                    storage={0: 0xDEAD0060A7},
                    code=bytes.fromhex("600054506000ff00"),
                ),
                callee_25: Account(
                    storage={24743: 57005},
                    code=bytes.fromhex(
                        "5a6000526160a75460205260135a600051030360005260206000f300"  # noqa: E501
                    ),
                ),
                contract: Account(
                    code=bytes.fromhex(
                        "60406000600060006000600435611000015af15060005160005560205160015500"  # noqa: E501
                    )
                ),
            },
        },
        {
            "indexes": {"data": 29, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex("600060006000600061c0575af400")
                ),
                callee_1: Account(
                    code=bytes.fromhex("6000600060006000600061c0575af100")
                ),
                callee_2: Account(
                    code=bytes.fromhex("6000600060006000600061c0575af200")
                ),
                callee_3: Account(
                    code=bytes.fromhex(
                        "602060006000600063ead0c0575afa5060005160005500"
                    )
                ),
                callee_4: Account(
                    storage={24743: 48879},
                    code=bytes.fromhex(
                        "5a600052600260005560115a60005103036000525a6020526160a754604052601a5a602051030360205260406000fd00"  # noqa: E501
                    ),
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "5a6000526000600060006000600063dead01115af150617fe85a600051030360005500"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "5a6000526000600060006000600063dead01125af150617fe85a600051030360005500"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "610bad600052602060006000600061f1135afa5060005160005500"  # noqa: E501
                    ),
                ),
                callee_8: Account(
                    code=bytes.fromhex("6020600060006000600061f114610b65f100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6020600060006000600061f115611800f100")
                ),
                callee_10: Account(
                    storage={
                        256: 103,
                        257: 103,
                        258: 103,
                        259: 103,
                        260: 103,
                        261: 103,
                        262: 103,
                        263: 103,
                        264: 103,
                        265: 103,
                        266: 103,
                        267: 103,
                        268: 103,
                        269: 103,
                        270: 103,
                        271: 20003,
                        512: 100,
                        513: 100,
                        514: 100,
                        515: 100,
                        516: 100,
                        517: 100,
                        518: 100,
                        519: 100,
                        520: 100,
                        521: 100,
                        522: 100,
                        523: 100,
                        524: 100,
                        525: 100,
                        526: 100,
                        527: 100,
                        768: 20003,
                        769: 20003,
                        770: 20003,
                        771: 20003,
                        772: 20003,
                        773: 20003,
                        774: 20003,
                        775: 20003,
                        776: 20003,
                        777: 20003,
                        778: 20003,
                        779: 20003,
                        780: 20003,
                        781: 20003,
                        782: 20003,
                        783: 20003,
                        1024: 100,
                        1025: 100,
                        1026: 100,
                        1027: 100,
                        1028: 100,
                        1029: 100,
                        1030: 100,
                        1031: 100,
                        1032: 100,
                        1033: 100,
                        1034: 100,
                        1035: 100,
                        1036: 100,
                        1037: 100,
                        1038: 100,
                        1039: 100,
                        24743: 57005,
                        48879: 2,
                        61440: 48879,
                        61441: 48879,
                        61442: 48879,
                        61443: 48879,
                        61444: 48879,
                        61445: 48879,
                        61446: 48879,
                        61447: 48879,
                        61448: 48879,
                        61449: 48879,
                        61450: 48879,
                        61451: 48879,
                        61452: 48879,
                        61453: 48879,
                        61454: 48879,
                        61455: 48879,
                    },
                    code=bytes.fromhex(
                        "600054505a600052600261beef5560115a60005103036000525a6020526160a75460a05260235a60205103036020525a60405261beef60005461f000015560785a60405103036040525a60605260005461f010015450607a5a60605103036060526000516000546101000155602051600054610200015560405160005461030001556060516000546104000155600060005411609b57600060b4565b600160005403600055600060006000600060006110165af15b00"  # noqa: E501
                    ),
                ),
                callee_11: Account(
                    code=bytes.fromhex(
                        "60068060336101003961020052602180603960003961022052610200516101000160006000f0610240526102405160015500fe60ff600055005a60005261ffff6000555a6000510360015561010061010060003960106000f300"  # noqa: E501
                    )
                ),
                callee_12: Account(
                    code=bytes.fromhex(
                        "60068060366101003961020052602180603c60003961022052615a17610200516101000160006000f5610240526102405160015500fe60ff600055005a60005261ffff6000555a6000510360015561010061010060003960106000f300"  # noqa: E501
                    )
                ),
                callee_13: Account(
                    code=bytes.fromhex(
                        "60138060446101003961020052600f80605760003961022052610200516101000160006000f06102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a600051036001550061010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_14: Account(
                    code=bytes.fromhex(
                        "60138060476101003961020052600f80605a60003961022052615a17610200516101000160006000f56102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a600051036001550061010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_15: Account(
                    code=bytes.fromhex(
                        "60138060446101003961020052602180605760003961022052610200516101000160006000f06102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a60005103600255005a60005261ffff6000555a6000510360015561010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_16: Account(
                    code=bytes.fromhex(
                        "60138060476101003961020052602180605a60003961022052615a17610200516101000160006000f56102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a60005103600255005a60005261ffff6000555a6000510360015561010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_17: Account(
                    code=bytes.fromhex(
                        "6000600060006000600061f1265af1506000600060006000600061f1265af100"  # noqa: E501
                    )
                ),
                callee_18: Account(
                    storage={24743: 57005},
                    code=bytes.fromhex(
                        "5a600052600260005560115a60005103036000526000516001555a6000526160a75460205260105a600051030360005260005160025500"  # noqa: E501
                    ),
                ),
                callee_19: Account(
                    code=bytes.fromhex(
                        "63dead60a760005561600d60005260206000f300"
                    )
                ),
                callee_20: Account(
                    storage={0: 2989}, code=bytes.fromhex("61600d60005500")
                ),
                callee_21: Account(
                    storage={0: 2989, 24743: 57005},
                    code=bytes.fromhex("6160a75460005261600d60005500"),
                ),
                callee_22: Account(
                    code=bytes.fromhex(
                        "5a6000526160a76000555a60005103600052600060015414602457600051600255602b565b6000516001555b00"  # noqa: E501
                    )
                ),
                callee_23: Account(code=bytes.fromhex("61dead6000556000ff00")),
                callee_24: Account(
                    storage={0: 0xDEAD0060A7},
                    code=bytes.fromhex("600054506000ff00"),
                ),
                callee_25: Account(
                    storage={24743: 57005},
                    code=bytes.fromhex(
                        "5a6000526160a75460205260135a600051030360005260206000f300"  # noqa: E501
                    ),
                ),
                contract: Account(
                    code=bytes.fromhex(
                        "60406000600060006000600435611000015af15060005160005560205160015500"  # noqa: E501
                    )
                ),
            },
        },
        {
            "indexes": {"data": 30, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex("600060006000600061c0575af400")
                ),
                callee_1: Account(
                    code=bytes.fromhex("6000600060006000600061c0575af100")
                ),
                callee_2: Account(
                    code=bytes.fromhex("6000600060006000600061c0575af200")
                ),
                callee_3: Account(
                    code=bytes.fromhex(
                        "602060006000600063ead0c0575afa5060005160005500"
                    )
                ),
                callee_4: Account(
                    storage={24743: 48879},
                    code=bytes.fromhex(
                        "5a600052600260005560115a60005103036000525a6020526160a754604052601a5a602051030360205260406000fd00"  # noqa: E501
                    ),
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "5a6000526000600060006000600063dead01115af150617fe85a600051030360005500"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "5a6000526000600060006000600063dead01125af150617fe85a600051030360005500"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    storage={0: 2989},
                    code=bytes.fromhex(
                        "610bad600052602060006000600061f1135afa5060005160005500"  # noqa: E501
                    ),
                ),
                callee_8: Account(
                    code=bytes.fromhex("6020600060006000600061f114610b65f100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6020600060006000600061f115611800f100")
                ),
                callee_10: Account(
                    storage={0: 15, 24743: 57005},
                    code=bytes.fromhex(
                        "600054505a600052600261beef5560115a60005103036000525a6020526160a75460a05260235a60205103036020525a60405261beef60005461f000015560785a60405103036040525a60605260005461f010015450607a5a60605103036060526000516000546101000155602051600054610200015560405160005461030001556060516000546104000155600060005411609b57600060b4565b600160005403600055600060006000600060006110165af15b00"  # noqa: E501
                    ),
                ),
                callee_11: Account(
                    code=bytes.fromhex(
                        "60068060336101003961020052602180603960003961022052610200516101000160006000f0610240526102405160015500fe60ff600055005a60005261ffff6000555a6000510360015561010061010060003960106000f300"  # noqa: E501
                    )
                ),
                callee_12: Account(
                    code=bytes.fromhex(
                        "60068060366101003961020052602180603c60003961022052615a17610200516101000160006000f5610240526102405160015500fe60ff600055005a60005261ffff6000555a6000510360015561010061010060003960106000f300"  # noqa: E501
                    )
                ),
                callee_13: Account(
                    code=bytes.fromhex(
                        "60138060446101003961020052600f80605760003961022052610200516101000160006000f06102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a600051036001550061010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_14: Account(
                    code=bytes.fromhex(
                        "60138060476101003961020052600f80605a60003961022052615a17610200516101000160006000f56102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a600051036001550061010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_15: Account(
                    code=bytes.fromhex(
                        "60138060446101003961020052602180605760003961022052610200516101000160006000f06102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a60005103600255005a60005261ffff6000555a6000510360015561010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_16: Account(
                    code=bytes.fromhex(
                        "60138060476101003961020052602180605a60003961022052615a17610200516101000160006000f56102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a60005103600255005a60005261ffff6000555a6000510360015561010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_17: Account(
                    code=bytes.fromhex(
                        "6000600060006000600061f1265af1506000600060006000600061f1265af100"  # noqa: E501
                    )
                ),
                callee_18: Account(
                    storage={24743: 57005},
                    code=bytes.fromhex(
                        "5a600052600260005560115a60005103036000526000516001555a6000526160a75460205260105a600051030360005260005160025500"  # noqa: E501
                    ),
                ),
                callee_19: Account(
                    code=bytes.fromhex(
                        "63dead60a760005561600d60005260206000f300"
                    )
                ),
                callee_20: Account(
                    storage={0: 2989}, code=bytes.fromhex("61600d60005500")
                ),
                callee_21: Account(
                    storage={0: 2989, 24743: 57005},
                    code=bytes.fromhex("6160a75460005261600d60005500"),
                ),
                callee_22: Account(
                    code=bytes.fromhex(
                        "5a6000526160a76000555a60005103600052600060015414602457600051600255602b565b6000516001555b00"  # noqa: E501
                    )
                ),
                callee_23: Account(code=bytes.fromhex("61dead6000556000ff00")),
                callee_24: Account(
                    storage={0: 0xDEAD0060A7},
                    code=bytes.fromhex("600054506000ff00"),
                ),
                callee_25: Account(
                    storage={24743: 57005},
                    code=bytes.fromhex(
                        "5a6000526160a75460205260135a600051030360005260206000f300"  # noqa: E501
                    ),
                ),
                contract: Account(
                    code=bytes.fromhex(
                        "60406000600060006000600435611000015af15060005160005560205160015500"  # noqa: E501
                    )
                ),
            },
        },
        {
            "indexes": {"data": 31, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex("600060006000600061c0575af400")
                ),
                callee_1: Account(
                    code=bytes.fromhex("6000600060006000600061c0575af100")
                ),
                callee_2: Account(
                    code=bytes.fromhex("6000600060006000600061c0575af200")
                ),
                callee_3: Account(
                    code=bytes.fromhex(
                        "602060006000600063ead0c0575afa5060005160005500"
                    )
                ),
                callee_4: Account(
                    storage={24743: 48879},
                    code=bytes.fromhex(
                        "5a600052600260005560115a60005103036000525a6020526160a754604052601a5a602051030360205260406000fd00"  # noqa: E501
                    ),
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "5a6000526000600060006000600063dead01115af150617fe85a600051030360005500"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "5a6000526000600060006000600063dead01125af150617fe85a600051030360005500"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    storage={0: 2989},
                    code=bytes.fromhex(
                        "610bad600052602060006000600061f1135afa5060005160005500"  # noqa: E501
                    ),
                ),
                callee_8: Account(
                    code=bytes.fromhex("6020600060006000600061f114610b65f100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6020600060006000600061f115611800f100")
                ),
                callee_10: Account(
                    storage={0: 15, 24743: 57005},
                    code=bytes.fromhex(
                        "600054505a600052600261beef5560115a60005103036000525a6020526160a75460a05260235a60205103036020525a60405261beef60005461f000015560785a60405103036040525a60605260005461f010015450607a5a60605103036060526000516000546101000155602051600054610200015560405160005461030001556060516000546104000155600060005411609b57600060b4565b600160005403600055600060006000600060006110165af15b00"  # noqa: E501
                    ),
                ),
                callee_11: Account(
                    code=bytes.fromhex(
                        "60068060336101003961020052602180603960003961022052610200516101000160006000f0610240526102405160015500fe60ff600055005a60005261ffff6000555a6000510360015561010061010060003960106000f300"  # noqa: E501
                    )
                ),
                callee_12: Account(
                    code=bytes.fromhex(
                        "60068060366101003961020052602180603c60003961022052615a17610200516101000160006000f5610240526102405160015500fe60ff600055005a60005261ffff6000555a6000510360015561010061010060003960106000f300"  # noqa: E501
                    )
                ),
                callee_13: Account(
                    code=bytes.fromhex(
                        "60138060446101003961020052600f80605760003961022052610200516101000160006000f06102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a600051036001550061010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_14: Account(
                    code=bytes.fromhex(
                        "60138060476101003961020052600f80605a60003961022052615a17610200516101000160006000f56102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a600051036001550061010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_15: Account(
                    code=bytes.fromhex(
                        "60138060446101003961020052602180605760003961022052610200516101000160006000f06102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a60005103600255005a60005261ffff6000555a6000510360015561010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_16: Account(
                    code=bytes.fromhex(
                        "60138060476101003961020052602180605a60003961022052615a17610200516101000160006000f56102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a60005103600255005a60005261ffff6000555a6000510360015561010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_17: Account(
                    code=bytes.fromhex(
                        "6000600060006000600061f1265af1506000600060006000600061f1265af100"  # noqa: E501
                    )
                ),
                callee_18: Account(
                    storage={24743: 57005},
                    code=bytes.fromhex(
                        "5a600052600260005560115a60005103036000526000516001555a6000526160a75460205260105a600051030360005260005160025500"  # noqa: E501
                    ),
                ),
                callee_19: Account(
                    code=bytes.fromhex(
                        "63dead60a760005561600d60005260206000f300"
                    )
                ),
                callee_20: Account(
                    storage={0: 2989}, code=bytes.fromhex("61600d60005500")
                ),
                callee_21: Account(
                    storage={0: 2989, 24743: 57005},
                    code=bytes.fromhex("6160a75460005261600d60005500"),
                ),
                callee_22: Account(
                    code=bytes.fromhex(
                        "5a6000526160a76000555a60005103600052600060015414602457600051600255602b565b6000516001555b00"  # noqa: E501
                    )
                ),
                callee_23: Account(code=bytes.fromhex("61dead6000556000ff00")),
                callee_24: Account(
                    storage={0: 0xDEAD0060A7},
                    code=bytes.fromhex("600054506000ff00"),
                ),
                callee_25: Account(
                    storage={24743: 57005},
                    code=bytes.fromhex(
                        "5a6000526160a75460205260135a600051030360005260206000f300"  # noqa: E501
                    ),
                ),
                contract: Account(
                    code=bytes.fromhex(
                        "60406000600060006000600435611000015af15060005160005560205160015500"  # noqa: E501
                    )
                ),
            },
        },
        {
            "indexes": {"data": 32, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex("600060006000600061c0575af400")
                ),
                callee_1: Account(
                    code=bytes.fromhex("6000600060006000600061c0575af100")
                ),
                callee_2: Account(
                    code=bytes.fromhex("6000600060006000600061c0575af200")
                ),
                callee_3: Account(
                    storage={0: 107},
                    code=bytes.fromhex(
                        "602060006000600063ead0c0575afa5060005160005500"
                    ),
                ),
                callee_4: Account(
                    storage={24743: 48879},
                    code=bytes.fromhex(
                        "5a600052600260005560115a60005103036000525a6020526160a754604052601a5a602051030360205260406000fd00"  # noqa: E501
                    ),
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "5a6000526000600060006000600063dead01115af150617fe85a600051030360005500"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "5a6000526000600060006000600063dead01125af150617fe85a600051030360005500"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "610bad600052602060006000600061f1135afa5060005160005500"  # noqa: E501
                    ),
                ),
                callee_8: Account(
                    code=bytes.fromhex("6020600060006000600061f114610b65f100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6020600060006000600061f115611800f100")
                ),
                callee_10: Account(
                    storage={0: 15, 24743: 57005},
                    code=bytes.fromhex(
                        "600054505a600052600261beef5560115a60005103036000525a6020526160a75460a05260235a60205103036020525a60405261beef60005461f000015560785a60405103036040525a60605260005461f010015450607a5a60605103036060526000516000546101000155602051600054610200015560405160005461030001556060516000546104000155600060005411609b57600060b4565b600160005403600055600060006000600060006110165af15b00"  # noqa: E501
                    ),
                ),
                callee_11: Account(
                    code=bytes.fromhex(
                        "60068060336101003961020052602180603960003961022052610200516101000160006000f0610240526102405160015500fe60ff600055005a60005261ffff6000555a6000510360015561010061010060003960106000f300"  # noqa: E501
                    )
                ),
                callee_12: Account(
                    code=bytes.fromhex(
                        "60068060366101003961020052602180603c60003961022052615a17610200516101000160006000f5610240526102405160015500fe60ff600055005a60005261ffff6000555a6000510360015561010061010060003960106000f300"  # noqa: E501
                    )
                ),
                callee_13: Account(
                    code=bytes.fromhex(
                        "60138060446101003961020052600f80605760003961022052610200516101000160006000f06102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a600051036001550061010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_14: Account(
                    code=bytes.fromhex(
                        "60138060476101003961020052600f80605a60003961022052615a17610200516101000160006000f56102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a600051036001550061010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_15: Account(
                    code=bytes.fromhex(
                        "60138060446101003961020052602180605760003961022052610200516101000160006000f06102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a60005103600255005a60005261ffff6000555a6000510360015561010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_16: Account(
                    code=bytes.fromhex(
                        "60138060476101003961020052602180605a60003961022052615a17610200516101000160006000f56102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a60005103600255005a60005261ffff6000555a6000510360015561010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_17: Account(
                    code=bytes.fromhex(
                        "6000600060006000600061f1265af1506000600060006000600061f1265af100"  # noqa: E501
                    )
                ),
                callee_18: Account(
                    storage={24743: 57005},
                    code=bytes.fromhex(
                        "5a600052600260005560115a60005103036000526000516001555a6000526160a75460205260105a600051030360005260005160025500"  # noqa: E501
                    ),
                ),
                callee_19: Account(
                    code=bytes.fromhex(
                        "63dead60a760005561600d60005260206000f300"
                    )
                ),
                callee_20: Account(
                    storage={0: 2989}, code=bytes.fromhex("61600d60005500")
                ),
                callee_21: Account(
                    storage={0: 2989, 24743: 57005},
                    code=bytes.fromhex("6160a75460005261600d60005500"),
                ),
                callee_22: Account(
                    code=bytes.fromhex(
                        "5a6000526160a76000555a60005103600052600060015414602457600051600255602b565b6000516001555b00"  # noqa: E501
                    )
                ),
                callee_23: Account(code=bytes.fromhex("61dead6000556000ff00")),
                callee_24: Account(
                    storage={0: 0xDEAD0060A7},
                    code=bytes.fromhex("600054506000ff00"),
                ),
                callee_25: Account(
                    storage={24743: 57005},
                    code=bytes.fromhex(
                        "5a6000526160a75460205260135a600051030360005260206000f300"  # noqa: E501
                    ),
                ),
                contract: Account(
                    code=bytes.fromhex(
                        "60406000600060006000600435611000015af15060005160005560205160015500"  # noqa: E501
                    )
                ),
            },
        },
        {
            "indexes": {"data": 33, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex("600060006000600061c0575af400")
                ),
                callee_1: Account(
                    code=bytes.fromhex("6000600060006000600061c0575af100")
                ),
                callee_2: Account(
                    code=bytes.fromhex("6000600060006000600061c0575af200")
                ),
                callee_3: Account(
                    storage={0: 2107},
                    code=bytes.fromhex(
                        "602060006000600063ead0c0575afa5060005160005500"
                    ),
                ),
                callee_4: Account(
                    storage={24743: 48879},
                    code=bytes.fromhex(
                        "5a600052600260005560115a60005103036000525a6020526160a754604052601a5a602051030360205260406000fd00"  # noqa: E501
                    ),
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "5a6000526000600060006000600063dead01115af150617fe85a600051030360005500"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "5a6000526000600060006000600063dead01125af150617fe85a600051030360005500"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "610bad600052602060006000600061f1135afa5060005160005500"  # noqa: E501
                    ),
                ),
                callee_8: Account(
                    code=bytes.fromhex("6020600060006000600061f114610b65f100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6020600060006000600061f115611800f100")
                ),
                callee_10: Account(
                    storage={0: 15, 24743: 57005},
                    code=bytes.fromhex(
                        "600054505a600052600261beef5560115a60005103036000525a6020526160a75460a05260235a60205103036020525a60405261beef60005461f000015560785a60405103036040525a60605260005461f010015450607a5a60605103036060526000516000546101000155602051600054610200015560405160005461030001556060516000546104000155600060005411609b57600060b4565b600160005403600055600060006000600060006110165af15b00"  # noqa: E501
                    ),
                ),
                callee_11: Account(
                    code=bytes.fromhex(
                        "60068060336101003961020052602180603960003961022052610200516101000160006000f0610240526102405160015500fe60ff600055005a60005261ffff6000555a6000510360015561010061010060003960106000f300"  # noqa: E501
                    )
                ),
                callee_12: Account(
                    code=bytes.fromhex(
                        "60068060366101003961020052602180603c60003961022052615a17610200516101000160006000f5610240526102405160015500fe60ff600055005a60005261ffff6000555a6000510360015561010061010060003960106000f300"  # noqa: E501
                    )
                ),
                callee_13: Account(
                    code=bytes.fromhex(
                        "60138060446101003961020052600f80605760003961022052610200516101000160006000f06102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a600051036001550061010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_14: Account(
                    code=bytes.fromhex(
                        "60138060476101003961020052600f80605a60003961022052615a17610200516101000160006000f56102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a600051036001550061010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_15: Account(
                    code=bytes.fromhex(
                        "60138060446101003961020052602180605760003961022052610200516101000160006000f06102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a60005103600255005a60005261ffff6000555a6000510360015561010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_16: Account(
                    code=bytes.fromhex(
                        "60138060476101003961020052602180605a60003961022052615a17610200516101000160006000f56102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a60005103600255005a60005261ffff6000555a6000510360015561010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_17: Account(
                    code=bytes.fromhex(
                        "6000600060006000600061f1265af1506000600060006000600061f1265af100"  # noqa: E501
                    )
                ),
                callee_18: Account(
                    storage={24743: 57005},
                    code=bytes.fromhex(
                        "5a600052600260005560115a60005103036000526000516001555a6000526160a75460205260105a600051030360005260005160025500"  # noqa: E501
                    ),
                ),
                callee_19: Account(
                    code=bytes.fromhex(
                        "63dead60a760005561600d60005260206000f300"
                    )
                ),
                callee_20: Account(
                    storage={0: 2989}, code=bytes.fromhex("61600d60005500")
                ),
                callee_21: Account(
                    storage={0: 2989, 24743: 57005},
                    code=bytes.fromhex("6160a75460005261600d60005500"),
                ),
                callee_22: Account(
                    code=bytes.fromhex(
                        "5a6000526160a76000555a60005103600052600060015414602457600051600255602b565b6000516001555b00"  # noqa: E501
                    )
                ),
                callee_23: Account(code=bytes.fromhex("61dead6000556000ff00")),
                callee_24: Account(
                    storage={0: 0xDEAD0060A7},
                    code=bytes.fromhex("600054506000ff00"),
                ),
                callee_25: Account(
                    storage={24743: 57005},
                    code=bytes.fromhex(
                        "5a6000526160a75460205260135a600051030360005260206000f300"  # noqa: E501
                    ),
                ),
                contract: Account(
                    code=bytes.fromhex(
                        "60406000600060006000600435611000015af15060005160005560205160015500"  # noqa: E501
                    )
                ),
            },
        },
        {
            "indexes": {"data": 34, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex("600060006000600061c0575af400")
                ),
                callee_1: Account(
                    code=bytes.fromhex("6000600060006000600061c0575af100")
                ),
                callee_2: Account(
                    code=bytes.fromhex("6000600060006000600061c0575af200")
                ),
                callee_3: Account(
                    code=bytes.fromhex(
                        "602060006000600063ead0c0575afa5060005160005500"
                    )
                ),
                callee_4: Account(
                    storage={24743: 48879},
                    code=bytes.fromhex(
                        "5a600052600260005560115a60005103036000525a6020526160a754604052601a5a602051030360205260406000fd00"  # noqa: E501
                    ),
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "5a6000526000600060006000600063dead01115af150617fe85a600051030360005500"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "5a6000526000600060006000600063dead01125af150617fe85a600051030360005500"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "610bad600052602060006000600061f1135afa5060005160005500"  # noqa: E501
                    ),
                ),
                callee_8: Account(
                    code=bytes.fromhex("6020600060006000600061f114610b65f100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6020600060006000600061f115611800f100")
                ),
                callee_10: Account(
                    storage={0: 15, 24743: 57005},
                    code=bytes.fromhex(
                        "600054505a600052600261beef5560115a60005103036000525a6020526160a75460a05260235a60205103036020525a60405261beef60005461f000015560785a60405103036040525a60605260005461f010015450607a5a60605103036060526000516000546101000155602051600054610200015560405160005461030001556060516000546104000155600060005411609b57600060b4565b600160005403600055600060006000600060006110165af15b00"  # noqa: E501
                    ),
                ),
                callee_11: Account(
                    code=bytes.fromhex(
                        "60068060336101003961020052602180603960003961022052610200516101000160006000f0610240526102405160015500fe60ff600055005a60005261ffff6000555a6000510360015561010061010060003960106000f300"  # noqa: E501
                    )
                ),
                callee_12: Account(
                    code=bytes.fromhex(
                        "60068060366101003961020052602180603c60003961022052615a17610200516101000160006000f5610240526102405160015500fe60ff600055005a60005261ffff6000555a6000510360015561010061010060003960106000f300"  # noqa: E501
                    )
                ),
                callee_13: Account(
                    code=bytes.fromhex(
                        "60138060446101003961020052600f80605760003961022052610200516101000160006000f06102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a600051036001550061010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_14: Account(
                    code=bytes.fromhex(
                        "60138060476101003961020052600f80605a60003961022052615a17610200516101000160006000f56102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a600051036001550061010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_15: Account(
                    code=bytes.fromhex(
                        "60138060446101003961020052602180605760003961022052610200516101000160006000f06102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a60005103600255005a60005261ffff6000555a6000510360015561010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_16: Account(
                    code=bytes.fromhex(
                        "60138060476101003961020052602180605a60003961022052615a17610200516101000160006000f56102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a60005103600255005a60005261ffff6000555a6000510360015561010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_17: Account(
                    code=bytes.fromhex(
                        "6000600060006000600061f1265af1506000600060006000600061f1265af100"  # noqa: E501
                    )
                ),
                callee_18: Account(
                    storage={24743: 57005},
                    code=bytes.fromhex(
                        "5a600052600260005560115a60005103036000526000516001555a6000526160a75460205260105a600051030360005260005160025500"  # noqa: E501
                    ),
                ),
                callee_19: Account(
                    code=bytes.fromhex(
                        "63dead60a760005561600d60005260206000f300"
                    )
                ),
                callee_20: Account(
                    storage={0: 2989}, code=bytes.fromhex("61600d60005500")
                ),
                callee_21: Account(
                    storage={0: 2989, 24743: 57005},
                    code=bytes.fromhex("6160a75460005261600d60005500"),
                ),
                callee_22: Account(
                    code=bytes.fromhex(
                        "5a6000526160a76000555a60005103600052600060015414602457600051600255602b565b6000516001555b00"  # noqa: E501
                    )
                ),
                callee_23: Account(code=bytes.fromhex("61dead6000556000ff00")),
                callee_24: Account(
                    storage={0: 0xDEAD0060A7},
                    code=bytes.fromhex("600054506000ff00"),
                ),
                callee_25: Account(
                    storage={24743: 57005},
                    code=bytes.fromhex(
                        "5a6000526160a75460205260135a600051030360005260206000f300"  # noqa: E501
                    ),
                ),
                contract: Account(
                    code=bytes.fromhex(
                        "60406000600060006000600435611000015af15060005160005560205160015500"  # noqa: E501
                    )
                ),
            },
        },
        {
            "indexes": {"data": 35, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex("600060006000600061c0575af400")
                ),
                callee_1: Account(
                    code=bytes.fromhex("6000600060006000600061c0575af100")
                ),
                callee_2: Account(
                    code=bytes.fromhex("6000600060006000600061c0575af200")
                ),
                callee_3: Account(
                    code=bytes.fromhex(
                        "602060006000600063ead0c0575afa5060005160005500"
                    )
                ),
                callee_4: Account(
                    storage={24743: 48879},
                    code=bytes.fromhex(
                        "5a600052600260005560115a60005103036000525a6020526160a754604052601a5a602051030360205260406000fd00"  # noqa: E501
                    ),
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "5a6000526000600060006000600063dead01115af150617fe85a600051030360005500"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "5a6000526000600060006000600063dead01125af150617fe85a600051030360005500"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "610bad600052602060006000600061f1135afa5060005160005500"  # noqa: E501
                    ),
                ),
                callee_8: Account(
                    code=bytes.fromhex("6020600060006000600061f114610b65f100")
                ),
                callee_9: Account(
                    code=bytes.fromhex("6020600060006000600061f115611800f100")
                ),
                callee_10: Account(
                    storage={0: 15, 24743: 57005},
                    code=bytes.fromhex(
                        "600054505a600052600261beef5560115a60005103036000525a6020526160a75460a05260235a60205103036020525a60405261beef60005461f000015560785a60405103036040525a60605260005461f010015450607a5a60605103036060526000516000546101000155602051600054610200015560405160005461030001556060516000546104000155600060005411609b57600060b4565b600160005403600055600060006000600060006110165af15b00"  # noqa: E501
                    ),
                ),
                callee_11: Account(
                    code=bytes.fromhex(
                        "60068060336101003961020052602180603960003961022052610200516101000160006000f0610240526102405160015500fe60ff600055005a60005261ffff6000555a6000510360015561010061010060003960106000f300"  # noqa: E501
                    )
                ),
                callee_12: Account(
                    code=bytes.fromhex(
                        "60068060366101003961020052602180603c60003961022052615a17610200516101000160006000f5610240526102405160015500fe60ff600055005a60005261ffff6000555a6000510360015561010061010060003960106000f300"  # noqa: E501
                    )
                ),
                callee_13: Account(
                    code=bytes.fromhex(
                        "60138060446101003961020052600f80605760003961022052610200516101000160006000f06102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a600051036001550061010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_14: Account(
                    code=bytes.fromhex(
                        "60138060476101003961020052600f80605a60003961022052615a17610200516101000160006000f56102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a600051036001550061010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_15: Account(
                    code=bytes.fromhex(
                        "60138060446101003961020052602180605760003961022052610200516101000160006000f06102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a60005103600255005a60005261ffff6000555a6000510360015561010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_16: Account(
                    code=bytes.fromhex(
                        "60138060476101003961020052602180605a60003961022052615a17610200516101000160006000f56102405260006000600060006000610240515af1506102405160015500fe5a60005261ffff6000555a60005103600255005a60005261ffff6000555a6000510360015561010061010060003960806000f300"  # noqa: E501
                    )
                ),
                callee_17: Account(
                    code=bytes.fromhex(
                        "6000600060006000600061f1265af1506000600060006000600061f1265af100"  # noqa: E501
                    )
                ),
                callee_18: Account(
                    storage={24743: 57005},
                    code=bytes.fromhex(
                        "5a600052600260005560115a60005103036000526000516001555a6000526160a75460205260105a600051030360005260005160025500"  # noqa: E501
                    ),
                ),
                callee_19: Account(
                    code=bytes.fromhex(
                        "63dead60a760005561600d60005260206000f300"
                    )
                ),
                callee_20: Account(
                    storage={0: 24589}, code=bytes.fromhex("61600d60005500")
                ),
                callee_21: Account(
                    storage={0: 2989, 24743: 57005},
                    code=bytes.fromhex("6160a75460005261600d60005500"),
                ),
                callee_22: Account(
                    code=bytes.fromhex(
                        "5a6000526160a76000555a60005103600052600060015414602457600051600255602b565b6000516001555b00"  # noqa: E501
                    )
                ),
                callee_23: Account(code=bytes.fromhex("61dead6000556000ff00")),
                callee_24: Account(
                    storage={0: 0xDEAD0060A7},
                    code=bytes.fromhex("600054506000ff00"),
                ),
                callee_25: Account(
                    storage={24743: 57005},
                    code=bytes.fromhex(
                        "5a6000526160a75460205260135a600051030360005260206000f300"  # noqa: E501
                    ),
                ),
                contract: Account(
                    code=bytes.fromhex(
                        "60406000600060006000600435611000015af15060005160005560205160015500"  # noqa: E501
                    )
                ),
            },
        },
    ]

    post, _exc = resolve_expect_post(EXPECT_ENTRIES, d, g, v, fork)

    tx = Transaction(
        sender=sender,
        to=contract,
        data=_tx_data(d),
        gas_limit=TX_GAS[g],
        value=TX_VALUE[v],
        access_list=tx_access_list,
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
