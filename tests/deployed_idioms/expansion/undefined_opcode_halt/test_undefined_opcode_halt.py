"""
Candidate class: an undefined opcode byte halts exceptionally, and
deployed code relies on it.

The classic deployed spelling is `0xfe` -- solc `<0.8` compiled `assert`
to `INVALID`, and solc `<=0.4.12` compiled `throw` to it -- used as a
guaranteed halt that is cheaper than `REVERT` and leaves no return data.
`0xfe` is reserved for that purpose forever, so it is safe. **Any other
undefined byte written into the same position is not**, and four EIPs have
now claimed five of them:

```text
0x5F  PUSH0                     EIP-3855   Shanghai
0x1E  CLZ                       EIP-7939   Osaka
0x4B  SLOTNUM                   EIP-7843   Amsterdam
0xE6  DUPN      + 1 immediate   EIP-8024   Amsterdam
0xE7  SWAPN     + 1 immediate   EIP-8024   Amsterdam
0xE8  EXCHANGE  + 1 immediate   EIP-8024   Amsterdam
```

**Mechanism** (CHECKED, at the pinned Amsterdam commit):

```text
try:    op = Ops(evm.code[evm.pc])
except ValueError as e:
        raise InvalidOpcode(evm.code[evm.pc]) from e
                                       amsterdam/vm/interpreter.py:440-442
InvalidOpcode is an ExceptionalHalt, so the handler runs
        restore_state_gas(...); forfeit_remaining_gas(...)
                                       amsterdam/vm/interpreter.py:455-457
```

`0xFE` is **not** a named member of `Ops` in EELS on any fork in range, so
the designated-INVALID byte and a merely unassigned byte halt through
exactly the same code path (CHECKED: no `= 0xFE` assignment exists in
`vm/instructions/__init__.py` for Berlin..Amsterdam -- 8 forks checked).

**Why no gas-shaped archetype can see this.** Assignment moves no price.
The frame stops being a halt and starts being a success, the code behind
the byte starts executing, and every constant in `vm/gas.py` is
untouched. This is the same blind spot EIP-7702 opened for class #22:
semantics changed, nothing was repriced.

**Relation to the official suites.** The EIP-7939/7843/8024 directories
each carry a `ForkTransition.Invalid` test that observes the pre-fork halt
(`tests/osaka/eip7939_count_leading_zeros/test_count_leading_zeros.py:274`,
`tests/amsterdam/eip7843_slotnum/test_fork_transition.py:30`,
`tests/amsterdam/eip8024_dupn_swapn_exchange/test_fork_transition.py:43`).
Three differences, all deliberate:

1. Those are `valid_at_transition_to(...)` blockchain tests. They observe
   the halt in **one block, on one fork boundary**. The deployed idiom
   relies on it across every fork the code has lived through, which is
   what `valid_until` expresses here.
2. In those tests the opcode is the **last** thing that runs before its
   result is stored, so the post-fork outcome reads as "the new feature
   works". Here real code sits **behind** the byte and must never run, so
   the post-fork outcome reads as "a guard vanished and a forbidden write
   committed". Same rule, opposite side.
3. Nothing there asserts that undefined bytes in *unreachable* positions
   leave a contract runnable, which is the invariant with the largest
   deployed population by far (every contract's trailing metadata).
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytecode,
    Op,
    StateTestFiller,
    Storage,
    Transaction,
)

REFERENCE_SPEC_GIT_PATH = "EIPS/eip-7843.md"
REFERENCE_SPEC_VERSION = "N/A"  # no single spec owns the invariant

# Sentinel the guarded slot holds before anything runs. Asserting that
# it is *still* there is a positive statement; asserting 0 would also be
# satisfied by a slot that was never written at all.
SENTINEL = 0x5AFE
FORBIDDEN = 0xBAD

# byte sequence -> stack items the frame is given before the byte.
#   decode_single(0x80) = (128 + 145) % 256 = 17   -> DUPN/SWAPN index 17
#   decode_pair(0x8E):   k = 0x8E ^ 143 = 1        -> EXCHANGE(1, 2)
# `vm/stack.py:25,55`.
#
# EXCHANGE's figure is 15, not the 3 its decoded pair needs, and that is
# deliberate: the immediate byte 0x8E is *itself* `DUP15`, so under the
# `exp-op-undefined-is-a-noop-*` mutation -- which skips 0xE8 and then
# executes 0x8E as an ordinary opcode -- a 3-deep stack underflows and
# the mutation is survived for an irrelevant reason. At 15 the mutation
# can reach this param. Measured: with 3 the exchange arm survives
# `exp-op-undefined-is-a-noop-osaka`; with 15 it is DETECTED.
BYTES: dict[str, tuple[bytes, int]] = {
    "push0_5f": (b"\x5f", 0),
    "clz_1e": (b"\x1e", 1),
    "slotnum_4b": (b"\x4b", 0),
    "dupn_e6": (b"\xe6\x80", 17),
    "swapn_e7": (b"\xe7\x80", 18),
    "exchange_e8": (b"\xe8\x8e", 15),
}

# The fork that assigns each byte, and the last fork on which a deployed
# guaranteed-halt guard written with it still works.
ASSIGNED_AT = {
    "push0_5f": ("Shanghai", "Paris"),
    "clz_1e": ("Osaka", "Prague"),
    "slotnum_4b": ("Amsterdam", "Osaka"),
    "dupn_e6": ("Amsterdam", "Osaka"),
    "swapn_e7": ("Amsterdam", "Osaka"),
    "exchange_e8": ("Amsterdam", "Osaka"),
}

PRE_ASSIGNMENT = [
    pytest.param(
        name,
        id=name,
        marks=[
            pytest.mark.valid_from("Berlin"),
            pytest.mark.valid_until(ASSIGNED_AT[name][1]),
        ],
    )
    for name in BYTES
]

POST_ASSIGNMENT = [
    pytest.param(
        name,
        id=name,
        marks=pytest.mark.valid_from(ASSIGNED_AT[name][0]),
    )
    for name in BYTES
]


def raw(code: bytes) -> Bytecode:
    """Emit literal bytes, with no stack bookkeeping claimed for them."""
    return Bytecode(code, popped_stack_items=0, pushed_stack_items=0)


def _guard(pre: Alloc, byte_name: str, reached: bool) -> tuple:
    """
    A frame that falls through onto the byte, with a forbidden SSTORE
    sitting behind it.

    The `pad` pushes are the only artificial part and they are load
    bearing in one direction only: without them, DUPN/SWAPN/EXCHANGE
    would halt on *stack underflow* after assignment and the flip would
    be invisible. Measured (CHECKED, `expansion/tests/tools`): at
    Amsterdam the byte stops guarding at stack depth >= 17 for 0xE6,
    >= 18 for 0xE7 and >= 3 for 0xE8 with immediate 0x8E, while 0x4B and
    0x5F stop guarding at depth 0 -- they consume nothing. So the two
    zero-input assignments break a guard unconditionally and EIP-8024's
    three break it only in a deep frame. The underflow behaviour itself
    is already swept by
    `tests/amsterdam/eip8024_dupn_swapn_exchange/test_dupn.py:246` and
    `test_swapn.py:301`, and is not re-asserted here.
    """
    code, pad = BYTES[byte_name]
    storage = Storage()
    address = pre.deploy_contract(
        sum((Op.PUSH1(1) for _ in range(pad)), Bytecode())
        + raw(code)
        + Op.SSTORE(
            storage.store_next(
                FORBIDDEN if reached else SENTINEL, "guarded_slot"
            ),
            FORBIDDEN,
        )
        + Op.STOP,
        storage={0: SENTINEL},
    )
    return address, storage


def _probe(pre: Alloc, guard, ok: int) -> tuple:
    """A caller that tolerates the guard's failure and records it."""
    storage = Storage()
    address = pre.deploy_contract(
        # Forward GAS, never a literal: a literal gas operand in support
        # code is itself a frozen budget, and the Amsterdam floor for one
        # fresh slot is ~110,026 (class #1).
        Op.SSTORE(
            storage.store_next(ok, "call_succeeded"),
            Op.CALL(gas=Op.GAS, address=guard),
        )
        + Op.STOP
    )
    return address, storage


