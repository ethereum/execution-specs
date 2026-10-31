"""
Measurement instrument, not a corpus test: what does a frame actually get
charged, from inside the EVM, for creating / updating / clearing one
storage slot?

Its FAILURES ARE THE MEASUREMENT. Each param asserts 0, so the mismatch
message prints the real value as `want 0x0, got 0x...`. Do not add this
directory to a corpus gate.

Reproduce (from engine/eels):
  ./.venv/bin/fill ../../wave1/instruments --from <Fork> --until <Fork> \
      -k "storage_cost and state_test" --output /tmp/sc -q --tb=long \
      -p no:cacheprovider
"""

import pytest
from execution_testing import Account, Alloc, Op, StateTestFiller, Transaction

SLOT_FRESH = 0x01
SLOT_EXISTING = 0x02
SLOT_MEASURED = 0x09

WRITES = {
    # create a slot that did not exist
    "create": Op.SSTORE(SLOT_FRESH, 1),
    # update a slot that already holds a non-zero value
    "update": Op.SSTORE(SLOT_EXISTING, 2),
    # clear a slot that already holds a non-zero value
    "clear": Op.SSTORE(SLOT_EXISTING, 0),
}


@pytest.mark.parametrize("write", list(WRITES))
@pytest.mark.valid_from("Berlin")
def test_storage_cost(
    state_test: StateTestFiller, pre: Alloc, write: str
) -> None:
    """Probe: the in-frame gas delta across one storage write."""
    subject = pre.deploy_contract(
        Op.MSTORE(0, Op.GAS)
        + WRITES[write]
        + Op.MSTORE(0x20, Op.GAS)
        + Op.SSTORE(SLOT_MEASURED, Op.SUB(Op.MLOAD(0), Op.MLOAD(0x20)))
        + Op.STOP,
        storage={SLOT_EXISTING: 1},
    )
    tx = Transaction(to=subject, state_gas_reservoir=0, sender=pre.fund_eoa())
    state_test(
        pre=pre,
        post={subject: Account(storage={SLOT_MEASURED: 0})},
        tx=tx,
    )
