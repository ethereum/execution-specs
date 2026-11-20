"""
The gas each opcode charges, against the framework.

Tests take an opcode's cost from the framework's `gas_cost(fork)`, which
prices it from metadata that describes the access: how far memory grows,
whether an address or key is warm, what a slot held. Here the access is
set up to match the metadata and the opcode is run in the spec: the frame
must finish on exactly the gas the framework prices and run out on one
less, and earn the refund the framework prices.
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Optional, Set

import pytest
from execution_testing import Bytecode, Op
from execution_testing.forks import Fork
from hypothesis import given
from hypothesis import strategies as st

from ethereum_spec_tools.forks import Hardfork

from .forks import SPEC_PACKAGES, requires
from .spec_api import add_account, block_state_with, run_code, set_storage
from .strategies import DELEGATION_PREFIX

CALLER = b"\x0c" * 20
# The account whose code is the opcode under test.
CONTRACT = b"\x0a" * 20
# The account an opcode reads, calls or pays.
TARGET = b"\x7a" * 20
DELEGATE = b"\xde" * 20
SLOT = 1

OPCODES = [
    opcode
    for opcode in Op
    if any(opcode in fork.valid_opcodes() for fork in SPEC_PACKAGES)
]
CONSTANT_OPCODES = [opcode for opcode in OPCODES if not opcode.metadata]
PRICED_BY_METADATA = [opcode for opcode in OPCODES if opcode.metadata]


@dataclass
class Scenario:
    """An opcode's arguments and metadata, and the state they describe."""

    arguments: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    # Code that runs before the opcode to bring about what it describes,
    # and after it.
    before: Bytecode = field(default_factory=Bytecode)
    after: Bytecode = field(default_factory=Bytecode)
    contract_balance: int = 0
    target_code: Optional[bytes] = None
    storage: Dict[int, int] = field(default_factory=dict)
    warm_addresses: Set[bytes] = field(default_factory=set)
    warm_storage_keys: Set[int] = field(default_factory=set)


def constant_code(opcode: Op) -> Bytecode:
    """Return code that runs `opcode` once, on a stack of zeros."""
    if opcode == Op.JUMP:
        return Op.JUMP(pc=3) + Op.JUMPDEST
    if opcode in (Op.DUPN, Op.SWAPN):
        return Op.PUSH1(0) * 20 + opcode[17]
    if opcode == Op.EXCHANGE:
        return Op.PUSH1(0) * 20 + opcode[1, 2]
    if opcode.data_portion_length:
        return opcode(0)
    if opcode.kwargs:
        arguments: Dict[str, Any] = dict.fromkeys(opcode.kwargs, 0)
        return opcode(**arguments)
    return Op.PUSH1(0) * (opcode.min_stack_height or 0) + opcode


def grow_memory(draw: st.DrawFn, opcode: Op, scenario: Scenario) -> None:
    """Point the opcode at memory, some of it already paid for."""
    arguments, metadata = scenario.arguments, scenario.metadata
    paid = draw(st.sampled_from([0, 32, 96]))
    if paid:
        scenario.before += Op.MSTORE(
            offset=paid - 32, value=0, new_memory_size=paid
        )
    offset = draw(st.sampled_from([0, 1, 31, 32, 100]))
    size = draw(st.sampled_from([0, 1, 32, 33, 70]))
    if opcode == Op.RETURNDATACOPY:
        # There is no return data to copy.
        size = 0

    # An access of no bytes grows nothing, wherever it points.
    ends = [offset + size if size else 0]
    if opcode in (Op.MLOAD, Op.MSTORE):
        arguments["offset"] = offset
        ends = [offset + 32]
    elif opcode == Op.MSTORE8:
        arguments["offset"] = offset
        ends = [offset + 1]
    elif "args_offset" in opcode.kwargs:
        ret_offset = draw(st.sampled_from([0, 64, 200]))
        ret_size = draw(st.sampled_from([0, 32]))
        arguments.update(
            args_offset=offset,
            args_size=size,
            ret_offset=ret_offset,
            ret_size=ret_size,
        )
        ends.append(ret_offset + ret_size if ret_size else 0)
    elif "dest_offset" in opcode.kwargs:
        arguments.update(dest_offset=offset, size=size)
    else:
        arguments.update(offset=offset, size=size)

    metadata.update(old_memory_size=paid, new_memory_size=max(paid, *ends))
    if "data_size" in opcode.metadata:
        metadata["data_size"] = size
    if "init_code_size" in opcode.metadata:
        metadata["init_code_size"] = size


