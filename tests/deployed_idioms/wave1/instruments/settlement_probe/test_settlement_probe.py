"""
Measurement instrument for invariant classes 13/14/15. NOT a corpus test.

Unusually for this directory these probes are expected to PASS; the
measurement is the JSON the conftest writes, not the verdict, because
the instrument reports the settlement quantities directly instead of
inferring them from which parameters failed.

`SETTLEMENT_PROBE_LOG` is required -- without it the conftest patches
nothing and these are just transactions:

  cd /home/devops/toni/datanalysis/eip-8037/engine/eels
  rm -f /tmp/sp.jsonl
  SETTLEMENT_PROBE_LOG=/tmp/sp.jsonl ./.venv/bin/fill \
      ../../wave1/instruments/settlement_probe \
      --from Amsterdam --until Amsterdam -k state_test \
      --output /tmp/sp-out -q --tb=no -p no:cacheprovider

The `-k state_test` keeps one settlement record per probe instead of one
per fixture format.

To measure a *corpus* test's exact shape rather than a probe's, copy the
test file in here so this conftest instruments it, run, then delete the
copy. That is how the figures pinned in `tests/state_gas_clamp/` and
`tests/calldata_floor_refund/` were taken.

**Take `tools/.mutate.lock` around any measurement run.** `tools/mutate.py`
edits the shared EELS tree, and a `fill` that lands inside another
agent's mutation window reads mutated gas numbers while looking like a
clean measurement. That happened once during this work: a shape that is
27,212 on a pristine tree measured 30,112.
"""

import pytest
from execution_testing import (
    Alloc,
    AuthorizationTuple,
    Op,
    StateTestFiller,
    Transaction,
)

K1 = 0x01
K2 = 0x02
K3 = 0x03


# --------------------------------------------------------------------------
# Class 14: is `state_gas_used` ever negative, i.e. does `max(0, ...)` ever
# have anything to clamp?
# --------------------------------------------------------------------------


@pytest.mark.valid_from("EIP8037")
def test_p14_clear_preexisting_only(state_test: StateTestFiller, pre: Alloc) -> None:
    """Clear three pre-existing non-zero slots, create nothing."""
    target = pre.deploy_contract(
        Op.SSTORE(K1, 0) + Op.SSTORE(K2, 0) + Op.SSTORE(K3, 0) + Op.STOP,
        storage={K1: 1, K2: 1, K3: 1},
    )
    state_test(
        pre=pre,
        post={},
        tx=Transaction(to=target, gas_limit=1_000_000, sender=pre.fund_eoa()),
    )


@pytest.mark.valid_from("EIP8037")
def test_p14_inframe_set_then_clear(state_test: StateTestFiller, pre: Alloc) -> None:
    """Create a slot then clear it in the same frame (reservoir 0)."""
    target = pre.deploy_contract(Op.SSTORE(K1, 1) + Op.SSTORE(K1, 0) + Op.STOP)
    state_test(
        pre=pre,
        post={},
        tx=Transaction(
            to=target,
            gas_limit=1_000_000,
            state_gas_reservoir=0,
            sender=pre.fund_eoa(),
        ),
    )


@pytest.mark.valid_from("EIP8037")
def test_p14_child_clears_parent_slot(state_test: StateTestFiller, pre: Alloc) -> None:
    """Parent creates a slot; a DELEGATECALL child clears it."""
    clearer = pre.deploy_contract(Op.SSTORE(K1, 0) + Op.STOP)
    parent = pre.deploy_contract(
        Op.SSTORE(K1, 1) + Op.POP(Op.DELEGATECALL(gas=Op.GAS, address=clearer)) + Op.STOP
    )
    state_test(
        pre=pre,
        post={},
        tx=Transaction(
            to=parent,
            gas_limit=1_000_000,
            state_gas_reservoir=0,
            sender=pre.fund_eoa(),
        ),
    )


@pytest.mark.valid_from("EIP8037")
def test_p14_child_clears_with_reservoir(state_test: StateTestFiller, pre: Alloc) -> None:
    """Same, but the transaction declares a reservoir larger than the set."""
    clearer = pre.deploy_contract(Op.SSTORE(K1, 0) + Op.STOP)
    parent = pre.deploy_contract(
        Op.SSTORE(K1, 1) + Op.POP(Op.DELEGATECALL(gas=Op.GAS, address=clearer)) + Op.STOP
    )
    state_test(
        pre=pre,
        post={},
        tx=Transaction(
            to=parent,
            gas_limit=1_000_000,
            state_gas_reservoir=300_000,
            sender=pre.fund_eoa(),
        ),
    )


