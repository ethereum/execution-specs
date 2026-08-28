"""
Verify the gas a CREATE's init code observes when the creating contract is
entered directly by the transaction: the child receives all but one 64th
of what remains in the creating frame.

Ported from:
state_tests/stTransactionTest/StoreGasOnCreateFiller.json

@manually-enhanced: Do not overwrite. The ported bytecode is kept, but
the creating frame is entered through an outer call with a derived
budget, so the child's stored GAS observation depends on neither the
transaction gas limit nor the fork's intrinsic cost (the ported absolute
pin moved with every schedule change). The floor is TangerineWhistle
because the 63/64 withhold this test measures is EIP-150's.
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

CHILD_GAS_SLOT = 0xFD
# The child must afford its store out of the 63/64 it is granted, so the
# creating frame carries a little more than that store costs.
CHILD_HEADROOM = 5_000


@pytest.mark.ported_from(
    ["state_tests/stTransactionTest/StoreGasOnCreateFiller.json"],
)
@pytest.mark.valid_from("TangerineWhistle")
def test_store_gas_on_create(
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

    setup = Op.MSTORE(
        offset=0x0,
        value=int.from_bytes(child_code, "big"),
        new_memory_size=0x20,
    )
    create_code = Op.CREATE(
        value=0x0,
        offset=0x20 - len(child_code),
        size=len(child_code),
        new_memory_size=0x20,
        old_memory_size=0x20,
        init_code_size=len(child_code),
    )
    creator = pre.deploy_contract(
        code=setup + Op.POP(create_code) + Op.STOP,
    )

    # Enter the creator through an outer call with a fixed budget, so
    # the child's observation depends on neither the transaction's gas
    # limit nor the fork's intrinsic cost. The budget is chosen from
    # what the child should see, then grown to cover the frame's own
    # charges.
    child_budget = child_code.gas_cost(fork) + CHILD_HEADROOM
    creator_gas = (
        child_budget + setup.gas_cost(fork) + create_code.gas_cost(fork)
    )
    entry = pre.deploy_contract(
        code=Op.POP(Op.CALL(gas=creator_gas, address=creator)) + Op.STOP
    )

    tx = Transaction(
        sender=pre.fund_eoa(),
        to=entry,
        protected=fork.supports_protected_txs(),
        # Charge state gas to the frames, so an EIP-8037 CREATE's own
        # cost comes out of the budget above rather than a reservoir.
        state_gas_reservoir=0,
    )

    # The child receives all but one 64th of what the creating frame
    # still holds at the CREATE, and must afford its store out of that.
    granted = child_budget - child_budget // 64
    assert granted > child_code.gas_cost(fork), (
        "CHILD_HEADROOM no longer covers the 63/64 withhold"
    )
    child_observed = granted - Op.GAS.gas_cost(fork)

    post = {
        compute_create_address(address=creator, nonce=1): Account(
            nonce=int(fork.is_eip_enabled(161)),
            code=b"",
            storage={CHILD_GAS_SLOT: child_observed},
        ),
    }

    state_test(pre=pre, post=post, tx=tx)
