"""
Measurement instruments for invariant classes 8, 9 and 11, not corpus tests.

**Their FAILURES ARE THE MEASUREMENT.** Every expectation below is
deliberately `0` (or a deliberately wrong budget outcome), so the
`KeyValueMismatchError` prints the real value: `want 0x0, got 0x<actual>`.
Do not add this directory to a corpus pass/fail gate.

Reproduce (from engine/eels), one fork at a time:

    ./.venv/bin/fill ../../wave1/instruments --from <Fork> --until <Fork> \
        -k "refund_probe and state_test" --output /tmp/p -q --tb=line \
        -p no:cacheprovider

Note on summary parsing: with `-k`, an all-failed run prints
"N failed, M deselected in Xs" -- no "passed" token. Check the exit code
and read the summary line, never grep for FAILED alone.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Block,
    BlockchainTestFiller,
    Bytecode,
    Fork,
    GasConsumer,
    Op,
    StateTestFiller,
    Storage,
    Transaction,
    WhileGas,
)

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

# ---------------------------------------------------------------------------
# Class 8: the refund cap  min(gas_used_before_refund // D, refund_counter)
# ---------------------------------------------------------------------------
# Two senders run bytecode of *identical* gas cost over identical storage.
# One clears its slots (1 -> 0, refund granted); the other merely moves
# them to another non-zero value (1 -> 2, same charge, no refund). Their
# post-transaction balances therefore differ by exactly the refund, which
# cancels every pricing term the two have in common.

P8_PRICE = 10**9
P8_GAS = 1_000_000
P8_SLOTS = 50


def _slot_writer(n: int, value: int) -> Bytecode:
    """`SSTORE(k, value)` for k in 1..n, with identical cost for any value."""
    code = Bytecode()
    for k in range(1, n + 1):
        # PUSH1 value; PUSH1 k; SSTORE -- fixed width, so the two variants
        # cost the same to the gas.
        code += Op.PUSH1[value] + Op.PUSH1[k] + Op.SSTORE
    return code


def _p8_prober(kind: str, sa: object, sb: object, slot: int) -> Bytecode:
    """Store the measured quantity, in gas units, in `slot`."""
    la = Op.DIV(Op.BALANCE(sa), P8_PRICE)
    lb = Op.DIV(Op.BALANCE(sb), P8_PRICE)
    used = Op.SUB(P8_GAS, lb)
    refund = Op.SUB(la, lb)
    expr = {
        "used": used,
        "refund": refund,
        "ratio": Op.DIV(used, refund),
        "counter_refund": refund,
    }[kind]
    return Op.SSTORE(slot, expr) + Op.STOP


@pytest.mark.parametrize("kind", ["used", "refund", "ratio"])
@pytest.mark.valid_from("Berlin")
def test_refund_probe_cap_bound(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    kind: str,
) -> None:
    """Probe: 50 clears, so the cap binds. Measures used, refund, ratio."""
    slots = {k: 1 for k in range(1, P8_SLOTS + 1)}
    clearer = pre.deploy_contract(
        _slot_writer(P8_SLOTS, 0) + Op.STOP, storage=slots
    )
    updater = pre.deploy_contract(
        _slot_writer(P8_SLOTS, 2) + Op.STOP, storage=slots
    )
    sa = pre.fund_eoa(amount=P8_GAS * P8_PRICE)
    sb = pre.fund_eoa(amount=P8_GAS * P8_PRICE)
    st = Storage()
    prober = pre.deploy_contract(
        _p8_prober(kind, sa, sb, st.store_next(0, kind))
    )
    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[
                    Transaction(
                        ty=0,
                        sender=sa,
                        to=clearer,
                        gas_limit=P8_GAS,
                        gas_price=P8_PRICE,
                    ),
                    Transaction(
                        ty=0,
                        sender=sb,
                        to=updater,
                        gas_limit=P8_GAS,
                        gas_price=P8_PRICE,
                    ),
                    Transaction(
                        ty=0,
                        sender=pre.fund_eoa(),
                        to=prober,
                        gas_limit=1_000_000,
                        gas_price=P8_PRICE,
                    ),
                ]
            )
        ],
        post={prober: Account(storage=st)},
    )


P8_BURN_OFFSET = 122_304  # ~40,000 gas of memory expansion.


@pytest.mark.parametrize("clears", [1, 2])
@pytest.mark.valid_from("Berlin")
def test_refund_probe_counter_bound(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    clears: int,
) -> None:
    """
    Probe: few clears inside an expensive transaction, so the *counter*
    is the smaller term of the `min` and the refund equals it exactly.

    A literal memory expansion inflates `gas_used_before_refund` so that
    `used // D` sits above the counter on every fork.
    """
    slots = {k: 1 for k in range(1, clears + 1)}
    burn = Op.MSTORE(P8_BURN_OFFSET, 0)
    clearer = pre.deploy_contract(
        _slot_writer(clears, 0) + burn + Op.STOP, storage=slots
    )
    updater = pre.deploy_contract(
        _slot_writer(clears, 2) + burn + Op.STOP, storage=slots
    )
    sa = pre.fund_eoa(amount=P8_GAS * P8_PRICE)
    sb = pre.fund_eoa(amount=P8_GAS * P8_PRICE)
    st = Storage()
    prober = pre.deploy_contract(
        _p8_prober("refund", sa, sb, st.store_next(0, "counter_refund"))
    )
    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[
                    Transaction(
                        ty=0,
                        sender=sa,
                        to=clearer,
                        gas_limit=P8_GAS,
                        gas_price=P8_PRICE,
                    ),
                    Transaction(
                        ty=0,
                        sender=sb,
                        to=updater,
                        gas_limit=P8_GAS,
                        gas_price=P8_PRICE,
                    ),
                    Transaction(
                        ty=0,
                        sender=pre.fund_eoa(),
                        to=prober,
                        gas_limit=1_000_000,
                        gas_price=P8_PRICE,
                    ),
                ]
            )
        ],
        post={prober: Account(storage=st)},
    )


# ---------------------------------------------------------------------------
# Class 9: does a frame's own clear change what the frame can afford?
# ---------------------------------------------------------------------------
# The child sets a slot, clears it, then burns a fixed `JUMPDEST` sled.
# Pre-8037 the clear only moves the refund *counter*, so the budget must
# cover the full set cost. From EIP-8037 the clear returns the state-gas
# spill to `gas_left`, so a smaller budget suffices.

P9_BURN = 15_000  # JUMPDEST = 1 gas on every fork Frontier..Amsterdam.

P9_LADDER = [
    20_000,
    30_000,
    35_000,
    36_000,
    37_000,
    37_200,
    37_300,
    37_400,
    37_500,
    38_000,
    40_000,
    100_000,
    105_000,
    110_000,
    110_100,
    110_200,
    112_000,
    115_000,
    118_000,
    120_000,
    123_000,
    125_000,
    125_200,
    125_500,
    126_000,
    130_000,
]


def _p9_child(burn: int) -> Bytecode:
    """Create a slot, clear it, then do `burn` gas of further work."""
    return (
        Op.SSTORE(0x01, 1) + Op.SSTORE(0x01, 0) + Op.JUMPDEST * burn + Op.STOP
    )


def _tolerant(child: object, budget: int, slot: int) -> Bytecode:
    """Call `child` with a literal budget; record 2 on success, 1 on fail."""
    return (
        Op.SSTORE(slot, Op.ADD(Op.CALL(gas=budget, address=child), 1))
        + Op.STOP
    )


@pytest.mark.parametrize("budget", P9_LADDER)
@pytest.mark.valid_from("Berlin")
def test_refund_probe_set_clear_budget(
    state_test: StateTestFiller,
    pre: Alloc,
    budget: int,
) -> None:
    """Probe: smallest literal budget in which set+clear+15,000 completes."""
    child = pre.deploy_contract(_p9_child(P9_BURN))
    st = Storage()
    caller = pre.deploy_contract(
        _tolerant(child, budget, st.store_next(2, "child_ok"))
    )
    tx = Transaction(
        to=caller, sender=pre.fund_eoa(), state_gas_reservoir=0
    )
    state_test(pre=pre, post={caller: Account(storage=st)}, tx=tx)


# ---------------------------------------------------------------------------
# Class 11: how much gas does a tolerant caller hold after the child ends?
# ---------------------------------------------------------------------------
# The caller forwards `GAS` (the deployed `call(gas(), ...)` shape), so it
# retains exactly the 63/64 remainder. The child then ends four different
# ways and the caller returns its own remaining gas for measurement.

P11_GRANT = 200_000


def _p11_child(mode: str, fork: Fork) -> Bytecode:
    """The four endings a child can have."""
    if mode == "stop":
        return Op.STOP
    if mode == "revert":
        return Op.REVERT(0, 0)
    if mode == "invalid":
        return Op.INVALID
    if mode == "oog":
        return GasConsumer.out_of_gas(fork) + Op.STOP
    raise ValueError(mode)


def _p11_mid(child: object) -> Bytecode:
    """Forward everything, tolerate failure, return the gas left over."""
    return (
        Op.POP(Op.CALL(gas=Op.GAS, address=child))
        + Op.MSTORE(0, Op.GAS)
        + Op.RETURN(0, 32)
    )


P11_RESERVE = 4_000


def _p11_drained_child(ending: str, fork: Fork) -> Bytecode:
    """
    Set a slot, burn almost everything, clear the slot, then end.

    The clear is what makes this interesting: pre-8037 it only moves the
    refund counter, so the frame ends holding ~`P11_RESERVE`; from
    EIP-8037 it returns the state-gas spill to `gas_left`, so the frame
    ends holding ~97,920 more than that.
    """
    return (
        Op.SSTORE(0x01, 1)
        + WhileGas(body=Op.JUMPDEST, fork=fork, extra_gas=P11_RESERVE)
        + Op.SSTORE(0x01, 0)
        + (Op.REVERT(0, 0) if ending == "revert" else Op.INVALID)
    )


def _p11_unrepaid_child(ending: str, fork: Fork) -> Bytecode:
    """
    Set a slot, burn almost everything, then end -- with NO clear.

    The spill is therefore still outstanding when the frame ends, so a
    revert's gas return comes from `restore_state_gas` and nothing else.
    The drained child above cannot isolate that: its clear has already
    moved the spill into `gas_left` via `credit_state_gas_refund`.
    """
    return (
        Op.SSTORE(0x01, 1)
        + WhileGas(body=Op.JUMPDEST, fork=fork, extra_gas=P11_RESERVE)
        + (Op.REVERT(0, 0) if ending == "revert" else Op.INVALID)
    )


@pytest.mark.parametrize("ending", ["revert", "invalid"])
@pytest.mark.valid_from("Berlin")
def test_refund_probe_retained_after_unrepaid_child(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    ending: str,
) -> None:
    """Probe: the caller's gas after a child reverts holding its spill."""
    child = pre.deploy_contract(_p11_unrepaid_child(ending, fork))
    mid = pre.deploy_contract(_p11_mid(child))
    st = Storage()
    outer = pre.deploy_contract(
        Op.POP(
            Op.CALL(gas=P11_GRANT, address=mid, ret_offset=0, ret_size=32)
        )
        + Op.SSTORE(
            st.store_next(0, f"retained_unrepaid_{ending}"), Op.MLOAD(0)
        )
        + Op.STOP
    )
    tx = Transaction(to=outer, sender=pre.fund_eoa(), state_gas_reservoir=0)
    state_test(pre=pre, post={outer: Account(storage=st)}, tx=tx)


