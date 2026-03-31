"""
Ori Pomerantz qbzzt1@gmail.com.

Ported from:
state_tests/stMemoryTest/bufferSrcOffsetFiller.yml
"""

import pytest
from execution_testing import (
    EOA,
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
from execution_testing.specs.static_state.expect_section import (
    resolve_expect_post,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stMemoryTest/bufferSrcOffsetFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            1,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            2,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            3,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            4,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            5,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            6,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            7,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            8,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            9,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            10,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            11,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            12,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            13,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            14,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            15,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            16,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            17,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            18,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            19,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            20,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            21,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            22,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            23,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            24,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            25,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            26,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            27,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            28,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            29,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            30,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            31,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            32,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            33,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            34,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            35,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            36,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            37,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            38,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            39,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            40,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            41,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            42,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            43,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            44,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            45,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            46,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            47,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            48,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            49,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            50,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            51,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            52,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            53,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            54,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            55,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            56,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            57,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            58,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            59,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            60,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            61,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            62,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            63,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            64,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            65,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            66,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            67,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            68,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            69,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            70,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            71,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            72,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            73,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            74,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            75,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            76,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            77,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            78,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            79,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            80,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            81,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            82,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            83,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            84,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            85,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            86,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            87,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            88,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            89,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            90,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            91,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            92,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            93,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            94,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            95,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            96,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            97,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            98,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            99,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            100,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            101,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            102,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            103,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            104,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            105,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            106,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            107,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            108,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            109,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            110,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            111,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            112,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            113,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            114,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            115,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            116,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            117,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            118,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            119,
            0,
            0,
            id="fail",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_buffer_src_offset(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Ori Pomerantz qbzzt1@gmail."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    contract_0 = Address(0x000000000000000000000000000000000000C0DE)
    contract_1 = Address(0xCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC)
    sender = EOA(
        key=0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    # Source: lll
    # {
    #       (return 0 0x120)
    # }
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=Op.RETURN(offset=0x0, size=0x120) + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x000000000000000000000000000000000000C0DE),  # noqa: E501
    )
    # Source: lll
    # {
    #    (def 'opcode $4)
    #    (def 'bufferType $36)
    #    (def 'bufferLength $68)
    #    (def 'NOP 0)
    #
    #    ; Variables
    #    (def 'srcOffset  0x2020)
    #    (def 'offset     0x2040)
    #    (def 'length     0x2060)
    #
    #    [offset] 0    ; Write to the first word in memory
    #
    #    ; bufferType 0  is no offset (0x0)
    #    ; bufferType 1  is a reasonable number as an offset (0x10)
    #    ; bufferType 2  is a high number that could happen in theory (0x100000)  # noqa: E501
    #    ; bufferType 3  is a negative number (- 0 0x10)
    #    ; bufferType 4  is 2^31-1 0x7FFFFFFF
    #    ; bufferType 5  is 2^31   0x80000000
    #    ; bufferType 6  is 2^32-1 0xFFFFFFFF
    #    ; bufferType 7  is 2^32   0x0100000000
    #    ; bufferType 8  is 2^63-1 0x7FFFFFFFFFFFFFFF
    #    ; bufferType 9  is 2^63   0x8000000000000000
    #    ; bufferType 10 is 2^64-1 0xFFFFFFFFFFFFFFFF
    #    ; bufferType 11 is 2^64   0x010000000000000000
    #    (if (= bufferType 0)  [srcOffset] 0 NOP)
    #    (if (= bufferType 1)  [srcOffset] 0x10 NOP)
    #    (if (= bufferType 2)  [srcOffset] 0100000 NOP)
    #    (if (= bufferType 3)  [srcOffset] (- 0 0x10) NOP)
    #    (if (= bufferType 4)  [srcOffset] 0x7FFFFFFF NOP)
    # ... (40 more lines)
    contract_1 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x2040, value=0x0)
        + Op.JUMPI(
            pc=Op.PUSH2[0x17],
            condition=Op.EQ(Op.CALLDATALOAD(offset=0x24), 0x0),
        )
        + Op.POP(0x0)
        + Op.JUMP(pc=Op.PUSH2[0x1E])
        + Op.JUMPDEST
        + Op.MSTORE(offset=0x2020, value=0x0)
        + Op.JUMPDEST
        + Op.JUMPI(
            pc=Op.PUSH2[0x30],
            condition=Op.EQ(Op.CALLDATALOAD(offset=0x24), 0x1),
        )
        + Op.POP(0x0)
        + Op.JUMP(pc=Op.PUSH2[0x37])
        + Op.JUMPDEST
        + Op.MSTORE(offset=0x2020, value=0x10)
        + Op.JUMPDEST
        + Op.JUMPI(
            pc=Op.PUSH2[0x49],
            condition=Op.EQ(Op.CALLDATALOAD(offset=0x24), 0x2),
        )
        + Op.POP(0x0)
        + Op.JUMP(pc=Op.PUSH2[0x51])
        + Op.JUMPDEST
        + Op.MSTORE(offset=0x2020, value=0x8000)
        + Op.JUMPDEST
        + Op.JUMPI(
            pc=Op.PUSH2[0x63],
            condition=Op.EQ(Op.CALLDATALOAD(offset=0x24), 0x3),
        )
        + Op.POP(0x0)
        + Op.JUMP(pc=Op.PUSH2[0x6D])
        + Op.JUMPDEST
        + Op.MSTORE(offset=0x2020, value=Op.SUB(0x0, 0x10))
        + Op.JUMPDEST
        + Op.JUMPI(
            pc=Op.PUSH2[0x7F],
            condition=Op.EQ(Op.CALLDATALOAD(offset=0x24), 0x4),
        )
        + Op.POP(0x0)
        + Op.JUMP(pc=Op.PUSH2[0x89])
        + Op.JUMPDEST
        + Op.MSTORE(offset=0x2020, value=0x7FFFFFFF)
        + Op.JUMPDEST
        + Op.JUMPI(
            pc=Op.PUSH2[0x9B],
            condition=Op.EQ(Op.CALLDATALOAD(offset=0x24), 0x5),
        )
        + Op.POP(0x0)
        + Op.JUMP(pc=Op.PUSH2[0xA5])
        + Op.JUMPDEST
        + Op.MSTORE(offset=0x2020, value=0x80000000)
        + Op.JUMPDEST
        + Op.JUMPI(
            pc=Op.PUSH2[0xB7],
            condition=Op.EQ(Op.CALLDATALOAD(offset=0x24), 0x6),
        )
        + Op.POP(0x0)
        + Op.JUMP(pc=Op.PUSH2[0xC1])
        + Op.JUMPDEST
        + Op.MSTORE(offset=0x2020, value=0xFFFFFFFF)
        + Op.JUMPDEST
        + Op.JUMPI(
            pc=Op.PUSH2[0xD3],
            condition=Op.EQ(Op.CALLDATALOAD(offset=0x24), 0x7),
        )
        + Op.POP(0x0)
        + Op.JUMP(pc=Op.PUSH2[0xDE])
        + Op.JUMPDEST
        + Op.MSTORE(offset=0x2020, value=0x100000000)
        + Op.JUMPDEST
        + Op.JUMPI(
            pc=Op.PUSH2[0xF0],
            condition=Op.EQ(Op.CALLDATALOAD(offset=0x24), 0x8),
        )
        + Op.POP(0x0)
        + Op.JUMP(pc=Op.PUSH2[0xFE])
        + Op.JUMPDEST
        + Op.MSTORE(offset=0x2020, value=0x7FFFFFFFFFFFFFFF)
        + Op.JUMPDEST
        + Op.JUMPI(
            pc=0x110, condition=Op.EQ(Op.CALLDATALOAD(offset=0x24), 0x9)
        )
        + Op.POP(0x0)
        + Op.JUMP(pc=0x11E)
        + Op.JUMPDEST
        + Op.MSTORE(offset=0x2020, value=0x8000000000000000)
        + Op.JUMPDEST
        + Op.JUMPI(
            pc=0x130, condition=Op.EQ(Op.CALLDATALOAD(offset=0x24), 0xA)
        )
        + Op.POP(0x0)
        + Op.JUMP(pc=0x13E)
        + Op.JUMPDEST
        + Op.MSTORE(offset=0x2020, value=0xFFFFFFFFFFFFFFFF)
        + Op.JUMPDEST
        + Op.JUMPI(
            pc=0x150, condition=Op.EQ(Op.CALLDATALOAD(offset=0x24), 0xB)
        )
        + Op.POP(0x0)
        + Op.JUMP(pc=0x15F)
        + Op.JUMPDEST
        + Op.MSTORE(offset=0x2020, value=0x10000000000000000)
        + Op.JUMPDEST
        + Op.JUMPI(
            pc=0x171, condition=Op.EQ(Op.CALLDATALOAD(offset=0x44), 0x0)
        )
        + Op.POP(0x0)
        + Op.JUMP(pc=0x178)
        + Op.JUMPDEST
        + Op.MSTORE(offset=0x2060, value=0x0)
        + Op.JUMPDEST
        + Op.JUMPI(
            pc=0x18A, condition=Op.EQ(Op.CALLDATALOAD(offset=0x44), 0x1)
        )
        + Op.POP(0x0)
        + Op.JUMP(pc=0x191)
        + Op.JUMPDEST
        + Op.MSTORE(offset=0x2060, value=0x10)
        + Op.JUMPDEST
        + Op.JUMPI(
            pc=0x1A3, condition=Op.EQ(Op.CALLDATALOAD(offset=0x44), 0x2)
        )
        + Op.POP(0x0)
        + Op.JUMP(pc=0x1AB)
        + Op.JUMPDEST
        + Op.MSTORE(offset=0x2060, value=0x8000)
        + Op.JUMPDEST
        + Op.JUMPI(
            pc=0x1BD, condition=Op.EQ(Op.CALLDATALOAD(offset=0x44), 0x3)
        )
        + Op.POP(0x0)
        + Op.JUMP(pc=0x1C7)
        + Op.JUMPDEST
        + Op.MSTORE(offset=0x2060, value=Op.SUB(0x0, 0x10))
        + Op.JUMPDEST
        + Op.JUMPI(
            pc=0x1D9, condition=Op.EQ(Op.CALLDATALOAD(offset=0x4), 0x37)
        )
        + Op.POP(0x0)
        + Op.JUMP(pc=0x1E7)
        + Op.JUMPDEST
        + Op.CALLDATACOPY(
            dest_offset=Op.MLOAD(offset=0x2040),
            offset=Op.MLOAD(offset=0x2020),
            size=Op.MLOAD(offset=0x2060),
        )
        + Op.JUMPDEST
        + Op.JUMPI(
            pc=0x1F9, condition=Op.EQ(Op.CALLDATALOAD(offset=0x4), 0x39)
        )
        + Op.POP(0x0)
        + Op.JUMP(pc=0x207)
        + Op.JUMPDEST
        + Op.CODECOPY(
            dest_offset=Op.MLOAD(offset=0x2040),
            offset=Op.MLOAD(offset=0x2020),
            size=Op.MLOAD(offset=0x2060),
        )
        + Op.JUMPDEST
        + Op.JUMPI(
            pc=0x219, condition=Op.EQ(Op.CALLDATALOAD(offset=0x4), 0x3C)
        )
        + Op.POP(0x0)
        + Op.JUMP(pc=0x22A)
        + Op.JUMPDEST
        + Op.EXTCODECOPY(
            address=0xC0DE,
            dest_offset=Op.MLOAD(offset=0x2040),
            offset=Op.MLOAD(offset=0x2020),
            size=Op.MLOAD(offset=0x2060),
        )
        + Op.JUMPDEST
        + Op.JUMPI(
            pc=0x23C, condition=Op.EQ(Op.CALLDATALOAD(offset=0x4), 0x3E)
        )
        + Op.POP(0x0)
        + Op.JUMP(pc=0x24A)
        + Op.JUMPDEST
        + Op.RETURNDATACOPY(
            dest_offset=Op.MLOAD(offset=0x2040),
            offset=Op.MLOAD(offset=0x2020),
            size=Op.MLOAD(offset=0x2060),
        )
        + Op.JUMPDEST
        + Op.JUMPI(
            pc=0x25D, condition=Op.EQ(Op.CALLDATALOAD(offset=0x4), 0x13E)
        )
        + Op.POP(0x0)
        + Op.JUMP(pc=0x27F)
        + Op.JUMPDEST
        + Op.POP(
            Op.CALL(
                gas=0x1000,
                address=0xC0DE,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x100,
                ret_size=0x100,
            )
        )
        + Op.RETURNDATACOPY(
            dest_offset=Op.MLOAD(offset=0x2040),
            offset=Op.MLOAD(offset=0x2020),
            size=Op.MLOAD(offset=0x2060),
        )
        + Op.JUMPDEST
        + Op.SSTORE(key=0x100, value=0x0)
        + Op.JUMPI(
            pc=0x298,
            condition=Op.ISZERO(Op.LT(Op.CALLDATALOAD(offset=0x24), 0x3)),
        )
        + Op.POP(0x0)
        + Op.JUMP(pc=0x2A5)
        + Op.JUMPDEST
        + Op.SSTORE(key=0x0, value=Op.MLOAD(offset=0x0))
        + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x20))
        + Op.JUMPDEST
        + Op.STOP,
        storage={256: 24743},
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0xCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC),  # noqa: E501
    )
    pre[sender] = Account(balance=0xBA1A9CE0BA1A9CE)

    expect_entries_: list[dict] = [
        {
            "indexes": {
                "data": [
                    0,
                    1,
                    2,
                    4,
                    5,
                    6,
                    8,
                    9,
                    10,
                    12,
                    13,
                    14,
                    16,
                    17,
                    18,
                    19,
                    20,
                    21,
                    22,
                    23,
                    24,
                    25,
                    26,
                    28,
                    29,
                    30,
                    32,
                    33,
                    34,
                    36,
                    37,
                    38,
                    40,
                    41,
                    42,
                    43,
                    44,
                    45,
                    46,
                    47,
                    48,
                    49,
                    50,
                    52,
                    53,
                    54,
                    56,
                    57,
                    58,
                    60,
                    61,
                    62,
                    64,
                    65,
                    66,
                    67,
                    68,
                    69,
                    70,
                    71,
                    72,
                    96,
                    97,
                    100,
                    101,
                ],
                "gas": -1,
                "value": -1,
            },
            "network": [">=Cancun"],
            "result": {contract_1: Account(storage={0: 0, 1: 0, 256: 0})},
        },
        {
            "indexes": {
                "data": [
                    3,
                    7,
                    11,
                    15,
                    27,
                    31,
                    35,
                    39,
                    51,
                    55,
                    59,
                    63,
                    73,
                    74,
                    75,
                    76,
                    77,
                    78,
                    79,
                    80,
                    81,
                    82,
                    83,
                    84,
                    85,
                    86,
                    87,
                    88,
                    89,
                    90,
                    91,
                    92,
                    93,
                    94,
                    95,
                    98,
                    99,
                    102,
                    103,
                    104,
                    105,
                    106,
                    107,
                    108,
                    109,
                    110,
                    111,
                    112,
                    113,
                    114,
                    115,
                    116,
                    117,
                    118,
                    119,
                ],
                "gas": -1,
                "value": -1,
            },
            "network": [">=Cancun"],
            "result": {contract_1: Account(storage={256: 24743})},
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx_data = [
        Bytes("048071d3") + Hash(0x37) + Hash(0x0) + Hash(0x0),
        Bytes("048071d3") + Hash(0x37) + Hash(0x0) + Hash(0x1),
        Bytes("048071d3") + Hash(0x37) + Hash(0x0) + Hash(0x2),
        Bytes("048071d3") + Hash(0x37) + Hash(0x0) + Hash(0x3),
        Bytes("048071d3") + Hash(0x37) + Hash(0x1) + Hash(0x0),
        Bytes("048071d3") + Hash(0x37) + Hash(0x1) + Hash(0x1),
        Bytes("048071d3") + Hash(0x37) + Hash(0x1) + Hash(0x2),
        Bytes("048071d3") + Hash(0x37) + Hash(0x1) + Hash(0x3),
        Bytes("048071d3") + Hash(0x37) + Hash(0x2) + Hash(0x0),
        Bytes("048071d3") + Hash(0x37) + Hash(0x2) + Hash(0x1),
        Bytes("048071d3") + Hash(0x37) + Hash(0x2) + Hash(0x2),
        Bytes("048071d3") + Hash(0x37) + Hash(0x2) + Hash(0x3),
        Bytes("048071d3") + Hash(0x37) + Hash(0x3) + Hash(0x0),
        Bytes("048071d3") + Hash(0x37) + Hash(0x3) + Hash(0x1),
        Bytes("048071d3") + Hash(0x37) + Hash(0x3) + Hash(0x2),
        Bytes("048071d3") + Hash(0x37) + Hash(0x3) + Hash(0x3),
        Bytes("048071d3") + Hash(0x37) + Hash(0x4) + Hash(0x1),
        Bytes("048071d3") + Hash(0x37) + Hash(0x5) + Hash(0x1),
        Bytes("048071d3") + Hash(0x37) + Hash(0x6) + Hash(0x1),
        Bytes("048071d3") + Hash(0x37) + Hash(0x7) + Hash(0x1),
        Bytes("048071d3") + Hash(0x37) + Hash(0x8) + Hash(0x1),
        Bytes("048071d3") + Hash(0x37) + Hash(0x9) + Hash(0x1),
        Bytes("048071d3") + Hash(0x37) + Hash(0xA) + Hash(0x1),
        Bytes("048071d3") + Hash(0x37) + Hash(0xB) + Hash(0x1),
        Bytes("048071d3") + Hash(0x39) + Hash(0x0) + Hash(0x0),
        Bytes("048071d3") + Hash(0x39) + Hash(0x0) + Hash(0x1),
        Bytes("048071d3") + Hash(0x39) + Hash(0x0) + Hash(0x2),
        Bytes("048071d3") + Hash(0x39) + Hash(0x0) + Hash(0x3),
        Bytes("048071d3") + Hash(0x39) + Hash(0x1) + Hash(0x0),
        Bytes("048071d3") + Hash(0x39) + Hash(0x1) + Hash(0x1),
        Bytes("048071d3") + Hash(0x39) + Hash(0x1) + Hash(0x2),
        Bytes("048071d3") + Hash(0x39) + Hash(0x1) + Hash(0x3),
        Bytes("048071d3") + Hash(0x39) + Hash(0x2) + Hash(0x0),
        Bytes("048071d3") + Hash(0x39) + Hash(0x2) + Hash(0x1),
        Bytes("048071d3") + Hash(0x39) + Hash(0x2) + Hash(0x2),
        Bytes("048071d3") + Hash(0x39) + Hash(0x2) + Hash(0x3),
        Bytes("048071d3") + Hash(0x39) + Hash(0x3) + Hash(0x0),
        Bytes("048071d3") + Hash(0x39) + Hash(0x3) + Hash(0x1),
        Bytes("048071d3") + Hash(0x39) + Hash(0x3) + Hash(0x2),
        Bytes("048071d3") + Hash(0x39) + Hash(0x3) + Hash(0x3),
        Bytes("048071d3") + Hash(0x39) + Hash(0x4) + Hash(0x1),
        Bytes("048071d3") + Hash(0x39) + Hash(0x5) + Hash(0x1),
        Bytes("048071d3") + Hash(0x39) + Hash(0x6) + Hash(0x1),
        Bytes("048071d3") + Hash(0x39) + Hash(0x7) + Hash(0x1),
        Bytes("048071d3") + Hash(0x39) + Hash(0x8) + Hash(0x1),
        Bytes("048071d3") + Hash(0x39) + Hash(0x9) + Hash(0x1),
        Bytes("048071d3") + Hash(0x39) + Hash(0xA) + Hash(0x1),
        Bytes("048071d3") + Hash(0x39) + Hash(0xB) + Hash(0x1),
        Bytes("048071d3") + Hash(0x3C) + Hash(0x0) + Hash(0x0),
        Bytes("048071d3") + Hash(0x3C) + Hash(0x0) + Hash(0x1),
        Bytes("048071d3") + Hash(0x3C) + Hash(0x0) + Hash(0x2),
        Bytes("048071d3") + Hash(0x3C) + Hash(0x0) + Hash(0x3),
        Bytes("048071d3") + Hash(0x3C) + Hash(0x1) + Hash(0x0),
        Bytes("048071d3") + Hash(0x3C) + Hash(0x1) + Hash(0x1),
        Bytes("048071d3") + Hash(0x3C) + Hash(0x1) + Hash(0x2),
        Bytes("048071d3") + Hash(0x3C) + Hash(0x1) + Hash(0x3),
        Bytes("048071d3") + Hash(0x3C) + Hash(0x2) + Hash(0x0),
        Bytes("048071d3") + Hash(0x3C) + Hash(0x2) + Hash(0x1),
        Bytes("048071d3") + Hash(0x3C) + Hash(0x2) + Hash(0x2),
        Bytes("048071d3") + Hash(0x3C) + Hash(0x2) + Hash(0x3),
        Bytes("048071d3") + Hash(0x3C) + Hash(0x3) + Hash(0x0),
        Bytes("048071d3") + Hash(0x3C) + Hash(0x3) + Hash(0x1),
        Bytes("048071d3") + Hash(0x3C) + Hash(0x3) + Hash(0x2),
        Bytes("048071d3") + Hash(0x3C) + Hash(0x3) + Hash(0x3),
        Bytes("048071d3") + Hash(0x3C) + Hash(0x4) + Hash(0x1),
        Bytes("048071d3") + Hash(0x3C) + Hash(0x5) + Hash(0x1),
        Bytes("048071d3") + Hash(0x3C) + Hash(0x6) + Hash(0x1),
        Bytes("048071d3") + Hash(0x3C) + Hash(0x7) + Hash(0x1),
        Bytes("048071d3") + Hash(0x3C) + Hash(0x8) + Hash(0x1),
        Bytes("048071d3") + Hash(0x3C) + Hash(0x9) + Hash(0x1),
        Bytes("048071d3") + Hash(0x3C) + Hash(0xA) + Hash(0x1),
        Bytes("048071d3") + Hash(0x3C) + Hash(0xB) + Hash(0x1),
        Bytes("048071d3") + Hash(0x3E) + Hash(0x0) + Hash(0x0),
        Bytes("048071d3") + Hash(0x3E) + Hash(0x0) + Hash(0x1),
        Bytes("048071d3") + Hash(0x3E) + Hash(0x0) + Hash(0x2),
        Bytes("048071d3") + Hash(0x3E) + Hash(0x0) + Hash(0x3),
        Bytes("048071d3") + Hash(0x3E) + Hash(0x1) + Hash(0x0),
        Bytes("048071d3") + Hash(0x3E) + Hash(0x1) + Hash(0x1),
        Bytes("048071d3") + Hash(0x3E) + Hash(0x1) + Hash(0x2),
        Bytes("048071d3") + Hash(0x3E) + Hash(0x1) + Hash(0x3),
        Bytes("048071d3") + Hash(0x3E) + Hash(0x2) + Hash(0x0),
        Bytes("048071d3") + Hash(0x3E) + Hash(0x2) + Hash(0x1),
        Bytes("048071d3") + Hash(0x3E) + Hash(0x2) + Hash(0x2),
        Bytes("048071d3") + Hash(0x3E) + Hash(0x2) + Hash(0x3),
        Bytes("048071d3") + Hash(0x3E) + Hash(0x3) + Hash(0x0),
        Bytes("048071d3") + Hash(0x3E) + Hash(0x3) + Hash(0x1),
        Bytes("048071d3") + Hash(0x3E) + Hash(0x3) + Hash(0x2),
        Bytes("048071d3") + Hash(0x3E) + Hash(0x3) + Hash(0x3),
        Bytes("048071d3") + Hash(0x3E) + Hash(0x4) + Hash(0x1),
        Bytes("048071d3") + Hash(0x3E) + Hash(0x5) + Hash(0x1),
        Bytes("048071d3") + Hash(0x3E) + Hash(0x6) + Hash(0x1),
        Bytes("048071d3") + Hash(0x3E) + Hash(0x7) + Hash(0x1),
        Bytes("048071d3") + Hash(0x3E) + Hash(0x8) + Hash(0x1),
        Bytes("048071d3") + Hash(0x3E) + Hash(0x9) + Hash(0x1),
        Bytes("048071d3") + Hash(0x3E) + Hash(0xA) + Hash(0x1),
        Bytes("048071d3") + Hash(0x3E) + Hash(0xB) + Hash(0x1),
        Bytes("048071d3") + Hash(0x13E) + Hash(0x0) + Hash(0x0),
        Bytes("048071d3") + Hash(0x13E) + Hash(0x0) + Hash(0x1),
        Bytes("048071d3") + Hash(0x13E) + Hash(0x0) + Hash(0x2),
        Bytes("048071d3") + Hash(0x13E) + Hash(0x0) + Hash(0x3),
        Bytes("048071d3") + Hash(0x13E) + Hash(0x1) + Hash(0x0),
        Bytes("048071d3") + Hash(0x13E) + Hash(0x1) + Hash(0x1),
        Bytes("048071d3") + Hash(0x13E) + Hash(0x1) + Hash(0x2),
        Bytes("048071d3") + Hash(0x13E) + Hash(0x1) + Hash(0x3),
        Bytes("048071d3") + Hash(0x13E) + Hash(0x2) + Hash(0x0),
        Bytes("048071d3") + Hash(0x13E) + Hash(0x2) + Hash(0x1),
        Bytes("048071d3") + Hash(0x13E) + Hash(0x2) + Hash(0x2),
        Bytes("048071d3") + Hash(0x13E) + Hash(0x2) + Hash(0x3),
        Bytes("048071d3") + Hash(0x13E) + Hash(0x3) + Hash(0x0),
        Bytes("048071d3") + Hash(0x13E) + Hash(0x3) + Hash(0x1),
        Bytes("048071d3") + Hash(0x13E) + Hash(0x3) + Hash(0x2),
        Bytes("048071d3") + Hash(0x13E) + Hash(0x3) + Hash(0x3),
        Bytes("048071d3") + Hash(0x13E) + Hash(0x4) + Hash(0x1),
        Bytes("048071d3") + Hash(0x13E) + Hash(0x5) + Hash(0x1),
        Bytes("048071d3") + Hash(0x13E) + Hash(0x6) + Hash(0x1),
        Bytes("048071d3") + Hash(0x13E) + Hash(0x7) + Hash(0x1),
        Bytes("048071d3") + Hash(0x13E) + Hash(0x8) + Hash(0x1),
        Bytes("048071d3") + Hash(0x13E) + Hash(0x9) + Hash(0x1),
        Bytes("048071d3") + Hash(0x13E) + Hash(0xA) + Hash(0x1),
        Bytes("048071d3") + Hash(0x13E) + Hash(0xB) + Hash(0x1),
    ]
    tx_gas = [16777216]
    tx_value = [1]

    tx = Transaction(
        sender=sender,
        to=contract_1,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        value=tx_value[v],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
