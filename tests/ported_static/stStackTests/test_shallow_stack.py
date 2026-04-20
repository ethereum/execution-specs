"""
Test_shallow_stack.

Ported from:
state_tests/stStackTests/shallowStackFiller.json
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
    compute_create_address,
)
from execution_testing.forks import Fork
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stStackTests/shallowStackFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0,
            0,
            0,
            id="d0",
        ),
        pytest.param(
            1,
            0,
            0,
            id="d1",
        ),
        pytest.param(
            2,
            0,
            0,
            id="d2",
        ),
        pytest.param(
            3,
            0,
            0,
            id="d3",
        ),
        pytest.param(
            4,
            0,
            0,
            id="d4",
        ),
        pytest.param(
            5,
            0,
            0,
            id="d5",
        ),
        pytest.param(
            6,
            0,
            0,
            id="d6",
        ),
        pytest.param(
            7,
            0,
            0,
            id="d7",
        ),
        pytest.param(
            8,
            0,
            0,
            id="d8",
        ),
        pytest.param(
            9,
            0,
            0,
            id="d9",
        ),
        pytest.param(
            10,
            0,
            0,
            id="d10",
        ),
        pytest.param(
            11,
            0,
            0,
            id="d11",
        ),
        pytest.param(
            12,
            0,
            0,
            id="d12",
        ),
        pytest.param(
            13,
            0,
            0,
            id="d13",
        ),
        pytest.param(
            14,
            0,
            0,
            id="d14",
        ),
        pytest.param(
            15,
            0,
            0,
            id="d15",
        ),
        pytest.param(
            16,
            0,
            0,
            id="d16",
        ),
        pytest.param(
            17,
            0,
            0,
            id="d17",
        ),
        pytest.param(
            18,
            0,
            0,
            id="d18",
        ),
        pytest.param(
            19,
            0,
            0,
            id="d19",
        ),
        pytest.param(
            20,
            0,
            0,
            id="d20",
        ),
        pytest.param(
            21,
            0,
            0,
            id="d21",
        ),
        pytest.param(
            22,
            0,
            0,
            id="d22",
        ),
        pytest.param(
            23,
            0,
            0,
            id="d23",
        ),
        pytest.param(
            24,
            0,
            0,
            id="d24",
        ),
        pytest.param(
            25,
            0,
            0,
            id="d25",
        ),
        pytest.param(
            26,
            0,
            0,
            id="d26",
        ),
        pytest.param(
            27,
            0,
            0,
            id="d27",
        ),
        pytest.param(
            28,
            0,
            0,
            id="d28",
        ),
        pytest.param(
            29,
            0,
            0,
            id="d29",
        ),
        pytest.param(
            30,
            0,
            0,
            id="d30",
        ),
        pytest.param(
            31,
            0,
            0,
            id="d31",
        ),
        pytest.param(
            32,
            0,
            0,
            id="d32",
        ),
        pytest.param(
            33,
            0,
            0,
            id="d33",
        ),
        pytest.param(
            34,
            0,
            0,
            id="d34",
        ),
        pytest.param(
            35,
            0,
            0,
            id="d35",
        ),
        pytest.param(
            36,
            0,
            0,
            id="d36",
        ),
        pytest.param(
            37,
            0,
            0,
            id="d37",
        ),
        pytest.param(
            38,
            0,
            0,
            id="d38",
        ),
        pytest.param(
            39,
            0,
            0,
            id="d39",
        ),
        pytest.param(
            40,
            0,
            0,
            id="d40",
        ),
        pytest.param(
            41,
            0,
            0,
            id="d41",
        ),
        pytest.param(
            42,
            0,
            0,
            id="d42",
        ),
        pytest.param(
            43,
            0,
            0,
            id="d43",
        ),
        pytest.param(
            44,
            0,
            0,
            id="d44",
        ),
        pytest.param(
            45,
            0,
            0,
            id="d45",
        ),
        pytest.param(
            46,
            0,
            0,
            id="d46",
        ),
        pytest.param(
            47,
            0,
            0,
            id="d47",
        ),
        pytest.param(
            48,
            0,
            0,
            id="d48",
        ),
        pytest.param(
            49,
            0,
            0,
            id="d49",
        ),
        pytest.param(
            50,
            0,
            0,
            id="d50",
        ),
        pytest.param(
            51,
            0,
            0,
            id="d51",
        ),
        pytest.param(
            52,
            0,
            0,
            id="d52",
        ),
        pytest.param(
            53,
            0,
            0,
            id="d53",
        ),
        pytest.param(
            54,
            0,
            0,
            id="d54",
        ),
        pytest.param(
            55,
            0,
            0,
            id="d55",
        ),
        pytest.param(
            56,
            0,
            0,
            id="d56",
        ),
        pytest.param(
            57,
            0,
            0,
            id="d57",
        ),
        pytest.param(
            58,
            0,
            0,
            id="d58",
        ),
        pytest.param(
            59,
            0,
            0,
            id="d59",
        ),
        pytest.param(
            60,
            0,
            0,
            id="d60",
        ),
        pytest.param(
            61,
            0,
            0,
            id="d61",
        ),
        pytest.param(
            62,
            0,
            0,
            id="d62",
        ),
        pytest.param(
            63,
            0,
            0,
            id="d63",
        ),
        pytest.param(
            64,
            0,
            0,
            id="d64",
        ),
        pytest.param(
            65,
            0,
            0,
            id="d65",
        ),
        pytest.param(
            66,
            0,
            0,
            id="d66",
        ),
        pytest.param(
            67,
            0,
            0,
            id="d67",
        ),
        pytest.param(
            68,
            0,
            0,
            id="d68",
        ),
        pytest.param(
            69,
            0,
            0,
            id="d69",
        ),
        pytest.param(
            70,
            0,
            0,
            id="d70",
        ),
        pytest.param(
            71,
            0,
            0,
            id="d71",
        ),
        pytest.param(
            72,
            0,
            0,
            id="d72",
        ),
        pytest.param(
            73,
            0,
            0,
            id="d73",
        ),
        pytest.param(
            74,
            0,
            0,
            id="d74",
        ),
        pytest.param(
            75,
            0,
            0,
            id="d75",
        ),
        pytest.param(
            76,
            0,
            0,
            id="d76",
        ),
        pytest.param(
            77,
            0,
            0,
            id="d77",
        ),
        pytest.param(
            78,
            0,
            0,
            id="d78",
        ),
        pytest.param(
            79,
            0,
            0,
            id="d79",
        ),
        pytest.param(
            80,
            0,
            0,
            id="d80",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_shallow_stack(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test_shallow_stack."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = EOA(
        key=0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
    )

    pre[sender] = Account(balance=0x271000000000)

    tx_data = [
        Op.PUSH1[0x1] + Op.SSTORE(key=0x0, value=Op.ADD),
        Op.PUSH1[0x1] + Op.SSTORE(key=0x0, value=Op.MUL),
        Op.PUSH1[0x1] + Op.SSTORE(key=0x0, value=Op.SUB),
        Op.PUSH1[0x1] + Op.SSTORE(key=0x0, value=Op.DIV),
        Op.PUSH1[0x1] + Op.SSTORE(key=0x0, value=Op.SDIV),
        Op.PUSH1[0x1] + Op.SSTORE(key=0x0, value=Op.MOD),
        Op.PUSH1[0x1] + Op.SSTORE(key=0x0, value=Op.SMOD),
        Op.PUSH1[0x2] + Op.PUSH1[0x1] + Op.SSTORE(key=0x0, value=Op.ADDMOD),
        Op.PUSH1[0x2] + Op.PUSH1[0x1] + Op.SSTORE(key=0x0, value=Op.MULMOD),
        Op.PUSH1[0x1] + Op.SSTORE(key=0x0, value=Op.EXP),
        Op.PUSH1[0x1] + Op.SSTORE(key=0x0, value=Op.SIGNEXTEND),
        Op.PUSH1[0x1] + Op.SSTORE(key=0x0, value=Op.LT),
        Op.PUSH1[0x1] + Op.SSTORE(key=0x0, value=Op.GT),
        Op.PUSH1[0x1] + Op.SSTORE(key=0x0, value=Op.SLT),
        Op.PUSH1[0x1] + Op.SSTORE(key=0x0, value=Op.SGT),
        Op.PUSH1[0x1] + Op.SSTORE(key=0x0, value=Op.EQ),
        Op.SSTORE(key=0x0, value=Op.ISZERO),
        Op.PUSH1[0x1] + Op.SSTORE(key=0x0, value=Op.AND),
        Op.PUSH1[0x1] + Op.SSTORE(key=0x0, value=Op.OR),
        Op.PUSH1[0x1] + Op.SSTORE(key=0x0, value=Op.XOR),
        Op.SSTORE(key=0x0, value=Op.NOT),
        Op.PUSH1[0x1] + Op.SSTORE(key=0x0, value=Op.BYTE),
        Op.PUSH1[0x1] + Op.SSTORE(key=0x0, value=Op.SHA3),
        Op.SSTORE(key=0x0, value=Op.BALANCE),
        Op.SSTORE(key=0x0, value=Op.CALLDATALOAD),
        Op.PUSH1[0x1]
        + Op.PUSH1[0x2]
        + Op.CALLDATACOPY
        + Op.PUSH1[0x0]
        + Op.SSTORE,
        Op.PUSH1[0x1]
        + Op.PUSH1[0x2]
        + Op.CODECOPY
        + Op.PUSH1[0x0]
        + Op.SSTORE,
        Op.SSTORE(key=0x0, value=Op.EXTCODESIZE),
        Op.PUSH1[0x1]
        + Op.PUSH1[0x2]
        + Op.PUSH1[0x3]
        + Op.EXTCODECOPY
        + Op.PUSH1[0x0]
        + Op.SSTORE,
        Op.SSTORE(key=0x0, value=Op.BLOCKHASH),
        Op.POP + Op.PUSH1[0x0] + Op.SSTORE,
        Op.SSTORE(key=0x0, value=Op.MLOAD),
        Op.PUSH1[0x1] + Op.MSTORE + Op.PUSH1[0x0] + Op.SSTORE,
        Op.PUSH1[0x1] + Op.MSTORE8 + Op.PUSH1[0x0] + Op.SSTORE,
        Op.SSTORE(key=0x0, value=Op.SLOAD),
        Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x0] + Op.SSTORE,
        Op.JUMP + Op.PUSH1[0x0] + Op.SSTORE,
        Op.PUSH1[0x1] + Op.JUMPI + Op.PUSH1[0x0] + Op.SSTORE,
        Op.SSTORE(key=0x0, value=Op.DUP1),
        Op.PUSH1[0x1] + Op.SSTORE(key=0x0, value=Op.DUP2),
        Op.PUSH1[0x2] + Op.PUSH1[0x1] + Op.SSTORE(key=0x0, value=Op.DUP3),
        Op.PUSH1[0x3]
        + Op.PUSH1[0x2]
        + Op.PUSH1[0x1]
        + Op.SSTORE(key=0x0, value=Op.DUP4),
        Op.PUSH1[0x4]
        + Op.PUSH1[0x3]
        + Op.PUSH1[0x2]
        + Op.PUSH1[0x1]
        + Op.SSTORE(key=0x0, value=Op.DUP5),
        Op.PUSH1[0x5]
        + Op.PUSH1[0x4]
        + Op.PUSH1[0x3]
        + Op.PUSH1[0x2]
        + Op.PUSH1[0x1]
        + Op.SSTORE(key=0x0, value=Op.DUP6),
        Op.PUSH1[0x6]
        + Op.PUSH1[0x5]
        + Op.PUSH1[0x4]
        + Op.PUSH1[0x3]
        + Op.PUSH1[0x2]
        + Op.PUSH1[0x1]
        + Op.SSTORE(key=0x0, value=Op.DUP7),
        Op.PUSH1[0x7]
        + Op.PUSH1[0x6]
        + Op.PUSH1[0x5]
        + Op.PUSH1[0x4]
        + Op.PUSH1[0x3]
        + Op.PUSH1[0x2]
        + Op.PUSH1[0x1]
        + Op.SSTORE(key=0x0, value=Op.DUP8),
        Op.PUSH1[0x8]
        + Op.PUSH1[0x7]
        + Op.PUSH1[0x6]
        + Op.PUSH1[0x5]
        + Op.PUSH1[0x4]
        + Op.PUSH1[0x3]
        + Op.PUSH1[0x2]
        + Op.PUSH1[0x1]
        + Op.SSTORE(key=0x0, value=Op.DUP9),
        Op.PUSH1[0x9]
        + Op.PUSH1[0x8]
        + Op.PUSH1[0x7]
        + Op.PUSH1[0x6]
        + Op.PUSH1[0x5]
        + Op.PUSH1[0x4]
        + Op.PUSH1[0x3]
        + Op.PUSH1[0x2]
        + Op.PUSH1[0x1]
        + Op.SSTORE(key=0x0, value=Op.DUP10),
        Op.PUSH1[0x10]
        + Op.PUSH1[0x9]
        + Op.PUSH1[0x8]
        + Op.PUSH1[0x7]
        + Op.PUSH1[0x6]
        + Op.PUSH1[0x5]
        + Op.PUSH1[0x4]
        + Op.PUSH1[0x3]
        + Op.PUSH1[0x2]
        + Op.PUSH1[0x1]
        + Op.SSTORE(key=0x0, value=Op.DUP11),
        Op.PUSH1[0x11]
        + Op.PUSH1[0x10]
        + Op.PUSH1[0x9]
        + Op.PUSH1[0x8]
        + Op.PUSH1[0x7]
        + Op.PUSH1[0x6]
        + Op.PUSH1[0x5]
        + Op.PUSH1[0x4]
        + Op.PUSH1[0x3]
        + Op.PUSH1[0x2]
        + Op.PUSH1[0x1]
        + Op.SSTORE(key=0x0, value=Op.DUP12),
        Op.PUSH1[0x12]
        + Op.PUSH1[0x11]
        + Op.PUSH1[0x10]
        + Op.PUSH1[0x9]
        + Op.PUSH1[0x8]
        + Op.PUSH1[0x7]
        + Op.PUSH1[0x6]
        + Op.PUSH1[0x5]
        + Op.PUSH1[0x4]
        + Op.PUSH1[0x3]
        + Op.PUSH1[0x2]
        + Op.PUSH1[0x1]
        + Op.SSTORE(key=0x0, value=Op.DUP13),
        Op.PUSH1[0x13]
        + Op.PUSH1[0x12]
        + Op.PUSH1[0x11]
        + Op.PUSH1[0x10]
        + Op.PUSH1[0x9]
        + Op.PUSH1[0x8]
        + Op.PUSH1[0x7]
        + Op.PUSH1[0x6]
        + Op.PUSH1[0x5]
        + Op.PUSH1[0x4]
        + Op.PUSH1[0x3]
        + Op.PUSH1[0x2]
        + Op.PUSH1[0x1]
        + Op.SSTORE(key=0x0, value=Op.DUP14),
        Op.PUSH1[0x14]
        + Op.PUSH1[0x13]
        + Op.PUSH1[0x12]
        + Op.PUSH1[0x11]
        + Op.PUSH1[0x10]
        + Op.PUSH1[0x9]
        + Op.PUSH1[0x8]
        + Op.PUSH1[0x7]
        + Op.PUSH1[0x6]
        + Op.PUSH1[0x5]
        + Op.PUSH1[0x4]
        + Op.PUSH1[0x3]
        + Op.PUSH1[0x2]
        + Op.PUSH1[0x1]
        + Op.SSTORE(key=0x0, value=Op.DUP15),
        Op.PUSH1[0x13]
        + Op.PUSH1[0x12]
        + Op.PUSH1[0x11]
        + Op.PUSH1[0x10]
        + Op.PUSH1[0x9]
        + Op.PUSH1[0x8]
        + Op.PUSH1[0x7]
        + Op.PUSH1[0x6]
        + Op.PUSH1[0x5]
        + Op.PUSH1[0x4]
        + Op.PUSH1[0x3]
        + Op.PUSH1[0x2]
        + Op.PUSH1[0x1]
        + Op.SSTORE(key=0x0, value=Op.DUP16),
        Op.PUSH1[0x1] + Op.SWAP1 + Op.PUSH1[0x0] + Op.SSTORE,
        Op.PUSH1[0x2] + Op.PUSH1[0x1] + Op.SWAP2 + Op.PUSH1[0x0] + Op.SSTORE,
        Op.PUSH1[0x3]
        + Op.PUSH1[0x2]
        + Op.PUSH1[0x1]
        + Op.SWAP3
        + Op.PUSH1[0x0]
        + Op.SSTORE,
        Op.PUSH1[0x4]
        + Op.PUSH1[0x3]
        + Op.PUSH1[0x2]
        + Op.PUSH1[0x1]
        + Op.SWAP4
        + Op.PUSH1[0x0]
        + Op.SSTORE,
        Op.PUSH1[0x5]
        + Op.PUSH1[0x4]
        + Op.PUSH1[0x3]
        + Op.PUSH1[0x2]
        + Op.PUSH1[0x1]
        + Op.SWAP5
        + Op.PUSH1[0x0]
        + Op.SSTORE,
        Op.PUSH1[0x6]
        + Op.PUSH1[0x5]
        + Op.PUSH1[0x4]
        + Op.PUSH1[0x3]
        + Op.PUSH1[0x2]
        + Op.PUSH1[0x1]
        + Op.SWAP6
        + Op.PUSH1[0x0]
        + Op.SSTORE,
        Op.PUSH1[0x7]
        + Op.PUSH1[0x6]
        + Op.PUSH1[0x5]
        + Op.PUSH1[0x4]
        + Op.PUSH1[0x3]
        + Op.PUSH1[0x2]
        + Op.PUSH1[0x1]
        + Op.SWAP7
        + Op.PUSH1[0x0]
        + Op.SSTORE,
        Op.PUSH1[0x8]
        + Op.PUSH1[0x7]
        + Op.PUSH1[0x6]
        + Op.PUSH1[0x5]
        + Op.PUSH1[0x4]
        + Op.PUSH1[0x3]
        + Op.PUSH1[0x2]
        + Op.PUSH1[0x1]
        + Op.SWAP8
        + Op.PUSH1[0x0]
        + Op.SSTORE,
        Op.PUSH1[0x9]
        + Op.PUSH1[0x8]
        + Op.PUSH1[0x7]
        + Op.PUSH1[0x6]
        + Op.PUSH1[0x5]
        + Op.PUSH1[0x4]
        + Op.PUSH1[0x3]
        + Op.PUSH1[0x2]
        + Op.PUSH1[0x1]
        + Op.SWAP9
        + Op.PUSH1[0x0]
        + Op.SSTORE,
        Op.PUSH1[0x10]
        + Op.PUSH1[0x9]
        + Op.PUSH1[0x8]
        + Op.PUSH1[0x7]
        + Op.PUSH1[0x6]
        + Op.PUSH1[0x5]
        + Op.PUSH1[0x4]
        + Op.PUSH1[0x3]
        + Op.PUSH1[0x2]
        + Op.PUSH1[0x1]
        + Op.SWAP10
        + Op.PUSH1[0x0]
        + Op.SSTORE,
        Op.PUSH1[0x11]
        + Op.PUSH1[0x10]
        + Op.PUSH1[0x9]
        + Op.PUSH1[0x8]
        + Op.PUSH1[0x7]
        + Op.PUSH1[0x6]
        + Op.PUSH1[0x5]
        + Op.PUSH1[0x4]
        + Op.PUSH1[0x3]
        + Op.PUSH1[0x2]
        + Op.PUSH1[0x1]
        + Op.SWAP11
        + Op.PUSH1[0x0]
        + Op.SSTORE,
        Op.PUSH1[0x12]
        + Op.PUSH1[0x11]
        + Op.PUSH1[0x10]
        + Op.PUSH1[0x9]
        + Op.PUSH1[0x8]
        + Op.PUSH1[0x7]
        + Op.PUSH1[0x6]
        + Op.PUSH1[0x5]
        + Op.PUSH1[0x4]
        + Op.PUSH1[0x3]
        + Op.PUSH1[0x2]
        + Op.PUSH1[0x1]
        + Op.SWAP12
        + Op.PUSH1[0x0]
        + Op.SSTORE,
        Op.PUSH1[0x13]
        + Op.PUSH1[0x12]
        + Op.PUSH1[0x11]
        + Op.PUSH1[0x10]
        + Op.PUSH1[0x9]
        + Op.PUSH1[0x8]
        + Op.PUSH1[0x7]
        + Op.PUSH1[0x6]
        + Op.PUSH1[0x5]
        + Op.PUSH1[0x4]
        + Op.PUSH1[0x3]
        + Op.PUSH1[0x2]
        + Op.PUSH1[0x1]
        + Op.SWAP13
        + Op.PUSH1[0x0]
        + Op.SSTORE,
        Op.PUSH1[0x14]
        + Op.PUSH1[0x13]
        + Op.PUSH1[0x12]
        + Op.PUSH1[0x11]
        + Op.PUSH1[0x10]
        + Op.PUSH1[0x9]
        + Op.PUSH1[0x8]
        + Op.PUSH1[0x7]
        + Op.PUSH1[0x6]
        + Op.PUSH1[0x5]
        + Op.PUSH1[0x4]
        + Op.PUSH1[0x3]
        + Op.PUSH1[0x2]
        + Op.PUSH1[0x1]
        + Op.SWAP14
        + Op.PUSH1[0x0]
        + Op.SSTORE,
        Op.PUSH1[0x15]
        + Op.PUSH1[0x14]
        + Op.PUSH1[0x13]
        + Op.PUSH1[0x12]
        + Op.PUSH1[0x11]
        + Op.PUSH1[0x10]
        + Op.PUSH1[0x9]
        + Op.PUSH1[0x8]
        + Op.PUSH1[0x7]
        + Op.PUSH1[0x6]
        + Op.PUSH1[0x5]
        + Op.PUSH1[0x4]
        + Op.PUSH1[0x3]
        + Op.PUSH1[0x2]
        + Op.PUSH1[0x1]
        + Op.SWAP15
        + Op.PUSH1[0x0]
        + Op.SSTORE,
        Op.PUSH1[0x12]
        + Op.PUSH1[0x11]
        + Op.PUSH1[0x10]
        + Op.PUSH1[0x9]
        + Op.PUSH1[0x8]
        + Op.PUSH1[0x7]
        + Op.PUSH1[0x6]
        + Op.PUSH1[0x5]
        + Op.PUSH1[0x4]
        + Op.PUSH1[0x3]
        + Op.PUSH1[0x2]
        + Op.PUSH1[0x1]
        + Op.SWAP16
        + Op.PUSH1[0x0]
        + Op.SSTORE,
        Op.PUSH1[0x1] + Op.LOG0 + Op.PUSH1[0x0] + Op.SSTORE,
        Op.PUSH1[0x2] + Op.PUSH1[0x1] + Op.LOG1 + Op.PUSH1[0x0] + Op.SSTORE,
        Op.PUSH1[0x3]
        + Op.PUSH1[0x2]
        + Op.PUSH1[0x1]
        + Op.LOG2
        + Op.PUSH1[0x0]
        + Op.SSTORE,
        Op.PUSH1[0x4]
        + Op.PUSH1[0x3]
        + Op.PUSH1[0x2]
        + Op.PUSH1[0x1]
        + Op.LOG3
        + Op.PUSH1[0x0]
        + Op.SSTORE,
        Op.PUSH1[0x5]
        + Op.PUSH1[0x4]
        + Op.PUSH1[0x3]
        + Op.PUSH1[0x2]
        + Op.PUSH1[0x1]
        + Op.LOG4
        + Op.PUSH1[0x0]
        + Op.SSTORE,
        Op.PUSH1[0x2] + Op.PUSH1[0x1] + Op.SSTORE(key=0x0, value=Op.CREATE),
        Op.PUSH1[0x6]
        + Op.PUSH1[0x5]
        + Op.PUSH1[0x4]
        + Op.PUSH1[0x3]
        + Op.PUSH1[0x2]
        + Op.PUSH1[0x1]
        + Op.SSTORE(key=0x0, value=Op.CALL),
        Op.PUSH1[0x6]
        + Op.PUSH1[0x5]
        + Op.PUSH1[0x4]
        + Op.PUSH1[0x3]
        + Op.PUSH1[0x2]
        + Op.PUSH1[0x1]
        + Op.SSTORE(key=0x0, value=Op.CALLCODE),
        Op.PUSH1[0x1] + Op.RETURN + Op.PUSH1[0x0] + Op.SSTORE,
        Op.PUSH1[0x5]
        + Op.PUSH1[0x4]
        + Op.PUSH1[0x3]
        + Op.PUSH1[0x2]
        + Op.PUSH1[0x1]
        + Op.SSTORE(key=0x0, value=Op.DELEGATECALL),
        Op.SELFDESTRUCT + Op.PUSH1[0x0] + Op.SSTORE,
    ]
    tx_gas = [300000]

    tx = Transaction(
        sender=sender,
        to=None,
        data=tx_data[d],
        gas_limit=tx_gas[g],
    )

    post = {
        compute_create_address(address=sender, nonce=0): Account.NONEXISTENT
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
