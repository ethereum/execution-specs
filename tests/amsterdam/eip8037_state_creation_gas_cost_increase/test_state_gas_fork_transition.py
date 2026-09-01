"""
State gas fork transition tests for EIP-8037.

Verify that state gas pricing and the modified transaction validity
constraint (tx.gas can exceed TX_MAX_GAS_LIMIT) activate correctly at
the EIP-8037 fork boundary.

Before EIP-8037: no state gas dimension, tx.gas capped at
TX_MAX_GAS_LIMIT (EIP-7825).

At/after EIP-8037: state gas charges apply, tx.gas above
TX_MAX_GAS_LIMIT is valid (excess feeds the reservoir).

Tests for [EIP-8037: State Creation Gas Cost Increase]
(https://eips.ethereum.org/EIPS/eip-8037).
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Block,
    BlockchainTestFiller,
    EIPChecklist,
    Fork,
    Op,
    Storage,
    Transaction,
    TransactionException,
)

from .spec import ref_spec_8037

REFERENCE_SPEC_GIT_PATH = ref_spec_8037.git_path
REFERENCE_SPEC_VERSION = ref_spec_8037.version

pytestmark = pytest.mark.valid_at_transition_to("EIP8037")


@EIPChecklist.GasCostChanges.Test.ForkTransition.Before()
@EIPChecklist.GasCostChanges.Test.ForkTransition.After()
def test_sstore_state_gas_at_transition(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test SSTORE state gas activates at the EIP-8037 fork boundary.

    A sub-call granted only the store's execution gas succeeds before
    the fork, and after it only when a reservoir carries the new state
    charge into the child frame.
    """
    before_fork = fork.fork_at(timestamp=14_999)
    after_fork = fork.fork_at(timestamp=15_000)

    sstore_code = Op.SSTORE(0, 1, original_value=0, new_value=1)
    # Each side gets only what its own fork prices as execution gas.
    before_grant = sstore_code.gas_cost(before_fork)
    execution_gas = sstore_code.execution_cost(after_fork)
    state_gas = sstore_code.state_cost(after_fork)
    assert sstore_code.state_cost(before_fork) == 0, "no state dimension yet"
    assert state_gas > 0

    storage_before = Storage()
    target_before = pre.deploy_contract(code=sstore_code)
    caller_before = pre.deploy_contract(
        code=Op.SSTORE(
            storage_before.store_next(1, "subcall_succeeds"),
            Op.CALL(gas=before_grant, address=target_before),
        ),
    )

    storage_funded = Storage()
    target_funded = pre.deploy_contract(code=sstore_code)
    caller_funded = pre.deploy_contract(
        code=Op.SSTORE(
            storage_funded.store_next(1, "reservoir_pays_state_gas"),
            Op.CALL(gas=execution_gas, address=target_funded),
        ),
    )

    storage_starved = Storage()
    target_starved = pre.deploy_contract(code=sstore_code)
    caller_starved = pre.deploy_contract(
        code=Op.SSTORE(
            storage_starved.store_next(0, "subcall_runs_out_of_state_gas"),
            Op.CALL(gas=execution_gas, address=target_starved),
        ),
    )

    blocks = [
        # Pre-fork: the grant is the whole price.
        Block(
            timestamp=14_999,
            txs=[
                Transaction(
                    to=caller_before,
                    state_gas_reservoir=0,
                    sender=pre.fund_eoa(),
                ),
            ],
        ),
        # Post-fork: the reservoir pays the state charge.
        Block(
            timestamp=15_000,
            txs=[
                Transaction(
                    to=caller_funded,
                    state_gas_reservoir=state_gas,
                    sender=pre.fund_eoa(),
                ),
            ],
        ),
        # Post-fork, no reservoir: the state charge halts the child.
        Block(
            timestamp=15_001,
            txs=[
                Transaction(
                    to=caller_starved,
                    state_gas_reservoir=0,
                    sender=pre.fund_eoa(),
                ),
            ],
        ),
    ]

    post = {
        caller_before: Account(storage=storage_before),
        target_before: Account(storage={0: 1}),
        caller_funded: Account(storage=storage_funded),
        target_funded: Account(storage={0: 1}),
        caller_starved: Account(storage=storage_starved),
        target_starved: Account(storage={0: 0}),
    }

    blockchain_test(pre=pre, blocks=blocks, post=post)