def write_storage(draw: st.DrawFn, fork: Fork, scenario: Scenario) -> None:
    """
    Give the slot a value before the transaction and, when it differs,
    another one before the opcode writes a third.
    """
    metadata = scenario.metadata
    values = st.sampled_from([0, 1, 2])
    original, current, new = draw(values), draw(values), draw(values)
    if original:
        scenario.storage[SLOT] = original
    if current != original:
        # Only an earlier write in the transaction changes the slot, and
        # that write is priced as well.
        scenario.before += Op.SSTORE(
            key=SLOT,
            value=current,
            key_warm=metadata["key_warm"],
            original_value=original,
            new_value=current,
        )
        metadata.update(key_warm=True, current_value=current)
    scenario.arguments["value"] = new
    metadata.update(original_value=original, new_value=new)
    # EIP-2200: `SSTORE` fails unless more gas than the call stipend is
    # left, so the code after it costs that much.
    scenario.after += Op.JUMPDEST * fork.call_value_stipend()


def call_target(
    draw: st.DrawFn, fork: Fork, opcode: Op, scenario: Scenario
) -> None:
    """Call an account that may be missing, funded or delegated."""
    metadata = scenario.metadata
    value = 0
    if "value" in opcode.kwargs:
        value = draw(st.sampled_from([0, 1]))
        scenario.arguments["value"] = value
        scenario.contract_balance += value
        metadata["value_transfer"] = bool(value)

    if draw(st.booleans()):
        scenario.target_code = b""
    if fork.is_eip_enabled(7702) and draw(st.booleans()):
        scenario.target_code = DELEGATION_PREFIX + DELEGATE
        delegate_warm = draw(st.booleans())
        if delegate_warm:
            scenario.warm_addresses.add(DELEGATE)
        metadata.update(
            delegated_address=True, delegated_address_warm=delegate_warm
        )
    if opcode == Op.CALL:
        metadata["account_new"] = comes_into_being(
            fork, scenario, transfers=bool(value)
        )


def comes_into_being(
    fork: Fork, scenario: Scenario, *, transfers: bool
) -> bool:
    """
    Say whether the target is charged as a new account: one that does not
    exist yet and, from EIP-161, that is also sent value.
    """
    if scenario.target_code is not None:
        return False
    return transfers or not fork.is_eip_enabled(161)


@st.composite
def scenarios(draw: st.DrawFn, fork: Fork, opcode: Op) -> Scenario:
    """Draw what `opcode` accesses, with the metadata that describes it."""
    scenario = Scenario(arguments=dict.fromkeys(opcode.kwargs, 0))
    metadata = scenario.metadata

    if "new_memory_size" in opcode.metadata:
        grow_memory(draw, opcode, scenario)
    if "address_warm" in opcode.metadata:
        scenario.arguments["address"] = int.from_bytes(TARGET, "big")
        metadata["address_warm"] = draw(st.booleans())
        if metadata["address_warm"]:
            scenario.warm_addresses.add(TARGET)
    if "key_warm" in opcode.metadata:
        scenario.arguments["key"] = SLOT
        metadata["key_warm"] = draw(st.booleans())
        if metadata["key_warm"]:
            scenario.warm_storage_keys.add(SLOT)

    if opcode == Op.EXP:
        metadata["exponent"] = draw(
            st.sampled_from([0, 1, 255, 256, 2**64, 2**255])
        )
    elif opcode == Op.SSTORE:
        write_storage(draw, fork, scenario)
    elif "inner_call_cost" in opcode.metadata:
        call_target(draw, fork, opcode, scenario)
    elif opcode == Op.SELFDESTRUCT:
        scenario.contract_balance = draw(st.sampled_from([0, 1]))
        if draw(st.booleans()):
            scenario.target_code = b""
        metadata["account_new"] = comes_into_being(
            fork, scenario, transfers=scenario.contract_balance > 0
        )
        # A frame's first `SELFDESTRUCT` earns the refund, where there
        # is one.
        metadata["self_destructed_account"] = (
            fork.gas_costs().REFUND_SELF_DESTRUCT > 0
        )
    return scenario


