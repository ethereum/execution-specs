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

    Before the fork, an SSTORE zero-to-nonzero succeeds with only
    regular gas (no state gas dimension). After the fork, the same
    operation requires state gas. Both blocks use TX_MAX_GAS_LIMIT
    which provides enough gas in either regime.
    """
    after_fork = fork.fork_at(timestamp=15_000)
    gas_limit_cap = after_fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    contract_before = pre.deploy_contract(
        code=Op.SSTORE(0, 1),
    )
    contract_after = pre.deploy_contract(
        code=Op.SSTORE(0, 1),
    )

    blocks = [
        # Before fork: SSTORE succeeds with regular gas only
        Block(
            timestamp=14_999,
            txs=[
                Transaction(
                    to=contract_before,
                    gas_limit=gas_limit_cap,
                    sender=pre.fund_eoa(),
                ),
            ],
        ),
        # After fork: SSTORE succeeds — state gas drawn from gas_left
        Block(
            timestamp=15_000,
            txs=[
                Transaction(
                    to=contract_after,
                    gas_limit=gas_limit_cap,
                    sender=pre.fund_eoa(),
                ),
            ],
        ),
    ]

    post = {
        contract_before: Account(storage={0: 1}),
        contract_after: Account(storage={0: 1}),
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
    gas_limit_cap = after_fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    sstore_state_gas = after_fork.sstore_state_gas()

    child_storage = Storage()
    child = pre.deploy_contract(
        code=Op.SSTORE(child_storage.store_next(1), 1),
    )

    parent_storage = Storage()
    parent = pre.deploy_contract(
        code=(
            Op.SSTORE(
                parent_storage.store_next(1),
                Op.CALL(gas=100_000, address=child),
            )
        ),
    )

    blocks = [
        Block(
            timestamp=15_000,
            txs=[
                Transaction(
                    to=parent,
                    gas_limit=gas_limit_cap + sstore_state_gas,
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
