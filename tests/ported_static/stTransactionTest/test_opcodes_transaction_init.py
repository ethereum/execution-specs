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
    StateTestFiller,
    Transaction,
    compute_create_address,
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
                compute_create_address(address=sender, nonce=0): Account(
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
                compute_create_address(address=sender, nonce=0): Account(
                    nonce=1
                ),
            },
        },
        {
            "indexes": {"data": 38, "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                sender: Account(nonce=1),
                compute_create_address(address=sender, nonce=0): Account(
                    nonce=1
                ),
            },
        },
        {
            "indexes": {"data": 120, "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                sender: Account(nonce=1),
                compute_create_address(address=sender, nonce=0): Account(
                    nonce=2
                ),
            },
        },
        {
            "indexes": {"data": 124, "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                sender: Account(nonce=1),
                compute_create_address(address=sender, nonce=0): Account(
                    nonce=1
                ),
            },
        },
        {
            "indexes": {"data": 125, "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                sender: Account(nonce=1),
                compute_create_address(address=sender, nonce=0): Account(
                    nonce=1
                ),
            },
        },
        {
            "indexes": {"data": 126, "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                sender: Account(nonce=1),
                compute_create_address(
                    address=sender, nonce=0
                ): Account.NONEXISTENT,
            },
        },
        {
            "indexes": {"data": 127, "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                sender: Account(nonce=1),
                compute_create_address(
                    address=sender, nonce=0
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
                compute_create_address(address=sender, nonce=0): Account(
                    nonce=1
                ),
            },
        },
        {
            "indexes": {"data": [128], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                sender: Account(nonce=1),
                compute_create_address(
                    address=sender, nonce=0
                ): Account.NONEXISTENT,
            },
        },
        {
            "indexes": {"data": [129], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                sender: Account(nonce=1),
                contract_0: Account(storage={0: 1, 1: 0}),
                compute_create_address(address=sender, nonce=0): Account(
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
                compute_create_address(
                    address=sender, nonce=0
                ): Account.NONEXISTENT,
            },
        },
        {
            "indexes": {"data": [131], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                sender: Account(nonce=1),
                contract_0: Account(storage={}),
                compute_create_address(
                    address=sender, nonce=0
                ): Account.NONEXISTENT,
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx_data = [
        Op.STOP + Op.RETURN(offset=0x0, size=0x1),
        Op.POP(Op.ADD(0x1, 0x1)) + Op.RETURN(offset=0x0, size=0x0),
        Op.POP(Op.MUL(0x1, 0x1)) + Op.RETURN(offset=0x0, size=0x0),
        Op.POP(Op.SUB(0x1, 0x1)) + Op.RETURN(offset=0x0, size=0x0),
        Op.POP(Op.DIV(0x1, 0x1)) + Op.RETURN(offset=0x0, size=0x0),
        Op.POP(Op.SDIV(0x1, 0x1)) + Op.RETURN(offset=0x0, size=0x0),
        Op.POP(Op.MOD(0x1, 0x1)) + Op.RETURN(offset=0x0, size=0x0),
        Op.POP(Op.SMOD(0x1, 0x1)) + Op.RETURN(offset=0x0, size=0x0),
        Op.POP(Op.ADDMOD(0x1, 0x1, 0x1)) + Op.RETURN(offset=0x0, size=0x0),
        Op.POP(Op.MULMOD(0x1, 0x1, 0x1)) + Op.RETURN(offset=0x0, size=0x0),
        Op.POP(Op.EXP(0x1, 0x1)) + Op.RETURN(offset=0x0, size=0x0),
        Op.POP(Op.SIGNEXTEND(0x1, 0x1)) + Op.RETURN(offset=0x0, size=0x0),
        Op.POP(Op.LT(0x1, 0x1)) + Op.RETURN(offset=0x0, size=0x0),
        Op.POP(Op.GT(0x1, 0x1)) + Op.RETURN(offset=0x0, size=0x0),
        Op.POP(Op.SLT(0x1, 0x1)) + Op.RETURN(offset=0x0, size=0x0),
        Op.POP(Op.SGT(0x1, 0x1)) + Op.RETURN(offset=0x0, size=0x0),
        Op.POP(Op.EQ(0x1, 0x1)) + Op.RETURN(offset=0x0, size=0x0),
        Op.POP(Op.ISZERO(0x0)) + Op.RETURN(offset=0x0, size=0x0),
        Op.POP(Op.AND(0x0, 0x0)) + Op.RETURN(offset=0x0, size=0x0),
        Op.POP(Op.OR(0x0, 0x0)) + Op.RETURN(offset=0x0, size=0x0),
        Op.POP(Op.XOR(0x0, 0x0)) + Op.RETURN(offset=0x0, size=0x0),
        Op.POP(Op.NOT(0x0)) + Op.RETURN(offset=0x0, size=0x0),
        Op.POP(Op.BYTE(0x0, 0x8050201008040201))
        + Op.RETURN(offset=0x0, size=0x0),
        Op.SHA3(offset=0x0, size=0x0) + Op.RETURN(offset=0x0, size=0x0),
        Op.POP(Op.ADDRESS) + Op.RETURN(offset=0x0, size=0x0),
        Op.POP(Op.BALANCE(address=0x0)) + Op.RETURN(offset=0x0, size=0x0),
        Op.POP(Op.ORIGIN) + Op.RETURN(offset=0x0, size=0x0),
        Op.POP(Op.CALLER) + Op.RETURN(offset=0x0, size=0x0),
        Op.POP(Op.CALLVALUE) + Op.RETURN(offset=0x0, size=0x0),
        Op.POP(Op.CALLDATALOAD(offset=0x0)) + Op.RETURN(offset=0x0, size=0x0),
        Op.POP(Op.CALLDATASIZE) + Op.RETURN(offset=0x0, size=0x0),
        Op.CALLDATACOPY(dest_offset=0x0, offset=0x0, size=0x0)
        + Op.RETURN(offset=0x0, size=0x0),
        Op.POP(Op.CODESIZE) + Op.RETURN(offset=0x0, size=0x0),
        Op.CODECOPY(dest_offset=0x1, offset=0x0, size=Op.CODESIZE)
        + Op.SSTORE(key=0x0, value=Op.MLOAD(offset=0x1))
        + Op.RETURN(offset=0x0, size=0x0),
        Op.POP(Op.GASPRICE) + Op.RETURN(offset=0x0, size=0x0),
        Op.POP(Op.EXTCODESIZE(address=0x0)) + Op.RETURN(offset=0x0, size=0x0),
        Op.EXTCODECOPY(
            address=0x1000000000000000000000000000000000000010,
            dest_offset=0x0,
            offset=0x0,
            size=0x14,
        )
        + Op.RETURN(offset=0x0, size=0x0),
        Op.POP(Op.RETURNDATASIZE) + Op.RETURN(offset=0x0, size=0x0),
        Op.RETURNDATACOPY(dest_offset=0x0, offset=0x0, size=0x0)
        + Op.RETURN(offset=0x0, size=0x0),
        Op.POP(0x0) * 2 + Op.RETURN(offset=0x0, size=0x0),
        Op.POP(Op.MLOAD(offset=0x0)) + Op.RETURN(offset=0x0, size=0x0),
        Op.MSTORE(offset=0x0, value=0x0) + Op.RETURN(offset=0x0, size=0x0),
        Op.MSTORE8(offset=0x0, value=0xFF) + Op.RETURN(offset=0x0, size=0x0),
        Op.POP(Op.SLOAD(key=0x0)) + Op.RETURN(offset=0x0, size=0x0),
        Op.SSTORE(key=0x1, value=0x1) + Op.RETURN(offset=0x0, size=0x0),
        Op.JUMP(pc=0x4)
        + Op.STOP
        + Op.JUMPDEST
        + Op.RETURN(offset=0x0, size=0x0),
        Op.JUMPI(pc=0x6, condition=0x1)
        + Op.STOP
        + Op.JUMPDEST
        + Op.RETURN(offset=0x0, size=0x0),
        Op.POP(Op.PC) + Op.RETURN(offset=0x0, size=0x0),
        Op.POP(Op.MSIZE) + Op.RETURN(offset=0x0, size=0x0),
        Op.POP(Op.GAS) + Op.RETURN(offset=0x0, size=0x0),
        Op.JUMPDEST + Op.RETURN(offset=0x0, size=0x0),
        Op.POP(0xFF) + Op.RETURN(offset=0x0, size=0x0),
        Op.POP(0xFFFF) + Op.RETURN(offset=0x0, size=0x0),
        Op.POP(0xFFFFFF) + Op.RETURN(offset=0x0, size=0x0),
        Op.POP(0xFFFFFFFF) + Op.RETURN(offset=0x0, size=0x0),
        Op.POP(0xFFFFFFFFFF) + Op.RETURN(offset=0x0, size=0x0),
        Op.POP(0xFFFFFFFFFFFF) + Op.RETURN(offset=0x0, size=0x0),
        Op.POP(0xFFFFFFFFFFFFFF) + Op.RETURN(offset=0x0, size=0x0),
        Op.POP(0xFFFFFFFFFFFFFFFF) + Op.RETURN(offset=0x0, size=0x0),
        Op.POP(0xFFFFFFFFFFFFFFFFFF) + Op.RETURN(offset=0x0, size=0x0),
        Op.POP(0xFFFFFFFFFFFFFFFFFFFF) + Op.RETURN(offset=0x0, size=0x0),
        Op.POP(0xFFFFFFFFFFFFFFFFFFFFFF) + Op.RETURN(offset=0x0, size=0x0),
        Op.POP(0xFFFFFFFFFFFFFFFFFFFFFFFF) + Op.RETURN(offset=0x0, size=0x0),
        Op.POP(0xFFFFFFFFFFFFFFFFFFFFFFFFFF) + Op.RETURN(offset=0x0, size=0x0),
        Op.POP(0xFFFFFFFFFFFFFFFFFFFFFFFFFFFF)
        + Op.RETURN(offset=0x0, size=0x0),
        Op.POP(0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)
        + Op.RETURN(offset=0x0, size=0x0),
        Op.POP(0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)
        + Op.RETURN(offset=0x0, size=0x0),
        Op.POP(0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)
        + Op.RETURN(offset=0x0, size=0x0),
        Op.POP(0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)
        + Op.RETURN(offset=0x0, size=0x0),
        Op.POP(0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)
        + Op.RETURN(offset=0x0, size=0x0),
        Op.POP(0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)
        + Op.RETURN(offset=0x0, size=0x0),
        Op.POP(0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)
        + Op.RETURN(offset=0x0, size=0x0),
        Op.POP(0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)
        + Op.RETURN(offset=0x0, size=0x0),
        Op.POP(0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)
        + Op.RETURN(offset=0x0, size=0x0),
        Op.POP(0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)
        + Op.RETURN(offset=0x0, size=0x0),
        Op.POP(0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)
        + Op.RETURN(offset=0x0, size=0x0),
        Op.POP(0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)
        + Op.RETURN(offset=0x0, size=0x0),
        Op.POP(0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)
        + Op.RETURN(offset=0x0, size=0x0),
        Op.POP(0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)
        + Op.RETURN(offset=0x0, size=0x0),
        Op.POP(0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)
        + Op.RETURN(offset=0x0, size=0x0),
        Op.POP(0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)
        + Op.RETURN(offset=0x0, size=0x0),
        Op.POP(
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
        )
        + Op.RETURN(offset=0x0, size=0x0),
        Op.POP(
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
        )
        + Op.RETURN(offset=0x0, size=0x0),
        Op.PUSH1[0xFF]
        + Op.POP(Op.DUP1)
        + Op.POP
        + Op.RETURN(offset=0x0, size=0x0),
        Op.PUSH1[0xFF] * 2
        + Op.POP(Op.DUP2)
        + Op.POP * 2
        + Op.RETURN(offset=0x0, size=0x0),
        Op.PUSH1[0xFF] * 3
        + Op.POP(Op.DUP3)
        + Op.POP * 3
        + Op.RETURN(offset=0x0, size=0x0),
        Op.PUSH1[0xFF] * 4
        + Op.POP(Op.DUP4)
        + Op.POP * 4
        + Op.RETURN(offset=0x0, size=0x0),
        Op.PUSH1[0xFF] * 5
        + Op.POP(Op.DUP5)
        + Op.POP * 5
        + Op.RETURN(offset=0x0, size=0x0),
        Op.PUSH1[0xFF] * 6
        + Op.POP(Op.DUP6)
        + Op.POP * 6
        + Op.RETURN(offset=0x0, size=0x0),
        Op.PUSH1[0xFF] * 7
        + Op.POP(Op.DUP7)
        + Op.POP * 7
        + Op.RETURN(offset=0x0, size=0x0),
        Op.PUSH1[0xFF] * 8
        + Op.POP(Op.DUP8)
        + Op.POP * 8
        + Op.RETURN(offset=0x0, size=0x0),
        Op.PUSH1[0xFF] * 9
        + Op.POP(Op.DUP9)
        + Op.POP * 9
        + Op.RETURN(offset=0x0, size=0x0),
        Op.PUSH1[0xFF] * 10
        + Op.POP(Op.DUP10)
        + Op.POP * 10
        + Op.RETURN(offset=0x0, size=0x0),
        Op.PUSH1[0xFF] * 11
        + Op.POP(Op.DUP11)
        + Op.POP * 11
        + Op.RETURN(offset=0x0, size=0x0),
        Op.PUSH1[0xFF] * 12
        + Op.POP(Op.DUP12)
        + Op.POP * 12
        + Op.RETURN(offset=0x0, size=0x0),
        Op.PUSH1[0xFF] * 13
        + Op.POP(Op.DUP13)
        + Op.POP * 13
        + Op.RETURN(offset=0x0, size=0x0),
        Op.PUSH1[0xFF] * 14
        + Op.POP(Op.DUP14)
        + Op.POP * 14
        + Op.RETURN(offset=0x0, size=0x0),
        Op.PUSH1[0xFF] * 15
        + Op.POP(Op.DUP15)
        + Op.POP * 15
        + Op.RETURN(offset=0x0, size=0x0),
        Op.PUSH1[0xFF] * 16
        + Op.POP(Op.DUP16)
        + Op.POP * 16
        + Op.RETURN(offset=0x0, size=0x0),
        Op.PUSH1[0xFF] * 2
        + Op.SWAP1
        + Op.POP * 2
        + Op.RETURN(offset=0x0, size=0x0),
        Op.PUSH1[0xFF] * 3
        + Op.SWAP2
        + Op.POP * 3
        + Op.RETURN(offset=0x0, size=0x0),
        Op.PUSH1[0xFF] * 4
        + Op.SWAP3
        + Op.POP * 4
        + Op.RETURN(offset=0x0, size=0x0),
        Op.PUSH1[0xFF] * 5
        + Op.SWAP4
        + Op.POP * 5
        + Op.RETURN(offset=0x0, size=0x0),
        Op.PUSH1[0xFF] * 6
        + Op.SWAP5
        + Op.POP * 6
        + Op.RETURN(offset=0x0, size=0x0),
        Op.PUSH1[0xFF] * 7
        + Op.SWAP6
        + Op.POP * 7
        + Op.RETURN(offset=0x0, size=0x0),
        Op.PUSH1[0xFF] * 8
        + Op.SWAP7
        + Op.POP * 8
        + Op.RETURN(offset=0x0, size=0x0),
        Op.PUSH1[0x0]
        + Op.PUSH1[0xFF] * 8
        + Op.SWAP8
        + Op.POP * 9
        + Op.RETURN(offset=0x0, size=0x0),
        Op.PUSH1[0x0]
        + Op.PUSH1[0xFF] * 9
        + Op.SWAP9
        + Op.POP * 10
        + Op.RETURN(offset=0x0, size=0x0),
        Op.PUSH1[0x0]
        + Op.PUSH1[0xFF] * 10
        + Op.SWAP10
        + Op.POP * 11
        + Op.RETURN(offset=0x0, size=0x0),
        Op.PUSH1[0x0]
        + Op.PUSH1[0xFF] * 11
        + Op.SWAP11
        + Op.POP * 12
        + Op.RETURN(offset=0x0, size=0x0),
        Op.PUSH1[0x0]
        + Op.PUSH1[0xFF] * 12
        + Op.SWAP12
        + Op.POP * 13
        + Op.RETURN(offset=0x0, size=0x0),
        Op.PUSH1[0x0]
        + Op.PUSH1[0xFF] * 13
        + Op.SWAP13
        + Op.POP * 14
        + Op.RETURN(offset=0x0, size=0x0),
        Op.PUSH1[0x0]
        + Op.PUSH1[0xFF] * 14
        + Op.SWAP14
        + Op.POP * 15
        + Op.RETURN(offset=0x0, size=0x0),
        Op.PUSH1[0x0]
        + Op.PUSH1[0xFF] * 15
        + Op.SWAP15
        + Op.POP * 16
        + Op.RETURN(offset=0x0, size=0x0),
        Op.PUSH1[0x0]
        + Op.PUSH1[0xFF] * 16
        + Op.SWAP16
        + Op.POP * 17
        + Op.RETURN(offset=0x0, size=0x0),
        Op.LOG0(offset=0x0, size=0x0) + Op.RETURN(offset=0x0, size=0x0),
        Op.LOG1(offset=0x0, size=0x0, topic_1=0xFF)
        + Op.RETURN(offset=0x0, size=0x0),
        Op.LOG2(offset=0x0, size=0x0, topic_1=0xFF, topic_2=0xFF)
        + Op.RETURN(offset=0x0, size=0x0),
        Op.LOG3(offset=0x0, size=0x0, topic_1=0xFF, topic_2=0xFF, topic_3=0xFF)
        + Op.RETURN(offset=0x0, size=0x0),
        Op.LOG4(
            offset=0x0,
            size=0x0,
            topic_1=0xFF,
            topic_2=0xFF,
            topic_3=0xFF,
            topic_4=0xFF,
        )
        + Op.RETURN(offset=0x0, size=0x0),
        Op.POP(Op.CREATE(value=0xFF, offset=0x0, size=0x0))
        + Op.RETURN(offset=0x0, size=0x0),
        Op.POP(
            Op.CALL(
                gas=0x64,
                address=contract_1,
                value=0x17,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.RETURN(offset=0x0, size=0x0),
        Op.POP(
            Op.CALLCODE(
                gas=0x64,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.RETURN(offset=0x0, size=0x0),
        Op.RETURN(offset=0x0, size=0x0),
        Op.POP(
            Op.DELEGATECALL(
                gas=0x186A0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.RETURN(offset=0x0, size=0x0),
        Op.POP(
            Op.STATICCALL(
                gas=0x2710,
                address=contract_1,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.RETURN(offset=0x0, size=0x0),
        Op.REVERT(offset=0x0, size=0x0) + Op.RETURN(offset=0x0, size=0x0),
        Op.SELFDESTRUCT(address=Op.ORIGIN),
        Bytes("ef"),
        Op.CALL(
            gas=0xC350,
            address=contract_0,
            value=Op.DUP1,
            args_offset=Op.DUP1,
            args_size=Op.DUP1,
            ret_offset=Op.DUP1,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.POP(
            Op.CALL(
                gas=0xC350,
                address=contract_0,
                value=Op.DUP1,
                args_offset=Op.DUP1,
                args_size=Op.DUP1,
                ret_offset=Op.DUP1,
                ret_size=0x0,
            )
        )
        + Op.INVALID,
        Op.POP(
            Op.CALL(
                gas=0xC350,
                address=contract_0,
                value=Op.DUP1,
                args_offset=Op.DUP1,
                args_size=Op.DUP1,
                ret_offset=Op.DUP1,
                ret_size=0x0,
            )
        )
        + Op.MSTORE8(offset=0x0, value=0xEF)
        + Op.RETURN(offset=0x0, size=0x1),
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
