"""
Verify that each memory-touching operation runs out of gas at its budget:
a caller forwards a fixed amount to a contract holding one operation
whose memory reach exceeds it, and stores whether the sub-call survived.

Ported from:
state_tests/stMemoryTest/oogFiller.yml

@manually-enhanced: Do not overwrite. The ported fan of 22 pre-deployed
contracts collapses to one subject built per case, and every ported gas
constant becomes a budget derived from that subject's own bytecode: its
exact cost, or one gas short. The two RETURNDATACOPY arms instead
withhold one of EIP-211's two gas terms each, which is what the filler
starved with its pinned pair before EIP-2929 moved the CALL leg past it.
"""

from typing import Generator

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytecode,
    Fork,
    Hash,
    Op,
    StateTestFiller,
    Transaction,
)

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

# Memory offsets the operations reach for, past what the starved budgets
# can pay to expand to.
REACH = 0x1000
FAR_REACH = 0x10000
# Handed back by the return-data source for RETURNDATACOPY to copy.
RETURN_WORD = 0x102030405060708090A0B0C0D0E0F101112131415161718191A1B1C1D1E1F20
# Size of the argument and return windows the calls hand out.
WINDOW = 0x20
# Proves the caller ran to completion when the observable is zero.
CANARY = 0xC0DE

OPERATIONS_BY_OPCODE = {
    Op.CALL: [
        "call",
        "call_args",
        "call_return",
    ],
    Op.CALLCODE: [
        "callcode",
        "callcode_args",
        "callcode_return",
    ],
    Op.DELEGATECALL: [
        "delegatecall",
        "delegatecall_args",
        "delegatecall_return",
    ],
    Op.STATICCALL: [
        "staticcall",
        "staticcall_args",
        "staticcall_return",
    ],
}


# Memory-touching opcodes that `test_oog`'s success flag cannot observe,
# and so are covered by a test of their own.
SPECIAL_CASED = {Op.REVERT}


def operations_by_fork(fork: Fork) -> Generator[str, None, None]:
    """Return the list of operations per opcode that modifies the memory."""
    for opcode in fork.valid_opcodes():
        if "new_memory_size" in opcode.metadata:
            if opcode in SPECIAL_CASED:
                continue
            if opcode not in OPERATIONS_BY_OPCODE:
                operations = [opcode._name_.lower()]
            else:
                operations = OPERATIONS_BY_OPCODE[opcode]
            for operation in operations:
                yield operation


