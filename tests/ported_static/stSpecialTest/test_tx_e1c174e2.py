"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stSpecialTest/tx_e1c174e2Filler.json
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
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["tests/static/state_tests/stSpecialTest/tx_e1c174e2Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_tx_e1c174e2(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x68795c4aa09d6f4ed3e5deddf8c2ad3049a601da")
    sender = EOA(
        key=0x98D5E7375843784F7EB2606A693BAB39EBAC533561559E372DC3017F30519535
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=3141592,
    )

    pre[sender] = Account(balance=0xDE0B6B3A7640000, nonce=24)
    # Source: raw bytecode
    contract = pre.deploy_contract(
        code=(
            Op.MSTORE8(offset=0x155F, value=0x0)
            + Op.DIV(
                Op.CALLDATALOAD(offset=0x0),
                0x100000000000000000000000000000000000000000000000000000000,
            )
            + Op.JUMPI(
                pc=Op.PUSH2[0x65],
                condition=Op.ISZERO(Op.EQ(Op.DUP2, 0x55F10AAF)),
            )
            + Op.MSTORE(offset=0x40, value=Op.CALLDATALOAD(offset=0x4))
            + Op.JUMPI(
                pc=Op.PUSH2[0x52],
                condition=Op.ISZERO(Op.SGT(Op.CALLVALUE, 0x0)),
            )
            + Op.POP(
                Op.CALL(
                    gas=0x1388,
                    address=Op.CALLER,
                    value=Op.CALLVALUE,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.JUMPDEST
            + Op.MSTORE(
                offset=0x60,
                value=Op.SLOAD(
                    key=Op.ADD(0x7, Op.MUL(Op.MLOAD(offset=0x40), 0xC)),
                ),
            )
            + Op.RETURN(offset=0x60, size=0x20)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x53F, condition=Op.ISZERO(Op.EQ(Op.DUP2, 0x69E0998B))
            )
            + Op.MSTORE(offset=0x80, value=Op.CALLDATALOAD(offset=0x4))
            + Op.MSTORE(offset=0xA0, value=Op.CALLDATALOAD(offset=0x24))
            + Op.MSTORE(offset=0x40, value=Op.CALLDATALOAD(offset=0x44))
            + Op.JUMPI(
                pc=Op.PUSH2[0x9A],
                condition=Op.ISZERO(
                    Op.ISZERO(Op.SGT(Op.MLOAD(offset=0x80), 0x0))
                ),
            )
            + Op.MSTORE(offset=0xC0, value=0x2)
            + Op.RETURN(offset=0xC0, size=0x20)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=Op.PUSH2[0xB1],
                condition=Op.ISZERO(
                    Op.ISZERO(Op.SGT(Op.MLOAD(offset=0xA0), 0x0))
                ),
            )
            + Op.MSTORE(offset=0xE0, value=0x3)
            + Op.RETURN(offset=0xE0, size=0x20)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=Op.PUSH2[0xCA],
                condition=Op.ISZERO(
                    Op.ISZERO(Op.SGT(Op.MLOAD(offset=0x40), 0x0))
                ),
            )
            + Op.MSTORE(offset=0x100, value=0x4)
            + Op.RETURN(offset=0x100, size=0x20)
            + Op.JUMPDEST
            + Op.MSTORE(
                offset=0x120,
                value=Op.MUL(
                    Op.SDIV(
                        Op.MUL(Op.MLOAD(offset=0x80), Op.MLOAD(offset=0xA0)),
                        Op.MUL(
                            Op.SLOAD(
                                key=Op.ADD(
                                    0x4,
                                    Op.MUL(Op.MLOAD(offset=0x40), 0xC),
                                ),
                            ),
                            Op.EXP(
                                0xA,
                                Op.SLOAD(
                                    key=Op.ADD(
                                        0x3,
                                        Op.MUL(Op.MLOAD(offset=0x40), 0xC),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    0xDE0B6B3A7640000,
                ),
            )
            + Op.JUMPI(
                pc=0x12F,
                condition=Op.ISZERO(
                    Op.SLT(
                        Op.CALLVALUE,
                        Op.SLOAD(
                            key=Op.ADD(
                                0x5, Op.MUL(Op.MLOAD(offset=0x40), 0xC)
                            ),
                        ),
                    ),
                ),
            )
            + Op.JUMPI(
                pc=0x122, condition=Op.ISZERO(Op.SGT(Op.CALLVALUE, 0x0))
            )
            + Op.POP(
                Op.CALL(
                    gas=0x1388,
                    address=Op.CALLER,
                    value=Op.CALLVALUE,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.JUMPDEST
            + Op.MSTORE(offset=0x140, value=0xB)
            + Op.RETURN(offset=0x140, size=0x20)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x160,
                condition=Op.ISZERO(
                    Op.SLT(Op.CALLVALUE, Op.MLOAD(offset=0x120))
                ),
            )
            + Op.JUMPI(
                pc=0x153, condition=Op.ISZERO(Op.SGT(Op.CALLVALUE, 0x0))
            )
            + Op.POP(
                Op.CALL(
                    gas=0x1388,
                    address=Op.CALLER,
                    value=Op.CALLVALUE,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.JUMPDEST
            + Op.MSTORE(offset=0x160, value=0x14)
            + Op.RETURN(offset=0x160, size=0x20)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x180,
                condition=Op.ISZERO(
                    Op.SGT(Op.CALLVALUE, Op.MLOAD(offset=0x120))
                ),
            )
            + Op.POP(
                Op.CALL(
                    gas=0x1388,
                    address=Op.CALLER,
                    value=Op.SUB(Op.CALLVALUE, Op.MLOAD(offset=0x120)),
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.JUMPDEST
            + Op.PUSH1[0xE0]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x6)
            + Op.MSTORE(offset=Op.ADD(Op.DUP3, 0x20), value=0x1)
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP3, 0x40), value=Op.MLOAD(offset=0x40)
            )
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP3, 0x60), value=Op.MLOAD(offset=0x80)
            )
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP3, 0x80), value=Op.MLOAD(offset=0xA0)
            )
            + Op.MSTORE(offset=Op.ADD(Op.DUP3, 0xA0), value=Op.CALLER)
            + Op.MSTORE(offset=Op.ADD(Op.DUP3, 0xC0), value=Op.NUMBER)
            + Op.ADD(Op.DUP2, 0x20)
            + Op.SWAP1
            + Op.POP
            + Op.PUSH2[0x180]
            + Op.MSTORE
            + Op.MLOAD(offset=0x180)
            + Op.SHA3(
                offset=Op.DUP2,
                size=Op.MUL(Op.MLOAD(offset=Op.SUB(Op.DUP3, 0x20)), 0x20),
            )
            + Op.SWAP1
            + Op.POP
            + Op.PUSH2[0x1C0]
            + Op.MSTORE
            + Op.JUMPI(
                pc=0x4BE,
                condition=Op.ISZERO(
                    Op.ISZERO(
                        Op.SLOAD(
                            key=Op.ADD(
                                0xE0000000000000000000000000000000000000000,
                                Op.MUL(Op.MLOAD(offset=0x1C0), 0x8),
                            ),
                        ),
                    ),
                ),
            )
            + Op.SSTORE(
                key=Op.ADD(
                    0xE0000000000000000000000000000000000000000,
                    Op.MUL(Op.MLOAD(offset=0x1C0), 0x8),
                ),
                value=Op.MLOAD(offset=0x1C0),
            )
            + Op.SSTORE(
                key=Op.ADD(
                    0xE0000000000000000000000000000000000000001,
                    Op.MUL(Op.MLOAD(offset=0x1C0), 0x8),
                ),
                value=0x1,
            )
            + Op.SSTORE(
                key=Op.ADD(
                    0xE0000000000000000000000000000000000000002,
                    Op.MUL(Op.MLOAD(offset=0x1C0), 0x8),
                ),
                value=Op.MLOAD(offset=0x40),
            )
            + Op.SSTORE(
                key=Op.ADD(
                    0xE0000000000000000000000000000000000000003,
                    Op.MUL(Op.MLOAD(offset=0x1C0), 0x8),
                ),
                value=Op.MLOAD(offset=0x80),
            )
            + Op.SSTORE(
                key=Op.ADD(
                    0xE0000000000000000000000000000000000000004,
                    Op.MUL(Op.MLOAD(offset=0x1C0), 0x8),
                ),
                value=Op.MLOAD(offset=0xA0),
            )
            + Op.SSTORE(
                key=Op.ADD(
                    0xE0000000000000000000000000000000000000005,
                    Op.MUL(Op.MLOAD(offset=0x1C0), 0x8),
                ),
                value=Op.CALLER,
            )
            + Op.SSTORE(
                key=Op.ADD(
                    0xE0000000000000000000000000000000000000006,
                    Op.MUL(Op.MLOAD(offset=0x1C0), 0x8),
                ),
                value=Op.NUMBER,
            )
            + Op.SSTORE(
                key=Op.ADD(
                    0xE0000000000000000000000000000000000000007,
                    Op.MUL(Op.MLOAD(offset=0x1C0), 0x8),
                ),
                value=Op.ADD(
                    0xE0000000000000000000000000000000000000000,
                    Op.MUL(Op.MLOAD(offset=0x1C0), 0x8),
                ),
            )
            + Op.MSTORE(
                offset=0x200,
                value=Op.SLOAD(
                    key=Op.ADD(0xB, Op.MUL(Op.MLOAD(offset=0x40), 0xC)),
                ),
            )
            + Op.MLOAD(offset=0x1C0)
            + Op.PUSH1[0xA0]
            + Op.PUSH1[0xA0]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x40)
            )
            + Op.MSTORE(offset=Op.ADD(0x40, Op.DUP2), value=0xC)
            + Op.MSTORE(
                offset=Op.ADD(0x60, Op.DUP2), value=Op.MLOAD(offset=0x200)
            )
            + Op.MSTORE(offset=Op.ADD(0x80, Op.DUP2), value=0x1)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SHA3
            + Op.SSTORE
            + Op.MLOAD(offset=0x200)
            + Op.PUSH1[0xA0]
            + Op.PUSH1[0xA0]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x40)
            )
            + Op.MSTORE(offset=Op.ADD(0x40, Op.DUP2), value=0xC)
            + Op.MSTORE(
                offset=Op.ADD(0x60, Op.DUP2), value=Op.MLOAD(offset=0x1C0)
            )
            + Op.MSTORE(offset=Op.ADD(0x80, Op.DUP2), value=0x2)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SHA3
            + Op.SSTORE
            + Op.MLOAD(offset=0x1C0)
            + Op.PUSH1[0xA0]
            + Op.PUSH1[0xA0]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x40)
            )
            + Op.MSTORE(offset=Op.ADD(0x40, Op.DUP2), value=0xC)
            + Op.MSTORE(
                offset=Op.ADD(0x60, Op.DUP2), value=Op.MLOAD(offset=0x1C0)
            )
            + Op.MSTORE(offset=Op.ADD(0x80, Op.DUP2), value=0x0)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SHA3
            + Op.SSTORE
            + Op.SSTORE(
                key=Op.ADD(0xB, Op.MUL(Op.MLOAD(offset=0x40), 0xC)),
                value=Op.MLOAD(offset=0x1C0),
            )
            + Op.SSTORE(
                key=Op.ADD(0xA, Op.MUL(Op.MLOAD(offset=0x40), 0xC)),
                value=Op.ADD(
                    Op.SLOAD(
                        key=Op.ADD(0xA, Op.MUL(Op.MLOAD(offset=0x40), 0xC))
                    ),
                    0x1,
                ),
            )
            + Op.JUMPI(pc=0x4B9, condition=Op.ISZERO(Op.EQ(0x1, 0x2)))
            + Op.MLOAD(offset=0x80)
            + Op.PUSH1[0x80]
            + Op.PUSH1[0x80]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x4)
            + Op.MSTORE(offset=Op.ADD(0x20, Op.DUP2), value=Op.CALLER)
            + Op.MSTORE(
                offset=Op.ADD(0x40, Op.DUP2), value=Op.MLOAD(offset=0x40)
            )
            + Op.MSTORE(offset=Op.ADD(0x60, Op.DUP2), value=0x0)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SLOAD(key=Op.SHA3)
            + Op.SUB
            + Op.PUSH1[0x80]
            + Op.PUSH1[0x80]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x4)
            + Op.MSTORE(offset=Op.ADD(0x20, Op.DUP2), value=Op.CALLER)
            + Op.MSTORE(
                offset=Op.ADD(0x40, Op.DUP2), value=Op.MLOAD(offset=0x40)
            )
            + Op.MSTORE(offset=Op.ADD(0x60, Op.DUP2), value=0x0)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SHA3
            + Op.SSTORE
            + Op.MLOAD(offset=0x80)
            + Op.PUSH1[0x80]
            + Op.PUSH1[0x80]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x4)
            + Op.MSTORE(offset=Op.ADD(0x20, Op.DUP2), value=Op.CALLER)
            + Op.MSTORE(
                offset=Op.ADD(0x40, Op.DUP2), value=Op.MLOAD(offset=0x40)
            )
            + Op.MSTORE(offset=Op.ADD(0x60, Op.DUP2), value=0x1)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SLOAD(key=Op.SHA3)
            + Op.ADD
            + Op.PUSH1[0x80]
            + Op.PUSH1[0x80]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x4)
            + Op.MSTORE(offset=Op.ADD(0x20, Op.DUP2), value=Op.CALLER)
            + Op.MSTORE(
                offset=Op.ADD(0x40, Op.DUP2), value=Op.MLOAD(offset=0x40)
            )
            + Op.MSTORE(offset=Op.ADD(0x60, Op.DUP2), value=0x1)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SHA3
            + Op.SSTORE
            + Op.JUMPDEST
            + Op.JUMP(pc=0x4CB)
            + Op.JUMPDEST
            + Op.MSTORE(offset=0x300, value=0x15)
            + Op.RETURN(offset=0x300, size=0x20)
            + Op.JUMPDEST
            + Op.PUSH1[0x1C]
            + Op.PUSH1[0xC0]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.ADD
            + Op.MSTORE(offset=Op.DUP2, value=Op.CALLER)
            + Op.MSTORE(offset=Op.ADD(Op.DUP3, 0x20), value=0x1)
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP3, 0x40), value=Op.MLOAD(offset=0xA0)
            )
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP3, 0x60), value=Op.MLOAD(offset=0x80)
            )
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP3, 0x80), value=Op.MLOAD(offset=0x1C0)
            )
            + Op.LOG2(
                offset=Op.DUP4,
                size=0xA0,
                topic_1=0x9463D1CC4AA2DB0DC624C996B1846F028D43C48CFC8B9F427F13336E4A732264,  # noqa: E501
                topic_2=Op.MLOAD(offset=0x40),
            )
            + Op.POP
            + Op.MSTORE(offset=0x340, value=Op.MLOAD(offset=0x1C0))
            + Op.RETURN(offset=0x340, size=0x20)
            + Op.MSTORE(offset=0x360, value=0x0)
            + Op.RETURN(offset=0x360, size=0x20)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0xA0C, condition=Op.ISZERO(Op.EQ(Op.DUP2, 0x909F073))
            )
            + Op.MSTORE(offset=0x80, value=Op.CALLDATALOAD(offset=0x4))
            + Op.MSTORE(offset=0xA0, value=Op.CALLDATALOAD(offset=0x24))
            + Op.MSTORE(offset=0x40, value=Op.CALLDATALOAD(offset=0x44))
            + Op.JUMPI(
                pc=0x576,
                condition=Op.ISZERO(
                    Op.ISZERO(Op.SGT(Op.MLOAD(offset=0x80), 0x0))
                ),
            )
            + Op.MSTORE(offset=0x380, value=0x2)
            + Op.RETURN(offset=0x380, size=0x20)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x58F,
                condition=Op.ISZERO(
                    Op.ISZERO(Op.SGT(Op.MLOAD(offset=0xA0), 0x0))
                ),
            )
            + Op.MSTORE(offset=0x3A0, value=0x3)
            + Op.RETURN(offset=0x3A0, size=0x20)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x5A8,
                condition=Op.ISZERO(
                    Op.ISZERO(Op.SGT(Op.MLOAD(offset=0x40), 0x0))
                ),
            )
            + Op.MSTORE(offset=0x3C0, value=0x4)
            + Op.RETURN(offset=0x3C0, size=0x20)
            + Op.JUMPDEST
            + Op.MSTORE(
                offset=0x120,
                value=Op.MUL(
                    Op.SDIV(
                        Op.MUL(Op.MLOAD(offset=0x80), Op.MLOAD(offset=0xA0)),
                        Op.MUL(
                            Op.SLOAD(
                                key=Op.ADD(
                                    0x4,
                                    Op.MUL(Op.MLOAD(offset=0x40), 0xC),
                                ),
                            ),
                            Op.EXP(
                                0xA,
                                Op.SLOAD(
                                    key=Op.ADD(
                                        0x3,
                                        Op.MUL(Op.MLOAD(offset=0x40), 0xC),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    0xDE0B6B3A7640000,
                ),
            )
            + Op.JUMPI(
                pc=0x610,
                condition=Op.ISZERO(
                    Op.SLT(
                        Op.MLOAD(offset=0x120),
                        Op.SLOAD(
                            key=Op.ADD(
                                0x5, Op.MUL(Op.MLOAD(offset=0x40), 0xC)
                            ),
                        ),
                    ),
                ),
            )
            + Op.JUMPI(
                pc=0x603, condition=Op.ISZERO(Op.SGT(Op.CALLVALUE, 0x0))
            )
            + Op.POP(
                Op.CALL(
                    gas=0x1388,
                    address=Op.CALLER,
                    value=Op.CALLVALUE,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.JUMPDEST
            + Op.MSTORE(offset=0x3E0, value=0xB)
            + Op.RETURN(offset=0x3E0, size=0x20)
            + Op.JUMPDEST
            + Op.PUSH1[0x80]
            + Op.PUSH1[0x80]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x4)
            + Op.MSTORE(offset=Op.ADD(0x20, Op.DUP2), value=Op.CALLER)
            + Op.MSTORE(
                offset=Op.ADD(0x40, Op.DUP2), value=Op.MLOAD(offset=0x40)
            )
            + Op.MSTORE(offset=Op.ADD(0x60, Op.DUP2), value=0x0)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.MSTORE(offset=0x400, value=Op.SLOAD(key=Op.SHA3))
            + Op.JUMPI(
                pc=0x9FF,
                condition=Op.ISZERO(
                    Op.ISZERO(
                        Op.SLT(Op.MLOAD(offset=0x400), Op.MLOAD(offset=0x80)),
                    ),
                ),
            )
            + Op.PUSH1[0xE0]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x6)
            + Op.MSTORE(offset=Op.ADD(Op.DUP3, 0x20), value=0x2)
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP3, 0x40), value=Op.MLOAD(offset=0x40)
            )
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP3, 0x60), value=Op.MLOAD(offset=0x80)
            )
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP3, 0x80), value=Op.MLOAD(offset=0xA0)
            )
            + Op.MSTORE(offset=Op.ADD(Op.DUP3, 0xA0), value=Op.CALLER)
            + Op.MSTORE(offset=Op.ADD(Op.DUP3, 0xC0), value=Op.NUMBER)
            + Op.ADD(Op.DUP2, 0x20)
            + Op.SWAP1
            + Op.POP
            + Op.PUSH2[0x180]
            + Op.MSTORE
            + Op.MLOAD(offset=0x180)
            + Op.SHA3(
                offset=Op.DUP2,
                size=Op.MUL(Op.MLOAD(offset=Op.SUB(Op.DUP3, 0x20)), 0x20),
            )
            + Op.SWAP1
            + Op.POP
            + Op.PUSH2[0x1C0]
            + Op.MSTORE
            + Op.JUMPI(
                pc=0x98A,
                condition=Op.ISZERO(
                    Op.ISZERO(
                        Op.SLOAD(
                            key=Op.ADD(
                                0xE0000000000000000000000000000000000000000,
                                Op.MUL(Op.MLOAD(offset=0x1C0), 0x8),
                            ),
                        ),
                    ),
                ),
            )
            + Op.SSTORE(
                key=Op.ADD(
                    0xE0000000000000000000000000000000000000000,
                    Op.MUL(Op.MLOAD(offset=0x1C0), 0x8),
                ),
                value=Op.MLOAD(offset=0x1C0),
            )
            + Op.SSTORE(
                key=Op.ADD(
                    0xE0000000000000000000000000000000000000001,
                    Op.MUL(Op.MLOAD(offset=0x1C0), 0x8),
                ),
                value=0x2,
            )
            + Op.SSTORE(
                key=Op.ADD(
                    0xE0000000000000000000000000000000000000002,
                    Op.MUL(Op.MLOAD(offset=0x1C0), 0x8),
                ),
                value=Op.MLOAD(offset=0x40),
            )
            + Op.SSTORE(
                key=Op.ADD(
                    0xE0000000000000000000000000000000000000003,
                    Op.MUL(Op.MLOAD(offset=0x1C0), 0x8),
                ),
                value=Op.MLOAD(offset=0x80),
            )
            + Op.SSTORE(
                key=Op.ADD(
                    0xE0000000000000000000000000000000000000004,
                    Op.MUL(Op.MLOAD(offset=0x1C0), 0x8),
                ),
                value=Op.MLOAD(offset=0xA0),
            )
            + Op.SSTORE(
                key=Op.ADD(
                    0xE0000000000000000000000000000000000000005,
                    Op.MUL(Op.MLOAD(offset=0x1C0), 0x8),
                ),
                value=Op.CALLER,
            )
            + Op.SSTORE(
                key=Op.ADD(
                    0xE0000000000000000000000000000000000000006,
                    Op.MUL(Op.MLOAD(offset=0x1C0), 0x8),
                ),
                value=Op.NUMBER,
            )
            + Op.SSTORE(
                key=Op.ADD(
                    0xE0000000000000000000000000000000000000007,
                    Op.MUL(Op.MLOAD(offset=0x1C0), 0x8),
                ),
                value=Op.ADD(
                    0xE0000000000000000000000000000000000000000,
                    Op.MUL(Op.MLOAD(offset=0x1C0), 0x8),
                ),
            )
            + Op.MSTORE(
                offset=0x200,
                value=Op.SLOAD(
                    key=Op.ADD(0xB, Op.MUL(Op.MLOAD(offset=0x40), 0xC)),
                ),
            )
            + Op.MLOAD(offset=0x1C0)
            + Op.PUSH1[0xA0]
            + Op.PUSH1[0xA0]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x40)
            )
            + Op.MSTORE(offset=Op.ADD(0x40, Op.DUP2), value=0xC)
            + Op.MSTORE(
                offset=Op.ADD(0x60, Op.DUP2), value=Op.MLOAD(offset=0x200)
            )
            + Op.MSTORE(offset=Op.ADD(0x80, Op.DUP2), value=0x1)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SHA3
            + Op.SSTORE
            + Op.MLOAD(offset=0x200)
            + Op.PUSH1[0xA0]
            + Op.PUSH1[0xA0]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x40)
            )
            + Op.MSTORE(offset=Op.ADD(0x40, Op.DUP2), value=0xC)
            + Op.MSTORE(
                offset=Op.ADD(0x60, Op.DUP2), value=Op.MLOAD(offset=0x1C0)
            )
            + Op.MSTORE(offset=Op.ADD(0x80, Op.DUP2), value=0x2)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SHA3
            + Op.SSTORE
            + Op.MLOAD(offset=0x1C0)
            + Op.PUSH1[0xA0]
            + Op.PUSH1[0xA0]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x40)
            )
            + Op.MSTORE(offset=Op.ADD(0x40, Op.DUP2), value=0xC)
            + Op.MSTORE(
                offset=Op.ADD(0x60, Op.DUP2), value=Op.MLOAD(offset=0x1C0)
            )
            + Op.MSTORE(offset=Op.ADD(0x80, Op.DUP2), value=0x0)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SHA3
            + Op.SSTORE
            + Op.SSTORE(
                key=Op.ADD(0xB, Op.MUL(Op.MLOAD(offset=0x40), 0xC)),
                value=Op.MLOAD(offset=0x1C0),
            )
            + Op.SSTORE(
                key=Op.ADD(0xA, Op.MUL(Op.MLOAD(offset=0x40), 0xC)),
                value=Op.ADD(
                    Op.SLOAD(
                        key=Op.ADD(0xA, Op.MUL(Op.MLOAD(offset=0x40), 0xC))
                    ),
                    0x1,
                ),
            )
            + Op.JUMPI(pc=0x985, condition=Op.ISZERO(Op.EQ(0x2, 0x2)))
            + Op.MLOAD(offset=0x80)
            + Op.PUSH1[0x80]
            + Op.PUSH1[0x80]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x4)
            + Op.MSTORE(offset=Op.ADD(0x20, Op.DUP2), value=Op.CALLER)
            + Op.MSTORE(
                offset=Op.ADD(0x40, Op.DUP2), value=Op.MLOAD(offset=0x40)
            )
            + Op.MSTORE(offset=Op.ADD(0x60, Op.DUP2), value=0x0)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SLOAD(key=Op.SHA3)
            + Op.SUB
            + Op.PUSH1[0x80]
            + Op.PUSH1[0x80]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x4)
            + Op.MSTORE(offset=Op.ADD(0x20, Op.DUP2), value=Op.CALLER)
            + Op.MSTORE(
                offset=Op.ADD(0x40, Op.DUP2), value=Op.MLOAD(offset=0x40)
            )
            + Op.MSTORE(offset=Op.ADD(0x60, Op.DUP2), value=0x0)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SHA3
            + Op.SSTORE
            + Op.MLOAD(offset=0x80)
            + Op.PUSH1[0x80]
            + Op.PUSH1[0x80]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x4)
            + Op.MSTORE(offset=Op.ADD(0x20, Op.DUP2), value=Op.CALLER)
            + Op.MSTORE(
                offset=Op.ADD(0x40, Op.DUP2), value=Op.MLOAD(offset=0x40)
            )
            + Op.MSTORE(offset=Op.ADD(0x60, Op.DUP2), value=0x1)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SLOAD(key=Op.SHA3)
            + Op.ADD
            + Op.PUSH1[0x80]
            + Op.PUSH1[0x80]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x4)
            + Op.MSTORE(offset=Op.ADD(0x20, Op.DUP2), value=Op.CALLER)
            + Op.MSTORE(
                offset=Op.ADD(0x40, Op.DUP2), value=Op.MLOAD(offset=0x40)
            )
            + Op.MSTORE(offset=Op.ADD(0x60, Op.DUP2), value=0x1)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SHA3
            + Op.SSTORE
            + Op.JUMPDEST
            + Op.JUMP(pc=0x997)
            + Op.JUMPDEST
            + Op.MSTORE(offset=0x560, value=0x15)
            + Op.RETURN(offset=0x560, size=0x20)
            + Op.JUMPDEST
            + Op.PUSH1[0x1C]
            + Op.PUSH1[0xC0]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.ADD
            + Op.MSTORE(offset=Op.DUP2, value=Op.CALLER)
            + Op.MSTORE(offset=Op.ADD(Op.DUP3, 0x20), value=0x2)
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP3, 0x40), value=Op.MLOAD(offset=0xA0)
            )
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP3, 0x60), value=Op.MLOAD(offset=0x80)
            )
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP3, 0x80), value=Op.MLOAD(offset=0x1C0)
            )
            + Op.LOG2(
                offset=Op.DUP4,
                size=0xA0,
                topic_1=0x9463D1CC4AA2DB0DC624C996B1846F028D43C48CFC8B9F427F13336E4A732264,  # noqa: E501
                topic_2=Op.MLOAD(offset=0x40),
            )
            + Op.POP
            + Op.MSTORE(offset=0x580, value=Op.MLOAD(offset=0x1C0))
            + Op.RETURN(offset=0x580, size=0x20)
            + Op.JUMPDEST
            + Op.MSTORE(offset=0x5A0, value=0x0)
            + Op.RETURN(offset=0x5A0, size=0x20)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x1733, condition=Op.ISZERO(Op.EQ(Op.DUP2, 0x9998BD00))
            )
            + Op.CALLDATASIZE
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.CALLDATACOPY(
                dest_offset=Op.DUP3,
                offset=0x4,
                size=Op.CALLDATASIZE,
            )
            + Op.MSTORE(offset=0x5E0, value=Op.CALLDATALOAD(offset=0x4))
            + Op.MSTORE(
                offset=0x600,
                value=Op.ADD(
                    Op.ADD(Op.DUP3, 0x20), Op.CALLDATALOAD(offset=0x24)
                ),
            )
            + Op.POP
            + Op.MSTORE(offset=0x620, value=Op.CALLVALUE)
            + Op.MSTORE(offset=0x640, value=0x0)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x170A,
                condition=Op.ISZERO(
                    Op.SLT(
                        Op.MLOAD(offset=0x640),
                        Op.MLOAD(offset=Op.SUB(Op.MLOAD(offset=0x600), 0x20)),
                    ),
                ),
            )
            + Op.MSTORE(
                offset=0x1C0,
                value=Op.MLOAD(
                    offset=Op.ADD(
                        Op.MLOAD(offset=0x600),
                        Op.MUL(0x20, Op.MLOAD(offset=0x640)),
                    ),
                ),
            )
            + Op.JUMPI(
                pc=0xA9D,
                condition=Op.ISZERO(
                    Op.ISZERO(
                        Op.SGT(
                            Op.NUMBER,
                            Op.SLOAD(
                                key=Op.ADD(
                                    0xE0000000000000000000000000000000000000006,  # noqa: E501
                                    Op.MUL(Op.MLOAD(offset=0x1C0), 0x8),
                                ),
                            ),
                        ),
                    ),
                ),
            )
            + Op.MSTORE(offset=0x660, value=0x16)
            + Op.RETURN(offset=0x660, size=0x20)
            + Op.JUMPDEST
            + Op.MSTORE(
                offset=0x40,
                value=Op.SLOAD(
                    key=Op.ADD(
                        0xE0000000000000000000000000000000000000002,
                        Op.MUL(Op.MLOAD(offset=0x1C0), 0x8),
                    ),
                ),
            )
            + Op.MSTORE(
                offset=0x680,
                value=Op.SLOAD(
                    key=Op.ADD(0x2, Op.MUL(Op.MLOAD(offset=0x40), 0xC)),
                ),
            )
            + Op.MSTORE(
                offset=0x6A0,
                value=Op.SLOAD(
                    key=Op.ADD(0x3, Op.MUL(Op.MLOAD(offset=0x40), 0xC)),
                ),
            )
            + Op.MSTORE(
                offset=0x6C0,
                value=Op.SLOAD(
                    key=Op.ADD(0x4, Op.MUL(Op.MLOAD(offset=0x40), 0xC)),
                ),
            )
            + Op.MSTORE(
                offset=0x6E0,
                value=Op.SLOAD(
                    key=Op.ADD(0x5, Op.MUL(Op.MLOAD(offset=0x40), 0xC)),
                ),
            )
            + Op.MSTORE(
                offset=0x700,
                value=Op.SLOAD(
                    key=Op.ADD(
                        0xE0000000000000000000000000000000000000001,
                        Op.MUL(Op.MLOAD(offset=0x1C0), 0x8),
                    ),
                ),
            )
            + Op.MSTORE(
                offset=0x80,
                value=Op.SLOAD(
                    key=Op.ADD(
                        0xE0000000000000000000000000000000000000003,
                        Op.MUL(Op.MLOAD(offset=0x1C0), 0x8),
                    ),
                ),
            )
            + Op.MSTORE(
                offset=0xA0,
                value=Op.SLOAD(
                    key=Op.ADD(
                        0xE0000000000000000000000000000000000000004,
                        Op.MUL(Op.MLOAD(offset=0x1C0), 0x8),
                    ),
                ),
            )
            + Op.MSTORE(
                offset=0x720,
                value=Op.SLOAD(
                    key=Op.ADD(
                        0xE0000000000000000000000000000000000000005,
                        Op.MUL(Op.MLOAD(offset=0x1C0), 0x8),
                    ),
                ),
            )
            + Op.JUMPI(
                pc=0x110E,
                condition=Op.ISZERO(Op.EQ(Op.MLOAD(offset=0x700), 0x1)),
            )
            + Op.PUSH1[0x80]
            + Op.PUSH1[0x80]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x4)
            + Op.MSTORE(offset=Op.ADD(0x20, Op.DUP2), value=Op.CALLER)
            + Op.MSTORE(
                offset=Op.ADD(0x40, Op.DUP2), value=Op.MLOAD(offset=0x40)
            )
            + Op.MSTORE(offset=Op.ADD(0x60, Op.DUP2), value=0x0)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.MSTORE(offset=0x400, value=Op.SLOAD(key=Op.SHA3))
            + Op.JUMPI(
                pc=0x10FC,
                condition=Op.ISZERO(Op.SGT(Op.MLOAD(offset=0x400), 0x0)),
            )
            + Op.MLOAD(offset=0x80)
            + Op.MLOAD(offset=0x400)
            + Op.MLOAD(offset=0x5E0)
            + Op.JUMPI(pc=0xBE0, condition=Op.ISZERO(Op.SLT(Op.DUP3, Op.DUP1)))
            + Op.DUP2
            + Op.JUMP(pc=0xBE2)
            + Op.JUMPDEST
            + Op.DUP1
            + Op.JUMPDEST
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.JUMPI(pc=0xBF4, condition=Op.ISZERO(Op.SLT(Op.DUP3, Op.DUP1)))
            + Op.DUP2
            + Op.JUMP(pc=0xBF6)
            + Op.JUMPDEST
            + Op.DUP1
            + Op.JUMPDEST
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.PUSH2[0x760]
            + Op.MSTORE
            + Op.MSTORE(
                offset=0x120,
                value=Op.SDIV(
                    Op.MUL(
                        Op.MUL(Op.MLOAD(offset=0x760), Op.MLOAD(offset=0xA0)),
                        0xDE0B6B3A7640000,
                    ),
                    Op.MUL(
                        Op.MLOAD(offset=0x6C0),
                        Op.EXP(0xA, Op.MLOAD(offset=0x6A0)),
                    ),
                ),
            )
            + Op.JUMPI(
                pc=0xC5B,
                condition=Op.ISZERO(
                    Op.SLT(Op.MLOAD(offset=0x120), Op.MLOAD(offset=0x6E0)),
                ),
            )
            + Op.JUMPI(
                pc=0xC4E,
                condition=Op.ISZERO(Op.SGT(Op.MLOAD(offset=0x620), 0x0)),
            )
            + Op.POP(
                Op.CALL(
                    gas=0x1388,
                    address=Op.CALLER,
                    value=Op.MLOAD(offset=0x620),
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.JUMPDEST
            + Op.MSTORE(offset=0x800, value=0xC)
            + Op.RETURN(offset=0x800, size=0x20)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0xCB0,
                condition=Op.ISZERO(
                    Op.SLT(Op.MLOAD(offset=0x760), Op.MLOAD(offset=0x80)),
                ),
            )
            + Op.SSTORE(
                key=Op.ADD(
                    0xE0000000000000000000000000000000000000003,
                    Op.MUL(Op.MLOAD(offset=0x1C0), 0x8),
                ),
                value=Op.SUB(
                    Op.SLOAD(
                        key=Op.ADD(
                            0xE0000000000000000000000000000000000000003,
                            Op.MUL(Op.MLOAD(offset=0x1C0), 0x8),
                        ),
                    ),
                    Op.MLOAD(offset=0x760),
                ),
            )
            + Op.JUMP(pc=0xFD4)
            + Op.JUMPDEST
            + Op.SSTORE(
                key=Op.ADD(
                    0xE0000000000000000000000000000000000000000,
                    Op.MUL(Op.MLOAD(offset=0x1C0), 0x8),
                ),
                value=0x0,
            )
            + Op.SSTORE(
                key=Op.ADD(
                    0xE0000000000000000000000000000000000000001,
                    Op.MUL(Op.MLOAD(offset=0x1C0), 0x8),
                ),
                value=0x0,
            )
            + Op.SSTORE(
                key=Op.ADD(
                    0xE0000000000000000000000000000000000000002,
                    Op.MUL(Op.MLOAD(offset=0x1C0), 0x8),
                ),
                value=0x0,
            )
            + Op.SSTORE(
                key=Op.ADD(
                    0xE0000000000000000000000000000000000000003,
                    Op.MUL(Op.MLOAD(offset=0x1C0), 0x8),
                ),
                value=0x0,
            )
            + Op.SSTORE(
                key=Op.ADD(
                    0xE0000000000000000000000000000000000000004,
                    Op.MUL(Op.MLOAD(offset=0x1C0), 0x8),
                ),
                value=0x0,
            )
            + Op.SSTORE(
                key=Op.ADD(
                    0xE0000000000000000000000000000000000000005,
                    Op.MUL(Op.MLOAD(offset=0x1C0), 0x8),
                ),
                value=0x0,
            )
            + Op.SSTORE(
                key=Op.ADD(
                    0xE0000000000000000000000000000000000000006,
                    Op.MUL(Op.MLOAD(offset=0x1C0), 0x8),
                ),
                value=0x0,
            )
            + Op.SSTORE(
                key=Op.ADD(
                    0xE0000000000000000000000000000000000000007,
                    Op.MUL(Op.MLOAD(offset=0x1C0), 0x8),
                ),
                value=0x0,
            )
            + Op.PUSH1[0xA0]
            + Op.PUSH1[0xA0]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x40)
            )
            + Op.MSTORE(offset=Op.ADD(0x40, Op.DUP2), value=0xC)
            + Op.MSTORE(
                offset=Op.ADD(0x60, Op.DUP2), value=Op.MLOAD(offset=0x1C0)
            )
            + Op.MSTORE(offset=Op.ADD(0x80, Op.DUP2), value=0x2)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.MSTORE(offset=0x820, value=Op.SLOAD(key=Op.SHA3))
            + Op.PUSH1[0xA0]
            + Op.PUSH1[0xA0]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x40)
            )
            + Op.MSTORE(offset=Op.ADD(0x40, Op.DUP2), value=0xC)
            + Op.MSTORE(
                offset=Op.ADD(0x60, Op.DUP2), value=Op.MLOAD(offset=0x1C0)
            )
            + Op.MSTORE(offset=Op.ADD(0x80, Op.DUP2), value=0x1)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.MSTORE(offset=0x860, value=Op.SLOAD(key=Op.SHA3))
            + Op.JUMPI(pc=0xE3A, condition=Op.ISZERO(Op.MLOAD(offset=0x820)))
            + Op.MLOAD(offset=0x860)
            + Op.JUMP(pc=0xE3D)
            + Op.JUMPDEST
            + Op.PUSH1[0x0]
            + Op.JUMPDEST
            + Op.JUMPI(pc=0xEB7, condition=Op.ISZERO)
            + Op.MLOAD(offset=0x860)
            + Op.PUSH1[0xA0]
            + Op.PUSH1[0xA0]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x40)
            )
            + Op.MSTORE(offset=Op.ADD(0x40, Op.DUP2), value=0xC)
            + Op.MSTORE(
                offset=Op.ADD(0x60, Op.DUP2), value=Op.MLOAD(offset=0x820)
            )
            + Op.MSTORE(offset=Op.ADD(0x80, Op.DUP2), value=0x1)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SHA3
            + Op.SSTORE
            + Op.MLOAD(offset=0x820)
            + Op.PUSH1[0xA0]
            + Op.PUSH1[0xA0]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x40)
            )
            + Op.MSTORE(offset=Op.ADD(0x40, Op.DUP2), value=0xC)
            + Op.MSTORE(
                offset=Op.ADD(0x60, Op.DUP2), value=Op.MLOAD(offset=0x860)
            )
            + Op.MSTORE(offset=Op.ADD(0x80, Op.DUP2), value=0x2)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SHA3
            + Op.SSTORE
            + Op.JUMP(pc=0xF06)
            + Op.JUMPDEST
            + Op.JUMPI(pc=0xF05, condition=Op.ISZERO(Op.MLOAD(offset=0x820)))
            + Op.SSTORE(
                key=Op.ADD(0xB, Op.MUL(Op.MLOAD(offset=0x40), 0xC)),
                value=Op.MLOAD(offset=0x820),
            )
            + Op.PUSH1[0x0]
            + Op.PUSH1[0xA0]
            + Op.PUSH1[0xA0]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x40)
            )
            + Op.MSTORE(offset=Op.ADD(0x40, Op.DUP2), value=0xC)
            + Op.MSTORE(
                offset=Op.ADD(0x60, Op.DUP2), value=Op.MLOAD(offset=0x820)
            )
            + Op.MSTORE(offset=Op.ADD(0x80, Op.DUP2), value=0x1)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SHA3
            + Op.SSTORE
            + Op.JUMPDEST
            + Op.JUMPDEST
            + Op.JUMPI(pc=0xF46, condition=Op.ISZERO(Op.MLOAD(offset=0x860)))
            + Op.PUSH1[0x0]
            + Op.PUSH1[0xA0]
            + Op.PUSH1[0xA0]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x40)
            )
            + Op.MSTORE(offset=Op.ADD(0x40, Op.DUP2), value=0xC)
            + Op.MSTORE(
                offset=Op.ADD(0x60, Op.DUP2), value=Op.MLOAD(offset=0x1C0)
            )
            + Op.MSTORE(offset=Op.ADD(0x80, Op.DUP2), value=0x1)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SHA3
            + Op.SSTORE
            + Op.JUMPDEST
            + Op.JUMPI(pc=0xF86, condition=Op.ISZERO(Op.MLOAD(offset=0x820)))
            + Op.PUSH1[0x0]
            + Op.PUSH1[0xA0]
            + Op.PUSH1[0xA0]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x40)
            )
            + Op.MSTORE(offset=Op.ADD(0x40, Op.DUP2), value=0xC)
            + Op.MSTORE(
                offset=Op.ADD(0x60, Op.DUP2), value=Op.MLOAD(offset=0x1C0)
            )
            + Op.MSTORE(offset=Op.ADD(0x80, Op.DUP2), value=0x2)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SHA3
            + Op.SSTORE
            + Op.JUMPDEST
            + Op.PUSH1[0x0]
            + Op.PUSH1[0xA0]
            + Op.PUSH1[0xA0]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x40)
            )
            + Op.MSTORE(offset=Op.ADD(0x40, Op.DUP2), value=0xC)
            + Op.MSTORE(
                offset=Op.ADD(0x60, Op.DUP2), value=Op.MLOAD(offset=0x1C0)
            )
            + Op.MSTORE(offset=Op.ADD(0x80, Op.DUP2), value=0x0)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SHA3
            + Op.SSTORE
            + Op.SSTORE(
                key=Op.ADD(0xA, Op.MUL(Op.MLOAD(offset=0x40), 0xC)),
                value=Op.SUB(
                    Op.SLOAD(
                        key=Op.ADD(0xA, Op.MUL(Op.MLOAD(offset=0x40), 0xC))
                    ),
                    0x1,
                ),
            )
            + Op.JUMPDEST
            + Op.MLOAD(offset=0x760)
            + Op.PUSH1[0x80]
            + Op.PUSH1[0x80]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x4)
            + Op.MSTORE(offset=Op.ADD(0x20, Op.DUP2), value=Op.CALLER)
            + Op.MSTORE(
                offset=Op.ADD(0x40, Op.DUP2), value=Op.MLOAD(offset=0x40)
            )
            + Op.MSTORE(offset=Op.ADD(0x60, Op.DUP2), value=0x0)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SLOAD(key=Op.SHA3)
            + Op.SUB
            + Op.PUSH1[0x80]
            + Op.PUSH1[0x80]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x4)
            + Op.MSTORE(offset=Op.ADD(0x20, Op.DUP2), value=Op.CALLER)
            + Op.MSTORE(
                offset=Op.ADD(0x40, Op.DUP2), value=Op.MLOAD(offset=0x40)
            )
            + Op.MSTORE(offset=Op.ADD(0x60, Op.DUP2), value=0x0)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SHA3
            + Op.SSTORE
            + Op.MLOAD(offset=0x760)
            + Op.PUSH1[0x80]
            + Op.PUSH1[0x80]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x4)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x720)
            )
            + Op.MSTORE(
                offset=Op.ADD(0x40, Op.DUP2), value=Op.MLOAD(offset=0x40)
            )
            + Op.MSTORE(offset=Op.ADD(0x60, Op.DUP2), value=0x0)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SLOAD(key=Op.SHA3)
            + Op.ADD
            + Op.PUSH1[0x80]
            + Op.PUSH1[0x80]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x4)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x720)
            )
            + Op.MSTORE(
                offset=Op.ADD(0x40, Op.DUP2), value=Op.MLOAD(offset=0x40)
            )
            + Op.MSTORE(offset=Op.ADD(0x60, Op.DUP2), value=0x0)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SHA3
            + Op.SSTORE
            + Op.POP(
                Op.CALL(
                    gas=0x1388,
                    address=Op.CALLER,
                    value=Op.MLOAD(offset=0x120),
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.PUSH1[0x1C]
            + Op.PUSH1[0xA0]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.ADD
            + Op.MSTORE(offset=Op.DUP2, value=0x2)
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP3, 0x20), value=Op.MLOAD(offset=0xA0)
            )
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP3, 0x40), value=Op.MLOAD(offset=0x760)
            )
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP3, 0x60), value=Op.MLOAD(offset=0x1C0)
            )
            + Op.LOG4(
                offset=Op.DUP6,
                size=0x80,
                topic_1=0xF9FE89F83633CC2ECA9B17E1F77422F037CB026EACA4E6A5337FA1595F50A81,  # noqa: E501
                topic_2=Op.MLOAD(offset=0x40),
                topic_3=Op.CALLER,
                topic_4=Op.MLOAD(offset=0x720),
            )
            + Op.POP
            + Op.JUMP(pc=0x1109)
            + Op.JUMPDEST
            + Op.MSTORE(offset=0x9E0, value=0xA)
            + Op.RETURN(offset=0x9E0, size=0x20)
            + Op.JUMPDEST
            + Op.JUMP(pc=0x1680)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x167F,
                condition=Op.ISZERO(Op.EQ(Op.MLOAD(offset=0x700), 0x2)),
            )
            + Op.JUMPI(
                pc=0x1671,
                condition=Op.ISZERO(Op.SGT(Op.MLOAD(offset=0x620), 0x0)),
            )
            + Op.JUMPI(
                pc=0x1160,
                condition=Op.ISZERO(
                    Op.SLT(Op.MLOAD(offset=0x620), Op.MLOAD(offset=0x6E0)),
                ),
            )
            + Op.JUMPI(
                pc=0x1153,
                condition=Op.ISZERO(Op.SGT(Op.MLOAD(offset=0x620), 0x0)),
            )
            + Op.POP(
                Op.CALL(
                    gas=0x1388,
                    address=Op.CALLER,
                    value=Op.MLOAD(offset=0x620),
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.JUMPDEST
            + Op.MSTORE(offset=0xA00, value=0xC)
            + Op.RETURN(offset=0xA00, size=0x20)
            + Op.JUMPDEST
            + Op.MSTORE(
                offset=0xA20,
                value=Op.SDIV(
                    Op.MUL(
                        Op.MUL(Op.MLOAD(offset=0x80), Op.MLOAD(offset=0xA0)),
                        0xDE0B6B3A7640000,
                    ),
                    Op.MUL(
                        Op.MLOAD(offset=0x6C0),
                        Op.EXP(0xA, Op.MLOAD(offset=0x6A0)),
                    ),
                ),
            )
            + Op.MLOAD(offset=0x620)
            + Op.MLOAD(offset=0xA20)
            + Op.JUMPI(
                pc=0x1198, condition=Op.ISZERO(Op.SLT(Op.DUP3, Op.DUP1))
            )
            + Op.DUP2
            + Op.JUMP(pc=0x119A)
            + Op.JUMPDEST
            + Op.DUP1
            + Op.JUMPDEST
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.PUSH2[0x120]
            + Op.MSTORE
            + Op.JUMPI(
                pc=0x121B,
                condition=Op.ISZERO(
                    Op.SLT(Op.MLOAD(offset=0x120), Op.MLOAD(offset=0xA20)),
                ),
            )
            + Op.MSTORE(
                offset=0x760,
                value=Op.SDIV(
                    Op.SDIV(
                        Op.MUL(
                            Op.MLOAD(offset=0x120),
                            Op.MUL(
                                Op.MLOAD(offset=0x6C0),
                                Op.EXP(0xA, Op.MLOAD(offset=0x6A0)),
                            ),
                        ),
                        Op.MLOAD(offset=0xA0),
                    ),
                    0xDE0B6B3A7640000,
                ),
            )
            + Op.SSTORE(
                key=Op.ADD(
                    0xE0000000000000000000000000000000000000003,
                    Op.MUL(Op.MLOAD(offset=0x1C0), 0x8),
                ),
                value=Op.SUB(
                    Op.SLOAD(
                        key=Op.ADD(
                            0xE0000000000000000000000000000000000000003,
                            Op.MUL(Op.MLOAD(offset=0x1C0), 0x8),
                        ),
                    ),
                    Op.MLOAD(offset=0x760),
                ),
            )
            + Op.JUMP(pc=0x1546)
            + Op.JUMPDEST
            + Op.MSTORE(offset=0x760, value=Op.MLOAD(offset=0x80))
            + Op.SSTORE(
                key=Op.ADD(
                    0xE0000000000000000000000000000000000000000,
                    Op.MUL(Op.MLOAD(offset=0x1C0), 0x8),
                ),
                value=0x0,
            )
            + Op.SSTORE(
                key=Op.ADD(
                    0xE0000000000000000000000000000000000000001,
                    Op.MUL(Op.MLOAD(offset=0x1C0), 0x8),
                ),
                value=0x0,
            )
            + Op.SSTORE(
                key=Op.ADD(
                    0xE0000000000000000000000000000000000000002,
                    Op.MUL(Op.MLOAD(offset=0x1C0), 0x8),
                ),
                value=0x0,
            )
            + Op.SSTORE(
                key=Op.ADD(
                    0xE0000000000000000000000000000000000000003,
                    Op.MUL(Op.MLOAD(offset=0x1C0), 0x8),
                ),
                value=0x0,
            )
            + Op.SSTORE(
                key=Op.ADD(
                    0xE0000000000000000000000000000000000000004,
                    Op.MUL(Op.MLOAD(offset=0x1C0), 0x8),
                ),
                value=0x0,
            )
            + Op.SSTORE(
                key=Op.ADD(
                    0xE0000000000000000000000000000000000000005,
                    Op.MUL(Op.MLOAD(offset=0x1C0), 0x8),
                ),
                value=0x0,
            )
            + Op.SSTORE(
                key=Op.ADD(
                    0xE0000000000000000000000000000000000000006,
                    Op.MUL(Op.MLOAD(offset=0x1C0), 0x8),
                ),
                value=0x0,
            )
            + Op.SSTORE(
                key=Op.ADD(
                    0xE0000000000000000000000000000000000000007,
                    Op.MUL(Op.MLOAD(offset=0x1C0), 0x8),
                ),
                value=0x0,
            )
            + Op.PUSH1[0xA0]
            + Op.PUSH1[0xA0]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x40)
            )
            + Op.MSTORE(offset=Op.ADD(0x40, Op.DUP2), value=0xC)
            + Op.MSTORE(
                offset=Op.ADD(0x60, Op.DUP2), value=Op.MLOAD(offset=0x1C0)
            )
            + Op.MSTORE(offset=Op.ADD(0x80, Op.DUP2), value=0x2)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.MSTORE(offset=0x820, value=Op.SLOAD(key=Op.SHA3))
            + Op.PUSH1[0xA0]
            + Op.PUSH1[0xA0]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x40)
            )
            + Op.MSTORE(offset=Op.ADD(0x40, Op.DUP2), value=0xC)
            + Op.MSTORE(
                offset=Op.ADD(0x60, Op.DUP2), value=Op.MLOAD(offset=0x1C0)
            )
            + Op.MSTORE(offset=Op.ADD(0x80, Op.DUP2), value=0x1)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.MSTORE(offset=0x860, value=Op.SLOAD(key=Op.SHA3))
            + Op.JUMPI(pc=0x13AC, condition=Op.ISZERO(Op.MLOAD(offset=0x820)))
            + Op.MLOAD(offset=0x860)
            + Op.JUMP(pc=0x13AF)
            + Op.JUMPDEST
            + Op.PUSH1[0x0]
            + Op.JUMPDEST
            + Op.JUMPI(pc=0x1429, condition=Op.ISZERO)
            + Op.MLOAD(offset=0x860)
            + Op.PUSH1[0xA0]
            + Op.PUSH1[0xA0]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x40)
            )
            + Op.MSTORE(offset=Op.ADD(0x40, Op.DUP2), value=0xC)
            + Op.MSTORE(
                offset=Op.ADD(0x60, Op.DUP2), value=Op.MLOAD(offset=0x820)
            )
            + Op.MSTORE(offset=Op.ADD(0x80, Op.DUP2), value=0x1)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SHA3
            + Op.SSTORE
            + Op.MLOAD(offset=0x820)
            + Op.PUSH1[0xA0]
            + Op.PUSH1[0xA0]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x40)
            )
            + Op.MSTORE(offset=Op.ADD(0x40, Op.DUP2), value=0xC)
            + Op.MSTORE(
                offset=Op.ADD(0x60, Op.DUP2), value=Op.MLOAD(offset=0x860)
            )
            + Op.MSTORE(offset=Op.ADD(0x80, Op.DUP2), value=0x2)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SHA3
            + Op.SSTORE
            + Op.JUMP(pc=0x1478)
            + Op.JUMPDEST
            + Op.JUMPI(pc=0x1477, condition=Op.ISZERO(Op.MLOAD(offset=0x820)))
            + Op.SSTORE(
                key=Op.ADD(0xB, Op.MUL(Op.MLOAD(offset=0x40), 0xC)),
                value=Op.MLOAD(offset=0x820),
            )
            + Op.PUSH1[0x0]
            + Op.PUSH1[0xA0]
            + Op.PUSH1[0xA0]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x40)
            )
            + Op.MSTORE(offset=Op.ADD(0x40, Op.DUP2), value=0xC)
            + Op.MSTORE(
                offset=Op.ADD(0x60, Op.DUP2), value=Op.MLOAD(offset=0x820)
            )
            + Op.MSTORE(offset=Op.ADD(0x80, Op.DUP2), value=0x1)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SHA3
            + Op.SSTORE
            + Op.JUMPDEST
            + Op.JUMPDEST
            + Op.JUMPI(pc=0x14B8, condition=Op.ISZERO(Op.MLOAD(offset=0x860)))
            + Op.PUSH1[0x0]
            + Op.PUSH1[0xA0]
            + Op.PUSH1[0xA0]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x40)
            )
            + Op.MSTORE(offset=Op.ADD(0x40, Op.DUP2), value=0xC)
            + Op.MSTORE(
                offset=Op.ADD(0x60, Op.DUP2), value=Op.MLOAD(offset=0x1C0)
            )
            + Op.MSTORE(offset=Op.ADD(0x80, Op.DUP2), value=0x1)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SHA3
            + Op.SSTORE
            + Op.JUMPDEST
            + Op.JUMPI(pc=0x14F8, condition=Op.ISZERO(Op.MLOAD(offset=0x820)))
            + Op.PUSH1[0x0]
            + Op.PUSH1[0xA0]
            + Op.PUSH1[0xA0]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x40)
            )
            + Op.MSTORE(offset=Op.ADD(0x40, Op.DUP2), value=0xC)
            + Op.MSTORE(
                offset=Op.ADD(0x60, Op.DUP2), value=Op.MLOAD(offset=0x1C0)
            )
            + Op.MSTORE(offset=Op.ADD(0x80, Op.DUP2), value=0x2)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SHA3
            + Op.SSTORE
            + Op.JUMPDEST
            + Op.PUSH1[0x0]
            + Op.PUSH1[0xA0]
            + Op.PUSH1[0xA0]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x40)
            )
            + Op.MSTORE(offset=Op.ADD(0x40, Op.DUP2), value=0xC)
            + Op.MSTORE(
                offset=Op.ADD(0x60, Op.DUP2), value=Op.MLOAD(offset=0x1C0)
            )
            + Op.MSTORE(offset=Op.ADD(0x80, Op.DUP2), value=0x0)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SHA3
            + Op.SSTORE
            + Op.SSTORE(
                key=Op.ADD(0xA, Op.MUL(Op.MLOAD(offset=0x40), 0xC)),
                value=Op.SUB(
                    Op.SLOAD(
                        key=Op.ADD(0xA, Op.MUL(Op.MLOAD(offset=0x40), 0xC))
                    ),
                    0x1,
                ),
            )
            + Op.JUMPDEST
            + Op.MLOAD(offset=0x760)
            + Op.PUSH1[0x80]
            + Op.PUSH1[0x80]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x4)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x720)
            )
            + Op.MSTORE(
                offset=Op.ADD(0x40, Op.DUP2), value=Op.MLOAD(offset=0x40)
            )
            + Op.MSTORE(offset=Op.ADD(0x60, Op.DUP2), value=0x1)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SLOAD(key=Op.SHA3)
            + Op.SUB
            + Op.PUSH1[0x80]
            + Op.PUSH1[0x80]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x4)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x720)
            )
            + Op.MSTORE(
                offset=Op.ADD(0x40, Op.DUP2), value=Op.MLOAD(offset=0x40)
            )
            + Op.MSTORE(offset=Op.ADD(0x60, Op.DUP2), value=0x1)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SHA3
            + Op.SSTORE
            + Op.MLOAD(offset=0x760)
            + Op.PUSH1[0x80]
            + Op.PUSH1[0x80]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x4)
            + Op.MSTORE(offset=Op.ADD(0x20, Op.DUP2), value=Op.CALLER)
            + Op.MSTORE(
                offset=Op.ADD(0x40, Op.DUP2), value=Op.MLOAD(offset=0x40)
            )
            + Op.MSTORE(offset=Op.ADD(0x60, Op.DUP2), value=0x0)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SLOAD(key=Op.SHA3)
            + Op.ADD
            + Op.PUSH1[0x80]
            + Op.PUSH1[0x80]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x4)
            + Op.MSTORE(offset=Op.ADD(0x20, Op.DUP2), value=Op.CALLER)
            + Op.MSTORE(
                offset=Op.ADD(0x40, Op.DUP2), value=Op.MLOAD(offset=0x40)
            )
            + Op.MSTORE(offset=Op.ADD(0x60, Op.DUP2), value=0x0)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SHA3
            + Op.SSTORE
            + Op.POP(
                Op.CALL(
                    gas=0x1388,
                    address=Op.MLOAD(offset=0x720),
                    value=Op.MLOAD(offset=0x120),
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.PUSH1[0x1C]
            + Op.PUSH1[0xA0]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.ADD
            + Op.MSTORE(offset=Op.DUP2, value=0x1)
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP3, 0x20), value=Op.MLOAD(offset=0xA0)
            )
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP3, 0x40), value=Op.MLOAD(offset=0x760)
            )
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP3, 0x60), value=Op.MLOAD(offset=0x1C0)
            )
            + Op.LOG4(
                offset=Op.DUP6,
                size=0x80,
                topic_1=0xF9FE89F83633CC2ECA9B17E1F77422F037CB026EACA4E6A5337FA1595F50A81,  # noqa: E501
                topic_2=Op.MLOAD(offset=0x40),
                topic_3=Op.CALLER,
                topic_4=Op.MLOAD(offset=0x720),
            )
            + Op.POP
            + Op.JUMP(pc=0x167E)
            + Op.JUMPDEST
            + Op.MSTORE(offset=0xC00, value=0xA)
            + Op.RETURN(offset=0xC00, size=0x20)
            + Op.JUMPDEST
            + Op.JUMPDEST
            + Op.JUMPDEST
            + Op.SSTORE(
                key=Op.ADD(0x7, Op.MUL(Op.MLOAD(offset=0x40), 0xC)),
                value=Op.MLOAD(offset=0xA0),
            )
            + Op.PUSH1[0x1C]
            + Op.PUSH1[0xA0]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.ADD
            + Op.MSTORE(offset=Op.DUP2, value=Op.MLOAD(offset=0x700))
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP3, 0x20), value=Op.MLOAD(offset=0xA0)
            )
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP3, 0x40), value=Op.MLOAD(offset=0x760)
            )
            + Op.MSTORE(offset=Op.ADD(Op.DUP3, 0x60), value=Op.TIMESTAMP)
            + Op.LOG2(
                offset=Op.DUP4,
                size=0x80,
                topic_1=0x50944F09CE56F9F0E2CB67683C9B451049C39F60452B850B169148F3DAA51ED6,  # noqa: E501
                topic_2=Op.MLOAD(offset=0x40),
            )
            + Op.POP
            + Op.MSTORE(
                offset=0x5E0,
                value=Op.SUB(Op.MLOAD(offset=0x5E0), Op.MLOAD(offset=0x760)),
            )
            + Op.MSTORE(
                offset=0x620,
                value=Op.SUB(Op.MLOAD(offset=0x620), Op.MLOAD(offset=0x120)),
            )
            + Op.MSTORE(
                offset=0x640, value=Op.ADD(Op.MLOAD(offset=0x640), 0x1)
            )
            + Op.JUMP(pc=0xA46)
            + Op.JUMPDEST
            + Op.JUMPI(pc=0x1726, condition=Op.ISZERO(Op.MLOAD(offset=0x620)))
            + Op.POP(
                Op.CALL(
                    gas=0x1388,
                    address=Op.CALLER,
                    value=Op.MLOAD(offset=0x620),
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.JUMPDEST
            + Op.MSTORE(offset=0xC20, value=0x1)
            + Op.RETURN(offset=0xC20, size=0x20)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x185B, condition=Op.ISZERO(Op.EQ(Op.DUP2, 0x34A501C7))
            )
            + Op.MSTORE(offset=0x80, value=Op.CALLDATALOAD(offset=0x4))
            + Op.MSTORE(offset=0x40, value=Op.CALLDATALOAD(offset=0x24))
            + Op.PUSH1[0x1C]
            + Op.PUSH1[0x84]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.ADD
            + Op.MSTORE(offset=Op.SUB(Op.DUP3, 0x1C), value=0x27F08B00)
            + Op.MSTORE(offset=Op.ADD(Op.DUP3, 0x4), value=Op.CALLER)
            + Op.MSTORE(offset=Op.ADD(Op.DUP3, 0x24), value=Op.ADDRESS)
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP3, 0x44), value=Op.MLOAD(offset=0x80)
            )
            + Op.POP(
                Op.CALL(
                    gas=Op.SUB(Op.GAS, 0x2D),
                    address=Op.SLOAD(
                        key=Op.ADD(0x2, Op.MUL(Op.MLOAD(offset=0x40), 0xC)),
                    ),
                    value=0x0,
                    args_offset=Op.DUP4,
                    args_size=0x64,
                    ret_offset=0xC40,
                    ret_size=0x20,
                ),
            )
            + Op.MLOAD(offset=0xC40)
            + Op.SWAP1
            + Op.POP
            + Op.JUMPI(pc=0x184E, condition=Op.ISZERO)
            + Op.PUSH1[0x80]
            + Op.PUSH1[0x80]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x4)
            + Op.MSTORE(offset=Op.ADD(0x20, Op.DUP2), value=Op.CALLER)
            + Op.MSTORE(
                offset=Op.ADD(0x40, Op.DUP2), value=Op.MLOAD(offset=0x40)
            )
            + Op.MSTORE(offset=Op.ADD(0x60, Op.DUP2), value=0x0)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.MSTORE(offset=0x400, value=Op.SLOAD(key=Op.SHA3))
            + Op.MSTORE(
                offset=0xC80,
                value=Op.ADD(Op.MLOAD(offset=0x400), Op.MLOAD(offset=0x80)),
            )
            + Op.MLOAD(offset=0xC80)
            + Op.PUSH1[0x80]
            + Op.PUSH1[0x80]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x4)
            + Op.MSTORE(offset=Op.ADD(0x20, Op.DUP2), value=Op.CALLER)
            + Op.MSTORE(
                offset=Op.ADD(0x40, Op.DUP2), value=Op.MLOAD(offset=0x40)
            )
            + Op.MSTORE(offset=Op.ADD(0x60, Op.DUP2), value=0x0)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SHA3
            + Op.SSTORE
            + Op.PUSH1[0x1C]
            + Op.PUSH1[0x40]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.ADD
            + Op.MSTORE(offset=Op.DUP2, value=Op.MLOAD(offset=0x80))
            + Op.LOG3(
                offset=Op.DUP5,
                size=0x20,
                topic_1=0x301CD746DBB5E7F9ADE2BCD9E8A849B968BFCC222DE48D2086BA200184ACC83D,  # noqa: E501
                topic_2=Op.MLOAD(offset=0x40),
                topic_3=Op.CALLER,
            )
            + Op.POP
            + Op.MSTORE(offset=0xCC0, value=Op.MLOAD(offset=0xC80))
            + Op.RETURN(offset=0xCC0, size=0x20)
            + Op.JUMPDEST
            + Op.MSTORE(offset=0xCE0, value=0x0)
            + Op.RETURN(offset=0xCE0, size=0x20)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x1982, condition=Op.ISZERO(Op.EQ(Op.DUP2, 0xE1ED3AD3))
            )
            + Op.MSTORE(offset=0x80, value=Op.CALLDATALOAD(offset=0x4))
            + Op.MSTORE(offset=0x40, value=Op.CALLDATALOAD(offset=0x24))
            + Op.PUSH1[0x80]
            + Op.PUSH1[0x80]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x4)
            + Op.MSTORE(offset=Op.ADD(0x20, Op.DUP2), value=Op.CALLER)
            + Op.MSTORE(
                offset=Op.ADD(0x40, Op.DUP2), value=Op.MLOAD(offset=0x40)
            )
            + Op.MSTORE(offset=Op.ADD(0x60, Op.DUP2), value=0x0)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.MSTORE(offset=0x400, value=Op.SLOAD(key=Op.SHA3))
            + Op.JUMPI(
                pc=0x1975,
                condition=Op.ISZERO(
                    Op.ISZERO(
                        Op.SLT(Op.MLOAD(offset=0x400), Op.MLOAD(offset=0x80)),
                    ),
                ),
            )
            + Op.SUB(Op.MLOAD(offset=0x400), Op.MLOAD(offset=0x80))
            + Op.PUSH1[0x80]
            + Op.PUSH1[0x80]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x4)
            + Op.MSTORE(offset=Op.ADD(0x20, Op.DUP2), value=Op.CALLER)
            + Op.MSTORE(
                offset=Op.ADD(0x40, Op.DUP2), value=Op.MLOAD(offset=0x40)
            )
            + Op.MSTORE(offset=Op.ADD(0x60, Op.DUP2), value=0x0)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SHA3
            + Op.SSTORE
            + Op.PUSH1[0x1C]
            + Op.PUSH1[0x64]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.ADD
            + Op.MSTORE(offset=Op.SUB(Op.DUP3, 0x1C), value=0x86744558)
            + Op.MSTORE(offset=Op.ADD(Op.DUP3, 0x4), value=Op.CALLER)
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP3, 0x24), value=Op.MLOAD(offset=0x80)
            )
            + Op.POP(
                Op.CALL(
                    gas=Op.SUB(Op.GAS, 0x2D),
                    address=Op.SLOAD(
                        key=Op.ADD(0x2, Op.MUL(Op.MLOAD(offset=0x40), 0xC)),
                    ),
                    value=0x0,
                    args_offset=Op.DUP4,
                    args_size=0x44,
                    ret_offset=0xD60,
                    ret_size=0x20,
                ),
            )
            + Op.MLOAD(offset=0xD60)
            + Op.SWAP1
            + Op.POP
            + Op.PUSH2[0xD40]
            + Op.MSTORE
            + Op.PUSH1[0x1C]
            + Op.PUSH1[0x40]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.ADD
            + Op.MSTORE(offset=Op.DUP2, value=Op.MLOAD(offset=0x80))
            + Op.LOG3(
                offset=Op.DUP5,
                size=0x20,
                topic_1=0xFA4460934F383B326D79DCD4F1E59A17AC8EE9A87312169933E7F68B85C1A8CE,  # noqa: E501
                topic_2=Op.MLOAD(offset=0x40),
                topic_3=Op.CALLER,
            )
            + Op.POP
            + Op.MSTORE(offset=0xD80, value=Op.MLOAD(offset=0xD40))
            + Op.RETURN(offset=0xD80, size=0x20)
            + Op.JUMPDEST
            + Op.MSTORE(offset=0xDA0, value=0x0)
            + Op.RETURN(offset=0xDA0, size=0x20)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x1F08, condition=Op.ISZERO(Op.EQ(Op.DUP2, 0x327A22F1))
            )
            + Op.MSTORE(offset=0x1C0, value=Op.CALLDATALOAD(offset=0x4))
            + Op.MSTORE(
                offset=0x700,
                value=Op.SLOAD(
                    key=Op.ADD(
                        0xE0000000000000000000000000000000000000001,
                        Op.MUL(Op.MLOAD(offset=0x1C0), 0x8),
                    ),
                ),
            )
            + Op.MSTORE(
                offset=0x80,
                value=Op.SLOAD(
                    key=Op.ADD(
                        0xE0000000000000000000000000000000000000003,
                        Op.MUL(Op.MLOAD(offset=0x1C0), 0x8),
                    ),
                ),
            )
            + Op.MSTORE(
                offset=0xA0,
                value=Op.SLOAD(
                    key=Op.ADD(
                        0xE0000000000000000000000000000000000000004,
                        Op.MUL(Op.MLOAD(offset=0x1C0), 0x8),
                    ),
                ),
            )
            + Op.MSTORE(
                offset=0x720,
                value=Op.SLOAD(
                    key=Op.ADD(
                        0xE0000000000000000000000000000000000000005,
                        Op.MUL(Op.MLOAD(offset=0x1C0), 0x8),
                    ),
                ),
            )
            + Op.MSTORE(
                offset=0x40,
                value=Op.SLOAD(
                    key=Op.ADD(
                        0xE0000000000000000000000000000000000000002,
                        Op.MUL(Op.MLOAD(offset=0x1C0), 0x8),
                    ),
                ),
            )
            + Op.MSTORE(
                offset=0x680,
                value=Op.SLOAD(
                    key=Op.ADD(0x2, Op.MUL(Op.MLOAD(offset=0x40), 0xC)),
                ),
            )
            + Op.MSTORE(
                offset=0x6A0,
                value=Op.SLOAD(
                    key=Op.ADD(0x3, Op.MUL(Op.MLOAD(offset=0x40), 0xC)),
                ),
            )
            + Op.MSTORE(
                offset=0x6C0,
                value=Op.SLOAD(
                    key=Op.ADD(0x4, Op.MUL(Op.MLOAD(offset=0x40), 0xC)),
                ),
            )
            + Op.JUMPI(
                pc=0x1EFB,
                condition=Op.ISZERO(Op.EQ(Op.CALLER, Op.MLOAD(offset=0x720))),
            )
            + Op.SSTORE(
                key=Op.ADD(
                    0xE0000000000000000000000000000000000000000,
                    Op.MUL(Op.MLOAD(offset=0x1C0), 0x8),
                ),
                value=0x0,
            )
            + Op.SSTORE(
                key=Op.ADD(
                    0xE0000000000000000000000000000000000000001,
                    Op.MUL(Op.MLOAD(offset=0x1C0), 0x8),
                ),
                value=0x0,
            )
            + Op.SSTORE(
                key=Op.ADD(
                    0xE0000000000000000000000000000000000000002,
                    Op.MUL(Op.MLOAD(offset=0x1C0), 0x8),
                ),
                value=0x0,
            )
            + Op.SSTORE(
                key=Op.ADD(
                    0xE0000000000000000000000000000000000000003,
                    Op.MUL(Op.MLOAD(offset=0x1C0), 0x8),
                ),
                value=0x0,
            )
            + Op.SSTORE(
                key=Op.ADD(
                    0xE0000000000000000000000000000000000000004,
                    Op.MUL(Op.MLOAD(offset=0x1C0), 0x8),
                ),
                value=0x0,
            )
            + Op.SSTORE(
                key=Op.ADD(
                    0xE0000000000000000000000000000000000000005,
                    Op.MUL(Op.MLOAD(offset=0x1C0), 0x8),
                ),
                value=0x0,
            )
            + Op.SSTORE(
                key=Op.ADD(
                    0xE0000000000000000000000000000000000000006,
                    Op.MUL(Op.MLOAD(offset=0x1C0), 0x8),
                ),
                value=0x0,
            )
            + Op.SSTORE(
                key=Op.ADD(
                    0xE0000000000000000000000000000000000000007,
                    Op.MUL(Op.MLOAD(offset=0x1C0), 0x8),
                ),
                value=0x0,
            )
            + Op.PUSH1[0xA0]
            + Op.PUSH1[0xA0]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x40)
            )
            + Op.MSTORE(offset=Op.ADD(0x40, Op.DUP2), value=0xC)
            + Op.MSTORE(
                offset=Op.ADD(0x60, Op.DUP2), value=Op.MLOAD(offset=0x1C0)
            )
            + Op.MSTORE(offset=Op.ADD(0x80, Op.DUP2), value=0x2)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.MSTORE(offset=0x820, value=Op.SLOAD(key=Op.SHA3))
            + Op.PUSH1[0xA0]
            + Op.PUSH1[0xA0]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x40)
            )
            + Op.MSTORE(offset=Op.ADD(0x40, Op.DUP2), value=0xC)
            + Op.MSTORE(
                offset=Op.ADD(0x60, Op.DUP2), value=Op.MLOAD(offset=0x1C0)
            )
            + Op.MSTORE(offset=Op.ADD(0x80, Op.DUP2), value=0x1)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.MSTORE(offset=0x860, value=Op.SLOAD(key=Op.SHA3))
            + Op.JUMPI(pc=0x1C00, condition=Op.ISZERO(Op.MLOAD(offset=0x820)))
            + Op.MLOAD(offset=0x860)
            + Op.JUMP(pc=0x1C03)
            + Op.JUMPDEST
            + Op.PUSH1[0x0]
            + Op.JUMPDEST
            + Op.JUMPI(pc=0x1C7D, condition=Op.ISZERO)
            + Op.MLOAD(offset=0x860)
            + Op.PUSH1[0xA0]
            + Op.PUSH1[0xA0]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x40)
            )
            + Op.MSTORE(offset=Op.ADD(0x40, Op.DUP2), value=0xC)
            + Op.MSTORE(
                offset=Op.ADD(0x60, Op.DUP2), value=Op.MLOAD(offset=0x820)
            )
            + Op.MSTORE(offset=Op.ADD(0x80, Op.DUP2), value=0x1)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SHA3
            + Op.SSTORE
            + Op.MLOAD(offset=0x820)
            + Op.PUSH1[0xA0]
            + Op.PUSH1[0xA0]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x40)
            )
            + Op.MSTORE(offset=Op.ADD(0x40, Op.DUP2), value=0xC)
            + Op.MSTORE(
                offset=Op.ADD(0x60, Op.DUP2), value=Op.MLOAD(offset=0x860)
            )
            + Op.MSTORE(offset=Op.ADD(0x80, Op.DUP2), value=0x2)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SHA3
            + Op.SSTORE
            + Op.JUMP(pc=0x1CCC)
            + Op.JUMPDEST
            + Op.JUMPI(pc=0x1CCB, condition=Op.ISZERO(Op.MLOAD(offset=0x820)))
            + Op.SSTORE(
                key=Op.ADD(0xB, Op.MUL(Op.MLOAD(offset=0x40), 0xC)),
                value=Op.MLOAD(offset=0x820),
            )
            + Op.PUSH1[0x0]
            + Op.PUSH1[0xA0]
            + Op.PUSH1[0xA0]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x40)
            )
            + Op.MSTORE(offset=Op.ADD(0x40, Op.DUP2), value=0xC)
            + Op.MSTORE(
                offset=Op.ADD(0x60, Op.DUP2), value=Op.MLOAD(offset=0x820)
            )
            + Op.MSTORE(offset=Op.ADD(0x80, Op.DUP2), value=0x1)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SHA3
            + Op.SSTORE
            + Op.JUMPDEST
            + Op.JUMPDEST
            + Op.JUMPI(pc=0x1D0C, condition=Op.ISZERO(Op.MLOAD(offset=0x860)))
            + Op.PUSH1[0x0]
            + Op.PUSH1[0xA0]
            + Op.PUSH1[0xA0]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x40)
            )
            + Op.MSTORE(offset=Op.ADD(0x40, Op.DUP2), value=0xC)
            + Op.MSTORE(
                offset=Op.ADD(0x60, Op.DUP2), value=Op.MLOAD(offset=0x1C0)
            )
            + Op.MSTORE(offset=Op.ADD(0x80, Op.DUP2), value=0x1)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SHA3
            + Op.SSTORE
            + Op.JUMPDEST
            + Op.JUMPI(pc=0x1D4C, condition=Op.ISZERO(Op.MLOAD(offset=0x820)))
            + Op.PUSH1[0x0]
            + Op.PUSH1[0xA0]
            + Op.PUSH1[0xA0]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x40)
            )
            + Op.MSTORE(offset=Op.ADD(0x40, Op.DUP2), value=0xC)
            + Op.MSTORE(
                offset=Op.ADD(0x60, Op.DUP2), value=Op.MLOAD(offset=0x1C0)
            )
            + Op.MSTORE(offset=Op.ADD(0x80, Op.DUP2), value=0x2)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SHA3
            + Op.SSTORE
            + Op.JUMPDEST
            + Op.PUSH1[0x0]
            + Op.PUSH1[0xA0]
            + Op.PUSH1[0xA0]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x40)
            )
            + Op.MSTORE(offset=Op.ADD(0x40, Op.DUP2), value=0xC)
            + Op.MSTORE(
                offset=Op.ADD(0x60, Op.DUP2), value=Op.MLOAD(offset=0x1C0)
            )
            + Op.MSTORE(offset=Op.ADD(0x80, Op.DUP2), value=0x0)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SHA3
            + Op.SSTORE
            + Op.SSTORE(
                key=Op.ADD(0xA, Op.MUL(Op.MLOAD(offset=0x40), 0xC)),
                value=Op.SUB(
                    Op.SLOAD(
                        key=Op.ADD(0xA, Op.MUL(Op.MLOAD(offset=0x40), 0xC))
                    ),
                    0x1,
                ),
            )
            + Op.JUMPI(
                pc=0x1DDE,
                condition=Op.ISZERO(Op.EQ(Op.MLOAD(offset=0x700), 0x1)),
            )
            + Op.MSTORE(
                offset=0x120,
                value=Op.MUL(
                    Op.SDIV(
                        Op.MUL(Op.MLOAD(offset=0x80), Op.MLOAD(offset=0xA0)),
                        Op.MUL(
                            Op.MLOAD(offset=0x6C0),
                            Op.EXP(0xA, Op.MLOAD(offset=0x6A0)),
                        ),
                    ),
                    0xDE0B6B3A7640000,
                ),
            )
            + Op.POP(
                Op.CALL(
                    gas=0x1388,
                    address=Op.CALLER,
                    value=Op.MLOAD(offset=0x120),
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.JUMP(pc=0x1E9C)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x1E9B,
                condition=Op.ISZERO(Op.EQ(Op.MLOAD(offset=0x700), 0x2)),
            )
            + Op.MLOAD(offset=0x80)
            + Op.PUSH1[0x80]
            + Op.PUSH1[0x80]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x4)
            + Op.MSTORE(offset=Op.ADD(0x20, Op.DUP2), value=Op.CALLER)
            + Op.MSTORE(
                offset=Op.ADD(0x40, Op.DUP2), value=Op.MLOAD(offset=0x40)
            )
            + Op.MSTORE(offset=Op.ADD(0x60, Op.DUP2), value=0x1)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SLOAD(key=Op.SHA3)
            + Op.SUB
            + Op.PUSH1[0x80]
            + Op.PUSH1[0x80]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x4)
            + Op.MSTORE(offset=Op.ADD(0x20, Op.DUP2), value=Op.CALLER)
            + Op.MSTORE(
                offset=Op.ADD(0x40, Op.DUP2), value=Op.MLOAD(offset=0x40)
            )
            + Op.MSTORE(offset=Op.ADD(0x60, Op.DUP2), value=0x1)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SHA3
            + Op.SSTORE
            + Op.MLOAD(offset=0x80)
            + Op.PUSH1[0x80]
            + Op.PUSH1[0x80]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x4)
            + Op.MSTORE(offset=Op.ADD(0x20, Op.DUP2), value=Op.CALLER)
            + Op.MSTORE(
                offset=Op.ADD(0x40, Op.DUP2), value=Op.MLOAD(offset=0x40)
            )
            + Op.MSTORE(offset=Op.ADD(0x60, Op.DUP2), value=0x0)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SLOAD(key=Op.SHA3)
            + Op.ADD
            + Op.PUSH1[0x80]
            + Op.PUSH1[0x80]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x4)
            + Op.MSTORE(offset=Op.ADD(0x20, Op.DUP2), value=Op.CALLER)
            + Op.MSTORE(
                offset=Op.ADD(0x40, Op.DUP2), value=Op.MLOAD(offset=0x40)
            )
            + Op.MSTORE(offset=Op.ADD(0x60, Op.DUP2), value=0x0)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.SHA3
            + Op.SSTORE
            + Op.JUMPDEST
            + Op.JUMPDEST
            + Op.PUSH1[0x1C]
            + Op.PUSH1[0xA0]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.ADD
            + Op.MSTORE(offset=Op.DUP2, value=Op.CALLER)
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP3, 0x20), value=Op.MLOAD(offset=0xA0)
            )
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP3, 0x40), value=Op.MLOAD(offset=0x80)
            )
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP3, 0x60), value=Op.MLOAD(offset=0x1C0)
            )
            + Op.LOG2(
                offset=Op.DUP4,
                size=0x80,
                topic_1=0xAC6333455D304288767A0F1039D666D16882D10B6EA83693D2556E4C8098001,  # noqa: E501
                topic_2=Op.MLOAD(offset=0x40),
            )
            + Op.POP
            + Op.MSTORE(offset=0xF40, value=0x1)
            + Op.RETURN(offset=0xF40, size=0x20)
            + Op.JUMPDEST
            + Op.MSTORE(offset=0xF60, value=0x0)
            + Op.RETURN(offset=0xF60, size=0x20)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x22F0, condition=Op.ISZERO(Op.EQ(Op.DUP2, 0xD91E22F4))
            )
            + Op.MSTORE(offset=0xF80, value=Op.CALLDATALOAD(offset=0x4))
            + Op.MSTORE(offset=0x680, value=Op.CALLDATALOAD(offset=0x24))
            + Op.MSTORE(offset=0x6A0, value=Op.CALLDATALOAD(offset=0x44))
            + Op.MSTORE(offset=0x6C0, value=Op.CALLDATALOAD(offset=0x64))
            + Op.MSTORE(offset=0x6E0, value=Op.CALLDATALOAD(offset=0x84))
            + Op.MSTORE(offset=0xFA0, value=Op.CALLDATALOAD(offset=0xA4))
            + Op.MSTORE(
                offset=0xFC0,
                value=Op.ADD(
                    Op.SLOAD(key=0x160000000000000000000000000000000000000000),
                    0x1,
                ),
            )
            + Op.JUMPI(
                pc=0x1F76,
                condition=Op.ISZERO(
                    Op.ISZERO(Op.SGT(Op.MLOAD(offset=0xF80), 0x0)),
                ),
            )
            + Op.MSTORE(offset=0xFE0, value=0x1E)
            + Op.RETURN(offset=0xFE0, size=0x20)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x1FA4,
                condition=Op.ISZERO(
                    Op.SLOAD(
                        key=Op.ADD(
                            0xD0000000000000000000000000000000000000000,
                            Op.MLOAD(offset=0xF80),
                        ),
                    ),
                ),
            )
            + Op.MSTORE(offset=0x1000, value=0x1F)
            + Op.RETURN(offset=0x1000, size=0x20)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x1FBE,
                condition=Op.ISZERO(
                    Op.ISZERO(Op.SGT(Op.MLOAD(offset=0x680), 0x0)),
                ),
            )
            + Op.MSTORE(offset=0x1020, value=0x20)
            + Op.RETURN(offset=0x1020, size=0x20)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x1FD7,
                condition=Op.ISZERO(Op.SLT(Op.MLOAD(offset=0xFA0), 0x0)),
            )
            + Op.MSTORE(offset=0x1040, value=0x21)
            + Op.RETURN(offset=0x1040, size=0x20)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x1FF0,
                condition=Op.ISZERO(Op.SLT(Op.MLOAD(offset=0x6A0), 0x0)),
            )
            + Op.MSTORE(offset=0x1060, value=0x22)
            + Op.RETURN(offset=0x1060, size=0x20)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x2009,
                condition=Op.ISZERO(Op.SLT(Op.MLOAD(offset=0x6C0), 0x0)),
            )
            + Op.MSTORE(offset=0x1080, value=0x23)
            + Op.RETURN(offset=0x1080, size=0x20)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x2022,
                condition=Op.ISZERO(Op.SLT(Op.MLOAD(offset=0x6E0), 0x0)),
            )
            + Op.MSTORE(offset=0x10A0, value=0x24)
            + Op.RETURN(offset=0x10A0, size=0x20)
            + Op.JUMPDEST
            + Op.PUSH1[0x0]
            + Op.PUSH1[0x1C]
            + Op.PUSH1[0x64]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.ADD
            + Op.MSTORE(offset=Op.SUB(Op.DUP3, 0x1C), value=0xC32D01A1)
            + Op.MSTORE(offset=Op.ADD(Op.DUP3, 0x4), value=Op.CALLER)
            + Op.MSTORE(offset=Op.ADD(Op.DUP3, 0x24), value=Op.ADDRESS)
            + Op.POP(
                Op.CALL(
                    gas=Op.SUB(Op.GAS, 0x2D),
                    address=Op.MLOAD(offset=0x680),
                    value=0x0,
                    args_offset=Op.DUP4,
                    args_size=0x44,
                    ret_offset=0x10C0,
                    ret_size=0x20,
                ),
            )
            + Op.MLOAD(offset=0x10C0)
            + Op.SWAP1
            + Op.POP
            + Op.JUMPI(pc=0x2075, condition=Op.ISZERO(Op.ISZERO(Op.EQ)))
            + Op.MSTORE(offset=0x10E0, value=0x28)
            + Op.RETURN(offset=0x10E0, size=0x20)
            + Op.JUMPDEST
            + Op.PUSH1[0x1]
            + Op.PUSH1[0x1C]
            + Op.PUSH1[0x64]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.ADD
            + Op.MSTORE(offset=Op.SUB(Op.DUP3, 0x1C), value=0x83B58638)
            + Op.MSTORE(offset=Op.ADD(Op.DUP3, 0x4), value=Op.ADDRESS)
            + Op.MSTORE(offset=Op.ADD(Op.DUP3, 0x24), value=0x0)
            + Op.POP(
                Op.CALL(
                    gas=Op.SUB(Op.GAS, 0x2D),
                    address=Op.MLOAD(offset=0x680),
                    value=0x0,
                    args_offset=Op.DUP4,
                    args_size=0x44,
                    ret_offset=0x1100,
                    ret_size=0x20,
                ),
            )
            + Op.MLOAD(offset=0x1100)
            + Op.SWAP1
            + Op.POP
            + Op.JUMPI(pc=0x20C9, condition=Op.ISZERO(Op.ISZERO(Op.EQ)))
            + Op.MSTORE(offset=0x1120, value=0x29)
            + Op.RETURN(offset=0x1120, size=0x20)
            + Op.JUMPDEST
            + Op.PUSH1[0x0]
            + Op.PUSH1[0x1C]
            + Op.PUSH1[0x44]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.ADD
            + Op.MSTORE(offset=Op.SUB(Op.DUP3, 0x1C), value=0x26690247)
            + Op.MSTORE(offset=Op.ADD(Op.DUP3, 0x4), value=Op.ADDRESS)
            + Op.POP(
                Op.CALL(
                    gas=Op.SUB(Op.GAS, 0x2D),
                    address=Op.MLOAD(offset=0x680),
                    value=0x0,
                    args_offset=Op.DUP4,
                    args_size=0x24,
                    ret_offset=0x1140,
                    ret_size=0x20,
                ),
            )
            + Op.MLOAD(offset=0x1140)
            + Op.SWAP1
            + Op.POP
            + Op.JUMPI(pc=0x2116, condition=Op.ISZERO(Op.ISZERO(Op.EQ)))
            + Op.MSTORE(offset=0x1160, value=0x2A)
            + Op.RETURN(offset=0x1160, size=0x20)
            + Op.JUMPDEST
            + Op.PUSH1[0x0]
            + Op.PUSH1[0x1C]
            + Op.PUSH1[0x64]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.ADD
            + Op.MSTORE(offset=Op.SUB(Op.DUP3, 0x1C), value=0x86744558)
            + Op.MSTORE(offset=Op.ADD(Op.DUP3, 0x4), value=Op.CALLER)
            + Op.MSTORE(offset=Op.ADD(Op.DUP3, 0x24), value=0x0)
            + Op.POP(
                Op.CALL(
                    gas=Op.SUB(Op.GAS, 0x2D),
                    address=Op.MLOAD(offset=0x680),
                    value=0x0,
                    args_offset=Op.DUP4,
                    args_size=0x44,
                    ret_offset=0x1180,
                    ret_size=0x20,
                ),
            )
            + Op.MLOAD(offset=0x1180)
            + Op.SWAP1
            + Op.POP
            + Op.JUMPI(pc=0x216A, condition=Op.ISZERO(Op.ISZERO(Op.EQ)))
            + Op.MSTORE(offset=0x11A0, value=0x2B)
            + Op.RETURN(offset=0x11A0, size=0x20)
            + Op.JUMPDEST
            + Op.PUSH1[0x0]
            + Op.PUSH1[0x1C]
            + Op.PUSH1[0x84]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.ADD
            + Op.MSTORE(offset=Op.SUB(Op.DUP3, 0x1C), value=0x27F08B00)
            + Op.MSTORE(offset=Op.ADD(Op.DUP3, 0x4), value=Op.ADDRESS)
            + Op.MSTORE(offset=Op.ADD(Op.DUP3, 0x24), value=Op.CALLER)
            + Op.MSTORE(offset=Op.ADD(Op.DUP3, 0x44), value=0x0)
            + Op.POP(
                Op.CALL(
                    gas=Op.SUB(Op.GAS, 0x2D),
                    address=Op.MLOAD(offset=0x680),
                    value=0x0,
                    args_offset=Op.DUP4,
                    args_size=0x64,
                    ret_offset=0x11C0,
                    ret_size=0x20,
                ),
            )
            + Op.MLOAD(offset=0x11C0)
            + Op.SWAP1
            + Op.POP
            + Op.JUMPI(pc=0x21C4, condition=Op.ISZERO(Op.ISZERO(Op.EQ)))
            + Op.MSTORE(offset=0x11E0, value=0x2C)
            + Op.RETURN(offset=0x11E0, size=0x20)
            + Op.JUMPDEST
            + Op.SSTORE(
                key=Op.MUL(Op.MLOAD(offset=0xFC0), 0xC),
                value=Op.MLOAD(offset=0xFC0),
            )
            + Op.SSTORE(
                key=Op.ADD(0x1, Op.MUL(Op.MLOAD(offset=0xFC0), 0xC)),
                value=Op.MLOAD(offset=0xF80),
            )
            + Op.SSTORE(
                key=Op.ADD(0x2, Op.MUL(Op.MLOAD(offset=0xFC0), 0xC)),
                value=Op.MLOAD(offset=0x680),
            )
            + Op.SSTORE(
                key=Op.ADD(0x6, Op.MUL(Op.MLOAD(offset=0xFC0), 0xC)),
                value=Op.MLOAD(offset=0xFA0),
            )
            + Op.SSTORE(
                key=Op.ADD(0x3, Op.MUL(Op.MLOAD(offset=0xFC0), 0xC)),
                value=Op.MLOAD(offset=0x6A0),
            )
            + Op.SSTORE(
                key=Op.ADD(0x4, Op.MUL(Op.MLOAD(offset=0xFC0), 0xC)),
                value=Op.MLOAD(offset=0x6C0),
            )
            + Op.SSTORE(
                key=Op.ADD(0x5, Op.MUL(Op.MLOAD(offset=0xFC0), 0xC)),
                value=Op.MLOAD(offset=0x6E0),
            )
            + Op.SSTORE(
                key=Op.ADD(0x7, Op.MUL(Op.MLOAD(offset=0xFC0), 0xC)),
                value=0x1,
            )
            + Op.SSTORE(
                key=Op.ADD(0x8, Op.MUL(Op.MLOAD(offset=0xFC0), 0xC)),
                value=Op.CALLER,
            )
            + Op.SSTORE(
                key=Op.ADD(0x9, Op.MUL(Op.MLOAD(offset=0xFC0), 0xC)),
                value=Op.NUMBER,
            )
            + Op.SSTORE(
                key=Op.ADD(
                    0xC0000000000000000000000000000000000000000,
                    Op.MLOAD(offset=0x680),
                ),
                value=Op.MLOAD(offset=0xFC0),
            )
            + Op.SSTORE(
                key=Op.ADD(
                    0xD0000000000000000000000000000000000000000,
                    Op.MLOAD(offset=0xF80),
                ),
                value=Op.MLOAD(offset=0xFC0),
            )
            + Op.SSTORE(
                key=0x160000000000000000000000000000000000000000,
                value=Op.MLOAD(offset=0xFC0),
            )
            + Op.PUSH1[0x1C]
            + Op.PUSH1[0x40]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.ADD
            + Op.MSTORE(offset=Op.DUP2, value=Op.MLOAD(offset=0xFC0))
            + Op.LOG1(
                offset=Op.DUP3,
                size=0x20,
                topic_1=0x1238FE6D44CF796960D61B74766B3A383110E472D849F5CA16AE50215BC05E58,  # noqa: E501
            )
            + Op.POP
            + Op.MSTORE(offset=0x1200, value=0x1)
            + Op.RETURN(offset=0x1200, size=0x20)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x232A, condition=Op.ISZERO(Op.EQ(Op.DUP2, 0x41569661))
            )
            + Op.MSTORE(offset=0x1220, value=Op.CALLDATALOAD(offset=0x4))
            + Op.MSTORE(
                offset=0x1240,
                value=Op.SLOAD(
                    key=Op.ADD(
                        0xC0000000000000000000000000000000000000000,
                        Op.MLOAD(offset=0x1220),
                    ),
                ),
            )
            + Op.RETURN(offset=0x1240, size=0x20)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x2364, condition=Op.ISZERO(Op.EQ(Op.DUP2, 0xFCDE9F78))
            )
            + Op.MSTORE(offset=0xF80, value=Op.CALLDATALOAD(offset=0x4))
            + Op.MSTORE(
                offset=0x1260,
                value=Op.SLOAD(
                    key=Op.ADD(
                        0xD0000000000000000000000000000000000000000,
                        Op.MLOAD(offset=0xF80),
                    ),
                ),
            )
            + Op.RETURN(offset=0x1260, size=0x20)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x2392, condition=Op.ISZERO(Op.EQ(Op.DUP2, 0x6E5B4343))
            )
            + Op.MSTORE(
                offset=0x1280,
                value=Op.SLOAD(
                    key=0x160000000000000000000000000000000000000000
                ),
            )
            + Op.RETURN(offset=0x1280, size=0x20)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x24E6, condition=Op.ISZERO(Op.EQ(Op.DUP2, 0xFAFA69C2))
            )
            + Op.MSTORE(offset=0xFC0, value=Op.CALLDATALOAD(offset=0x4))
            + Op.PUSH2[0x180]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0xB)
            + Op.ADD(Op.DUP2, 0x20)
            + Op.SWAP1
            + Op.POP
            + Op.PUSH2[0x12A0]
            + Op.MSTORE
            + Op.MSTORE(
                offset=Op.MLOAD(offset=0x12A0),
                value=Op.SLOAD(key=Op.MUL(Op.MLOAD(offset=0xFC0), 0xC)),
            )
            + Op.MSTORE(
                offset=Op.ADD(Op.MLOAD(offset=0x12A0), 0x20),
                value=Op.SLOAD(
                    key=Op.ADD(0x1, Op.MUL(Op.MLOAD(offset=0xFC0), 0xC)),
                ),
            )
            + Op.MSTORE(
                offset=Op.ADD(Op.MLOAD(offset=0x12A0), 0x40),
                value=Op.SLOAD(
                    key=Op.ADD(0x2, Op.MUL(Op.MLOAD(offset=0xFC0), 0xC)),
                ),
            )
            + Op.MSTORE(
                offset=Op.ADD(Op.MLOAD(offset=0x12A0), 0x60),
                value=Op.SLOAD(
                    key=Op.ADD(0x3, Op.MUL(Op.MLOAD(offset=0xFC0), 0xC)),
                ),
            )
            + Op.MSTORE(
                offset=Op.ADD(Op.MLOAD(offset=0x12A0), 0x80),
                value=Op.SLOAD(
                    key=Op.ADD(0x4, Op.MUL(Op.MLOAD(offset=0xFC0), 0xC)),
                ),
            )
            + Op.MSTORE(
                offset=Op.ADD(Op.MLOAD(offset=0x12A0), 0xA0),
                value=Op.SLOAD(
                    key=Op.ADD(0x5, Op.MUL(Op.MLOAD(offset=0xFC0), 0xC)),
                ),
            )
            + Op.MSTORE(
                offset=Op.ADD(Op.MLOAD(offset=0x12A0), 0xC0),
                value=Op.SLOAD(
                    key=Op.ADD(0x7, Op.MUL(Op.MLOAD(offset=0xFC0), 0xC)),
                ),
            )
            + Op.MSTORE(
                offset=Op.ADD(Op.MLOAD(offset=0x12A0), 0xE0),
                value=Op.SLOAD(
                    key=Op.ADD(0x8, Op.MUL(Op.MLOAD(offset=0xFC0), 0xC)),
                ),
            )
            + Op.MSTORE(
                offset=Op.ADD(Op.MLOAD(offset=0x12A0), 0x100),
                value=Op.SLOAD(
                    key=Op.ADD(0x9, Op.MUL(Op.MLOAD(offset=0xFC0), 0xC)),
                ),
            )
            + Op.MSTORE(
                offset=Op.ADD(Op.MLOAD(offset=0x12A0), 0x120),
                value=Op.SLOAD(
                    key=Op.ADD(0xA, Op.MUL(Op.MLOAD(offset=0xFC0), 0xC)),
                ),
            )
            + Op.MSTORE(
                offset=Op.ADD(Op.MLOAD(offset=0x12A0), 0x140),
                value=Op.SLOAD(
                    key=Op.ADD(0x6, Op.MUL(Op.MLOAD(offset=0xFC0), 0xC)),
                ),
            )
            + Op.JUMPI(pc=0x24B2, condition=Op.ISZERO(Op.MLOAD(offset=0x12A0)))
            + Op.MLOAD(offset=0x12A0)
            + Op.MSTORE(offset=Op.SUB(Op.DUP3, 0x40), value=0x20)
            + Op.RETURN(
                offset=Op.SUB(Op.DUP3, 0x40),
                size=Op.ADD(
                    0x40,
                    Op.MUL(Op.MLOAD(offset=Op.SUB(Op.DUP3, 0x20)), 0x20),
                ),
            )
            + Op.POP
            + Op.JUMPDEST
            + Op.PUSH1[0x40]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x1)
            + Op.MSTORE(offset=Op.ADD(Op.DUP3, 0x20), value=0x0)
            + Op.ADD(Op.DUP2, 0x20)
            + Op.SWAP1
            + Op.POP
            + Op.MSTORE(offset=Op.SUB(Op.DUP3, 0x40), value=0x20)
            + Op.RETURN(
                offset=Op.SUB(Op.DUP3, 0x40),
                size=Op.ADD(
                    0x40,
                    Op.MUL(Op.MLOAD(offset=Op.SUB(Op.DUP3, 0x20)), 0x20),
                ),
            )
            + Op.POP
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x262E, condition=Op.ISZERO(Op.EQ(Op.DUP2, 0x9CFC1535))
            )
            + Op.MSTORE(offset=0x40, value=Op.CALLDATALOAD(offset=0x4))
            + Op.MSTORE(
                offset=0x1340,
                value=Op.SLOAD(
                    key=Op.ADD(0xA, Op.MUL(Op.MLOAD(offset=0x40), 0xC)),
                ),
            )
            + Op.MSTORE(
                offset=0x1C0,
                value=Op.SLOAD(
                    key=Op.ADD(0xB, Op.MUL(Op.MLOAD(offset=0x40), 0xC)),
                ),
            )
            + Op.MLOAD(offset=0x1340)
            + Op.ADD(0x20, Op.MUL(0x20, Op.DUP1))
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=Op.DUP2)
            + Op.ADD(Op.DUP2, 0x20)
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.POP
            + Op.PUSH2[0x600]
            + Op.MSTORE
            + Op.MSTORE(offset=0x13A0, value=0x0)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x25D4,
                condition=Op.ISZERO(
                    Op.SLT(Op.MLOAD(offset=0x13A0), Op.MLOAD(offset=0x1340)),
                ),
            )
            + Op.PUSH1[0xA0]
            + Op.PUSH1[0xA0]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x40)
            )
            + Op.MSTORE(offset=Op.ADD(0x40, Op.DUP2), value=0xC)
            + Op.MSTORE(
                offset=Op.ADD(0x60, Op.DUP2), value=Op.MLOAD(offset=0x1C0)
            )
            + Op.MSTORE(offset=Op.ADD(0x80, Op.DUP2), value=0x0)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.MSTORE(
                offset=Op.ADD(
                    Op.MLOAD(offset=0x600),
                    Op.MUL(0x20, Op.MLOAD(offset=0x13A0)),
                ),
                value=Op.SLOAD(key=Op.SHA3),
            )
            + Op.PUSH1[0xA0]
            + Op.PUSH1[0xA0]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x0)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2), value=Op.MLOAD(offset=0x40)
            )
            + Op.MSTORE(offset=Op.ADD(0x40, Op.DUP2), value=0xC)
            + Op.MSTORE(
                offset=Op.ADD(0x60, Op.DUP2), value=Op.MLOAD(offset=0x1C0)
            )
            + Op.MSTORE(offset=Op.ADD(0x80, Op.DUP2), value=0x2)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.MSTORE(offset=0x1C0, value=Op.SLOAD(key=Op.SHA3))
            + Op.MSTORE(
                offset=0x13A0, value=Op.ADD(Op.MLOAD(offset=0x13A0), 0x1)
            )
            + Op.JUMP(pc=0x253D)
            + Op.JUMPDEST
            + Op.JUMPI(pc=0x25FA, condition=Op.ISZERO(Op.MLOAD(offset=0x600)))
            + Op.MLOAD(offset=0x600)
            + Op.MSTORE(offset=Op.SUB(Op.DUP3, 0x40), value=0x20)
            + Op.RETURN(
                offset=Op.SUB(Op.DUP3, 0x40),
                size=Op.ADD(
                    0x40,
                    Op.MUL(Op.MLOAD(offset=Op.SUB(Op.DUP3, 0x20)), 0x20),
                ),
            )
            + Op.POP
            + Op.JUMPDEST
            + Op.PUSH1[0x40]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x1)
            + Op.MSTORE(offset=Op.ADD(Op.DUP3, 0x20), value=0x0)
            + Op.ADD(Op.DUP2, 0x20)
            + Op.SWAP1
            + Op.POP
            + Op.MSTORE(offset=Op.SUB(Op.DUP3, 0x40), value=0x20)
            + Op.RETURN(
                offset=Op.SUB(Op.DUP3, 0x40),
                size=Op.ADD(
                    0x40,
                    Op.MUL(Op.MLOAD(offset=Op.SUB(Op.DUP3, 0x20)), 0x20),
                ),
            )
            + Op.POP
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x27E9, condition=Op.ISZERO(Op.EQ(Op.DUP2, 0xF718190))
            )
            + Op.MSTORE(offset=0xFC0, value=Op.CALLDATALOAD(offset=0x4))
            + Op.PUSH2[0x120]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x8)
            + Op.ADD(Op.DUP2, 0x20)
            + Op.SWAP1
            + Op.POP
            + Op.PUSH2[0x180]
            + Op.MSTORE
            + Op.MSTORE(
                offset=Op.MLOAD(offset=0x180),
                value=Op.SLOAD(
                    key=Op.ADD(
                        0xE0000000000000000000000000000000000000000,
                        Op.MUL(Op.MLOAD(offset=0xFC0), 0x8),
                    ),
                ),
            )
            + Op.MSTORE(
                offset=Op.ADD(Op.MLOAD(offset=0x180), 0x20),
                value=Op.SLOAD(
                    key=Op.ADD(
                        0xE0000000000000000000000000000000000000001,
                        Op.MUL(Op.MLOAD(offset=0xFC0), 0x8),
                    ),
                ),
            )
            + Op.MSTORE(
                offset=Op.ADD(Op.MLOAD(offset=0x180), 0x40),
                value=Op.SLOAD(
                    key=Op.ADD(
                        0xE0000000000000000000000000000000000000002,
                        Op.MUL(Op.MLOAD(offset=0xFC0), 0x8),
                    ),
                ),
            )
            + Op.MSTORE(
                offset=Op.ADD(Op.MLOAD(offset=0x180), 0x60),
                value=Op.SLOAD(
                    key=Op.ADD(
                        0xE0000000000000000000000000000000000000003,
                        Op.MUL(Op.MLOAD(offset=0xFC0), 0x8),
                    ),
                ),
            )
            + Op.MSTORE(
                offset=Op.ADD(Op.MLOAD(offset=0x180), 0x80),
                value=Op.SLOAD(
                    key=Op.ADD(
                        0xE0000000000000000000000000000000000000004,
                        Op.MUL(Op.MLOAD(offset=0xFC0), 0x8),
                    ),
                ),
            )
            + Op.MSTORE(
                offset=Op.ADD(Op.MLOAD(offset=0x180), 0xA0),
                value=Op.SLOAD(
                    key=Op.ADD(
                        0xE0000000000000000000000000000000000000005,
                        Op.MUL(Op.MLOAD(offset=0xFC0), 0x8),
                    ),
                ),
            )
            + Op.MSTORE(
                offset=Op.ADD(Op.MLOAD(offset=0x180), 0xC0),
                value=Op.SLOAD(
                    key=Op.ADD(
                        0xE0000000000000000000000000000000000000006,
                        Op.MUL(Op.MLOAD(offset=0xFC0), 0x8),
                    ),
                ),
            )
            + Op.MSTORE(
                offset=Op.ADD(Op.MLOAD(offset=0x180), 0xE0),
                value=Op.SLOAD(
                    key=Op.ADD(
                        0xE0000000000000000000000000000000000000007,
                        Op.MUL(Op.MLOAD(offset=0xFC0), 0x8),
                    ),
                ),
            )
            + Op.JUMPI(pc=0x27B5, condition=Op.ISZERO(Op.MLOAD(offset=0x180)))
            + Op.MLOAD(offset=0x180)
            + Op.MSTORE(offset=Op.SUB(Op.DUP3, 0x40), value=0x20)
            + Op.RETURN(
                offset=Op.SUB(Op.DUP3, 0x40),
                size=Op.ADD(
                    0x40,
                    Op.MUL(Op.MLOAD(offset=Op.SUB(Op.DUP3, 0x20)), 0x20),
                ),
            )
            + Op.POP
            + Op.JUMPDEST
            + Op.PUSH1[0x40]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x1)
            + Op.MSTORE(offset=Op.ADD(Op.DUP3, 0x20), value=0x0)
            + Op.ADD(Op.DUP2, 0x20)
            + Op.SWAP1
            + Op.POP
            + Op.MSTORE(offset=Op.SUB(Op.DUP3, 0x40), value=0x20)
            + Op.RETURN(
                offset=Op.SUB(Op.DUP3, 0x40),
                size=Op.ADD(
                    0x40,
                    Op.MUL(Op.MLOAD(offset=Op.SUB(Op.DUP3, 0x20)), 0x20),
                ),
            )
            + Op.POP
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x2893, condition=Op.ISZERO(Op.EQ(Op.DUP2, 0x1C9AA4B6))
            )
            + Op.MSTORE(offset=0x1220, value=Op.CALLDATALOAD(offset=0x4))
            + Op.MSTORE(offset=0x40, value=Op.CALLDATALOAD(offset=0x24))
            + Op.PUSH1[0x60]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x2)
            + Op.PUSH1[0x80]
            + Op.PUSH1[0x80]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x4)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2),
                value=Op.MLOAD(offset=0x1220),
            )
            + Op.MSTORE(
                offset=Op.ADD(0x40, Op.DUP2), value=Op.MLOAD(offset=0x40)
            )
            + Op.MSTORE(offset=Op.ADD(0x60, Op.DUP2), value=0x0)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP3, 0x20), value=Op.SLOAD(key=Op.SHA3)
            )
            + Op.PUSH1[0x80]
            + Op.PUSH1[0x80]
            + Op.MSIZE
            + Op.SWAP1
            + Op.MSIZE
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.MSTORE
            + Op.MSTORE(offset=Op.DUP2, value=0x4)
            + Op.MSTORE(
                offset=Op.ADD(0x20, Op.DUP2),
                value=Op.MLOAD(offset=0x1220),
            )
            + Op.MSTORE(
                offset=Op.ADD(0x40, Op.DUP2), value=Op.MLOAD(offset=0x40)
            )
            + Op.MSTORE(offset=Op.ADD(0x60, Op.DUP2), value=0x1)
            + Op.DUP1
            + Op.SWAP1
            + Op.POP
            + Op.MSTORE(
                offset=Op.ADD(Op.DUP3, 0x40), value=Op.SLOAD(key=Op.SHA3)
            )
            + Op.ADD(Op.DUP2, 0x20)
            + Op.SWAP1
            + Op.POP
            + Op.MSTORE(offset=Op.SUB(Op.DUP3, 0x40), value=0x20)
            + Op.RETURN(
                offset=Op.SUB(Op.DUP3, 0x40),
                size=Op.ADD(
                    0x40,
                    Op.MUL(Op.MLOAD(offset=Op.SUB(Op.DUP3, 0x20)), 0x20),
                ),
            )
            + Op.POP
            + Op.JUMPDEST
            + Op.POP
        ),
        storage={
            0xD0000000000000000000000000000000000505347: 0x0,
            0x160000000000000000000000000000000000000000: 0x1,
        },
        nonce=0,
        address=Address("0xf47bacb0d8f13fa44d31623c3d5ae72907d241c1"),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=contract,
        data=bytes.fromhex(
            "d91e22f40000000000000000000000000000000000000000000000000000000000505347"  # noqa: E501
            "000000000000000000000000000000000000000000000000000000002450534700000000"  # noqa: E501
            "000000000000000000000000000000000000000000000000000000010000000000000000"  # noqa: E501
            "000000000000000000000000000000000000000005f5e100000000000000000000000000"  # noqa: E501
            "000000000000000000000000002386f26fc1000000000000000000000000000000000000"  # noqa: E501
            "00000000000000000000000000000001"
        ),
        gas_limit=500000,
        gas_price=52637211012,
        nonce=24,
    )

    post = {
        contract: Account(
            storage={0x160000000000000000000000000000000000000000: 1},
        ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
