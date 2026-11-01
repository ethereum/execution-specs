"""
Candidate class, gas dimension: the halt on an undefined opcode byte
forfeits the caller's entire grant, and assigning the byte turns that
into a near-total refund.

Class #11 (`tests/halt_vs_revert/`) pins halt-versus-revert gas return
with `INVALID` as the trigger, and `INVALID` is `0xfe`, reserved
forever. **This is the same rule with a trigger that moves.** A caller
that caps a sub-call precisely because the callee may halt is budgeting
against a loss of the whole cap; once the byte becomes an instruction the
loss drops to almost nothing, in the same deployed bytecode, with no gas
constant changed.

Both directions matter and they break different populations:

* a **capability probe** that reads "the child consumed everything" as
  "not supported" starts reading "supported" (class #12's inversion,
  reached here through semantics rather than a reprice);
* a **metering or reimbursement** caller that charges a fee derived from
  what the sub-call consumed starts charging ~1/16th of it.

**Mechanism** (CHECKED, pinned Amsterdam commit):

```text
except ExceptionalHalt as error:
        restore_state_gas(evm.gas_meter)
        forfeit_remaining_gas(evm.gas_meter)   amsterdam/vm/interpreter.py:455-457
forfeit_remaining_gas: gas_meter.gas_left = ExecutionGas(Uint(0))
                                               amsterdam/vm/gas.py
except Revert as error:
        restore_state_gas(evm.gas_meter)       -- and NOT forfeit
                                               amsterdam/vm/interpreter.py:461-465
```

So an undefined byte burns the grant through exactly the same path
`0xfe` does, and **measurably so**. With a 400,000-gas grant and a
*fresh slot* behind the byte, the caller's consumption quantised to 1024
(CHECKED, `test_undefined_byte_cost`) reads 393 units -- the whole grant
plus the `CALL`'s own charge -- on every fork where the byte is
undefined, identically for `0xfe`, for the never-assigned `0x0c`, and
for all six later-assigned bytes before their assignment fork. After
assignment the same bytecode reads 24 units (Shanghai..Osaka) or 110
units (Amsterdam, where a fresh slot is ~110,026). A 16x swing in what
the caller pays, triggered by nothing but a byte becoming valid. The
Amsterdam figure is an independent re-measurement of class #1's
fresh-slot floor and agrees with it.

**No gas number is asserted here.** The instrument is a boolean over a
grant this test chooses itself: `consumed > grant/2` on the halting arm,
`consumed < grant/8` on the executing arm. Measured against the shape
this file actually uses -- a *warm* `1 -> 2` update behind the byte, so
the child's own work is cheap on every fork (CHECKED):

```text
                       halting arm        executing arm
Berlin..Osaka          402,634            7,642 .. 7,648
Amsterdam              403,034            15,142 .. 15,197
thresholds             > 200,000          < 50,000
slack                  2.01x              3.29x (Amsterdam), 6.5x (earlier)
```

so neither arm sits on a cliff a reprice could nudge it over.
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

# A grant large enough that the halt's forfeit dwarfs anything the child
# could legitimately spend, and small enough to sit well inside the
# transaction limit after the 63/64 retention.
GRANT = 400_000
TX_GAS = 3_000_000

# byte sequence -> stack items the frame is given before the byte.
#   decode_single(0x80) = 17   -> DUPN/SWAPN index 17   (vm/stack.py:25)
#   decode_pair(0x8E)  = (1,2) -> EXCHANGE(1, 2)        (vm/stack.py:55)
# EXCHANGE gets 15 rather than its minimum 3, because its immediate byte
# 0x8E is itself `DUP15`: at depth 3 the `undefined-is-a-noop` mutation
# would be survived on an unrelated stack underflow. See the sibling
# archetype's note.
BYTES: dict[str, tuple[bytes, int]] = {
    "push0_5f": (b"\x5f", 0),
    "clz_1e": (b"\x1e", 1),
    "slotnum_4b": (b"\x4b", 0),
    "dupn_e6": (b"\xe6\x80", 17),
    "swapn_e7": (b"\xe7\x80", 18),
    "exchange_e8": (b"\xe8\x8e", 15),
}

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
] + [
    # Never assigned on any fork in range, so it carries the invariant
    # on all of them. This is the arm that stays green, and the one that
    # would fire if a fork made an exceptional halt return gas.
    pytest.param(
        "unassigned_0c", id="unassigned_0c", marks=pytest.mark.valid_from("Berlin")
    )
]

POST_ASSIGNMENT = [
    pytest.param(
        name, id=name, marks=pytest.mark.valid_from(ASSIGNED_AT[name][0])
    )
    for name in BYTES
]

ALL_BYTES: dict[str, tuple[bytes, int]] = dict(
    BYTES, unassigned_0c=(b"\x0c", 0)
)


def raw(code: bytes) -> Bytecode:
    """Emit literal bytes, with no stack bookkeeping claimed for them."""
    return Bytecode(code, popped_stack_items=0, pushed_stack_items=0)


def _child(pre: Alloc, byte_name: str, reached: bool):
    """
    A child that reaches the byte, with a cheap committed effect behind
    it.

    The effect is a **warm update** (1 -> 2) rather than a fresh slot, so
    the executing arm's consumption is a few thousand gas on every fork
    instead of the ~110,026 a fresh slot costs at EIP-8037. That keeps
    the `consumed < grant/8` threshold off any cliff: the point of this
    test is the forfeit, not the cost of the child's work.
    """
    code, pad = ALL_BYTES[byte_name]
    storage = Storage()
    address = pre.deploy_contract(
        sum((Op.PUSH1(1) for _ in range(pad)), Bytecode())
        + raw(code)
        + Op.SSTORE(storage.store_next(2 if reached else 1, "slot"), 2)
        + Op.STOP,
        storage={0: 1},
    )
    return address, storage


def _meter(pre: Alloc, child, ok: int, burned: int):
    """
    A caller that caps the sub-call and measures what it cost.

    `GAS` before and after, differenced, then compared with a fraction of
    the grant -- so the committed effect is a boolean, not a gas figure
    (SCHEMA §4.1).
    """
    storage = Storage()
    address = pre.deploy_contract(
        Op.MSTORE(0x00, Op.GAS)
        + Op.MSTORE(0x20, Op.CALL(gas=GRANT, address=child))
        + Op.MSTORE(0x40, Op.GAS)
        + Op.MSTORE(0x60, Op.SUB(Op.MLOAD(0x00), Op.MLOAD(0x40)))
        + Op.SSTORE(storage.store_next(ok, "call_succeeded"), Op.MLOAD(0x20))
        + Op.SSTORE(
            storage.store_next(burned, "consumed_over_half_the_grant"),
            Op.GT(Op.MLOAD(0x60), GRANT // 2),
        )
        + Op.SSTORE(
            storage.store_next(1 - burned, "consumed_under_an_eighth"),
            Op.LT(Op.MLOAD(0x60), GRANT // 8),
        )
        + Op.STOP
    )
    return address, storage


@pytest.mark.parametrize("byte_name", PRE_ASSIGNMENT)
def test_halt_on_an_undefined_byte_forfeits_the_grant(
    state_test: StateTestFiller,
    pre: Alloc,
    byte_name: str,
) -> None:
    """
    Test the whole grant is destroyed when the child reaches an undefined
    byte.

    Pinned on every fork from Berlin to the last one before the byte was
    assigned. It **would fail if run unscoped on a later fork**, which is
    the invariant being fork-scoped rather than a defect; the violation
    is asserted separately below.
    """
    child, child_storage = _child(pre, byte_name, reached=False)
    meter, meter_storage = _meter(pre, child, ok=0, burned=1)

    tx = Transaction(
        to=meter,
        gas_limit=TX_GAS,
        state_gas_reservoir=0,
        sender=pre.fund_eoa(),
    )
    state_test(
        pre=pre,
        post={
            child: Account(storage=child_storage),
            meter: Account(storage=meter_storage),
        },
        tx=tx,
    )


@pytest.mark.parametrize("byte_name", POST_ASSIGNMENT)
def test_assigned_byte_hands_the_grant_back(
    state_test: StateTestFiller,
    pre: Alloc,
    byte_name: str,
) -> None:
    """
    Test the same capped sub-call returns almost all of its grant once
    the byte is an instruction.

    The caller's own accounting inverts without anything reverting: a
    probe reading "consumed everything" as a failure signal now reads
    success, and a reimbursement derived from the consumption under-bills
    by an order of magnitude.
    """
    child, child_storage = _child(pre, byte_name, reached=True)
    meter, meter_storage = _meter(pre, child, ok=1, burned=0)

    tx = Transaction(
        to=meter,
        gas_limit=TX_GAS,
        state_gas_reservoir=0,
        sender=pre.fund_eoa(),
    )
    state_test(
        pre=pre,
        post={
            child: Account(storage=child_storage),
            meter: Account(storage=meter_storage),
        },
        tx=tx,
    )
