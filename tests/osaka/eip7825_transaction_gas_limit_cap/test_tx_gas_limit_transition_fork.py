"""
Transaction gas limit cap fork transition tests.

Tests for fork transition behavior in [EIP-7825: Transaction Gas Limit
Cap](https://eips.ethereum.org/EIPS/eip-7825).
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
    Transaction,
    TransactionException,
)
from execution_testing.forks import Osaka

from .spec import ref_spec_7825

REFERENCE_SPEC_GIT_PATH = ref_spec_7825.git_path
REFERENCE_SPEC_VERSION = ref_spec_7825.version


@EIPChecklist.ModifiedTransactionValidityConstraint.Test.ForkTransition.AcceptedBeforeFork()
@EIPChecklist.ModifiedTransactionValidityConstraint.Test.ForkTransition.RejectedBeforeFork()
@EIPChecklist.ModifiedTransactionValidityConstraint.Test.ForkTransition.AcceptedAfterFork()
@EIPChecklist.ModifiedTransactionValidityConstraint.Test.ForkTransition.RejectedAfterFork()
@pytest.mark.valid_at_transition_to("Osaka")
@pytest.mark.parametrize(
    "transaction_at_cap",
    [
        pytest.param(True, id="at_cap"),
        pytest.param(False, marks=pytest.mark.exception_test, id="above_cap"),
    ],
)
def test_transaction_gas_limit_cap_at_transition(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    transaction_at_cap: bool,
) -> None:
    """
    Test transaction gas limit cap behavior at the Osaka transition.

    Before transition_timestamp: No gas limit cap (transactions with
    gas > 2^24 are valid).
    At/after transition_timestamp: Gas limit cap of 2^24 is enforced.
    """
    t = Osaka.transition_timestamp()
    contract_address = pre.deploy_contract(
        code=Op.SSTORE(Op.TIMESTAMP, Op.ADD(Op.SLOAD(Op.TIMESTAMP), 1))
        + Op.STOP,
    )

    # Get the gas limit cap at fork activation
    tx_gas_cap = fork.transaction_gas_limit_cap(timestamp=t)
    assert tx_gas_cap is not None, (
        "Gas limit cap should not be None after fork activation"
    )

    # Test boundary: cap + 1 should fail after fork activation
    above_cap = tx_gas_cap + 1

    # Before fork activation: both cap and above_cap transactions should
    # succeed
    at_cap_tx_before_fork = Transaction(
        ty=0,  # Legacy transaction
        to=contract_address,
        gas_limit=tx_gas_cap,
        sender=pre.fund_eoa(),
    )

    above_cap_tx_before_fork = Transaction(
        ty=0,  # Legacy transaction
        to=contract_address,
        gas_limit=above_cap,
        sender=pre.fund_eoa(),
    )

    post_cap_tx_error = TransactionException.GAS_LIMIT_EXCEEDS_MAXIMUM

    # After fork activation: test at cap vs above cap
    transition_tx = Transaction(
        ty=0,  # Legacy transaction
        to=contract_address,
        gas_limit=tx_gas_cap if transaction_at_cap else above_cap,
        sender=pre.fund_eoa(),
        error=None if transaction_at_cap else post_cap_tx_error,
    )

    blocks = []

    # Before transition: both cap and above_cap transactions
    # should succeed
    blocks.append(
        Block(
            timestamp=t - 1,
            txs=[above_cap_tx_before_fork, at_cap_tx_before_fork],
        )
    )

    # At transition:
    # - transaction at cap should succeed
    # - transaction above cap (cap + 1) should fail
    blocks.append(
        Block(
            timestamp=t,
            txs=[transition_tx],
            exception=post_cap_tx_error if not transaction_at_cap else None,
        )
    )

    # Post state: storage should be updated by successful transactions
    post = {
        contract_address: Account(
            storage={
                # Set by both txs in first block (before transition):
                t - 1: 2,
                # After transition:
                # - Set by transaction at cap (should succeed)
                # - Not set by tx above cap (should fail)
                t: 1 if transaction_at_cap else 0,
            }
        )
    }

    blockchain_test(pre=pre, blocks=blocks, post=post)
