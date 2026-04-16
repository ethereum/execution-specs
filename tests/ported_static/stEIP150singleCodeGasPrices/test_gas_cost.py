"""
Ori Pomerantz qbzzt1@gmail.com.

Ported from:
state_tests/stEIP150singleCodeGasPrices/gasCostFiller.yml
"""

import pytest
from execution_testing import (
    EOA,
    Account,
    Address,
    Alloc,
    Bytes,
    Environment,
    StateTestFiller,
    Storage,
    Transaction,
)
from execution_testing.forks import Fork
from execution_testing.specs.static_state.expect_section import (
    resolve_expect_post,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


def _storage_with_any(base: dict, any_keys: list) -> Storage:
    """Create Storage with set_expect_any for specified keys."""
    s = Storage(base)
    for k in any_keys:
        s.set_expect_any(k)
    return s


@pytest.mark.ported_from(
    ["state_tests/stEIP150singleCodeGasPrices/gasCostFiller.yml"],
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
        pytest.param(
            81,
            0,
            0,
            id="d81",
        ),
        pytest.param(
            82,
            0,
            0,
            id="d82",
        ),
        pytest.param(
            83,
            0,
            0,
            id="d83",
        ),
        pytest.param(
            84,
            0,
            0,
            id="d84",
        ),
        pytest.param(
            85,
            0,
            0,
            id="d85",
        ),
        pytest.param(
            86,
            0,
            0,
            id="d86",
        ),
        pytest.param(
            87,
            0,
            0,
            id="d87",
        ),
        pytest.param(
            88,
            0,
            0,
            id="d88",
        ),
        pytest.param(
            89,
            0,
            0,
            id="d89",
        ),
        pytest.param(
            90,
            0,
            0,
            id="d90",
        ),
        pytest.param(
            91,
            0,
            0,
            id="d91",
        ),
        pytest.param(
            92,
            0,
            0,
            id="d92",
        ),
        pytest.param(
            93,
            0,
            0,
            id="d93",
        ),
        pytest.param(
            94,
            0,
            0,
            id="d94",
        ),
        pytest.param(
            95,
            0,
            0,
            id="d95",
        ),
        pytest.param(
            96,
            0,
            0,
            id="d96",
        ),
        pytest.param(
            97,
            0,
            0,
            id="d97",
        ),
        pytest.param(
            98,
            0,
            0,
            id="d98",
        ),
        pytest.param(
            99,
            0,
            0,
            id="d99",
        ),
        pytest.param(
            100,
            0,
            0,
            id="d100",
        ),
        pytest.param(
            101,
            0,
            0,
            id="d101",
        ),
        pytest.param(
            102,
            0,
            0,
            id="d102",
        ),
        pytest.param(
            103,
            0,
            0,
            id="d103",
        ),
        pytest.param(
            104,
            0,
            0,
            id="d104",
        ),
        pytest.param(
            105,
            0,
            0,
            id="d105",
        ),
        pytest.param(
            106,
            0,
            0,
            id="d106",
        ),
        pytest.param(
            107,
            0,
            0,
            id="d107",
        ),
        pytest.param(
            108,
            0,
            0,
            id="d108",
        ),
        pytest.param(
            109,
            0,
            0,
            id="d109",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_gas_cost(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Ori Pomerantz qbzzt1@gmail."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = EOA(
        key=0x40AC0FC28C27E961EE46EC43355A094DE205856EDBD4654CF2577C2608D4EC1E
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[sender] = Account(balance=0xBA1A9CE0BA1A9CE)
    # Source: lll
    # { ; LLL doesn't let us call arbitrary code, so we craft
    #   ; a new contract with the opcode and then call it to see
    #   ; how much the contract cost
    #   ;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
    #   ; Initialization
    #
    #   ; Variables (0x20 byte wide)
    #   (def 'opcode            0x200)
    #   (def 'contractLength    0x220)
    #   (def 'constructorLength 0x240)
    #   (def 'i                 0x260)
    #   (def 'addr              0x280)
    #   (def 'gasB4             0x300)
    #   (def 'gasAfter          0x320)
    #   (def 'expectedCost      0x340)
    #
    #   ; Maximum length of contract
    #   (def 'maxLength         0x100)
    #
    #   ; Code in memory
    #   (def 'constructorCode   0x000)
    #   (def 'contractCode      (+ constructorCode maxLength))
    #   ; contractCode has to be immediately after constructoCode
    #   ; for us to send it as part of the constructor code
    #
    #   ; Cost of everything around the opcode
    #   (def 'sysCost           0x311)
    #
    #
    #   ; Understand the input
    # ... (55 more lines)
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(
            offset=0x200,
            value=Op.DIV(Op.CALLDATALOAD(offset=0x0), Op.EXP(0x2, 0xF8)),
        )
        + Op.MSTORE(
            offset=0x340,
            value=Op.AND(
                Op.DIV(Op.CALLDATALOAD(offset=0x0), Op.EXP(0x2, 0xE8)), 0xFFFF
            ),
        )
        + Op.MSTORE(offset=0x260, value=0x11)
        + Op.JUMPDEST
        + Op.JUMPI(pc=0x76, condition=Op.ISZERO(Op.MLOAD(offset=0x260)))
        + Op.MSTORE(offset=0x260, value=Op.SUB(Op.MLOAD(offset=0x260), 0x1))
        + Op.MSTORE8(
            offset=Op.ADD(Op.ADD(0x0, 0x100), Op.MLOAD(offset=0x220)),
            value=0x61,
        )
        + Op.MSTORE8(
            offset=Op.ADD(
                Op.ADD(Op.ADD(0x0, 0x100), Op.MLOAD(offset=0x220)), 0x1
            ),
            value=0xDA,
        )
        + Op.MSTORE8(
            offset=Op.ADD(
                Op.ADD(Op.ADD(0x0, 0x100), Op.MLOAD(offset=0x220)), 0x2
            ),
            value=0x7A,
        )
        + Op.MSTORE(offset=0x220, value=Op.ADD(Op.MLOAD(offset=0x220), 0x3))
        + Op.JUMP(pc=0x24)
        + Op.JUMPDEST
        + Op.MSTORE8(
            offset=Op.ADD(Op.ADD(0x0, 0x100), Op.MLOAD(offset=0x220)),
            value=Op.MLOAD(offset=0x200),
        )
        + Op.MSTORE8(
            offset=Op.ADD(
                Op.ADD(Op.ADD(0x0, 0x100), Op.MLOAD(offset=0x220)), 0x1
            ),
            value=0x0,
        )
        + Op.MSTORE(offset=0x220, value=Op.ADD(Op.MLOAD(offset=0x220), 0x2))
        + Op.PUSH1[0x1B]
        + Op.CODECOPY(dest_offset=0x0, offset=Op.PUSH2[0xFB], size=Op.DUP1)
        + Op.PUSH2[0x240]
        + Op.MSTORE
        + Op.MSTORE(
            offset=0x280,
            value=Op.CREATE(value=0x0, offset=0x0, size=Op.MUL(0x100, 0x2)),
        )
        + Op.MSTORE(offset=0x300, value=Op.GAS)
        + Op.POP(
            Op.CALL(
                gas=0x10000,
                address=Op.MLOAD(offset=0x280),
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.MSTORE(offset=0x320, value=Op.GAS)
        + Op.SSTORE(
            key=0x0,
            value=Op.SUB(
                Op.SUB(
                    Op.SUB(Op.MLOAD(offset=0x300), Op.MLOAD(offset=0x320)),
                    0x311,
                ),
                Op.MLOAD(offset=0x340),
            ),
        )
        + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x340))
        + Op.STOP
        + Op.INVALID
        + Op.CODECOPY(
            dest_offset=Op.ADD(0x0, 0x100),
            offset=Op.ADD(0x0, 0x100),
            size=0x100,
        )
        + Op.RETURN(offset=Op.ADD(0x0, 0x100), size=0x100)
        + Op.STOP,
        storage={0: 24743},
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0xCCDCF3FF42C8382ABEEF05BB8949F975A6BC345C),  # noqa: E501
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {
                "data": [
                    0,
                    1,
                    2,
                    3,
                    4,
                    5,
                    6,
                    7,
                    8,
                    9,
                    10,
                    11,
                    12,
                    13,
                    14,
                    15,
                    16,
                    17,
                    18,
                    19,
                    20,
                    21,
                    22,
                    24,
                    25,
                    26,
                    27,
                    28,
                    29,
                    30,
                    32,
                    33,
                    34,
                    35,
                    36,
                    37,
                    38,
                    41,
                    42,
                    43,
                    44,
                    46,
                    47,
                    48,
                    49,
                    50,
                    51,
                    52,
                    53,
                    54,
                    55,
                    56,
                    57,
                    58,
                    59,
                    60,
                    61,
                    62,
                    63,
                    64,
                    65,
                    66,
                    67,
                    68,
                    69,
                    70,
                    71,
                    72,
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
                    96,
                    97,
                    98,
                    99,
                    100,
                    101,
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
                    120,
                    121,
                    122,
                    123,
                    124,
                    125,
                    126,
                    127,
                    128,
                    129,
                    130,
                    131,
                    132,
                    133,
                    134,
                    135,
                    136,
                    137,
                    138,
                    139,
                    140,
                    141,
                    142,
                    143,
                    144,
                    145,
                    146,
                    147,
                    148,
                    149,
                    150,
                    151,
                    152,
                    153,
                    154,
                    155,
                    156,
                    157,
                    158,
                    159,
                    160,
                    161,
                    162,
                    163,
                    164,
                    165,
                    166,
                    167,
                    168,
                    169,
                    170,
                    171,
                    172,
                    173,
                    174,
                    175,
                    176,
                    177,
                    178,
                    179,
                    180,
                    181,
                    182,
                    183,
                    184,
                    185,
                    186,
                    187,
                    188,
                    189,
                    190,
                    191,
                    192,
                    193,
                    194,
                    195,
                    196,
                    197,
                    198,
                    199,
                    200,
                ],
                "gas": -1,
                "value": -1,
            },
            "network": [">=Cancun"],
            "result": {
                addr: Account(
                    storage=_storage_with_any(
                        {
                            0: 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFDA8,  # noqa: E501
                        },
                        [1],
                    ),
                ),
            },
        },
        {
            "indexes": {"data": [39], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                addr: Account(storage=_storage_with_any({0: 700}, [1]))
            },
        },
        {
            "indexes": {"data": [40], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                addr: Account(storage=_storage_with_any({0: 1500}, [1]))
            },
        },
        {
            "indexes": {"data": [45], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                addr: Account(storage=_storage_with_any({0: 2000}, [1]))
            },
        },
        {
            "indexes": {"data": [31, 23], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                addr: Account(storage=_storage_with_any({0: 1300}, [1]))
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx_data = [
        Bytes("000000"),
        Bytes("010003"),
        Bytes("020005"),
        Bytes("030003"),
        Bytes("040005"),
        Bytes("050005"),
        Bytes("060005"),
        Bytes("070005"),
        Bytes("080008"),
        Bytes("090008"),
        Bytes("0b0005"),
        Bytes("100003"),
        Bytes("110003"),
        Bytes("120003"),
        Bytes("130003"),
        Bytes("140003"),
        Bytes("150003"),
        Bytes("160003"),
        Bytes("170003"),
        Bytes("180003"),
        Bytes("190003"),
        Bytes("1a0003"),
        Bytes("300002"),
        Bytes("3102bc"),
        Bytes("320002"),
        Bytes("330002"),
        Bytes("340002"),
        Bytes("350003"),
        Bytes("360002"),
        Bytes("380002"),
        Bytes("3a0002"),
        Bytes("3b02bc"),
        Bytes("400014"),
        Bytes("410002"),
        Bytes("420002"),
        Bytes("430002"),
        Bytes("440002"),
        Bytes("450002"),
        Bytes("500002"),
        Bytes("540320"),
        Bytes("554e20"),
        Bytes("580002"),
        Bytes("590002"),
        Bytes("5a0002"),
        Bytes("5b0001"),
        Bytes("ff1388"),
        Bytes("600003"),
        Bytes("610003"),
        Bytes("620003"),
        Bytes("630003"),
        Bytes("640003"),
        Bytes("650003"),
        Bytes("660003"),
        Bytes("670003"),
        Bytes("680003"),
        Bytes("690003"),
        Bytes("6a0003"),
        Bytes("6b0003"),
        Bytes("6c0003"),
        Bytes("6d0003"),
        Bytes("6e0003"),
        Bytes("6f0003"),
        Bytes("700003"),
        Bytes("710003"),
        Bytes("720003"),
        Bytes("730003"),
        Bytes("740003"),
        Bytes("750003"),
        Bytes("760003"),
        Bytes("770003"),
        Bytes("780003"),
        Bytes("790003"),
        Bytes("7a0003"),
        Bytes("7b0003"),
        Bytes("7c0003"),
        Bytes("7d0003"),
        Bytes("7e0003"),
        Bytes("7f0003"),
        Bytes("800003"),
        Bytes("810003"),
        Bytes("820003"),
        Bytes("830003"),
        Bytes("840003"),
        Bytes("850003"),
        Bytes("860003"),
        Bytes("870003"),
        Bytes("880003"),
        Bytes("890003"),
        Bytes("8a0003"),
        Bytes("8b0003"),
        Bytes("8c0003"),
        Bytes("8d0003"),
        Bytes("8e0003"),
        Bytes("8f0003"),
        Bytes("900003"),
        Bytes("910003"),
        Bytes("920003"),
        Bytes("930003"),
        Bytes("940003"),
        Bytes("950003"),
        Bytes("960003"),
        Bytes("970003"),
        Bytes("980003"),
        Bytes("990003"),
        Bytes("9a0003"),
        Bytes("9b0003"),
        Bytes("9c0003"),
        Bytes("9d0003"),
        Bytes("9e0003"),
        Bytes("9f0003"),
    ]
    tx_gas = [16777216]
    tx_value = [1]

    tx = Transaction(
        sender=sender,
        to=addr,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        value=tx_value[v],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
