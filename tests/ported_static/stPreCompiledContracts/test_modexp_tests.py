"""
Ori Pomerantz qbzzt1@gmail.com.

Ported from:
state_tests/stPreCompiledContracts/modexpTestsFiller.yml
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Bytes,
    Environment,
    Hash,
    StateTestFiller,
    Transaction,
)
from execution_testing.forks import Fork
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stPreCompiledContracts/modexpTestsFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Prague")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0,
            0,
            0,
            id="m_n_01",
        ),
        pytest.param(
            1,
            0,
            0,
            id="m_n_01",
        ),
        pytest.param(
            2,
            0,
            0,
            id="0_0_n",
        ),
        pytest.param(
            3,
            0,
            0,
            id="0_0_n",
        ),
        pytest.param(
            4,
            0,
            0,
            id="0_0_n",
        ),
        pytest.param(
            5,
            0,
            0,
            id="0_0_n",
        ),
        pytest.param(
            6,
            0,
            0,
            id="0_0_n",
        ),
        pytest.param(
            7,
            0,
            0,
            id="0_0_n",
        ),
        pytest.param(
            8,
            0,
            0,
            id="0_0_n",
        ),
        pytest.param(
            9,
            0,
            0,
            id="0_0_n",
        ),
        pytest.param(
            10,
            0,
            0,
            id="0_0_n",
        ),
        pytest.param(
            11,
            0,
            0,
            id="0_0_n",
        ),
        pytest.param(
            12,
            0,
            0,
            id="0_0_n",
        ),
        pytest.param(
            13,
            0,
            0,
            id="0_0_n",
        ),
        pytest.param(
            14,
            0,
            0,
            id="0_0_n",
        ),
        pytest.param(
            15,
            0,
            0,
            id="0_0_n",
        ),
        pytest.param(
            16,
            0,
            0,
            id="0_0_n",
        ),
        pytest.param(
            17,
            0,
            0,
            id="m_n_01",
        ),
        pytest.param(
            18,
            0,
            0,
            id="m_n_01",
        ),
        pytest.param(
            19,
            0,
            0,
            id="0_m_n",
        ),
        pytest.param(
            20,
            0,
            0,
            id="0_m_n",
        ),
        pytest.param(
            21,
            0,
            0,
            id="0_m_n",
        ),
        pytest.param(
            22,
            0,
            0,
            id="0_m_n",
        ),
        pytest.param(
            23,
            0,
            0,
            id="0_m_n",
        ),
        pytest.param(
            24,
            0,
            0,
            id="0_m_n",
        ),
        pytest.param(
            25,
            0,
            0,
            id="0_m_n",
        ),
        pytest.param(
            26,
            0,
            0,
            id="0_m_n",
        ),
        pytest.param(
            27,
            0,
            0,
            id="0_m_n",
        ),
        pytest.param(
            28,
            0,
            0,
            id="0_m_n",
        ),
        pytest.param(
            29,
            0,
            0,
            id="0_m_n",
        ),
        pytest.param(
            30,
            0,
            0,
            id="0_m_n",
        ),
        pytest.param(
            31,
            0,
            0,
            id="0_m_n",
        ),
        pytest.param(
            32,
            0,
            0,
            id="0_m_n",
        ),
        pytest.param(
            33,
            0,
            0,
            id="0_m_n",
        ),
        pytest.param(
            34,
            0,
            0,
            id="m_n_01",
        ),
        pytest.param(
            35,
            0,
            0,
            id="m_n_01",
        ),
        pytest.param(
            36,
            0,
            0,
            id="0_m_n",
        ),
        pytest.param(
            37,
            0,
            0,
            id="0_m_n",
        ),
        pytest.param(
            38,
            0,
            0,
            id="0_m_n",
        ),
        pytest.param(
            39,
            0,
            0,
            id="0_m_n",
        ),
        pytest.param(
            40,
            0,
            0,
            id="0_m_n",
        ),
        pytest.param(
            41,
            0,
            0,
            id="0_m_n",
        ),
        pytest.param(
            42,
            0,
            0,
            id="0_m_n",
        ),
        pytest.param(
            43,
            0,
            0,
            id="0_m_n",
        ),
        pytest.param(
            44,
            0,
            0,
            id="0_m_n",
        ),
        pytest.param(
            45,
            0,
            0,
            id="0_m_n",
        ),
        pytest.param(
            46,
            0,
            0,
            id="0_m_n",
        ),
        pytest.param(
            47,
            0,
            0,
            id="0_m_n",
        ),
        pytest.param(
            48,
            0,
            0,
            id="0_m_n",
        ),
        pytest.param(
            49,
            0,
            0,
            id="0_m_n",
        ),
        pytest.param(
            50,
            0,
            0,
            id="0_m_n",
        ),
        pytest.param(
            51,
            0,
            0,
            id="0_m_n",
        ),
        pytest.param(
            52,
            0,
            0,
            id="0_m_n",
        ),
        pytest.param(
            53,
            0,
            0,
            id="0_m_n",
        ),
        pytest.param(
            54,
            0,
            0,
            id="0_m_n",
        ),
        pytest.param(
            55,
            0,
            0,
            id="0_m_n",
        ),
        pytest.param(
            56,
            0,
            0,
            id="0_m_n",
        ),
        pytest.param(
            57,
            0,
            0,
            id="0_m_n",
        ),
        pytest.param(
            58,
            0,
            0,
            id="0_m_n",
        ),
        pytest.param(
            59,
            0,
            0,
            id="0_m_n",
        ),
        pytest.param(
            60,
            0,
            0,
            id="0_m_n",
        ),
        pytest.param(
            61,
            0,
            0,
            id="0_m_n",
        ),
        pytest.param(
            62,
            0,
            0,
            id="0_m_n",
        ),
        pytest.param(
            63,
            0,
            0,
            id="0_m_n",
        ),
        pytest.param(
            64,
            0,
            0,
            id="0_m_n",
        ),
        pytest.param(
            65,
            0,
            0,
            id="0_m_n",
        ),
        pytest.param(
            66,
            0,
            0,
            id="0_m_n",
        ),
        pytest.param(
            67,
            0,
            0,
            id="m_n_01",
        ),
        pytest.param(
            68,
            0,
            0,
            id="m_n_01",
        ),
        pytest.param(
            69,
            0,
            0,
            id="1_0_n",
        ),
        pytest.param(
            70,
            0,
            0,
            id="1_0_n",
        ),
        pytest.param(
            71,
            0,
            0,
            id="1_0_n",
        ),
        pytest.param(
            72,
            0,
            0,
            id="1_0_n",
        ),
        pytest.param(
            73,
            0,
            0,
            id="1_0_n",
        ),
        pytest.param(
            74,
            0,
            0,
            id="1_0_n",
        ),
        pytest.param(
            75,
            0,
            0,
            id="1_0_n",
        ),
        pytest.param(
            76,
            0,
            0,
            id="1_0_n",
        ),
        pytest.param(
            77,
            0,
            0,
            id="1_0_n",
        ),
        pytest.param(
            78,
            0,
            0,
            id="1_0_n",
        ),
        pytest.param(
            79,
            0,
            0,
            id="1_0_n",
        ),
        pytest.param(
            80,
            0,
            0,
            id="1_0_n",
        ),
        pytest.param(
            81,
            0,
            0,
            id="1_0_n",
        ),
        pytest.param(
            82,
            0,
            0,
            id="1_0_n",
        ),
        pytest.param(
            83,
            0,
            0,
            id="1_0_n",
        ),
        pytest.param(
            84,
            0,
            0,
            id="m_n_01",
        ),
        pytest.param(
            85,
            0,
            0,
            id="m_n_01",
        ),
        pytest.param(
            86,
            0,
            0,
            id="1_m_n",
        ),
        pytest.param(
            87,
            0,
            0,
            id="1_m_n",
        ),
        pytest.param(
            88,
            0,
            0,
            id="1_m_n",
        ),
        pytest.param(
            89,
            0,
            0,
            id="1_m_n",
        ),
        pytest.param(
            90,
            0,
            0,
            id="1_m_n",
        ),
        pytest.param(
            91,
            0,
            0,
            id="1_m_n",
        ),
        pytest.param(
            92,
            0,
            0,
            id="1_m_n",
        ),
        pytest.param(
            93,
            0,
            0,
            id="1_m_n",
        ),
        pytest.param(
            94,
            0,
            0,
            id="1_m_n",
        ),
        pytest.param(
            95,
            0,
            0,
            id="1_m_n",
        ),
        pytest.param(
            96,
            0,
            0,
            id="1_m_n",
        ),
        pytest.param(
            97,
            0,
            0,
            id="1_m_n",
        ),
        pytest.param(
            98,
            0,
            0,
            id="1_m_n",
        ),
        pytest.param(
            99,
            0,
            0,
            id="1_m_n",
        ),
        pytest.param(
            100,
            0,
            0,
            id="1_m_n",
        ),
        pytest.param(
            101,
            0,
            0,
            id="m_n_01",
        ),
        pytest.param(
            102,
            0,
            0,
            id="m_n_01",
        ),
        pytest.param(
            103,
            0,
            0,
            id="1_m_n",
        ),
        pytest.param(
            104,
            0,
            0,
            id="m_n_01",
        ),
        pytest.param(
            105,
            0,
            0,
            id="m_n_01",
        ),
        pytest.param(
            106,
            0,
            0,
            id="2_0_2",
        ),
        pytest.param(
            107,
            0,
            0,
            id="m_n_01",
        ),
        pytest.param(
            108,
            0,
            0,
            id="m_n_01",
        ),
        pytest.param(
            109,
            0,
            0,
            id="2_n_2",
        ),
        pytest.param(
            110,
            0,
            0,
            id="m_n_01",
        ),
        pytest.param(
            111,
            0,
            0,
            id="m_n_01",
        ),
        pytest.param(
            112,
            0,
            0,
            id="2_n_2",
        ),
        pytest.param(
            113,
            0,
            0,
            id="3_5_100",
        ),
        pytest.param(
            114,
            0,
            0,
            id="3_9984_39936",
        ),
        pytest.param(
            115,
            0,
            0,
            id="3_28948_11579",
        ),
        pytest.param(
            116,
            0,
            0,
            id="9_37111_37111",
        ),
        pytest.param(
            117,
            0,
            0,
            id="9_3711_37111",
        ),
        pytest.param(
            118,
            0,
            0,
            id="49_2401_2401",
        ),
        pytest.param(
            119,
            0,
            0,
            id="37120_22411_22000",
        ),
        pytest.param(
            120,
            0,
            0,
            id="37120_37111_0",
        ),
        pytest.param(
            121,
            0,
            0,
            id="37120_37111_1",
        ),
        pytest.param(
            122,
            0,
            0,
            id="37120_37111_37111",
        ),
        pytest.param(
            123,
            0,
            0,
            id="7120_37111_97",
        ),
        pytest.param(
            124,
            0,
            0,
            id="37120_37111_97",
        ),
        pytest.param(
            125,
            0,
            0,
            id="39936_1_55201",
        ),
        pytest.param(
            126,
            0,
            0,
            id="55190_55190_42965",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_modexp_tests(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Ori Pomerantz qbzzt1@gmail."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = pre.fund_eoa(amount=0xBA1A9CE0BA1A9CE, nonce=1)

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    # Source: yul
    # berlin
    # {
    #    // Our input values, 20 bytes each
    #    // This is not the most efficient use of gas, but
    #    // this is a test. Readability is more important
    #    let base := calldataload(0x04)
    #    let expV := calldataload(0x24)
    #    let modV := calldataload(0x44)
    #
    #    // Prepare the calldata
    #    mstore(0x00, 0x20)
    #    mstore(0x20, 0x20)
    #    mstore(0x40, 0x20)
    #    mstore(0x60, base)
    #    mstore(0x80, expV)
    #    mstore(0xA0, modV)
    #
    #    let gas0 := gas()
    #    pop(call(gas(), 0x05, 0, 0, 0xC0, 0x100, 0x20))
    #    let gas1 := gas()
    #    sstore(0, mload(0x100))
    #    sstore(1, sub(sub(gas0, gas1), 0x14c))
    # }
    target = pre.deploy_contract(  # noqa: F841
        code=Op.CALLDATALOAD(offset=0x4)
        + Op.CALLDATALOAD(offset=0x24)
        + Op.CALLDATALOAD(offset=0x44)
        + Op.SWAP2
        + Op.MSTORE(offset=0x0, value=0x20)
        + Op.MSTORE(offset=Op.DUP1, value=0x20)
        + Op.MSTORE(offset=0x40, value=0x20)
        + Op.PUSH1[0x60]
        + Op.MSTORE
        + Op.PUSH1[0x80]
        + Op.MSTORE
        + Op.PUSH1[0xA0]
        + Op.MSTORE
        + Op.PUSH2[0x14C]
        + Op.GAS
        + Op.POP(
            Op.CALL(
                gas=Op.GAS,
                address=0x5,
                value=Op.DUP1,
                args_offset=0x0,
                args_size=0xC0,
                ret_offset=0x100,
                ret_size=0x20,
            )
        )
        + Op.GAS
        + Op.SWAP1
        + Op.SSTORE(key=0x0, value=Op.MLOAD(offset=0x100))
        + Op.SUB
        + Op.SSTORE(key=0x1, value=Op.SUB)
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=1,
    )

    expect_posts: list[dict] = [
        {target: Account(storage={0: 0, 1: 1})},
        {target: Account(storage={0: 1, 1: 1})},
        {target: Account(storage={0: 43, 1: 1})},
        {target: Account(storage={0: 26625, 1: 1})},
        {target: Account(storage={0: 27, 1: 1})},
        {target: Account(storage={0: 34325, 1: 1})},
        {target: Account(storage={0: 7227, 1: 1})},
        {target: Account(storage={0: 16000, 1: 1})},
        {target: Account(storage={0: 80, 1: 1})},
        {target: Account(storage={0: 95, 1: 1})},
        {target: Account(storage={0: 39936, 1: 1})},
        {target: Account(storage={0: 34410, 1: 1})},
    ]
    post = expect_posts[
        {
            (0, 0, 0): 0,
            (1, 0, 0): 0,
            (2, 0, 0): 1,
            (3, 0, 0): 1,
            (4, 0, 0): 1,
            (5, 0, 0): 1,
            (6, 0, 0): 1,
            (7, 0, 0): 1,
            (8, 0, 0): 1,
            (9, 0, 0): 1,
            (10, 0, 0): 1,
            (11, 0, 0): 1,
            (12, 0, 0): 1,
            (13, 0, 0): 1,
            (14, 0, 0): 1,
            (15, 0, 0): 1,
            (16, 0, 0): 1,
            (17, 0, 0): 0,
            (18, 0, 0): 0,
            (19, 0, 0): 0,
            (20, 0, 0): 0,
            (21, 0, 0): 0,
            (22, 0, 0): 0,
            (23, 0, 0): 0,
            (24, 0, 0): 0,
            (25, 0, 0): 0,
            (26, 0, 0): 0,
            (27, 0, 0): 0,
            (28, 0, 0): 0,
            (29, 0, 0): 0,
            (30, 0, 0): 0,
            (31, 0, 0): 0,
            (32, 0, 0): 0,
            (33, 0, 0): 0,
            (34, 0, 0): 0,
            (35, 0, 0): 0,
            (36, 0, 0): 0,
            (37, 0, 0): 0,
            (38, 0, 0): 0,
            (39, 0, 0): 0,
            (40, 0, 0): 0,
            (41, 0, 0): 0,
            (42, 0, 0): 0,
            (43, 0, 0): 0,
            (44, 0, 0): 0,
            (45, 0, 0): 0,
            (46, 0, 0): 0,
            (47, 0, 0): 0,
            (48, 0, 0): 0,
            (49, 0, 0): 0,
            (50, 0, 0): 0,
            (51, 0, 0): 0,
            (52, 0, 0): 0,
            (53, 0, 0): 0,
            (54, 0, 0): 0,
            (55, 0, 0): 0,
            (56, 0, 0): 0,
            (57, 0, 0): 0,
            (58, 0, 0): 0,
            (59, 0, 0): 0,
            (60, 0, 0): 0,
            (61, 0, 0): 0,
            (62, 0, 0): 0,
            (63, 0, 0): 0,
            (64, 0, 0): 0,
            (65, 0, 0): 0,
            (66, 0, 0): 0,
            (67, 0, 0): 0,
            (68, 0, 0): 0,
            (69, 0, 0): 1,
            (70, 0, 0): 1,
            (71, 0, 0): 1,
            (72, 0, 0): 1,
            (73, 0, 0): 1,
            (74, 0, 0): 1,
            (75, 0, 0): 1,
            (76, 0, 0): 1,
            (77, 0, 0): 1,
            (78, 0, 0): 1,
            (79, 0, 0): 1,
            (80, 0, 0): 1,
            (81, 0, 0): 1,
            (82, 0, 0): 1,
            (83, 0, 0): 1,
            (84, 0, 0): 0,
            (85, 0, 0): 0,
            (86, 0, 0): 1,
            (87, 0, 0): 1,
            (88, 0, 0): 1,
            (89, 0, 0): 1,
            (90, 0, 0): 1,
            (91, 0, 0): 1,
            (92, 0, 0): 1,
            (93, 0, 0): 1,
            (94, 0, 0): 1,
            (95, 0, 0): 1,
            (96, 0, 0): 1,
            (97, 0, 0): 1,
            (98, 0, 0): 1,
            (99, 0, 0): 1,
            (100, 0, 0): 1,
            (101, 0, 0): 0,
            (102, 0, 0): 0,
            (103, 0, 0): 1,
            (104, 0, 0): 0,
            (105, 0, 0): 0,
            (106, 0, 0): 1,
            (107, 0, 0): 0,
            (108, 0, 0): 0,
            (109, 0, 0): 0,
            (110, 0, 0): 0,
            (111, 0, 0): 0,
            (112, 0, 0): 0,
            (113, 0, 0): 2,
            (114, 0, 0): 3,
            (115, 0, 0): 4,
            (116, 0, 0): 6,
            (117, 0, 0): 5,
            (118, 0, 0): 0,
            (119, 0, 0): 7,
            (120, 0, 0): 0,
            (121, 0, 0): 0,
            (122, 0, 0): 6,
            (123, 0, 0): 8,
            (124, 0, 0): 9,
            (125, 0, 0): 10,
            (126, 0, 0): 11,
        }[d, g, v]
    ]
    _exc = None

    tx_data = [
        Bytes("048071d3") + Hash(0x0) + Hash(0x0) + Hash(0x0),
        Bytes("048071d3") + Hash(0x0) + Hash(0x0) + Hash(0x1),
        Bytes("048071d3") + Hash(0x0) + Hash(0x0) + Hash(0x2),
        Bytes("048071d3") + Hash(0x0) + Hash(0x0) + Hash(0x4),
        Bytes("048071d3") + Hash(0x0) + Hash(0x0) + Hash(0x8),
        Bytes("048071d3") + Hash(0x0) + Hash(0x0) + Hash(0x10),
        Bytes("048071d3") + Hash(0x0) + Hash(0x0) + Hash(0x20),
        Bytes("048071d3") + Hash(0x0) + Hash(0x0) + Hash(0x40),
        Bytes("048071d3") + Hash(0x0) + Hash(0x0) + Hash(0x64),
        Bytes("048071d3") + Hash(0x0) + Hash(0x0) + Hash(0x80),
        Bytes("048071d3") + Hash(0x0) + Hash(0x0) + Hash(0x1001),
        Bytes("048071d3") + Hash(0x0) + Hash(0x0) + Hash(0x100002),
        Bytes("048071d3") + Hash(0x0) + Hash(0x0) + Hash(0x10000004),
        Bytes("048071d3") + Hash(0x0) + Hash(0x0) + Hash(0x1000000008),
        Bytes("048071d3") + Hash(0x0) + Hash(0x0) + Hash(0xFFFFFFFFFFFF),
        Bytes("048071d3") + Hash(0x0) + Hash(0x0) + Hash(0xFFFFFFFFFFFFFF),
        Bytes("048071d3") + Hash(0x0) + Hash(0x0) + Hash(0xFFFFFFFFFFFFFFFF),
        Bytes("048071d3") + Hash(0x0) + Hash(0x1) + Hash(0x0),
        Bytes("048071d3") + Hash(0x0) + Hash(0x1) + Hash(0x1),
        Bytes("048071d3") + Hash(0x0) + Hash(0x1) + Hash(0x2),
        Bytes("048071d3") + Hash(0x0) + Hash(0x1) + Hash(0x4),
        Bytes("048071d3") + Hash(0x0) + Hash(0x1) + Hash(0x8),
        Bytes("048071d3") + Hash(0x0) + Hash(0x1) + Hash(0x10),
        Bytes("048071d3") + Hash(0x0) + Hash(0x1) + Hash(0x20),
        Bytes("048071d3") + Hash(0x0) + Hash(0x1) + Hash(0x40),
        Bytes("048071d3") + Hash(0x0) + Hash(0x1) + Hash(0x64),
        Bytes("048071d3") + Hash(0x0) + Hash(0x1) + Hash(0x80),
        Bytes("048071d3") + Hash(0x0) + Hash(0x1) + Hash(0x1001),
        Bytes("048071d3") + Hash(0x0) + Hash(0x1) + Hash(0x100002),
        Bytes("048071d3") + Hash(0x0) + Hash(0x1) + Hash(0x10000004),
        Bytes("048071d3") + Hash(0x0) + Hash(0x1) + Hash(0x1000000008),
        Bytes("048071d3") + Hash(0x0) + Hash(0x1) + Hash(0xFFFFFFFFFFFF),
        Bytes("048071d3") + Hash(0x0) + Hash(0x1) + Hash(0xFFFFFFFFFFFFFF),
        Bytes("048071d3") + Hash(0x0) + Hash(0x1) + Hash(0xFFFFFFFFFFFFFFFF),
        Bytes("048071d3") + Hash(0x0) + Hash(0x2) + Hash(0x0),
        Bytes("048071d3") + Hash(0x0) + Hash(0x2) + Hash(0x1),
        Bytes("048071d3") + Hash(0x0) + Hash(0x2) + Hash(0x2),
        Bytes("048071d3") + Hash(0x0) + Hash(0x3) + Hash(0x2),
        Bytes("048071d3") + Hash(0x0) + Hash(0x3) + Hash(0x4),
        Bytes("048071d3") + Hash(0x0) + Hash(0x3) + Hash(0x8),
        Bytes("048071d3") + Hash(0x0) + Hash(0x3) + Hash(0x10),
        Bytes("048071d3") + Hash(0x0) + Hash(0x3) + Hash(0x20),
        Bytes("048071d3") + Hash(0x0) + Hash(0x3) + Hash(0x40),
        Bytes("048071d3") + Hash(0x0) + Hash(0x3) + Hash(0x64),
        Bytes("048071d3") + Hash(0x0) + Hash(0x3) + Hash(0x80),
        Bytes("048071d3") + Hash(0x0) + Hash(0x3) + Hash(0x1001),
        Bytes("048071d3") + Hash(0x0) + Hash(0x3) + Hash(0x100002),
        Bytes("048071d3") + Hash(0x0) + Hash(0x3) + Hash(0x10000004),
        Bytes("048071d3") + Hash(0x0) + Hash(0x3) + Hash(0x1000000008),
        Bytes("048071d3") + Hash(0x0) + Hash(0x3) + Hash(0xFFFFFFFFFFFF),
        Bytes("048071d3") + Hash(0x0) + Hash(0x3) + Hash(0xFFFFFFFFFFFFFF),
        Bytes("048071d3") + Hash(0x0) + Hash(0x3) + Hash(0xFFFFFFFFFFFFFFFF),
        Bytes("048071d3") + Hash(0x0) + Hash(0xFFFFFF) + Hash(0x2),
        Bytes("048071d3") + Hash(0x0) + Hash(0xFFFFFF) + Hash(0x4),
        Bytes("048071d3") + Hash(0x0) + Hash(0xFFFFFF) + Hash(0x8),
        Bytes("048071d3") + Hash(0x0) + Hash(0xFFFFFF) + Hash(0x10),
        Bytes("048071d3") + Hash(0x0) + Hash(0xFFFFFF) + Hash(0x20),
        Bytes("048071d3") + Hash(0x0) + Hash(0xFFFFFF) + Hash(0x40),
        Bytes("048071d3") + Hash(0x0) + Hash(0xFFFFFF) + Hash(0x64),
        Bytes("048071d3") + Hash(0x0) + Hash(0xFFFFFF) + Hash(0x80),
        Bytes("048071d3") + Hash(0x0) + Hash(0xFFFFFF) + Hash(0x1001),
        Bytes("048071d3") + Hash(0x0) + Hash(0xFFFFFF) + Hash(0x100002),
        Bytes("048071d3") + Hash(0x0) + Hash(0xFFFFFF) + Hash(0x10000004),
        Bytes("048071d3") + Hash(0x0) + Hash(0xFFFFFF) + Hash(0x1000000008),
        Bytes("048071d3") + Hash(0x0) + Hash(0xFFFFFF) + Hash(0xFFFFFFFFFFFF),
        Bytes("048071d3")
        + Hash(0x0)
        + Hash(0xFFFFFF)
        + Hash(0xFFFFFFFFFFFFFF),
        Bytes("048071d3")
        + Hash(0x0)
        + Hash(0xFFFFFF)
        + Hash(0xFFFFFFFFFFFFFFFF),
        Bytes("048071d3") + Hash(0x1) + Hash(0x0) + Hash(0x0),
        Bytes("048071d3") + Hash(0x1) + Hash(0x0) + Hash(0x1),
        Bytes("048071d3") + Hash(0x1) + Hash(0x0) + Hash(0x2),
        Bytes("048071d3") + Hash(0x1) + Hash(0x0) + Hash(0x4),
        Bytes("048071d3") + Hash(0x1) + Hash(0x0) + Hash(0x8),
        Bytes("048071d3") + Hash(0x1) + Hash(0x0) + Hash(0x10),
        Bytes("048071d3") + Hash(0x1) + Hash(0x0) + Hash(0x20),
        Bytes("048071d3") + Hash(0x1) + Hash(0x0) + Hash(0x40),
        Bytes("048071d3") + Hash(0x1) + Hash(0x0) + Hash(0x64),
        Bytes("048071d3") + Hash(0x1) + Hash(0x0) + Hash(0x80),
        Bytes("048071d3") + Hash(0x1) + Hash(0x0) + Hash(0x1001),
        Bytes("048071d3") + Hash(0x1) + Hash(0x0) + Hash(0x100002),
        Bytes("048071d3") + Hash(0x1) + Hash(0x0) + Hash(0x10000004),
        Bytes("048071d3") + Hash(0x1) + Hash(0x0) + Hash(0x1000000008),
        Bytes("048071d3") + Hash(0x1) + Hash(0x0) + Hash(0xFFFFFFFFFFFF),
        Bytes("048071d3") + Hash(0x1) + Hash(0x0) + Hash(0xFFFFFFFFFFFFFF),
        Bytes("048071d3") + Hash(0x1) + Hash(0x0) + Hash(0xFFFFFFFFFFFFFFFF),
        Bytes("048071d3") + Hash(0x1) + Hash(0x1) + Hash(0x0),
        Bytes("048071d3") + Hash(0x1) + Hash(0x1) + Hash(0x1),
        Bytes("048071d3") + Hash(0x1) + Hash(0x1) + Hash(0x2),
        Bytes("048071d3") + Hash(0x1) + Hash(0x1) + Hash(0x4),
        Bytes("048071d3") + Hash(0x1) + Hash(0x1) + Hash(0x8),
        Bytes("048071d3") + Hash(0x1) + Hash(0x1) + Hash(0x10),
        Bytes("048071d3") + Hash(0x1) + Hash(0x1) + Hash(0x20),
        Bytes("048071d3") + Hash(0x1) + Hash(0x1) + Hash(0x40),
        Bytes("048071d3") + Hash(0x1) + Hash(0x1) + Hash(0x64),
        Bytes("048071d3") + Hash(0x1) + Hash(0x1) + Hash(0x80),
        Bytes("048071d3") + Hash(0x1) + Hash(0x1) + Hash(0x1001),
        Bytes("048071d3") + Hash(0x1) + Hash(0x1) + Hash(0x100002),
        Bytes("048071d3") + Hash(0x1) + Hash(0x1) + Hash(0x10000004),
        Bytes("048071d3") + Hash(0x1) + Hash(0x1) + Hash(0x1000000008),
        Bytes("048071d3") + Hash(0x1) + Hash(0x1) + Hash(0xFFFFFFFFFFFF),
        Bytes("048071d3") + Hash(0x1) + Hash(0x1) + Hash(0xFFFFFFFFFFFFFF),
        Bytes("048071d3") + Hash(0x1) + Hash(0x1) + Hash(0xFFFFFFFFFFFFFFFF),
        Bytes("048071d3") + Hash(0x1) + Hash(0x2) + Hash(0x0),
        Bytes("048071d3") + Hash(0x1) + Hash(0x2) + Hash(0x1),
        Bytes("048071d3") + Hash(0x1) + Hash(0x2) + Hash(0x2),
        Bytes("048071d3") + Hash(0x2) + Hash(0x0) + Hash(0x0),
        Bytes("048071d3") + Hash(0x2) + Hash(0x0) + Hash(0x1),
        Bytes("048071d3") + Hash(0x2) + Hash(0x0) + Hash(0x2),
        Bytes("048071d3") + Hash(0x2) + Hash(0x1) + Hash(0x0),
        Bytes("048071d3") + Hash(0x2) + Hash(0x1) + Hash(0x1),
        Bytes("048071d3") + Hash(0x2) + Hash(0x1) + Hash(0x2),
        Bytes("048071d3") + Hash(0x2) + Hash(0x2) + Hash(0x0),
        Bytes("048071d3") + Hash(0x2) + Hash(0x2) + Hash(0x1),
        Bytes("048071d3") + Hash(0x2) + Hash(0x2) + Hash(0x2),
        Bytes("048071d3") + Hash(0x3) + Hash(0x5) + Hash(0x64),
        Bytes("048071d3") + Hash(0x3) + Hash(0x2700) + Hash(0x9C00),
        Bytes("048071d3") + Hash(0x3) + Hash(0x7114) + Hash(0x2D3B),
        Bytes("048071d3") + Hash(0x9) + Hash(0x90F7) + Hash(0x90F7),
        Bytes("048071d3") + Hash(0x9) + Hash(0xE7F) + Hash(0x90F7),
        Bytes("048071d3") + Hash(0x31) + Hash(0x961) + Hash(0x961),
        Bytes("048071d3") + Hash(0x9100) + Hash(0x578B) + Hash(0x55F0),
        Bytes("048071d3") + Hash(0x9100) + Hash(0x90F7) + Hash(0x0),
        Bytes("048071d3") + Hash(0x9100) + Hash(0x90F7) + Hash(0x1),
        Bytes("048071d3") + Hash(0x9100) + Hash(0x90F7) + Hash(0x90F7),
        Bytes("048071d3") + Hash(0x1BD0) + Hash(0x90F7) + Hash(0x61),
        Bytes("048071d3") + Hash(0x9100) + Hash(0x90F7) + Hash(0x61),
        Bytes("048071d3") + Hash(0x9C00) + Hash(0x1) + Hash(0xD7A1),
        Bytes("048071d3") + Hash(0xD796) + Hash(0xD796) + Hash(0xA7D5),
    ]
    tx_gas = [16777216]

    tx = Transaction(
        sender=sender,
        to=target,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        nonce=1,
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