@pytest.mark.valid_from("EIP8037")
def test_p14_child_clears_preexisting_parent_sets(
    state_test: StateTestFiller, pre: Alloc
) -> None:
    """A child clears a pre-existing slot while the parent creates a new one."""
    clearer = pre.deploy_contract(Op.SSTORE(K2, 0) + Op.STOP)
    parent = pre.deploy_contract(
        Op.SSTORE(K1, 1) + Op.POP(Op.DELEGATECALL(gas=Op.GAS, address=clearer)) + Op.STOP,
        storage={K2: 1},
    )
    state_test(
        pre=pre,
        post={},
        tx=Transaction(
            to=parent,
            gas_limit=1_000_000,
            state_gas_reservoir=0,
            sender=pre.fund_eoa(),
        ),
    )


@pytest.mark.valid_from("EIP8037")
def test_p14_auth_then_clear(state_test: StateTestFiller, pre: Alloc) -> None:
    """
    7702 authorization (the only `commit_state_gas` path) plus clears.

    A commit folds the spill into `state_gas_committed_spill` and leaves
    the spill at zero, so any later refund credits the reservoir instead
    of `gas_left`. This is the structurally most promising route to a
    reservoir above the grant, hence to a negative net.
    """
    target = pre.deploy_contract(
        Op.SSTORE(K1, 0) + Op.SSTORE(K2, 0) + Op.STOP, storage={K1: 1, K2: 1}
    )
    authority = pre.fund_eoa()
    state_test(
        pre=pre,
        post={},
        tx=Transaction(
            to=target,
            gas_limit=2_000_000,
            state_gas_reservoir=0,
            authorization_list=[
                AuthorizationTuple(address=target, nonce=0, signer=authority)
            ],
            sender=pre.fund_eoa(),
        ),
    )


@pytest.mark.valid_from("EIP8037")
def test_p14_auth_setclear_in_frame(state_test: StateTestFiller, pre: Alloc) -> None:
    """7702 authorization, then an in-frame set/clear pair."""
    target = pre.deploy_contract(Op.SSTORE(K1, 1) + Op.SSTORE(K1, 0) + Op.STOP)
    authority = pre.fund_eoa()
    state_test(
        pre=pre,
        post={},
        tx=Transaction(
            to=target,
            gas_limit=2_000_000,
            state_gas_reservoir=0,
            authorization_list=[
                AuthorizationTuple(address=target, nonce=0, signer=authority)
            ],
            sender=pre.fund_eoa(),
        ),
    )


@pytest.mark.valid_from("EIP8037")
def test_p14_auth_child_clears(state_test: StateTestFiller, pre: Alloc) -> None:
    """7702 authorization, parent sets, child clears (cross-frame credit)."""
    clearer = pre.deploy_contract(Op.SSTORE(K1, 0) + Op.STOP)
    parent = pre.deploy_contract(
        Op.SSTORE(K1, 1) + Op.POP(Op.DELEGATECALL(gas=Op.GAS, address=clearer)) + Op.STOP
    )
    authority = pre.fund_eoa()
    state_test(
        pre=pre,
        post={},
        tx=Transaction(
            to=parent,
            gas_limit=2_000_000,
            state_gas_reservoir=0,
            authorization_list=[
                AuthorizationTuple(address=parent, nonce=0, signer=authority)
            ],
            sender=pre.fund_eoa(),
        ),
    )


@pytest.mark.valid_from("EIP8037")
def test_p14_failed_create_after_new_account_charge(
    state_test: StateTestFiller, pre: Alloc
) -> None:
    """A CREATE whose child reverts, so the NEW_ACCOUNT charge is credited."""
    factory = pre.deploy_contract(
        Op.MSTORE(0, Op.PUSH2(0xFEFE))
        + Op.POP(Op.CREATE(value=0, offset=30, size=2))
        + Op.STOP
    )
    state_test(
        pre=pre,
        post={},
        tx=Transaction(
            to=factory,
            gas_limit=1_000_000,
            state_gas_reservoir=0,
            sender=pre.fund_eoa(),
        ),
    )


# --------------------------------------------------------------------------
# Class 13: the receipt figure versus the block figure, per fork.
# --------------------------------------------------------------------------


@pytest.mark.parametrize("clears", [0, 1, 4])
@pytest.mark.valid_from("Berlin")
def test_p13_refunding_tx(state_test: StateTestFiller, pre: Alloc, clears: int) -> None:
    """A tx clearing `clears` pre-existing slots: receipt vs block figure."""
    slots = list(range(1, clears + 1))
    code = Op.STOP
    if slots:
        body = Op.SSTORE(slots[0], 0)
        for s in slots[1:]:
            body += Op.SSTORE(s, 0)
        code = body + Op.STOP
    target = pre.deploy_contract(code, storage=dict.fromkeys(slots, 1))
    state_test(
        pre=pre,
        post={},
        tx=Transaction(
            to=target,
            gas_limit=1_000_000,
            state_gas_reservoir=0,
            sender=pre.fund_eoa(),
        ),
    )


