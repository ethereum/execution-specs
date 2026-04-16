"""
Ori Pomerantz qbzzt1@gmail.com.

Ported from:
state_tests/stBadOpcode/invalidAddrFiller.yml
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
    ["state_tests/stBadOpcode/invalidAddrFiller.yml"],
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
            id="ok",
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
            id="ok",
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
            id="ok",
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
            id="ok",
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
            id="ok",
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
            id="ok",
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
            id="ok",
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
            id="ok",
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
            id="ok",
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
            id="ok",
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
            id="ok",
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
            id="ok",
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
            id="ok",
        ),
        pytest.param(
            74,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            75,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            76,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            77,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            78,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            79,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            80,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            81,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            82,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            83,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            84,
            0,
            0,
            id="ok",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_invalid_addr(
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
    #       [0] 0xDEADBEEF
    #       (return 0 0x120)
    # }
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x0, value=0xDEADBEEF)
        + Op.RETURN(offset=0x0, size=0x120)
        + Op.STOP,
        balance=0x10000,
        nonce=0,
        address=Address(0x1C60A961CFF23C82B2F809E76B815D003898E196),  # noqa: E501
    )
    # Source: lll
    # {
    #    (selfdestruct $0)
    # }
    dead1 = pre.deploy_contract(  # noqa: F841
        code=Op.SELFDESTRUCT(address=Op.CALLDATALOAD(offset=0x0)) + Op.STOP,
        balance=4096,
        nonce=0,
        address=Address(0x9CB657C71386D578195B90DA7DE545482E0A9440),  # noqa: E501
    )
    # Source: lll
    # {
    #    (selfdestruct $0)
    # }
    dead2 = pre.deploy_contract(  # noqa: F841
        code=Op.SELFDESTRUCT(address=Op.CALLDATALOAD(offset=0x0)) + Op.STOP,
        balance=4096,
        nonce=0,
        address=Address(0xE2CFFD6602680D87B7872C3B69F42FA631058CBF),  # noqa: E501
    )
    # Source: lll
    # {
    #    ; Inputs
    #    (def 'opcode $4)
    #    (def 'addrBase $36)
    #    (def 'addrType $68)
    #
    #    ; Constants
    #    (def 'NOP 0)
    #    (def 'two160 (shl 1 160))
    #    (def 'two254 (shl 1 254))
    #    (def 'two255 (shl 1 255))
    #    (def 'word 0x20) ; 32 bytes per word
    #
    #    ; Variables
    #    (def 'addr1       0x2000)
    #    (def 'res1        0x2020)
    #    (def 'addr2       0x2040)
    #    (def 'res2        0x2060)
    #    (def 'resExpected 0x2080)
    #    (def 'temp        0x20A0)
    #
    #    ; addrBase 1 is a normal valid address (<contract:0x000000000000000000000000000000000000c0de>)  # noqa: E501
    #    ; addrBase 2 is a precompiled address  (0x00000002)
    #    (if (= addrBase 1) [addr1] <contract:0x000000000000000000000000000000000000c0de> NOP)  # noqa: E501
    #    (if (= addrBase 2) [addr1] 0x0002 NOP)
    #
    #    ; addrType  0 is to just use the base (twice, verify result is consistent)  # noqa: E501
    #    ; addrType  1 is addr1 + 2^160
    #    ; addrType  2 is addr1 + 2^254
    #    ; addrType  3 is addr1 + 2^255
    # ... (108 more lines)
    target = pre.deploy_contract(  # noqa: F841
        code=Op.JUMPI(
            pc=Op.PUSH2[0x11],
            condition=Op.EQ(Op.CALLDATALOAD(offset=0x24), 0x1),
        )
        + Op.POP(0x0)
        + Op.JUMP(pc=Op.PUSH2[0x2B])
        + Op.JUMPDEST
        + Op.MSTORE(
            offset=0x2000, value=0x1C60A961CFF23C82B2F809E76B815D003898E196
        )
        + Op.JUMPDEST
        + Op.JUMPI(
            pc=Op.PUSH2[0x3D],
            condition=Op.EQ(Op.CALLDATALOAD(offset=0x24), 0x2),
        )
        + Op.POP(0x0)
        + Op.JUMP(pc=Op.PUSH2[0x44])
        + Op.JUMPDEST
        + Op.MSTORE(offset=0x2000, value=0x2)
        + Op.JUMPDEST
        + Op.JUMPI(
            pc=Op.PUSH2[0x56],
            condition=Op.EQ(Op.CALLDATALOAD(offset=0x44), 0x0),
        )
        + Op.POP(0x0)
        + Op.JUMP(pc=Op.PUSH2[0x5F])
        + Op.JUMPDEST
        + Op.MSTORE(offset=0x2040, value=Op.MLOAD(offset=0x2000))
        + Op.JUMPDEST
        + Op.JUMPI(
            pc=Op.PUSH2[0x71],
            condition=Op.EQ(Op.CALLDATALOAD(offset=0x44), 0x1),
        )
        + Op.POP(0x0)
        + Op.JUMP(pc=Op.PUSH2[0x83])
        + Op.JUMPDEST
        + Op.MSTORE(
            offset=0x2040,
            value=Op.ADD(
                Op.MLOAD(offset=0x2000), Op.MUL(0x1, Op.EXP(0x2, 0xA0))
            ),
        )
        + Op.JUMPDEST
        + Op.JUMPI(
            pc=Op.PUSH2[0x95],
            condition=Op.EQ(Op.CALLDATALOAD(offset=0x44), 0x2),
        )
        + Op.POP(0x0)
        + Op.JUMP(pc=Op.PUSH2[0xA7])
        + Op.JUMPDEST
        + Op.MSTORE(
            offset=0x2040,
            value=Op.ADD(
                Op.MLOAD(offset=0x2000), Op.MUL(0x1, Op.EXP(0x2, 0xFE))
            ),
        )
        + Op.JUMPDEST
        + Op.JUMPI(
            pc=Op.PUSH2[0xB9],
            condition=Op.EQ(Op.CALLDATALOAD(offset=0x44), 0x3),
        )
        + Op.POP(0x0)
        + Op.JUMP(pc=Op.PUSH2[0xCB])
        + Op.JUMPDEST
        + Op.MSTORE(
            offset=0x2040,
            value=Op.ADD(
                Op.MLOAD(offset=0x2000), Op.MUL(0x1, Op.EXP(0x2, 0xFF))
            ),
        )
        + Op.JUMPDEST
        + Op.JUMPI(
            pc=Op.PUSH2[0xDD],
            condition=Op.EQ(Op.CALLDATALOAD(offset=0x44), 0x4),
        )
        + Op.POP(0x0)
        + Op.JUMP(pc=Op.PUSH2[0xEF])
        + Op.JUMPDEST
        + Op.MSTORE(
            offset=0x2040,
            value=Op.SUB(
                Op.MLOAD(offset=0x2000), Op.MUL(0x1, Op.EXP(0x2, 0xA0))
            ),
        )
        + Op.JUMPDEST
        + Op.MSTORE(offset=0x2020, value=0xFF00FF00FF00FF00)
        + Op.MSTORE(offset=0x2060, value=0xFF00FF00FF00FF)
        + Op.JUMPI(
            pc=0x11A, condition=Op.EQ(Op.CALLDATALOAD(offset=0x4), 0x31)
        )
        + Op.POP(0x0)
        + Op.JUMP(pc=0x14B)
        + Op.JUMPDEST
        + Op.MSTORE(
            offset=0x2020, value=Op.BALANCE(address=Op.MLOAD(offset=0x2000))
        )
        + Op.MSTORE(
            offset=0x2060, value=Op.BALANCE(address=Op.MLOAD(offset=0x2040))
        )
        + Op.JUMPI(
            pc=0x141, condition=Op.EQ(Op.CALLDATALOAD(offset=0x24), 0x1)
        )
        + Op.MSTORE(offset=0x2080, value=0x0)
        + Op.JUMP(pc=0x14A)
        + Op.JUMPDEST
        + Op.MSTORE(offset=0x2080, value=0x10000)
        + Op.JUMPDEST * 2
        + Op.JUMPI(
            pc=0x15D, condition=Op.EQ(Op.CALLDATALOAD(offset=0x4), 0x3B)
        )
        + Op.POP(0x0)
        + Op.JUMP(pc=0x18C)
        + Op.JUMPDEST
        + Op.MSTORE(
            offset=0x2020,
            value=Op.EXTCODESIZE(address=Op.MLOAD(offset=0x2000)),
        )
        + Op.MSTORE(
            offset=0x2060,
            value=Op.EXTCODESIZE(address=Op.MLOAD(offset=0x2040)),
        )
        + Op.JUMPI(
            pc=0x184, condition=Op.EQ(Op.CALLDATALOAD(offset=0x24), 0x1)
        )
        + Op.MSTORE(offset=0x2080, value=0x0)
        + Op.JUMP(pc=0x18B)
        + Op.JUMPDEST
        + Op.MSTORE(offset=0x2080, value=0xF)
        + Op.JUMPDEST * 2
        + Op.JUMPI(
            pc=0x19E, condition=Op.EQ(Op.CALLDATALOAD(offset=0x4), 0x3C)
        )
        + Op.POP(0x0)
        + Op.JUMP(pc=0x1F2)
        + Op.JUMPDEST
        + Op.EXTCODECOPY(
            address=Op.MLOAD(offset=0x2000),
            dest_offset=0x2020,
            offset=0x0,
            size=0x20,
        )
        + Op.EXTCODECOPY(
            address=Op.MLOAD(offset=0x2040),
            dest_offset=0x2060,
            offset=0x0,
            size=0x20,
        )
        + Op.JUMPI(
            pc=0x1CB, condition=Op.EQ(Op.CALLDATALOAD(offset=0x24), 0x1)
        )
        + Op.MSTORE(offset=0x2080, value=0x0)
        + Op.JUMP(pc=0x1F1)
        + Op.JUMPDEST
        + Op.MSTORE(
            offset=0x2080,
            value=0x63DEADBEEF6000526101206000F3000000000000000000000000000000000000,  # noqa: E501
        )
        + Op.JUMPDEST * 2
        + Op.JUMPI(
            pc=0x204, condition=Op.EQ(Op.CALLDATALOAD(offset=0x4), 0x3F)
        )
        + Op.POP(0x0)
        + Op.JUMP(pc=0x252)
        + Op.JUMPDEST
        + Op.MSTORE(
            offset=0x2020,
            value=Op.EXTCODEHASH(address=Op.MLOAD(offset=0x2000)),
        )
        + Op.MSTORE(
            offset=0x2060,
            value=Op.EXTCODEHASH(address=Op.MLOAD(offset=0x2040)),
        )
        + Op.JUMPI(
            pc=0x22B, condition=Op.EQ(Op.CALLDATALOAD(offset=0x24), 0x1)
        )
        + Op.MSTORE(offset=0x2080, value=0x0)
        + Op.JUMP(pc=0x251)
        + Op.JUMPDEST
        + Op.MSTORE(
            offset=0x2080,
            value=0x85AB232A015279867A1F5B5DA4F9688C6C92E555C122E9147F9D13BC53C03E92,  # noqa: E501
        )
        + Op.JUMPDEST * 2
        + Op.JUMPI(
            pc=0x264, condition=Op.EQ(Op.CALLDATALOAD(offset=0x4), 0xF1)
        )
        + Op.POP(0x0)
        + Op.JUMP(pc=0x2CD)
        + Op.JUMPDEST
        + Op.POP(
            Op.CALL(
                gas=0x1000,
                address=Op.MLOAD(offset=0x2000),
                value=0x0,
                args_offset=0x2000,
                args_size=0x20,
                ret_offset=0x2020,
                ret_size=0x20,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x1000,
                address=Op.MLOAD(offset=0x2040),
                value=0x0,
                args_offset=0x2000,
                args_size=0x20,
                ret_offset=0x2060,
                ret_size=0x20,
            )
        )
        + Op.JUMPI(
            pc=0x2C2, condition=Op.EQ(Op.CALLDATALOAD(offset=0x24), 0x1)
        )
        + Op.MSTORE(
            offset=0x2080,
            value=0x9267D3DBED802941483F1AFA2A6BC68DE5F653128ACA9BF1461C5D0A3AD36ED2,  # noqa: E501
        )
        + Op.JUMP(pc=0x2CC)
        + Op.JUMPDEST
        + Op.MSTORE(offset=0x2080, value=0xDEADBEEF)
        + Op.JUMPDEST * 2
        + Op.JUMPI(
            pc=0x2DF, condition=Op.EQ(Op.CALLDATALOAD(offset=0x4), 0xF2)
        )
        + Op.POP(0x0)
        + Op.JUMP(pc=0x348)
        + Op.JUMPDEST
        + Op.POP(
            Op.CALLCODE(
                gas=0x1000,
                address=Op.MLOAD(offset=0x2000),
                value=0x0,
                args_offset=0x2000,
                args_size=0x20,
                ret_offset=0x2020,
                ret_size=0x20,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x1000,
                address=Op.MLOAD(offset=0x2040),
                value=0x0,
                args_offset=0x2000,
                args_size=0x20,
                ret_offset=0x2060,
                ret_size=0x20,
            )
        )
        + Op.JUMPI(
            pc=0x33D, condition=Op.EQ(Op.CALLDATALOAD(offset=0x24), 0x1)
        )
        + Op.MSTORE(
            offset=0x2080,
            value=0x9267D3DBED802941483F1AFA2A6BC68DE5F653128ACA9BF1461C5D0A3AD36ED2,  # noqa: E501
        )
        + Op.JUMP(pc=0x347)
        + Op.JUMPDEST
        + Op.MSTORE(offset=0x2080, value=0xDEADBEEF)
        + Op.JUMPDEST * 2
        + Op.JUMPI(
            pc=0x35A, condition=Op.EQ(Op.CALLDATALOAD(offset=0x4), 0xF4)
        )
        + Op.POP(0x0)
        + Op.JUMP(pc=0x3BF)
        + Op.JUMPDEST
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x1000,
                address=Op.MLOAD(offset=0x2000),
                args_offset=0x2000,
                args_size=0x20,
                ret_offset=0x2020,
                ret_size=0x20,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x1000,
                address=Op.MLOAD(offset=0x2040),
                args_offset=0x2000,
                args_size=0x20,
                ret_offset=0x2060,
                ret_size=0x20,
            )
        )
        + Op.JUMPI(
            pc=0x3B4, condition=Op.EQ(Op.CALLDATALOAD(offset=0x24), 0x1)
        )
        + Op.MSTORE(
            offset=0x2080,
            value=0x9267D3DBED802941483F1AFA2A6BC68DE5F653128ACA9BF1461C5D0A3AD36ED2,  # noqa: E501
        )
        + Op.JUMP(pc=0x3BE)
        + Op.JUMPDEST
        + Op.MSTORE(offset=0x2080, value=0xDEADBEEF)
        + Op.JUMPDEST * 2
        + Op.JUMPI(
            pc=0x3D1, condition=Op.EQ(Op.CALLDATALOAD(offset=0x4), 0xFA)
        )
        + Op.POP(0x0)
        + Op.JUMP(pc=0x436)
        + Op.JUMPDEST
        + Op.POP(
            Op.STATICCALL(
                gas=0x1000,
                address=Op.MLOAD(offset=0x2000),
                args_offset=0x2000,
                args_size=0x20,
                ret_offset=0x2020,
                ret_size=0x20,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x1000,
                address=Op.MLOAD(offset=0x2040),
                args_offset=0x2000,
                args_size=0x20,
                ret_offset=0x2060,
                ret_size=0x20,
            )
        )
        + Op.JUMPI(
            pc=0x42B, condition=Op.EQ(Op.CALLDATALOAD(offset=0x24), 0x1)
        )
        + Op.MSTORE(
            offset=0x2080,
            value=0x9267D3DBED802941483F1AFA2A6BC68DE5F653128ACA9BF1461C5D0A3AD36ED2,  # noqa: E501
        )
        + Op.JUMP(pc=0x435)
        + Op.JUMPDEST
        + Op.MSTORE(offset=0x2080, value=0xDEADBEEF)
        + Op.JUMPDEST * 2
        + Op.JUMPI(
            pc=0x448, condition=Op.EQ(Op.CALLDATALOAD(offset=0x4), 0xFF)
        )
        + Op.POP(0x0)
        + Op.JUMP(pc=0x4EA)
        + Op.JUMPDEST
        + Op.MSTORE(
            offset=0x20A0, value=Op.BALANCE(address=Op.MLOAD(offset=0x2000))
        )
        + Op.POP(
            Op.CALL(
                gas=0x10000000,
                address=0x9CB657C71386D578195B90DA7DE545482E0A9440,
                value=0x0,
                args_offset=0x2000,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.MSTORE(
            offset=0x2020, value=Op.BALANCE(address=Op.MLOAD(offset=0x2000))
        )
        + Op.POP(
            Op.CALL(
                gas=0x10000000,
                address=0xE2CFFD6602680D87B7872C3B69F42FA631058CBF,
                value=0x0,
                args_offset=0x2040,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.MSTORE(
            offset=0x2060, value=Op.BALANCE(address=Op.MLOAD(offset=0x2000))
        )
        + Op.MSTORE(
            offset=0x2060,
            value=Op.SUB(Op.MLOAD(offset=0x2060), Op.MLOAD(offset=0x2020)),
        )
        + Op.MSTORE(
            offset=0x2020,
            value=Op.SUB(Op.MLOAD(offset=0x2020), Op.MLOAD(offset=0x20A0)),
        )
        + Op.JUMPI(
            pc=0x4E1, condition=Op.EQ(Op.CALLDATALOAD(offset=0x24), 0x1)
        )
        + Op.MSTORE(offset=0x2080, value=0x1000)
        + Op.JUMP(pc=0x4E9)
        + Op.JUMPDEST
        + Op.MSTORE(offset=0x2080, value=0x1000)
        + Op.JUMPDEST * 2
        + Op.SSTORE(
            key=0x0,
            value=Op.SUB(Op.MLOAD(offset=0x2020), Op.MLOAD(offset=0x2060)),
        )
        + Op.SSTORE(
            key=0x1,
            value=Op.SUB(Op.MLOAD(offset=0x2020), Op.MLOAD(offset=0x2080)),
        )
        + Op.SSTORE(key=0x100, value=0x0)
        + Op.STOP,
        storage={256: 24743},
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x2D876FD03A90703F170C256363BA225F9494E604),  # noqa: E501
    )

    tx_data = [
        Bytes("048071d3") + Hash(0x31) + Hash(0x1) + Hash(0x0),
        Bytes("048071d3") + Hash(0x31) + Hash(0x2) + Hash(0x0),
        Bytes("048071d3") + Hash(0x31) + Hash(0x1) + Hash(0x1),
        Bytes("048071d3") + Hash(0x31) + Hash(0x2) + Hash(0x1),
        Bytes("048071d3") + Hash(0x31) + Hash(0x1) + Hash(0x2),
        Bytes("048071d3") + Hash(0x31) + Hash(0x2) + Hash(0x2),
        Bytes("048071d3") + Hash(0x31) + Hash(0x1) + Hash(0x3),
        Bytes("048071d3") + Hash(0x31) + Hash(0x2) + Hash(0x3),
        Bytes("048071d3") + Hash(0x31) + Hash(0x1) + Hash(0x4),
        Bytes("048071d3") + Hash(0x31) + Hash(0x2) + Hash(0x4),
        Bytes("048071d3") + Hash(0x3B) + Hash(0x1) + Hash(0x0),
        Bytes("048071d3") + Hash(0x3B) + Hash(0x2) + Hash(0x0),
        Bytes("048071d3") + Hash(0x3B) + Hash(0x1) + Hash(0x1),
        Bytes("048071d3") + Hash(0x3B) + Hash(0x2) + Hash(0x1),
        Bytes("048071d3") + Hash(0x3B) + Hash(0x1) + Hash(0x2),
        Bytes("048071d3") + Hash(0x3B) + Hash(0x2) + Hash(0x2),
        Bytes("048071d3") + Hash(0x3B) + Hash(0x1) + Hash(0x3),
        Bytes("048071d3") + Hash(0x3B) + Hash(0x2) + Hash(0x3),
        Bytes("048071d3") + Hash(0x3B) + Hash(0x1) + Hash(0x4),
        Bytes("048071d3") + Hash(0x3B) + Hash(0x2) + Hash(0x4),
        Bytes("048071d3") + Hash(0x3C) + Hash(0x1) + Hash(0x0),
        Bytes("048071d3") + Hash(0x3C) + Hash(0x2) + Hash(0x0),
        Bytes("048071d3") + Hash(0x3C) + Hash(0x1) + Hash(0x1),
        Bytes("048071d3") + Hash(0x3C) + Hash(0x2) + Hash(0x1),
        Bytes("048071d3") + Hash(0x3C) + Hash(0x1) + Hash(0x2),
        Bytes("048071d3") + Hash(0x3C) + Hash(0x2) + Hash(0x2),
        Bytes("048071d3") + Hash(0x3C) + Hash(0x1) + Hash(0x3),
        Bytes("048071d3") + Hash(0x3C) + Hash(0x2) + Hash(0x3),
        Bytes("048071d3") + Hash(0x3C) + Hash(0x1) + Hash(0x4),
        Bytes("048071d3") + Hash(0x3C) + Hash(0x2) + Hash(0x4),
        Bytes("048071d3") + Hash(0x3F) + Hash(0x1) + Hash(0x0),
        Bytes("048071d3") + Hash(0x3F) + Hash(0x2) + Hash(0x0),
        Bytes("048071d3") + Hash(0x3F) + Hash(0x1) + Hash(0x1),
        Bytes("048071d3") + Hash(0x3F) + Hash(0x2) + Hash(0x1),
        Bytes("048071d3") + Hash(0x3F) + Hash(0x1) + Hash(0x2),
        Bytes("048071d3") + Hash(0x3F) + Hash(0x2) + Hash(0x2),
        Bytes("048071d3") + Hash(0x3F) + Hash(0x1) + Hash(0x3),
        Bytes("048071d3") + Hash(0x3F) + Hash(0x2) + Hash(0x3),
        Bytes("048071d3") + Hash(0x3F) + Hash(0x1) + Hash(0x4),
        Bytes("048071d3") + Hash(0x3F) + Hash(0x2) + Hash(0x4),
        Bytes("048071d3") + Hash(0xF1) + Hash(0x1) + Hash(0x0),
        Bytes("048071d3") + Hash(0xF1) + Hash(0x2) + Hash(0x0),
        Bytes("048071d3") + Hash(0xF1) + Hash(0x1) + Hash(0x1),
        Bytes("048071d3") + Hash(0xF1) + Hash(0x2) + Hash(0x1),
        Bytes("048071d3") + Hash(0xF1) + Hash(0x1) + Hash(0x2),
        Bytes("048071d3") + Hash(0xF1) + Hash(0x2) + Hash(0x2),
        Bytes("048071d3") + Hash(0xF1) + Hash(0x1) + Hash(0x3),
        Bytes("048071d3") + Hash(0xF1) + Hash(0x2) + Hash(0x3),
        Bytes("048071d3") + Hash(0xF1) + Hash(0x1) + Hash(0x4),
        Bytes("048071d3") + Hash(0xF1) + Hash(0x2) + Hash(0x4),
        Bytes("048071d3") + Hash(0xF2) + Hash(0x1) + Hash(0x0),
        Bytes("048071d3") + Hash(0xF2) + Hash(0x2) + Hash(0x0),
        Bytes("048071d3") + Hash(0xF2) + Hash(0x1) + Hash(0x1),
        Bytes("048071d3") + Hash(0xF2) + Hash(0x2) + Hash(0x1),
        Bytes("048071d3") + Hash(0xF2) + Hash(0x1) + Hash(0x2),
        Bytes("048071d3") + Hash(0xF2) + Hash(0x2) + Hash(0x2),
        Bytes("048071d3") + Hash(0xF2) + Hash(0x1) + Hash(0x3),
        Bytes("048071d3") + Hash(0xF2) + Hash(0x2) + Hash(0x3),
        Bytes("048071d3") + Hash(0xF2) + Hash(0x1) + Hash(0x4),
        Bytes("048071d3") + Hash(0xF2) + Hash(0x2) + Hash(0x4),
        Bytes("048071d3") + Hash(0xF4) + Hash(0x1) + Hash(0x0),
        Bytes("048071d3") + Hash(0xF4) + Hash(0x2) + Hash(0x0),
        Bytes("048071d3") + Hash(0xF4) + Hash(0x1) + Hash(0x1),
        Bytes("048071d3") + Hash(0xF4) + Hash(0x2) + Hash(0x1),
        Bytes("048071d3") + Hash(0xF4) + Hash(0x1) + Hash(0x2),
        Bytes("048071d3") + Hash(0xF4) + Hash(0x2) + Hash(0x2),
        Bytes("048071d3") + Hash(0xF4) + Hash(0x1) + Hash(0x3),
        Bytes("048071d3") + Hash(0xF4) + Hash(0x2) + Hash(0x3),
        Bytes("048071d3") + Hash(0xF4) + Hash(0x1) + Hash(0x4),
        Bytes("048071d3") + Hash(0xF4) + Hash(0x2) + Hash(0x4),
        Bytes("048071d3") + Hash(0xFA) + Hash(0x1) + Hash(0x0),
        Bytes("048071d3") + Hash(0xFA) + Hash(0x2) + Hash(0x0),
        Bytes("048071d3") + Hash(0xFA) + Hash(0x1) + Hash(0x1),
        Bytes("048071d3") + Hash(0xFA) + Hash(0x2) + Hash(0x1),
        Bytes("048071d3") + Hash(0xFA) + Hash(0x1) + Hash(0x2),
        Bytes("048071d3") + Hash(0xFA) + Hash(0x2) + Hash(0x2),
        Bytes("048071d3") + Hash(0xFA) + Hash(0x1) + Hash(0x3),
        Bytes("048071d3") + Hash(0xFA) + Hash(0x2) + Hash(0x3),
        Bytes("048071d3") + Hash(0xFA) + Hash(0x1) + Hash(0x4),
        Bytes("048071d3") + Hash(0xFA) + Hash(0x2) + Hash(0x4),
        Bytes("048071d3") + Hash(0xFF) + Hash(0x1) + Hash(0x0),
        Bytes("048071d3") + Hash(0xFF) + Hash(0x1) + Hash(0x1),
        Bytes("048071d3") + Hash(0xFF) + Hash(0x1) + Hash(0x2),
        Bytes("048071d3") + Hash(0xFF) + Hash(0x1) + Hash(0x3),
        Bytes("048071d3") + Hash(0xFF) + Hash(0x1) + Hash(0x4),
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

    post = {
        target: Account(
            storage={0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 256: 0},
        ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
