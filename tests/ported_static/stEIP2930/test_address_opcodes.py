"""
Ori Pomerantz qbzzt1@gmail.com.

Ported from:
state_tests/stEIP2930/addressOpcodesFiller.yml
"""

import pytest
from execution_testing import (
    EOA,
    AccessList,
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
    ["state_tests/stEIP2930/addressOpcodesFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0,
            0,
            0,
            id="valid",
        ),
        pytest.param(
            1,
            0,
            0,
            id="valid",
        ),
        pytest.param(
            2,
            0,
            0,
            id="invalid",
        ),
        pytest.param(
            3,
            0,
            0,
            id="invalid",
        ),
        pytest.param(
            4,
            0,
            0,
            id="valid",
        ),
        pytest.param(
            5,
            0,
            0,
            id="valid",
        ),
        pytest.param(
            6,
            0,
            0,
            id="valid",
        ),
        pytest.param(
            7,
            0,
            0,
            id="valid",
        ),
        pytest.param(
            8,
            0,
            0,
            id="valid",
        ),
        pytest.param(
            9,
            0,
            0,
            id="valid",
        ),
        pytest.param(
            10,
            0,
            0,
            id="valid",
        ),
        pytest.param(
            11,
            0,
            0,
            id="valid",
        ),
        pytest.param(
            12,
            0,
            0,
            id="valid",
        ),
        pytest.param(
            13,
            0,
            0,
            id="valid",
        ),
        pytest.param(
            14,
            0,
            0,
            id="invalid",
        ),
        pytest.param(
            15,
            0,
            0,
            id="invalid",
        ),
        pytest.param(
            16,
            0,
            0,
            id="valid",
        ),
        pytest.param(
            17,
            0,
            0,
            id="valid",
        ),
        pytest.param(
            18,
            0,
            0,
            id="valid",
        ),
        pytest.param(
            19,
            0,
            0,
            id="valid",
        ),
        pytest.param(
            20,
            0,
            0,
            id="valid",
        ),
        pytest.param(
            21,
            0,
            0,
            id="valid",
        ),
        pytest.param(
            22,
            0,
            0,
            id="valid",
        ),
        pytest.param(
            23,
            0,
            0,
            id="valid",
        ),
        pytest.param(
            24,
            0,
            0,
            id="valid",
        ),
        pytest.param(
            25,
            0,
            0,
            id="valid",
        ),
        pytest.param(
            26,
            0,
            0,
            id="invalid",
        ),
        pytest.param(
            27,
            0,
            0,
            id="invalid",
        ),
        pytest.param(
            28,
            0,
            0,
            id="valid",
        ),
        pytest.param(
            29,
            0,
            0,
            id="valid",
        ),
        pytest.param(
            30,
            0,
            0,
            id="valid",
        ),
        pytest.param(
            31,
            0,
            0,
            id="valid",
        ),
        pytest.param(
            32,
            0,
            0,
            id="valid",
        ),
        pytest.param(
            33,
            0,
            0,
            id="valid",
        ),
        pytest.param(
            34,
            0,
            0,
            id="valid",
        ),
        pytest.param(
            35,
            0,
            0,
            id="valid",
        ),
        pytest.param(
            36,
            0,
            0,
            id="valid",
        ),
        pytest.param(
            37,
            0,
            0,
            id="valid",
        ),
        pytest.param(
            38,
            0,
            0,
            id="invalid",
        ),
        pytest.param(
            39,
            0,
            0,
            id="invalid",
        ),
        pytest.param(
            40,
            0,
            0,
            id="valid",
        ),
        pytest.param(
            41,
            0,
            0,
            id="valid",
        ),
        pytest.param(
            42,
            0,
            0,
            id="valid",
        ),
        pytest.param(
            43,
            0,
            0,
            id="valid",
        ),
        pytest.param(
            44,
            0,
            0,
            id="valid",
        ),
        pytest.param(
            45,
            0,
            0,
            id="valid",
        ),
        pytest.param(
            46,
            0,
            0,
            id="valid",
        ),
        pytest.param(
            47,
            0,
            0,
            id="valid",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_address_opcodes(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Ori Pomerantz qbzzt1@gmail."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    contract_0 = Address(0x0000000000000000000000000000000000001000)
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
    )

    # Source: lll
    # {
    #    (def 'acctType  $0)   ; type of account we handle
    #    (def 'opcode $0x20)   ; the opcode we are dealing with
    #
    #    (def 'acct 0x20)
    #
    #    (def 'NOP 0)
    #
    #
    #    ; the type of account we handle
    #
    #    ; unrelated account
    #    (if (= acctType 0) [acct] 0x1001 NOP)
    #
    #    ; transaction sender
    #    (if (= acctType 1) [acct] (origin) NOP)
    #
    #    ; the contract that called us
    #    (if (= acctType 2) [acct] (caller) NOP)
    #
    #    ; our own contract
    #    (if (= acctType 3) [acct] (address) NOP)
    #
    #    ; a precompile
    #    (if (= acctType 4) [acct] 0x0001 NOP)
    #
    #
    #    [0] @0    ; Just to disable the first use of memory cost
    #
    #    (if (= opcode 0) {
    # ... (47 more lines)
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=Op.JUMPI(
            pc=Op.PUSH2[0x11],
            condition=Op.EQ(Op.CALLDATALOAD(offset=0x0), 0x0),
        )
        + Op.POP(0x0)
        + Op.JUMP(pc=Op.PUSH2[0x18])
        + Op.JUMPDEST
        + Op.MSTORE(offset=0x20, value=0x1001)
        + Op.JUMPDEST
        + Op.JUMPI(
            pc=Op.PUSH2[0x2A],
            condition=Op.EQ(Op.CALLDATALOAD(offset=0x0), 0x1),
        )
        + Op.POP(0x0)
        + Op.JUMP(pc=Op.PUSH2[0x2F])
        + Op.JUMPDEST
        + Op.MSTORE(offset=0x20, value=Op.ORIGIN)
        + Op.JUMPDEST
        + Op.JUMPI(
            pc=Op.PUSH2[0x41],
            condition=Op.EQ(Op.CALLDATALOAD(offset=0x0), 0x2),
        )
        + Op.POP(0x0)
        + Op.JUMP(pc=Op.PUSH2[0x46])
        + Op.JUMPDEST
        + Op.MSTORE(offset=0x20, value=Op.CALLER)
        + Op.JUMPDEST
        + Op.JUMPI(
            pc=Op.PUSH2[0x58],
            condition=Op.EQ(Op.CALLDATALOAD(offset=0x0), 0x3),
        )
        + Op.POP(0x0)
        + Op.JUMP(pc=Op.PUSH2[0x5D])
        + Op.JUMPDEST
        + Op.MSTORE(offset=0x20, value=Op.ADDRESS)
        + Op.JUMPDEST
        + Op.JUMPI(
            pc=Op.PUSH2[0x6F],
            condition=Op.EQ(Op.CALLDATALOAD(offset=0x0), 0x4),
        )
        + Op.POP(0x0)
        + Op.JUMP(pc=Op.PUSH2[0x75])
        + Op.JUMPDEST
        + Op.MSTORE(offset=0x20, value=0x1)
        + Op.JUMPDEST
        + Op.MSTORE(offset=0x0, value=Op.MLOAD(offset=0x0))
        + Op.JUMPI(
            pc=Op.PUSH2[0x8D],
            condition=Op.EQ(Op.CALLDATALOAD(offset=0x20), 0x0),
        )
        + Op.POP(0x0)
        + Op.JUMP(pc=Op.PUSH2[0xB6])
        + Op.JUMPDEST
        + Op.MSTORE(offset=0x0, value=Op.GAS)
        + Op.POP(Op.BALANCE(address=Op.MLOAD(offset=0x20)))
        + Op.SSTORE(
            key=0x0, value=Op.SUB(Op.SUB(Op.MLOAD(offset=0x0), Op.GAS), 0x16)
        )
        + Op.MSTORE(offset=0x0, value=Op.GAS)
        + Op.POP(Op.BALANCE(address=Op.MLOAD(offset=0x20)))
        + Op.SSTORE(
            key=0x1, value=Op.SUB(Op.SUB(Op.MLOAD(offset=0x0), Op.GAS), 0x16)
        )
        + Op.JUMPDEST
        + Op.JUMPI(
            pc=Op.PUSH2[0xC8],
            condition=Op.EQ(Op.CALLDATALOAD(offset=0x20), 0x1),
        )
        + Op.POP(0x0)
        + Op.JUMP(pc=Op.PUSH2[0xF1])
        + Op.JUMPDEST
        + Op.MSTORE(offset=0x0, value=Op.GAS)
        + Op.POP(Op.EXTCODESIZE(address=Op.MLOAD(offset=0x20)))
        + Op.SSTORE(
            key=0x0, value=Op.SUB(Op.SUB(Op.MLOAD(offset=0x0), Op.GAS), 0x16)
        )
        + Op.MSTORE(offset=0x0, value=Op.GAS)
        + Op.POP(Op.EXTCODESIZE(address=Op.MLOAD(offset=0x20)))
        + Op.SSTORE(
            key=0x1, value=Op.SUB(Op.SUB(Op.MLOAD(offset=0x0), Op.GAS), 0x16)
        )
        + Op.JUMPDEST
        + Op.JUMPI(
            pc=0x103, condition=Op.EQ(Op.CALLDATALOAD(offset=0x20), 0x2)
        )
        + Op.POP(0x0)
        + Op.JUMP(pc=0x12C)
        + Op.JUMPDEST
        + Op.MSTORE(offset=0x0, value=Op.GAS)
        + Op.POP(Op.EXTCODEHASH(address=Op.MLOAD(offset=0x20)))
        + Op.SSTORE(
            key=0x0, value=Op.SUB(Op.SUB(Op.MLOAD(offset=0x0), Op.GAS), 0x16)
        )
        + Op.MSTORE(offset=0x0, value=Op.GAS)
        + Op.POP(Op.EXTCODEHASH(address=Op.MLOAD(offset=0x20)))
        + Op.SSTORE(
            key=0x1, value=Op.SUB(Op.SUB(Op.MLOAD(offset=0x0), Op.GAS), 0x16)
        )
        + Op.JUMPDEST
        + Op.JUMPI(
            pc=0x13E, condition=Op.EQ(Op.CALLDATALOAD(offset=0x20), 0x3)
        )
        + Op.POP(0x0)
        + Op.JUMP(pc=0x17A)
        + Op.JUMPDEST
        + Op.MSTORE(offset=0x100, value=0x6A5)
        + Op.MSTORE(offset=0x0, value=Op.GAS)
        + Op.EXTCODECOPY(
            address=Op.MLOAD(offset=0x20),
            dest_offset=0x100,
            offset=0x0,
            size=0x20,
        )
        + Op.SSTORE(
            key=0x0, value=Op.SUB(Op.SUB(Op.MLOAD(offset=0x0), Op.GAS), 0x20)
        )
        + Op.MSTORE(offset=0x0, value=Op.GAS)
        + Op.EXTCODECOPY(
            address=Op.MLOAD(offset=0x20),
            dest_offset=0x100,
            offset=0x0,
            size=0x20,
        )
        + Op.SSTORE(
            key=0x1, value=Op.SUB(Op.SUB(Op.MLOAD(offset=0x0), Op.GAS), 0x20)
        )
        + Op.JUMPDEST
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address(0x0000000000000000000000000000000000001000),  # noqa: E501
    )
    # Source: lll
    # {
    #     ; relay the parameters
    #     [0x100] $4
    #     [0x120] $36
    #     (call (gas) 0x1000 0 0x100 0x40 0 0x40)
    #
    #     ; Write the returned results, if any
    #     [[0]] @0x00
    #     [[1]] @0x20
    # }
    contract_1 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x100, value=Op.CALLDATALOAD(offset=0x4))
        + Op.MSTORE(offset=0x120, value=Op.CALLDATALOAD(offset=0x24))
        + Op.POP(
            Op.CALL(
                gas=Op.GAS,
                address=0x1000,
                value=0x0,
                args_offset=0x100,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x40,
            )
        )
        + Op.SSTORE(key=0x0, value=Op.MLOAD(offset=0x0))
        + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x20))
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0xCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    expect_entries_: list[dict] = [
        {
            "indexes": {
                "data": [
                    0,
                    1,
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
                    28,
                    29,
                    30,
                    31,
                    32,
                    33,
                    34,
                    35,
                    36,
                    37,
                    40,
                    41,
                    42,
                    43,
                    44,
                    45,
                    46,
                    47,
                ],
                "gas": -1,
                "value": -1,
            },
            "network": [">=Cancun"],
            "result": {contract_0: Account(storage={0: 97, 1: 97})},
        },
        {
            "indexes": {
                "data": [2, 3, 14, 15, 26, 27, 38, 39],
                "gas": -1,
                "value": -1,
            },
            "network": [">=Cancun"],
            "result": {contract_0: Account(storage={0: 2597, 1: 97, 2: 0})},
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx_data = [
        Bytes("1a8451e6") + Hash(0x0) + Hash(0x0),
        Bytes("1a8451e6") + Hash(0x0) + Hash(0x0),
        Bytes("1a8451e6") + Hash(0x0) + Hash(0x0),
        Bytes("1a8451e6") + Hash(0x0) + Hash(0x0),
        Bytes("1a8451e6") + Hash(0x1) + Hash(0x0),
        Bytes("1a8451e6") + Hash(0x1) + Hash(0x0),
        Bytes("1a8451e6") + Hash(0x2) + Hash(0x0),
        Bytes("1a8451e6") + Hash(0x2) + Hash(0x0),
        Bytes("1a8451e6") + Hash(0x3) + Hash(0x0),
        Bytes("1a8451e6") + Hash(0x3) + Hash(0x0),
        Bytes("1a8451e6") + Hash(0x4) + Hash(0x0),
        Bytes("1a8451e6") + Hash(0x4) + Hash(0x0),
        Bytes("1a8451e6") + Hash(0x0) + Hash(0x1),
        Bytes("1a8451e6") + Hash(0x0) + Hash(0x1),
        Bytes("1a8451e6") + Hash(0x0) + Hash(0x1),
        Bytes("1a8451e6") + Hash(0x0) + Hash(0x1),
        Bytes("1a8451e6") + Hash(0x1) + Hash(0x1),
        Bytes("1a8451e6") + Hash(0x1) + Hash(0x1),
        Bytes("1a8451e6") + Hash(0x2) + Hash(0x1),
        Bytes("1a8451e6") + Hash(0x2) + Hash(0x1),
        Bytes("1a8451e6") + Hash(0x3) + Hash(0x1),
        Bytes("1a8451e6") + Hash(0x3) + Hash(0x1),
        Bytes("1a8451e6") + Hash(0x4) + Hash(0x1),
        Bytes("1a8451e6") + Hash(0x4) + Hash(0x1),
        Bytes("1a8451e6") + Hash(0x0) + Hash(0x2),
        Bytes("1a8451e6") + Hash(0x0) + Hash(0x2),
        Bytes("1a8451e6") + Hash(0x0) + Hash(0x2),
        Bytes("1a8451e6") + Hash(0x0) + Hash(0x2),
        Bytes("1a8451e6") + Hash(0x1) + Hash(0x2),
        Bytes("1a8451e6") + Hash(0x1) + Hash(0x2),
        Bytes("1a8451e6") + Hash(0x2) + Hash(0x2),
        Bytes("1a8451e6") + Hash(0x2) + Hash(0x2),
        Bytes("1a8451e6") + Hash(0x3) + Hash(0x2),
        Bytes("1a8451e6") + Hash(0x3) + Hash(0x2),
        Bytes("1a8451e6") + Hash(0x4) + Hash(0x2),
        Bytes("1a8451e6") + Hash(0x4) + Hash(0x2),
        Bytes("1a8451e6") + Hash(0x0) + Hash(0x3),
        Bytes("1a8451e6") + Hash(0x0) + Hash(0x3),
        Bytes("1a8451e6") + Hash(0x0) + Hash(0x3),
        Bytes("1a8451e6") + Hash(0x0) + Hash(0x3),
        Bytes("1a8451e6") + Hash(0x1) + Hash(0x3),
        Bytes("1a8451e6") + Hash(0x1) + Hash(0x3),
        Bytes("1a8451e6") + Hash(0x2) + Hash(0x3),
        Bytes("1a8451e6") + Hash(0x2) + Hash(0x3),
        Bytes("1a8451e6") + Hash(0x3) + Hash(0x3),
        Bytes("1a8451e6") + Hash(0x3) + Hash(0x3),
        Bytes("1a8451e6") + Hash(0x4) + Hash(0x3),
        Bytes("1a8451e6") + Hash(0x4) + Hash(0x3),
    ]
    tx_gas = [16777216]
    tx_value = [100000]
    tx_access_lists: dict[int, list] = {
        0: [
            AccessList(
                address=Address(0x0000000000000000000000000000000000001001),
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                    ),  # noqa: E501
                    Hash(
                        "0x00000000000000000000000000000000000000000000000000000000000060a7"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
        ],
        1: [
            AccessList(
                address=Address(0x0000000000000000000000000000000000001001),
                storage_keys=[],
            ),
        ],
        2: [],
        3: [
            AccessList(
                address=Address(0xF00000000000000000000000000000000000F101),
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                    ),  # noqa: E501
                    Hash(
                        "0x00000000000000000000000000000000000000000000000000000000000060a7"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
        ],
        4: [
            AccessList(
                address=Address(0xA94F5374FCE5EDBC8E2A8697C15331677E6EBF0B),
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                    ),  # noqa: E501
                    Hash(
                        "0x00000000000000000000000000000000000000000000000000000000000060a7"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
        ],
        5: [],
        6: [
            AccessList(
                address=Address(0xCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC),
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                    ),  # noqa: E501
                    Hash(
                        "0x00000000000000000000000000000000000000000000000000000000000060a7"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
        ],
        7: [],
        8: [
            AccessList(
                address=Address(0x0000000000000000000000000000000000001000),
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                    ),  # noqa: E501
                    Hash(
                        "0x00000000000000000000000000000000000000000000000000000000000060a7"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
        ],
        9: [],
        10: [
            AccessList(
                address=Address(0x0000000000000000000000000000000000000001),
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                    ),  # noqa: E501
                    Hash(
                        "0x00000000000000000000000000000000000000000000000000000000000060a7"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
        ],
        11: [],
        12: [
            AccessList(
                address=Address(0x0000000000000000000000000000000000001001),
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                    ),  # noqa: E501
                    Hash(
                        "0x00000000000000000000000000000000000000000000000000000000000060a7"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
        ],
        13: [
            AccessList(
                address=Address(0x0000000000000000000000000000000000001001),
                storage_keys=[],
            ),
        ],
        14: [],
        15: [
            AccessList(
                address=Address(0xF00000000000000000000000000000000000F101),
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                    ),  # noqa: E501
                    Hash(
                        "0x00000000000000000000000000000000000000000000000000000000000060a7"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
        ],
        16: [
            AccessList(
                address=Address(0xA94F5374FCE5EDBC8E2A8697C15331677E6EBF0B),
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                    ),  # noqa: E501
                    Hash(
                        "0x00000000000000000000000000000000000000000000000000000000000060a7"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
        ],
        17: [],
        18: [
            AccessList(
                address=Address(0xCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC),
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                    ),  # noqa: E501
                    Hash(
                        "0x00000000000000000000000000000000000000000000000000000000000060a7"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
        ],
        19: [],
        20: [
            AccessList(
                address=Address(0x0000000000000000000000000000000000001000),
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                    ),  # noqa: E501
                    Hash(
                        "0x00000000000000000000000000000000000000000000000000000000000060a7"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
        ],
        21: [],
        22: [
            AccessList(
                address=Address(0x0000000000000000000000000000000000000001),
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                    ),  # noqa: E501
                    Hash(
                        "0x00000000000000000000000000000000000000000000000000000000000060a7"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
        ],
        23: [],
        24: [
            AccessList(
                address=Address(0x0000000000000000000000000000000000001001),
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                    ),  # noqa: E501
                    Hash(
                        "0x00000000000000000000000000000000000000000000000000000000000060a7"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
        ],
        25: [
            AccessList(
                address=Address(0x0000000000000000000000000000000000001001),
                storage_keys=[],
            ),
        ],
        26: [],
        27: [
            AccessList(
                address=Address(0xF00000000000000000000000000000000000F101),
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                    ),  # noqa: E501
                    Hash(
                        "0x00000000000000000000000000000000000000000000000000000000000060a7"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
        ],
        28: [
            AccessList(
                address=Address(0xA94F5374FCE5EDBC8E2A8697C15331677E6EBF0B),
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                    ),  # noqa: E501
                    Hash(
                        "0x00000000000000000000000000000000000000000000000000000000000060a7"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
        ],
        29: [],
        30: [
            AccessList(
                address=Address(0xCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC),
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                    ),  # noqa: E501
                    Hash(
                        "0x00000000000000000000000000000000000000000000000000000000000060a7"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
        ],
        31: [],
        32: [
            AccessList(
                address=Address(0x0000000000000000000000000000000000001000),
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                    ),  # noqa: E501
                    Hash(
                        "0x00000000000000000000000000000000000000000000000000000000000060a7"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
        ],
        33: [],
        34: [
            AccessList(
                address=Address(0x0000000000000000000000000000000000000001),
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                    ),  # noqa: E501
                    Hash(
                        "0x00000000000000000000000000000000000000000000000000000000000060a7"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
        ],
        35: [],
        36: [
            AccessList(
                address=Address(0x0000000000000000000000000000000000001001),
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                    ),  # noqa: E501
                    Hash(
                        "0x00000000000000000000000000000000000000000000000000000000000060a7"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
        ],
        37: [
            AccessList(
                address=Address(0x0000000000000000000000000000000000001001),
                storage_keys=[],
            ),
        ],
        38: [],
        39: [
            AccessList(
                address=Address(0xF00000000000000000000000000000000000F101),
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                    ),  # noqa: E501
                    Hash(
                        "0x00000000000000000000000000000000000000000000000000000000000060a7"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
        ],
        40: [
            AccessList(
                address=Address(0xA94F5374FCE5EDBC8E2A8697C15331677E6EBF0B),
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                    ),  # noqa: E501
                    Hash(
                        "0x00000000000000000000000000000000000000000000000000000000000060a7"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
        ],
        41: [],
        42: [
            AccessList(
                address=Address(0xCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC),
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                    ),  # noqa: E501
                    Hash(
                        "0x00000000000000000000000000000000000000000000000000000000000060a7"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
        ],
        43: [],
        44: [
            AccessList(
                address=Address(0x0000000000000000000000000000000000001000),
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                    ),  # noqa: E501
                    Hash(
                        "0x00000000000000000000000000000000000000000000000000000000000060a7"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
        ],
        45: [],
        46: [
            AccessList(
                address=Address(0x0000000000000000000000000000000000000001),
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                    ),  # noqa: E501
                    Hash(
                        "0x00000000000000000000000000000000000000000000000000000000000060a7"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
        ],
        47: [],
    }

    tx = Transaction(
        sender=sender,
        to=contract_1,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        value=tx_value[v],
        access_list=tx_access_lists.get(d),
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
