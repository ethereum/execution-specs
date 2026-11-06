"""
Test JUMP, JUMPI and LLL control flow constructs.

Ported from:
state_tests/VMTests/vmIOandFlowOperations/jumpFiller.yml
state_tests/VMTests/vmIOandFlowOperations/jumpiFiller.yml
state_tests/VMTests/vmIOandFlowOperations/loopsConditionalsFiller.yml
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytecode,
    Fork,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

SENTINEL = 0x0BAD


CASES = [
    # jump
    pytest.param(
        Op.SSTORE(key=0x0, value=0x600D)
        + Op.JUMP(pc=Op.MUL(0x20, 0x10))
        + Op.JUMPDEST
        + Op.STOP,
        {0: SENTINEL},
        id="jump-jump-hyperspace_1",
    ),
    pytest.param(
        Op.SSTORE(key=0x0, value=0x600D)
        + Op.JUMPI(pc=Op.MUL(0x20, 0x10), condition=0x1)
        + Op.JUMPDEST
        + Op.STOP,
        {0: SENTINEL},
        id="jump-jump-hyperspace_2",
    ),
    pytest.param(
        Op.JUMP(pc=0x4)
        + Op.STOP
        + Op.JUMPDEST
        + Op.SSTORE(key=0x0, value=0x600D)
        + Op.STOP,
        {0: 24589},
        id="jump-jump-stop-dest",
    ),
    pytest.param(
        Op.SSTORE(key=0x0, value=0x600D) + Op.JUMP(pc=0xFFFFFFF) + Op.STOP,
        {0: SENTINEL},
        id="jump-jump-hyperspace_3",
    ),
    pytest.param(
        Op.PUSH1[0x23]
        + Op.JUMP(pc=0x8)
        + Op.PUSH1[0x1]
        + Op.JUMPDEST
        + Op.PUSH1[0x2]
        + Op.SSTORE,
        {0: SENTINEL},
        id="jump-jump-not-jumpdest_1",
    ),
    pytest.param(
        Op.PUSH2[0x600D]
        + Op.JUMP(pc=0x8)
        + Op.PUSH1[0xFF]
        + Op.JUMPDEST
        + Op.PUSH1[0x0]
        + Op.SSTORE,
        {0: 24589},
        id="jump-jump-dest_1",
    ),
    pytest.param(
        Op.JUMP(pc=0xB)
        + Op.JUMPDEST
        + Op.SSTORE(key=0x0, value=0x600D)
        + Op.STOP
        + Op.JUMPDEST
        + Op.JUMP(pc=0x3),
        {0: 24589},
        id="jump-jump-dest_2",
    ),
    pytest.param(
        Op.JUMP(pc=Op.ADD(0x5, 0x2))
        + Op.STOP
        + Op.JUMPDEST
        + Op.SSTORE(key=0x0, value=0x600D),
        {0: 24589},
        id="jump-jump-dynamic",
    ),
    pytest.param(
        Op.JUMP(pc=0x5)
        + Op.STOP
        + Op.PUSH1[0x5B]
        + Op.SSTORE(key=0x0, value=0x600D),
        {0: SENTINEL},
        id="jump-jump-2-push_1",
    ),
    pytest.param(
        Op.JUMP(pc=0x5)
        + Op.STOP
        + Op.PUSH1[0x1]
        + Op.SSTORE(key=0x0, value=0x600D),
        {0: SENTINEL},
        id="jump-jump-2-push_2",
    ),
    pytest.param(
        Op.SSTORE(key=0x0, value=0x600D)
        + Op.JUMP(pc=0xB)
        + Op.GAS
        + Op.JUMPDEST
        + Op.SSTORE(key=0x1, value=Op.GAS),
        {0: SENTINEL},
        id="jump-jump-not-jumpdest_2",
    ),
    pytest.param(
        Op.SSTORE(key=0x0, value=0x600D)
        + Op.JUMP(pc=0x9)
        + Op.GAS
        + Op.JUMPDEST
        + Op.SSTORE(key=0x1, value=Op.GAS),
        {0: SENTINEL},
        id="jump-jump-not-jumpdest_3",
    ),
    pytest.param(
        Op.JUMP(pc=0x1000000000000000B)
        + Op.JUMPDEST * 2
        + Op.SSTORE(key=0x1, value=0x1),
        {0: SENTINEL},
        id="jump-jump-hyperspace_4",
    ),
    pytest.param(
        Op.JUMP(pc=0x100000007)
        + Op.JUMPDEST * 2
        + Op.SSTORE(key=0x1, value=0x1),
        {0: SENTINEL},
        id="jump-jump-hyperspace_5",
    ),
    pytest.param(
        Op.POP(Op.MLOAD(offset=0x0))
        + Op.POP(Op.SUB(0x0, 0x1))
        + Op.JUMP(pc=Op.MLOAD(offset=0x0))
        + Op.SSTORE(key=0x0, value=0x600D)
        + Op.STOP,
        {0: SENTINEL},
        id="jump-jump-hyperspace_6",
    ),
    pytest.param(
        Op.JUMP(pc=0xE) + Op.JUMPDEST * 16 + Op.SSTORE(key=0x0, value=0x600D),
        {0: 24589},
        id="jump-jump-to-list",
    ),
    # jumpi
    pytest.param(
        Op.SSTORE(key=0x0, value=0x600D)
        + Op.JUMPI(pc=Op.MUL(0x20, 0x10), condition=0x0)
        + Op.JUMPDEST
        + Op.STOP,
        {0: 24589},
        id="jumpi-not-jump-hyperspace_1",
    ),
    pytest.param(
        Op.JUMPI(pc=0x6, condition=0x1)
        + Op.STOP
        + Op.JUMPDEST
        + Op.SSTORE(key=0x0, value=0x600D)
        + Op.STOP,
        {0: 24589},
        id="jumpi-jump-stop-dest",
    ),
    pytest.param(
        Op.JUMPI(pc=0x6, condition=0x0)
        + Op.STOP
        + Op.JUMPDEST
        + Op.SSTORE(key=0x0, value=0x600D)
        + Op.STOP,
        {0: SENTINEL},
        id="jumpi-not-jump-stop-dest",
    ),
    pytest.param(
        Op.SSTORE(key=0x0, value=0x600D)
        + Op.JUMPI(pc=0xFFFFFFF, condition=0xFF)
        + Op.STOP,
        {0: SENTINEL},
        id="jumpi-jump-hyperspace_3",
    ),
    pytest.param(
        Op.SSTORE(key=0x0, value=0x600D)
        + Op.JUMPI(pc=0xFFFFFFF, condition=0x0)
        + Op.STOP,
        {0: 24589},
        id="jumpi-not-jump-hyperspace_3",
    ),
    pytest.param(
        Op.PUSH1[0x23]
        + Op.JUMPI(pc=0x8, condition=0x1)
        + Op.PUSH1[0x1]
        + Op.JUMPDEST
        + Op.PUSH1[0x2]
        + Op.SSTORE,
        {0: SENTINEL},
        id="jumpi-jump-not-jumpdest_1",
    ),
    pytest.param(
        Op.PUSH2[0x600D]
        + Op.JUMPI(pc=0xA, condition=0x1)
        + Op.PUSH1[0xFF]
        + Op.JUMPDEST
        + Op.PUSH1[0x0]
        + Op.SSTORE,
        {0: 24589},
        id="jumpi-jump-dest_1",
    ),
    pytest.param(
        Op.JUMP(pc=0xB)
        + Op.JUMPDEST
        + Op.SSTORE(key=0x0, value=0x600D)
        + Op.STOP
        + Op.JUMPDEST
        + Op.JUMPI(pc=0x3, condition=0x1),
        {0: 24589},
        id="jumpi-jump-dest_2",
    ),
    pytest.param(
        Op.JUMPI(pc=Op.ADD(0x5, 0x4), condition=0x1)
        + Op.STOP
        + Op.JUMPDEST
        + Op.SSTORE(key=0x0, value=0x600D),
        {0: 24589},
        id="jumpi-jump-dynamic",
    ),
    pytest.param(
        Op.JUMPI(pc=Op.ADD(0x5, 0x4), condition=0x0)
        + Op.STOP
        + Op.JUMPDEST
        + Op.SSTORE(key=0x0, value=0x600D),
        {0: SENTINEL},
        id="jumpi-not-jump-dynamic",
    ),
    pytest.param(
        Op.JUMPI(pc=0x7, condition=0x1)
        + Op.STOP
        + Op.PUSH1[0x5B]
        + Op.SSTORE(key=0x0, value=0x600D),
        {0: SENTINEL},
        id="jumpi-jump-2-push_1",
    ),
    pytest.param(
        Op.JUMPI(pc=0x7, condition=0x1)
        + Op.STOP
        + Op.PUSH1[0x1]
        + Op.SSTORE(key=0x0, value=0x600D),
        {0: SENTINEL},
        id="jumpi-jump-2-push_2",
    ),
    pytest.param(
        Op.SSTORE(key=0x0, value=0x600D)
        + Op.JUMPI(pc=0xD, condition=0x1)
        + Op.GAS
        + Op.JUMPDEST
        + Op.SSTORE(key=0x1, value=Op.GAS),
        {0: SENTINEL},
        id="jumpi-jump-not-jumpdest_2",
    ),
    pytest.param(
        Op.SSTORE(key=0x0, value=0x600D)
        + Op.JUMPI(pc=0xB, condition=0x1)
        + Op.GAS
        + Op.JUMPDEST
        + Op.SSTORE(key=0x1, value=Op.GAS),
        {0: SENTINEL},
        id="jumpi-jump-not-jumpdest_3",
    ),
    pytest.param(
        Op.JUMPI(pc=0x1000000000000000D, condition=0x11)
        + Op.JUMPDEST * 2
        + Op.SSTORE(key=0x0, value=0x600D),
        {0: SENTINEL},
        id="jumpi-jump-hyperspace_4",
    ),
    pytest.param(
        Op.JUMPI(pc=0x1000000000000000D, condition=0x0)
        + Op.JUMPDEST * 2
        + Op.SSTORE(key=0x0, value=0x600D),
        {0: 24589},
        id="jumpi-not-jump-hyperspace_4",
    ),
    pytest.param(
        Op.JUMPI(pc=0x100000009, condition=0x11)
        + Op.JUMPDEST * 2
        + Op.SSTORE(key=0x0, value=0x600D),
        {0: SENTINEL},
        id="jumpi-jump-hyperspace_5",
    ),
    pytest.param(
        Op.JUMPI(pc=0x100000009, condition=0x0)
        + Op.JUMPDEST * 2
        + Op.SSTORE(key=0x0, value=0x600D),
        {0: 24589},
        id="jumpi-not-jump-hyperspace_5",
    ),
    pytest.param(
        Op.POP(Op.MLOAD(offset=0x0))
        + Op.POP(Op.SUB(0x0, 0x1))
        + Op.JUMPI(pc=Op.MLOAD(offset=0x0), condition=0x1)
        + Op.SSTORE(key=0x0, value=0x600D)
        + Op.STOP,
        {0: SENTINEL},
        id="jumpi-jump-hyperspace_6",
    ),
    pytest.param(
        Op.POP(Op.MLOAD(offset=0x0))
        + Op.POP(Op.SUB(0x0, 0x1))
        + Op.JUMPI(pc=Op.MLOAD(offset=0x0), condition=0x0)
        + Op.SSTORE(key=0x0, value=0x600D)
        + Op.STOP,
        {0: 24589},
        id="jumpi-not-jump-hyperspace_6",
    ),
    pytest.param(
        Op.JUMPI(pc=0xE, condition=0x1)
        + Op.JUMPDEST * 16
        + Op.SSTORE(key=0x0, value=0x600D),
        {0: 24589},
        id="jumpi-jump-to-list",
    ),
    pytest.param(
        Op.SSTORE(key=0x0, value=0x600D)
        + Op.MSTORE(offset=0x0, value=0x10)
        + Op.JUMPDEST
        + Op.SUB(Op.MLOAD(offset=0x0), 0x1)
        + Op.MSTORE(offset=0x0, value=Op.DUP1)
        + Op.PUSH1[0xB]
        + Op.JUMPI,
        {0: 24589},
        id="jumpi-loop",
    ),
    # loopsConditionals
    pytest.param(
        Op.JUMPI(pc=0xF, condition=Op.ISZERO(Op.GT(0x1, 0x0)))
        + Op.SSTORE(key=0x0, value=0x600D)
        + Op.JUMPDEST
        + Op.STOP,
        {0: 24589},
        id="loopsConditionals-whenTrue",
    ),
    pytest.param(
        Op.JUMPI(pc=0xF, condition=Op.ISZERO(Op.LT(0x1, 0x0)))
        + Op.SSTORE(key=0x0, value=0x600D)
        + Op.JUMPDEST
        + Op.STOP,
        {0: SENTINEL},
        id="loopsConditionals-whenFalse",
    ),
    pytest.param(
        Op.JUMPI(pc=0xE, condition=Op.LT(0x1, 0x0))
        + Op.SSTORE(key=0x0, value=0x600D)
        + Op.JUMPDEST
        + Op.STOP,
        {0: 24589},
        id="loopsConditionals-unlessTrue",
    ),
    pytest.param(
        Op.JUMPI(pc=0xE, condition=Op.GT(0x1, 0x0))
        + Op.SSTORE(key=0x0, value=0x600D)
        + Op.JUMPDEST
        + Op.STOP,
        {0: SENTINEL},
        id="loopsConditionals-unlessFalse",
    ),
    pytest.param(
        Op.JUMPI(pc=0xE, condition=Op.GT(0x1, 0x0))
        + Op.PUSH2[0x60A7]
        + Op.JUMP(pc=0x12)
        + Op.JUMPDEST
        + Op.PUSH2[0x600D]
        + Op.JUMPDEST
        + Op.PUSH1[0x0]
        + Op.SSTORE
        + Op.STOP,
        {0: 24589},
        id="loopsConditionals-ifTrue",
    ),
    pytest.param(
        Op.JUMPI(pc=0xE, condition=Op.LT(0x1, 0x0))
        + Op.PUSH2[0x60A7]
        + Op.JUMP(pc=0x12)
        + Op.JUMPDEST
        + Op.PUSH2[0x600D]
        + Op.JUMPDEST
        + Op.PUSH1[0x0]
        + Op.SSTORE
        + Op.STOP,
        {0: 24743},
        id="loopsConditionals-ifFalse",
    ),
    pytest.param(
        Op.SSTORE(key=0x0, value=0x10)
        + Op.SSTORE(key=0x1, value=0x1)
        + Op.JUMPDEST
        + Op.JUMPI(pc=0x27, condition=Op.ISZERO(Op.SLOAD(key=0x0)))
        + Op.SSTORE(key=0x0, value=Op.SUB(Op.SLOAD(key=0x0), 0x1))
        + Op.SSTORE(key=0x1, value=Op.MUL(Op.SLOAD(key=0x1), 0x2))
        + Op.JUMP(pc=0xA)
        + Op.JUMPDEST
        + Op.STOP,
        {0: 0, 1: 0x10000},
        id="loopsConditionals-while",
    ),
    pytest.param(
        Op.SSTORE(key=0x0, value=0x10)
        + Op.SSTORE(key=0x1, value=0x1)
        + Op.JUMPDEST
        + Op.JUMPI(pc=0x29, condition=Op.EQ(Op.SLOAD(key=0x0), 0x0))
        + Op.SSTORE(key=0x0, value=Op.SUB(Op.SLOAD(key=0x0), 0x1))
        + Op.SSTORE(key=0x1, value=Op.MUL(Op.SLOAD(key=0x1), 0x2))
        + Op.JUMP(pc=0xA)
        + Op.JUMPDEST
        + Op.STOP,
        {0: 0, 1: 0x10000},
        id="loopsConditionals-until",
    ),
    pytest.param(
        Op.SSTORE(key=0x0, value=0x10)
        + Op.SSTORE(key=0x1, value=0x1)
        + Op.JUMPDEST
        + Op.JUMPI(pc=0x2A, condition=Op.ISZERO(Op.GT(Op.SLOAD(key=0x0), 0x0)))
        + Op.SSTORE(key=0x1, value=Op.MUL(Op.SLOAD(key=0x1), 0x2))
        + Op.SSTORE(key=0x0, value=Op.SUB(Op.SLOAD(key=0x0), 0x1))
        + Op.JUMP(pc=0xA)
        + Op.JUMPDEST
        + Op.STOP,
        {0: 0, 1: 0x10000},
        id="loopsConditionals-for",
    ),
    pytest.param(
        Op.MSTORE(offset=0x80, value=0xA)
        + Op.JUMPDEST
        + Op.JUMPI(
            pc=0x26, condition=Op.ISZERO(Op.GT(Op.MLOAD(offset=0x80), 0x0))
        )
        + Op.MSTORE(
            offset=0xA0,
            value=Op.ADD(Op.MLOAD(offset=0x80), Op.MLOAD(offset=0xA0)),
        )
        + Op.MSTORE(offset=0x80, value=Op.SUB(Op.MLOAD(offset=0x80), 0x1))
        + Op.JUMP(pc=0x5)
        + Op.JUMPDEST
        + Op.SSTORE(key=0x0, value=Op.MLOAD(offset=0xA0))
        + Op.STOP,
        {0: 55},
        id="loopsConditionals-for_loop1",
    ),
    pytest.param(
        Op.MSTORE(offset=0x80, value=0x0)
        + Op.JUMPDEST
        + Op.JUMPI(
            pc=0x27,
            condition=Op.ISZERO(Op.ISZERO(Op.GT(Op.MLOAD(offset=0x80), 0xA))),
        )
        + Op.MSTORE(
            offset=0xA0,
            value=Op.ADD(Op.MLOAD(offset=0x80), Op.MLOAD(offset=0xA0)),
        )
        + Op.MSTORE(offset=0x80, value=Op.ADD(Op.MLOAD(offset=0x80), 0x1))
        + Op.JUMP(pc=0x5)
        + Op.JUMPDEST
        + Op.SSTORE(key=0x0, value=Op.MLOAD(offset=0xA0))
        + Op.STOP,
        {0: 55},
        id="loopsConditionals-for_loop2",
    ),
]


@pytest.mark.ported_from(
    [
        "state_tests/VMTests/vmIOandFlowOperations/jumpFiller.yml",
        "state_tests/VMTests/vmIOandFlowOperations/jumpiFiller.yml",
        "state_tests/VMTests/vmIOandFlowOperations/loopsConditionalsFiller.yml",
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize("code, storage", CASES)
def test_jump(
    state_test: StateTestFiller,
    pre: Alloc,
    code: Bytecode,
    storage: dict,
) -> None:
    """Run a control flow case and check the storage it leaves."""
    contract = pre.deploy_contract(code=code, storage={0: SENTINEL})
    tx = Transaction(sender=pre.fund_eoa(), to=contract)
    post = {contract: Account(storage=storage)}
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    [
        "state_tests/VMTests/vmIOandFlowOperations/jumpFiller.yml",
        "state_tests/VMTests/vmIOandFlowOperations/jumpiFiller.yml",
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "loop_jump",
    [
        pytest.param(Op.JUMP(pc=0x6), id="jump-endless-loop"),
        pytest.param(Op.JUMPI(pc=0x6, condition=0x6), id="jumpi-endless-loop"),
    ],
)
def test_endless_loop(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    loop_jump: Bytecode,
) -> None:
    """Revert a storage write when a jump loops until out of gas."""
    code = Op.SSTORE(key=0x0, value=0x600D) + Op.JUMPDEST + loop_jump
    contract = pre.deploy_contract(code=code, storage={0: SENTINEL})
    tx = Transaction(
        sender=pre.fund_eoa(),
        to=contract,
        gas_limit=fork.transaction_intrinsic_cost_calculator()() + 100_000,
    )
    post = {contract: Account(storage={0: SENTINEL})}
    state_test(pre=pre, post=post, tx=tx)
