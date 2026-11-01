"""
Measurement instrument, not a corpus test (class #16, reservoir allocation).

Its FAILURES ARE THE MEASUREMENT. A failing param is a budget too small.

`test_cls16_child_literal`   locates the smallest forwarded execution-gas
                             literal in which a child can create one fresh
                             slot, as a function of the reservoir it is
                             handed.
`test_cls16_drained`         does the same after an earlier child has spent
                             the reservoir.
`test_cls16_retained_mult`   locates the transaction gas limit at which the
                             63/64 rule retains enough execution gas for the
                             parent to create one fresh slot itself.

Reproduce (from engine/eels):
  ./.venv/bin/fill ../../wave1/instruments --from Amsterdam \
      --until Amsterdam -k "cls16 and state_test" --output /tmp/p16 -q \
      --tb=line -p no:cacheprovider
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Fork,
    GasConsumer,
    Op,
    StateTestFiller,
    Storage,
    Transaction,
)

# STATE_BYTES_PER_STORAGE_SET(64) * COST_PER_STATE_BYTE(1530)
ONE_SLOT_STATE_GAS = 97_920


@pytest.mark.parametrize("reservoir", [0, ONE_SLOT_STATE_GAS])
@pytest.mark.parametrize(
    "literal", [12_100, 12_110, 12_200, 13_000, 13_630, 13_700, 20_000]
)
@pytest.mark.valid_from("EIP8037")
def test_cls16_child_literal(
    state_test: StateTestFiller, pre: Alloc, reservoir: int, literal: int
) -> None:
    """Probe."""
    cs = Storage()
    child = pre.deploy_contract(
        Op.SSTORE(cs.store_next(1, "child_wrote"), 1) + Op.STOP
    )
    caller = pre.deploy_contract(
        Op.POP(Op.CALL(gas=literal, address=child)) + Op.STOP
    )
    # No explicit gas_limit: EIP-8037 defines the reservoir as the part of
    # `tx.gas` above TX_MAX_GAS_LIMIT (= 16,777,216), so the harness must be
    # allowed to set `tx.gas = cap + reservoir` itself.
    tx = Transaction(
        to=caller,
        state_gas_reservoir=reservoir,
        sender=pre.fund_eoa(),
    )
    state_test(pre=pre, post={child: Account(storage=cs)}, tx=tx)


@pytest.mark.parametrize("drained", [False, True])
@pytest.mark.parametrize("literal", [12_200, 13_630, 20_000, 110_040])
@pytest.mark.valid_from("EIP8037")
def test_cls16_drained(
    state_test: StateTestFiller, pre: Alloc, drained: bool, literal: int
) -> None:
    """Probe: can a second child still create a slot?"""
    drain_code = Op.SSTORE(0x20, 1) + Op.STOP if drained else Op.STOP
    drain = pre.deploy_contract(drain_code)
    es = Storage()
    epi = pre.deploy_contract(
        Op.SSTORE(es.store_next(1, "epilogue_wrote"), 1) + Op.STOP
    )
    caller = pre.deploy_contract(
        Op.POP(Op.CALL(gas=20_000, address=drain))
        + Op.POP(Op.CALL(gas=literal, address=epi))
        + Op.STOP
    )
    tx = Transaction(
        to=caller,
        state_gas_reservoir=ONE_SLOT_STATE_GAS,
        sender=pre.fund_eoa(),
    )
    state_test(pre=pre, post={epi: Account(storage=es)}, tx=tx)


@pytest.mark.parametrize(
    "gas_limit",
    [6_949_784, 7_041_280, 7_059_683, 7_059_811, 7_059_812, 7_060_000],
)
@pytest.mark.valid_from("EIP8037")
def test_cls16_retained_mult(
    state_test: StateTestFiller, pre: Alloc, fork: Fork, gas_limit: int
) -> None:
    """Probe: does the retained 1/64 of execution gas cover one slot?"""
    burner = pre.deploy_contract(GasConsumer(gas=None, fork=fork))
    s = Storage()
    caller = pre.deploy_contract(
        Op.POP(Op.CALL(gas=Op.GAS, address=burner))
        + Op.SSTORE(s.store_next(1, "parent_wrote"), 1)
        + Op.STOP
    )
    tx = Transaction(
        to=caller,
        gas_limit=gas_limit,
        state_gas_reservoir=0,
        sender=pre.fund_eoa(),
    )
    state_test(pre=pre, post={caller: Account(storage=s)}, tx=tx)
