"""
Test JUMP, JUMPI and LLL control flow constructs.

The original tests were written by Ori Pomerantz.

Ported from:
state_tests/VMTests/vmIOandFlowOperations/jumpFiller.yml
state_tests/VMTests/vmIOandFlowOperations/jumpiFiller.yml
state_tests/VMTests/vmIOandFlowOperations/loopsConditionalsFiller.yml
state_tests/VMTests/vmIOandFlowOperations/jumpToPushFiller.yml

@manually-enhanced: Do not overwrite. Built from readable parameters.

`test_jump_destination` crosses every jump kind with every destination
class and with a target read from PUSH data (static) or calldata
(dynamic), laying out the destination markers and computing their offsets
with `len()`. `test_loops_conditionals` assembles each LLL construct with
computed labels and derives the stored result from what it computes.
`test_endless_loop` checks that a loop running out of gas reverts.
`test_jump_to_push` jumps, with JUMP or a taken JUMPI, just past, or
into, the data of a PUSHn whose data bytes are all 0x5B (JUMPDEST), using
the same target sources.
"""

from enum import StrEnum

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytecode,
    Bytes,
    Fork,
    Hash,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

pytestmark = [
    pytest.mark.ported_from(
        [
            "state_tests/VMTests/vmIOandFlowOperations/jumpFiller.yml",
            "state_tests/VMTests/vmIOandFlowOperations/jumpiFiller.yml",
            "state_tests/VMTests/vmIOandFlowOperations/loopsConditionalsFiller.yml",
            "state_tests/VMTests/vmIOandFlowOperations/jumpToPushFiller.yml",
        ],
    ),
    pytest.mark.valid_from("Frontier"),
]

RESULT_SLOT = 0
JUMP_REACHED_SLOT = 1
DONE_SLOT = 2

SENTINEL = 0x0BAD
JUMPED = 0x600D
FELL_THROUGH = 0x60A7

JUMPDEST_LIST_LENGTH = 16
PAST_CODE_END = 0x200
FAR_PAST_CODE_END = 0xFFFFFFF
MAX_UINT = 2**256 - 1


class JumpKind(StrEnum):
    """Jump instruction under test and, for JUMPI, its condition."""

    JUMP = "jump"
    JUMPI_TAKEN = "jumpi_taken"
    JUMPI_TAKEN_HIGH_CONDITION = "jumpi_taken_high_condition"
    JUMPI_NOT_TAKEN = "jumpi_not_taken"

    @property
    def condition(self) -> int:
        """Return the JUMPI condition (ignored by JUMP)."""
        if self == JumpKind.JUMPI_NOT_TAKEN:
            return 0
        if self == JumpKind.JUMPI_TAKEN_HIGH_CONDITION:
            # Non-zero only above the low 64 bits.
            return 2**255
        return 1

    @property
    def taken(self) -> bool:
        """Return whether the jump transfers control."""
        return self != JumpKind.JUMPI_NOT_TAKEN


class Destination(StrEnum):
    """Where the jump under test points."""

    JUMPDEST = "jumpdest"
    JUMPDEST_BACKWARDS = "jumpdest_backwards"
    JUMPDEST_IN_LIST = "jumpdest_in_list"
    JUMPDEST_PLUS_2_32 = "jumpdest_plus_2_32"
    JUMPDEST_PLUS_2_64 = "jumpdest_plus_2_64"
    NOT_JUMPDEST = "not_jumpdest"
    CODE_START = "code_start"
    JUMPDEST_IN_PUSH_DATA = "jumpdest_in_push_data"
    PUSH_DATA_NOT_JUMPDEST = "push_data_not_jumpdest"
    CODE_END = "code_end"
    PAST_CODE_END = "past_code_end"
    FAR_PAST_CODE_END = "far_past_code_end"
    MAX_UINT = "max_uint"

    @property
    def valid(self) -> bool:
        """Return whether jumping here continues execution."""
        return self in (
            Destination.JUMPDEST,
            Destination.JUMPDEST_BACKWARDS,
            Destination.JUMPDEST_IN_LIST,
        )


class TargetSource(StrEnum):
    """How the jump target and condition reach the stack."""

    PUSH = "push"
    CALLDATA = "calldata"