def code_of(opcode: Op, scenario: Scenario) -> Bytecode:
    """Return the code that runs `opcode` as the scenario describes."""
    if opcode == Op.EXP:
        priced = opcode.with_metadata(**scenario.metadata)
        body = Op.PUSH32(scenario.metadata["exponent"]) + Op.PUSH1(2) + priced
    else:
        body = opcode(**scenario.arguments, **scenario.metadata)
    return scenario.before + body + scenario.after


def run(
    spec: Hardfork,
    code: Bytecode,
    scenario: Scenario,
    *,
    gas: int,
    reservoir: int = 0,
) -> Any:
    """Run `code` in the state the scenario describes."""
    block_state = block_state_with(
        spec.module("state_tracker"), CALLER, nonce=1, balance=0
    )
    # EIP-7523: an account that exists is never empty.
    add_account(
        block_state,
        CONTRACT,
        nonce=1,
        balance=scenario.contract_balance,
        code=bytes(code),
    )
    if scenario.target_code is not None:
        add_account(
            block_state, TARGET, nonce=1, balance=1, code=scenario.target_code
        )
    for key, value in scenario.storage.items():
        set_storage(block_state, CONTRACT, key, value)
    return run_code(
        spec,
        block_state,
        bytes(code),
        caller=CALLER,
        address=CONTRACT,
        gas=gas,
        state_gas=reservoir,
        warm_addresses=scenario.warm_addresses,
        warm_storage_keys=scenario.warm_storage_keys,
    )