@pytest.mark.parametrize("ending", ["revert", "invalid"])
@pytest.mark.valid_from("Berlin")
def test_refund_probe_retained_after_drained_child(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    ending: str,
) -> None:
    """Probe: the caller's gas after a drained child reverts or halts."""
    child = pre.deploy_contract(_p11_drained_child(ending, fork))
    mid = pre.deploy_contract(_p11_mid(child))
    st = Storage()
    outer = pre.deploy_contract(
        Op.POP(
            Op.CALL(gas=P11_GRANT, address=mid, ret_offset=0, ret_size=32)
        )
        + Op.SSTORE(
            st.store_next(0, f"retained_drained_{ending}"), Op.MLOAD(0)
        )
        + Op.STOP
    )
    tx = Transaction(to=outer, sender=pre.fund_eoa(), state_gas_reservoir=0)
    state_test(pre=pre, post={outer: Account(storage=st)}, tx=tx)


@pytest.mark.parametrize("mode", ["stop", "revert", "invalid", "oog"])
@pytest.mark.valid_from("Berlin")
def test_refund_probe_retained_after_child(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    mode: str,
) -> None:
    """Probe: the caller's gas after a child that stops/reverts/halts."""
    child = pre.deploy_contract(_p11_child(mode, fork))
    mid = pre.deploy_contract(_p11_mid(child))
    st = Storage()
    outer = pre.deploy_contract(
        Op.POP(
            Op.CALL(gas=P11_GRANT, address=mid, ret_offset=0, ret_size=32)
        )
        + Op.SSTORE(st.store_next(0, f"retained_after_{mode}"), Op.MLOAD(0))
        + Op.STOP
    )
    tx = Transaction(to=outer, sender=pre.fund_eoa(), state_gas_reservoir=0)
    state_test(pre=pre, post={outer: Account(storage=st)}, tx=tx)