def jump_instruction(
    jump_kind: JumpKind, target_source: TargetSource, target: int
) -> Bytecode:
    """Return the jump under test, reading its operands from the source."""
    pc: int | Bytecode = target
    condition: int | Bytecode = jump_kind.condition
    if target_source == TargetSource.CALLDATA:
        pc = Op.CALLDATALOAD(0)
        condition = Op.CALLDATALOAD(32)
    if jump_kind == JumpKind.JUMP:
        return Op.JUMP(pc=pc)
    return Op.JUMPI(pc=pc, condition=condition)


def lay_out_destinations(
    jump: Bytecode,
) -> tuple[Bytecode, dict[Destination, int], int]:
    """
    Place `jump` among the destination markers.

    Return the code, the offset of each in-code destination, and the code
    length. Every valid destination stores the `JUMPED` value pushed
    before the jump, proving the stack survives it, while the fall-through
    path stores `FELL_THROUGH`.
    """
    store_pushed_value = Op.PUSH1[RESULT_SLOT] + Op.SSTORE + Op.STOP
    backwards = Op.JUMPDEST + store_pushed_value
    offsets: dict[Destination, int] = {Destination.CODE_START: 0}

    # Skip over the backwards destination to the entry point.
    code = Op.JUMP(pc=Op.PUSH1(data_placeholder="entry"))
    offsets[Destination.JUMPDEST_BACKWARDS] = len(code)
    code += backwards
    code.substitute(entry=len(code))

    code += (
        Op.JUMPDEST
        + Op.SSTORE(JUMP_REACHED_SLOT, 1)
        + Op.PUSH2[JUMPED]
        + jump
        + Op.POP
        + Op.SSTORE(RESULT_SLOT, FELL_THROUGH)
        + Op.STOP
    )

    offsets[Destination.JUMPDEST] = len(code)
    code += Op.JUMPDEST + store_pushed_value

    offsets[Destination.NOT_JUMPDEST] = len(code)
    code += Op.GAS + store_pushed_value

    # Land on the PUSH1 immediate, not on the PUSH1 opcode.
    offsets[Destination.JUMPDEST_IN_PUSH_DATA] = len(code) + 1
    code += Op.PUSH1[0x5B] + store_pushed_value

    offsets[Destination.PUSH_DATA_NOT_JUMPDEST] = len(code) + 1
    code += Op.PUSH1[0x01] + store_pushed_value

    offsets[Destination.JUMPDEST_IN_LIST] = (
        len(code) + JUMPDEST_LIST_LENGTH // 2
    )
    code += Op.JUMPDEST * JUMPDEST_LIST_LENGTH + store_pushed_value

    return code, offsets, len(code)


def resolve_target(
    destination: Destination, offsets: dict[Destination, int], end: int
) -> int:
    """Return the jump target for `destination` in a laid-out contract."""
    if destination in offsets:
        return offsets[destination]
    if destination == Destination.JUMPDEST_PLUS_2_32:
        return offsets[Destination.JUMPDEST] + 2**32
    if destination == Destination.JUMPDEST_PLUS_2_64:
        return offsets[Destination.JUMPDEST] + 2**64
    if destination == Destination.CODE_END:
        return end
    if destination == Destination.PAST_CODE_END:
        assert end < PAST_CODE_END
        return PAST_CODE_END
    if destination == Destination.FAR_PAST_CODE_END:
        return FAR_PAST_CODE_END
    if destination == Destination.MAX_UINT:
        return MAX_UINT
    raise ValueError(f"Unknown destination: {destination}")


def build_jump_code(
    jump_kind: JumpKind,
    target_source: TargetSource,
    destination: Destination,
) -> tuple[Bytecode, int]:
    """
    Return the contract and the jump target it needs.

    A PUSH target's width moves the markers after it, so re-lay the code
    until the target settles.
    """
    target = 0
    while True:
        jump = jump_instruction(jump_kind, target_source, target)
        code, offsets, end = lay_out_destinations(jump)
        resolved = resolve_target(destination, offsets, end)
        if resolved == target:
            return code, target
        target = resolved