@pytest.fixture
def subject_code(operation: str, pre: Alloc, fork: Fork) -> Bytecode:
    """Build the body exercising `operation` past its memory reach."""
    if operation == "sha3":
        code = (
            Op.SHA3(
                offset=0x0,
                size=REACH,
                data_size=REACH,
                new_memory_size=REACH,
            )
            + Op.STOP
        )
        return code
    if operation == "calldatacopy":
        code = (
            Op.CALLDATACOPY(
                dest_offset=0x0,
                offset=0x0,
                size=REACH,
                data_size=REACH,
                new_memory_size=REACH,
            )
            + Op.STOP
        )
        return code
    if operation == "codecopy":
        code = (
            Op.CODECOPY(
                dest_offset=0x0,
                offset=0x0,
                size=REACH,
                data_size=REACH,
                new_memory_size=REACH,
            )
            + Op.STOP
        )
        return code
    if operation == "extcodecopy":
        code = (
            Op.EXTCODECOPY(
                address=Op.ADDRESS,
                dest_offset=0x0,
                offset=0x0,
                size=REACH,
                address_warm=True,
                data_size=REACH,
                new_memory_size=REACH,
            )
            + Op.STOP
        )
        return code
    if operation == "returndatacopy":
        callee_code = Op.MSTORE(
            offset=0x0, value=RETURN_WORD, new_memory_size=0x20
        ) + Op.RETURN(
            offset=0x0, size=0x20, new_memory_size=0x20, old_memory_size=0x20
        )
        return_data_source = pre.deploy_contract(code=callee_code)
        return (
            # Give RETURNDATACOPY something to copy. `inner_call_cost`
            # folds the callee's own gas into this frame's cost.
            Op.POP(
                Op.CALL(
                    gas=Op.GAS,
                    address=return_data_source,
                    value=0x0,
                    args_offset=0x0,
                    args_size=WINDOW,
                    ret_offset=0x0,
                    ret_size=WINDOW,
                    address_warm=False,
                    value_transfer=False,
                    new_memory_size=0x20,
                    inner_call_cost=callee_code.gas_cost(fork),
                )
            )
            + Op.RETURNDATACOPY(
                dest_offset=REACH,
                offset=0x0,
                size=0x10,
                data_size=0x10,
                old_memory_size=0x20,
                new_memory_size=REACH + 0x10,
            )
            + Op.STOP
        )
    if operation == "mload":
        code = Op.MLOAD(offset=REACH, new_memory_size=REACH + 0x20) + Op.STOP
        return code
    if operation == "mstore":
        code = (
            Op.MSTORE(offset=REACH, value=0xFF, new_memory_size=REACH + 0x20)
            + Op.STOP
        )
        return code
    if operation == "mstore8":
        code = (
            Op.MSTORE8(offset=REACH, value=0xFF, new_memory_size=REACH + 0x1)
            + Op.STOP
        )
        return code
    if operation == "mcopy":
        code = (
            Op.MCOPY(
                dest_offset=REACH,
                offset=0x0,
                size=WINDOW,
                data_size=WINDOW,
                new_memory_size=REACH + WINDOW,
            )
            + Op.STOP
        )
        return code
    if operation.startswith("log"):
        topics = [0x1, 0x2, 0x3, 0x4][: int(operation[3:])]
        log_opcode = getattr(Op, operation.upper())
        code = (
            log_opcode(
                FAR_REACH,
                0x20,
                *topics,
                data_size=0x20,
                new_memory_size=FAR_REACH + 0x20,
            )
            + Op.STOP
        )
        return code
    if operation == "create":
        # Metadata leaves the bytes unchanged, so the budget is derived
        # from the very code deployed.
        code = (
            Op.CREATE(
                value=0x0,
                offset=FAR_REACH,
                size=0x20,
                new_memory_size=FAR_REACH + 0x20,
                init_code_size=0x20,
            )
            + Op.STOP
        )
        return code
    if operation == "create2":
        code = (
            Op.CREATE2(
                value=0x0,
                offset=FAR_REACH,
                size=0x20,
                salt=0x5A17,
                new_memory_size=FAR_REACH + 0x20,
                init_code_size=0x20,
            )
            + Op.STOP
        )
        return code
    if operation == "return":
        code = Op.RETURN(
            offset=FAR_REACH, size=0x20, new_memory_size=FAR_REACH + 0x20
        )
        return code

    stop_contract = pre.deploy_contract(code=Op.STOP)
    call_op, _, window = operation.partition("_")
    assert call_op in ("call", "callcode", "delegatecall", "staticcall"), (
        f"unknown operation {operation}"
    )
    args_offset = 0x0 if window == "return" else FAR_REACH
    ret_offset = 0x0 if window == "args" else FAR_REACH
    if not window:
        ret_offset = FAR_REACH + WINDOW
    call_kwargs: dict = {
        "gas": Op.GAS,
        "address": stop_contract,
        "args_offset": args_offset,
        "args_size": WINDOW,
        "ret_offset": ret_offset,
        "ret_size": WINDOW,
        "address_warm": False,
        "new_memory_size": max(args_offset, ret_offset) + WINDOW,
    }
    if call_op in ("call", "callcode"):
        call_kwargs["value"] = 0x0
    code = getattr(Op, call_op.upper())(**call_kwargs) + Op.STOP
    return code


