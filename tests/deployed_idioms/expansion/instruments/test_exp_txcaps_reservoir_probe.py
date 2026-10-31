"""
Measurement instrument: where does the state-gas reservoir begin?

EIP-8037 defines the reservoir as `tx.gas` above `TX_MAX_GAS_LIMIT`, so the
EIP-7825 cap and the reservoir are the same boundary seen from two sides.
Arithmetically `reservoir = tx.gas - TX_MAX_GAS_LIMIT` for `tx.gas >= cap`,
with the intrinsic cost cancelling out entirely:

    evm_gas   = tx.gas - intrinsic
    budget    = CAP    - intrinsic
    execution = min(budget, evm_gas)
    reservoir = evm_gas - execution = tx.gas - CAP      (when tx.gas >= CAP)

Instrument: a child frame given a tight execution forward writes one FRESH
slot (97,920 state gas). With no reservoir the state charge must spill into
the child's execution gas and the write cannot land; with a reservoir it can.
Phase (a) measures the child's exact execution cost; phase (b) locates the
reservoir threshold.

FAILURES ARE THE MEASUREMENT.
"""

import pytest
from execution_testing import Account, Alloc, Op, StateTestFiller, Transaction

CAP = 2**24
STORAGE_SET = 64 * 1530  # 97,920


def _shape(pre: Alloc, fwd: int) -> tuple[object, object]:
    writer = pre.deploy_contract(Op.SSTORE(0, 1) + Op.STOP)
    parent = pre.deploy_contract(
        Op.SSTORE(0, Op.CALL(gas=fwd, address=writer)) + Op.STOP,
        storage={0: 0xFF},
    )
    return writer, parent


# ---- phase (a): the child's exact execution cost for one fresh slot -------
@pytest.mark.parametrize(
    "fwd", [12_100, 12_103, 12_106, 12_109, 12_112, 12_200]
)
@pytest.mark.valid_from("Amsterdam")
def test_child_cost(
    state_test: StateTestFiller, pre: Alloc, fwd: int
) -> None:
    """Probe: with an ample reservoir, which forward is enough?"""
    writer, parent = _shape(pre, fwd)
    tx = Transaction(
        to=parent,
        gas_limit=CAP + 400_000,
        sender=pre.fund_eoa(amount=10**18),
    )
    state_test(
        pre=pre,
        post={writer: Account(storage={0: 1}), parent: Account(storage={0: 1})},
        tx=tx,
    )


# ---- phase (b): where the reservoir starts --------------------------------
@pytest.mark.parametrize(
    "tx_gas",
    [
        CAP,
        CAP + STORAGE_SET - 1,
        CAP + STORAGE_SET,
        CAP + STORAGE_SET + 1,
    ],
    ids=["at_cap", "one_short", "exact", "one_over"],
)
@pytest.mark.parametrize("landed", [0, 1])
@pytest.mark.valid_from("Amsterdam")
def test_threshold(
    state_test: StateTestFiller, pre: Alloc, tx_gas: int, landed: int
) -> None:
    """Probe: a tight child forward, so only the reservoir can fund it."""
    writer, parent = _shape(pre, 12_106)
    tx = Transaction(
        to=parent, gas_limit=tx_gas, sender=pre.fund_eoa(amount=10**18)
    )
    state_test(
        pre=pre,
        post={
            writer: Account(storage={0: landed}),
            parent: Account(storage={0: landed}),
        },
        tx=tx,
    )
