"""
Verify the gas a CREATE's init code observes when the creating frame also
expands memory: the child receives all but one 64th of what remains, and
the creating frame's entry and post-CREATE gas readings are asserted.

Ported from:
state_tests/stMemExpandingEIP150Calls/CreateAndGasInsideCreateWithMemExpandingCallsFiller.json

@manually-enhanced: Do not overwrite. The ported bytecode is kept, but the
transaction budget and every stored gas reading (entry snapshot, child
observation, post-CREATE reading) are derived from the fork instead of
pinned — the entry snapshot doubles as a transaction-intrinsic pin.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Fork,
    StateTestFiller,
    Transaction,
    compute_create_address,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

ENTRY_GAS_SLOT = 0xA
ADDRESS_SLOT = 0xB
AFTER_GAS_SLOT = 0x9
CHILD_GAS_SLOT = 0xFD


@pytest.mark.ported_from(
    [
        "state_tests/stMemExpandingEIP150Calls/CreateAndGasInsideCreateWithMemExpandingCallsFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Berlin")
def test_create_and_gas_inside_create_with_mem_expanding_calls(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """A CREATE's init code observes 63/64 of the creating frame's gas."""
    # Child init code: stores the gas it observes, deposits no code.
    child_code = Op.SSTORE(
        key=CHILD_GAS_SLOT,
        value=Op.GAS,
        key_warm=False,
        original_value=0,
        new_value=1,
    )
    child_bytes = bytes(child_code)

    entry_snapshot = Op.SSTORE(
        key=ENTRY_GAS_SLOT,
        value=Op.GAS,
        key_warm=False,
        original_value=0,
        new_value=1,
    )
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
    after_snapshot = Op.SSTORE(
        key=AFTER_GAS_SLOT,
        value=Op.GAS,
        key_warm=False,
        original_value=0,
        new_value=1,
    )
    creator = pre.deploy_contract(
        code=entry_snapshot + setup + create_store + after_snapshot + Op.STOP,
    )

    # Fork-derived budget: the ported 600000 no longer covers the three
    # state-priced stores plus the CREATE under EIP-8037. The margin
    # keeps the final store above the EIP-2200 stipend.
    intrinsic = fork.transaction_intrinsic_cost_calculator()()
    tx_gas = (
        intrinsic
        + entry_snapshot.gas_cost(fork)
        + setup.gas_cost(fork)
        + create_store.gas_cost(fork)
        + child_code.gas_cost(fork)
        + after_snapshot.gas_cost(fork)
        + 5_000
    )
    tx = Transaction(
        sender=pre.fund_eoa(),
        to=creator,
        gas_limit=tx_gas,
    )

    # Entry reading: everything after the intrinsic, minus the GAS opcode
    # itself (it executes first in the store's operand order).
    entry_observed = tx_gas - intrinsic - Op.GAS.gas_cost(fork)
    # The child receives all but one 64th of what remains after the entry
    # store, the setup, and the CREATE's own charges.
    base = (
        tx_gas
        - intrinsic
        - entry_snapshot.gas_cost(fork)
        - setup.gas_cost(fork)
        - create_code.gas_cost(fork)
    )
    assert base > 0, "the budget must cover the CREATE's charges"
    child_observed = (base - base // 64) - Op.GAS.gas_cost(fork)
    # After the CREATE: the child's consumption and the address store are
    # gone; the address store's own cost is the composite minus the
    # CREATE it wraps.
    after_observed = (
        base
        - child_code.gas_cost(fork)
        - (create_store.gas_cost(fork) - create_code.gas_cost(fork))
        - Op.GAS.gas_cost(fork)
    )

    created = compute_create_address(address=creator, nonce=1)
    post = {
        creator: Account(
            storage={
                ENTRY_GAS_SLOT: entry_observed,
                ADDRESS_SLOT: created,
                AFTER_GAS_SLOT: after_observed,
            },
        ),
        created: Account(
            nonce=1,
            code=b"",
            storage={CHILD_GAS_SLOT: child_observed},
        ),
    }

    state_test(pre=pre, post=post, tx=tx)
