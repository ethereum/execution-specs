"""
Measurement instrument, not a corpus test.

Question: for each opcode byte that was undefined and later became a valid
instruction, on which forks does a frame that reaches the byte halt, and
how much of a caller's grant does that halt destroy?

Two instruments, read differently.

`test_undefined_byte_flip` is parametrised over `executed` in {0, 1} and
**its passing param is the answer**: exactly one of the two passes per
(fork, byte), and which one says whether the byte is an instruction on
that fork. Three observables move together and all three are asserted,
so a half-flip (e.g. the byte becomes valid but underflows the stack)
cannot be mistaken for either answer:

  reached   1 if the SSTORE sitting *after* the byte ran
  ok        the caller's CALL status word
  burned    1 if the child consumed more than half the grant

`test_undefined_byte_cost` **always fails on purpose**: it asserts
`used_k == 0`, so the mismatch prints `(gas before the call - gas after)
// 1024` for every fork. That is the halt-versus-return figure in gas.

`burned` is the instrument the corpus wants for the gas dimension: a
boolean over a self-chosen grant, not a pinned gas number. An exceptional
halt forfeits the whole grant; a frame that completes hands the unspent
remainder back.

Do not add this directory to a corpus gate.

Reproduce (from tests/deployed_idioms/):
  python3 tools/locked_fill.py \
      /home/devops/toni/datanalysis/eip-8037/expansion/instruments \
      --from Berlin --until Amsterdam \
      -k "undefined_byte and state_test and not blockchain" \
      --output /tmp/uop -q --tb=line -rA -p no:cacheprovider
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

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

# byte sequence -> stack items the instruction needs once it is valid.
# The pad is what lets the post-assignment arm run *past* the byte
# instead of tripping a stack underflow, which would look exactly like
# the byte still halting and would silently hide the flip.
#
# DUPN/SWAPN/EXCHANGE carry one immediate byte (EIP-8024).
#   decode_single(0x80) = (128 + 145) % 256 = 17   -> DUPN/SWAPN index 17
#   decode_pair(0x8E):   k = 0x8E ^ 143 = 1 -> (1, 2)  -> EXCHANGE(1, 2)
BYTES: dict[str, tuple[bytes, int]] = {
    "clz_1e": (b"\x1e", 1),
    "slotnum_4b": (b"\x4b", 0),
    "push0_5f": (b"\x5f", 0),
    "dupn_e6": (b"\xe6\x80", 17),
    "swapn_e7": (b"\xe7\x80", 18),
    "exchange_e8": (b"\xe8\x8e", 3),
    # Controls. 0xfe is reserved as INVALID forever, so it must never
    # flip. 0x0c is undefined on every fork in range.
    "invalid_fe": (b"\xfe", 0),
    "still_undefined_0c": (b"\x0c", 0),
}

GRANT = 400_000
TX_GAS = 3_000_000


def raw(code: bytes) -> Bytecode:
    """Emit literal bytes, with no stack bookkeeping claimed for them."""
    return Bytecode(code, popped_stack_items=0, pushed_stack_items=0)


def _guard(
    pre: Alloc, byte_name: str, reached: int, pad_items: int | None = None
) -> tuple:
    """A frame that reaches the byte, with an SSTORE behind it."""
    code, pad = BYTES[byte_name]
    if pad_items is not None:
        pad = pad_items
    storage = Storage()
    address = pre.deploy_contract(
        sum((Op.PUSH1(1) for _ in range(pad)), Bytecode())
        + raw(code)
        + Op.SSTORE(storage.store_next(reached, "reached"), 1)
        + Op.STOP
    )
    return address, storage


@pytest.mark.parametrize("executed", [0, 1])
@pytest.mark.parametrize("byte_name", list(BYTES))
@pytest.mark.valid_from("Berlin")
def test_undefined_byte_flip(
    state_test: StateTestFiller,
    pre: Alloc,
    byte_name: str,
    executed: int,
) -> None:
    """Probe: is the byte an instruction on this fork? Passing param wins."""
    guard, guard_storage = _guard(pre, byte_name, executed)

    caller_storage = Storage()
    caller = pre.deploy_contract(
        Op.MSTORE(0x00, Op.GAS)
        + Op.MSTORE(0x20, Op.CALL(gas=GRANT, address=guard))
        + Op.MSTORE(0x40, Op.GAS)
        + Op.MSTORE(0x60, Op.SUB(Op.MLOAD(0x00), Op.MLOAD(0x40)))
        + Op.SSTORE(caller_storage.store_next(executed, "ok"), Op.MLOAD(0x20))
        + Op.SSTORE(
            caller_storage.store_next(
                1 - executed, "burned_over_half_the_grant"
            ),
            Op.GT(Op.MLOAD(0x60), GRANT // 2),
        )
        + Op.STOP
    )

    tx = Transaction(
        to=caller,
        gas_limit=TX_GAS,
        state_gas_reservoir=0,
        sender=pre.fund_eoa(),
    )
    state_test(
        pre=pre,
        post={
            guard: Account(storage=guard_storage),
            caller: Account(storage=caller_storage),
        },
        tx=tx,
    )


@pytest.mark.parametrize("byte_name", list(BYTES))
@pytest.mark.valid_from("Berlin")
def test_undefined_byte_cost(
    state_test: StateTestFiller,
    pre: Alloc,
    byte_name: str,
) -> None:
    """Probe: always fails, printing the caller's gas consumption // 1024."""
    guard, _ = _guard(pre, byte_name, 0)

    caller_storage = Storage()
    caller = pre.deploy_contract(
        Op.MSTORE(0x00, Op.GAS)
        + Op.POP(Op.CALL(gas=GRANT, address=guard))
        + Op.MSTORE(0x40, Op.GAS)
        + Op.SSTORE(
            caller_storage.store_next(0, "used_k"),
            Op.DIV(Op.SUB(Op.MLOAD(0x00), Op.MLOAD(0x40)), 1024),
        )
        + Op.STOP
    )

    tx = Transaction(
        to=caller,
        gas_limit=TX_GAS,
        state_gas_reservoir=0,
        sender=pre.fund_eoa(),
    )
    state_test(
        pre=pre,
        post={caller: Account(storage=caller_storage)},
        tx=tx,
    )


