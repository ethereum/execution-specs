"""
Ori Pomerantz qbzzt1@gmail.com.

Ported from:
state_tests/VMTests/vmArithmeticTest/divByZeroFiller.yml
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
    ["state_tests/VMTests/vmArithmeticTest/divByZeroFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0,
            0,
            0,
            id="div_2_0",
        ),
        pytest.param(
            1,
            0,
            0,
            id="div_1_0",
        ),
        pytest.param(
            2,
            0,
            0,
            id="div_0_0",
        ),
        pytest.param(
            3,
            0,
            0,
            id="div_neg1_0",
        ),
        pytest.param(
            4,
            0,
            0,
            id="div_neg2_0",
        ),
        pytest.param(
            5,
            0,
            0,
            id="div_maxint_0",
        ),
        pytest.param(
            6,
            0,
            0,
            id="div_minint_0",
        ),
        pytest.param(
            7,
            0,
            0,
            id="sdiv_2_0",
        ),
        pytest.param(
            8,
            0,
            0,
            id="sdiv_1_0",
        ),
        pytest.param(
            9,
            0,
            0,
            id="sdiv_0_0",
        ),
        pytest.param(
            10,
            0,
            0,
            id="sdiv_neg1_0",
        ),
        pytest.param(
            11,
            0,
            0,
            id="sdiv_neg2_0",
        ),
        pytest.param(
            12,
            0,
            0,
            id="sdiv_maxint_0",
        ),
        pytest.param(
            13,
            0,
            0,
            id="sdiv_minint_0",
        ),
        pytest.param(
            14,
            0,
            0,
            id="mod_2_0",
        ),
        pytest.param(
            15,
            0,
            0,
            id="mod_1_0",
        ),
        pytest.param(
            16,
            0,
            0,
            id="mod_0_0",
        ),
        pytest.param(
            17,
            0,
            0,
            id="mod_neg1_0",
        ),
        pytest.param(
            18,
            0,
            0,
            id="mod_neg2_0",
        ),
        pytest.param(
            19,
            0,
            0,
            id="mod_maxint_0",
        ),
        pytest.param(
            20,
            0,
            0,
            id="mod_minint_0",
        ),
        pytest.param(
            21,
            0,
            0,
            id="smod_2_0",
        ),
        pytest.param(
            22,
            0,
            0,
            id="smod_1_0",
        ),
        pytest.param(
            23,
            0,
            0,
            id="smod_0_0",
        ),
        pytest.param(
            24,
            0,
            0,
            id="smod_neg1_0",
        ),
        pytest.param(
            25,
            0,
            0,
            id="smod_neg2_0",
        ),
        pytest.param(
            26,
            0,
            0,
            id="smod_maxint_0",
        ),
        pytest.param(
            27,
            0,
            0,
            id="smod_minint_0",
        ),
        pytest.param(
            28,
            0,
            0,
            id="addmod_0_0_0",
        ),
        pytest.param(
            29,
            0,
            0,
            id="addmod_0_1_0",
        ),
        pytest.param(
            30,
            0,
            0,
            id="addmod_1_0_0",
        ),
        pytest.param(
            31,
            0,
            0,
            id="addmod_1_1_0",
        ),
        pytest.param(
            32,
            0,
            0,
            id="addmod_0_2_0",
        ),
        pytest.param(
            33,
            0,
            0,
            id="addmod_2_0_0",
        ),
        pytest.param(
            34,
            0,
            0,
            id="addmod_2_2_0",
        ),
        pytest.param(
            35,
            0,
            0,
            id="addmod_1_2_0",
        ),
        pytest.param(
            36,
            0,
            0,
            id="addmod_2_1_0",
        ),
        pytest.param(
            37,
            0,
            0,
            id="addmod_0_0_0",
        ),
        pytest.param(
            38,
            0,
            0,
            id="addmod_0_1_0",
        ),
        pytest.param(
            39,
            0,
            0,
            id="addmod_1_0_0",
        ),
        pytest.param(
            40,
            0,
            0,
            id="addmod_1_1_0",
        ),
        pytest.param(
            41,
            0,
            0,
            id="addmod_0_neg1_0",
        ),
        pytest.param(
            42,
            0,
            0,
            id="addmod_neg1_0_0",
        ),
        pytest.param(
            43,
            0,
            0,
            id="addmod_neg1_neg1_0",
        ),
        pytest.param(
            44,
            0,
            0,
            id="addmod_0_neg2_0",
        ),
        pytest.param(
            45,
            0,
            0,
            id="addmod_neg2_0_0",
        ),
        pytest.param(
            46,
            0,
            0,
            id="addmod_neg2_neg2_0",
        ),
        pytest.param(
            47,
            0,
            0,
            id="addmod_0_neg1_0",
        ),
        pytest.param(
            48,
            0,
            0,
            id="addmod_neg1_0_0",
        ),
        pytest.param(
            49,
            0,
            0,
            id="addmod_neg1_neg1_0",
        ),
        pytest.param(
            50,
            0,
            0,
            id="addmod_0_neg2_0",
        ),
        pytest.param(
            51,
            0,
            0,
            id="addmod_neg2_0_0",
        ),
        pytest.param(
            52,
            0,
            0,
            id="addmod_neg2_neg2_0",
        ),
        pytest.param(
            53,
            0,
            0,
            id="addmod_1_neg1_0",
        ),
        pytest.param(
            54,
            0,
            0,
            id="addmod_neg1_1_0",
        ),
        pytest.param(
            55,
            0,
            0,
            id="addmod_1_neg2_0",
        ),
        pytest.param(
            56,
            0,
            0,
            id="addmod_neg2_1_0",
        ),
        pytest.param(
            57,
            0,
            0,
            id="addmod_1_neg1_0",
        ),
        pytest.param(
            58,
            0,
            0,
            id="addmod_neg1_1_0",
        ),
        pytest.param(
            59,
            0,
            0,
            id="addmod_2_neg2_0",
        ),
        pytest.param(
            60,
            0,
            0,
            id="addmod_neg2_2_0",
        ),
        pytest.param(
            61,
            0,
            0,
            id="addmod_neg1_neg2_0",
        ),
        pytest.param(
            62,
            0,
            0,
            id="addmod_neg2_neg1_0",
        ),
        pytest.param(
            63,
            0,
            0,
            id="mulmod_0_0_0",
        ),
        pytest.param(
            64,
            0,
            0,
            id="mulmod_0_1_0",
        ),
        pytest.param(
            65,
            0,
            0,
            id="mulmod_1_0_0",
        ),
        pytest.param(
            66,
            0,
            0,
            id="mulmod_1_1_0",
        ),
        pytest.param(
            67,
            0,
            0,
            id="mulmod_0_2_0",
        ),
        pytest.param(
            68,
            0,
            0,
            id="mulmod_2_0_0",
        ),
        pytest.param(
            69,
            0,
            0,
            id="mulmod_2_2_0",
        ),
        pytest.param(
            70,
            0,
            0,
            id="mulmod_1_2_0",
        ),
        pytest.param(
            71,
            0,
            0,
            id="mulmod_2_1_0",
        ),
        pytest.param(
            72,
            0,
            0,
            id="mulmod_0_0_0",
        ),
        pytest.param(
            73,
            0,
            0,
            id="mulmod_0_1_0",
        ),
        pytest.param(
            74,
            0,
            0,
            id="mulmod_1_0_0",
        ),
        pytest.param(
            75,
            0,
            0,
            id="mulmod_1_1_0",
        ),
        pytest.param(
            76,
            0,
            0,
            id="mulmod_0_neg1_0",
        ),
        pytest.param(
            77,
            0,
            0,
            id="mulmod_neg1_0_0",
        ),
        pytest.param(
            78,
            0,
            0,
            id="mulmod_neg1_neg1_0",
        ),
        pytest.param(
            79,
            0,
            0,
            id="mulmod_0_neg2_0",
        ),
        pytest.param(
            80,
            0,
            0,
            id="mulmod_neg2_0_0",
        ),
        pytest.param(
            81,
            0,
            0,
            id="mulmod_neg2_neg2_0",
        ),
        pytest.param(
            82,
            0,
            0,
            id="mulmod_0_neg1_0",
        ),
        pytest.param(
            83,
            0,
            0,
            id="mulmod_neg1_0_0",
        ),
        pytest.param(
            84,
            0,
            0,
            id="mulmod_neg1_neg1_0",
        ),
        pytest.param(
            85,
            0,
            0,
            id="mulmod_0_neg2_0",
        ),
        pytest.param(
            86,
            0,
            0,
            id="mulmod_neg2_0_0",
        ),
        pytest.param(
            87,
            0,
            0,
            id="mulmod_neg2_neg2_0",
        ),
        pytest.param(
            88,
            0,
            0,
            id="mulmod_1_neg1_0",
        ),
        pytest.param(
            89,
            0,
            0,
            id="mulmod_neg1_1_0",
        ),
        pytest.param(
            90,
            0,
            0,
            id="mulmod_1_neg2_0",
        ),
        pytest.param(
            91,
            0,
            0,
            id="mulmod_neg2_1_0",
        ),
        pytest.param(
            92,
            0,
            0,
            id="mulmod_1_neg1_0",
        ),
        pytest.param(
            93,
            0,
            0,
            id="mulmod_neg1_1_0",
        ),
        pytest.param(
            94,
            0,
            0,
            id="mulmod_2_neg2_0",
        ),
        pytest.param(
            95,
            0,
            0,
            id="mulmod_neg2_2_0",
        ),
        pytest.param(
            96,
            0,
            0,
            id="mulmod_neg1_neg2_0",
        ),
        pytest.param(
            97,
            0,
            0,
            id="mulmod_neg2_neg1_0",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_div_by_zero(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Ori Pomerantz qbzzt1@gmail."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = pre.fund_eoa(amount=0xBA1A9CE0BA1A9CE)

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
    #     (def 'NOP 0)
    #     (def 'opcode $4)
    #     (def 'a      $36)
    #     (def 'b      $68)
    #
    #     (if (= opcode 0x04) [[0]] (div a 0) NOP)
    #     (if (= opcode 0x05) [[0]] (sdiv a 0) NOP)
    #     (if (= opcode 0x06) [[0]] (mod a 0) NOP)
    #     (if (= opcode 0x07) [[0]] (smod a 0) NOP)
    #     (if (= opcode 0x08) [[0]] (addmod a b 0) NOP)
    #     (if (= opcode 0x09) [[0]] (mulmod a b 0) NOP)
    # }
    target = pre.deploy_contract(  # noqa: F841
        code=Op.JUMPI(
            pc=0xF, condition=Op.EQ(Op.CALLDATALOAD(offset=0x4), 0x4)
        )
        + Op.POP(0x0)
        + Op.JUMP(pc=0x19)
        + Op.JUMPDEST
        + Op.SSTORE(key=0x0, value=Op.DIV(Op.CALLDATALOAD(offset=0x24), 0x0))
        + Op.JUMPDEST
        + Op.JUMPI(pc=0x29, condition=Op.EQ(Op.CALLDATALOAD(offset=0x4), 0x5))
        + Op.POP(0x0)
        + Op.JUMP(pc=0x33)
        + Op.JUMPDEST
        + Op.SSTORE(key=0x0, value=Op.SDIV(Op.CALLDATALOAD(offset=0x24), 0x0))
        + Op.JUMPDEST
        + Op.JUMPI(pc=0x43, condition=Op.EQ(Op.CALLDATALOAD(offset=0x4), 0x6))
        + Op.POP(0x0)
        + Op.JUMP(pc=0x4D)
        + Op.JUMPDEST
        + Op.SSTORE(key=0x0, value=Op.MOD(Op.CALLDATALOAD(offset=0x24), 0x0))
        + Op.JUMPDEST
        + Op.JUMPI(pc=0x5D, condition=Op.EQ(Op.CALLDATALOAD(offset=0x4), 0x7))
        + Op.POP(0x0)
        + Op.JUMP(pc=0x67)
        + Op.JUMPDEST
        + Op.SSTORE(key=0x0, value=Op.SMOD(Op.CALLDATALOAD(offset=0x24), 0x0))
        + Op.JUMPDEST
        + Op.JUMPI(pc=0x77, condition=Op.EQ(Op.CALLDATALOAD(offset=0x4), 0x8))
        + Op.POP(0x0)
        + Op.JUMP(pc=0x84)
        + Op.JUMPDEST
        + Op.SSTORE(
            key=0x0,
            value=Op.ADDMOD(
                Op.CALLDATALOAD(offset=0x24), Op.CALLDATALOAD(offset=0x44), 0x0
            ),
        )
        + Op.JUMPDEST
        + Op.JUMPI(pc=0x94, condition=Op.EQ(Op.CALLDATALOAD(offset=0x4), 0x9))
        + Op.POP(0x0)
        + Op.JUMP(pc=0xA1)
        + Op.JUMPDEST
        + Op.SSTORE(
            key=0x0,
            value=Op.MULMOD(
                Op.CALLDATALOAD(offset=0x24), Op.CALLDATALOAD(offset=0x44), 0x0
            ),
        )
        + Op.JUMPDEST
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
    )

    tx_data = [
        Bytes("1a8451e6") + Hash(0x4) + Hash(0x2),
        Bytes("1a8451e6") + Hash(0x4) + Hash(0x1),
        Bytes("1a8451e6") + Hash(0x4) + Hash(0x0),
        Bytes("1a8451e6")
        + Hash(0x4)
        + Hash(
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
        ),
        Bytes("1a8451e6")
        + Hash(0x4)
        + Hash(
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE
        ),
        Bytes("1a8451e6")
        + Hash(0x4)
        + Hash(
            0x7FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
        ),
        Bytes("1a8451e6")
        + Hash(0x4)
        + Hash(
            0x8000000000000000000000000000000000000000000000000000000000000000
        ),
        Bytes("1a8451e6") + Hash(0x5) + Hash(0x2),
        Bytes("1a8451e6") + Hash(0x5) + Hash(0x1),
        Bytes("1a8451e6") + Hash(0x5) + Hash(0x0),
        Bytes("1a8451e6")
        + Hash(0x5)
        + Hash(
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
        ),
        Bytes("1a8451e6")
        + Hash(0x5)
        + Hash(
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE
        ),
        Bytes("1a8451e6")
        + Hash(0x5)
        + Hash(
            0x7FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
        ),
        Bytes("1a8451e6")
        + Hash(0x5)
        + Hash(
            0x8000000000000000000000000000000000000000000000000000000000000000
        ),
        Bytes("1a8451e6") + Hash(0x6) + Hash(0x2),
        Bytes("1a8451e6") + Hash(0x6) + Hash(0x1),
        Bytes("1a8451e6") + Hash(0x6) + Hash(0x0),
        Bytes("1a8451e6")
        + Hash(0x6)
        + Hash(
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
        ),
        Bytes("1a8451e6")
        + Hash(0x6)
        + Hash(
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE
        ),
        Bytes("1a8451e6")
        + Hash(0x6)
        + Hash(
            0x7FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
        ),
        Bytes("1a8451e6")
        + Hash(0x6)
        + Hash(
            0x8000000000000000000000000000000000000000000000000000000000000000
        ),
        Bytes("1a8451e6") + Hash(0x7) + Hash(0x2),
        Bytes("1a8451e6") + Hash(0x7) + Hash(0x1),
        Bytes("1a8451e6") + Hash(0x7) + Hash(0x0),
        Bytes("1a8451e6")
        + Hash(0x7)
        + Hash(
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
        ),
        Bytes("1a8451e6")
        + Hash(0x7)
        + Hash(
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE
        ),
        Bytes("1a8451e6")
        + Hash(0x7)
        + Hash(
            0x7FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
        ),
        Bytes("1a8451e6")
        + Hash(0x7)
        + Hash(
            0x8000000000000000000000000000000000000000000000000000000000000000
        ),
        Bytes("048071d3") + Hash(0x8) + Hash(0x0) + Hash(0x0),
        Bytes("048071d3") + Hash(0x8) + Hash(0x0) + Hash(0x1),
        Bytes("048071d3") + Hash(0x8) + Hash(0x1) + Hash(0x0),
        Bytes("048071d3") + Hash(0x8) + Hash(0x1) + Hash(0x1),
        Bytes("048071d3") + Hash(0x8) + Hash(0x0) + Hash(0x2),
        Bytes("048071d3") + Hash(0x8) + Hash(0x2) + Hash(0x0),
        Bytes("048071d3") + Hash(0x8) + Hash(0x2) + Hash(0x2),
        Bytes("048071d3") + Hash(0x8) + Hash(0x1) + Hash(0x2),
        Bytes("048071d3") + Hash(0x8) + Hash(0x2) + Hash(0x1),
        Bytes("048071d3") + Hash(0x8) + Hash(0x0) + Hash(0x0),
        Bytes("048071d3") + Hash(0x8) + Hash(0x0) + Hash(0x1),
        Bytes("048071d3") + Hash(0x8) + Hash(0x1) + Hash(0x0),
        Bytes("048071d3") + Hash(0x8) + Hash(0x1) + Hash(0x1),
        Bytes("048071d3")
        + Hash(0x8)
        + Hash(0x0)
        + Hash(
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
        ),
        Bytes("048071d3")
        + Hash(0x8)
        + Hash(
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
        )
        + Hash(0x0),
        Bytes("048071d3")
        + Hash(0x8)
        + Hash(
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
        )
        + Hash(
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
        ),
        Bytes("048071d3")
        + Hash(0x8)
        + Hash(0x0)
        + Hash(
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE
        ),
        Bytes("048071d3")
        + Hash(0x8)
        + Hash(
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE
        )
        + Hash(0x0),
        Bytes("048071d3")
        + Hash(0x8)
        + Hash(
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE
        )
        + Hash(
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE
        ),
        Bytes("048071d3")
        + Hash(0x8)
        + Hash(0x0)
        + Hash(
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
        ),
        Bytes("048071d3")
        + Hash(0x8)
        + Hash(
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
        )
        + Hash(0x0),
        Bytes("048071d3")
        + Hash(0x8)
        + Hash(
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
        )
        + Hash(
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
        ),
        Bytes("048071d3")
        + Hash(0x8)
        + Hash(0x0)
        + Hash(
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE
        ),
        Bytes("048071d3")
        + Hash(0x8)
        + Hash(
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE
        )
        + Hash(0x0),
        Bytes("048071d3")
        + Hash(0x8)
        + Hash(
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE
        )
        + Hash(
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE
        ),
        Bytes("048071d3")
        + Hash(0x8)
        + Hash(0x1)
        + Hash(
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
        ),
        Bytes("048071d3")
        + Hash(0x8)
        + Hash(
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
        )
        + Hash(0x1),
        Bytes("048071d3")
        + Hash(0x8)
        + Hash(0x1)
        + Hash(
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE
        ),
        Bytes("048071d3")
        + Hash(0x8)
        + Hash(
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE
        )
        + Hash(0x1),
        Bytes("048071d3")
        + Hash(0x8)
        + Hash(0x1)
        + Hash(
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
        ),
        Bytes("048071d3")
        + Hash(0x8)
        + Hash(
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
        )
        + Hash(0x1),
        Bytes("048071d3")
        + Hash(0x8)
        + Hash(0x2)
        + Hash(
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE
        ),
        Bytes("048071d3")
        + Hash(0x8)
        + Hash(
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE
        )
        + Hash(0x2),
        Bytes("048071d3")
        + Hash(0x8)
        + Hash(
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
        )
        + Hash(
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE
        ),
        Bytes("048071d3")
        + Hash(0x8)
        + Hash(
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE
        )
        + Hash(
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
        ),
        Bytes("048071d3") + Hash(0x9) + Hash(0x0) + Hash(0x0),
        Bytes("048071d3") + Hash(0x9) + Hash(0x0) + Hash(0x1),
        Bytes("048071d3") + Hash(0x9) + Hash(0x1) + Hash(0x0),
        Bytes("048071d3") + Hash(0x9) + Hash(0x1) + Hash(0x1),
        Bytes("048071d3") + Hash(0x9) + Hash(0x0) + Hash(0x2),
        Bytes("048071d3") + Hash(0x9) + Hash(0x2) + Hash(0x0),
        Bytes("048071d3") + Hash(0x9) + Hash(0x2) + Hash(0x2),
        Bytes("048071d3") + Hash(0x9) + Hash(0x1) + Hash(0x2),
        Bytes("048071d3") + Hash(0x9) + Hash(0x2) + Hash(0x1),
        Bytes("048071d3") + Hash(0x9) + Hash(0x0) + Hash(0x0),
        Bytes("048071d3") + Hash(0x9) + Hash(0x0) + Hash(0x1),
        Bytes("048071d3") + Hash(0x9) + Hash(0x1) + Hash(0x0),
        Bytes("048071d3") + Hash(0x9) + Hash(0x1) + Hash(0x1),
        Bytes("048071d3")
        + Hash(0x9)
        + Hash(0x0)
        + Hash(
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
        ),
        Bytes("048071d3")
        + Hash(0x9)
        + Hash(
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
        )
        + Hash(0x0),
        Bytes("048071d3")
        + Hash(0x9)
        + Hash(
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
        )
        + Hash(
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
        ),
        Bytes("048071d3")
        + Hash(0x9)
        + Hash(0x0)
        + Hash(
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE
        ),
        Bytes("048071d3")
        + Hash(0x9)
        + Hash(
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE
        )
        + Hash(0x0),
        Bytes("048071d3")
        + Hash(0x9)
        + Hash(
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE
        )
        + Hash(
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE
        ),
        Bytes("048071d3")
        + Hash(0x9)
        + Hash(0x0)
        + Hash(
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
        ),
        Bytes("048071d3")
        + Hash(0x9)
        + Hash(
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
        )
        + Hash(0x0),
        Bytes("048071d3")
        + Hash(0x9)
        + Hash(
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
        )
        + Hash(
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
        ),
        Bytes("048071d3")
        + Hash(0x9)
        + Hash(0x0)
        + Hash(
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE
        ),
        Bytes("048071d3")
        + Hash(0x9)
        + Hash(
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE
        )
        + Hash(0x0),
        Bytes("048071d3")
        + Hash(0x9)
        + Hash(
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE
        )
        + Hash(
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE
        ),
        Bytes("048071d3")
        + Hash(0x9)
        + Hash(0x1)
        + Hash(
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
        ),
        Bytes("048071d3")
        + Hash(0x9)
        + Hash(
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
        )
        + Hash(0x1),
        Bytes("048071d3")
        + Hash(0x9)
        + Hash(0x1)
        + Hash(
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE
        ),
        Bytes("048071d3")
        + Hash(0x9)
        + Hash(
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE
        )
        + Hash(0x1),
        Bytes("048071d3")
        + Hash(0x9)
        + Hash(0x1)
        + Hash(
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
        ),
        Bytes("048071d3")
        + Hash(0x9)
        + Hash(
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
        )
        + Hash(0x1),
        Bytes("048071d3")
        + Hash(0x9)
        + Hash(0x2)
        + Hash(
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE
        ),
        Bytes("048071d3")
        + Hash(0x9)
        + Hash(
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE
        )
        + Hash(0x2),
        Bytes("048071d3")
        + Hash(0x9)
        + Hash(
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
        )
        + Hash(
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE
        ),
        Bytes("048071d3")
        + Hash(0x9)
        + Hash(
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE
        )
        + Hash(
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
        ),
    ]
    tx_gas = [16777216]
    tx_value = [1]

    tx = Transaction(
        sender=sender,
        to=target,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        value=tx_value[v],
    )

    post = {target: Account(storage={0: 0})}

    state_test(env=env, pre=pre, post=post, tx=tx)
