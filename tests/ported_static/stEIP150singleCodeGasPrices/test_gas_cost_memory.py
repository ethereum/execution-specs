"""
Ori Pomerantz qbzzt1@gmail.com.

Ported from:
state_tests/stEIP150singleCodeGasPrices/gasCostMemoryFiller.yml
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
    ["state_tests/stEIP150singleCodeGasPrices/gasCostMemoryFiller.yml"],
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
    ],
)
@pytest.mark.pre_alloc_mutable
def test_gas_cost_memory(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Ori Pomerantz qbzzt1@gmail."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    contract_0 = Address(0x000000000000000000000000000000000000BA5E)
    contract_1 = Address(0x000000000000000000000000000000000010BA5E)
    contract_2 = Address(0x000000000000000000000000000000000011BA5E)
    contract_3 = Address(0x095E7BAEA6A6C7C4C2DFEB977EFAC326AF552D87)
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
    #    (mstore $0 0x60A7)
    #    (mload $0)
    # }
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=Op.CALLDATALOAD(offset=0x0), value=0x60A7)
        + Op.MLOAD(offset=Op.CALLDATALOAD(offset=0x0))
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x000000000000000000000000000000000000BA5E),  # noqa: E501
    )
    # Source: lll
    # {
    #    (mstore $0 0x60A7)
    #    (mload $0)
    #    (mload $0)
    # }
    contract_1 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=Op.CALLDATALOAD(offset=0x0), value=0x60A7)
        + Op.POP(Op.MLOAD(offset=Op.CALLDATALOAD(offset=0x0)))
        + Op.MLOAD(offset=Op.CALLDATALOAD(offset=0x0))
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x000000000000000000000000000000000010BA5E),  # noqa: E501
    )
    # Source: lll
    # {
    #    (mstore $0 0x60A7)
    #    (mload $0)
    #    (mstore $0 0x60A7)
    # }
    contract_2 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=Op.CALLDATALOAD(offset=0x0), value=0x60A7)
        + Op.POP(Op.MLOAD(offset=Op.CALLDATALOAD(offset=0x0)))
        + Op.MSTORE(offset=Op.CALLDATALOAD(offset=0x0), value=0x60A7)
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x000000000000000000000000000000000011BA5E),  # noqa: E501
    )
    # Source: lll
    # {
    #   ;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
    #   ; Initialization
    #
    #   ; Variables (0x20 byte wide)
    #   (def 'action            0x000)  ; Action to take with the memory
    #   (def 'addr              0x020)  ; Address to read / write
    #   (def 'expectedCost      0x040)  ; Expected gas cost
    #   (def 'gasB4             0x060)  ; Before the action being measured
    #   (def 'gasAfter          0x080)  ; After the action being measured
    #
    #   ; Gas cost for a baseline operation (call a contract that does mstore
    #   ; and then mload)
    #   (def 'gasBaseline       0x0A0)
    #
    #   ; Gas for for the action intself (call a contract plus <whatever>)
    #   (def 'gasAction         0x0C0)
    #
    #   ; Temporary values
    #   (def 'temp              0x0E0)
    #
    #   ; Understand CALLDATA. It is four bytes of function
    #   ; selector (irrelevant) followed by 32 byte words
    #   ; of the parameters
    #   [action]        $4
    #   [addr]          $36
    #   [expectedCost]  $68
    #
    #   ; Constants
    #   (def  'NOP    0) ; No operation (for if statements)
    # ... (103 more lines)
    contract_3 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x0, value=Op.CALLDATALOAD(offset=0x4))
        + Op.MSTORE(offset=0x20, value=Op.CALLDATALOAD(offset=0x24))
        + Op.MSTORE(offset=0x40, value=Op.CALLDATALOAD(offset=0x44))
        + Op.JUMPI(
            pc=Op.PUSH2[0x23], condition=Op.EQ(Op.MLOAD(offset=0x0), 0x0)
        )
        + Op.POP(0x0)
        + Op.JUMP(pc=Op.PUSH2[0x31])
        + Op.JUMPDEST
        + Op.MSTORE(offset=0x60, value=Op.GAS)
        + Op.POP(Op.MLOAD(offset=Op.MLOAD(offset=0x20)))
        + Op.MSTORE(offset=0x80, value=Op.GAS)
        + Op.JUMPDEST
        + Op.JUMPI(
            pc=Op.PUSH2[0x43], condition=Op.EQ(Op.MLOAD(offset=0x0), 0x1)
        )
        + Op.POP(0x0)
        + Op.JUMP(pc=Op.PUSH2[0x53])
        + Op.JUMPDEST
        + Op.MSTORE(offset=0x60, value=Op.GAS)
        + Op.MSTORE(offset=Op.MLOAD(offset=0x20), value=0x60A7)
        + Op.MSTORE(offset=0x80, value=Op.GAS)
        + Op.JUMPDEST
        + Op.JUMPI(
            pc=Op.PUSH2[0x65], condition=Op.EQ(Op.MLOAD(offset=0x0), 0x2)
        )
        + Op.POP(0x0)
        + Op.JUMP(pc=Op.PUSH2[0x74])
        + Op.JUMPDEST
        + Op.MSTORE(offset=0x60, value=Op.GAS)
        + Op.MSTORE8(offset=Op.MLOAD(offset=0x20), value=0xFF)
        + Op.MSTORE(offset=0x80, value=Op.GAS)
        + Op.JUMPDEST
        + Op.JUMPI(
            pc=Op.PUSH2[0x86], condition=Op.EQ(Op.MLOAD(offset=0x0), 0x3)
        )
        + Op.POP(0x0)
        + Op.JUMP(pc=Op.PUSH2[0xAC])
        + Op.JUMPDEST
        + Op.MSTORE(offset=0x60, value=Op.GAS)
        + Op.POP(
            Op.CALL(
                gas=0x10000,
                address=0xBA5E,
                value=0x0,
                args_offset=0x20,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.MSTORE(offset=0x80, value=Op.GAS)
        + Op.MSTORE(
            offset=0xA0,
            value=Op.SUB(Op.MLOAD(offset=0x60), Op.MLOAD(offset=0x80)),
        )
        + Op.JUMPDEST
        + Op.JUMPI(
            pc=Op.PUSH2[0xBE], condition=Op.EQ(Op.MLOAD(offset=0x0), 0x10)
        )
        + Op.POP(0x0)
        + Op.JUMP(pc=0x10A)
        + Op.JUMPDEST
        + Op.MSTORE(offset=0x60, value=Op.GAS)
        + Op.POP(
            Op.CALL(
                gas=0x10000,
                address=0xBA5E,
                value=0x0,
                args_offset=0x20,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.MSTORE(offset=0x80, value=Op.GAS)
        + Op.MSTORE(
            offset=0xA0,
            value=Op.SUB(Op.MLOAD(offset=0x60), Op.MLOAD(offset=0x80)),
        )
        + Op.MSTORE(offset=0x60, value=Op.GAS)
        + Op.POP(
            Op.CALL(
                gas=0x10000,
                address=0x10BA5E,
                value=0x0,
                args_offset=0x20,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.MSTORE(offset=0x80, value=Op.GAS)
        + Op.MSTORE(
            offset=0xC0,
            value=Op.SUB(Op.MLOAD(offset=0x60), Op.MLOAD(offset=0x80)),
        )
        + Op.JUMPDEST
        + Op.JUMPI(pc=0x11C, condition=Op.EQ(Op.MLOAD(offset=0x0), 0x11))
        + Op.POP(0x0)
        + Op.JUMP(pc=0x168)
        + Op.JUMPDEST
        + Op.MSTORE(offset=0x60, value=Op.GAS)
        + Op.POP(
            Op.CALL(
                gas=0x10000,
                address=0xBA5E,
                value=0x0,
                args_offset=0x20,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.MSTORE(offset=0x80, value=Op.GAS)
        + Op.MSTORE(
            offset=0xA0,
            value=Op.SUB(Op.MLOAD(offset=0x60), Op.MLOAD(offset=0x80)),
        )
        + Op.MSTORE(offset=0x60, value=Op.GAS)
        + Op.POP(
            Op.CALL(
                gas=0x10000,
                address=0x11BA5E,
                value=0x0,
                args_offset=0x20,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.MSTORE(offset=0x80, value=Op.GAS)
        + Op.MSTORE(
            offset=0xC0,
            value=Op.SUB(Op.MLOAD(offset=0x60), Op.MLOAD(offset=0x80)),
        )
        + Op.JUMPDEST
        + Op.JUMPI(
            pc=0x17B, condition=Op.ISZERO(Op.GT(Op.MLOAD(offset=0x0), 0x2))
        )
        + Op.POP(0x0)
        + Op.JUMP(pc=0x18A)
        + Op.JUMPDEST
        + Op.SSTORE(
            key=0x0,
            value=Op.SUB(
                Op.SUB(Op.MLOAD(offset=0x60), Op.MLOAD(offset=0x80)),
                Op.MLOAD(offset=0x40),
            ),
        )
        + Op.JUMPDEST
        + Op.JUMPI(pc=0x19C, condition=Op.EQ(Op.MLOAD(offset=0x0), 0x3))
        + Op.POP(0x0)
        + Op.JUMP(pc=0x1A7)
        + Op.JUMPDEST
        + Op.SSTORE(
            key=0x0, value=Op.SUB(Op.MLOAD(offset=0xA0), Op.MLOAD(offset=0x40))
        )
        + Op.JUMPDEST
        + Op.JUMPI(
            pc=0x1BC, condition=Op.EQ(0x10, Op.AND(Op.MLOAD(offset=0x0), 0xF0))
        )
        + Op.POP(0x0)
        + Op.JUMP(pc=0x1CB)
        + Op.JUMPDEST
        + Op.SSTORE(
            key=0x0,
            value=Op.SUB(
                Op.SUB(Op.MLOAD(offset=0xC0), Op.MLOAD(offset=0xA0)),
                Op.MLOAD(offset=0x40),
            ),
        )
        + Op.JUMPDEST
        + Op.STOP,
        storage={0: 24743},
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x095E7BAEA6A6C7C4C2DFEB977EFAC326AF552D87),  # noqa: E501
    )
    pre[sender] = Account(balance=0xBA1A9CE0BA1A9CE)

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
                    33,
                    34,
                    35,
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
                ],
                "gas": -1,
                "value": -1,
            },
            "network": [">=Cancun"],
            "result": {contract_3: Account(storage={0: 0})},
        },
        {
            "indexes": {
                "data": [36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48],
                "gas": -1,
                "value": -1,
            },
            "network": [">=Cancun"],
            "result": {contract_3: Account(storage={0: 1900})},
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx_data = [
        Bytes("d086d23d") + Hash(0x0) + Hash(0x100) + Hash(0x25),
        Bytes("d086d23d") + Hash(0x0) + Hash(0x120) + Hash(0x28),
        Bytes("d086d23d") + Hash(0x0) + Hash(0x140) + Hash(0x2B),
        Bytes("d086d23d") + Hash(0x0) + Hash(0x160) + Hash(0x2E),
        Bytes("d086d23d") + Hash(0x0) + Hash(0x180) + Hash(0x31),
        Bytes("d086d23d") + Hash(0x0) + Hash(0x200) + Hash(0x3D),
        Bytes("d086d23d") + Hash(0x0) + Hash(0x300) + Hash(0x56),
        Bytes("d086d23d") + Hash(0x0) + Hash(0x400) + Hash(0x6F),
        Bytes("d086d23d") + Hash(0x0) + Hash(0x800) + Hash(0xD5),
        Bytes("d086d23d") + Hash(0x0) + Hash(0x1000) + Hash(0x1AD),
        Bytes("d086d23d") + Hash(0x0) + Hash(0x2000) + Hash(0x38E),
        Bytes("d086d23d") + Hash(0x0) + Hash(0x3000) + Hash(0x5AE),
        Bytes("d086d23d") + Hash(0x1) + Hash(0x100) + Hash(0x26),
        Bytes("d086d23d") + Hash(0x1) + Hash(0x120) + Hash(0x29),
        Bytes("d086d23d") + Hash(0x1) + Hash(0x140) + Hash(0x2C),
        Bytes("d086d23d") + Hash(0x1) + Hash(0x160) + Hash(0x2F),
        Bytes("d086d23d") + Hash(0x1) + Hash(0x180) + Hash(0x32),
        Bytes("d086d23d") + Hash(0x1) + Hash(0x200) + Hash(0x3E),
        Bytes("d086d23d") + Hash(0x1) + Hash(0x300) + Hash(0x57),
        Bytes("d086d23d") + Hash(0x1) + Hash(0x400) + Hash(0x70),
        Bytes("d086d23d") + Hash(0x1) + Hash(0x800) + Hash(0xD6),
        Bytes("d086d23d") + Hash(0x1) + Hash(0x1000) + Hash(0x1AE),
        Bytes("d086d23d") + Hash(0x1) + Hash(0x2000) + Hash(0x38F),
        Bytes("d086d23d") + Hash(0x1) + Hash(0x3000) + Hash(0x5AF),
        Bytes("d086d23d") + Hash(0x2) + Hash(0x100) + Hash(0x26),
        Bytes("d086d23d") + Hash(0x2) + Hash(0x120) + Hash(0x29),
        Bytes("d086d23d") + Hash(0x2) + Hash(0x140) + Hash(0x2C),
        Bytes("d086d23d") + Hash(0x2) + Hash(0x160) + Hash(0x2F),
        Bytes("d086d23d") + Hash(0x2) + Hash(0x180) + Hash(0x32),
        Bytes("d086d23d") + Hash(0x2) + Hash(0x200) + Hash(0x3E),
        Bytes("d086d23d") + Hash(0x2) + Hash(0x300) + Hash(0x57),
        Bytes("d086d23d") + Hash(0x2) + Hash(0x400) + Hash(0x70),
        Bytes("d086d23d") + Hash(0x2) + Hash(0x800) + Hash(0xD6),
        Bytes("d086d23d") + Hash(0x2) + Hash(0x1000) + Hash(0x1AE),
        Bytes("d086d23d") + Hash(0x2) + Hash(0x2000) + Hash(0x38F),
        Bytes("d086d23d") + Hash(0x2) + Hash(0x3000) + Hash(0x5AF),
        Bytes("d086d23d") + Hash(0x3) + Hash(0x0) + Hash(0x2F6),
        Bytes("d086d23d") + Hash(0x3) + Hash(0x20) + Hash(0x2F9),
        Bytes("d086d23d") + Hash(0x3) + Hash(0x40) + Hash(0x2FC),
        Bytes("d086d23d") + Hash(0x3) + Hash(0x60) + Hash(0x2FF),
        Bytes("d086d23d") + Hash(0x3) + Hash(0x80) + Hash(0x302),
        Bytes("d086d23d") + Hash(0x3) + Hash(0x100) + Hash(0x30E),
        Bytes("d086d23d") + Hash(0x3) + Hash(0x200) + Hash(0x326),
        Bytes("d086d23d") + Hash(0x3) + Hash(0x400) + Hash(0x358),
        Bytes("d086d23d") + Hash(0x3) + Hash(0x800) + Hash(0x3BE),
        Bytes("d086d23d") + Hash(0x3) + Hash(0x1000) + Hash(0x496),
        Bytes("d086d23d") + Hash(0x3) + Hash(0x2000) + Hash(0x677),
        Bytes("d086d23d") + Hash(0x3) + Hash(0x4000) + Hash(0xAF8),
        Bytes("d086d23d") + Hash(0x3) + Hash(0x8000) + Hash(0x16FA),
        Bytes("d086d23d") + Hash(0x10) + Hash(0x0) + Hash(0x8),
        Bytes("d086d23d") + Hash(0x10) + Hash(0x10) + Hash(0x8),
        Bytes("d086d23d") + Hash(0x10) + Hash(0x20) + Hash(0x8),
        Bytes("d086d23d") + Hash(0x10) + Hash(0x40) + Hash(0x8),
        Bytes("d086d23d") + Hash(0x10) + Hash(0x80) + Hash(0x8),
        Bytes("d086d23d") + Hash(0x10) + Hash(0x100) + Hash(0x8),
        Bytes("d086d23d") + Hash(0x10) + Hash(0x200) + Hash(0x8),
        Bytes("d086d23d") + Hash(0x10) + Hash(0x400) + Hash(0x8),
        Bytes("d086d23d") + Hash(0x10) + Hash(0x800) + Hash(0x8),
        Bytes("d086d23d") + Hash(0x10) + Hash(0x1000) + Hash(0x8),
        Bytes("d086d23d") + Hash(0x10) + Hash(0x2000) + Hash(0x8),
        Bytes("d086d23d") + Hash(0x10) + Hash(0x4000) + Hash(0x8),
        Bytes("d086d23d") + Hash(0x10) + Hash(0x8000) + Hash(0x8),
        Bytes("d086d23d") + Hash(0x11) + Hash(0x0) + Hash(0xB),
        Bytes("d086d23d") + Hash(0x11) + Hash(0x10) + Hash(0xB),
        Bytes("d086d23d") + Hash(0x11) + Hash(0x20) + Hash(0xB),
        Bytes("d086d23d") + Hash(0x11) + Hash(0x40) + Hash(0xB),
        Bytes("d086d23d") + Hash(0x11) + Hash(0x80) + Hash(0xB),
        Bytes("d086d23d") + Hash(0x11) + Hash(0x100) + Hash(0xB),
        Bytes("d086d23d") + Hash(0x11) + Hash(0x200) + Hash(0xB),
        Bytes("d086d23d") + Hash(0x11) + Hash(0x400) + Hash(0xB),
        Bytes("d086d23d") + Hash(0x11) + Hash(0x800) + Hash(0xB),
        Bytes("d086d23d") + Hash(0x11) + Hash(0x1000) + Hash(0xB),
        Bytes("d086d23d") + Hash(0x11) + Hash(0x2000) + Hash(0xB),
        Bytes("d086d23d") + Hash(0x11) + Hash(0x4000) + Hash(0xB),
        Bytes("d086d23d") + Hash(0x11) + Hash(0x8000) + Hash(0xB),
    ]
    tx_gas = [16777216]
    tx_value = [1]

    tx = Transaction(
        sender=sender,
        to=contract_3,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        value=tx_value[v],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
