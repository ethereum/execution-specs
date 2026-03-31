"""
Ori Pomerantz qbzzt1@gmail.com.

Ported from:
state_tests/stCreateTest/CreateResultsFiller.yml
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
    ["state_tests/stCreateTest/CreateResultsFiller.yml"],
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
    ],
)
@pytest.mark.pre_alloc_mutable
def test_create_results(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Ori Pomerantz qbzzt1@gmail."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    contract_0 = Address(0xCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC)
    contract_1 = Address(0x00000000000000000000000000000000000060A7)
    sender = EOA(
        key=0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=4294967296,
    )

    # Source: lll
    # {
    #   ; Variables are 0x20 bytes (= 256 bits) apart, except for
    #   ; code buffers that get 0x100 (256 bytes)
    #   (def 'creation          0x100)
    #   (def 'callType          0x120)
    #   (def 'constructor       0x140)
    #   (def 'contractCode      0x200)
    #   (def 'constructorCode   0x300)
    #   (def 'extCode           0x400)
    #   (def 'contractLength    0x520)
    #   (def 'constructorLength 0x540)
    #   (def 'extLength         0x560)
    #   (def 'addr1             0x600)
    #   (def 'addr2             0x620)
    #   (def 'callRet           0x640)
    #   (def 'retData0          0x160)   ; storage for returned data
    #   ; Other constants
    #   (def 'NOP 0)   ; No OPeration
    #   ; Understand the input.
    #   [creation]       $0x04
    #   [callType]       $0x24
    #   [constructor]    $0x44
    #   ; The contract code
    #   (def 'contractMacro
    #             (lll
    #                (call 0xFFFF 0x60A7 0 0 0 0 0)
    #                contractCode
    #             ) ; inner lll
    #   )
    #   ; I did not want to rely on knowing the address at which the contract
    # ... (138 more lines)
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x100, value=Op.CALLDATALOAD(offset=0x4))
        + Op.MSTORE(offset=0x120, value=Op.CALLDATALOAD(offset=0x24))
        + Op.MSTORE(offset=0x140, value=Op.CALLDATALOAD(offset=0x44))
        + Op.JUMPI(
            pc=Op.PUSH2[0x2F],
            condition=Op.OR(
                Op.EQ(Op.MLOAD(offset=0x140), 0x0),
                Op.EQ(Op.MLOAD(offset=0x140), 0x4),
            ),
        )
        + Op.POP(0x0)
        + Op.JUMP(pc=Op.PUSH2[0x3E])
        + Op.JUMPDEST
        + Op.PUSH1[0x21]
        + Op.CODECOPY(dest_offset=0x300, offset=0x250, size=Op.DUP1)
        + Op.PUSH2[0x540]
        + Op.MSTORE
        + Op.JUMPDEST
        + Op.JUMPI(
            pc=Op.PUSH2[0x51], condition=Op.EQ(Op.MLOAD(offset=0x140), 0x1)
        )
        + Op.POP(0x0)
        + Op.JUMP(pc=Op.PUSH2[0x60])
        + Op.JUMPDEST
        + Op.PUSH1[0x29]
        + Op.CODECOPY(dest_offset=0x300, offset=0x271, size=Op.DUP1)
        + Op.PUSH2[0x540]
        + Op.MSTORE
        + Op.JUMPDEST
        + Op.JUMPI(
            pc=Op.PUSH2[0x73], condition=Op.EQ(Op.MLOAD(offset=0x140), 0x2)
        )
        + Op.POP(0x0)
        + Op.JUMP(pc=Op.PUSH2[0x82])
        + Op.JUMPDEST
        + Op.PUSH1[0x26]
        + Op.CODECOPY(dest_offset=0x300, offset=0x29A, size=Op.DUP1)
        + Op.PUSH2[0x540]
        + Op.MSTORE
        + Op.JUMPDEST
        + Op.JUMPI(
            pc=Op.PUSH2[0x95], condition=Op.EQ(Op.MLOAD(offset=0x140), 0x3)
        )
        + Op.POP(0x0)
        + Op.JUMP(pc=Op.PUSH2[0xA4])
        + Op.JUMPDEST
        + Op.PUSH1[0x2C]
        + Op.CODECOPY(dest_offset=0x300, offset=0x2C0, size=Op.DUP1)
        + Op.PUSH2[0x540]
        + Op.MSTORE
        + Op.JUMPDEST
        + Op.JUMPI(
            pc=Op.PUSH2[0xB7], condition=Op.EQ(Op.MLOAD(offset=0x140), 0x5)
        )
        + Op.POP(0x0)
        + Op.JUMP(pc=Op.PUSH2[0xC6])
        + Op.JUMPDEST
        + Op.PUSH1[0x28]
        + Op.CODECOPY(dest_offset=0x300, offset=0x2EC, size=Op.DUP1)
        + Op.PUSH2[0x540]
        + Op.MSTORE
        + Op.JUMPDEST
        + Op.JUMPI(
            pc=Op.PUSH2[0xD9], condition=Op.EQ(Op.MLOAD(offset=0x140), 0x6)
        )
        + Op.POP(0x0)
        + Op.JUMP(pc=Op.PUSH2[0xE8])
        + Op.JUMPDEST
        + Op.PUSH1[0x2A]
        + Op.CODECOPY(dest_offset=0x300, offset=0x314, size=Op.DUP1)
        + Op.PUSH2[0x540]
        + Op.MSTORE
        + Op.JUMPDEST
        + Op.PUSH1[0x12]
        + Op.CODECOPY(dest_offset=0x200, offset=0x33E, size=Op.DUP1)
        + Op.PUSH2[0x520]
        + Op.MSTORE
        + Op.JUMPI(pc=0x117, condition=Op.EQ(Op.MLOAD(offset=0x100), 0x1))
        + Op.MSTORE(
            offset=0x600,
            value=Op.CREATE2(
                value=0x0,
                offset=0x300,
                size=Op.MLOAD(offset=0x540),
                salt=0x5A17,
            ),
        )
        + Op.JUMP(pc=0x126)
        + Op.JUMPDEST
        + Op.MSTORE(
            offset=0x600,
            value=Op.CREATE(
                value=0x0, offset=0x300, size=Op.MLOAD(offset=0x540)
            ),
        )
        + Op.JUMPDEST
        + Op.SSTORE(key=0x20, value=Op.PC)
        + Op.SSTORE(key=0x10, value=Op.RETURNDATASIZE)
        + Op.JUMPI(
            pc=0x143,
            condition=Op.OR(
                Op.RETURNDATASIZE, Op.EQ(Op.MLOAD(offset=0x140), 0x4)
            ),
        )
        + Op.POP(0x0)
        + Op.JUMP(pc=0x153)
        + Op.JUMPDEST
        + Op.RETURNDATACOPY(dest_offset=0x160, offset=0x0, size=0x20)
        + Op.SSTORE(key=0x11, value=Op.MLOAD(offset=0x160))
        + Op.JUMPDEST
        + Op.MSTORE(
            offset=0x560, value=Op.EXTCODESIZE(address=Op.MLOAD(offset=0x600))
        )
        + Op.EXTCODECOPY(
            address=Op.MLOAD(offset=0x600),
            dest_offset=0x400,
            offset=0x0,
            size=Op.MLOAD(offset=0x560),
        )
        + Op.SSTORE(
            key=0x12,
            value=Op.SUB(Op.MLOAD(offset=0x520), Op.MLOAD(offset=0x560)),
        )
        + Op.SSTORE(
            key=0x13,
            value=Op.SUB(Op.MLOAD(offset=0x200), Op.MLOAD(offset=0x400)),
        )
        + Op.JUMPI(pc=0x195, condition=Op.EQ(Op.MLOAD(offset=0x120), 0x1))
        + Op.POP(0x0)
        + Op.JUMP(pc=0x1AC)
        + Op.JUMPDEST
        + Op.MSTORE(
            offset=0x640,
            value=Op.CALL(
                gas=0xFFFF,
                address=Op.MLOAD(offset=0x600),
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.JUMPDEST
        + Op.JUMPI(pc=0x1BF, condition=Op.EQ(Op.MLOAD(offset=0x120), 0x2))
        + Op.POP(0x0)
        + Op.JUMP(pc=0x1D6)
        + Op.JUMPDEST
        + Op.MSTORE(
            offset=0x640,
            value=Op.CALLCODE(
                gas=0xFFFF,
                address=Op.MLOAD(offset=0x600),
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.JUMPDEST
        + Op.JUMPI(pc=0x1E9, condition=Op.EQ(Op.MLOAD(offset=0x120), 0x3))
        + Op.POP(0x0)
        + Op.JUMP(pc=0x1FE)
        + Op.JUMPDEST
        + Op.MSTORE(
            offset=0x640,
            value=Op.DELEGATECALL(
                gas=0xFFFF,
                address=Op.MLOAD(offset=0x600),
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.JUMPDEST
        + Op.JUMPI(pc=0x211, condition=Op.EQ(Op.MLOAD(offset=0x120), 0x4))
        + Op.POP(0x0)
        + Op.JUMP(pc=0x226)
        + Op.JUMPDEST
        + Op.MSTORE(
            offset=0x640,
            value=Op.STATICCALL(
                gas=0xFFFF,
                address=Op.MLOAD(offset=0x600),
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.JUMPDEST
        + Op.SSTORE(key=0x21, value=Op.PC)
        + Op.JUMPI(
            pc=0x23E, condition=Op.ISZERO(Op.EQ(Op.MLOAD(offset=0x120), 0x0))
        )
        + Op.POP(0x0)
        + Op.JUMP(pc=0x24D)
        + Op.JUMPDEST
        + Op.SSTORE(key=0x14, value=Op.SUB(Op.MLOAD(offset=0x640), 0x1))
        + Op.SSTORE(key=0x15, value=Op.RETURNDATASIZE)
        + Op.JUMPDEST
        + Op.STOP
        + Op.INVALID
        + Op.PUSH1[0x12]
        + Op.CODECOPY(dest_offset=0x200, offset=0xF, size=Op.DUP1)
        + Op.PUSH2[0x200]
        + Op.RETURN
        + Op.STOP
        + Op.INVALID
        + Op.CALL(
            gas=0xFFFF,
            address=0x60A7,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP
        + Op.POP(Op.SHA3(offset=0x0, size=0x2FFFFF))
        + Op.PUSH1[0x12]
        + Op.CODECOPY(dest_offset=0x200, offset=0x17, size=Op.DUP1)
        + Op.PUSH2[0x200]
        + Op.RETURN
        + Op.STOP
        + Op.INVALID
        + Op.CALL(
            gas=0xFFFF,
            address=0x60A7,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP
        + Op.REVERT(offset=0x0, size=0x0)
        + Op.PUSH1[0x12]
        + Op.CODECOPY(dest_offset=0x200, offset=0x14, size=Op.DUP1)
        + Op.PUSH2[0x200]
        + Op.RETURN
        + Op.STOP
        + Op.INVALID
        + Op.CALL(
            gas=0xFFFF,
            address=0x60A7,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP
        + Op.MSTORE(offset=0x0, value=0x60A7)
        + Op.REVERT(offset=0x0, size=0x20)
        + Op.PUSH1[0x12]
        + Op.CODECOPY(dest_offset=0x200, offset=0x1A, size=Op.DUP1)
        + Op.PUSH2[0x200]
        + Op.RETURN
        + Op.STOP
        + Op.INVALID
        + Op.CALL(
            gas=0xFFFF,
            address=0x60A7,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP
        + Op.MSTORE(offset=0x0, value=0x60A7)
        + Op.STOP
        + Op.PUSH1[0x12]
        + Op.CODECOPY(dest_offset=0x200, offset=0x16, size=Op.DUP1)
        + Op.PUSH2[0x200]
        + Op.RETURN
        + Op.STOP
        + Op.INVALID
        + Op.CALL(
            gas=0xFFFF,
            address=0x60A7,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP
        + Op.MSTORE(offset=0x0, value=0x60A7)
        + Op.SELFDESTRUCT(address=0x0)
        + Op.PUSH1[0x12]
        + Op.CODECOPY(dest_offset=0x200, offset=0x18, size=Op.DUP1)
        + Op.PUSH2[0x200]
        + Op.RETURN
        + Op.STOP
        + Op.INVALID
        + Op.CALL(
            gas=0xFFFF,
            address=0x60A7,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP
        + Op.CALL(
            gas=0xFFFF,
            address=0x60A7,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        storage={
            16: 24743,
            18: 24743,
            19: 24743,
            20: 24743,
            21: 24743,
            32: 24743,
            33: 24743,
        },
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0xCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC),  # noqa: E501
    )
    # Source: lll
    # {
    #   [[0]] 0x60A7
    # }   ; end of LLL code
    contract_1 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x60A7) + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x00000000000000000000000000000000000060A7),  # noqa: E501
    )
    pre[sender] = Account(balance=0xBA1A9CE0BA1A9CE)

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": [0, 1, 2, 4, 5, 6], "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract_0: Account(storage={32: 295, 33: 551}),
                contract_1: Account(storage={0: 24743}),
            },
        },
        {
            "indexes": {"data": [3, 7], "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {contract_0: Account(storage={32: 295, 33: 551})},
        },
        {
            "indexes": {
                "data": [8, 9, 10, 11, 12, 13, 14, 15],
                "gas": 0,
                "value": 0,
            },
            "network": [">=Cancun"],
            "result": {
                contract_0: Account(
                    storage={
                        18: 18,
                        19: 0x600060006000600060006160A761FFFFF1000000000000000000000000000000,  # noqa: E501
                        20: 24743,
                        21: 24743,
                        32: 295,
                        33: 551,
                    },
                ),
            },
        },
        {
            "indexes": {"data": [16, 17], "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract_0: Account(
                    storage={
                        16: 32,
                        17: 24743,
                        18: 18,
                        19: 0x600060006000600060006160A761FFFFF1000000000000000000000000000000,  # noqa: E501
                        20: 24743,
                        21: 24743,
                        32: 295,
                        33: 551,
                    },
                ),
            },
        },
        {
            "indexes": {
                "data": [18, 19, 20, 21, 22, 23, 24, 25],
                "gas": 0,
                "value": 0,
            },
            "network": [">=Cancun"],
            "result": {
                contract_0: Account(
                    storage={
                        16: 24743,
                        17: 0,
                        18: 24743,
                        19: 24743,
                        20: 24743,
                        21: 24743,
                        32: 24743,
                        33: 24743,
                    },
                ),
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx_data = [
        Bytes("048071d3") + Hash(0x1) + Hash(0x1) + Hash(0x0),
        Bytes("048071d3") + Hash(0x1) + Hash(0x2) + Hash(0x0),
        Bytes("048071d3") + Hash(0x1) + Hash(0x3) + Hash(0x0),
        Bytes("048071d3") + Hash(0x1) + Hash(0x4) + Hash(0x0),
        Bytes("048071d3") + Hash(0x2) + Hash(0x1) + Hash(0x0),
        Bytes("048071d3") + Hash(0x2) + Hash(0x2) + Hash(0x0),
        Bytes("048071d3") + Hash(0x2) + Hash(0x3) + Hash(0x0),
        Bytes("048071d3") + Hash(0x2) + Hash(0x4) + Hash(0x0),
        Bytes("048071d3") + Hash(0x1) + Hash(0x0) + Hash(0x1),
        Bytes("048071d3") + Hash(0x2) + Hash(0x0) + Hash(0x1),
        Bytes("048071d3") + Hash(0x1) + Hash(0x0) + Hash(0x2),
        Bytes("048071d3") + Hash(0x2) + Hash(0x0) + Hash(0x2),
        Bytes("048071d3") + Hash(0x1) + Hash(0x0) + Hash(0x5),
        Bytes("048071d3") + Hash(0x2) + Hash(0x0) + Hash(0x5),
        Bytes("048071d3") + Hash(0x1) + Hash(0x0) + Hash(0x6),
        Bytes("048071d3") + Hash(0x2) + Hash(0x0) + Hash(0x6),
        Bytes("048071d3") + Hash(0x1) + Hash(0x0) + Hash(0x3),
        Bytes("048071d3") + Hash(0x2) + Hash(0x0) + Hash(0x3),
        Bytes("048071d3") + Hash(0x1) + Hash(0x1) + Hash(0x4),
        Bytes("048071d3") + Hash(0x1) + Hash(0x2) + Hash(0x4),
        Bytes("048071d3") + Hash(0x1) + Hash(0x3) + Hash(0x4),
        Bytes("048071d3") + Hash(0x1) + Hash(0x4) + Hash(0x4),
        Bytes("048071d3") + Hash(0x2) + Hash(0x1) + Hash(0x4),
        Bytes("048071d3") + Hash(0x2) + Hash(0x2) + Hash(0x4),
        Bytes("048071d3") + Hash(0x2) + Hash(0x3) + Hash(0x4),
        Bytes("048071d3") + Hash(0x2) + Hash(0x4) + Hash(0x4),
    ]
    tx_gas = [9437184]

    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
