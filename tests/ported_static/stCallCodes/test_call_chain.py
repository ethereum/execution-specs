"""
Chains of CALL / CALLCODE / DELEGATECALL: where each level's storage writes
land, and what context the innermost code observes.

Ported from:
state_tests/stCallCodes/callcallcall_000Filler.json
state_tests/stCallCodes/callcallcallcode_001Filler.json
state_tests/stCallCodes/callcallcodecall_010Filler.json
state_tests/stCallCodes/callcallcodecallcode_011Filler.json
state_tests/stCallCodes/callcodecallcall_100Filler.json
state_tests/stCallCodes/callcodecallcallcode_101Filler.json
state_tests/stCallCodes/callcodecallcodecall_110Filler.json
state_tests/stCallCodes/callcodecallcodecallcode_111Filler.json
state_tests/stCallDelegateCodesHomestead/callcallcallcode_001Filler.json
state_tests/stCallDelegateCodesHomestead/callcallcodecall_010Filler.json
state_tests/stCallDelegateCodesHomestead/callcallcodecallcode_011Filler.json
state_tests/stCallDelegateCodesHomestead/callcodecallcall_100Filler.json
state_tests/stCallDelegateCodesHomestead/callcodecallcallcode_101Filler.json
state_tests/stCallDelegateCodesHomestead/callcodecallcodecall_110Filler.json
state_tests/stCallDelegateCodesHomestead/callcodecallcodecallcode_111Filler.json
state_tests/stCallDelegateCodesCallCodeHomestead/callcallcallcode_001Filler.json
state_tests/stCallDelegateCodesCallCodeHomestead/callcallcodecall_010Filler.json
state_tests/stCallDelegateCodesCallCodeHomestead/callcallcodecallcode_011Filler.json
state_tests/stCallDelegateCodesCallCodeHomestead/callcodecallcall_100Filler.json
state_tests/stCallDelegateCodesCallCodeHomestead/callcodecallcallcode_101Filler.json
state_tests/stCallDelegateCodesCallCodeHomestead/callcodecallcodecall_110Filler.json
state_tests/stCallDelegateCodesCallCodeHomestead/callcodecallcodecallcode_111Filler.json
state_tests/stCallCodes/callcall_00Filler.json
state_tests/stCallCodes/callcallcode_01Filler.json
state_tests/stCallCodes/callcodecall_10Filler.json
state_tests/stCallCodes/callcodecallcode_11Filler.json
state_tests/stCallDelegateCodesHomestead/callcallcode_01Filler.json
state_tests/stCallDelegateCodesHomestead/callcodecall_10Filler.json
state_tests/stCallDelegateCodesHomestead/callcodecallcode_11Filler.json
state_tests/stCallDelegateCodesCallCodeHomestead/callcallcode_01Filler.json
state_tests/stCallDelegateCodesCallCodeHomestead/callcodecall_10Filler.json
state_tests/stCallDelegateCodesCallCodeHomestead/callcodecallcode_11Filler.json
state_tests/stCallCodes/callcallcall_ABCB_RECURSIVEFiller.json
state_tests/stCallCodes/callcallcallcode_ABCB_RECURSIVEFiller.json
state_tests/stCallCodes/callcallcodecall_ABCB_RECURSIVEFiller.json
state_tests/stCallCodes/callcallcodecallcode_ABCB_RECURSIVEFiller.json
state_tests/stCallCodes/callcodecallcall_ABCB_RECURSIVEFiller.json
state_tests/stCallCodes/callcodecallcallcode_ABCB_RECURSIVEFiller.json
state_tests/stCallCodes/callcodecallcodecall_ABCB_RECURSIVEFiller.json
state_tests/stCallCodes/callcodecallcodecallcode_ABCB_RECURSIVEFiller.json
state_tests/stCallDelegateCodesHomestead/callcallcallcode_ABCB_RECURSIVEFiller.json
state_tests/stCallDelegateCodesHomestead/callcallcodecall_ABCB_RECURSIVEFiller.json
state_tests/stCallDelegateCodesHomestead/callcallcodecallcode_ABCB_RECURSIVEFiller.json
state_tests/stCallDelegateCodesHomestead/callcodecallcall_ABCB_RECURSIVEFiller.json
state_tests/stCallDelegateCodesHomestead/callcodecallcallcode_ABCB_RECURSIVEFiller.json
state_tests/stCallDelegateCodesHomestead/callcodecallcodecall_ABCB_RECURSIVEFiller.json
state_tests/stCallDelegateCodesHomestead/callcodecallcodecallcode_ABCB_RECURSIVEFiller.json
state_tests/stCallDelegateCodesCallCodeHomestead/callcallcallcode_ABCB_RECURSIVEFiller.json
state_tests/stCallDelegateCodesCallCodeHomestead/callcallcodecall_ABCB_RECURSIVEFiller.json
state_tests/stCallDelegateCodesCallCodeHomestead/callcallcodecallcode_ABCB_RECURSIVEFiller.json
state_tests/stCallDelegateCodesCallCodeHomestead/callcodecallcall_ABCB_RECURSIVEFiller.json
state_tests/stCallDelegateCodesCallCodeHomestead/callcodecallcallcode_ABCB_RECURSIVEFiller.json
state_tests/stCallDelegateCodesCallCodeHomestead/callcodecallcodecall_ABCB_RECURSIVEFiller.json
state_tests/stCallDelegateCodesCallCodeHomestead/callcodecallcodecallcode_ABCB_RECURSIVEFiller.json

@manually-enhanced: Do not overwrite. The fillers are one chain test copied
into three directories, each substituting a different pair of call opcodes,
so they collapse to one test per chain depth parametrized on every chain of
CALL, CALLCODE and DELEGATECALL. The Homestead copies added CALLER stores to
some intermediate levels and moved the innermost CALLVALUE store between
slots 5, 6 and 7; every level now stores CALLER and the innermost code
stores CALLVALUE in slot 7. The post state is derived from the opcodes:
CALL moves the context to the callee, CALLCODE keeps the caller's account
but makes it the CALLER, and DELEGATECALL keeps the caller's whole context.

In the recursive A -> B -> C -> B chains, the fillers recursed until the
gas ran out (about 132 rounds, of which only the first re-entry decided the
outcome). The recursion is now bounded by a round count passed down as
calldata, together with B's address, which C would otherwise have to embed
while B embeds C's.
"""