@EIPChecklist.ModifiedTransactionValidityConstraint.Test.ForkTransition.AcceptedBeforeFork()
@EIPChecklist.ModifiedTransactionValidityConstraint.Test.ForkTransition.RejectedBeforeFork()
@EIPChecklist.ModifiedTransactionValidityConstraint.Test.ForkTransition.AcceptedAfterFork()
@EIPChecklist.ModifiedTransactionValidityConstraint.Test.ForkTransition.RejectedAfterFork()
@pytest.mark.parametrize(
    "gas_above_cap",
    [
        pytest.param(False, id="at_cap"),
        pytest.param(
            True,
            id="above_cap",
            marks=pytest.mark.exception_test,
        ),
    ],
)
def test_tx_gas_above_cap_at_transition(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    gas_above_cap: bool,
    fork: Fork,
) -> None:
    """
    Test tx.gas > TX_MAX_GAS_LIMIT validity at the EIP-8037 transition.

    Before EIP-8037, EIP-7825 rejects any tx with gas > TX_MAX_GAS_LIMIT.
    After EIP-8037 it's allowed — the excess feeds the state gas
    reservoir. This test sends a tx at the cap (always valid) and one
    above the cap (rejected before, accepted after).
    """
    after_fork = fork.fork_at(timestamp=15_000)
    gas_limit_cap = after_fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    storage_before = Storage()
    contract_before = pre.deploy_contract(
        code=(Op.SSTORE(storage_before.store_next(1), 1)),
    )

    storage_after = Storage()
    contract_after = pre.deploy_contract(
        code=(Op.SSTORE(storage_after.store_next(1), 1)),
    )

    gas_limit = gas_limit_cap + 1 if gas_above_cap else gas_limit_cap

    # Before fork: above-cap tx is rejected by EIP-7825
    before_error = (
        TransactionException.GAS_LIMIT_EXCEEDS_MAXIMUM
        if gas_above_cap
        else None
    )

    blocks = [
        Block(
            timestamp=14_999,
            txs=[
                Transaction(
                    to=contract_before,
                    gas_limit=gas_limit,
                    sender=pre.fund_eoa(),
                    error=before_error,
                ),
            ],
            exception=before_error,
        ),
        # After fork: above-cap tx is now valid (excess feeds reservoir)
        Block(
            timestamp=15_000,
            txs=[
                Transaction(
                    to=contract_after,
                    gas_limit=gas_limit,
                    sender=pre.fund_eoa(),
                ),
            ],
        ),
    ]

    post = {
        contract_before: Account(
            storage=storage_before if not gas_above_cap else {0: 0},
        ),
        contract_after: Account(storage=storage_after),
    }

    blockchain_test(pre=pre, blocks=blocks, post=post)


@EIPChecklist.GasCostChanges.Test.ForkTransition.After()
def test_reservoir_available_after_transition(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test reservoir is available for state ops after the fork.

    Before the fork, tx.gas is capped at TX_MAX_GAS_LIMIT and there is
    no reservoir. After the fork, gas above the cap feeds the reservoir,
    which child calls can draw from for state operations.
    """
    after_fork = fork.fork_at(timestamp=15_000)
    child_code = Op.SSTORE(0, 1, original_value=0, new_value=1)
    sstore_state_gas = child_code.state_cost(after_fork)

    child_storage = Storage()
    child_storage.store_next(1, "child_slot_set")
    child = pre.deploy_contract(code=child_code)

    parent_storage = Storage()
    parent = pre.deploy_contract(
        code=Op.SSTORE(
            parent_storage.store_next(1, "subcall_succeeds"),
            Op.CALL(gas=child_code.execution_cost(after_fork), address=child),
        ),
    )

    blocks = [
        Block(
            timestamp=15_000,
            txs=[
                Transaction(
                    to=parent,
                    state_gas_reservoir=sstore_state_gas,
                    sender=pre.fund_eoa(),
                ),
            ],
        ),
    ]

    post = {
        parent: Account(storage=parent_storage),
        child: Account(storage=child_storage),
    }

    blockchain_test(pre=pre, blocks=blocks, post=post)
