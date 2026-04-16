"""
Ori Pomerantz qbzzt1@gmail.com.

Ported from:
state_tests/stReturnDataTest/revertRetDataSizeFiller.yml
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
    ["state_tests/stReturnDataTest/revertRetDataSizeFiller.yml"],
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
    ],
)
@pytest.mark.pre_alloc_mutable
def test_revert_ret_data_size(
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
    contract_1 = Address(0x0000000000000000000000000000000000001000)
    contract_2 = Address(0x0000000000000000000000000000000000000200)
    contract_3 = Address(0x0000000000000000000000000000000000000300)
    contract_4 = Address(0x0000000000000000000000000000000000000400)
    contract_5 = Address(0x0000000000000000000000000000000000000500)
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
    #    [0x00] (/ (- 0 1) 2)
    #    [0x20] (+ @0x00 1)
    #
    #    (return 0 0x40)
    # }
    contract_1 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x0, value=Op.DIV(Op.SUB(0x0, 0x1), 0x2))
        + Op.MSTORE(offset=0x20, value=Op.ADD(Op.MLOAD(offset=0x0), 0x1))
        + Op.RETURN(offset=0x0, size=0x40)
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x0000000000000000000000000000000000001000),  # noqa: E501
    )
    # Source: raw
    # 0x5000
    contract_2 = pre.deploy_contract(  # noqa: F841
        code=Op.POP + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x0000000000000000000000000000000000000200),  # noqa: E501
    )
    # Source: raw
    # 0x600056
    contract_3 = pre.deploy_contract(  # noqa: F841
        code=Op.JUMP(pc=0x0),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x0000000000000000000000000000000000000300),  # noqa: E501
    )
    # Source: raw
    # 0x6001600157
    contract_4 = pre.deploy_contract(  # noqa: F841
        code=Op.JUMPI(pc=0x1, condition=0x1),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x0000000000000000000000000000000000000400),  # noqa: E501
    )
    # Source: raw
    # 0xFE00
    contract_5 = pre.deploy_contract(  # noqa: F841
        code=Op.INVALID + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x0000000000000000000000000000000000000500),  # noqa: E501
    )
    # Source: lll
    # {   ;  $4 is the type of thing that fails
    #     ; $36 is the failure itself
    #
    #     (def 'callType   $4)
    #     (def 'call         0xf1)
    #     (def 'callcode     0xf2)
    #     (def 'delegatecall 0xf4)
    #     (def 'staticcall   0xfa)
    #     (def 'create       0xf0)
    #     (def 'create2      0xf5)
    #
    #     (def 'failureType $36)
    #     (def 'oog 0)
    #
    #     ; We need these values for CREATE(2)
    #     (def 'uf        0x0200)
    #     (def 'jmp       0x0300)
    #     (def 'jmpi      0x0400)
    #     (def 'badOpcode 0x0500)
    #     (def 'badCall   0xFF00)
    #
    #     (def 'NOP 0)
    #
    #     ; Code for CREATE(2) to fail
    #
    #     (def 'codeLoc      0x0000)
    #     (def 'codeLength   0x0100)
    #
    #     (if (= failureType oog)
    #        [codeLength] (lll (sha3 0 (- 0 1)) codeLoc)
    # ... (170 more lines)
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=Op.JUMPI(
            pc=Op.PUSH2[0x11],
            condition=Op.EQ(Op.CALLDATALOAD(offset=0x24), 0x0),
        )
        + Op.POP(0x0)
        + Op.JUMP(pc=Op.PUSH2[0x1F])
        + Op.JUMPDEST
        + Op.PUSH1[0x9]
        + Op.CODECOPY(dest_offset=0x0, offset=0x391, size=Op.DUP1)
        + Op.PUSH2[0x100]
        + Op.MSTORE
        + Op.JUMPDEST
        + Op.JUMPI(
            pc=Op.PUSH2[0x32],
            condition=Op.EQ(Op.CALLDATALOAD(offset=0x24), 0xFF00),
        )
        + Op.POP(0x0)
        + Op.JUMP(pc=Op.PUSH2[0x46])
        + Op.JUMPDEST
        + Op.MSTORE(
            offset=0x100,
            value=Op.CALL(
                gas=Op.GAS,
                address=0xFF00,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.JUMPDEST
        + Op.JUMPI(
            pc=Op.PUSH2[0x59],
            condition=Op.EQ(Op.CALLDATALOAD(offset=0x24), 0x200),
        )
        + Op.POP(0x0)
        + Op.JUMP(pc=Op.PUSH2[0x6D])
        + Op.JUMPDEST
        + Op.MSTORE8(offset=0x0, value=0x50)
        + Op.MSTORE8(offset=Op.ADD(0x0, 0x1), value=0x0)
        + Op.MSTORE(offset=0x100, value=0x2)
        + Op.JUMPDEST
        + Op.JUMPI(
            pc=Op.PUSH2[0x80],
            condition=Op.EQ(Op.CALLDATALOAD(offset=0x24), 0x300),
        )
        + Op.POP(0x0)
        + Op.JUMP(pc=Op.PUSH2[0xA4])
        + Op.JUMPDEST
        + Op.MSTORE8(offset=0x0, value=0x60)
        + Op.MSTORE8(offset=Op.ADD(0x0, 0x1), value=0x0)
        + Op.MSTORE8(offset=Op.ADD(0x0, 0x2), value=0x56)
        + Op.MSTORE8(offset=Op.ADD(0x0, 0x2), value=0x0)
        + Op.MSTORE(offset=0x100, value=0x4)
        + Op.JUMPDEST
        + Op.JUMPI(
            pc=Op.PUSH2[0xB7],
            condition=Op.EQ(Op.CALLDATALOAD(offset=0x24), 0x400),
        )
        + Op.POP(0x0)
        + Op.JUMP(pc=Op.PUSH2[0xEB])
        + Op.JUMPDEST
        + Op.MSTORE8(offset=0x0, value=0x60)
        + Op.MSTORE8(offset=Op.ADD(0x0, 0x1), value=0x1)
        + Op.MSTORE8(offset=Op.ADD(0x0, 0x2), value=0x60)
        + Op.MSTORE8(offset=Op.ADD(0x0, 0x3), value=0x1)
        + Op.MSTORE8(offset=Op.ADD(0x0, 0x4), value=0x57)
        + Op.MSTORE8(offset=Op.ADD(0x0, 0x5), value=0x0)
        + Op.MSTORE(offset=0x100, value=0x6)
        + Op.JUMPDEST
        + Op.JUMPI(
            pc=Op.PUSH2[0xFE],
            condition=Op.EQ(Op.CALLDATALOAD(offset=0x24), 0x500),
        )
        + Op.POP(0x0)
        + Op.JUMP(pc=0x112)
        + Op.JUMPDEST
        + Op.MSTORE8(offset=0x0, value=0xFE)
        + Op.MSTORE8(offset=Op.ADD(0x0, 0x1), value=0x0)
        + Op.MSTORE(offset=0x100, value=0x2)
        + Op.JUMPDEST
        + Op.JUMPI(
            pc=0x12B,
            condition=Op.AND(
                Op.EQ(Op.CALLDATALOAD(offset=0x4), 0xF1),
                Op.EQ(Op.CALLDATALOAD(offset=0x24), 0x0),
            ),
        )
        + Op.POP(0x0)
        + Op.JUMP(pc=0x155)
        + Op.JUMPDEST
        + Op.POP(
            Op.CALL(
                gas=Op.GAS,
                address=0x1000,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x40,
            )
        )
        + Op.SSTORE(key=0x0, value=Op.RETURNDATASIZE)
        + Op.POP(
            Op.CALL(
                gas=0x0,
                address=0x1000,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x40,
            )
        )
        + Op.SSTORE(key=0x1, value=Op.RETURNDATASIZE)
        + Op.JUMPDEST
        + Op.JUMPI(
            pc=0x16E,
            condition=Op.AND(
                Op.EQ(Op.CALLDATALOAD(offset=0x4), 0xF1),
                Op.GT(Op.CALLDATALOAD(offset=0x24), 0x0),
            ),
        )
        + Op.POP(0x0)
        + Op.JUMP(pc=0x19C)
        + Op.JUMPDEST
        + Op.POP(
            Op.CALL(
                gas=Op.GAS,
                address=0x1000,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x40,
            )
        )
        + Op.SSTORE(key=0x0, value=Op.RETURNDATASIZE)
        + Op.POP(
            Op.CALL(
                gas=Op.SUB(Op.GAS, 0xF0000),
                address=Op.CALLDATALOAD(offset=0x24),
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x40,
            )
        )
        + Op.SSTORE(key=0x1, value=Op.RETURNDATASIZE)
        + Op.JUMPDEST
        + Op.JUMPI(
            pc=0x1B5,
            condition=Op.AND(
                Op.EQ(Op.CALLDATALOAD(offset=0x4), 0xF2),
                Op.EQ(Op.CALLDATALOAD(offset=0x24), 0x0),
            ),
        )
        + Op.POP(0x0)
        + Op.JUMP(pc=0x1DF)
        + Op.JUMPDEST
        + Op.POP(
            Op.CALLCODE(
                gas=Op.GAS,
                address=0x1000,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x40,
            )
        )
        + Op.SSTORE(key=0x0, value=Op.RETURNDATASIZE)
        + Op.POP(
            Op.CALLCODE(
                gas=0x0,
                address=0x1000,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x40,
            )
        )
        + Op.SSTORE(key=0x1, value=Op.RETURNDATASIZE)
        + Op.JUMPDEST
        + Op.JUMPI(
            pc=0x1F8,
            condition=Op.AND(
                Op.EQ(Op.CALLDATALOAD(offset=0x4), 0xF2),
                Op.GT(Op.CALLDATALOAD(offset=0x24), 0x0),
            ),
        )
        + Op.POP(0x0)
        + Op.JUMP(pc=0x221)
        + Op.JUMPDEST
        + Op.POP(
            Op.CALL(
                gas=Op.GAS,
                address=0x1000,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x40,
            )
        )
        + Op.SSTORE(key=0x0, value=Op.RETURNDATASIZE)
        + Op.POP(
            Op.CALLCODE(
                gas=Op.GAS,
                address=Op.CALLDATALOAD(offset=0x24),
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x40,
            )
        )
        + Op.SSTORE(key=0x1, value=Op.RETURNDATASIZE)
        + Op.JUMPDEST
        + Op.JUMPI(
            pc=0x23A,
            condition=Op.AND(
                Op.EQ(Op.CALLDATALOAD(offset=0x4), 0xF4),
                Op.EQ(Op.CALLDATALOAD(offset=0x24), 0x0),
            ),
        )
        + Op.POP(0x0)
        + Op.JUMP(pc=0x260)
        + Op.JUMPDEST
        + Op.POP(
            Op.DELEGATECALL(
                gas=Op.GAS,
                address=0x1000,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x40,
            )
        )
        + Op.SSTORE(key=0x0, value=Op.RETURNDATASIZE)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x0,
                address=0x1000,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x40,
            )
        )
        + Op.SSTORE(key=0x1, value=Op.RETURNDATASIZE)
        + Op.JUMPDEST
        + Op.JUMPI(
            pc=0x279,
            condition=Op.AND(
                Op.EQ(Op.CALLDATALOAD(offset=0x4), 0xF4),
                Op.GT(Op.CALLDATALOAD(offset=0x24), 0x0),
            ),
        )
        + Op.POP(0x0)
        + Op.JUMP(pc=0x2A0)
        + Op.JUMPDEST
        + Op.POP(
            Op.CALL(
                gas=Op.GAS,
                address=0x1000,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x40,
            )
        )
        + Op.SSTORE(key=0x0, value=Op.RETURNDATASIZE)
        + Op.POP(
            Op.DELEGATECALL(
                gas=Op.GAS,
                address=Op.CALLDATALOAD(offset=0x24),
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x40,
            )
        )
        + Op.SSTORE(key=0x1, value=Op.RETURNDATASIZE)
        + Op.JUMPDEST
        + Op.JUMPI(
            pc=0x2B9,
            condition=Op.AND(
                Op.EQ(Op.CALLDATALOAD(offset=0x4), 0xFA),
                Op.EQ(Op.CALLDATALOAD(offset=0x24), 0x0),
            ),
        )
        + Op.POP(0x0)
        + Op.JUMP(pc=0x2DF)
        + Op.JUMPDEST
        + Op.POP(
            Op.STATICCALL(
                gas=Op.GAS,
                address=0x1000,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x40,
            )
        )
        + Op.SSTORE(key=0x0, value=Op.RETURNDATASIZE)
        + Op.POP(
            Op.STATICCALL(
                gas=0x0,
                address=0x1000,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x40,
            )
        )
        + Op.SSTORE(key=0x1, value=Op.RETURNDATASIZE)
        + Op.JUMPDEST
        + Op.JUMPI(
            pc=0x2F8,
            condition=Op.AND(
                Op.EQ(Op.CALLDATALOAD(offset=0x4), 0xFA),
                Op.GT(Op.CALLDATALOAD(offset=0x24), 0x0),
            ),
        )
        + Op.POP(0x0)
        + Op.JUMP(pc=0x31F)
        + Op.JUMPDEST
        + Op.POP(
            Op.CALL(
                gas=Op.GAS,
                address=0x1000,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x40,
            )
        )
        + Op.SSTORE(key=0x0, value=Op.RETURNDATASIZE)
        + Op.POP(
            Op.STATICCALL(
                gas=Op.GAS,
                address=Op.CALLDATALOAD(offset=0x24),
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x40,
            )
        )
        + Op.SSTORE(key=0x1, value=Op.RETURNDATASIZE)
        + Op.JUMPDEST
        + Op.JUMPI(
            pc=0x331, condition=Op.EQ(Op.CALLDATALOAD(offset=0x4), 0xF0)
        )
        + Op.POP(0x0)
        + Op.JUMP(pc=0x352)
        + Op.JUMPDEST
        + Op.POP(
            Op.STATICCALL(
                gas=Op.GAS,
                address=0x1000,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x40,
            )
        )
        + Op.SSTORE(key=0x0, value=Op.RETURNDATASIZE)
        + Op.POP(Op.CREATE(value=0x0, offset=0x0, size=Op.MLOAD(offset=0x100)))
        + Op.SSTORE(key=0x1, value=Op.RETURNDATASIZE)
        + Op.JUMPDEST
        + Op.JUMPI(
            pc=0x364, condition=Op.EQ(Op.CALLDATALOAD(offset=0x4), 0xF5)
        )
        + Op.POP(0x0)
        + Op.JUMP(pc=0x388)
        + Op.JUMPDEST
        + Op.POP(
            Op.STATICCALL(
                gas=Op.GAS,
                address=0x1000,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x40,
            )
        )
        + Op.SSTORE(key=0x0, value=Op.RETURNDATASIZE)
        + Op.POP(
            Op.CREATE2(
                value=0x5A17, offset=0x0, size=0x0, salt=Op.MLOAD(offset=0x100)
            )
        )
        + Op.SSTORE(key=0x1, value=Op.RETURNDATASIZE)
        + Op.JUMPDEST
        + Op.SSTORE(key=0x2, value=0x60A7)
        + Op.STOP
        + Op.INVALID
        + Op.SHA3(offset=0x0, size=Op.SUB(0x0, 0x1))
        + Op.STOP,
        storage={0: 24743, 1: 24743},
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0xCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC),  # noqa: E501
    )

    tx_data = [
        Bytes("1a8451e6") + Hash(0xF1) + Hash(0x0),
        Bytes("1a8451e6") + Hash(0xF2) + Hash(0x0),
        Bytes("1a8451e6") + Hash(0xF4) + Hash(0x0),
        Bytes("1a8451e6") + Hash(0xFA) + Hash(0x0),
        Bytes("1a8451e6") + Hash(0xF0) + Hash(0x0),
        Bytes("1a8451e6") + Hash(0xF5) + Hash(0x0),
        Bytes("1a8451e6") + Hash(0xF1) + Hash(contract_2, left_padding=True),
        Bytes("1a8451e6") + Hash(0xF2) + Hash(contract_2, left_padding=True),
        Bytes("1a8451e6") + Hash(0xF4) + Hash(contract_2, left_padding=True),
        Bytes("1a8451e6") + Hash(0xFA) + Hash(contract_2, left_padding=True),
        Bytes("1a8451e6") + Hash(0xF0) + Hash(contract_2, left_padding=True),
        Bytes("1a8451e6") + Hash(0xF5) + Hash(contract_2, left_padding=True),
        Bytes("1a8451e6") + Hash(0xF1) + Hash(contract_3, left_padding=True),
        Bytes("1a8451e6") + Hash(0xF2) + Hash(contract_3, left_padding=True),
        Bytes("1a8451e6") + Hash(0xF4) + Hash(contract_3, left_padding=True),
        Bytes("1a8451e6") + Hash(0xFA) + Hash(contract_3, left_padding=True),
        Bytes("1a8451e6") + Hash(0xF0) + Hash(contract_3, left_padding=True),
        Bytes("1a8451e6") + Hash(0xF5) + Hash(contract_3, left_padding=True),
        Bytes("1a8451e6") + Hash(0xF1) + Hash(contract_4, left_padding=True),
        Bytes("1a8451e6") + Hash(0xF2) + Hash(contract_4, left_padding=True),
        Bytes("1a8451e6") + Hash(0xF4) + Hash(contract_4, left_padding=True),
        Bytes("1a8451e6") + Hash(0xFA) + Hash(contract_4, left_padding=True),
        Bytes("1a8451e6") + Hash(0xF0) + Hash(contract_4, left_padding=True),
        Bytes("1a8451e6") + Hash(0xF5) + Hash(contract_4, left_padding=True),
        Bytes("1a8451e6") + Hash(0xF1) + Hash(contract_5, left_padding=True),
        Bytes("1a8451e6") + Hash(0xF2) + Hash(contract_5, left_padding=True),
        Bytes("1a8451e6") + Hash(0xF4) + Hash(contract_5, left_padding=True),
        Bytes("1a8451e6") + Hash(0xFA) + Hash(contract_5, left_padding=True),
        Bytes("1a8451e6") + Hash(0xF0) + Hash(contract_5, left_padding=True),
        Bytes("1a8451e6") + Hash(0xF5) + Hash(contract_5, left_padding=True),
        Bytes("1a8451e6") + Hash(0xF1) + Hash(0xFF00),
        Bytes("1a8451e6") + Hash(0xF2) + Hash(0xFF00),
        Bytes("1a8451e6") + Hash(0xF4) + Hash(0xFF00),
        Bytes("1a8451e6") + Hash(0xFA) + Hash(0xFF00),
        Bytes("1a8451e6") + Hash(0xF0) + Hash(0xFF00),
        Bytes("1a8451e6") + Hash(0xF5) + Hash(0xFF00),
    ]
    tx_gas = [16777216]
    tx_value = [1]

    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        value=tx_value[v],
    )

    post = {contract_0: Account(storage={0: 64, 1: 0, 2: 24743})}

    state_test(env=env, pre=pre, post=post, tx=tx)
