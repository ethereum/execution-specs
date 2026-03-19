"""
Ori Pomerantz qbzzt1@gmail.com.

Ported from:
tests/static/state_tests/stEIP2930/storageCostsFiller.yml
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
    "693c61390000000000000000000000000000000000000000000000000000000000000002",
    "693c61390000000000000000000000000000000000000000000000000000000000000005",
    "693c61390000000000000000000000000000000000000000000000000000000000000004",
    "693c61390000000000000000000000000000000000000000000000000000000000000001",
    "693c61390000000000000000000000000000000000000000000000000000000000000021",
    "693c61390000000000000000000000000000000000000000000000000000000000000011",
    "693c61390000000000000000000000000000000000000000000000000000000000000003",
    "693c61390000000000000000000000000000000000000000000000000000000000000000",
    "693c61390000000000000000000000000000000000000000000000000000000000000000",
    "693c61390000000000000000000000000000000000000000000000000000000000000020",
    "693c61390000000000000000000000000000000000000000000000000000000000000010",
    "693c61390000000000000000000000000000000000000000000000000000000000000fff",
    "693c61390000000000000000000000000000000000000000000000000000000000000002",
    "693c61390000000000000000000000000000000000000000000000000000000000000002",
    "",
    "693c61390000000000000000000000000000000000000000000000000000000000000004",
    "693c61390000000000000000000000000000000000000000000000000000000000000004",
    "693c61390000000000000000000000000000000000000000000000000000000000000005",
    "693c61390000000000000000000000000000000000000000000000000000000000000005",
    "693c61390000000000000000000000000000000000000000000000000000000000000001",
    "693c61390000000000000000000000000000000000000000000000000000000000000002",
    "693c61390000000000000000000000000000000000000000000000000000000000000001",
    "693c61390000000000000000000000000000000000000000000000000000000000000004",
    "693c61390000000000000000000000000000000000000000000000000000000000000005",
    "693c61390000000000000000000000000000000000000000000000000000000000000021",
    "693c61390000000000000000000000000000000000000000000000000000000000000011",
    "693c61390000000000000000000000000000000000000000000000000000000000000003",
    "693c61390000000000000000000000000000000000000000000000000000000000000003",
    "",
    "693c61390000000000000000000000000000000000000000000000000000000000000000",
    "693c61390000000000000000000000000000000000000000000000000000000000000000",
    "",
    "693c61390000000000000000000000000000000000000000000000000000000000000020",
    "693c61390000000000000000000000000000000000000000000000000000000000000010",
    "693c61390000000000000000000000000000000000000000000000000000000000000fff",
    "693c61390000000000000000000000000000000000000000000000000000000000000fff",
]

TX_GAS = [400000]

TX_VALUE = [100000]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d]) if TX_DATA[d] else b""


@pytest.mark.ported_from(
    ["tests/static/state_tests/stEIP2930/storageCostsFiller.yml"],
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
                        "0x0000000000000000000000000000000000001002"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                        )
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
                        "0x0000000000000000000000000000000000001005"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                        )
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
                        "0x0000000000000000000000000000000000001004"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
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
                        "0x0000000000000000000000000000000000001001"
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
                        "0x0000000000000000000000000000000000001021"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
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
                        "0x0000000000000000000000000000000000001011"
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
                        "0x0000000000000000000000000000000000001003"
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
                        "0x00000000000000000000000000000000000060a7"
                    ),
                    storage_keys=[
                        Hash(
                            "0x000000000000000000000000000000000000000000000000000000000fffffad"  # noqa: E501
                        ),
                        Hash(
                            "0x00000000000000000000000000000000000000000000000000000000000000ad"  # noqa: E501
                        ),
                        Hash(
                            "0x00000000000000000000000000000000000000000000000000000123214342ad"  # noqa: E501
                        ),
                        Hash(
                            "0x00000000000000000000000000000000000000000000000000000000deadbeef"  # noqa: E501
                        ),
                    ],
                ),
                AccessList(
                    address=Address(
                        "0x0000000000000000000000000000000000001000"
                    ),
                    storage_keys=[
                        Hash(
                            "0x00000000000000000000000000000000000000000000000000000000000fffff"  # noqa: E501
                        ),
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                        ),
                        Hash(
                            "0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"  # noqa: E501
                        ),
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000123214342"  # noqa: E501
                        ),
                        Hash(
                            "0x00000000000000000000000000000000000000000000000000000000deadbeef"  # noqa: E501
                        ),
                    ],
                ),
                AccessList(
                    address=Address(
                        "0x0000000000000000000000000010000000000100"
                    ),
                    storage_keys=[
                        Hash(
                            "0x000000000000000000000000000000000000000000000000000000000fffffbc"  # noqa: E501
                        ),
                        Hash(
                            "0x00000000000000000000000000000000000000000000000000000000000000bc"  # noqa: E501
                        ),
                        Hash(
                            "0x00000000000000000000000000000000000000000000000000000123214342bc"  # noqa: E501
                        ),
                        Hash(
                            "0x000000000000000000000000000000000000000000000000000000deadbeefbc"  # noqa: E501
                        ),
                    ],
                ),
                AccessList(
                    address=Address(
                        "0xffffffffffffffffffffffffffffffffffffffff"
                    ),
                    storage_keys=[
                        Hash(
                            "0x000000000000000000000000000000000000000000000000000000000fffffbc"  # noqa: E501
                        ),
                        Hash(
                            "0x00000000000000000000000000000000000000000000000000000000000000bc"  # noqa: E501
                        ),
                        Hash(
                            "0x00000000000000000000000000000000000000000000000000000123214342bc"  # noqa: E501
                        ),
                        Hash(
                            "0x000000000000000000000000000000000000000000000000000000deadbeefbc"  # noqa: E501
                        ),
                        Hash(
                            "0xdeadbeef12345678deadbeef12345678deadbeef12345678deadbeef12345678"  # noqa: E501
                        ),
                        Hash(
                            "0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"  # noqa: E501
                        ),
                    ],
                ),
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
                        "0x0000000000000000000000000000000000001000"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                        )
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
                        "0x0000000000000000000000000000000000001020"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                        )
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
                        "0x0000000000000000000000000000000000001010"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
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
                        "0xcccccccccccccccccccccccccccccccccccccccc"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                        ),
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000001"  # noqa: E501
                        ),
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000002"  # noqa: E501
                        ),
                        Hash(
                            "0x00000000000000000000000000000000000000000000000000000000000060a7"  # noqa: E501
                        ),
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
                        "0xf000000000000000000000000000000000000101"
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
        pytest.param(13, 0, 0, None, id="case13"),
        pytest.param(
            20,
            0,
            0,
            [
                AccessList(
                    address=Address(
                        "0x0000000000000000000000000000000000001002"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000010"  # noqa: E501
                        )
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
                        "0xf000000000000000000000000000000000000101"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                        )
                    ],
                )
            ],
            id="case15",
        ),
        pytest.param(16, 0, 0, None, id="case16"),
        pytest.param(
            17,
            0,
            0,
            [
                AccessList(
                    address=Address(
                        "0xf000000000000000000000000000000000000101"
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
        pytest.param(18, 0, 0, None, id="case18"),
        pytest.param(
            23,
            0,
            0,
            [
                AccessList(
                    address=Address(
                        "0x0000000000000000000000000000000000001005"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000010"  # noqa: E501
                        )
                    ],
                )
            ],
            id="case19",
        ),
        pytest.param(
            22,
            0,
            0,
            [
                AccessList(
                    address=Address(
                        "0x0000000000000000000000000000000000001004"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000010"  # noqa: E501
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
                        "0xf000000000000000000000000000000000000101"
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
        pytest.param(22, 0, 0, None, id="case22"),
        pytest.param(
            19,
            0,
            0,
            [
                AccessList(
                    address=Address(
                        "0x0000000000000000000000000000000000001001"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000010"  # noqa: E501
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
                        "0x0000000000000000000000000000000000001021"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000010"  # noqa: E501
                        )
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
                        "0x0000000000000000000000000000000000001011"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000010"  # noqa: E501
                        )
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
                        "0xf000000000000000000000000000000000000101"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                        )
                    ],
                )
            ],
            id="case26",
        ),
        pytest.param(27, 0, 0, None, id="case27"),
        pytest.param(
            21,
            0,
            0,
            [
                AccessList(
                    address=Address(
                        "0x0000000000000000000000000000000000001003"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000010"  # noqa: E501
                        )
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
                        "0xf000000000000000000000000000000000000100"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                        )
                    ],
                )
            ],
            id="case29",
        ),
        pytest.param(30, 0, 0, None, id="case30"),
        pytest.param(
            18,
            0,
            0,
            [
                AccessList(
                    address=Address(
                        "0x0000000000000000000000000000000000001000"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000010"  # noqa: E501
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
                        "0x0000000000000000000000000000000000001020"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000010"  # noqa: E501
                        )
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
                        "0x0000000000000000000000000000000000001010"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000010"  # noqa: E501
                        )
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
                        "0xcccccccccccccccccccccccccccccccccccccccc"
                    ),
                    storage_keys=[
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
                            "0x000000000000000000000000000000000000000000000000000000000000f0a7"  # noqa: E501
                        ),
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
                        "0xcccccccccccccccccccccccccccccccccc000000"
                    ),
                    storage_keys=[
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                        ),
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000001"  # noqa: E501
                        ),
                        Hash(
                            "0x0000000000000000000000000000000000000000000000000000000000000002"  # noqa: E501
                        ),
                        Hash(
                            "0x00000000000000000000000000000000000000000000000000000000000060a7"  # noqa: E501
                        ),
                    ],
                )
            ],
            id="case35",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_storage_costs(
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
            Op.MSTORE(offset=0x0, value=Op.GAS)
            + Op.SSTORE(key=0x0, value=0x2)
            + Op.MSTORE(
                offset=0x0,
                value=Op.SUB(Op.SUB(Op.MLOAD(offset=0x0), Op.GAS), 0x11),
            )
            + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x0))
            + Op.STOP
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001000"),  # noqa: E501
    )
    callee_1 = pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x0, value=Op.GAS)
            + Op.POP(Op.SLOAD(key=0x0))
            + Op.MSTORE(
                offset=0x0,
                value=Op.SUB(Op.SUB(Op.MLOAD(offset=0x0), Op.GAS), 0x13),
            )
            + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x0))
            + Op.STOP
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001001"),  # noqa: E501
    )
    callee_2 = pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x0, value=Op.GAS)
            + Op.SSTORE(key=0x0, value=0x0)
            + Op.MSTORE(
                offset=0x0,
                value=Op.SUB(Op.SUB(Op.MLOAD(offset=0x0), Op.GAS), 0x11),
            )
            + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x0))
            + Op.STOP
        ),
        storage={0x0: 0x60A7},
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001002"),  # noqa: E501
    )
    callee_3 = pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x0, value=Op.GAS)
            + Op.SSTORE(key=0x0, value=0xBEEF)
            + Op.MSTORE(
                offset=0x0,
                value=Op.SUB(Op.SUB(Op.MLOAD(offset=0x0), Op.GAS), 0x11),
            )
            + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x0))
            + Op.STOP
        ),
        storage={0x0: 0x60A7},
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001003"),  # noqa: E501
    )
    callee_4 = pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x0, value=Op.GAS)
            + Op.SSTORE(key=0x0, value=0x60A7)
            + Op.MSTORE(
                offset=0x0,
                value=Op.SUB(Op.SUB(Op.MLOAD(offset=0x0), Op.GAS), 0x11),
            )
            + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x0))
            + Op.STOP
        ),
        storage={0x0: 0x60A7},
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001004"),  # noqa: E501
    )
    callee_5 = pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x0, value=Op.GAS)
            + Op.SSTORE(key=0x0, value=0x0)
            + Op.MSTORE(
                offset=0x0,
                value=Op.SUB(Op.SUB(Op.MLOAD(offset=0x0), Op.GAS), 0x11),
            )
            + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x0))
            + Op.STOP
        ),
        storage={0x0: 0x0},
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001005"),  # noqa: E501
    )
    callee_6 = pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x60A7)
            + Op.MSTORE(offset=0x0, value=Op.GAS)
            + Op.SSTORE(key=0x0, value=0x2)
            + Op.MSTORE(
                offset=0x0,
                value=Op.SUB(Op.SUB(Op.MLOAD(offset=0x0), Op.GAS), 0x11),
            )
            + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x0))
            + Op.STOP
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001010"),  # noqa: E501
    )
    callee_7 = pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x60A7)
            + Op.MSTORE(offset=0x0, value=Op.GAS)
            + Op.POP(Op.SLOAD(key=0x0))
            + Op.MSTORE(
                offset=0x0,
                value=Op.SUB(Op.SUB(Op.MLOAD(offset=0x0), Op.GAS), 0x13),
            )
            + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x0))
            + Op.STOP
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001011"),  # noqa: E501
    )
    callee_8 = pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x20, value=Op.SLOAD(key=0x0))
            + Op.MSTORE(offset=0x0, value=Op.GAS)
            + Op.SSTORE(key=0x0, value=0x2)
            + Op.MSTORE(
                offset=0x0,
                value=Op.SUB(Op.SUB(Op.MLOAD(offset=0x0), Op.GAS), 0x11),
            )
            + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x0))
            + Op.STOP
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001020"),  # noqa: E501
    )
    callee_9 = pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x20, value=Op.SLOAD(key=0x0))
            + Op.MSTORE(offset=0x0, value=Op.GAS)
            + Op.POP(Op.SLOAD(key=0x0))
            + Op.MSTORE(
                offset=0x0,
                value=Op.SUB(Op.SUB(Op.MLOAD(offset=0x0), Op.GAS), 0x13),
            )
            + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x0))
            + Op.STOP
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001021"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)
    # Source: LLL
    # { ; TO_ADDR_VALID   TO_ADDR_INVALID_ADDR    TO_ADDR_INVALID_CELL
    #   ; Call a different contract
    #   (call (gas) (+ 0x1000 $4) 0 0 0 0 0)
    #
    #   ; Read @@0, and see how much gas that cost.
    #     [0]   (gas)
    #     @@0x60A7
    #     [0]   (- @0 (gas) 19)
    #    [[1]] @0
    #
    #
    #   ; Write to @@0, and see how much gas that cost. It should
    #   ; cost more when it is not declared storage
    #     [0]   (gas)
    #    [[0]]  0x02
    #     [0]   (- @0 (gas) 17)
    #    [[2]] @0
    #
    #   ; The 17 is the cost of the extra opcodes:
    #   ; PUSH1 0x00, MSTORE
    #   ; PUSH1 0x02, PUSH1 0x00, (and then comes the SSTORE we are measuring)
    #   ; GAS
    #
    #
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
                    ret_size=0x0,
                ),
            )
            + Op.MSTORE(offset=0x0, value=Op.GAS)
            + Op.POP(Op.SLOAD(key=0x60A7))
            + Op.MSTORE(
                offset=0x0,
                value=Op.SUB(Op.SUB(Op.MLOAD(offset=0x0), Op.GAS), 0x13),
            )
            + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x0))
            + Op.MSTORE(offset=0x0, value=Op.GAS)
            + Op.SSTORE(key=0x0, value=0x2)
            + Op.MSTORE(
                offset=0x0,
                value=Op.SUB(Op.SUB(Op.MLOAD(offset=0x0), Op.GAS), 0x11),
            )
            + Op.SSTORE(key=0x2, value=Op.MLOAD(offset=0x0))
            + Op.STOP
        ),
        storage={0x60A7: 0xDEAD},
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0xcccccccccccccccccccccccccccccccccccccccc"),  # noqa: E501
    )

    EXPECT_ENTRIES: list[dict] = [
        {
            "indexes": {"data": 0, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "5a600052600260005560115a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "5a6000526000545060135a600051030360005260005160015500"
                    )
                ),
                callee_2: Account(
                    storage={1: 2903},
                    code=bytes.fromhex(
                        "5a600052600060005560115a600051030360005260005160015500"  # noqa: E501
                    ),
                ),
                callee_3: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "5a60005261beef60005560115a600051030360005260005160015500"  # noqa: E501
                    ),
                ),
                callee_4: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "5a6000526160a760005560115a600051030360005260005160015500"  # noqa: E501
                    ),
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "5a600052600060005560115a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "6160a76000555a600052600260005560115a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "6160a76000555a6000526000545060135a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_8: Account(
                    code=bytes.fromhex(
                        "6000546020525a600052600260005560115a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_9: Account(
                    code=bytes.fromhex(
                        "6000546020525a6000526000545060135a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={0: 2, 1: 2100, 2: 22100, 24743: 57005},
                    code=bytes.fromhex(
                        "60006000600060006000600435611000015af1505a6000526160a7545060135a60005103036000526000516001555a600052600260005560115a600051030360005260005160025500"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 1, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "5a600052600260005560115a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "5a6000526000545060135a600051030360005260005160015500"
                    )
                ),
                callee_2: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "5a600052600060005560115a600051030360005260005160015500"  # noqa: E501
                    ),
                ),
                callee_3: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "5a60005261beef60005560115a600051030360005260005160015500"  # noqa: E501
                    ),
                ),
                callee_4: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "5a6000526160a760005560115a600051030360005260005160015500"  # noqa: E501
                    ),
                ),
                callee_5: Account(
                    storage={1: 103},
                    code=bytes.fromhex(
                        "5a600052600060005560115a600051030360005260005160015500"  # noqa: E501
                    ),
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "6160a76000555a600052600260005560115a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "6160a76000555a6000526000545060135a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_8: Account(
                    code=bytes.fromhex(
                        "6000546020525a600052600260005560115a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_9: Account(
                    code=bytes.fromhex(
                        "6000546020525a6000526000545060135a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={0: 2, 1: 2100, 2: 22100, 24743: 57005},
                    code=bytes.fromhex(
                        "60006000600060006000600435611000015af1505a6000526160a7545060135a60005103036000526000516001555a600052600260005560115a600051030360005260005160025500"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 2, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "5a600052600260005560115a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "5a6000526000545060135a600051030360005260005160015500"
                    )
                ),
                callee_2: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "5a600052600060005560115a600051030360005260005160015500"  # noqa: E501
                    ),
                ),
                callee_3: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "5a60005261beef60005560115a600051030360005260005160015500"  # noqa: E501
                    ),
                ),
                callee_4: Account(
                    storage={0: 24743, 1: 103},
                    code=bytes.fromhex(
                        "5a6000526160a760005560115a600051030360005260005160015500"  # noqa: E501
                    ),
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "5a600052600060005560115a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "6160a76000555a600052600260005560115a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "6160a76000555a6000526000545060135a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_8: Account(
                    code=bytes.fromhex(
                        "6000546020525a600052600260005560115a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_9: Account(
                    code=bytes.fromhex(
                        "6000546020525a6000526000545060135a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={0: 2, 1: 2100, 2: 22100, 24743: 57005},
                    code=bytes.fromhex(
                        "60006000600060006000600435611000015af1505a6000526160a7545060135a60005103036000526000516001555a600052600260005560115a600051030360005260005160025500"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 3, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "5a600052600260005560115a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    storage={1: 100},
                    code=bytes.fromhex(
                        "5a6000526000545060135a600051030360005260005160015500"
                    ),
                ),
                callee_2: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "5a600052600060005560115a600051030360005260005160015500"  # noqa: E501
                    ),
                ),
                callee_3: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "5a60005261beef60005560115a600051030360005260005160015500"  # noqa: E501
                    ),
                ),
                callee_4: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "5a6000526160a760005560115a600051030360005260005160015500"  # noqa: E501
                    ),
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "5a600052600060005560115a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "6160a76000555a600052600260005560115a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "6160a76000555a6000526000545060135a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_8: Account(
                    code=bytes.fromhex(
                        "6000546020525a600052600260005560115a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_9: Account(
                    code=bytes.fromhex(
                        "6000546020525a6000526000545060135a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={0: 2, 1: 2100, 2: 22100, 24743: 57005},
                    code=bytes.fromhex(
                        "60006000600060006000600435611000015af1505a6000526160a7545060135a60005103036000526000516001555a600052600260005560115a600051030360005260005160025500"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 4, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "5a600052600260005560115a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "5a6000526000545060135a600051030360005260005160015500"
                    )
                ),
                callee_2: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "5a600052600060005560115a600051030360005260005160015500"  # noqa: E501
                    ),
                ),
                callee_3: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "5a60005261beef60005560115a600051030360005260005160015500"  # noqa: E501
                    ),
                ),
                callee_4: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "5a6000526160a760005560115a600051030360005260005160015500"  # noqa: E501
                    ),
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "5a600052600060005560115a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "6160a76000555a600052600260005560115a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "6160a76000555a6000526000545060135a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_8: Account(
                    code=bytes.fromhex(
                        "6000546020525a600052600260005560115a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_9: Account(
                    storage={1: 97},
                    code=bytes.fromhex(
                        "6000546020525a6000526000545060135a600051030360005260005160015500"  # noqa: E501
                    ),
                ),
                contract: Account(
                    storage={0: 2, 1: 2100, 2: 22100, 24743: 57005},
                    code=bytes.fromhex(
                        "60006000600060006000600435611000015af1505a6000526160a7545060135a60005103036000526000516001555a600052600260005560115a600051030360005260005160025500"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 5, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "5a600052600260005560115a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "5a6000526000545060135a600051030360005260005160015500"
                    )
                ),
                callee_2: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "5a600052600060005560115a600051030360005260005160015500"  # noqa: E501
                    ),
                ),
                callee_3: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "5a60005261beef60005560115a600051030360005260005160015500"  # noqa: E501
                    ),
                ),
                callee_4: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "5a6000526160a760005560115a600051030360005260005160015500"  # noqa: E501
                    ),
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "5a600052600060005560115a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "6160a76000555a600052600260005560115a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    storage={0: 24743, 1: 100},
                    code=bytes.fromhex(
                        "6160a76000555a6000526000545060135a600051030360005260005160015500"  # noqa: E501
                    ),
                ),
                callee_8: Account(
                    code=bytes.fromhex(
                        "6000546020525a600052600260005560115a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_9: Account(
                    code=bytes.fromhex(
                        "6000546020525a6000526000545060135a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={0: 2, 1: 2100, 2: 22100, 24743: 57005},
                    code=bytes.fromhex(
                        "60006000600060006000600435611000015af1505a6000526160a7545060135a60005103036000526000516001555a600052600260005560115a600051030360005260005160025500"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 6, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "5a600052600260005560115a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "5a6000526000545060135a600051030360005260005160015500"
                    )
                ),
                callee_2: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "5a600052600060005560115a600051030360005260005160015500"  # noqa: E501
                    ),
                ),
                callee_3: Account(
                    storage={0: 48879, 1: 2903},
                    code=bytes.fromhex(
                        "5a60005261beef60005560115a600051030360005260005160015500"  # noqa: E501
                    ),
                ),
                callee_4: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "5a6000526160a760005560115a600051030360005260005160015500"  # noqa: E501
                    ),
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "5a600052600060005560115a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "6160a76000555a600052600260005560115a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "6160a76000555a6000526000545060135a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_8: Account(
                    code=bytes.fromhex(
                        "6000546020525a600052600260005560115a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_9: Account(
                    code=bytes.fromhex(
                        "6000546020525a6000526000545060135a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={0: 2, 1: 2100, 2: 22100, 24743: 57005},
                    code=bytes.fromhex(
                        "60006000600060006000600435611000015af1505a6000526160a7545060135a60005103036000526000516001555a600052600260005560115a600051030360005260005160025500"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 7, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    storage={0: 2, 1: 20003},
                    code=bytes.fromhex(
                        "5a600052600260005560115a600051030360005260005160015500"  # noqa: E501
                    ),
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "5a6000526000545060135a600051030360005260005160015500"
                    )
                ),
                callee_2: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "5a600052600060005560115a600051030360005260005160015500"  # noqa: E501
                    ),
                ),
                callee_3: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "5a60005261beef60005560115a600051030360005260005160015500"  # noqa: E501
                    ),
                ),
                callee_4: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "5a6000526160a760005560115a600051030360005260005160015500"  # noqa: E501
                    ),
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "5a600052600060005560115a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "6160a76000555a600052600260005560115a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "6160a76000555a6000526000545060135a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_8: Account(
                    code=bytes.fromhex(
                        "6000546020525a600052600260005560115a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_9: Account(
                    code=bytes.fromhex(
                        "6000546020525a6000526000545060135a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={0: 2, 1: 2100, 2: 22100, 24743: 57005},
                    code=bytes.fromhex(
                        "60006000600060006000600435611000015af1505a6000526160a7545060135a60005103036000526000516001555a600052600260005560115a600051030360005260005160025500"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 8, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    storage={0: 2, 1: 20003},
                    code=bytes.fromhex(
                        "5a600052600260005560115a600051030360005260005160015500"  # noqa: E501
                    ),
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "5a6000526000545060135a600051030360005260005160015500"
                    )
                ),
                callee_2: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "5a600052600060005560115a600051030360005260005160015500"  # noqa: E501
                    ),
                ),
                callee_3: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "5a60005261beef60005560115a600051030360005260005160015500"  # noqa: E501
                    ),
                ),
                callee_4: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "5a6000526160a760005560115a600051030360005260005160015500"  # noqa: E501
                    ),
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "5a600052600060005560115a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "6160a76000555a600052600260005560115a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "6160a76000555a6000526000545060135a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_8: Account(
                    code=bytes.fromhex(
                        "6000546020525a600052600260005560115a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_9: Account(
                    code=bytes.fromhex(
                        "6000546020525a6000526000545060135a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={0: 2, 1: 2100, 2: 22100, 24743: 57005},
                    code=bytes.fromhex(
                        "60006000600060006000600435611000015af1505a6000526160a7545060135a60005103036000526000516001555a600052600260005560115a600051030360005260005160025500"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 9, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "5a600052600260005560115a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "5a6000526000545060135a600051030360005260005160015500"
                    )
                ),
                callee_2: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "5a600052600060005560115a600051030360005260005160015500"  # noqa: E501
                    ),
                ),
                callee_3: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "5a60005261beef60005560115a600051030360005260005160015500"  # noqa: E501
                    ),
                ),
                callee_4: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "5a6000526160a760005560115a600051030360005260005160015500"  # noqa: E501
                    ),
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "5a600052600060005560115a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "6160a76000555a600052600260005560115a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "6160a76000555a6000526000545060135a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_8: Account(
                    storage={0: 2, 1: 20000},
                    code=bytes.fromhex(
                        "6000546020525a600052600260005560115a600051030360005260005160015500"  # noqa: E501
                    ),
                ),
                callee_9: Account(
                    code=bytes.fromhex(
                        "6000546020525a6000526000545060135a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={0: 2, 1: 2100, 2: 22100, 24743: 57005},
                    code=bytes.fromhex(
                        "60006000600060006000600435611000015af1505a6000526160a7545060135a60005103036000526000516001555a600052600260005560115a600051030360005260005160025500"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 10, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "5a600052600260005560115a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "5a6000526000545060135a600051030360005260005160015500"
                    )
                ),
                callee_2: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "5a600052600060005560115a600051030360005260005160015500"  # noqa: E501
                    ),
                ),
                callee_3: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "5a60005261beef60005560115a600051030360005260005160015500"  # noqa: E501
                    ),
                ),
                callee_4: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "5a6000526160a760005560115a600051030360005260005160015500"  # noqa: E501
                    ),
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "5a600052600060005560115a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    storage={0: 2, 1: 103},
                    code=bytes.fromhex(
                        "6160a76000555a600052600260005560115a600051030360005260005160015500"  # noqa: E501
                    ),
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "6160a76000555a6000526000545060135a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_8: Account(
                    code=bytes.fromhex(
                        "6000546020525a600052600260005560115a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_9: Account(
                    code=bytes.fromhex(
                        "6000546020525a6000526000545060135a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={0: 2, 1: 2100, 2: 22100, 24743: 57005},
                    code=bytes.fromhex(
                        "60006000600060006000600435611000015af1505a6000526160a7545060135a60005103036000526000516001555a600052600260005560115a600051030360005260005160025500"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 11, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "5a600052600260005560115a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "5a6000526000545060135a600051030360005260005160015500"
                    )
                ),
                callee_2: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "5a600052600060005560115a600051030360005260005160015500"  # noqa: E501
                    ),
                ),
                callee_3: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "5a60005261beef60005560115a600051030360005260005160015500"  # noqa: E501
                    ),
                ),
                callee_4: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "5a6000526160a760005560115a600051030360005260005160015500"  # noqa: E501
                    ),
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "5a600052600060005560115a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "6160a76000555a600052600260005560115a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "6160a76000555a6000526000545060135a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_8: Account(
                    code=bytes.fromhex(
                        "6000546020525a600052600260005560115a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_9: Account(
                    code=bytes.fromhex(
                        "6000546020525a6000526000545060135a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={0: 2, 1: 100, 2: 20000, 24743: 57005},
                    code=bytes.fromhex(
                        "60006000600060006000600435611000015af1505a6000526160a7545060135a60005103036000526000516001555a600052600260005560115a600051030360005260005160025500"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 12, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "5a600052600260005560115a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "5a6000526000545060135a600051030360005260005160015500"
                    )
                ),
                callee_2: Account(
                    storage={1: 5003},
                    code=bytes.fromhex(
                        "5a600052600060005560115a600051030360005260005160015500"  # noqa: E501
                    ),
                ),
                callee_3: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "5a60005261beef60005560115a600051030360005260005160015500"  # noqa: E501
                    ),
                ),
                callee_4: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "5a6000526160a760005560115a600051030360005260005160015500"  # noqa: E501
                    ),
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "5a600052600060005560115a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "6160a76000555a600052600260005560115a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "6160a76000555a6000526000545060135a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_8: Account(
                    code=bytes.fromhex(
                        "6000546020525a600052600260005560115a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_9: Account(
                    code=bytes.fromhex(
                        "6000546020525a6000526000545060135a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={0: 2, 1: 2100, 2: 22100, 24743: 57005},
                    code=bytes.fromhex(
                        "60006000600060006000600435611000015af1505a6000526160a7545060135a60005103036000526000516001555a600052600260005560115a600051030360005260005160025500"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 13, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "5a600052600260005560115a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "5a6000526000545060135a600051030360005260005160015500"
                    )
                ),
                callee_2: Account(
                    storage={1: 5003},
                    code=bytes.fromhex(
                        "5a600052600060005560115a600051030360005260005160015500"  # noqa: E501
                    ),
                ),
                callee_3: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "5a60005261beef60005560115a600051030360005260005160015500"  # noqa: E501
                    ),
                ),
                callee_4: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "5a6000526160a760005560115a600051030360005260005160015500"  # noqa: E501
                    ),
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "5a600052600060005560115a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "6160a76000555a600052600260005560115a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "6160a76000555a6000526000545060135a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_8: Account(
                    code=bytes.fromhex(
                        "6000546020525a600052600260005560115a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_9: Account(
                    code=bytes.fromhex(
                        "6000546020525a6000526000545060135a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={0: 2, 1: 2100, 2: 22100, 24743: 57005},
                    code=bytes.fromhex(
                        "60006000600060006000600435611000015af1505a6000526160a7545060135a60005103036000526000516001555a600052600260005560115a600051030360005260005160025500"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 20, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "5a600052600260005560115a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "5a6000526000545060135a600051030360005260005160015500"
                    )
                ),
                callee_2: Account(
                    storage={1: 5003},
                    code=bytes.fromhex(
                        "5a600052600060005560115a600051030360005260005160015500"  # noqa: E501
                    ),
                ),
                callee_3: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "5a60005261beef60005560115a600051030360005260005160015500"  # noqa: E501
                    ),
                ),
                callee_4: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "5a6000526160a760005560115a600051030360005260005160015500"  # noqa: E501
                    ),
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "5a600052600060005560115a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "6160a76000555a600052600260005560115a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "6160a76000555a6000526000545060135a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_8: Account(
                    code=bytes.fromhex(
                        "6000546020525a600052600260005560115a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_9: Account(
                    code=bytes.fromhex(
                        "6000546020525a6000526000545060135a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={0: 2, 1: 2100, 2: 22100, 24743: 57005},
                    code=bytes.fromhex(
                        "60006000600060006000600435611000015af1505a6000526160a7545060135a60005103036000526000516001555a600052600260005560115a600051030360005260005160025500"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 15, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "5a600052600260005560115a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "5a6000526000545060135a600051030360005260005160015500"
                    )
                ),
                callee_2: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "5a600052600060005560115a600051030360005260005160015500"  # noqa: E501
                    ),
                ),
                callee_3: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "5a60005261beef60005560115a600051030360005260005160015500"  # noqa: E501
                    ),
                ),
                callee_4: Account(
                    storage={0: 24743, 1: 2203},
                    code=bytes.fromhex(
                        "5a6000526160a760005560115a600051030360005260005160015500"  # noqa: E501
                    ),
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "5a600052600060005560115a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "6160a76000555a600052600260005560115a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "6160a76000555a6000526000545060135a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_8: Account(
                    code=bytes.fromhex(
                        "6000546020525a600052600260005560115a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_9: Account(
                    code=bytes.fromhex(
                        "6000546020525a6000526000545060135a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={0: 2, 1: 2100, 2: 22100, 24743: 57005},
                    code=bytes.fromhex(
                        "60006000600060006000600435611000015af1505a6000526160a7545060135a60005103036000526000516001555a600052600260005560115a600051030360005260005160025500"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 16, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "5a600052600260005560115a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "5a6000526000545060135a600051030360005260005160015500"
                    )
                ),
                callee_2: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "5a600052600060005560115a600051030360005260005160015500"  # noqa: E501
                    ),
                ),
                callee_3: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "5a60005261beef60005560115a600051030360005260005160015500"  # noqa: E501
                    ),
                ),
                callee_4: Account(
                    storage={0: 24743, 1: 2203},
                    code=bytes.fromhex(
                        "5a6000526160a760005560115a600051030360005260005160015500"  # noqa: E501
                    ),
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "5a600052600060005560115a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "6160a76000555a600052600260005560115a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "6160a76000555a6000526000545060135a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_8: Account(
                    code=bytes.fromhex(
                        "6000546020525a600052600260005560115a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_9: Account(
                    code=bytes.fromhex(
                        "6000546020525a6000526000545060135a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={0: 2, 1: 2100, 2: 22100, 24743: 57005},
                    code=bytes.fromhex(
                        "60006000600060006000600435611000015af1505a6000526160a7545060135a60005103036000526000516001555a600052600260005560115a600051030360005260005160025500"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 17, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "5a600052600260005560115a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "5a6000526000545060135a600051030360005260005160015500"
                    )
                ),
                callee_2: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "5a600052600060005560115a600051030360005260005160015500"  # noqa: E501
                    ),
                ),
                callee_3: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "5a60005261beef60005560115a600051030360005260005160015500"  # noqa: E501
                    ),
                ),
                callee_4: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "5a6000526160a760005560115a600051030360005260005160015500"  # noqa: E501
                    ),
                ),
                callee_5: Account(
                    storage={1: 2203},
                    code=bytes.fromhex(
                        "5a600052600060005560115a600051030360005260005160015500"  # noqa: E501
                    ),
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "6160a76000555a600052600260005560115a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "6160a76000555a6000526000545060135a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_8: Account(
                    code=bytes.fromhex(
                        "6000546020525a600052600260005560115a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_9: Account(
                    code=bytes.fromhex(
                        "6000546020525a6000526000545060135a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={0: 2, 1: 2100, 2: 22100, 24743: 57005},
                    code=bytes.fromhex(
                        "60006000600060006000600435611000015af1505a6000526160a7545060135a60005103036000526000516001555a600052600260005560115a600051030360005260005160025500"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 18, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "5a600052600260005560115a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "5a6000526000545060135a600051030360005260005160015500"
                    )
                ),
                callee_2: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "5a600052600060005560115a600051030360005260005160015500"  # noqa: E501
                    ),
                ),
                callee_3: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "5a60005261beef60005560115a600051030360005260005160015500"  # noqa: E501
                    ),
                ),
                callee_4: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "5a6000526160a760005560115a600051030360005260005160015500"  # noqa: E501
                    ),
                ),
                callee_5: Account(
                    storage={1: 2203},
                    code=bytes.fromhex(
                        "5a600052600060005560115a600051030360005260005160015500"  # noqa: E501
                    ),
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "6160a76000555a600052600260005560115a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "6160a76000555a6000526000545060135a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_8: Account(
                    code=bytes.fromhex(
                        "6000546020525a600052600260005560115a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_9: Account(
                    code=bytes.fromhex(
                        "6000546020525a6000526000545060135a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={0: 2, 1: 2100, 2: 22100, 24743: 57005},
                    code=bytes.fromhex(
                        "60006000600060006000600435611000015af1505a6000526160a7545060135a60005103036000526000516001555a600052600260005560115a600051030360005260005160025500"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 23, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "5a600052600260005560115a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "5a6000526000545060135a600051030360005260005160015500"
                    )
                ),
                callee_2: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "5a600052600060005560115a600051030360005260005160015500"  # noqa: E501
                    ),
                ),
                callee_3: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "5a60005261beef60005560115a600051030360005260005160015500"  # noqa: E501
                    ),
                ),
                callee_4: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "5a6000526160a760005560115a600051030360005260005160015500"  # noqa: E501
                    ),
                ),
                callee_5: Account(
                    storage={1: 2203},
                    code=bytes.fromhex(
                        "5a600052600060005560115a600051030360005260005160015500"  # noqa: E501
                    ),
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "6160a76000555a600052600260005560115a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "6160a76000555a6000526000545060135a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_8: Account(
                    code=bytes.fromhex(
                        "6000546020525a600052600260005560115a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_9: Account(
                    code=bytes.fromhex(
                        "6000546020525a6000526000545060135a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={0: 2, 1: 2100, 2: 22100, 24743: 57005},
                    code=bytes.fromhex(
                        "60006000600060006000600435611000015af1505a6000526160a7545060135a60005103036000526000516001555a600052600260005560115a600051030360005260005160025500"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 22, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "5a600052600260005560115a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "5a6000526000545060135a600051030360005260005160015500"
                    )
                ),
                callee_2: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "5a600052600060005560115a600051030360005260005160015500"  # noqa: E501
                    ),
                ),
                callee_3: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "5a60005261beef60005560115a600051030360005260005160015500"  # noqa: E501
                    ),
                ),
                callee_4: Account(
                    storage={0: 24743, 1: 2203},
                    code=bytes.fromhex(
                        "5a6000526160a760005560115a600051030360005260005160015500"  # noqa: E501
                    ),
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "5a600052600060005560115a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "6160a76000555a600052600260005560115a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "6160a76000555a6000526000545060135a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_8: Account(
                    code=bytes.fromhex(
                        "6000546020525a600052600260005560115a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_9: Account(
                    code=bytes.fromhex(
                        "6000546020525a6000526000545060135a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={0: 2, 1: 2100, 2: 22100, 24743: 57005},
                    code=bytes.fromhex(
                        "60006000600060006000600435611000015af1505a6000526160a7545060135a60005103036000526000516001555a600052600260005560115a600051030360005260005160025500"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 21, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "5a600052600260005560115a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    storage={1: 2100},
                    code=bytes.fromhex(
                        "5a6000526000545060135a600051030360005260005160015500"
                    ),
                ),
                callee_2: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "5a600052600060005560115a600051030360005260005160015500"  # noqa: E501
                    ),
                ),
                callee_3: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "5a60005261beef60005560115a600051030360005260005160015500"  # noqa: E501
                    ),
                ),
                callee_4: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "5a6000526160a760005560115a600051030360005260005160015500"  # noqa: E501
                    ),
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "5a600052600060005560115a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "6160a76000555a600052600260005560115a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "6160a76000555a6000526000545060135a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_8: Account(
                    code=bytes.fromhex(
                        "6000546020525a600052600260005560115a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_9: Account(
                    code=bytes.fromhex(
                        "6000546020525a6000526000545060135a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={0: 2, 1: 2100, 2: 22100, 24743: 57005},
                    code=bytes.fromhex(
                        "60006000600060006000600435611000015af1505a6000526160a7545060135a60005103036000526000516001555a600052600260005560115a600051030360005260005160025500"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 22, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "5a600052600260005560115a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    storage={1: 2100},
                    code=bytes.fromhex(
                        "5a6000526000545060135a600051030360005260005160015500"
                    ),
                ),
                callee_2: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "5a600052600060005560115a600051030360005260005160015500"  # noqa: E501
                    ),
                ),
                callee_3: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "5a60005261beef60005560115a600051030360005260005160015500"  # noqa: E501
                    ),
                ),
                callee_4: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "5a6000526160a760005560115a600051030360005260005160015500"  # noqa: E501
                    ),
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "5a600052600060005560115a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "6160a76000555a600052600260005560115a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "6160a76000555a6000526000545060135a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_8: Account(
                    code=bytes.fromhex(
                        "6000546020525a600052600260005560115a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_9: Account(
                    code=bytes.fromhex(
                        "6000546020525a6000526000545060135a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={0: 2, 1: 2100, 2: 22100, 24743: 57005},
                    code=bytes.fromhex(
                        "60006000600060006000600435611000015af1505a6000526160a7545060135a60005103036000526000516001555a600052600260005560115a600051030360005260005160025500"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 19, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "5a600052600260005560115a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    storage={1: 2100},
                    code=bytes.fromhex(
                        "5a6000526000545060135a600051030360005260005160015500"
                    ),
                ),
                callee_2: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "5a600052600060005560115a600051030360005260005160015500"  # noqa: E501
                    ),
                ),
                callee_3: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "5a60005261beef60005560115a600051030360005260005160015500"  # noqa: E501
                    ),
                ),
                callee_4: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "5a6000526160a760005560115a600051030360005260005160015500"  # noqa: E501
                    ),
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "5a600052600060005560115a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "6160a76000555a600052600260005560115a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "6160a76000555a6000526000545060135a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_8: Account(
                    code=bytes.fromhex(
                        "6000546020525a600052600260005560115a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_9: Account(
                    code=bytes.fromhex(
                        "6000546020525a6000526000545060135a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={0: 2, 1: 2100, 2: 22100, 24743: 57005},
                    code=bytes.fromhex(
                        "60006000600060006000600435611000015af1505a6000526160a7545060135a60005103036000526000516001555a600052600260005560115a600051030360005260005160025500"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 24, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "5a600052600260005560115a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "5a6000526000545060135a600051030360005260005160015500"
                    )
                ),
                callee_2: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "5a600052600060005560115a600051030360005260005160015500"  # noqa: E501
                    ),
                ),
                callee_3: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "5a60005261beef60005560115a600051030360005260005160015500"  # noqa: E501
                    ),
                ),
                callee_4: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "5a6000526160a760005560115a600051030360005260005160015500"  # noqa: E501
                    ),
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "5a600052600060005560115a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "6160a76000555a600052600260005560115a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "6160a76000555a6000526000545060135a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_8: Account(
                    code=bytes.fromhex(
                        "6000546020525a600052600260005560115a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_9: Account(
                    storage={1: 97},
                    code=bytes.fromhex(
                        "6000546020525a6000526000545060135a600051030360005260005160015500"  # noqa: E501
                    ),
                ),
                contract: Account(
                    storage={0: 2, 1: 2100, 2: 22100, 24743: 57005},
                    code=bytes.fromhex(
                        "60006000600060006000600435611000015af1505a6000526160a7545060135a60005103036000526000516001555a600052600260005560115a600051030360005260005160025500"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 25, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "5a600052600260005560115a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "5a6000526000545060135a600051030360005260005160015500"
                    )
                ),
                callee_2: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "5a600052600060005560115a600051030360005260005160015500"  # noqa: E501
                    ),
                ),
                callee_3: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "5a60005261beef60005560115a600051030360005260005160015500"  # noqa: E501
                    ),
                ),
                callee_4: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "5a6000526160a760005560115a600051030360005260005160015500"  # noqa: E501
                    ),
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "5a600052600060005560115a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "6160a76000555a600052600260005560115a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    storage={0: 24743, 1: 100},
                    code=bytes.fromhex(
                        "6160a76000555a6000526000545060135a600051030360005260005160015500"  # noqa: E501
                    ),
                ),
                callee_8: Account(
                    code=bytes.fromhex(
                        "6000546020525a600052600260005560115a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_9: Account(
                    code=bytes.fromhex(
                        "6000546020525a6000526000545060135a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={0: 2, 1: 2100, 2: 22100, 24743: 57005},
                    code=bytes.fromhex(
                        "60006000600060006000600435611000015af1505a6000526160a7545060135a60005103036000526000516001555a600052600260005560115a600051030360005260005160025500"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 26, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "5a600052600260005560115a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "5a6000526000545060135a600051030360005260005160015500"
                    )
                ),
                callee_2: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "5a600052600060005560115a600051030360005260005160015500"  # noqa: E501
                    ),
                ),
                callee_3: Account(
                    storage={0: 48879, 1: 5003},
                    code=bytes.fromhex(
                        "5a60005261beef60005560115a600051030360005260005160015500"  # noqa: E501
                    ),
                ),
                callee_4: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "5a6000526160a760005560115a600051030360005260005160015500"  # noqa: E501
                    ),
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "5a600052600060005560115a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "6160a76000555a600052600260005560115a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "6160a76000555a6000526000545060135a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_8: Account(
                    code=bytes.fromhex(
                        "6000546020525a600052600260005560115a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_9: Account(
                    code=bytes.fromhex(
                        "6000546020525a6000526000545060135a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={0: 2, 1: 2100, 2: 22100, 24743: 57005},
                    code=bytes.fromhex(
                        "60006000600060006000600435611000015af1505a6000526160a7545060135a60005103036000526000516001555a600052600260005560115a600051030360005260005160025500"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 27, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "5a600052600260005560115a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "5a6000526000545060135a600051030360005260005160015500"
                    )
                ),
                callee_2: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "5a600052600060005560115a600051030360005260005160015500"  # noqa: E501
                    ),
                ),
                callee_3: Account(
                    storage={0: 48879, 1: 5003},
                    code=bytes.fromhex(
                        "5a60005261beef60005560115a600051030360005260005160015500"  # noqa: E501
                    ),
                ),
                callee_4: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "5a6000526160a760005560115a600051030360005260005160015500"  # noqa: E501
                    ),
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "5a600052600060005560115a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "6160a76000555a600052600260005560115a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "6160a76000555a6000526000545060135a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_8: Account(
                    code=bytes.fromhex(
                        "6000546020525a600052600260005560115a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_9: Account(
                    code=bytes.fromhex(
                        "6000546020525a6000526000545060135a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={0: 2, 1: 2100, 2: 22100, 24743: 57005},
                    code=bytes.fromhex(
                        "60006000600060006000600435611000015af1505a6000526160a7545060135a60005103036000526000516001555a600052600260005560115a600051030360005260005160025500"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 21, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "5a600052600260005560115a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "5a6000526000545060135a600051030360005260005160015500"
                    )
                ),
                callee_2: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "5a600052600060005560115a600051030360005260005160015500"  # noqa: E501
                    ),
                ),
                callee_3: Account(
                    storage={0: 48879, 1: 5003},
                    code=bytes.fromhex(
                        "5a60005261beef60005560115a600051030360005260005160015500"  # noqa: E501
                    ),
                ),
                callee_4: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "5a6000526160a760005560115a600051030360005260005160015500"  # noqa: E501
                    ),
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "5a600052600060005560115a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "6160a76000555a600052600260005560115a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "6160a76000555a6000526000545060135a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_8: Account(
                    code=bytes.fromhex(
                        "6000546020525a600052600260005560115a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_9: Account(
                    code=bytes.fromhex(
                        "6000546020525a6000526000545060135a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={0: 2, 1: 2100, 2: 22100, 24743: 57005},
                    code=bytes.fromhex(
                        "60006000600060006000600435611000015af1505a6000526160a7545060135a60005103036000526000516001555a600052600260005560115a600051030360005260005160025500"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 29, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    storage={0: 2, 1: 22103},
                    code=bytes.fromhex(
                        "5a600052600260005560115a600051030360005260005160015500"  # noqa: E501
                    ),
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "5a6000526000545060135a600051030360005260005160015500"
                    )
                ),
                callee_2: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "5a600052600060005560115a600051030360005260005160015500"  # noqa: E501
                    ),
                ),
                callee_3: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "5a60005261beef60005560115a600051030360005260005160015500"  # noqa: E501
                    ),
                ),
                callee_4: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "5a6000526160a760005560115a600051030360005260005160015500"  # noqa: E501
                    ),
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "5a600052600060005560115a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "6160a76000555a600052600260005560115a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "6160a76000555a6000526000545060135a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_8: Account(
                    code=bytes.fromhex(
                        "6000546020525a600052600260005560115a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_9: Account(
                    code=bytes.fromhex(
                        "6000546020525a6000526000545060135a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={0: 2, 1: 2100, 2: 22100, 24743: 57005},
                    code=bytes.fromhex(
                        "60006000600060006000600435611000015af1505a6000526160a7545060135a60005103036000526000516001555a600052600260005560115a600051030360005260005160025500"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 30, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    storage={0: 2, 1: 22103},
                    code=bytes.fromhex(
                        "5a600052600260005560115a600051030360005260005160015500"  # noqa: E501
                    ),
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "5a6000526000545060135a600051030360005260005160015500"
                    )
                ),
                callee_2: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "5a600052600060005560115a600051030360005260005160015500"  # noqa: E501
                    ),
                ),
                callee_3: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "5a60005261beef60005560115a600051030360005260005160015500"  # noqa: E501
                    ),
                ),
                callee_4: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "5a6000526160a760005560115a600051030360005260005160015500"  # noqa: E501
                    ),
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "5a600052600060005560115a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "6160a76000555a600052600260005560115a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "6160a76000555a6000526000545060135a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_8: Account(
                    code=bytes.fromhex(
                        "6000546020525a600052600260005560115a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_9: Account(
                    code=bytes.fromhex(
                        "6000546020525a6000526000545060135a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={0: 2, 1: 2100, 2: 22100, 24743: 57005},
                    code=bytes.fromhex(
                        "60006000600060006000600435611000015af1505a6000526160a7545060135a60005103036000526000516001555a600052600260005560115a600051030360005260005160025500"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 18, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    storage={0: 2, 1: 22103},
                    code=bytes.fromhex(
                        "5a600052600260005560115a600051030360005260005160015500"  # noqa: E501
                    ),
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "5a6000526000545060135a600051030360005260005160015500"
                    )
                ),
                callee_2: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "5a600052600060005560115a600051030360005260005160015500"  # noqa: E501
                    ),
                ),
                callee_3: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "5a60005261beef60005560115a600051030360005260005160015500"  # noqa: E501
                    ),
                ),
                callee_4: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "5a6000526160a760005560115a600051030360005260005160015500"  # noqa: E501
                    ),
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "5a600052600060005560115a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "6160a76000555a600052600260005560115a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "6160a76000555a6000526000545060135a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_8: Account(
                    code=bytes.fromhex(
                        "6000546020525a600052600260005560115a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_9: Account(
                    code=bytes.fromhex(
                        "6000546020525a6000526000545060135a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={0: 2, 1: 2100, 2: 22100, 24743: 57005},
                    code=bytes.fromhex(
                        "60006000600060006000600435611000015af1505a6000526160a7545060135a60005103036000526000516001555a600052600260005560115a600051030360005260005160025500"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 32, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "5a600052600260005560115a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "5a6000526000545060135a600051030360005260005160015500"
                    )
                ),
                callee_2: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "5a600052600060005560115a600051030360005260005160015500"  # noqa: E501
                    ),
                ),
                callee_3: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "5a60005261beef60005560115a600051030360005260005160015500"  # noqa: E501
                    ),
                ),
                callee_4: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "5a6000526160a760005560115a600051030360005260005160015500"  # noqa: E501
                    ),
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "5a600052600060005560115a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "6160a76000555a600052600260005560115a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "6160a76000555a6000526000545060135a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_8: Account(
                    storage={0: 2, 1: 20000},
                    code=bytes.fromhex(
                        "6000546020525a600052600260005560115a600051030360005260005160015500"  # noqa: E501
                    ),
                ),
                callee_9: Account(
                    code=bytes.fromhex(
                        "6000546020525a6000526000545060135a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={0: 2, 1: 2100, 2: 22100, 24743: 57005},
                    code=bytes.fromhex(
                        "60006000600060006000600435611000015af1505a6000526160a7545060135a60005103036000526000516001555a600052600260005560115a600051030360005260005160025500"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 33, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "5a600052600260005560115a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "5a6000526000545060135a600051030360005260005160015500"
                    )
                ),
                callee_2: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "5a600052600060005560115a600051030360005260005160015500"  # noqa: E501
                    ),
                ),
                callee_3: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "5a60005261beef60005560115a600051030360005260005160015500"  # noqa: E501
                    ),
                ),
                callee_4: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "5a6000526160a760005560115a600051030360005260005160015500"  # noqa: E501
                    ),
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "5a600052600060005560115a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    storage={0: 2, 1: 103},
                    code=bytes.fromhex(
                        "6160a76000555a600052600260005560115a600051030360005260005160015500"  # noqa: E501
                    ),
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "6160a76000555a6000526000545060135a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_8: Account(
                    code=bytes.fromhex(
                        "6000546020525a600052600260005560115a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_9: Account(
                    code=bytes.fromhex(
                        "6000546020525a6000526000545060135a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={0: 2, 1: 2100, 2: 22100, 24743: 57005},
                    code=bytes.fromhex(
                        "60006000600060006000600435611000015af1505a6000526160a7545060135a60005103036000526000516001555a600052600260005560115a600051030360005260005160025500"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 34, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "5a600052600260005560115a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "5a6000526000545060135a600051030360005260005160015500"
                    )
                ),
                callee_2: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "5a600052600060005560115a600051030360005260005160015500"  # noqa: E501
                    ),
                ),
                callee_3: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "5a60005261beef60005560115a600051030360005260005160015500"  # noqa: E501
                    ),
                ),
                callee_4: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "5a6000526160a760005560115a600051030360005260005160015500"  # noqa: E501
                    ),
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "5a600052600060005560115a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "6160a76000555a600052600260005560115a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "6160a76000555a6000526000545060135a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_8: Account(
                    code=bytes.fromhex(
                        "6000546020525a600052600260005560115a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_9: Account(
                    code=bytes.fromhex(
                        "6000546020525a6000526000545060135a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={0: 2, 1: 2100, 2: 22100, 24743: 57005},
                    code=bytes.fromhex(
                        "60006000600060006000600435611000015af1505a6000526160a7545060135a60005103036000526000516001555a600052600260005560115a600051030360005260005160025500"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 35, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "5a600052600260005560115a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "5a6000526000545060135a600051030360005260005160015500"
                    )
                ),
                callee_2: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "5a600052600060005560115a600051030360005260005160015500"  # noqa: E501
                    ),
                ),
                callee_3: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "5a60005261beef60005560115a600051030360005260005160015500"  # noqa: E501
                    ),
                ),
                callee_4: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "5a6000526160a760005560115a600051030360005260005160015500"  # noqa: E501
                    ),
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "5a600052600060005560115a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "6160a76000555a600052600260005560115a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "6160a76000555a6000526000545060135a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_8: Account(
                    code=bytes.fromhex(
                        "6000546020525a600052600260005560115a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                callee_9: Account(
                    code=bytes.fromhex(
                        "6000546020525a6000526000545060135a600051030360005260005160015500"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={0: 2, 1: 2100, 2: 22100, 24743: 57005},
                    code=bytes.fromhex(
                        "60006000600060006000600435611000015af1505a6000526160a7545060135a60005103036000526000516001555a600052600260005560115a600051030360005260005160025500"  # noqa: E501
                    ),
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
