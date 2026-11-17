"""
Check ORIGIN, CALLER, ADDRESS and CALLVALUE at the end of call paths that
go through STATICCALL.

Ported from:
state_tests/stStaticCall/static_CheckOpcodesFiller.json
state_tests/stStaticCall/static_CheckOpcodes2Filler.json
state_tests/stStaticCall/static_CheckOpcodes3Filler.json
state_tests/stStaticCall/static_CheckOpcodes4Filler.json
state_tests/stStaticCall/static_CheckOpcodes5Filler.json
state_tests/stStaticCall/static_callToCallOpCodeCheckFiller.json
state_tests/stStaticCall/static_callToCallCodeOpCodeCheckFiller.json
state_tests/stStaticCall/static_callToDelCallOpCodeCheckFiller.json
state_tests/stStaticCall/static_callToStaticOpCodeCheckFiller.json

@manually-enhanced: Do not overwrite. Merged; expected context in calldata.
"""

from dataclasses import dataclass

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Bytecode,
    Conditional,
    Hash,
    Op,
    StateTestFiller,
    Transaction,
)

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

CONTRACT_BALANCE = 1000
ENTRY_CONTEXT_SLOTS = {"caller": 3, "callvalue": 4, "origin": 5, "address": 6}

S = (Op.STATICCALL, 0)
C0 = (Op.CALL, 0)
C1 = (Op.CALL, 1)
CC0 = (Op.CALLCODE, 0)
CC1 = (Op.CALLCODE, 1)
D = (Op.DELEGATECALL, 0)


@dataclass(frozen=True)
class Frame:
    """Execution context of one level of a call path."""

    address: Address
    caller: Address
    value: int

    def enter(self, opcode: Op, callee: Address, value: int) -> "Frame":
        """Return the context in which `opcode` runs `callee`'s code."""
        if opcode in (Op.CALL, Op.STATICCALL):
            return Frame(address=callee, caller=self.address, value=value)
        if opcode == Op.CALLCODE:
            return Frame(
                address=self.address, caller=self.address, value=value
            )
        return self