from dataclasses import dataclass
from itertools import product

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

CALL_OPCODES = {
    "call": Op.CALL,
    "callcode": Op.CALLCODE,
    "delegatecall": Op.DELEGATECALL,
}
CONTRACT_BALANCE = 10**18
GAS_PRICE = 10
WINDOW = 64
CALLER_SLOT = 4
CALLVALUE_SLOT = 7
ROUNDS_SLOT_OFFSET = 32


def call_chains(depth: int) -> list:
    """Return every chain of `depth` call opcodes as a pytest parameter."""
    return [
        pytest.param(
            tuple(CALL_OPCODES[name] for name in names), id="_".join(names)
        )
        for names in product(CALL_OPCODES, repeat=depth)
    ]


@dataclass(frozen=True)
class Frame:
    """Execution context of one level of a call chain."""

    address: Address
    caller: Address
    value: int

    def enter(self, opcode: Op, callee: Address, value: int) -> "Frame":
        """Return the context in which `opcode` runs `callee`'s code."""
        if opcode == Op.CALL:
            return Frame(address=callee, caller=self.address, value=value)
        if opcode == Op.CALLCODE:
            return Frame(
                address=self.address, caller=self.address, value=value
            )
        return self


def run_call_chain(
    state_test: StateTestFiller, pre: Alloc, chain: tuple[Op, ...]
) -> None:
    """
    Call down `chain`, one contract per opcode, and check each level's
    writes and balance and the context the innermost code observes.

    Level `n` stores its call's success in slot `n` and, below the top
    level, its CALLER in slot `CALLER_SLOT + n`.
    """
    depth = len(chain)
    sender = pre.fund_eoa()
    context_base = depth * 100

    # Construct the innermost contract.
    # Source: lll
    # {  (SSTORE 3 1) (SSTORE 4 (CALLER)) (SSTORE 7 (CALLVALUE)) (SSTORE 330 (ADDRESS)) (SSTORE 332 (ORIGIN)) (SSTORE 336 (CALLDATASIZE)) (SSTORE 338 (CODESIZE)) (SSTORE 340 (GASPRICE)) }  # noqa: E501
    leaf_code = (
        Op.SSTORE(depth, 1)
        + Op.SSTORE(CALLER_SLOT, Op.CALLER)
        + Op.SSTORE(CALLVALUE_SLOT, Op.CALLVALUE)
        + Op.SSTORE(context_base + 30, Op.ADDRESS)
        + Op.SSTORE(context_base + 32, Op.ORIGIN)
        + Op.SSTORE(context_base + 36, Op.CALLDATASIZE)
        + Op.SSTORE(context_base + 38, Op.CODESIZE)
        + Op.SSTORE(context_base + 40, Op.GASPRICE)
        + Op.STOP
    )

    # Assign call values: the k-th call that carries a value sends k wei.
    values = []
    sent = 0
    for opcode in chain:
        if opcode != Op.DELEGATECALL:
            sent += 1
        values.append(0 if opcode == Op.DELEGATECALL else sent)

    # Construct the calling contracts, from the innermost one outward.
    # Source: lll
    # {  [[ 2 ]] (CALL 250000 <contract:0x1000000000000000000000000000000000000003> 3 0 64 0 64 ) }  # noqa: E501
    contracts = [pre.deploy_contract(code=leaf_code, balance=CONTRACT_BALANCE)]
    for level in reversed(range(depth)):
        opcode = chain[level]
        if opcode == Op.DELEGATECALL:
            call = opcode(
                address=contracts[0], args_size=WINDOW, ret_size=WINDOW
            )
        else:
            call = opcode(
                address=contracts[0],
                value=values[level],
                args_size=WINDOW,
                ret_size=WINDOW,
            )
        code = Op.SSTORE(level, call)
        if level > 0:
            code += Op.SSTORE(CALLER_SLOT + level, Op.CALLER)
        contracts.insert(
            0,
            pre.deploy_contract(code=code + Op.STOP, balance=CONTRACT_BALANCE),
        )

    # Construct the transaction.
    tx = Transaction(sender=sender, to=contracts[0], gas_price=GAS_PRICE)

    # Simulate each call's context and value transfer.
    frames = [Frame(address=contracts[0], caller=sender, value=0)]
    balance = dict.fromkeys(contracts, CONTRACT_BALANCE)
    for opcode, callee, value in zip(
        chain, contracts[1:], values, strict=True
    ):
        frame = frames[-1]
        if opcode == Op.CALL:
            balance[frame.address] -= value
            balance[callee] += value
        frames.append(frame.enter(opcode, callee, value))

    # Construct the expected storage.
    storage: dict[Address, dict[int, int | Address]] = {
        c: {} for c in contracts
    }
    for level, frame in enumerate(frames[:-1]):
        storage[frame.address][level] = 1
        if level > 0:
            storage[frame.address][CALLER_SLOT + level] = frame.caller
    leaf = frames[-1]
    storage[leaf.address].update(
        {
            depth: 1,
            CALLER_SLOT: leaf.caller,
            CALLVALUE_SLOT: leaf.value,
            context_base + 30: leaf.address,
            context_base + 32: sender,
            context_base + 36: WINDOW,
            context_base + 38: len(leaf_code),
            context_base + 40: GAS_PRICE,
        }
    )

    # Construct the expected post-state.
    post = {
        contract: Account(storage=storage[contract], balance=balance[contract])
        for contract in contracts
    }

    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    [
        "state_tests/stCallCodes/callcallcall_000Filler.json",
        "state_tests/stCallCodes/callcallcallcode_001Filler.json",
        "state_tests/stCallCodes/callcallcodecall_010Filler.json",
        "state_tests/stCallCodes/callcallcodecallcode_011Filler.json",
        "state_tests/stCallCodes/callcodecallcall_100Filler.json",
        "state_tests/stCallCodes/callcodecallcallcode_101Filler.json",
        "state_tests/stCallCodes/callcodecallcodecall_110Filler.json",
        "state_tests/stCallCodes/callcodecallcodecallcode_111Filler.json",
        "state_tests/stCallDelegateCodesHomestead/callcallcallcode_001Filler.json",  # noqa: E501
        "state_tests/stCallDelegateCodesHomestead/callcallcodecall_010Filler.json",  # noqa: E501
        "state_tests/stCallDelegateCodesHomestead/callcallcodecallcode_011Filler.json",  # noqa: E501
        "state_tests/stCallDelegateCodesHomestead/callcodecallcall_100Filler.json",  # noqa: E501
        "state_tests/stCallDelegateCodesHomestead/callcodecallcallcode_101Filler.json",  # noqa: E501
        "state_tests/stCallDelegateCodesHomestead/callcodecallcodecall_110Filler.json",  # noqa: E501
        "state_tests/stCallDelegateCodesHomestead/callcodecallcodecallcode_111Filler.json",  # noqa: E501
        "state_tests/stCallDelegateCodesCallCodeHomestead/callcallcallcode_001Filler.json",  # noqa: E501
        "state_tests/stCallDelegateCodesCallCodeHomestead/callcallcodecall_010Filler.json",  # noqa: E501
        "state_tests/stCallDelegateCodesCallCodeHomestead/callcallcodecallcode_011Filler.json",  # noqa: E501
        "state_tests/stCallDelegateCodesCallCodeHomestead/callcodecallcall_100Filler.json",  # noqa: E501
        "state_tests/stCallDelegateCodesCallCodeHomestead/callcodecallcallcode_101Filler.json",  # noqa: E501
        "state_tests/stCallDelegateCodesCallCodeHomestead/callcodecallcodecall_110Filler.json",  # noqa: E501
        "state_tests/stCallDelegateCodesCallCodeHomestead/callcodecallcodecallcode_111Filler.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize("chain", call_chains(3))
def test_three_level_call_chain(
    state_test: StateTestFiller, pre: Alloc, chain: tuple[Op, Op, Op]
) -> None:
    """Call -> call -> call -> code, every combination of call opcodes."""
    run_call_chain(state_test, pre, chain)


@pytest.mark.ported_from(
    [
        "state_tests/stCallCodes/callcall_00Filler.json",
        "state_tests/stCallCodes/callcallcode_01Filler.json",
        "state_tests/stCallCodes/callcodecall_10Filler.json",
        "state_tests/stCallCodes/callcodecallcode_11Filler.json",
        "state_tests/stCallDelegateCodesHomestead/callcallcode_01Filler.json",
        "state_tests/stCallDelegateCodesHomestead/callcodecall_10Filler.json",
        "state_tests/stCallDelegateCodesHomestead/callcodecallcode_11Filler.json",  # noqa: E501
        "state_tests/stCallDelegateCodesCallCodeHomestead/callcallcode_01Filler.json",  # noqa: E501
        "state_tests/stCallDelegateCodesCallCodeHomestead/callcodecall_10Filler.json",  # noqa: E501
        "state_tests/stCallDelegateCodesCallCodeHomestead/callcodecallcode_11Filler.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize("chain", call_chains(2))
def test_two_level_call_chain(
    state_test: StateTestFiller, pre: Alloc, chain: tuple[Op, Op]
) -> None:
    """Call -> call -> code, every combination of call opcodes."""
    run_call_chain(state_test, pre, chain)


@pytest.mark.ported_from(
    [
        "state_tests/stCallCodes/callcallcall_ABCB_RECURSIVEFiller.json",
        "state_tests/stCallCodes/callcallcallcode_ABCB_RECURSIVEFiller.json",  # noqa: E501
        "state_tests/stCallCodes/callcallcodecall_ABCB_RECURSIVEFiller.json",  # noqa: E501
        "state_tests/stCallCodes/callcallcodecallcode_ABCB_RECURSIVEFiller.json",  # noqa: E501
        "state_tests/stCallCodes/callcodecallcall_ABCB_RECURSIVEFiller.json",  # noqa: E501
        "state_tests/stCallCodes/callcodecallcallcode_ABCB_RECURSIVEFiller.json",  # noqa: E501
        "state_tests/stCallCodes/callcodecallcodecall_ABCB_RECURSIVEFiller.json",  # noqa: E501
        "state_tests/stCallCodes/callcodecallcodecallcode_ABCB_RECURSIVEFiller.json",  # noqa: E501
        "state_tests/stCallDelegateCodesHomestead/callcallcallcode_ABCB_RECURSIVEFiller.json",  # noqa: E501
        "state_tests/stCallDelegateCodesHomestead/callcallcodecall_ABCB_RECURSIVEFiller.json",  # noqa: E501
        "state_tests/stCallDelegateCodesHomestead/callcallcodecallcode_ABCB_RECURSIVEFiller.json",  # noqa: E501
        "state_tests/stCallDelegateCodesHomestead/callcodecallcall_ABCB_RECURSIVEFiller.json",  # noqa: E501
        "state_tests/stCallDelegateCodesHomestead/callcodecallcallcode_ABCB_RECURSIVEFiller.json",  # noqa: E501
        "state_tests/stCallDelegateCodesHomestead/callcodecallcodecall_ABCB_RECURSIVEFiller.json",  # noqa: E501
        "state_tests/stCallDelegateCodesHomestead/callcodecallcodecallcode_ABCB_RECURSIVEFiller.json",  # noqa: E501
        "state_tests/stCallDelegateCodesCallCodeHomestead/callcallcallcode_ABCB_RECURSIVEFiller.json",  # noqa: E501
        "state_tests/stCallDelegateCodesCallCodeHomestead/callcallcodecall_ABCB_RECURSIVEFiller.json",  # noqa: E501
        "state_tests/stCallDelegateCodesCallCodeHomestead/callcallcodecallcode_ABCB_RECURSIVEFiller.json",  # noqa: E501
        "state_tests/stCallDelegateCodesCallCodeHomestead/callcodecallcall_ABCB_RECURSIVEFiller.json",  # noqa: E501
        "state_tests/stCallDelegateCodesCallCodeHomestead/callcodecallcallcode_ABCB_RECURSIVEFiller.json",  # noqa: E501
        "state_tests/stCallDelegateCodesCallCodeHomestead/callcodecallcodecall_ABCB_RECURSIVEFiller.json",  # noqa: E501
        "state_tests/stCallDelegateCodesCallCodeHomestead/callcodecallcodecallcode_ABCB_RECURSIVEFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize("rounds", [0, 1, 40], ids=lambda r: f"rounds_{r}")
@pytest.mark.parametrize("chain", call_chains(3))
def test_recursive_call_chain(
    state_test: StateTestFiller,
    pre: Alloc,
    chain: tuple[Op, Op, Op],
    rounds: int,
) -> None:
    """
    Call A -> B -> C, where C calls B again for `rounds` more rounds of
    B -> C, and the last C calls B with no gas so that call fails.

    `rounds=0` is the outcome the fillers checked: their recursion ran until
    the gas ran out, but the first recursive B already failed, so only A,
    B and the first C kept their writes. 40 rounds is about as far as the
    fillers' recursion did any work before its gas thinned out.
    """
    a_to_b, b_to_c, c_to_b = chain

    # Construct C, which calls back the address it receives as calldata
    # with one round less, or with no gas once no rounds are left.
    # Source: lll
    # {  [[ 2 ]] (CALL 500000 <contract:0x1000000000000000000000000000000000000001> 0 0 64 0 64 ) }  # noqa: E501
    rounds_left = Op.CALLDATALOAD(ROUNDS_SLOT_OFFSET)
    c = pre.deploy_contract(
        code=Op.CALLDATACOPY(dest_offset=0, offset=0, size=WINDOW)
        + Op.MSTORE(ROUNDS_SLOT_OFFSET, Op.SUB(rounds_left, 1))
        + Op.SSTORE(
            2,
            c_to_b(
                gas=Op.MUL(Op.GAS, Op.ISZERO(Op.ISZERO(rounds_left))),
                address=Op.CALLDATALOAD(0),
                args_size=WINDOW,
            ),
        )
        + Op.STOP,
        balance=CONTRACT_BALANCE,
    )

    # Construct B, which forwards its calldata to C.
    # Source: lll
    # {  [[ 1 ]] (CALL 1000000 <contract:0x1000000000000000000000000000000000000002> 0 0 64 0 64 ) }  # noqa: E501
    b = pre.deploy_contract(
        code=Op.CALLDATACOPY(dest_offset=0, offset=0, size=WINDOW)
        + Op.SSTORE(1, b_to_c(address=c, args_size=WINDOW))
        + Op.STOP,
        balance=CONTRACT_BALANCE,
    )

    # Construct A, which passes B's address and the round count down as
    # calldata.
    # Source: lll
    # {  [[ 0 ]] (CALL 25000000 <contract:0x1000000000000000000000000000000000000001> 0 0 64 0 64 ) }  # noqa: E501
    a = pre.deploy_contract(
        code=Op.MSTORE(0, b)
        + Op.MSTORE(ROUNDS_SLOT_OFFSET, rounds)
        + Op.SSTORE(0, a_to_b(address=b, args_size=WINDOW))
        + Op.STOP,
        balance=CONTRACT_BALANCE,
    )

    # Construct the transaction.
    sender = pre.fund_eoa()
    tx = Transaction(sender=sender, to=a)

    # Simulate the contexts of every frame, from A down to the last C,
    # with the slot each one stores its call's result in.
    frame = Frame(address=a, caller=sender, value=0)
    writes = [(frame, 0)]
    frame = frame.enter(a_to_b, b, 0)
    writes.append((frame, 1))
    frame = frame.enter(b_to_c, c, 0)
    writes.append((frame, 2))
    for _ in range(rounds):
        frame = frame.enter(c_to_b, b, 0)
        writes.append((frame, 1))
        frame = frame.enter(b_to_c, c, 0)
        writes.append((frame, 2))

    # Construct the expected storage: the frames store after their call
    # returns, innermost first; every call succeeds but the last C's.
    storage: dict[Address, dict[int, int]] = {a: {}, b: {}, c: {}}
    for index, (frame, slot) in reversed(list(enumerate(writes))):
        storage[frame.address][slot] = int(index < len(writes) - 1)

    # Construct the expected post-state.
    post = {
        contract: Account(storage=storage[contract], balance=CONTRACT_BALANCE)
        for contract in (a, b, c)
    }

    state_test(pre=pre, post=post, tx=tx)