@pytest.mark.parametrize("byte_name", PRE_ASSIGNMENT)
def test_undefined_byte_is_a_guaranteed_halt(
    state_test: StateTestFiller,
    pre: Alloc,
    byte_name: str,
) -> None:
    """
    Test an undefined byte halts the frame, so the code behind it never
    runs.

    This is the invariant the deployed idiom relies on, pinned on every
    fork from Berlin up to the last one before the byte was assigned. It
    is **expected to fail if run unscoped on a later fork** -- that is
    the point of the `valid_until` bound, and the violation is asserted
    separately below.
    """
    guard, guard_storage = _guard(pre, byte_name, reached=False)
    probe, probe_storage = _probe(pre, guard, ok=0)

    tx = Transaction(to=probe, state_gas_reservoir=0, sender=pre.fund_eoa())
    state_test(
        pre=pre,
        post={
            guard: Account(storage=guard_storage),
            probe: Account(storage=probe_storage),
        },
        tx=tx,
    )


@pytest.mark.parametrize("byte_name", POST_ASSIGNMENT)
def test_assigned_byte_no_longer_guards(
    state_test: StateTestFiller,
    pre: Alloc,
    byte_name: str,
) -> None:
    """
    Test the same bytecode runs straight through the byte once it is an
    instruction, committing the write it was written to prevent.

    The harm is asserted, not described: the guarded slot moves from its
    sentinel to the forbidden value and the caller's `CALL` reports
    success. Nothing reverts and no gas constant moved.
    """
    guard, guard_storage = _guard(pre, byte_name, reached=True)
    probe, probe_storage = _probe(pre, guard, ok=1)

    tx = Transaction(to=probe, state_gas_reservoir=0, sender=pre.fund_eoa())
    state_test(
        pre=pre,
        post={
            guard: Account(storage=guard_storage),
            probe: Account(storage=probe_storage),
        },
        tx=tx,
    )


