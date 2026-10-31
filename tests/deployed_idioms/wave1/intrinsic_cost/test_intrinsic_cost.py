"""
Archetype 17: hardcoded intrinsic transaction cost.

Every gas-refunding relayer on mainnet -- a widely deployed smart-account wallet, GSN, EIP-4337
paymasters, any meta-transaction forwarder -- reimburses its sender for gas
it cannot measure from inside the EVM. The intrinsic charge is deducted
before the first opcode runs, so `GAS` never sees it, and the contract has
no opcode that reports it. Deployed code therefore **hardcodes 21,000**.

EIP-2780 falsifies that constant, and does something subtler than reducing
it: it **decomposes** a flat charge into a shape-dependent one.

```
base_execution_gas = TX_BASE + recipient_execution_gas        transactions.py:777
  recipient_execution_gas = 0                     if tx.to == sender
                          = COLD_ACCOUNT_ACCESS   otherwise        (3,000)
                          + TX_VALUE_COST         if tx.value > 0  (6,000)
                          = CREATE_ACCESS + init_code_cost  if create
TX_BASE = 21,000 (frontier) -> 12,000 (Amsterdam)        vm/gas.py:143
```

Measured (`tests/tools/test_intrinsic_shape_probe.py`, CHECKED):

```
fork            value=0    value=1
Berlin..Osaka   21,000     21,000     flat, shape-independent
Amsterdam       15,000     21,000     shape-dependent
```

So a hardcoded 21,000 is still exactly right for a **value-bearing** call,
and over-states by **6,000** for a zero-value one -- which is the
overwhelmingly common shape: every ERC-20 transfer and every plain contract
call. The relayer over-reimburses by 6,000 gas times gasprice on each, and
nothing reverts. That is a silent, systematic funds leak in the direction
nobody designs for: **a reprice that makes gas CHEAPER.**

Of the 15 gas constants that changed value across the 15 mainnet forks, five
moved *down* (`TX_BASE`, `TX_DATA_PER_NON_ZERO`, and four EIP-1108
precompiles -- `PRECOMPILE_ECMUL` fell 40,000 -> 6,000). Reductions are not a
smaller version of the same hazard; they break a different population.

This is one of the two archetypes where asserting a raw gas number **is** the
invariant, so SCHEMA §4.1's prohibition does not apply (it says "unless the
gas number IS the invariant"). Do not "fix" a failure here by rebasing the
constants -- the constants are the assertion.
"""

import pytest
from execution_testing import Account, Alloc, Op, StateTestFiller, Transaction

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

# Frozen gas limit, so the measured value is an absolute, not a derived one.
FROZEN_LIMIT = 1_000_000

# `GAS` costs 2 and executes before the subtraction, so the recorded figure
# is the intrinsic charge plus 2.
GAS_OPCODE_COST = 2

RELAYER_ASSUMPTION = 21_000  # what deployed meta-tx code hardcodes


def _intrinsic_recorder() -> object:
    """Record the intrinsic charge the transaction actually paid."""
    return Op.SSTORE(0, Op.SUB(FROZEN_LIMIT, Op.GAS)) + Op.STOP


@pytest.mark.parametrize("value", [0, 1])
@pytest.mark.valid_from("Berlin")
@pytest.mark.valid_until("Osaka")
def test_intrinsic_cost_is_flat_before_eip2780(
    state_test: StateTestFiller,
    pre: Alloc,
    value: int,
) -> None:
    """
    Test the intrinsic charge is a flat 21,000 regardless of transaction shape.

    This is the assumption deployed relayers encode. Asserted on the forks
    where it holds, which no existing test does.
    """
    recorder = pre.deploy_contract(_intrinsic_recorder())
    tx = Transaction(
        to=recorder,
        gas_limit=FROZEN_LIMIT,
        value=value,
        sender=pre.fund_eoa(amount=10**18),
    )
    state_test(
        pre=pre,
        post={
            recorder: Account(
                storage={0: RELAYER_ASSUMPTION + GAS_OPCODE_COST}
            )
        },
        tx=tx,
    )


@pytest.mark.parametrize(
    "value,intrinsic",
    [
        pytest.param(0, 15_000, id="zero_value_drops_by_6000"),
        pytest.param(1, 21_000, id="value_bearing_unchanged"),
    ],
)
@pytest.mark.valid_from("EIP8037")
def test_intrinsic_cost_is_shape_dependent_from_eip2780(
    state_test: StateTestFiller,
    pre: Alloc,
    value: int,
    intrinsic: int,
) -> None:
    """
    Test the intrinsic charge splits by transaction shape once decomposed.

    A zero-value call pays `TX_BASE + COLD_ACCOUNT_ACCESS` = 15,000, so a
    relayer holding the 21,000 assumption over-reimburses by 6,000. A
    value-bearing call pays `TX_BASE + COLD_ACCOUNT_ACCESS + TX_VALUE_COST`
    = 21,000, coincidentally identical to the old flat charge, so the same
    relayer is still exactly right there. Both arms are asserted, because a
    test covering only one would make the hazard look uniform when its whole
    danger is that it is not.
    """
    recorder = pre.deploy_contract(_intrinsic_recorder())
    tx = Transaction(
        to=recorder,
        gas_limit=FROZEN_LIMIT,
        value=value,
        sender=pre.fund_eoa(amount=10**18),
    )
    state_test(
        pre=pre,
        post={recorder: Account(storage={0: intrinsic + GAS_OPCODE_COST})},
        tx=tx,
    )