# --------------------------------------------------------------------------
# Class 15: the calldata floor, with and without refunds.
# --------------------------------------------------------------------------


@pytest.mark.parametrize("data_len", [0, 128, 512, 2048])
@pytest.mark.parametrize("clears", [0, 8])
@pytest.mark.valid_from("Prague")
def test_p15_floor(
    state_test: StateTestFiller, pre: Alloc, data_len: int, clears: int
) -> None:
    """Calldata-heavy, execution-light, with and without refunds."""
    slots = list(range(1, clears + 1))
    code = Op.STOP
    if slots:
        body = Op.SSTORE(slots[0], 0)
        for s in slots[1:]:
            body += Op.SSTORE(s, 0)
        code = body + Op.STOP
    target = pre.deploy_contract(code, storage=dict.fromkeys(slots, 1))
    state_test(
        pre=pre,
        post={},
        tx=Transaction(
            to=target,
            data=b"\x01" * data_len,
            gas_limit=1_000_000,
            state_gas_reservoir=0,
            sender=pre.fund_eoa(),
        ),
    )


# --------------------------------------------------------------------------
# Class 14, round 2: the one-sidedness of state-gas block accounting.
# --------------------------------------------------------------------------


@pytest.mark.valid_from("EIP8037")
def test_p14b_free3_create0(state_test: StateTestFiller, pre: Alloc) -> None:
    """Free three pre-existing slots, create nothing."""
    target = pre.deploy_contract(
        Op.SSTORE(1, 0) + Op.SSTORE(2, 0) + Op.SSTORE(3, 0) + Op.STOP,
        storage={1: 1, 2: 1, 3: 1},
    )
    state_test(
        pre=pre,
        post={},
        tx=Transaction(
            to=target,
            gas_limit=1_000_000,
            state_gas_reservoir=0,
            sender=pre.fund_eoa(),
        ),
    )


@pytest.mark.valid_from("EIP8037")
def test_p14b_free0_create1(state_test: StateTestFiller, pre: Alloc) -> None:
    """Create one slot, free nothing."""
    target = pre.deploy_contract(Op.SSTORE(1, 1) + Op.STOP)
    state_test(
        pre=pre,
        post={},
        tx=Transaction(
            to=target,
            gas_limit=1_000_000,
            state_gas_reservoir=0,
            sender=pre.fund_eoa(),
        ),
    )


@pytest.mark.valid_from("EIP8037")
def test_p14b_free2_create1(state_test: StateTestFiller, pre: Alloc) -> None:
    """Create one slot and free two: physically net-freeing."""
    target = pre.deploy_contract(
        Op.SSTORE(1, 1) + Op.SSTORE(2, 0) + Op.SSTORE(3, 0) + Op.STOP,
        storage={2: 1, 3: 1},
    )
    state_test(
        pre=pre,
        post={},
        tx=Transaction(
            to=target,
            gas_limit=1_000_000,
            state_gas_reservoir=0,
            sender=pre.fund_eoa(),
        ),
    )


@pytest.mark.valid_from("EIP8037")
def test_p14b_free4_create1(state_test: StateTestFiller, pre: Alloc) -> None:
    """Create one slot and free four."""
    target = pre.deploy_contract(
        Op.SSTORE(1, 1)
        + Op.SSTORE(2, 0)
        + Op.SSTORE(3, 0)
        + Op.SSTORE(4, 0)
        + Op.SSTORE(5, 0)
        + Op.STOP,
        storage={2: 1, 3: 1, 4: 1, 5: 1},
    )
    state_test(
        pre=pre,
        post={},
        tx=Transaction(
            to=target,
            gas_limit=1_000_000,
            state_gas_reservoir=0,
            sender=pre.fund_eoa(),
        ),
    )


@pytest.mark.valid_from("EIP8037")
def test_p14b_setclear_same_slot(state_test: StateTestFiller, pre: Alloc) -> None:
    """Create one slot and clear that same slot: the credited case."""
    target = pre.deploy_contract(Op.SSTORE(1, 1) + Op.SSTORE(1, 0) + Op.STOP)
    state_test(
        pre=pre,
        post={},
        tx=Transaction(
            to=target,
            gas_limit=1_000_000,
            state_gas_reservoir=0,
            sender=pre.fund_eoa(),
        ),
    )