@pytest.mark.parametrize("target_source", list(TargetSource), ids=str)
@pytest.mark.parametrize("destination", list(Destination), ids=str)
@pytest.mark.parametrize("jump_kind", list(JumpKind), ids=str)
def test_jump_destination(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    jump_kind: JumpKind,
    destination: Destination,
    target_source: TargetSource,
) -> None:
    """
    Verify where JUMP and JUMPI may land.

    A taken jump to a JUMPDEST continues, any other taken jump halts
    exceptionally and reverts the frame, and a JUMPI that is not taken
    falls through whatever its target.
    """
    code, target = build_jump_code(jump_kind, target_source, destination)
    contract = pre.deploy_contract(code=code, storage={RESULT_SLOT: SENTINEL})
    data = Bytes()
    if target_source == TargetSource.CALLDATA:
        data = Bytes(Hash(target) + Hash(jump_kind.condition))
    tx = Transaction(
        sender=pre.fund_eoa(),
        to=contract,
        data=data,
        protected=fork.supports_protected_txs(),
    )

    storage: dict[int, int] = {RESULT_SLOT: SENTINEL}
    if not jump_kind.taken:
        storage = {RESULT_SLOT: FELL_THROUGH, JUMP_REACHED_SLOT: 1}
    elif destination.valid:
        storage = {RESULT_SLOT: JUMPED, JUMP_REACHED_SLOT: 1}

    state_test(pre=pre, post={contract: Account(storage=storage)}, tx=tx)


class ControlFlow(StrEnum):
    """LLL control flow construct."""

    WHEN = "when"
    UNLESS = "unless"
    IF_ELSE = "if_else"
    WHILE = "while"
    UNTIL = "until"
    FOR = "for"
    FOR_LOOP_DOWN = "for_loop_down"
    FOR_LOOP_UP = "for_loop_up"
    JUMPI_COUNTDOWN = "jumpi_countdown"

    @property
    def conditional(self) -> bool:
        """Return whether the construct takes a condition parameter."""
        return self in (
            ControlFlow.WHEN,
            ControlFlow.UNLESS,
            ControlFlow.IF_ELSE,
        )


DOUBLINGS = 16
SUM_LIMIT = 10
COUNTDOWN = 16


def loop_code(
    setup: Bytecode, exit_condition: Bytecode, body: Bytecode
) -> Bytecode:
    """
    Return `setup`, then loop over `body` until `exit_condition` holds.

    The loop head tests the condition, the body jumps back to the head,
    and the exit lands on the JUMPDEST after the body.
    """
    head = len(setup)
    code = (
        setup
        + Op.JUMPDEST
        + Op.JUMPI(
            pc=Op.PUSH1(data_placeholder="end"), condition=exit_condition
        )
        + body
        + Op.JUMP(pc=head)
    )
    code.substitute(end=len(code))
    return code + Op.JUMPDEST


