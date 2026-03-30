"""
Test_opcodes_transaction_init.

Ported from:
state_tests/stTransactionTest/Opcodes_TransactionInitFiller.json
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
    ["state_tests/stTransactionTest/Opcodes_TransactionInitFiller.json"],
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
        pytest.param(
            110,
            0,
            0,
            id="d110",
        ),
        pytest.param(
            111,
            0,
            0,
            id="d111",
        ),
        pytest.param(
            112,
            0,
            0,
            id="d112",
        ),
        pytest.param(
            113,
            0,
            0,
            id="d113",
        ),
        pytest.param(
            114,
            0,
            0,
            id="d114",
        ),
        pytest.param(
            115,
            0,
            0,
            id="d115",
        ),
        pytest.param(
            116,
            0,
            0,
            id="d116",
        ),
        pytest.param(
            117,
            0,
            0,
            id="d117",
        ),
        pytest.param(
            118,
            0,
            0,
            id="d118",
        ),
        pytest.param(
            119,
            0,
            0,
            id="d119",
        ),
        pytest.param(
            120,
            0,
            0,
            id="d120",
        ),
        pytest.param(
            121,
            0,
            0,
            id="d121",
        ),
        pytest.param(
            122,
            0,
            0,
            id="d122",
        ),
        pytest.param(
            123,
            0,
            0,
            id="d123",
        ),
        pytest.param(
            124,
            0,
            0,
            id="d124",
        ),
        pytest.param(
            125,
            0,
            0,
            id="d125",
        ),
        pytest.param(
            126,
            0,
            0,
            id="d126",
        ),
        pytest.param(
            127,
            0,
            0,
            id="d127",
        ),
        pytest.param(
            128,
            0,
            0,
            id="invalid_first_byte_ef",
        ),
        pytest.param(
            129,
            0,
            0,
            id="side_effects",
        ),
        pytest.param(
            130,
            0,
            0,
            id="side_effects_invalid_opcode",
        ),
        pytest.param(
            131,
            0,
            0,
            id="side_effects_return_ef",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_opcodes_transaction_init(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test_opcodes_transaction_init."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    contract_0 = Address(0xB94F5374FCE5EDBC8E2A8697C15331677E6EBF0B)
    contract_1 = Address(0x0F572E5295C57F15886F9B263E2F6D2D6C7B5EC6)
    sender = EOA(
        key=0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000,
    )

    pre[sender] = Account(balance=0xDE0B6B3A7640000, storage={0: 0})
    # Source: yul
    # berlin { sstore(0, 1) }
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x1) + Op.STOP,
        nonce=0,
        address=Address(0xB94F5374FCE5EDBC8E2A8697C15331677E6EBF0B),  # noqa: E501
    )
    # Source: raw
    # 0x61ffff5060046000f3
    contract_1 = pre.deploy_contract(  # noqa: F841
        code=Op.POP(0xFFFF) + Op.RETURN(offset=0x0, size=0x4),
        balance=0xDE0B6B3A7640000,
        nonce=1,
        address=Address(0x0F572E5295C57F15886F9B263E2F6D2D6C7B5EC6),  # noqa: E501
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": 33, "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                sender: Account(nonce=1),
                Address("0x6295ee1b4f6dd65047762f924ecd367c17eabf8f"): Account(
                    storage={
                        0: 0x38600060013960015160005560006000F3000000000000000000000000000000,  # noqa: E501
                    },
                    nonce=1,
                ),
            },
        },
        {
            "indexes": {"data": 37, "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                sender: Account(nonce=1),
                Address("0x6295ee1b4f6dd65047762f924ecd367c17eabf8f"): Account(
                    nonce=1
                ),
            },
        },
        {
            "indexes": {"data": 38, "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                sender: Account(nonce=1),
                Address("0x6295ee1b4f6dd65047762f924ecd367c17eabf8f"): Account(
                    nonce=1
                ),
            },
        },
        {
            "indexes": {"data": 120, "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                sender: Account(nonce=1),
                Address("0x6295ee1b4f6dd65047762f924ecd367c17eabf8f"): Account(
                    nonce=2
                ),
            },
        },
        {
            "indexes": {"data": 124, "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                sender: Account(nonce=1),
                Address("0x6295ee1b4f6dd65047762f924ecd367c17eabf8f"): Account(
                    nonce=1
                ),
            },
        },
        {
            "indexes": {"data": 125, "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                sender: Account(nonce=1),
                Address("0x6295ee1b4f6dd65047762f924ecd367c17eabf8f"): Account(
                    nonce=1
                ),
            },
        },
        {
            "indexes": {"data": 126, "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                sender: Account(nonce=1),
                Address(
                    "0x6295ee1b4f6dd65047762f924ecd367c17eabf8f"
                ): Account.NONEXISTENT,
            },
        },
        {
            "indexes": {"data": 127, "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                sender: Account(nonce=1),
                Address(
                    "0x6295ee1b4f6dd65047762f924ecd367c17eabf8f"
                ): Account.NONEXISTENT,
            },
        },
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
                    23,
                    24,
                    25,
                    26,
                    27,
                    28,
                    29,
                    30,
                    31,
                    32,
                    34,
                    35,
                    36,
                    39,
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
                    121,
                    122,
                    123,
                ],
                "gas": -1,
                "value": -1,
            },
            "network": [">=Cancun"],
            "result": {
                sender: Account(nonce=1),
                Address("0x6295ee1b4f6dd65047762f924ecd367c17eabf8f"): Account(
                    nonce=1
                ),
            },
        },
        {
            "indexes": {"data": [128], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                sender: Account(nonce=1),
                Address(
                    "0x6295ee1b4f6dd65047762f924ecd367c17eabf8f"
                ): Account.NONEXISTENT,
            },
        },
        {
            "indexes": {"data": [129], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                sender: Account(nonce=1),
                contract_0: Account(storage={0: 1, 1: 0}),
                Address("0x6295ee1b4f6dd65047762f924ecd367c17eabf8f"): Account(
                    nonce=1
                ),
            },
        },
        {
            "indexes": {"data": [130], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                sender: Account(nonce=1),
                contract_0: Account(storage={}),
                Address(
                    "0x6295ee1b4f6dd65047762f924ecd367c17eabf8f"
                ): Account.NONEXISTENT,
            },
        },
        {
            "indexes": {"data": [131], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                sender: Account(nonce=1),
                contract_0: Account(storage={}),
                Address(
                    "0x6295ee1b4f6dd65047762f924ecd367c17eabf8f"
                ): Account.NONEXISTENT,
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx_data = [
        Bytes("0060016000f3"),
        Bytes("60016001015060006000f3"),
        Bytes("60016001025060006000f3"),
        Bytes("60016001035060006000f3"),
        Bytes("60016001045060006000f3"),
        Bytes("60016001055060006000f3"),
        Bytes("60016001065060006000f3"),
        Bytes("60016001075060006000f3"),
        Bytes("600160016001085060006000f3"),
        Bytes("600160016001095060006000f3"),
        Bytes("600160010a5060006000f3"),
        Bytes("600160010b5060006000f3"),
        Bytes("60016001105060006000f3"),
        Bytes("60016001115060006000f3"),
        Bytes("60016001125060006000f3"),
        Bytes("60016001135060006000f3"),
        Bytes("60016001145060006000f3"),
        Bytes("6000155060006000f3"),
        Bytes("60006000165060006000f3"),
        Bytes("60006000175060006000f3"),
        Bytes("60006000185060006000f3"),
        Bytes("6000195060006000f3"),
        Bytes("67805020100804020160001a5060006000f3"),
        Bytes("600060002060006000f3"),
        Bytes("305060006000f3"),
        Bytes("6000315060006000f3"),
        Bytes("325060006000f3"),
        Bytes("335060006000f3"),
        Bytes("345060006000f3"),
        Bytes("6000355060006000f3"),
        Bytes("365060006000f3"),
        Bytes("6000600060003760006000f3"),
        Bytes("385060006000f3"),
        Bytes("38600060013960015160005560006000f3"),
        Bytes("3a5060006000f3"),
        Bytes("60003b5060006000f3"),
        Bytes(
            "6014600060007310000000000000000000000000000000000000103c60006000f3"  # noqa: E501
        ),
        Bytes("3d5060006000f3"),
        Bytes("6000600060003e60006000f3"),
        Bytes("60005060005060006000f3"),
        Bytes("6000515060006000f3"),
        Bytes("600060005260006000f3"),
        Bytes("60ff60005360006000f3"),
        Bytes("6000545060006000f3"),
        Bytes("600160015560006000f3"),
        Bytes("600456005b60006000f3"),
        Bytes("6001600657005b60006000f3"),
        Bytes("585060006000f3"),
        Bytes("595060006000f3"),
        Bytes("5a5060006000f3"),
        Bytes("5b60006000f3"),
        Bytes("60ff5060006000f3"),
        Bytes("61ffff5060006000f3"),
        Bytes("62ffffff5060006000f3"),
        Bytes("63ffffffff5060006000f3"),
        Bytes("64ffffffffff5060006000f3"),
        Bytes("65ffffffffffff5060006000f3"),
        Bytes("66ffffffffffffff5060006000f3"),
        Bytes("67ffffffffffffffff5060006000f3"),
        Bytes("68ffffffffffffffffff5060006000f3"),
        Bytes("69ffffffffffffffffffff5060006000f3"),
        Bytes("6affffffffffffffffffffff5060006000f3"),
        Bytes("6bffffffffffffffffffffffff5060006000f3"),
        Address(0x6CFFFFFFFFFFFFFFFFFFFFFFFFFF5060006000F3),
        Bytes("6dffffffffffffffffffffffffffff5060006000f3"),
        Bytes("6effffffffffffffffffffffffffffff5060006000f3"),
        Bytes("6fffffffffffffffffffffffffffffffff5060006000f3"),
        Bytes("70ffffffffffffffffffffffffffffffffff5060006000f3"),
        Bytes("71ffffffffffffffffffffffffffffffffffff5060006000f3"),
        Bytes("72ffffffffffffffffffffffffffffffffffffff5060006000f3"),
        Bytes("73ffffffffffffffffffffffffffffffffffffffff5060006000f3"),
        Bytes("74ffffffffffffffffffffffffffffffffffffffffff5060006000f3"),
        Bytes("75ffffffffffffffffffffffffffffffffffffffffffff5060006000f3"),
        Bytes("76ffffffffffffffffffffffffffffffffffffffffffffff5060006000f3"),
        Bytes(
            "77ffffffffffffffffffffffffffffffffffffffffffffffff5060006000f3"
        ),
        Hash(
            0x78FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF5060006000F3
        ),
        Bytes(
            "79ffffffffffffffffffffffffffffffffffffffffffffffffffff5060006000f3"  # noqa: E501
        ),
        Bytes(
            "7affffffffffffffffffffffffffffffffffffffffffffffffffffff5060006000f3"  # noqa: E501
        ),
        Bytes(
            "7bffffffffffffffffffffffffffffffffffffffffffffffffffffffff5060006000f3"  # noqa: E501
        ),
        Bytes(
            "7cffffffffffffffffffffffffffffffffffffffffffffffffffffffffff5060006000f3"  # noqa: E501
        ),
        Bytes(
            "7dffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff5060006000f3"  # noqa: E501
        ),
        Bytes(
            "7effffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff5060006000f3"  # noqa: E501
        ),
        Bytes(
            "7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff5060006000f3"  # noqa: E501
        ),
        Bytes("60ff80505060006000f3"),
        Bytes("60ff60ff8150505060006000f3"),
        Bytes("60ff60ff60ff825050505060006000f3"),
        Bytes("60ff60ff60ff60ff83505050505060006000f3"),
        Bytes("60ff60ff60ff60ff60ff8450505050505060006000f3"),
        Bytes("60ff60ff60ff60ff60ff60ff855050505050505060006000f3"),
        Bytes("60ff60ff60ff60ff60ff60ff60ff86505050505050505060006000f3"),
        Bytes(
            "60ff60ff60ff60ff60ff60ff60ff60ff8750505050505050505060006000f3"
        ),
        Bytes(
            "60ff60ff60ff60ff60ff60ff60ff60ff60ff885050505050505050505060006000f3"  # noqa: E501
        ),
        Bytes(
            "60ff60ff60ff60ff60ff60ff60ff60ff60ff60ff89505050505050505050505060006000f3"  # noqa: E501
        ),
        Bytes(
            "60ff60ff60ff60ff60ff60ff60ff60ff60ff60ff60ff8a50505050505050505050505060006000f3"  # noqa: E501
        ),
        Bytes(
            "60ff60ff60ff60ff60ff60ff60ff60ff60ff60ff60ff60ff8b5050505050505050505050505060006000f3"  # noqa: E501
        ),
        Bytes(
            "60ff60ff60ff60ff60ff60ff60ff60ff60ff60ff60ff60ff60ff8c505050505050505050505050505060006000f3"  # noqa: E501
        ),
        Bytes(
            "60ff60ff60ff60ff60ff60ff60ff60ff60ff60ff60ff60ff60ff60ff8d50505050505050505050505050505060006000f3"  # noqa: E501
        ),
        Bytes(
            "60ff60ff60ff60ff60ff60ff60ff60ff60ff60ff60ff60ff60ff60ff60ff8e5050505050505050505050505050505060006000f3"  # noqa: E501
        ),
        Bytes(
            "60ff60ff60ff60ff60ff60ff60ff60ff60ff60ff60ff60ff60ff60ff60ff60ff8f505050505050505050505050505050505060006000f3"  # noqa: E501
        ),
        Bytes("60ff60ff90505060006000f3"),
        Bytes("60ff60ff60ff9150505060006000f3"),
        Bytes("60ff60ff60ff60ff925050505060006000f3"),
        Bytes("60ff60ff60ff60ff60ff93505050505060006000f3"),
        Bytes("60ff60ff60ff60ff60ff60ff9450505050505060006000f3"),
        Bytes("60ff60ff60ff60ff60ff60ff60ff955050505050505060006000f3"),
        Bytes("60ff60ff60ff60ff60ff60ff60ff60ff96505050505050505060006000f3"),
        Bytes(
            "600060ff60ff60ff60ff60ff60ff60ff60ff9750505050505050505060006000f3"  # noqa: E501
        ),
        Bytes(
            "600060ff60ff60ff60ff60ff60ff60ff60ff60ff985050505050505050505060006000f3"  # noqa: E501
        ),
        Bytes(
            "600060ff60ff60ff60ff60ff60ff60ff60ff60ff60ff99505050505050505050505060006000f3"  # noqa: E501
        ),
        Bytes(
            "600060ff60ff60ff60ff60ff60ff60ff60ff60ff60ff60ff9a50505050505050505050505060006000f3"  # noqa: E501
        ),
        Bytes(
            "600060ff60ff60ff60ff60ff60ff60ff60ff60ff60ff60ff60ff9b5050505050505050505050505060006000f3"  # noqa: E501
        ),
        Bytes(
            "600060ff60ff60ff60ff60ff60ff60ff60ff60ff60ff60ff60ff60ff9c505050505050505050505050505060006000f3"  # noqa: E501
        ),
        Bytes(
            "600060ff60ff60ff60ff60ff60ff60ff60ff60ff60ff60ff60ff60ff60ff9d50505050505050505050505050505060006000f3"  # noqa: E501
        ),
        Bytes(
            "600060ff60ff60ff60ff60ff60ff60ff60ff60ff60ff60ff60ff60ff60ff60ff9e5050505050505050505050505050505060006000f3"  # noqa: E501
        ),
        Bytes(
            "600060ff60ff60ff60ff60ff60ff60ff60ff60ff60ff60ff60ff60ff60ff60ff60ff9f505050505050505050505050505050505060006000f3"  # noqa: E501
        ),
        Bytes("60006000a060006000f3"),
        Bytes("60ff60006000a160006000f3"),
        Bytes("60ff60ff60006000a260006000f3"),
        Bytes("60ff60ff60ff60006000a360006000f3"),
        Bytes("60ff60ff60ff60ff60006000a460006000f3"),
        Bytes("6000600060fff05060006000f3"),
        Bytes(
            "60006000600060006017730f572e5295c57f15886f9b263e2f6d2d6c7b5ec66064f15060006000f3"  # noqa: E501
        ),
        Bytes(
            "60006000600060006000730f572e5295c57f15886f9b263e2f6d2d6c7b5ec66064f25060006000f3"  # noqa: E501
        ),
        Bytes("60006000f3"),
        Bytes(
            "6000600060006000730f572e5295c57f15886f9b263e2f6d2d6c7b5ec6620186a0f45060006000f3"  # noqa: E501
        ),
        Bytes(
            "6000600060006000730f572e5295c57f15886f9b263e2f6d2d6c7b5ec6612710fa5060006000f3"  # noqa: E501
        ),
        Bytes("60006000fd60006000f3"),
        Bytes("32ff"),
        Bytes("ef"),
        Hash(
            0x60008080808073B94F5374FCE5EDBC8E2A8697C15331677E6EBF0B61C350F100
        ),
        Bytes(
            "60008080808073b94f5374fce5edbc8e2a8697c15331677e6ebf0b61c350f150fe"  # noqa: E501
        ),
        Bytes(
            "60008080808073b94f5374fce5edbc8e2a8697c15331677e6ebf0b61c350f15060ef60005360016000f3"  # noqa: E501
        ),
    ]
    tx_gas = [400000]
    tx_value = [100000]

    tx = Transaction(
        sender=sender,
        to=None,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        value=tx_value[v],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