@pytest.mark.parametrize("executed", [0, 1])
@pytest.mark.parametrize("pad_items", [0, 1, 2, 3, 16, 17, 18])
@pytest.mark.parametrize("byte_name", list(BYTES))
@pytest.mark.valid_from("Berlin")
def test_undefined_byte_stack_depth(
    state_test: StateTestFiller,
    pre: Alloc,
    byte_name: str,
    pad_items: int,
    executed: int,
) -> None:
    """
    Probe: at which stack depth does an assigned byte stop halting?

    Once the byte is an instruction it can still halt -- on stack
    underflow. That is accidental protection, not the invariant, and it
    means EIP-8024's three bytes break a guard only at sufficient depth.
    The passing param names the real answer per (fork, byte, depth).
    """
    guard, guard_storage = _guard(pre, byte_name, executed, pad_items)

    caller_storage = Storage()
    caller = pre.deploy_contract(
        Op.SSTORE(
            caller_storage.store_next(executed, "ok"),
            Op.CALL(gas=GRANT, address=guard),
        )
        + Op.STOP
    )
    tx = Transaction(
        to=caller,
        gas_limit=TX_GAS,
        state_gas_reservoir=0,
        sender=pre.fund_eoa(),
    )
    state_test(
        pre=pre,
        post={
            guard: Account(storage=guard_storage),
            caller: Account(storage=caller_storage),
        },
        tx=tx,
    )


@pytest.mark.parametrize("byte_name", list(BYTES))
@pytest.mark.valid_from("Berlin")
def test_undefined_byte_warm_cost(
    state_test: StateTestFiller,
    pre: Alloc,
    byte_name: str,
) -> None:
    """
    Probe: always fails, printing the caller's exact gas consumption when
    the child's committed effect behind the byte is a WARM update (1->2)
    rather than a fresh slot. This is the shape
    `undefined_opcode_gas_forfeit` uses, and the figure is what its
    `consumed < grant/8` threshold has to clear.
    """
    code, pad = BYTES[byte_name]
    child = pre.deploy_contract(
        sum((Op.PUSH1(1) for _ in range(pad)), Bytecode())
        + raw(code)
        + Op.SSTORE(0, 2)
        + Op.STOP,
        storage={0: 1},
    )
    caller_storage = Storage()
    caller = pre.deploy_contract(
        Op.MSTORE(0x00, Op.GAS)
        + Op.POP(Op.CALL(gas=GRANT, address=child))
        + Op.MSTORE(0x40, Op.GAS)
        + Op.SSTORE(
            caller_storage.store_next(0, "used_exact"),
            Op.SUB(Op.MLOAD(0x00), Op.MLOAD(0x40)),
        )
        + Op.STOP
    )
    tx = Transaction(
        to=caller,
        gas_limit=TX_GAS,
        state_gas_reservoir=0,
        sender=pre.fund_eoa(),
    )
    state_test(
        pre=pre, post={caller: Account(storage=caller_storage)}, tx=tx
    )