def control_flow_code(flow: ControlFlow, condition: bool) -> Bytecode:
    """Assemble `flow` as LLL compiles it, ending with a DONE_SLOT write."""
    # `(> 1 0)` is true and `(< 1 0)` is false.
    cond = Op.GT(1, 0) if condition else Op.LT(1, 0)
    store_good = Op.SSTORE(RESULT_SLOT, JUMPED)
    code: Bytecode
    if flow in (ControlFlow.WHEN, ControlFlow.UNLESS):
        # Skip the store when the (negated for WHEN) condition holds.
        skip = Op.ISZERO(cond) if flow == ControlFlow.WHEN else cond
        code = (
            Op.JUMPI(pc=Op.PUSH1(data_placeholder="end"), condition=skip)
            + store_good
        )
        code.substitute(end=len(code))
        code += Op.JUMPDEST
    elif flow == ControlFlow.IF_ELSE:
        # Each branch pushes its value; the join stores it.
        code = (
            Op.JUMPI(pc=Op.PUSH1(data_placeholder="then"), condition=cond)
            + Op.PUSH2[FELL_THROUGH]
            + Op.JUMP(pc=Op.PUSH1(data_placeholder="join"))
        )
        code.substitute(then=len(code))
        code += Op.JUMPDEST + Op.PUSH2[JUMPED]
        code.substitute(join=len(code))
        code += Op.JUMPDEST + Op.PUSH1[RESULT_SLOT] + Op.SSTORE
    elif flow in (ControlFlow.WHILE, ControlFlow.UNTIL, ControlFlow.FOR):
        # Double slot 1 once per countdown step of slot 0.
        counter = Op.SLOAD(0)
        exit_condition = {
            ControlFlow.WHILE: Op.ISZERO(counter),
            ControlFlow.UNTIL: Op.EQ(counter, 0),
            ControlFlow.FOR: Op.ISZERO(Op.GT(counter, 0)),
        }[flow]
        count_down = Op.SSTORE(0, Op.SUB(Op.SLOAD(0), 1))
        double = Op.SSTORE(1, Op.MUL(Op.SLOAD(1), 2))
        body = count_down + double
        if flow == ControlFlow.FOR:
            body = double + count_down
        code = loop_code(
            setup=Op.SSTORE(0, DOUBLINGS) + Op.SSTORE(1, 1),
            exit_condition=exit_condition,
            body=body,
        )
    elif flow == ControlFlow.FOR_LOOP_DOWN:
        # for (i = SUM_LIMIT; i > 0; i--) sum += i
        code = loop_code(
            setup=Op.MSTORE(0x80, SUM_LIMIT),
            exit_condition=Op.ISZERO(Op.GT(Op.MLOAD(0x80), 0)),
            body=Op.MSTORE(0xA0, Op.ADD(Op.MLOAD(0x80), Op.MLOAD(0xA0)))
            + Op.MSTORE(0x80, Op.SUB(Op.MLOAD(0x80), 1)),
        ) + Op.SSTORE(RESULT_SLOT, Op.MLOAD(0xA0))
    elif flow == ControlFlow.FOR_LOOP_UP:
        # for (i = 0; i <= SUM_LIMIT; i++) sum += i
        code = loop_code(
            setup=Op.MSTORE(0x80, 0),
            exit_condition=Op.ISZERO(
                Op.ISZERO(Op.GT(Op.MLOAD(0x80), SUM_LIMIT))
            ),
            body=Op.MSTORE(0xA0, Op.ADD(Op.MLOAD(0x80), Op.MLOAD(0xA0)))
            + Op.MSTORE(0x80, Op.ADD(Op.MLOAD(0x80), 1)),
        ) + Op.SSTORE(RESULT_SLOT, Op.MLOAD(0xA0))
    elif flow == ControlFlow.JUMPI_COUNTDOWN:
        # Decrement the memory counter, jumping back while it is non-zero.
        setup = Op.SSTORE(RESULT_SLOT, JUMPED) + Op.MSTORE(0, COUNTDOWN)
        code = (
            setup
            + Op.JUMPDEST
            + Op.MSTORE(0, Op.SUB(Op.MLOAD(0), 1))
            + Op.JUMPI(pc=len(setup), condition=Op.MLOAD(0))
        )
    else:
        raise ValueError(f"Unknown control flow: {flow}")
    return code + Op.SSTORE(DONE_SLOT, 1) + Op.STOP


def control_flow_storage(flow: ControlFlow, condition: bool) -> dict:
    """Return the storage `flow` leaves behind."""
    storage: dict[int, int]
    if flow == ControlFlow.WHEN:
        storage = {RESULT_SLOT: JUMPED if condition else SENTINEL}
    elif flow == ControlFlow.UNLESS:
        storage = {RESULT_SLOT: SENTINEL if condition else JUMPED}
    elif flow == ControlFlow.IF_ELSE:
        storage = {RESULT_SLOT: JUMPED if condition else FELL_THROUGH}
    elif flow in (ControlFlow.WHILE, ControlFlow.UNTIL, ControlFlow.FOR):
        storage = {0: 0, 1: 2**DOUBLINGS}
    elif flow in (ControlFlow.FOR_LOOP_DOWN, ControlFlow.FOR_LOOP_UP):
        storage = {RESULT_SLOT: sum(range(SUM_LIMIT + 1))}
    elif flow == ControlFlow.JUMPI_COUNTDOWN:
        storage = {RESULT_SLOT: JUMPED}
    else:
        raise ValueError(f"Unknown control flow: {flow}")
    return storage | {DONE_SLOT: 1}


