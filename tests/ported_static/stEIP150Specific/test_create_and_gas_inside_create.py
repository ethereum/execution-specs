"""
Verify the gas a CREATE's init code observes: the child receives all but
one 64th of what remains in the creating frame, and the parent's CREATE
cost is measured alongside it.

Ported from:
state_tests/stEIP150Specific/CreateAndGasInsideCreateFiller.json

@manually-enhanced: Do not overwrite. An outer call pins the creating
frame's budget so the child's stored GAS observation is fork-derived
(`63/64` of the derived base); the parent measures the CREATE with
CodeGasMeasure instead of raw snapshots.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    CodeGasMeasure,
    Fork,
    StateTestFiller,
    Transaction,
    compute_create_address,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

ADDRESS_SLOT = 0xB
GAS_SLOT = 0x9
CHILD_GAS_SLOT = 0xFD

# The creating frame's pinned budget (the ported transaction's).
CALLER_GAS = 600_000


@pytest.mark.ported_from(
    ["state_tests/stEIP150Specific/CreateAndGasInsideCreateFiller.json"],
)
@pytest.mark.valid_from("Berlin")
def test_create_and_gas_inside_create(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """A CREATE's init code observes 63/64 of the creating frame's gas."""
    # Child init code: stores the gas it observes into its own storage
    # and deposits no code.
    child_code = Op.SSTORE(
        key=CHILD_GAS_SLOT,
        value=Op.GAS,
        key_warm=False,
        original_value=0,
        new_value=1,
    )
    child_bytes = bytes(child_code)

    # The child bytes sit right-aligned in the first memory word.
    setup = Op.MSTORE(
        offset=0x0,
        value=int.from_bytes(child_bytes, "big"),
        new_memory_size=0x20,
    )
    create_code = Op.CREATE(
        value=0x0,
        offset=0x20 - len(child_bytes),
        size=len(child_bytes),
        new_memory_size=0x20,
        old_memory_size=0x20,
        init_code_size=len(child_bytes),
    )
    create_store = Op.SSTORE(
        key=ADDRESS_SLOT,
        value=create_code,
        key_warm=False,
        original_value=0,
        new_value=1,
    )
    creator = pre.deploy_contract(
        code=setup
        + CodeGasMeasure(
            code=create_store,
            extra_stack_items=0,
            sstore_key=GAS_SLOT,
        ),
    )

    # The outer call pins the creating frame's budget so the child's
    # observation does not depend on the tx gas limit.
    entry = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.CALL(gas=CALLER_GAS, address=creator))
        + Op.STOP,
    )

    tx = Transaction(
        sender=pre.fund_eoa(),
        to=entry,
        state_gas_reservoir=0,
    )

    # The child receives all but one 64th of what remains after the
    # setup, the measuring GAS read, and the CREATE's own charges (its
    # new-account state gas is taken before the withhold).
    base = (
        CALLER_GAS
        - setup.gas_cost(fork)
        - Op.GAS.gas_cost(fork)
        - create_code.gas_cost(fork)
    )
    assert base > 0, "CALLER_GAS must cover the CREATE's charges"
    child_observed = (base - base // 64) - Op.GAS.gas_cost(fork)
    measured_create = create_store.gas_cost(fork) + child_code.gas_cost(fork)

    created = compute_create_address(address=creator, nonce=1)
    post = {
        entry: Account(storage={0: 1}),
        creator: Account(
            storage={
                ADDRESS_SLOT: created,
                GAS_SLOT: measured_create,
            },
        ),
        created: Account(
            nonce=1,
            code=b"",
            storage={CHILD_GAS_SLOT: child_observed},
        ),
    }

    state_test(pre=pre, post=post, tx=tx)
