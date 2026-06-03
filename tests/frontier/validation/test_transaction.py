"""Test the transaction level validations applied from Frontier."""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Op,
    StateTestFiller,
    Storage,
    Transaction,
)
from execution_testing.base_types.base_types import ZeroPaddedHexNumber
from execution_testing.exceptions.exceptions import TransactionException
from execution_testing.forks.base_fork import BaseFork
from execution_testing.specs.blockchain import (
    Block,
    BlockchainTestFiller,
    Header,
)
from execution_testing.test_types.block_types import Environment
from execution_testing.test_types.transaction_types import TransactionDefaults


@pytest.mark.exception_test
@pytest.mark.eels_base_coverage
def test_tx_gas_limit(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    env: Environment,
) -> None:
    """
    Tests that if a tx gas limit is higher than the block gas limit,
    an exception is raised.
    """
    sender = pre.fund_eoa()
    to = pre.fund_eoa()

    tx = Transaction(
        gas_limit=21001,
        to=to,
        gas_price=0x10,  # Must be >= base fee to isolate gas limit validation
        sender=sender,
        protected=False,
        error=TransactionException.GAS_ALLOWANCE_EXCEEDED,
    )

    modified_fields = {"gas_limit": ZeroPaddedHexNumber(21000)}
    env.gas_limit = ZeroPaddedHexNumber(21000)

    block = Block(
        txs=[tx],
        rlp_modifier=Header(**modified_fields),
        exception=TransactionException.GAS_ALLOWANCE_EXCEEDED,
    )

    blockchain_test(pre=pre, post={}, blocks=[block], genesis_environment=env)


@pytest.mark.parametrize(
    "nonce_diff, expected_exception",
    [
        pytest.param(
            -1,
            TransactionException.NONCE_MISMATCH_TOO_LOW,
            marks=pytest.mark.exception_test,
        ),
        (0, None),  # Valid case - no exception
        pytest.param(
            1,
            TransactionException.NONCE_MISMATCH_TOO_HIGH,
            marks=pytest.mark.exception_test,
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
@pytest.mark.eels_base_coverage
def test_tx_nonce(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    env: Environment,
    nonce_diff: int,
    expected_exception: TransactionException | None,
) -> None:
    """
    Tests that the tx nonce matches the account nonce.
    """
    sender = pre.fund_eoa(nonce=5)
    to = pre.fund_eoa()

    tx = Transaction(
        to=to,
        nonce=sender.nonce + nonce_diff,
        sender=sender,
        protected=False,
        error=expected_exception,
    )

    block = Block(
        txs=[tx],
        exception=expected_exception,
    )

    blockchain_test(pre=pre, post={}, blocks=[block], genesis_environment=env)


@pytest.mark.parametrize(
    "balance_diff, expected_exception",
    [
        pytest.param(
            -1,
            TransactionException.INSUFFICIENT_ACCOUNT_FUNDS,
            marks=pytest.mark.exception_test,
        ),
        (0, None),  # Valid case - no exception
        (1, None),
    ],
)
@pytest.mark.eels_base_coverage
def test_sender_balance(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    env: Environment,
    fork: BaseFork,
    balance_diff: int,
    expected_exception: TransactionException | None,
) -> None:
    """
    Tests that the sender has sufficient balance.
    """
    sender = pre.fund_eoa()
    to = pre.fund_eoa()

    intrinsic_cost = fork.transaction_intrinsic_cost_calculator()
    tx_gas_limit = intrinsic_cost()
    tx_gas_price = TransactionDefaults.gas_price
    tx_value = 0

    # Calculate required balance from tx fields and fund sender
    required_balance = tx_gas_limit * tx_gas_price + tx_value
    sender = pre.fund_eoa(amount=required_balance + balance_diff)

    # Create transaction first with defaults
    tx = Transaction(
        sender=sender,
        gas_limit=tx_gas_limit,
        gas_price=tx_gas_price,
        value=tx_value,
        to=to,
        protected=False,
        error=expected_exception,
    )

    block = Block(
        txs=[tx],
        exception=expected_exception,
    )

    blockchain_test(pre=pre, post={}, blocks=[block], genesis_environment=env)


@pytest.mark.valid_from("Frontier")
@pytest.mark.state_test_only
@pytest.mark.exception_test
@pytest.mark.eels_base_coverage
def test_sender_balance_insufficient_state_test(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    A legacy transaction from a sender that cannot afford `gas * gasPrice`
    must be rejected, exercised through the state-test code path.
    """
    storage = Storage()
    # If the transaction were (incorrectly) executed, this SSTORE would land a
    # non-default value in slot 0, diverging the post-state root from the
    # rejected (pre == post) outcome.
    contract = pre.deploy_contract(
        code=Op.SSTORE(storage.store_next(0, "must_stay_unset"), 0x1)
        + Op.STOP,
    )
    # Zero balance, unable to cover any gas cost.
    sender = pre.fund_eoa(amount=0)

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=100_000,
        gas_price=10,
        protected=False,  # legacy tx
        error=TransactionException.INSUFFICIENT_ACCOUNT_FUNDS,
    )

    state_test(
        env=Environment(),
        pre=pre,
        # Transaction rejected: contract storage stays empty.
        post={contract: Account(storage=storage)},
        tx=tx,
    )