@pytest.mark.parametrize(
    "code",
    [
        pytest.param(b"\xfe", id="reserved_invalid_fe"),
        pytest.param(b"\x0c", id="unassigned_0c"),
    ],
)
@pytest.mark.valid_from("Berlin")
def test_bytes_that_never_got_assigned_still_halt(
    state_test: StateTestFiller,
    pre: Alloc,
    code: bytes,
) -> None:
    """
    Test the control: a byte nobody claimed still halts on every fork.

    `0xfe` is the byte the deployed guaranteed-halt idiom actually uses
    and is reserved as `INVALID` in perpetuity; `0x0c` is unassigned on
    every fork from Berlin to Amsterdam. Both must behave on Amsterdam
    exactly as they did on Berlin. This arm is green on all forks, and it
    is the one that fires if a future fork claims either byte -- the
    single event that would break the real deployed population rather
    than a reconstruction of it.
    """
    storage = Storage()
    guard = pre.deploy_contract(
        raw(code)
        + Op.SSTORE(storage.store_next(SENTINEL, "guarded_slot"), FORBIDDEN)
        + Op.STOP,
        storage={0: SENTINEL},
    )
    probe, probe_storage = _probe(pre, guard, ok=0)

    tx = Transaction(to=probe, state_gas_reservoir=0, sender=pre.fund_eoa())
    state_test(
        pre=pre,
        post={
            guard: Account(storage=storage),
            probe: Account(storage=probe_storage),
        },
        tx=tx,
    )


@pytest.mark.valid_from("Berlin")
def test_unreachable_undefined_bytes_leave_the_code_runnable(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Test undefined bytes in unreachable positions do not invalidate code.

    Legacy bytecode is never statically validated: the only thing that
    matters is whether the program counter reaches the byte. Every
    deployed contract depends on this, because solc appends a CBOR
    metadata blob of arbitrary bytes to every runtime, and a jump table
    or packed constant region is arbitrary bytes too. All six
    later-assigned bytes plus `0xfe` and `0x0c` are planted in a region
    the control flow jumps over, and the contract still commits.

    Two rules are pinned at once. First, no code validation: `Ops(...)`
    is resolved lazily, one byte at a time, as the program counter
    arrives (`amsterdam/vm/interpreter.py:440`). Second, jumpdest
    analysis is unaffected by unknown bytes -- `get_valid_jump_destinations`
    advances one byte past anything it cannot decode
    (`amsterdam/vm/runtime.py:55-59`), so the `JUMPDEST` behind the
    region stays reachable. A fork that adopted EOF-style code
    validation (EIP-3670) for legacy code would break both, and would
    break every contract on the chain at once.
    """
    junk = b"\x5f\x1e\x4b\xe6\x80\xe7\x80\xe8\x8e\xfe\x0c"
    storage = Storage()

    # PUSH1 <dest> JUMP <junk> JUMPDEST SSTORE(slot, 1) STOP
    # The destination is 3 (two bytes of PUSH1, one of JUMP) plus the
    # junk region, so the JUMPDEST sits immediately behind it.
    dest = 3 + len(junk)
    code = (
        Op.PUSH1(dest)
        + Op.JUMP
        + raw(junk)
        + Op.JUMPDEST
        + Op.SSTORE(storage.store_next(1, "committed_behind_the_junk"), 1)
        + Op.STOP
    )
    assert bytes(code)[dest] == 0x5B, "the JUMPDEST moved; fix `dest`"

    target = pre.deploy_contract(code)
    probe, probe_storage = _probe(pre, target, ok=1)

    tx = Transaction(to=probe, state_gas_reservoir=0, sender=pre.fund_eoa())
    state_test(
        pre=pre,
        post={
            target: Account(storage=storage),
            probe: Account(storage=probe_storage),
        },
        tx=tx,
    )