@pytest.mark.ported_from(
    ["state_tests/stMemoryTest/oogFiller.yml"],
)
@pytest.mark.valid_from("Berlin")
@pytest.mark.parametrize("succeeds", [True, False], ids=["enough", "oog"])
@pytest.mark.parametrize_by_fork("operation", operations_by_fork)
def test_oog(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    subject_code: Bytecode,
    succeeds: bool,
) -> None:
    """Forward a fixed budget to one memory-touching operation."""
    exact = subject_code.gas_cost(fork)
    forwarded_gas = exact if succeeds else exact - 1
    subject = pre.deploy_contract(code=subject_code)
    # Reads subject and budget from calldata, stores whether it survived.
    caller = pre.deploy_contract(
        code=Op.SSTORE(
            key=0x0, value=Op.CALL(gas=forwarded_gas, address=subject)
        )
        + Op.STOP,
    )
    tx = Transaction(sender=pre.fund_eoa(), to=caller, state_gas_reservoir=0)
    post = {caller: Account(storage={0: 1 if succeeds else 0})}
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["state_tests/stMemoryTest/oogFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize("succeeds", [True, False], ids=["enough", "oog"])
def test_oog_returndatacopy_expansion(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    succeeds: bool,
) -> None:
    """
    Starve RETURNDATACOPY's memory expansion specifically.

    EIP-211 prices the opcode as
    `_with_memory_expansion(_with_data_copy(...))`. `test_oog` withholds
    one gas, leaving the copy term unpaid; this withholds the expansion
    term whole, so the opcode is reached and dies on the other charge.
    """
    callee_code = Op.MSTORE(
        offset=0x0, value=RETURN_WORD, new_memory_size=0x20
    ) + Op.RETURN(
        offset=0x0, size=0x20, new_memory_size=0x20, old_memory_size=0x20
    )
    return_data_source = pre.deploy_contract(code=callee_code)
    # Give RETURNDATACOPY something to copy. `inner_call_cost` folds the
    # callee's own gas into this frame's cost.
    call_code = Op.POP(
        Op.CALL(
            gas=Op.GAS,
            address=return_data_source,
            value=0x0,
            args_offset=0x0,
            args_size=WINDOW,
            ret_offset=0x0,
            ret_size=WINDOW,
            address_warm=False,
            value_transfer=False,
            new_memory_size=0x20,
            inner_call_cost=callee_code.gas_cost(fork),
        )
    )
    # Pricing the same opcode with and without growth isolates the
    # expansion term, which is what this budget withholds.
    returndatacopy = Op.RETURNDATACOPY(
        dest_offset=REACH,
        offset=0x0,
        size=0x10,
        data_size=0x10,
        old_memory_size=0x20,
        new_memory_size=REACH + 0x10,
    )
    flat = Op.RETURNDATACOPY(
        dest_offset=REACH,
        offset=0x0,
        size=0x10,
        data_size=0x10,
        old_memory_size=0x20,
        new_memory_size=0x20,
    )
    expansion = returndatacopy.gas_cost(fork) - flat.gas_cost(fork)

    code = call_code + returndatacopy + Op.STOP
    starved = code.gas_cost(fork) - expansion
    # The budget still has to reach the opcode. The ported 0x7D0 no
    # longer does: EIP-2929 repriced the cold account access and the
    # CALL leg grew past it, so it starved the call instead.
    assert starved > call_code.gas_cost(fork), (
        "budget no longer reaches RETURNDATACOPY"
    )
    forwarded_gas = code.gas_cost(fork) if succeeds else starved
    subject = pre.deploy_contract(code=code)
    # Reads subject and budget from calldata, stores whether it survived.
    caller = pre.deploy_contract(
        code=Op.SSTORE(
            key=0x0,
            value=Op.CALL(
                gas=Op.CALLDATALOAD(offset=0x20),
                address=Op.CALLDATALOAD(offset=0x0),
            ),
        )
        + Op.STOP,
    )
    tx = Transaction(
        sender=pre.fund_eoa(),
        to=caller,
        data=Hash(subject, left_padding=True) + Hash(forwarded_gas),
        state_gas_reservoir=0,
    )
    post = {caller: Account(storage={0: 1 if succeeds else 0})}
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["state_tests/stMemoryTest/oogFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize("succeeds", [True, False], ids=["enough", "oog"])
def test_oog_revert(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    succeeds: bool,
) -> None:
    """
    Starve REVERT's memory expansion.

    A funded REVERT still makes the caller's CALL return 0, so the flag
    the other cases assert on cannot tell it apart from running out of
    gas. Its return data can: a REVERT that paid for its window hands
    back `WINDOW` bytes, one that ran out hands back none.
    """
    code = Op.REVERT(
        offset=FAR_REACH, size=WINDOW, new_memory_size=FAR_REACH + WINDOW
    )
    exact = code.gas_cost(fork)
    forwarded_gas = exact if succeeds else exact - 1
    subject = pre.deploy_contract(code=code)
    # Reads subject and budget from calldata, stores the size of the
    # revert data, then a canary so a caller that never ran is not
    # mistaken for a starved REVERT.
    caller = pre.deploy_contract(
        code=Op.POP(
            Op.CALL(
                gas=Op.CALLDATALOAD(offset=0x20),
                address=Op.CALLDATALOAD(offset=0x0),
            )
        )
        + Op.SSTORE(key=0x0, value=Op.RETURNDATASIZE)
        + Op.SSTORE(key=0x1, value=CANARY)
        + Op.STOP,
    )
    tx = Transaction(
        sender=pre.fund_eoa(),
        to=caller,
        data=Hash(subject, left_padding=True) + Hash(forwarded_gas),
        state_gas_reservoir=0,
    )
    post = {
        caller: Account(
            storage={0: WINDOW if succeeds else 0, 1: CANARY},
        )
    }
    state_test(pre=pre, post=post, tx=tx)