@pytest.mark.ported_from(
    [
        "state_tests/stStaticCall/static_CheckOpcodesFiller.json",
        "state_tests/stStaticCall/static_CheckOpcodes2Filler.json",
        "state_tests/stStaticCall/static_CheckOpcodes3Filler.json",
        "state_tests/stStaticCall/static_CheckOpcodes4Filler.json",
        "state_tests/stStaticCall/static_CheckOpcodes5Filler.json",
        "state_tests/stStaticCall/static_callToCallOpCodeCheckFiller.json",
        "state_tests/stStaticCall/static_callToCallCodeOpCodeCheckFiller.json",
        "state_tests/stStaticCall/static_callToDelCallOpCodeCheckFiller.json",
        "state_tests/stStaticCall/static_callToStaticOpCodeCheckFiller.json",
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize("tx_value", [0, 100])
@pytest.mark.parametrize(
    "path",
    [
        pytest.param((S,), id="static"),
        pytest.param((S, S), id="static_static"),
        pytest.param((S, C0), id="static_call"),
        pytest.param((S, C1), id="static_call_value"),
        pytest.param((S, CC0), id="static_callcode"),
        pytest.param((S, CC1), id="static_callcode_value"),
        pytest.param((S, D), id="static_delegatecall"),
        pytest.param((S, S, C0), id="static_static_call"),
        pytest.param((S, S, C1), id="static_static_call_value"),
        pytest.param((S, S, CC0), id="static_static_callcode"),
        pytest.param((S, S, CC1), id="static_static_callcode_value"),
        pytest.param((S, S, D), id="static_static_delegatecall"),
        pytest.param((S, C0, S), id="static_call_static"),
        pytest.param((S, C1, S), id="static_call_value_static"),
        pytest.param((S, CC0, S), id="static_callcode_static"),
        pytest.param((S, CC1, S), id="static_callcode_value_static"),
        pytest.param((S, D, S), id="static_delegatecall_static"),
        pytest.param((C0, C0, S), id="call_call_static"),
        pytest.param((C0, C1, S), id="call_call_value_static"),
        pytest.param((C0, CC0, S), id="call_callcode_static"),
        pytest.param((C0, CC1, S), id="call_callcode_value_static"),
        pytest.param((C0, D, S), id="call_delegatecall_static"),
    ],
)
def test_static_check_opcodes(
    state_test: StateTestFiller,
    pre: Alloc,
    path: tuple[tuple[Op, int], ...],
    tx_value: int,
) -> None:
    """
    Call down `path` and check the innermost frame's context.

    The expected context is passed down as calldata, and the innermost
    frame halts exceptionally on a mismatch. Each non-static frame stores
    its call's success in the slot of its level, and each static frame
    halts exceptionally when its call fails. A CALL with value from a
    static frame halts that frame.
    """
    depth = len(path)
    sender = pre.fund_eoa()
    static = [
        any(opcode == Op.STATICCALL for opcode, _ in path[:level])
        for level in range(depth + 1)
    ]

    # Construct the innermost contract, which checks its context.
    context_matches = Op.AND(
        Op.AND(
            Op.EQ(Op.ORIGIN, Op.CALLDATALOAD(0x00)),
            Op.EQ(Op.CALLER, Op.CALLDATALOAD(0x20)),
        ),
        Op.AND(
            Op.EQ(Op.ADDRESS, Op.CALLDATALOAD(0x40)),
            Op.EQ(Op.CALLVALUE, Op.CALLDATALOAD(0x60)),
        ),
    )
    contracts = [
        pre.deploy_contract(
            code=Conditional(
                condition=Op.ISZERO(context_matches), if_true=Op.INVALID
            )
            + Op.STOP
        )
    ]

    # Construct the calling contracts, from the innermost one outward.
    for level in reversed(range(depth)):
        opcode, value = path[level]
        if opcode in (Op.CALL, Op.CALLCODE):
            call = opcode(
                address=contracts[0], value=value, args_size=Op.CALLDATASIZE
            )
        else:
            call = opcode(address=contracts[0], args_size=Op.CALLDATASIZE)
        if static[level]:
            handle: Bytecode = Conditional(
                condition=Op.ISZERO(call), if_true=Op.INVALID
            )
        else:
            handle = Op.SSTORE(level, call)
        code = Op.CALLDATACOPY(size=Op.CALLDATASIZE) + handle
        if level == 0:
            code += (
                Op.SSTORE(ENTRY_CONTEXT_SLOTS["caller"], Op.CALLER)
                + Op.SSTORE(ENTRY_CONTEXT_SLOTS["callvalue"], Op.CALLVALUE)
                + Op.SSTORE(ENTRY_CONTEXT_SLOTS["origin"], Op.ORIGIN)
                + Op.SSTORE(ENTRY_CONTEXT_SLOTS["address"], Op.ADDRESS)
            )
        contracts.insert(
            0,
            pre.deploy_contract(code=code + Op.STOP, balance=CONTRACT_BALANCE),
        )

    # Simulate each frame's context.
    frames = [Frame(address=contracts[0], caller=sender, value=tx_value)]
    for (opcode, value), callee in zip(path, contracts[1:], strict=True):
        frames.append(frames[-1].enter(opcode, callee, value))
    checker = frames[-1]

    # Find the frame whose call fails: the deepest non-static frame above
    # a CALL with value from a static frame.
    failing_hop = next(
        (
            level
            for level, (opcode, value) in enumerate(path)
            if static[level] and opcode == Op.CALL and value > 0
        ),
        None,
    )
    if failing_hop is None:
        storing = [level for level in range(depth) if not static[level]]
        failed_level = None
    else:
        failed_level = max(
            level for level in range(failing_hop) if not static[level]
        )
        storing = [
            level for level in range(failed_level + 1) if not static[level]
        ]

    # Construct the transaction, with the expected context as calldata.
    tx = Transaction(
        sender=sender,
        to=contracts[0],
        data=Hash(sender, left_padding=True)
        + Hash(checker.caller, left_padding=True)
        + Hash(checker.address, left_padding=True)
        + Hash(checker.value),
        value=tx_value,
    )

    # Construct the expected storage and balances.
    storage: dict[Address, dict[int, int | Address]] = {
        c: {} for c in contracts
    }
    for level in storing:
        storage[frames[level].address][level] = int(level != failed_level)
    storage[contracts[0]].update(
        {
            ENTRY_CONTEXT_SLOTS["caller"]: sender,
            ENTRY_CONTEXT_SLOTS["callvalue"]: tx_value,
            ENTRY_CONTEXT_SLOTS["origin"]: sender,
            ENTRY_CONTEXT_SLOTS["address"]: contracts[0],
        }
    )
    balance = dict.fromkeys(contracts[:-1], CONTRACT_BALANCE)
    balance[contracts[-1]] = 0
    balance[contracts[0]] += tx_value
    for level in storing:
        opcode, value = path[level]
        if opcode == Op.CALL:
            balance[frames[level].address] -= value
            balance[contracts[level + 1]] += value

    post = {
        contract: Account(storage=storage[contract], balance=balance[contract])
        for contract in contracts
    }

    state_test(pre=pre, post=post, tx=tx)
