"""
Ori Pomerantz qbzzt1@gmail.com.

Ported from:
tests/static/state_tests/stReturnDataTest/revertRetDataSizeFiller.yml
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
)
from execution_testing.forks import Fork
from execution_testing.specs.static_state.expect_section import (
    resolve_expect_post,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

TX_DATA = [
    "1a8451e600000000000000000000000000000000000000000000000000000000000000f10000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
    "1a8451e600000000000000000000000000000000000000000000000000000000000000f20000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
    "1a8451e600000000000000000000000000000000000000000000000000000000000000f40000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
    "1a8451e600000000000000000000000000000000000000000000000000000000000000fa0000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
    "1a8451e600000000000000000000000000000000000000000000000000000000000000f00000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
    "1a8451e600000000000000000000000000000000000000000000000000000000000000f50000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
    "1a8451e600000000000000000000000000000000000000000000000000000000000000f10000000000000000000000000000000000000000000000000000000000000200",  # noqa: E501
    "1a8451e600000000000000000000000000000000000000000000000000000000000000f20000000000000000000000000000000000000000000000000000000000000200",  # noqa: E501
    "1a8451e600000000000000000000000000000000000000000000000000000000000000f40000000000000000000000000000000000000000000000000000000000000200",  # noqa: E501
    "1a8451e600000000000000000000000000000000000000000000000000000000000000fa0000000000000000000000000000000000000000000000000000000000000200",  # noqa: E501
    "1a8451e600000000000000000000000000000000000000000000000000000000000000f00000000000000000000000000000000000000000000000000000000000000200",  # noqa: E501
    "1a8451e600000000000000000000000000000000000000000000000000000000000000f50000000000000000000000000000000000000000000000000000000000000200",  # noqa: E501
    "1a8451e600000000000000000000000000000000000000000000000000000000000000f10000000000000000000000000000000000000000000000000000000000000300",  # noqa: E501
    "1a8451e600000000000000000000000000000000000000000000000000000000000000f20000000000000000000000000000000000000000000000000000000000000300",  # noqa: E501
    "1a8451e600000000000000000000000000000000000000000000000000000000000000f40000000000000000000000000000000000000000000000000000000000000300",  # noqa: E501
    "1a8451e600000000000000000000000000000000000000000000000000000000000000fa0000000000000000000000000000000000000000000000000000000000000300",  # noqa: E501
    "1a8451e600000000000000000000000000000000000000000000000000000000000000f00000000000000000000000000000000000000000000000000000000000000300",  # noqa: E501
    "1a8451e600000000000000000000000000000000000000000000000000000000000000f50000000000000000000000000000000000000000000000000000000000000300",  # noqa: E501
    "1a8451e600000000000000000000000000000000000000000000000000000000000000f10000000000000000000000000000000000000000000000000000000000000400",  # noqa: E501
    "1a8451e600000000000000000000000000000000000000000000000000000000000000f20000000000000000000000000000000000000000000000000000000000000400",  # noqa: E501
    "1a8451e600000000000000000000000000000000000000000000000000000000000000f40000000000000000000000000000000000000000000000000000000000000400",  # noqa: E501
    "1a8451e600000000000000000000000000000000000000000000000000000000000000fa0000000000000000000000000000000000000000000000000000000000000400",  # noqa: E501
    "1a8451e600000000000000000000000000000000000000000000000000000000000000f00000000000000000000000000000000000000000000000000000000000000400",  # noqa: E501
    "1a8451e600000000000000000000000000000000000000000000000000000000000000f50000000000000000000000000000000000000000000000000000000000000400",  # noqa: E501
    "1a8451e600000000000000000000000000000000000000000000000000000000000000f10000000000000000000000000000000000000000000000000000000000000500",  # noqa: E501
    "1a8451e600000000000000000000000000000000000000000000000000000000000000f20000000000000000000000000000000000000000000000000000000000000500",  # noqa: E501
    "1a8451e600000000000000000000000000000000000000000000000000000000000000f40000000000000000000000000000000000000000000000000000000000000500",  # noqa: E501
    "1a8451e600000000000000000000000000000000000000000000000000000000000000fa0000000000000000000000000000000000000000000000000000000000000500",  # noqa: E501
    "1a8451e600000000000000000000000000000000000000000000000000000000000000f00000000000000000000000000000000000000000000000000000000000000500",  # noqa: E501
    "1a8451e600000000000000000000000000000000000000000000000000000000000000f50000000000000000000000000000000000000000000000000000000000000500",  # noqa: E501
    "1a8451e600000000000000000000000000000000000000000000000000000000000000f1000000000000000000000000000000000000000000000000000000000000ff00",  # noqa: E501
    "1a8451e600000000000000000000000000000000000000000000000000000000000000f2000000000000000000000000000000000000000000000000000000000000ff00",  # noqa: E501
    "1a8451e600000000000000000000000000000000000000000000000000000000000000f4000000000000000000000000000000000000000000000000000000000000ff00",  # noqa: E501
    "1a8451e600000000000000000000000000000000000000000000000000000000000000fa000000000000000000000000000000000000000000000000000000000000ff00",  # noqa: E501
    "1a8451e600000000000000000000000000000000000000000000000000000000000000f0000000000000000000000000000000000000000000000000000000000000ff00",  # noqa: E501
    "1a8451e600000000000000000000000000000000000000000000000000000000000000f5000000000000000000000000000000000000000000000000000000000000ff00",  # noqa: E501
]

TX_GAS = [16777216]

TX_VALUE = [1]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d]) if TX_DATA[d] else b""


@pytest.mark.ported_from(
    ["tests/static/state_tests/stReturnDataTest/revertRetDataSizeFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(0, 0, 0, id="case0"),
        pytest.param(10, 0, 0, id="case1"),
        pytest.param(11, 0, 0, id="case2"),
        pytest.param(12, 0, 0, id="case3"),
        pytest.param(13, 0, 0, id="case4"),
        pytest.param(14, 0, 0, id="case5"),
        pytest.param(15, 0, 0, id="case6"),
        pytest.param(16, 0, 0, id="case7"),
        pytest.param(17, 0, 0, id="case8"),
        pytest.param(18, 0, 0, id="case9"),
        pytest.param(19, 0, 0, id="case10"),
        pytest.param(1, 0, 0, id="case11"),
        pytest.param(20, 0, 0, id="case12"),
        pytest.param(21, 0, 0, id="case13"),
        pytest.param(22, 0, 0, id="case14"),
        pytest.param(23, 0, 0, id="case15"),
        pytest.param(24, 0, 0, id="case16"),
        pytest.param(25, 0, 0, id="case17"),
        pytest.param(26, 0, 0, id="case18"),
        pytest.param(27, 0, 0, id="case19"),
        pytest.param(28, 0, 0, id="case20"),
        pytest.param(29, 0, 0, id="case21"),
        pytest.param(2, 0, 0, id="case22"),
        pytest.param(30, 0, 0, id="case23"),
        pytest.param(31, 0, 0, id="case24"),
        pytest.param(32, 0, 0, id="case25"),
        pytest.param(33, 0, 0, id="case26"),
        pytest.param(34, 0, 0, id="case27"),
        pytest.param(35, 0, 0, id="case28"),
        pytest.param(3, 0, 0, id="case29"),
        pytest.param(4, 0, 0, id="case30"),
        pytest.param(5, 0, 0, id="case31"),
        pytest.param(6, 0, 0, id="case32"),
        pytest.param(7, 0, 0, id="case33"),
        pytest.param(8, 0, 0, id="case34"),
        pytest.param(9, 0, 0, id="case35"),
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
    """Ori Pomerantz qbzzt1@gmail.com."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
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

    # Source: raw bytecode
    callee = pre.deploy_contract(
        code=Op.POP + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000000200"),  # noqa: E501
    )
    # Source: raw bytecode
    callee_1 = pre.deploy_contract(
        code=Op.JUMP(pc=0x0),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000000300"),  # noqa: E501
    )
    # Source: raw bytecode
    callee_2 = pre.deploy_contract(
        code=Op.JUMPI(pc=0x1, condition=0x1),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000000400"),  # noqa: E501
    )
    # Source: raw bytecode
    callee_3 = pre.deploy_contract(
        code=Op.INVALID + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000000500"),  # noqa: E501
    )
    callee_4 = pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x0, value=Op.DIV(Op.SUB(0x0, 0x1), 0x2))
            + Op.MSTORE(offset=0x20, value=Op.ADD(Op.MLOAD(offset=0x0), 0x1))
            + Op.RETURN(offset=0x0, size=0x40)
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001000"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xBA1A9CE0BA1A9CE)
    # Source: LLL
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
    contract = pre.deploy_contract(
        code=(
            Op.JUMPI(
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
                ),
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
                ),
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
                ),
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
                ),
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
                ),
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
                ),
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
                ),
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
                ),
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
                ),
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
                ),
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
                ),
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
                ),
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
                ),
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
                ),
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
                ),
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
                ),
            )
            + Op.SSTORE(key=0x1, value=Op.RETURNDATASIZE)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x331,
                condition=Op.EQ(Op.CALLDATALOAD(offset=0x4), 0xF0),
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
                ),
            )
            + Op.SSTORE(key=0x0, value=Op.RETURNDATASIZE)
            + Op.POP(
                Op.CREATE(value=0x0, offset=0x0, size=Op.MLOAD(offset=0x100))
            )
            + Op.SSTORE(key=0x1, value=Op.RETURNDATASIZE)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x364,
                condition=Op.EQ(Op.CALLDATALOAD(offset=0x4), 0xF5),
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
                ),
            )
            + Op.SSTORE(key=0x0, value=Op.RETURNDATASIZE)
            + Op.POP(
                Op.CREATE2(
                    value=0x5A17,
                    offset=0x0,
                    size=0x0,
                    salt=Op.MLOAD(offset=0x100),
                ),
            )
            + Op.SSTORE(key=0x1, value=Op.RETURNDATASIZE)
            + Op.JUMPDEST
            + Op.SSTORE(key=0x2, value=0x60A7)
            + Op.STOP
            + Op.INVALID
            + Op.SHA3(offset=0x0, size=Op.SUB(0x0, 0x1))
            + Op.STOP
        ),
        storage={0x0: 0x60A7, 0x1: 0x60A7},
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0xcccccccccccccccccccccccccccccccccccccccc"),  # noqa: E501
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": 0, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(code=bytes.fromhex("5000")),
                callee_1: Account(code=bytes.fromhex("600056")),
                callee_2: Account(code=bytes.fromhex("6001600157")),
                callee_3: Account(code=bytes.fromhex("fe00")),
                callee_4: Account(
                    code=bytes.fromhex(
                        "600260016000030460005260016000510160205260406000f300"
                    )
                ),
                contract: Account(
                    storage={0: 64, 2: 24743},
                    code=bytes.fromhex(
                        "6000602435146100115760005061001f565b600980610391600039610100525b61ff006024351461003257600050610046565b6000600060006000600061ff005af1610100525b610200602435146100595760005061006d565b605060005360006001600001536002610100525b61030060243514610080576000506100a4565b60606000536000600160000153605660026000015360006002600001536004610100525b610400602435146100b7576000506100eb565b6060600053600160016000015360606002600001536001600360000153605760046000015360006005600001536006610100525b610500602435146100fe57600050610112565b60fe60005360006001600001536002610100525b60006024351460f1600435141661012b57600050610155565b604060006000600060006110005af1503d600055604060006000600060006110006000f1503d6001555b60006024351160f1600435141661016e5760005061019c565b604060006000600060006110005af1503d60005560406000600060006000602435620f00005a03f1503d6001555b60006024351460f260043514166101b5576000506101df565b604060006000600060006110005af2503d600055604060006000600060006110006000f2503d6001555b60006024351160f260043514166101f857600050610221565b604060006000600060006110005af1503d600055604060006000600060006024355af2503d6001555b60006024351460f4600435141661023a57600050610260565b60406000600060006110005af4503d60005560406000600060006110006000f4503d6001555b60006024351160f46004351416610279576000506102a0565b604060006000600060006110005af1503d60005560406000600060006024355af4503d6001555b60006024351460fa60043514166102b9576000506102df565b60406000600060006110005afa503d60005560406000600060006110006000fa503d6001555b60006024351160fa60043514166102f85760005061031f565b604060006000600060006110005af1503d60005560406000600060006024355afa503d6001555b60f06004351461033157600050610352565b60406000600060006110005afa503d6000556101005160006000f0503d6001555b60f56004351461036457600050610388565b60406000600060006110005afa503d6000556101005160006000615a17f5503d6001555b6160a760025500fe600160000360002000"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 10, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(code=bytes.fromhex("5000")),
                callee_1: Account(code=bytes.fromhex("600056")),
                callee_2: Account(code=bytes.fromhex("6001600157")),
                callee_3: Account(code=bytes.fromhex("fe00")),
                callee_4: Account(
                    code=bytes.fromhex(
                        "600260016000030460005260016000510160205260406000f300"
                    )
                ),
                contract: Account(
                    storage={0: 64, 2: 24743},
                    code=bytes.fromhex(
                        "6000602435146100115760005061001f565b600980610391600039610100525b61ff006024351461003257600050610046565b6000600060006000600061ff005af1610100525b610200602435146100595760005061006d565b605060005360006001600001536002610100525b61030060243514610080576000506100a4565b60606000536000600160000153605660026000015360006002600001536004610100525b610400602435146100b7576000506100eb565b6060600053600160016000015360606002600001536001600360000153605760046000015360006005600001536006610100525b610500602435146100fe57600050610112565b60fe60005360006001600001536002610100525b60006024351460f1600435141661012b57600050610155565b604060006000600060006110005af1503d600055604060006000600060006110006000f1503d6001555b60006024351160f1600435141661016e5760005061019c565b604060006000600060006110005af1503d60005560406000600060006000602435620f00005a03f1503d6001555b60006024351460f260043514166101b5576000506101df565b604060006000600060006110005af2503d600055604060006000600060006110006000f2503d6001555b60006024351160f260043514166101f857600050610221565b604060006000600060006110005af1503d600055604060006000600060006024355af2503d6001555b60006024351460f4600435141661023a57600050610260565b60406000600060006110005af4503d60005560406000600060006110006000f4503d6001555b60006024351160f46004351416610279576000506102a0565b604060006000600060006110005af1503d60005560406000600060006024355af4503d6001555b60006024351460fa60043514166102b9576000506102df565b60406000600060006110005afa503d60005560406000600060006110006000fa503d6001555b60006024351160fa60043514166102f85760005061031f565b604060006000600060006110005af1503d60005560406000600060006024355afa503d6001555b60f06004351461033157600050610352565b60406000600060006110005afa503d6000556101005160006000f0503d6001555b60f56004351461036457600050610388565b60406000600060006110005afa503d6000556101005160006000615a17f5503d6001555b6160a760025500fe600160000360002000"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 11, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(code=bytes.fromhex("5000")),
                callee_1: Account(code=bytes.fromhex("600056")),
                callee_2: Account(code=bytes.fromhex("6001600157")),
                callee_3: Account(code=bytes.fromhex("fe00")),
                callee_4: Account(
                    code=bytes.fromhex(
                        "600260016000030460005260016000510160205260406000f300"
                    )
                ),
                contract: Account(
                    storage={0: 64, 2: 24743},
                    code=bytes.fromhex(
                        "6000602435146100115760005061001f565b600980610391600039610100525b61ff006024351461003257600050610046565b6000600060006000600061ff005af1610100525b610200602435146100595760005061006d565b605060005360006001600001536002610100525b61030060243514610080576000506100a4565b60606000536000600160000153605660026000015360006002600001536004610100525b610400602435146100b7576000506100eb565b6060600053600160016000015360606002600001536001600360000153605760046000015360006005600001536006610100525b610500602435146100fe57600050610112565b60fe60005360006001600001536002610100525b60006024351460f1600435141661012b57600050610155565b604060006000600060006110005af1503d600055604060006000600060006110006000f1503d6001555b60006024351160f1600435141661016e5760005061019c565b604060006000600060006110005af1503d60005560406000600060006000602435620f00005a03f1503d6001555b60006024351460f260043514166101b5576000506101df565b604060006000600060006110005af2503d600055604060006000600060006110006000f2503d6001555b60006024351160f260043514166101f857600050610221565b604060006000600060006110005af1503d600055604060006000600060006024355af2503d6001555b60006024351460f4600435141661023a57600050610260565b60406000600060006110005af4503d60005560406000600060006110006000f4503d6001555b60006024351160f46004351416610279576000506102a0565b604060006000600060006110005af1503d60005560406000600060006024355af4503d6001555b60006024351460fa60043514166102b9576000506102df565b60406000600060006110005afa503d60005560406000600060006110006000fa503d6001555b60006024351160fa60043514166102f85760005061031f565b604060006000600060006110005af1503d60005560406000600060006024355afa503d6001555b60f06004351461033157600050610352565b60406000600060006110005afa503d6000556101005160006000f0503d6001555b60f56004351461036457600050610388565b60406000600060006110005afa503d6000556101005160006000615a17f5503d6001555b6160a760025500fe600160000360002000"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 12, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(code=bytes.fromhex("5000")),
                callee_1: Account(code=bytes.fromhex("600056")),
                callee_2: Account(code=bytes.fromhex("6001600157")),
                callee_3: Account(code=bytes.fromhex("fe00")),
                callee_4: Account(
                    code=bytes.fromhex(
                        "600260016000030460005260016000510160205260406000f300"
                    )
                ),
                contract: Account(
                    storage={0: 64, 2: 24743},
                    code=bytes.fromhex(
                        "6000602435146100115760005061001f565b600980610391600039610100525b61ff006024351461003257600050610046565b6000600060006000600061ff005af1610100525b610200602435146100595760005061006d565b605060005360006001600001536002610100525b61030060243514610080576000506100a4565b60606000536000600160000153605660026000015360006002600001536004610100525b610400602435146100b7576000506100eb565b6060600053600160016000015360606002600001536001600360000153605760046000015360006005600001536006610100525b610500602435146100fe57600050610112565b60fe60005360006001600001536002610100525b60006024351460f1600435141661012b57600050610155565b604060006000600060006110005af1503d600055604060006000600060006110006000f1503d6001555b60006024351160f1600435141661016e5760005061019c565b604060006000600060006110005af1503d60005560406000600060006000602435620f00005a03f1503d6001555b60006024351460f260043514166101b5576000506101df565b604060006000600060006110005af2503d600055604060006000600060006110006000f2503d6001555b60006024351160f260043514166101f857600050610221565b604060006000600060006110005af1503d600055604060006000600060006024355af2503d6001555b60006024351460f4600435141661023a57600050610260565b60406000600060006110005af4503d60005560406000600060006110006000f4503d6001555b60006024351160f46004351416610279576000506102a0565b604060006000600060006110005af1503d60005560406000600060006024355af4503d6001555b60006024351460fa60043514166102b9576000506102df565b60406000600060006110005afa503d60005560406000600060006110006000fa503d6001555b60006024351160fa60043514166102f85760005061031f565b604060006000600060006110005af1503d60005560406000600060006024355afa503d6001555b60f06004351461033157600050610352565b60406000600060006110005afa503d6000556101005160006000f0503d6001555b60f56004351461036457600050610388565b60406000600060006110005afa503d6000556101005160006000615a17f5503d6001555b6160a760025500fe600160000360002000"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 13, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(code=bytes.fromhex("5000")),
                callee_1: Account(code=bytes.fromhex("600056")),
                callee_2: Account(code=bytes.fromhex("6001600157")),
                callee_3: Account(code=bytes.fromhex("fe00")),
                callee_4: Account(
                    code=bytes.fromhex(
                        "600260016000030460005260016000510160205260406000f300"
                    )
                ),
                contract: Account(
                    storage={0: 64, 2: 24743},
                    code=bytes.fromhex(
                        "6000602435146100115760005061001f565b600980610391600039610100525b61ff006024351461003257600050610046565b6000600060006000600061ff005af1610100525b610200602435146100595760005061006d565b605060005360006001600001536002610100525b61030060243514610080576000506100a4565b60606000536000600160000153605660026000015360006002600001536004610100525b610400602435146100b7576000506100eb565b6060600053600160016000015360606002600001536001600360000153605760046000015360006005600001536006610100525b610500602435146100fe57600050610112565b60fe60005360006001600001536002610100525b60006024351460f1600435141661012b57600050610155565b604060006000600060006110005af1503d600055604060006000600060006110006000f1503d6001555b60006024351160f1600435141661016e5760005061019c565b604060006000600060006110005af1503d60005560406000600060006000602435620f00005a03f1503d6001555b60006024351460f260043514166101b5576000506101df565b604060006000600060006110005af2503d600055604060006000600060006110006000f2503d6001555b60006024351160f260043514166101f857600050610221565b604060006000600060006110005af1503d600055604060006000600060006024355af2503d6001555b60006024351460f4600435141661023a57600050610260565b60406000600060006110005af4503d60005560406000600060006110006000f4503d6001555b60006024351160f46004351416610279576000506102a0565b604060006000600060006110005af1503d60005560406000600060006024355af4503d6001555b60006024351460fa60043514166102b9576000506102df565b60406000600060006110005afa503d60005560406000600060006110006000fa503d6001555b60006024351160fa60043514166102f85760005061031f565b604060006000600060006110005af1503d60005560406000600060006024355afa503d6001555b60f06004351461033157600050610352565b60406000600060006110005afa503d6000556101005160006000f0503d6001555b60f56004351461036457600050610388565b60406000600060006110005afa503d6000556101005160006000615a17f5503d6001555b6160a760025500fe600160000360002000"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 14, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(code=bytes.fromhex("5000")),
                callee_1: Account(code=bytes.fromhex("600056")),
                callee_2: Account(code=bytes.fromhex("6001600157")),
                callee_3: Account(code=bytes.fromhex("fe00")),
                callee_4: Account(
                    code=bytes.fromhex(
                        "600260016000030460005260016000510160205260406000f300"
                    )
                ),
                contract: Account(
                    storage={0: 64, 2: 24743},
                    code=bytes.fromhex(
                        "6000602435146100115760005061001f565b600980610391600039610100525b61ff006024351461003257600050610046565b6000600060006000600061ff005af1610100525b610200602435146100595760005061006d565b605060005360006001600001536002610100525b61030060243514610080576000506100a4565b60606000536000600160000153605660026000015360006002600001536004610100525b610400602435146100b7576000506100eb565b6060600053600160016000015360606002600001536001600360000153605760046000015360006005600001536006610100525b610500602435146100fe57600050610112565b60fe60005360006001600001536002610100525b60006024351460f1600435141661012b57600050610155565b604060006000600060006110005af1503d600055604060006000600060006110006000f1503d6001555b60006024351160f1600435141661016e5760005061019c565b604060006000600060006110005af1503d60005560406000600060006000602435620f00005a03f1503d6001555b60006024351460f260043514166101b5576000506101df565b604060006000600060006110005af2503d600055604060006000600060006110006000f2503d6001555b60006024351160f260043514166101f857600050610221565b604060006000600060006110005af1503d600055604060006000600060006024355af2503d6001555b60006024351460f4600435141661023a57600050610260565b60406000600060006110005af4503d60005560406000600060006110006000f4503d6001555b60006024351160f46004351416610279576000506102a0565b604060006000600060006110005af1503d60005560406000600060006024355af4503d6001555b60006024351460fa60043514166102b9576000506102df565b60406000600060006110005afa503d60005560406000600060006110006000fa503d6001555b60006024351160fa60043514166102f85760005061031f565b604060006000600060006110005af1503d60005560406000600060006024355afa503d6001555b60f06004351461033157600050610352565b60406000600060006110005afa503d6000556101005160006000f0503d6001555b60f56004351461036457600050610388565b60406000600060006110005afa503d6000556101005160006000615a17f5503d6001555b6160a760025500fe600160000360002000"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 15, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(code=bytes.fromhex("5000")),
                callee_1: Account(code=bytes.fromhex("600056")),
                callee_2: Account(code=bytes.fromhex("6001600157")),
                callee_3: Account(code=bytes.fromhex("fe00")),
                callee_4: Account(
                    code=bytes.fromhex(
                        "600260016000030460005260016000510160205260406000f300"
                    )
                ),
                contract: Account(
                    storage={0: 64, 2: 24743},
                    code=bytes.fromhex(
                        "6000602435146100115760005061001f565b600980610391600039610100525b61ff006024351461003257600050610046565b6000600060006000600061ff005af1610100525b610200602435146100595760005061006d565b605060005360006001600001536002610100525b61030060243514610080576000506100a4565b60606000536000600160000153605660026000015360006002600001536004610100525b610400602435146100b7576000506100eb565b6060600053600160016000015360606002600001536001600360000153605760046000015360006005600001536006610100525b610500602435146100fe57600050610112565b60fe60005360006001600001536002610100525b60006024351460f1600435141661012b57600050610155565b604060006000600060006110005af1503d600055604060006000600060006110006000f1503d6001555b60006024351160f1600435141661016e5760005061019c565b604060006000600060006110005af1503d60005560406000600060006000602435620f00005a03f1503d6001555b60006024351460f260043514166101b5576000506101df565b604060006000600060006110005af2503d600055604060006000600060006110006000f2503d6001555b60006024351160f260043514166101f857600050610221565b604060006000600060006110005af1503d600055604060006000600060006024355af2503d6001555b60006024351460f4600435141661023a57600050610260565b60406000600060006110005af4503d60005560406000600060006110006000f4503d6001555b60006024351160f46004351416610279576000506102a0565b604060006000600060006110005af1503d60005560406000600060006024355af4503d6001555b60006024351460fa60043514166102b9576000506102df565b60406000600060006110005afa503d60005560406000600060006110006000fa503d6001555b60006024351160fa60043514166102f85760005061031f565b604060006000600060006110005af1503d60005560406000600060006024355afa503d6001555b60f06004351461033157600050610352565b60406000600060006110005afa503d6000556101005160006000f0503d6001555b60f56004351461036457600050610388565b60406000600060006110005afa503d6000556101005160006000615a17f5503d6001555b6160a760025500fe600160000360002000"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 16, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(code=bytes.fromhex("5000")),
                callee_1: Account(code=bytes.fromhex("600056")),
                callee_2: Account(code=bytes.fromhex("6001600157")),
                callee_3: Account(code=bytes.fromhex("fe00")),
                callee_4: Account(
                    code=bytes.fromhex(
                        "600260016000030460005260016000510160205260406000f300"
                    )
                ),
                contract: Account(
                    storage={0: 64, 2: 24743},
                    code=bytes.fromhex(
                        "6000602435146100115760005061001f565b600980610391600039610100525b61ff006024351461003257600050610046565b6000600060006000600061ff005af1610100525b610200602435146100595760005061006d565b605060005360006001600001536002610100525b61030060243514610080576000506100a4565b60606000536000600160000153605660026000015360006002600001536004610100525b610400602435146100b7576000506100eb565b6060600053600160016000015360606002600001536001600360000153605760046000015360006005600001536006610100525b610500602435146100fe57600050610112565b60fe60005360006001600001536002610100525b60006024351460f1600435141661012b57600050610155565b604060006000600060006110005af1503d600055604060006000600060006110006000f1503d6001555b60006024351160f1600435141661016e5760005061019c565b604060006000600060006110005af1503d60005560406000600060006000602435620f00005a03f1503d6001555b60006024351460f260043514166101b5576000506101df565b604060006000600060006110005af2503d600055604060006000600060006110006000f2503d6001555b60006024351160f260043514166101f857600050610221565b604060006000600060006110005af1503d600055604060006000600060006024355af2503d6001555b60006024351460f4600435141661023a57600050610260565b60406000600060006110005af4503d60005560406000600060006110006000f4503d6001555b60006024351160f46004351416610279576000506102a0565b604060006000600060006110005af1503d60005560406000600060006024355af4503d6001555b60006024351460fa60043514166102b9576000506102df565b60406000600060006110005afa503d60005560406000600060006110006000fa503d6001555b60006024351160fa60043514166102f85760005061031f565b604060006000600060006110005af1503d60005560406000600060006024355afa503d6001555b60f06004351461033157600050610352565b60406000600060006110005afa503d6000556101005160006000f0503d6001555b60f56004351461036457600050610388565b60406000600060006110005afa503d6000556101005160006000615a17f5503d6001555b6160a760025500fe600160000360002000"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 17, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(code=bytes.fromhex("5000")),
                callee_1: Account(code=bytes.fromhex("600056")),
                callee_2: Account(code=bytes.fromhex("6001600157")),
                callee_3: Account(code=bytes.fromhex("fe00")),
                callee_4: Account(
                    code=bytes.fromhex(
                        "600260016000030460005260016000510160205260406000f300"
                    )
                ),
                contract: Account(
                    storage={0: 64, 2: 24743},
                    code=bytes.fromhex(
                        "6000602435146100115760005061001f565b600980610391600039610100525b61ff006024351461003257600050610046565b6000600060006000600061ff005af1610100525b610200602435146100595760005061006d565b605060005360006001600001536002610100525b61030060243514610080576000506100a4565b60606000536000600160000153605660026000015360006002600001536004610100525b610400602435146100b7576000506100eb565b6060600053600160016000015360606002600001536001600360000153605760046000015360006005600001536006610100525b610500602435146100fe57600050610112565b60fe60005360006001600001536002610100525b60006024351460f1600435141661012b57600050610155565b604060006000600060006110005af1503d600055604060006000600060006110006000f1503d6001555b60006024351160f1600435141661016e5760005061019c565b604060006000600060006110005af1503d60005560406000600060006000602435620f00005a03f1503d6001555b60006024351460f260043514166101b5576000506101df565b604060006000600060006110005af2503d600055604060006000600060006110006000f2503d6001555b60006024351160f260043514166101f857600050610221565b604060006000600060006110005af1503d600055604060006000600060006024355af2503d6001555b60006024351460f4600435141661023a57600050610260565b60406000600060006110005af4503d60005560406000600060006110006000f4503d6001555b60006024351160f46004351416610279576000506102a0565b604060006000600060006110005af1503d60005560406000600060006024355af4503d6001555b60006024351460fa60043514166102b9576000506102df565b60406000600060006110005afa503d60005560406000600060006110006000fa503d6001555b60006024351160fa60043514166102f85760005061031f565b604060006000600060006110005af1503d60005560406000600060006024355afa503d6001555b60f06004351461033157600050610352565b60406000600060006110005afa503d6000556101005160006000f0503d6001555b60f56004351461036457600050610388565b60406000600060006110005afa503d6000556101005160006000615a17f5503d6001555b6160a760025500fe600160000360002000"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 18, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(code=bytes.fromhex("5000")),
                callee_1: Account(code=bytes.fromhex("600056")),
                callee_2: Account(code=bytes.fromhex("6001600157")),
                callee_3: Account(code=bytes.fromhex("fe00")),
                callee_4: Account(
                    code=bytes.fromhex(
                        "600260016000030460005260016000510160205260406000f300"
                    )
                ),
                contract: Account(
                    storage={0: 64, 2: 24743},
                    code=bytes.fromhex(
                        "6000602435146100115760005061001f565b600980610391600039610100525b61ff006024351461003257600050610046565b6000600060006000600061ff005af1610100525b610200602435146100595760005061006d565b605060005360006001600001536002610100525b61030060243514610080576000506100a4565b60606000536000600160000153605660026000015360006002600001536004610100525b610400602435146100b7576000506100eb565b6060600053600160016000015360606002600001536001600360000153605760046000015360006005600001536006610100525b610500602435146100fe57600050610112565b60fe60005360006001600001536002610100525b60006024351460f1600435141661012b57600050610155565b604060006000600060006110005af1503d600055604060006000600060006110006000f1503d6001555b60006024351160f1600435141661016e5760005061019c565b604060006000600060006110005af1503d60005560406000600060006000602435620f00005a03f1503d6001555b60006024351460f260043514166101b5576000506101df565b604060006000600060006110005af2503d600055604060006000600060006110006000f2503d6001555b60006024351160f260043514166101f857600050610221565b604060006000600060006110005af1503d600055604060006000600060006024355af2503d6001555b60006024351460f4600435141661023a57600050610260565b60406000600060006110005af4503d60005560406000600060006110006000f4503d6001555b60006024351160f46004351416610279576000506102a0565b604060006000600060006110005af1503d60005560406000600060006024355af4503d6001555b60006024351460fa60043514166102b9576000506102df565b60406000600060006110005afa503d60005560406000600060006110006000fa503d6001555b60006024351160fa60043514166102f85760005061031f565b604060006000600060006110005af1503d60005560406000600060006024355afa503d6001555b60f06004351461033157600050610352565b60406000600060006110005afa503d6000556101005160006000f0503d6001555b60f56004351461036457600050610388565b60406000600060006110005afa503d6000556101005160006000615a17f5503d6001555b6160a760025500fe600160000360002000"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 19, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(code=bytes.fromhex("5000")),
                callee_1: Account(code=bytes.fromhex("600056")),
                callee_2: Account(code=bytes.fromhex("6001600157")),
                callee_3: Account(code=bytes.fromhex("fe00")),
                callee_4: Account(
                    code=bytes.fromhex(
                        "600260016000030460005260016000510160205260406000f300"
                    )
                ),
                contract: Account(
                    storage={0: 64, 2: 24743},
                    code=bytes.fromhex(
                        "6000602435146100115760005061001f565b600980610391600039610100525b61ff006024351461003257600050610046565b6000600060006000600061ff005af1610100525b610200602435146100595760005061006d565b605060005360006001600001536002610100525b61030060243514610080576000506100a4565b60606000536000600160000153605660026000015360006002600001536004610100525b610400602435146100b7576000506100eb565b6060600053600160016000015360606002600001536001600360000153605760046000015360006005600001536006610100525b610500602435146100fe57600050610112565b60fe60005360006001600001536002610100525b60006024351460f1600435141661012b57600050610155565b604060006000600060006110005af1503d600055604060006000600060006110006000f1503d6001555b60006024351160f1600435141661016e5760005061019c565b604060006000600060006110005af1503d60005560406000600060006000602435620f00005a03f1503d6001555b60006024351460f260043514166101b5576000506101df565b604060006000600060006110005af2503d600055604060006000600060006110006000f2503d6001555b60006024351160f260043514166101f857600050610221565b604060006000600060006110005af1503d600055604060006000600060006024355af2503d6001555b60006024351460f4600435141661023a57600050610260565b60406000600060006110005af4503d60005560406000600060006110006000f4503d6001555b60006024351160f46004351416610279576000506102a0565b604060006000600060006110005af1503d60005560406000600060006024355af4503d6001555b60006024351460fa60043514166102b9576000506102df565b60406000600060006110005afa503d60005560406000600060006110006000fa503d6001555b60006024351160fa60043514166102f85760005061031f565b604060006000600060006110005af1503d60005560406000600060006024355afa503d6001555b60f06004351461033157600050610352565b60406000600060006110005afa503d6000556101005160006000f0503d6001555b60f56004351461036457600050610388565b60406000600060006110005afa503d6000556101005160006000615a17f5503d6001555b6160a760025500fe600160000360002000"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 1, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(code=bytes.fromhex("5000")),
                callee_1: Account(code=bytes.fromhex("600056")),
                callee_2: Account(code=bytes.fromhex("6001600157")),
                callee_3: Account(code=bytes.fromhex("fe00")),
                callee_4: Account(
                    code=bytes.fromhex(
                        "600260016000030460005260016000510160205260406000f300"
                    )
                ),
                contract: Account(
                    storage={0: 64, 2: 24743},
                    code=bytes.fromhex(
                        "6000602435146100115760005061001f565b600980610391600039610100525b61ff006024351461003257600050610046565b6000600060006000600061ff005af1610100525b610200602435146100595760005061006d565b605060005360006001600001536002610100525b61030060243514610080576000506100a4565b60606000536000600160000153605660026000015360006002600001536004610100525b610400602435146100b7576000506100eb565b6060600053600160016000015360606002600001536001600360000153605760046000015360006005600001536006610100525b610500602435146100fe57600050610112565b60fe60005360006001600001536002610100525b60006024351460f1600435141661012b57600050610155565b604060006000600060006110005af1503d600055604060006000600060006110006000f1503d6001555b60006024351160f1600435141661016e5760005061019c565b604060006000600060006110005af1503d60005560406000600060006000602435620f00005a03f1503d6001555b60006024351460f260043514166101b5576000506101df565b604060006000600060006110005af2503d600055604060006000600060006110006000f2503d6001555b60006024351160f260043514166101f857600050610221565b604060006000600060006110005af1503d600055604060006000600060006024355af2503d6001555b60006024351460f4600435141661023a57600050610260565b60406000600060006110005af4503d60005560406000600060006110006000f4503d6001555b60006024351160f46004351416610279576000506102a0565b604060006000600060006110005af1503d60005560406000600060006024355af4503d6001555b60006024351460fa60043514166102b9576000506102df565b60406000600060006110005afa503d60005560406000600060006110006000fa503d6001555b60006024351160fa60043514166102f85760005061031f565b604060006000600060006110005af1503d60005560406000600060006024355afa503d6001555b60f06004351461033157600050610352565b60406000600060006110005afa503d6000556101005160006000f0503d6001555b60f56004351461036457600050610388565b60406000600060006110005afa503d6000556101005160006000615a17f5503d6001555b6160a760025500fe600160000360002000"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 20, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(code=bytes.fromhex("5000")),
                callee_1: Account(code=bytes.fromhex("600056")),
                callee_2: Account(code=bytes.fromhex("6001600157")),
                callee_3: Account(code=bytes.fromhex("fe00")),
                callee_4: Account(
                    code=bytes.fromhex(
                        "600260016000030460005260016000510160205260406000f300"
                    )
                ),
                contract: Account(
                    storage={0: 64, 2: 24743},
                    code=bytes.fromhex(
                        "6000602435146100115760005061001f565b600980610391600039610100525b61ff006024351461003257600050610046565b6000600060006000600061ff005af1610100525b610200602435146100595760005061006d565b605060005360006001600001536002610100525b61030060243514610080576000506100a4565b60606000536000600160000153605660026000015360006002600001536004610100525b610400602435146100b7576000506100eb565b6060600053600160016000015360606002600001536001600360000153605760046000015360006005600001536006610100525b610500602435146100fe57600050610112565b60fe60005360006001600001536002610100525b60006024351460f1600435141661012b57600050610155565b604060006000600060006110005af1503d600055604060006000600060006110006000f1503d6001555b60006024351160f1600435141661016e5760005061019c565b604060006000600060006110005af1503d60005560406000600060006000602435620f00005a03f1503d6001555b60006024351460f260043514166101b5576000506101df565b604060006000600060006110005af2503d600055604060006000600060006110006000f2503d6001555b60006024351160f260043514166101f857600050610221565b604060006000600060006110005af1503d600055604060006000600060006024355af2503d6001555b60006024351460f4600435141661023a57600050610260565b60406000600060006110005af4503d60005560406000600060006110006000f4503d6001555b60006024351160f46004351416610279576000506102a0565b604060006000600060006110005af1503d60005560406000600060006024355af4503d6001555b60006024351460fa60043514166102b9576000506102df565b60406000600060006110005afa503d60005560406000600060006110006000fa503d6001555b60006024351160fa60043514166102f85760005061031f565b604060006000600060006110005af1503d60005560406000600060006024355afa503d6001555b60f06004351461033157600050610352565b60406000600060006110005afa503d6000556101005160006000f0503d6001555b60f56004351461036457600050610388565b60406000600060006110005afa503d6000556101005160006000615a17f5503d6001555b6160a760025500fe600160000360002000"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 21, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(code=bytes.fromhex("5000")),
                callee_1: Account(code=bytes.fromhex("600056")),
                callee_2: Account(code=bytes.fromhex("6001600157")),
                callee_3: Account(code=bytes.fromhex("fe00")),
                callee_4: Account(
                    code=bytes.fromhex(
                        "600260016000030460005260016000510160205260406000f300"
                    )
                ),
                contract: Account(
                    storage={0: 64, 2: 24743},
                    code=bytes.fromhex(
                        "6000602435146100115760005061001f565b600980610391600039610100525b61ff006024351461003257600050610046565b6000600060006000600061ff005af1610100525b610200602435146100595760005061006d565b605060005360006001600001536002610100525b61030060243514610080576000506100a4565b60606000536000600160000153605660026000015360006002600001536004610100525b610400602435146100b7576000506100eb565b6060600053600160016000015360606002600001536001600360000153605760046000015360006005600001536006610100525b610500602435146100fe57600050610112565b60fe60005360006001600001536002610100525b60006024351460f1600435141661012b57600050610155565b604060006000600060006110005af1503d600055604060006000600060006110006000f1503d6001555b60006024351160f1600435141661016e5760005061019c565b604060006000600060006110005af1503d60005560406000600060006000602435620f00005a03f1503d6001555b60006024351460f260043514166101b5576000506101df565b604060006000600060006110005af2503d600055604060006000600060006110006000f2503d6001555b60006024351160f260043514166101f857600050610221565b604060006000600060006110005af1503d600055604060006000600060006024355af2503d6001555b60006024351460f4600435141661023a57600050610260565b60406000600060006110005af4503d60005560406000600060006110006000f4503d6001555b60006024351160f46004351416610279576000506102a0565b604060006000600060006110005af1503d60005560406000600060006024355af4503d6001555b60006024351460fa60043514166102b9576000506102df565b60406000600060006110005afa503d60005560406000600060006110006000fa503d6001555b60006024351160fa60043514166102f85760005061031f565b604060006000600060006110005af1503d60005560406000600060006024355afa503d6001555b60f06004351461033157600050610352565b60406000600060006110005afa503d6000556101005160006000f0503d6001555b60f56004351461036457600050610388565b60406000600060006110005afa503d6000556101005160006000615a17f5503d6001555b6160a760025500fe600160000360002000"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 22, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(code=bytes.fromhex("5000")),
                callee_1: Account(code=bytes.fromhex("600056")),
                callee_2: Account(code=bytes.fromhex("6001600157")),
                callee_3: Account(code=bytes.fromhex("fe00")),
                callee_4: Account(
                    code=bytes.fromhex(
                        "600260016000030460005260016000510160205260406000f300"
                    )
                ),
                contract: Account(
                    storage={0: 64, 2: 24743},
                    code=bytes.fromhex(
                        "6000602435146100115760005061001f565b600980610391600039610100525b61ff006024351461003257600050610046565b6000600060006000600061ff005af1610100525b610200602435146100595760005061006d565b605060005360006001600001536002610100525b61030060243514610080576000506100a4565b60606000536000600160000153605660026000015360006002600001536004610100525b610400602435146100b7576000506100eb565b6060600053600160016000015360606002600001536001600360000153605760046000015360006005600001536006610100525b610500602435146100fe57600050610112565b60fe60005360006001600001536002610100525b60006024351460f1600435141661012b57600050610155565b604060006000600060006110005af1503d600055604060006000600060006110006000f1503d6001555b60006024351160f1600435141661016e5760005061019c565b604060006000600060006110005af1503d60005560406000600060006000602435620f00005a03f1503d6001555b60006024351460f260043514166101b5576000506101df565b604060006000600060006110005af2503d600055604060006000600060006110006000f2503d6001555b60006024351160f260043514166101f857600050610221565b604060006000600060006110005af1503d600055604060006000600060006024355af2503d6001555b60006024351460f4600435141661023a57600050610260565b60406000600060006110005af4503d60005560406000600060006110006000f4503d6001555b60006024351160f46004351416610279576000506102a0565b604060006000600060006110005af1503d60005560406000600060006024355af4503d6001555b60006024351460fa60043514166102b9576000506102df565b60406000600060006110005afa503d60005560406000600060006110006000fa503d6001555b60006024351160fa60043514166102f85760005061031f565b604060006000600060006110005af1503d60005560406000600060006024355afa503d6001555b60f06004351461033157600050610352565b60406000600060006110005afa503d6000556101005160006000f0503d6001555b60f56004351461036457600050610388565b60406000600060006110005afa503d6000556101005160006000615a17f5503d6001555b6160a760025500fe600160000360002000"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 23, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(code=bytes.fromhex("5000")),
                callee_1: Account(code=bytes.fromhex("600056")),
                callee_2: Account(code=bytes.fromhex("6001600157")),
                callee_3: Account(code=bytes.fromhex("fe00")),
                callee_4: Account(
                    code=bytes.fromhex(
                        "600260016000030460005260016000510160205260406000f300"
                    )
                ),
                contract: Account(
                    storage={0: 64, 2: 24743},
                    code=bytes.fromhex(
                        "6000602435146100115760005061001f565b600980610391600039610100525b61ff006024351461003257600050610046565b6000600060006000600061ff005af1610100525b610200602435146100595760005061006d565b605060005360006001600001536002610100525b61030060243514610080576000506100a4565b60606000536000600160000153605660026000015360006002600001536004610100525b610400602435146100b7576000506100eb565b6060600053600160016000015360606002600001536001600360000153605760046000015360006005600001536006610100525b610500602435146100fe57600050610112565b60fe60005360006001600001536002610100525b60006024351460f1600435141661012b57600050610155565b604060006000600060006110005af1503d600055604060006000600060006110006000f1503d6001555b60006024351160f1600435141661016e5760005061019c565b604060006000600060006110005af1503d60005560406000600060006000602435620f00005a03f1503d6001555b60006024351460f260043514166101b5576000506101df565b604060006000600060006110005af2503d600055604060006000600060006110006000f2503d6001555b60006024351160f260043514166101f857600050610221565b604060006000600060006110005af1503d600055604060006000600060006024355af2503d6001555b60006024351460f4600435141661023a57600050610260565b60406000600060006110005af4503d60005560406000600060006110006000f4503d6001555b60006024351160f46004351416610279576000506102a0565b604060006000600060006110005af1503d60005560406000600060006024355af4503d6001555b60006024351460fa60043514166102b9576000506102df565b60406000600060006110005afa503d60005560406000600060006110006000fa503d6001555b60006024351160fa60043514166102f85760005061031f565b604060006000600060006110005af1503d60005560406000600060006024355afa503d6001555b60f06004351461033157600050610352565b60406000600060006110005afa503d6000556101005160006000f0503d6001555b60f56004351461036457600050610388565b60406000600060006110005afa503d6000556101005160006000615a17f5503d6001555b6160a760025500fe600160000360002000"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 24, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(code=bytes.fromhex("5000")),
                callee_1: Account(code=bytes.fromhex("600056")),
                callee_2: Account(code=bytes.fromhex("6001600157")),
                callee_3: Account(code=bytes.fromhex("fe00")),
                callee_4: Account(
                    code=bytes.fromhex(
                        "600260016000030460005260016000510160205260406000f300"
                    )
                ),
                contract: Account(
                    storage={0: 64, 2: 24743},
                    code=bytes.fromhex(
                        "6000602435146100115760005061001f565b600980610391600039610100525b61ff006024351461003257600050610046565b6000600060006000600061ff005af1610100525b610200602435146100595760005061006d565b605060005360006001600001536002610100525b61030060243514610080576000506100a4565b60606000536000600160000153605660026000015360006002600001536004610100525b610400602435146100b7576000506100eb565b6060600053600160016000015360606002600001536001600360000153605760046000015360006005600001536006610100525b610500602435146100fe57600050610112565b60fe60005360006001600001536002610100525b60006024351460f1600435141661012b57600050610155565b604060006000600060006110005af1503d600055604060006000600060006110006000f1503d6001555b60006024351160f1600435141661016e5760005061019c565b604060006000600060006110005af1503d60005560406000600060006000602435620f00005a03f1503d6001555b60006024351460f260043514166101b5576000506101df565b604060006000600060006110005af2503d600055604060006000600060006110006000f2503d6001555b60006024351160f260043514166101f857600050610221565b604060006000600060006110005af1503d600055604060006000600060006024355af2503d6001555b60006024351460f4600435141661023a57600050610260565b60406000600060006110005af4503d60005560406000600060006110006000f4503d6001555b60006024351160f46004351416610279576000506102a0565b604060006000600060006110005af1503d60005560406000600060006024355af4503d6001555b60006024351460fa60043514166102b9576000506102df565b60406000600060006110005afa503d60005560406000600060006110006000fa503d6001555b60006024351160fa60043514166102f85760005061031f565b604060006000600060006110005af1503d60005560406000600060006024355afa503d6001555b60f06004351461033157600050610352565b60406000600060006110005afa503d6000556101005160006000f0503d6001555b60f56004351461036457600050610388565b60406000600060006110005afa503d6000556101005160006000615a17f5503d6001555b6160a760025500fe600160000360002000"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 25, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(code=bytes.fromhex("5000")),
                callee_1: Account(code=bytes.fromhex("600056")),
                callee_2: Account(code=bytes.fromhex("6001600157")),
                callee_3: Account(code=bytes.fromhex("fe00")),
                callee_4: Account(
                    code=bytes.fromhex(
                        "600260016000030460005260016000510160205260406000f300"
                    )
                ),
                contract: Account(
                    storage={0: 64, 2: 24743},
                    code=bytes.fromhex(
                        "6000602435146100115760005061001f565b600980610391600039610100525b61ff006024351461003257600050610046565b6000600060006000600061ff005af1610100525b610200602435146100595760005061006d565b605060005360006001600001536002610100525b61030060243514610080576000506100a4565b60606000536000600160000153605660026000015360006002600001536004610100525b610400602435146100b7576000506100eb565b6060600053600160016000015360606002600001536001600360000153605760046000015360006005600001536006610100525b610500602435146100fe57600050610112565b60fe60005360006001600001536002610100525b60006024351460f1600435141661012b57600050610155565b604060006000600060006110005af1503d600055604060006000600060006110006000f1503d6001555b60006024351160f1600435141661016e5760005061019c565b604060006000600060006110005af1503d60005560406000600060006000602435620f00005a03f1503d6001555b60006024351460f260043514166101b5576000506101df565b604060006000600060006110005af2503d600055604060006000600060006110006000f2503d6001555b60006024351160f260043514166101f857600050610221565b604060006000600060006110005af1503d600055604060006000600060006024355af2503d6001555b60006024351460f4600435141661023a57600050610260565b60406000600060006110005af4503d60005560406000600060006110006000f4503d6001555b60006024351160f46004351416610279576000506102a0565b604060006000600060006110005af1503d60005560406000600060006024355af4503d6001555b60006024351460fa60043514166102b9576000506102df565b60406000600060006110005afa503d60005560406000600060006110006000fa503d6001555b60006024351160fa60043514166102f85760005061031f565b604060006000600060006110005af1503d60005560406000600060006024355afa503d6001555b60f06004351461033157600050610352565b60406000600060006110005afa503d6000556101005160006000f0503d6001555b60f56004351461036457600050610388565b60406000600060006110005afa503d6000556101005160006000615a17f5503d6001555b6160a760025500fe600160000360002000"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 26, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(code=bytes.fromhex("5000")),
                callee_1: Account(code=bytes.fromhex("600056")),
                callee_2: Account(code=bytes.fromhex("6001600157")),
                callee_3: Account(code=bytes.fromhex("fe00")),
                callee_4: Account(
                    code=bytes.fromhex(
                        "600260016000030460005260016000510160205260406000f300"
                    )
                ),
                contract: Account(
                    storage={0: 64, 2: 24743},
                    code=bytes.fromhex(
                        "6000602435146100115760005061001f565b600980610391600039610100525b61ff006024351461003257600050610046565b6000600060006000600061ff005af1610100525b610200602435146100595760005061006d565b605060005360006001600001536002610100525b61030060243514610080576000506100a4565b60606000536000600160000153605660026000015360006002600001536004610100525b610400602435146100b7576000506100eb565b6060600053600160016000015360606002600001536001600360000153605760046000015360006005600001536006610100525b610500602435146100fe57600050610112565b60fe60005360006001600001536002610100525b60006024351460f1600435141661012b57600050610155565b604060006000600060006110005af1503d600055604060006000600060006110006000f1503d6001555b60006024351160f1600435141661016e5760005061019c565b604060006000600060006110005af1503d60005560406000600060006000602435620f00005a03f1503d6001555b60006024351460f260043514166101b5576000506101df565b604060006000600060006110005af2503d600055604060006000600060006110006000f2503d6001555b60006024351160f260043514166101f857600050610221565b604060006000600060006110005af1503d600055604060006000600060006024355af2503d6001555b60006024351460f4600435141661023a57600050610260565b60406000600060006110005af4503d60005560406000600060006110006000f4503d6001555b60006024351160f46004351416610279576000506102a0565b604060006000600060006110005af1503d60005560406000600060006024355af4503d6001555b60006024351460fa60043514166102b9576000506102df565b60406000600060006110005afa503d60005560406000600060006110006000fa503d6001555b60006024351160fa60043514166102f85760005061031f565b604060006000600060006110005af1503d60005560406000600060006024355afa503d6001555b60f06004351461033157600050610352565b60406000600060006110005afa503d6000556101005160006000f0503d6001555b60f56004351461036457600050610388565b60406000600060006110005afa503d6000556101005160006000615a17f5503d6001555b6160a760025500fe600160000360002000"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 27, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(code=bytes.fromhex("5000")),
                callee_1: Account(code=bytes.fromhex("600056")),
                callee_2: Account(code=bytes.fromhex("6001600157")),
                callee_3: Account(code=bytes.fromhex("fe00")),
                callee_4: Account(
                    code=bytes.fromhex(
                        "600260016000030460005260016000510160205260406000f300"
                    )
                ),
                contract: Account(
                    storage={0: 64, 2: 24743},
                    code=bytes.fromhex(
                        "6000602435146100115760005061001f565b600980610391600039610100525b61ff006024351461003257600050610046565b6000600060006000600061ff005af1610100525b610200602435146100595760005061006d565b605060005360006001600001536002610100525b61030060243514610080576000506100a4565b60606000536000600160000153605660026000015360006002600001536004610100525b610400602435146100b7576000506100eb565b6060600053600160016000015360606002600001536001600360000153605760046000015360006005600001536006610100525b610500602435146100fe57600050610112565b60fe60005360006001600001536002610100525b60006024351460f1600435141661012b57600050610155565b604060006000600060006110005af1503d600055604060006000600060006110006000f1503d6001555b60006024351160f1600435141661016e5760005061019c565b604060006000600060006110005af1503d60005560406000600060006000602435620f00005a03f1503d6001555b60006024351460f260043514166101b5576000506101df565b604060006000600060006110005af2503d600055604060006000600060006110006000f2503d6001555b60006024351160f260043514166101f857600050610221565b604060006000600060006110005af1503d600055604060006000600060006024355af2503d6001555b60006024351460f4600435141661023a57600050610260565b60406000600060006110005af4503d60005560406000600060006110006000f4503d6001555b60006024351160f46004351416610279576000506102a0565b604060006000600060006110005af1503d60005560406000600060006024355af4503d6001555b60006024351460fa60043514166102b9576000506102df565b60406000600060006110005afa503d60005560406000600060006110006000fa503d6001555b60006024351160fa60043514166102f85760005061031f565b604060006000600060006110005af1503d60005560406000600060006024355afa503d6001555b60f06004351461033157600050610352565b60406000600060006110005afa503d6000556101005160006000f0503d6001555b60f56004351461036457600050610388565b60406000600060006110005afa503d6000556101005160006000615a17f5503d6001555b6160a760025500fe600160000360002000"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 28, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(code=bytes.fromhex("5000")),
                callee_1: Account(code=bytes.fromhex("600056")),
                callee_2: Account(code=bytes.fromhex("6001600157")),
                callee_3: Account(code=bytes.fromhex("fe00")),
                callee_4: Account(
                    code=bytes.fromhex(
                        "600260016000030460005260016000510160205260406000f300"
                    )
                ),
                contract: Account(
                    storage={0: 64, 2: 24743},
                    code=bytes.fromhex(
                        "6000602435146100115760005061001f565b600980610391600039610100525b61ff006024351461003257600050610046565b6000600060006000600061ff005af1610100525b610200602435146100595760005061006d565b605060005360006001600001536002610100525b61030060243514610080576000506100a4565b60606000536000600160000153605660026000015360006002600001536004610100525b610400602435146100b7576000506100eb565b6060600053600160016000015360606002600001536001600360000153605760046000015360006005600001536006610100525b610500602435146100fe57600050610112565b60fe60005360006001600001536002610100525b60006024351460f1600435141661012b57600050610155565b604060006000600060006110005af1503d600055604060006000600060006110006000f1503d6001555b60006024351160f1600435141661016e5760005061019c565b604060006000600060006110005af1503d60005560406000600060006000602435620f00005a03f1503d6001555b60006024351460f260043514166101b5576000506101df565b604060006000600060006110005af2503d600055604060006000600060006110006000f2503d6001555b60006024351160f260043514166101f857600050610221565b604060006000600060006110005af1503d600055604060006000600060006024355af2503d6001555b60006024351460f4600435141661023a57600050610260565b60406000600060006110005af4503d60005560406000600060006110006000f4503d6001555b60006024351160f46004351416610279576000506102a0565b604060006000600060006110005af1503d60005560406000600060006024355af4503d6001555b60006024351460fa60043514166102b9576000506102df565b60406000600060006110005afa503d60005560406000600060006110006000fa503d6001555b60006024351160fa60043514166102f85760005061031f565b604060006000600060006110005af1503d60005560406000600060006024355afa503d6001555b60f06004351461033157600050610352565b60406000600060006110005afa503d6000556101005160006000f0503d6001555b60f56004351461036457600050610388565b60406000600060006110005afa503d6000556101005160006000615a17f5503d6001555b6160a760025500fe600160000360002000"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 29, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(code=bytes.fromhex("5000")),
                callee_1: Account(code=bytes.fromhex("600056")),
                callee_2: Account(code=bytes.fromhex("6001600157")),
                callee_3: Account(code=bytes.fromhex("fe00")),
                callee_4: Account(
                    code=bytes.fromhex(
                        "600260016000030460005260016000510160205260406000f300"
                    )
                ),
                contract: Account(
                    storage={0: 64, 2: 24743},
                    code=bytes.fromhex(
                        "6000602435146100115760005061001f565b600980610391600039610100525b61ff006024351461003257600050610046565b6000600060006000600061ff005af1610100525b610200602435146100595760005061006d565b605060005360006001600001536002610100525b61030060243514610080576000506100a4565b60606000536000600160000153605660026000015360006002600001536004610100525b610400602435146100b7576000506100eb565b6060600053600160016000015360606002600001536001600360000153605760046000015360006005600001536006610100525b610500602435146100fe57600050610112565b60fe60005360006001600001536002610100525b60006024351460f1600435141661012b57600050610155565b604060006000600060006110005af1503d600055604060006000600060006110006000f1503d6001555b60006024351160f1600435141661016e5760005061019c565b604060006000600060006110005af1503d60005560406000600060006000602435620f00005a03f1503d6001555b60006024351460f260043514166101b5576000506101df565b604060006000600060006110005af2503d600055604060006000600060006110006000f2503d6001555b60006024351160f260043514166101f857600050610221565b604060006000600060006110005af1503d600055604060006000600060006024355af2503d6001555b60006024351460f4600435141661023a57600050610260565b60406000600060006110005af4503d60005560406000600060006110006000f4503d6001555b60006024351160f46004351416610279576000506102a0565b604060006000600060006110005af1503d60005560406000600060006024355af4503d6001555b60006024351460fa60043514166102b9576000506102df565b60406000600060006110005afa503d60005560406000600060006110006000fa503d6001555b60006024351160fa60043514166102f85760005061031f565b604060006000600060006110005af1503d60005560406000600060006024355afa503d6001555b60f06004351461033157600050610352565b60406000600060006110005afa503d6000556101005160006000f0503d6001555b60f56004351461036457600050610388565b60406000600060006110005afa503d6000556101005160006000615a17f5503d6001555b6160a760025500fe600160000360002000"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 2, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(code=bytes.fromhex("5000")),
                callee_1: Account(code=bytes.fromhex("600056")),
                callee_2: Account(code=bytes.fromhex("6001600157")),
                callee_3: Account(code=bytes.fromhex("fe00")),
                callee_4: Account(
                    code=bytes.fromhex(
                        "600260016000030460005260016000510160205260406000f300"
                    )
                ),
                contract: Account(
                    storage={0: 64, 2: 24743},
                    code=bytes.fromhex(
                        "6000602435146100115760005061001f565b600980610391600039610100525b61ff006024351461003257600050610046565b6000600060006000600061ff005af1610100525b610200602435146100595760005061006d565b605060005360006001600001536002610100525b61030060243514610080576000506100a4565b60606000536000600160000153605660026000015360006002600001536004610100525b610400602435146100b7576000506100eb565b6060600053600160016000015360606002600001536001600360000153605760046000015360006005600001536006610100525b610500602435146100fe57600050610112565b60fe60005360006001600001536002610100525b60006024351460f1600435141661012b57600050610155565b604060006000600060006110005af1503d600055604060006000600060006110006000f1503d6001555b60006024351160f1600435141661016e5760005061019c565b604060006000600060006110005af1503d60005560406000600060006000602435620f00005a03f1503d6001555b60006024351460f260043514166101b5576000506101df565b604060006000600060006110005af2503d600055604060006000600060006110006000f2503d6001555b60006024351160f260043514166101f857600050610221565b604060006000600060006110005af1503d600055604060006000600060006024355af2503d6001555b60006024351460f4600435141661023a57600050610260565b60406000600060006110005af4503d60005560406000600060006110006000f4503d6001555b60006024351160f46004351416610279576000506102a0565b604060006000600060006110005af1503d60005560406000600060006024355af4503d6001555b60006024351460fa60043514166102b9576000506102df565b60406000600060006110005afa503d60005560406000600060006110006000fa503d6001555b60006024351160fa60043514166102f85760005061031f565b604060006000600060006110005af1503d60005560406000600060006024355afa503d6001555b60f06004351461033157600050610352565b60406000600060006110005afa503d6000556101005160006000f0503d6001555b60f56004351461036457600050610388565b60406000600060006110005afa503d6000556101005160006000615a17f5503d6001555b6160a760025500fe600160000360002000"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 30, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(code=bytes.fromhex("5000")),
                callee_1: Account(code=bytes.fromhex("600056")),
                callee_2: Account(code=bytes.fromhex("6001600157")),
                callee_3: Account(code=bytes.fromhex("fe00")),
                callee_4: Account(
                    code=bytes.fromhex(
                        "600260016000030460005260016000510160205260406000f300"
                    )
                ),
                contract: Account(
                    storage={0: 64, 2: 24743},
                    code=bytes.fromhex(
                        "6000602435146100115760005061001f565b600980610391600039610100525b61ff006024351461003257600050610046565b6000600060006000600061ff005af1610100525b610200602435146100595760005061006d565b605060005360006001600001536002610100525b61030060243514610080576000506100a4565b60606000536000600160000153605660026000015360006002600001536004610100525b610400602435146100b7576000506100eb565b6060600053600160016000015360606002600001536001600360000153605760046000015360006005600001536006610100525b610500602435146100fe57600050610112565b60fe60005360006001600001536002610100525b60006024351460f1600435141661012b57600050610155565b604060006000600060006110005af1503d600055604060006000600060006110006000f1503d6001555b60006024351160f1600435141661016e5760005061019c565b604060006000600060006110005af1503d60005560406000600060006000602435620f00005a03f1503d6001555b60006024351460f260043514166101b5576000506101df565b604060006000600060006110005af2503d600055604060006000600060006110006000f2503d6001555b60006024351160f260043514166101f857600050610221565b604060006000600060006110005af1503d600055604060006000600060006024355af2503d6001555b60006024351460f4600435141661023a57600050610260565b60406000600060006110005af4503d60005560406000600060006110006000f4503d6001555b60006024351160f46004351416610279576000506102a0565b604060006000600060006110005af1503d60005560406000600060006024355af4503d6001555b60006024351460fa60043514166102b9576000506102df565b60406000600060006110005afa503d60005560406000600060006110006000fa503d6001555b60006024351160fa60043514166102f85760005061031f565b604060006000600060006110005af1503d60005560406000600060006024355afa503d6001555b60f06004351461033157600050610352565b60406000600060006110005afa503d6000556101005160006000f0503d6001555b60f56004351461036457600050610388565b60406000600060006110005afa503d6000556101005160006000615a17f5503d6001555b6160a760025500fe600160000360002000"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 31, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(code=bytes.fromhex("5000")),
                callee_1: Account(code=bytes.fromhex("600056")),
                callee_2: Account(code=bytes.fromhex("6001600157")),
                callee_3: Account(code=bytes.fromhex("fe00")),
                callee_4: Account(
                    code=bytes.fromhex(
                        "600260016000030460005260016000510160205260406000f300"
                    )
                ),
                contract: Account(
                    storage={0: 64, 2: 24743},
                    code=bytes.fromhex(
                        "6000602435146100115760005061001f565b600980610391600039610100525b61ff006024351461003257600050610046565b6000600060006000600061ff005af1610100525b610200602435146100595760005061006d565b605060005360006001600001536002610100525b61030060243514610080576000506100a4565b60606000536000600160000153605660026000015360006002600001536004610100525b610400602435146100b7576000506100eb565b6060600053600160016000015360606002600001536001600360000153605760046000015360006005600001536006610100525b610500602435146100fe57600050610112565b60fe60005360006001600001536002610100525b60006024351460f1600435141661012b57600050610155565b604060006000600060006110005af1503d600055604060006000600060006110006000f1503d6001555b60006024351160f1600435141661016e5760005061019c565b604060006000600060006110005af1503d60005560406000600060006000602435620f00005a03f1503d6001555b60006024351460f260043514166101b5576000506101df565b604060006000600060006110005af2503d600055604060006000600060006110006000f2503d6001555b60006024351160f260043514166101f857600050610221565b604060006000600060006110005af1503d600055604060006000600060006024355af2503d6001555b60006024351460f4600435141661023a57600050610260565b60406000600060006110005af4503d60005560406000600060006110006000f4503d6001555b60006024351160f46004351416610279576000506102a0565b604060006000600060006110005af1503d60005560406000600060006024355af4503d6001555b60006024351460fa60043514166102b9576000506102df565b60406000600060006110005afa503d60005560406000600060006110006000fa503d6001555b60006024351160fa60043514166102f85760005061031f565b604060006000600060006110005af1503d60005560406000600060006024355afa503d6001555b60f06004351461033157600050610352565b60406000600060006110005afa503d6000556101005160006000f0503d6001555b60f56004351461036457600050610388565b60406000600060006110005afa503d6000556101005160006000615a17f5503d6001555b6160a760025500fe600160000360002000"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 32, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(code=bytes.fromhex("5000")),
                callee_1: Account(code=bytes.fromhex("600056")),
                callee_2: Account(code=bytes.fromhex("6001600157")),
                callee_3: Account(code=bytes.fromhex("fe00")),
                callee_4: Account(
                    code=bytes.fromhex(
                        "600260016000030460005260016000510160205260406000f300"
                    )
                ),
                contract: Account(
                    storage={0: 64, 2: 24743},
                    code=bytes.fromhex(
                        "6000602435146100115760005061001f565b600980610391600039610100525b61ff006024351461003257600050610046565b6000600060006000600061ff005af1610100525b610200602435146100595760005061006d565b605060005360006001600001536002610100525b61030060243514610080576000506100a4565b60606000536000600160000153605660026000015360006002600001536004610100525b610400602435146100b7576000506100eb565b6060600053600160016000015360606002600001536001600360000153605760046000015360006005600001536006610100525b610500602435146100fe57600050610112565b60fe60005360006001600001536002610100525b60006024351460f1600435141661012b57600050610155565b604060006000600060006110005af1503d600055604060006000600060006110006000f1503d6001555b60006024351160f1600435141661016e5760005061019c565b604060006000600060006110005af1503d60005560406000600060006000602435620f00005a03f1503d6001555b60006024351460f260043514166101b5576000506101df565b604060006000600060006110005af2503d600055604060006000600060006110006000f2503d6001555b60006024351160f260043514166101f857600050610221565b604060006000600060006110005af1503d600055604060006000600060006024355af2503d6001555b60006024351460f4600435141661023a57600050610260565b60406000600060006110005af4503d60005560406000600060006110006000f4503d6001555b60006024351160f46004351416610279576000506102a0565b604060006000600060006110005af1503d60005560406000600060006024355af4503d6001555b60006024351460fa60043514166102b9576000506102df565b60406000600060006110005afa503d60005560406000600060006110006000fa503d6001555b60006024351160fa60043514166102f85760005061031f565b604060006000600060006110005af1503d60005560406000600060006024355afa503d6001555b60f06004351461033157600050610352565b60406000600060006110005afa503d6000556101005160006000f0503d6001555b60f56004351461036457600050610388565b60406000600060006110005afa503d6000556101005160006000615a17f5503d6001555b6160a760025500fe600160000360002000"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 33, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(code=bytes.fromhex("5000")),
                callee_1: Account(code=bytes.fromhex("600056")),
                callee_2: Account(code=bytes.fromhex("6001600157")),
                callee_3: Account(code=bytes.fromhex("fe00")),
                callee_4: Account(
                    code=bytes.fromhex(
                        "600260016000030460005260016000510160205260406000f300"
                    )
                ),
                contract: Account(
                    storage={0: 64, 2: 24743},
                    code=bytes.fromhex(
                        "6000602435146100115760005061001f565b600980610391600039610100525b61ff006024351461003257600050610046565b6000600060006000600061ff005af1610100525b610200602435146100595760005061006d565b605060005360006001600001536002610100525b61030060243514610080576000506100a4565b60606000536000600160000153605660026000015360006002600001536004610100525b610400602435146100b7576000506100eb565b6060600053600160016000015360606002600001536001600360000153605760046000015360006005600001536006610100525b610500602435146100fe57600050610112565b60fe60005360006001600001536002610100525b60006024351460f1600435141661012b57600050610155565b604060006000600060006110005af1503d600055604060006000600060006110006000f1503d6001555b60006024351160f1600435141661016e5760005061019c565b604060006000600060006110005af1503d60005560406000600060006000602435620f00005a03f1503d6001555b60006024351460f260043514166101b5576000506101df565b604060006000600060006110005af2503d600055604060006000600060006110006000f2503d6001555b60006024351160f260043514166101f857600050610221565b604060006000600060006110005af1503d600055604060006000600060006024355af2503d6001555b60006024351460f4600435141661023a57600050610260565b60406000600060006110005af4503d60005560406000600060006110006000f4503d6001555b60006024351160f46004351416610279576000506102a0565b604060006000600060006110005af1503d60005560406000600060006024355af4503d6001555b60006024351460fa60043514166102b9576000506102df565b60406000600060006110005afa503d60005560406000600060006110006000fa503d6001555b60006024351160fa60043514166102f85760005061031f565b604060006000600060006110005af1503d60005560406000600060006024355afa503d6001555b60f06004351461033157600050610352565b60406000600060006110005afa503d6000556101005160006000f0503d6001555b60f56004351461036457600050610388565b60406000600060006110005afa503d6000556101005160006000615a17f5503d6001555b6160a760025500fe600160000360002000"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 34, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(code=bytes.fromhex("5000")),
                callee_1: Account(code=bytes.fromhex("600056")),
                callee_2: Account(code=bytes.fromhex("6001600157")),
                callee_3: Account(code=bytes.fromhex("fe00")),
                callee_4: Account(
                    code=bytes.fromhex(
                        "600260016000030460005260016000510160205260406000f300"
                    )
                ),
                contract: Account(
                    storage={0: 64, 2: 24743},
                    code=bytes.fromhex(
                        "6000602435146100115760005061001f565b600980610391600039610100525b61ff006024351461003257600050610046565b6000600060006000600061ff005af1610100525b610200602435146100595760005061006d565b605060005360006001600001536002610100525b61030060243514610080576000506100a4565b60606000536000600160000153605660026000015360006002600001536004610100525b610400602435146100b7576000506100eb565b6060600053600160016000015360606002600001536001600360000153605760046000015360006005600001536006610100525b610500602435146100fe57600050610112565b60fe60005360006001600001536002610100525b60006024351460f1600435141661012b57600050610155565b604060006000600060006110005af1503d600055604060006000600060006110006000f1503d6001555b60006024351160f1600435141661016e5760005061019c565b604060006000600060006110005af1503d60005560406000600060006000602435620f00005a03f1503d6001555b60006024351460f260043514166101b5576000506101df565b604060006000600060006110005af2503d600055604060006000600060006110006000f2503d6001555b60006024351160f260043514166101f857600050610221565b604060006000600060006110005af1503d600055604060006000600060006024355af2503d6001555b60006024351460f4600435141661023a57600050610260565b60406000600060006110005af4503d60005560406000600060006110006000f4503d6001555b60006024351160f46004351416610279576000506102a0565b604060006000600060006110005af1503d60005560406000600060006024355af4503d6001555b60006024351460fa60043514166102b9576000506102df565b60406000600060006110005afa503d60005560406000600060006110006000fa503d6001555b60006024351160fa60043514166102f85760005061031f565b604060006000600060006110005af1503d60005560406000600060006024355afa503d6001555b60f06004351461033157600050610352565b60406000600060006110005afa503d6000556101005160006000f0503d6001555b60f56004351461036457600050610388565b60406000600060006110005afa503d6000556101005160006000615a17f5503d6001555b6160a760025500fe600160000360002000"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 35, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(code=bytes.fromhex("5000")),
                callee_1: Account(code=bytes.fromhex("600056")),
                callee_2: Account(code=bytes.fromhex("6001600157")),
                callee_3: Account(code=bytes.fromhex("fe00")),
                callee_4: Account(
                    code=bytes.fromhex(
                        "600260016000030460005260016000510160205260406000f300"
                    )
                ),
                contract: Account(
                    storage={0: 64, 2: 24743},
                    code=bytes.fromhex(
                        "6000602435146100115760005061001f565b600980610391600039610100525b61ff006024351461003257600050610046565b6000600060006000600061ff005af1610100525b610200602435146100595760005061006d565b605060005360006001600001536002610100525b61030060243514610080576000506100a4565b60606000536000600160000153605660026000015360006002600001536004610100525b610400602435146100b7576000506100eb565b6060600053600160016000015360606002600001536001600360000153605760046000015360006005600001536006610100525b610500602435146100fe57600050610112565b60fe60005360006001600001536002610100525b60006024351460f1600435141661012b57600050610155565b604060006000600060006110005af1503d600055604060006000600060006110006000f1503d6001555b60006024351160f1600435141661016e5760005061019c565b604060006000600060006110005af1503d60005560406000600060006000602435620f00005a03f1503d6001555b60006024351460f260043514166101b5576000506101df565b604060006000600060006110005af2503d600055604060006000600060006110006000f2503d6001555b60006024351160f260043514166101f857600050610221565b604060006000600060006110005af1503d600055604060006000600060006024355af2503d6001555b60006024351460f4600435141661023a57600050610260565b60406000600060006110005af4503d60005560406000600060006110006000f4503d6001555b60006024351160f46004351416610279576000506102a0565b604060006000600060006110005af1503d60005560406000600060006024355af4503d6001555b60006024351460fa60043514166102b9576000506102df565b60406000600060006110005afa503d60005560406000600060006110006000fa503d6001555b60006024351160fa60043514166102f85760005061031f565b604060006000600060006110005af1503d60005560406000600060006024355afa503d6001555b60f06004351461033157600050610352565b60406000600060006110005afa503d6000556101005160006000f0503d6001555b60f56004351461036457600050610388565b60406000600060006110005afa503d6000556101005160006000615a17f5503d6001555b6160a760025500fe600160000360002000"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 3, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(code=bytes.fromhex("5000")),
                callee_1: Account(code=bytes.fromhex("600056")),
                callee_2: Account(code=bytes.fromhex("6001600157")),
                callee_3: Account(code=bytes.fromhex("fe00")),
                callee_4: Account(
                    code=bytes.fromhex(
                        "600260016000030460005260016000510160205260406000f300"
                    )
                ),
                contract: Account(
                    storage={0: 64, 2: 24743},
                    code=bytes.fromhex(
                        "6000602435146100115760005061001f565b600980610391600039610100525b61ff006024351461003257600050610046565b6000600060006000600061ff005af1610100525b610200602435146100595760005061006d565b605060005360006001600001536002610100525b61030060243514610080576000506100a4565b60606000536000600160000153605660026000015360006002600001536004610100525b610400602435146100b7576000506100eb565b6060600053600160016000015360606002600001536001600360000153605760046000015360006005600001536006610100525b610500602435146100fe57600050610112565b60fe60005360006001600001536002610100525b60006024351460f1600435141661012b57600050610155565b604060006000600060006110005af1503d600055604060006000600060006110006000f1503d6001555b60006024351160f1600435141661016e5760005061019c565b604060006000600060006110005af1503d60005560406000600060006000602435620f00005a03f1503d6001555b60006024351460f260043514166101b5576000506101df565b604060006000600060006110005af2503d600055604060006000600060006110006000f2503d6001555b60006024351160f260043514166101f857600050610221565b604060006000600060006110005af1503d600055604060006000600060006024355af2503d6001555b60006024351460f4600435141661023a57600050610260565b60406000600060006110005af4503d60005560406000600060006110006000f4503d6001555b60006024351160f46004351416610279576000506102a0565b604060006000600060006110005af1503d60005560406000600060006024355af4503d6001555b60006024351460fa60043514166102b9576000506102df565b60406000600060006110005afa503d60005560406000600060006110006000fa503d6001555b60006024351160fa60043514166102f85760005061031f565b604060006000600060006110005af1503d60005560406000600060006024355afa503d6001555b60f06004351461033157600050610352565b60406000600060006110005afa503d6000556101005160006000f0503d6001555b60f56004351461036457600050610388565b60406000600060006110005afa503d6000556101005160006000615a17f5503d6001555b6160a760025500fe600160000360002000"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 4, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(code=bytes.fromhex("5000")),
                callee_1: Account(code=bytes.fromhex("600056")),
                callee_2: Account(code=bytes.fromhex("6001600157")),
                callee_3: Account(code=bytes.fromhex("fe00")),
                callee_4: Account(
                    code=bytes.fromhex(
                        "600260016000030460005260016000510160205260406000f300"
                    )
                ),
                contract: Account(
                    storage={0: 64, 2: 24743},
                    code=bytes.fromhex(
                        "6000602435146100115760005061001f565b600980610391600039610100525b61ff006024351461003257600050610046565b6000600060006000600061ff005af1610100525b610200602435146100595760005061006d565b605060005360006001600001536002610100525b61030060243514610080576000506100a4565b60606000536000600160000153605660026000015360006002600001536004610100525b610400602435146100b7576000506100eb565b6060600053600160016000015360606002600001536001600360000153605760046000015360006005600001536006610100525b610500602435146100fe57600050610112565b60fe60005360006001600001536002610100525b60006024351460f1600435141661012b57600050610155565b604060006000600060006110005af1503d600055604060006000600060006110006000f1503d6001555b60006024351160f1600435141661016e5760005061019c565b604060006000600060006110005af1503d60005560406000600060006000602435620f00005a03f1503d6001555b60006024351460f260043514166101b5576000506101df565b604060006000600060006110005af2503d600055604060006000600060006110006000f2503d6001555b60006024351160f260043514166101f857600050610221565b604060006000600060006110005af1503d600055604060006000600060006024355af2503d6001555b60006024351460f4600435141661023a57600050610260565b60406000600060006110005af4503d60005560406000600060006110006000f4503d6001555b60006024351160f46004351416610279576000506102a0565b604060006000600060006110005af1503d60005560406000600060006024355af4503d6001555b60006024351460fa60043514166102b9576000506102df565b60406000600060006110005afa503d60005560406000600060006110006000fa503d6001555b60006024351160fa60043514166102f85760005061031f565b604060006000600060006110005af1503d60005560406000600060006024355afa503d6001555b60f06004351461033157600050610352565b60406000600060006110005afa503d6000556101005160006000f0503d6001555b60f56004351461036457600050610388565b60406000600060006110005afa503d6000556101005160006000615a17f5503d6001555b6160a760025500fe600160000360002000"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 5, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(code=bytes.fromhex("5000")),
                callee_1: Account(code=bytes.fromhex("600056")),
                callee_2: Account(code=bytes.fromhex("6001600157")),
                callee_3: Account(code=bytes.fromhex("fe00")),
                callee_4: Account(
                    code=bytes.fromhex(
                        "600260016000030460005260016000510160205260406000f300"
                    )
                ),
                contract: Account(
                    storage={0: 64, 2: 24743},
                    code=bytes.fromhex(
                        "6000602435146100115760005061001f565b600980610391600039610100525b61ff006024351461003257600050610046565b6000600060006000600061ff005af1610100525b610200602435146100595760005061006d565b605060005360006001600001536002610100525b61030060243514610080576000506100a4565b60606000536000600160000153605660026000015360006002600001536004610100525b610400602435146100b7576000506100eb565b6060600053600160016000015360606002600001536001600360000153605760046000015360006005600001536006610100525b610500602435146100fe57600050610112565b60fe60005360006001600001536002610100525b60006024351460f1600435141661012b57600050610155565b604060006000600060006110005af1503d600055604060006000600060006110006000f1503d6001555b60006024351160f1600435141661016e5760005061019c565b604060006000600060006110005af1503d60005560406000600060006000602435620f00005a03f1503d6001555b60006024351460f260043514166101b5576000506101df565b604060006000600060006110005af2503d600055604060006000600060006110006000f2503d6001555b60006024351160f260043514166101f857600050610221565b604060006000600060006110005af1503d600055604060006000600060006024355af2503d6001555b60006024351460f4600435141661023a57600050610260565b60406000600060006110005af4503d60005560406000600060006110006000f4503d6001555b60006024351160f46004351416610279576000506102a0565b604060006000600060006110005af1503d60005560406000600060006024355af4503d6001555b60006024351460fa60043514166102b9576000506102df565b60406000600060006110005afa503d60005560406000600060006110006000fa503d6001555b60006024351160fa60043514166102f85760005061031f565b604060006000600060006110005af1503d60005560406000600060006024355afa503d6001555b60f06004351461033157600050610352565b60406000600060006110005afa503d6000556101005160006000f0503d6001555b60f56004351461036457600050610388565b60406000600060006110005afa503d6000556101005160006000615a17f5503d6001555b6160a760025500fe600160000360002000"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 6, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(code=bytes.fromhex("5000")),
                callee_1: Account(code=bytes.fromhex("600056")),
                callee_2: Account(code=bytes.fromhex("6001600157")),
                callee_3: Account(code=bytes.fromhex("fe00")),
                callee_4: Account(
                    code=bytes.fromhex(
                        "600260016000030460005260016000510160205260406000f300"
                    )
                ),
                contract: Account(
                    storage={0: 64, 2: 24743},
                    code=bytes.fromhex(
                        "6000602435146100115760005061001f565b600980610391600039610100525b61ff006024351461003257600050610046565b6000600060006000600061ff005af1610100525b610200602435146100595760005061006d565b605060005360006001600001536002610100525b61030060243514610080576000506100a4565b60606000536000600160000153605660026000015360006002600001536004610100525b610400602435146100b7576000506100eb565b6060600053600160016000015360606002600001536001600360000153605760046000015360006005600001536006610100525b610500602435146100fe57600050610112565b60fe60005360006001600001536002610100525b60006024351460f1600435141661012b57600050610155565b604060006000600060006110005af1503d600055604060006000600060006110006000f1503d6001555b60006024351160f1600435141661016e5760005061019c565b604060006000600060006110005af1503d60005560406000600060006000602435620f00005a03f1503d6001555b60006024351460f260043514166101b5576000506101df565b604060006000600060006110005af2503d600055604060006000600060006110006000f2503d6001555b60006024351160f260043514166101f857600050610221565b604060006000600060006110005af1503d600055604060006000600060006024355af2503d6001555b60006024351460f4600435141661023a57600050610260565b60406000600060006110005af4503d60005560406000600060006110006000f4503d6001555b60006024351160f46004351416610279576000506102a0565b604060006000600060006110005af1503d60005560406000600060006024355af4503d6001555b60006024351460fa60043514166102b9576000506102df565b60406000600060006110005afa503d60005560406000600060006110006000fa503d6001555b60006024351160fa60043514166102f85760005061031f565b604060006000600060006110005af1503d60005560406000600060006024355afa503d6001555b60f06004351461033157600050610352565b60406000600060006110005afa503d6000556101005160006000f0503d6001555b60f56004351461036457600050610388565b60406000600060006110005afa503d6000556101005160006000615a17f5503d6001555b6160a760025500fe600160000360002000"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 7, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(code=bytes.fromhex("5000")),
                callee_1: Account(code=bytes.fromhex("600056")),
                callee_2: Account(code=bytes.fromhex("6001600157")),
                callee_3: Account(code=bytes.fromhex("fe00")),
                callee_4: Account(
                    code=bytes.fromhex(
                        "600260016000030460005260016000510160205260406000f300"
                    )
                ),
                contract: Account(
                    storage={0: 64, 2: 24743},
                    code=bytes.fromhex(
                        "6000602435146100115760005061001f565b600980610391600039610100525b61ff006024351461003257600050610046565b6000600060006000600061ff005af1610100525b610200602435146100595760005061006d565b605060005360006001600001536002610100525b61030060243514610080576000506100a4565b60606000536000600160000153605660026000015360006002600001536004610100525b610400602435146100b7576000506100eb565b6060600053600160016000015360606002600001536001600360000153605760046000015360006005600001536006610100525b610500602435146100fe57600050610112565b60fe60005360006001600001536002610100525b60006024351460f1600435141661012b57600050610155565b604060006000600060006110005af1503d600055604060006000600060006110006000f1503d6001555b60006024351160f1600435141661016e5760005061019c565b604060006000600060006110005af1503d60005560406000600060006000602435620f00005a03f1503d6001555b60006024351460f260043514166101b5576000506101df565b604060006000600060006110005af2503d600055604060006000600060006110006000f2503d6001555b60006024351160f260043514166101f857600050610221565b604060006000600060006110005af1503d600055604060006000600060006024355af2503d6001555b60006024351460f4600435141661023a57600050610260565b60406000600060006110005af4503d60005560406000600060006110006000f4503d6001555b60006024351160f46004351416610279576000506102a0565b604060006000600060006110005af1503d60005560406000600060006024355af4503d6001555b60006024351460fa60043514166102b9576000506102df565b60406000600060006110005afa503d60005560406000600060006110006000fa503d6001555b60006024351160fa60043514166102f85760005061031f565b604060006000600060006110005af1503d60005560406000600060006024355afa503d6001555b60f06004351461033157600050610352565b60406000600060006110005afa503d6000556101005160006000f0503d6001555b60f56004351461036457600050610388565b60406000600060006110005afa503d6000556101005160006000615a17f5503d6001555b6160a760025500fe600160000360002000"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 8, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(code=bytes.fromhex("5000")),
                callee_1: Account(code=bytes.fromhex("600056")),
                callee_2: Account(code=bytes.fromhex("6001600157")),
                callee_3: Account(code=bytes.fromhex("fe00")),
                callee_4: Account(
                    code=bytes.fromhex(
                        "600260016000030460005260016000510160205260406000f300"
                    )
                ),
                contract: Account(
                    storage={0: 64, 2: 24743},
                    code=bytes.fromhex(
                        "6000602435146100115760005061001f565b600980610391600039610100525b61ff006024351461003257600050610046565b6000600060006000600061ff005af1610100525b610200602435146100595760005061006d565b605060005360006001600001536002610100525b61030060243514610080576000506100a4565b60606000536000600160000153605660026000015360006002600001536004610100525b610400602435146100b7576000506100eb565b6060600053600160016000015360606002600001536001600360000153605760046000015360006005600001536006610100525b610500602435146100fe57600050610112565b60fe60005360006001600001536002610100525b60006024351460f1600435141661012b57600050610155565b604060006000600060006110005af1503d600055604060006000600060006110006000f1503d6001555b60006024351160f1600435141661016e5760005061019c565b604060006000600060006110005af1503d60005560406000600060006000602435620f00005a03f1503d6001555b60006024351460f260043514166101b5576000506101df565b604060006000600060006110005af2503d600055604060006000600060006110006000f2503d6001555b60006024351160f260043514166101f857600050610221565b604060006000600060006110005af1503d600055604060006000600060006024355af2503d6001555b60006024351460f4600435141661023a57600050610260565b60406000600060006110005af4503d60005560406000600060006110006000f4503d6001555b60006024351160f46004351416610279576000506102a0565b604060006000600060006110005af1503d60005560406000600060006024355af4503d6001555b60006024351460fa60043514166102b9576000506102df565b60406000600060006110005afa503d60005560406000600060006110006000fa503d6001555b60006024351160fa60043514166102f85760005061031f565b604060006000600060006110005af1503d60005560406000600060006024355afa503d6001555b60f06004351461033157600050610352565b60406000600060006110005afa503d6000556101005160006000f0503d6001555b60f56004351461036457600050610388565b60406000600060006110005afa503d6000556101005160006000615a17f5503d6001555b6160a760025500fe600160000360002000"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 9, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(code=bytes.fromhex("5000")),
                callee_1: Account(code=bytes.fromhex("600056")),
                callee_2: Account(code=bytes.fromhex("6001600157")),
                callee_3: Account(code=bytes.fromhex("fe00")),
                callee_4: Account(
                    code=bytes.fromhex(
                        "600260016000030460005260016000510160205260406000f300"
                    )
                ),
                contract: Account(
                    storage={0: 64, 2: 24743},
                    code=bytes.fromhex(
                        "6000602435146100115760005061001f565b600980610391600039610100525b61ff006024351461003257600050610046565b6000600060006000600061ff005af1610100525b610200602435146100595760005061006d565b605060005360006001600001536002610100525b61030060243514610080576000506100a4565b60606000536000600160000153605660026000015360006002600001536004610100525b610400602435146100b7576000506100eb565b6060600053600160016000015360606002600001536001600360000153605760046000015360006005600001536006610100525b610500602435146100fe57600050610112565b60fe60005360006001600001536002610100525b60006024351460f1600435141661012b57600050610155565b604060006000600060006110005af1503d600055604060006000600060006110006000f1503d6001555b60006024351160f1600435141661016e5760005061019c565b604060006000600060006110005af1503d60005560406000600060006000602435620f00005a03f1503d6001555b60006024351460f260043514166101b5576000506101df565b604060006000600060006110005af2503d600055604060006000600060006110006000f2503d6001555b60006024351160f260043514166101f857600050610221565b604060006000600060006110005af1503d600055604060006000600060006024355af2503d6001555b60006024351460f4600435141661023a57600050610260565b60406000600060006110005af4503d60005560406000600060006110006000f4503d6001555b60006024351160f46004351416610279576000506102a0565b604060006000600060006110005af1503d60005560406000600060006024355af4503d6001555b60006024351460fa60043514166102b9576000506102df565b60406000600060006110005afa503d60005560406000600060006110006000fa503d6001555b60006024351160fa60043514166102f85760005061031f565b604060006000600060006110005af1503d60005560406000600060006024355afa503d6001555b60f06004351461033157600050610352565b60406000600060006110005afa503d6000556101005160006000f0503d6001555b60f56004351461036457600050610388565b60406000600060006110005afa503d6000556101005160006000615a17f5503d6001555b6160a760025500fe600160000360002000"  # noqa: E501
                    ),
                ),
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx = Transaction(
        sender=sender,
        to=contract,
        data=_tx_data(d),
        gas_limit=TX_GAS[g],
        value=TX_VALUE[v],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