def check_charge(
    fork: Fork,
    spec: Hardfork,
    code: Bytecode,
    scenario: Scenario,
    data: Optional[st.DataObject] = None,
) -> None:
    """Run `code` on exactly the gas the framework prices and on one less."""
    exceptions = spec.module("vm.exceptions")
    total = code.gas_cost(fork)
    # EIP-8037: state gas comes out of a reservoir first, and out of the
    # frame's gas for what the reservoir lacks.
    state_gas = code.state_cost(fork)
    reservoir = 0
    if state_gas:
        assert data is not None
        reservoir = data.draw(
            st.sampled_from([0, state_gas // 2, state_gas, 2 * state_gas]),
            label="reservoir",
        )
    needed = total - min(state_gas, reservoir)

    exact = run(spec, code, scenario, gas=needed, reservoir=reservoir)
    # `REVERT` ends the frame without running out of gas.
    reverted = getattr(exceptions, "Revert", ())
    assert exact.error is None or isinstance(exact.error, reverted), (
        f"{needed} gas did not cover the code: {exact.error!r}"
    )
    # EIP-8037: a state gas refund goes back to the gas that paid for it,
    # not to the refund counter.
    state_refund = code.state_refund(fork)
    assert exact.refund == code.refund(fork) - state_refund
    unspent = reservoir - min(state_gas, reservoir)
    # A call that sends value hands its callee a stipend on top of the
    # charge, and this callee returns it untouched.
    stipend = 0
    if scenario.metadata.get("value_transfer"):
        stipend = fork.call_value_stipend()
    if state_refund:
        # The refund fills the frame's gas up to what the charge took
        # from it, and the reservoir with the rest.
        to_gas_left = min(state_refund, state_gas - min(state_gas, reservoir))
        assert exact.gas_left == to_gas_left
        assert exact.state_gas_left == unspent + state_refund - to_gas_left
    else:
        assert exact.gas_left == stipend
        assert exact.state_gas_left == unspent

    # A state gas refund pays for the code after it, so less than the sum
    # of the charges can be enough.
    if needed > 0 and not state_refund:
        short = run(spec, code, scenario, gas=needed - 1, reservoir=reservoir)
        assert isinstance(short.error, exceptions.OutOfGasError), (
            f"the code ran on {needed - 1} gas"
        )


def priced_by(opcode: Op) -> Callable[[Fork], bool]:
    """Return the condition that a fork has `opcode`."""
    return lambda fork: opcode in fork.valid_opcodes()


def test_constant_opcodes_charge_what_the_framework_prices(
    fork: Fork, spec: Hardfork
) -> None:
    """
    Every opcode of the fork whose cost is fixed charges that cost, with
    the pushes that fill its stack.
    """
    opcodes = [
        opcode for opcode in CONSTANT_OPCODES if opcode in fork.valid_opcodes()
    ]
    assert opcodes
    for opcode in opcodes:
        try:
            check_charge(fork, spec, constant_code(opcode), Scenario())
        except AssertionError as error:
            raise AssertionError(f"{opcode._name_}: {error}") from error


@pytest.mark.parametrize(
    "opcode",
    [
        pytest.param(
            opcode,
            id=opcode._name_,
            marks=requires(priced_by(opcode)),
        )
        for opcode in PRICED_BY_METADATA
    ],
)
@given(data=st.data())
def test_opcode_charge_matches_the_framework(
    fork: Fork, spec: Hardfork, opcode: Op, data: st.DataObject
) -> None:
    """
    An opcode whose cost depends on what it accesses charges what the
    framework prices for that access, and earns the refund it prices.
    """
    scenario = data.draw(scenarios(fork, opcode))
    check_charge(fork, spec, code_of(opcode, scenario), scenario, data)


@requires(lambda fork: fork.is_eip_enabled(2200))
@pytest.mark.parametrize("gas_left", ["stipend", "above_stipend"])
def test_sstore_needs_more_gas_than_the_stipend(
    fork: Fork, spec: Hardfork, gas_left: str
) -> None:
    """
    EIP-2200: `SSTORE` fails unless more gas than the call stipend is
    left, however little it charges.
    """
    arguments = Op.PUSH1(0) + Op.PUSH1(SLOT)
    # A write that changes nothing is the cheapest one.
    write = Op.SSTORE.with_metadata(key_warm=True, new_value=0)
    padding = fork.call_value_stipend() - write.gas_cost(fork)
    assert padding > 0
    assert Op.JUMPDEST.gas_cost(fork) == 1
    if gas_left == "above_stipend":
        padding += 1
    elif gas_left != "stipend":
        raise ValueError(f"unknown gas left: {gas_left}")
    code = arguments + write + Op.JUMPDEST * padding
    # EIP-8037: the check counts the frame's gas only, so a reservoir of
    # state gas does not help.
    reservoir = 0
    if fork.state_gas_reservoir_enabled():
        reservoir = fork.call_value_stipend()

    frame = run(
        spec,
        code,
        Scenario(warm_storage_keys={SLOT}),
        gas=code.gas_cost(fork),
        reservoir=reservoir,
    )

    if gas_left == "stipend":
        out_of_gas = spec.module("vm.exceptions").OutOfGasError
        assert isinstance(frame.error, out_of_gas)
    else:
        assert frame.error is None


@requires(lambda fork: fork.state_gas_reservoir_enabled())
def test_failed_creation_returns_its_state_gas(
    fork: Fork, spec: Hardfork
) -> None:
    """
    EIP-8037: the state gas a creation pays for its new account goes back
    to the reservoir when the init code fails.
    """
    for opcode in fork.create_opcodes():
        code = Op.MSTORE8(
            offset=0, value=Op.INVALID.int(), new_memory_size=1
        ) + opcode(
            value=0,
            offset=0,
            size=1,
            init_code_size=1,
            old_memory_size=1,
            new_memory_size=1,
        )
        state_gas = code.state_cost(fork)
        assert state_gas > 0

        frame = run(
            spec,
            code,
            Scenario(),
            gas=code.execution_cost(fork),
            reservoir=state_gas,
        )

        assert frame.error is None
        assert frame.gas_left == 0
        assert frame.state_gas_left == state_gas