@pytest.mark.parametrize(
    "flow, condition",
    [
        pytest.param(flow, condition, id=f"{flow}-{condition}".lower())
        for flow in ControlFlow
        if flow.conditional
        for condition in (True, False)
    ]
    + [
        pytest.param(flow, True, id=str(flow))
        for flow in ControlFlow
        if not flow.conditional
    ],
)
def test_loops_conditionals(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    flow: ControlFlow,
    condition: bool,
) -> None:
    """Verify the storage an LLL conditional or loop construct leaves."""
    contract = pre.deploy_contract(
        code=control_flow_code(flow, condition),
        storage={RESULT_SLOT: SENTINEL},
    )
    tx = Transaction(
        sender=pre.fund_eoa(),
        to=contract,
        protected=fork.supports_protected_txs(),
    )
    post = {contract: Account(storage=control_flow_storage(flow, condition))}
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.parametrize(
    "jump_kind", [JumpKind.JUMP, JumpKind.JUMPI_TAKEN], ids=["jump", "jumpi"]
)
def test_endless_loop(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    jump_kind: JumpKind,
) -> None:
    """Revert a storage write when a jump loops until out of gas."""
    store = Op.SSTORE(RESULT_SLOT, JUMPED)
    loop = len(store)
    loop_jump = Op.JUMP(pc=loop)
    if jump_kind == JumpKind.JUMPI_TAKEN:
        # The original loops on a condition other than 1.
        loop_jump = Op.JUMPI(pc=loop, condition=6)
    code = store + Op.JUMPDEST + loop_jump
    contract = pre.deploy_contract(code=code, storage={RESULT_SLOT: SENTINEL})
    tx = Transaction(
        sender=pre.fund_eoa(),
        to=contract,
        gas_limit=fork.transaction_intrinsic_cost_calculator()() + 100_000,
        protected=fork.supports_protected_txs(),
    )
    post = {contract: Account(storage={RESULT_SLOT: SENTINEL})}
    state_test(pre=pre, post=post, tx=tx)


class PushDataTarget(StrEnum):
    """Where `test_jump_to_push` jumps relative to the PUSH data."""

    AFTER_DATA = "after_data"
    FIRST_DATA_BYTE = "first_data_byte"
    LAST_DATA_BYTE = "last_data_byte"


@pytest.mark.parametrize("target_source", list(TargetSource), ids=str)
@pytest.mark.parametrize(
    "push_size, target",
    [
        pytest.param(size, target, id=f"push{size}-{target}")
        for size in range(1, 33)
        for target in PushDataTarget
        # PUSH1's first and last data bytes are the same byte.
        if not (size == 1 and target == PushDataTarget.LAST_DATA_BYTE)
    ],
)
@pytest.mark.parametrize(
    "jump_kind", [JumpKind.JUMP, JumpKind.JUMPI_TAKEN], ids=str
)
def test_jump_to_push(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    push_size: int,
    target: PushDataTarget,
    target_source: TargetSource,
    jump_kind: JumpKind,
) -> None:
    """Jump past PUSHn data (succeeds) or into it (halts)."""
    prefix = Op.SSTORE(RESULT_SLOT, 1)
    push_offset = len(prefix) + len(
        jump_instruction(jump_kind, target_source, 0)
    )
    match target:
        case PushDataTarget.AFTER_DATA:
            dest = push_offset + 1 + push_size
        case PushDataTarget.FIRST_DATA_BYTE:
            dest = push_offset + 1
        case PushDataTarget.LAST_DATA_BYTE:
            dest = push_offset + push_size
    code = (
        prefix
        + jump_instruction(jump_kind, target_source, dest)
        + getattr(Op, f"PUSH{push_size}")[b"\x5b" * push_size]
        + Op.JUMPDEST
    )
    assert (dest == len(code) - 1) == (target == PushDataTarget.AFTER_DATA)
    contract = pre.deploy_contract(code=code, storage={RESULT_SLOT: SENTINEL})
    data = Bytes()
    if target_source == TargetSource.CALLDATA:
        data = Bytes(Hash(dest))
        if jump_kind != JumpKind.JUMP:
            data = Bytes(data + Hash(jump_kind.condition))
    tx = Transaction(
        sender=pre.fund_eoa(),
        to=contract,
        data=data,
        protected=fork.supports_protected_txs(),
    )
    expected = 1 if target == PushDataTarget.AFTER_DATA else SENTINEL
    post = {contract: Account(storage={RESULT_SLOT: expected})}
    state_test(pre=pre, post=post, tx=tx)
