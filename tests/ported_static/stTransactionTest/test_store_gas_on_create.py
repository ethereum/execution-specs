"""
Verify the gas a CREATE's init code observes when the creating contract is
entered directly by the transaction: the child receives all but one 64th
of what remains in the creating frame.

Ported from:
state_tests/stTransactionTest/StoreGasOnCreateFiller.json

@manually-enhanced: Do not overwrite. The ported bytecode is kept, but the
transaction budget and the child's stored GAS observation are derived from
the fork (the ported absolute pin moved with every schedule change).
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


@pytest.mark.ported_from(
    ["state_tests/stTransactionTest/StoreGasOnCreateFiller.json"],
)
@pytest.mark.valid_from("Berlin")
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
    child_bytes = bytes(child_code)

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
    creator = pre.deploy_contract(
        code=setup + Op.POP(create_code) + Op.STOP,
    )

    # Fork-derived budget with margin left after the child's work.
    intrinsic = fork.transaction_intrinsic_cost_calculator()()
    gas_limit = (
        intrinsic
        + setup.gas_cost(fork)
        + create_code.gas_cost(fork)
        + child_code.gas_cost(fork)
        + 15_000
    )

    tx = Transaction(
        sender=pre.fund_eoa(),
        to=creator,
        gas_limit=gas_limit,
    )

    # The child receives all but one 64th of what remains after the
    # setup and the CREATE's own charges; its GAS read costs 2.
    base = (
        gas_limit
        - intrinsic
        - setup.gas_cost(fork)
        - create_code.gas_cost(fork)
    )
    assert base > 0, "the budget must cover the CREATE's charges"
    child_observed = (base - base // 64) - Op.GAS.gas_cost(fork)

    post = {
        compute_create_address(address=creator, nonce=1): Account(
            nonce=1,
            code=b"",
            storage={CHILD_GAS_SLOT: child_observed},
        ),
    }

    state_test(pre=pre, post=post, tx=tx)
