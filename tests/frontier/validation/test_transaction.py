"""Test the transaction level validations applied from Frontier."""

import pytest
from execution_testing import Alloc, Transaction
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
def test_tx_gas_limit(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    env: Environment,
) -> None:
    """
    Tests that if a tx gas limit is higher than the block with a gas limit,
    an exception is raised.
    """
    sender = pre.fund_eoa()
    to = pre.fund_eoa()

    tx = Transaction(
        gas_limit=21001,
        to=to,
        gas_price=0x01,
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
def test_tx_nonce(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    env: Environment,
    nonce_diff: int,
    expected_exception: TransactionException | None,
) -> None:
    """
    Tests that if a tx nonce matches the account nonce.
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
def test_sender_balance(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    env: Environment,
    fork: BaseFork,
    balance_diff: int,
    expected_exception: TransactionException | None,
) -> None:
    """
    Tests that if a sender has sufficient balance.
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
