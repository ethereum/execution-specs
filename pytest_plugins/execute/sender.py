"""Sender mutex class that allows sending transactions one at a time."""

from pathlib import Path
from typing import Generator, Iterator

import pytest
from filelock import FileLock
from pytest_metadata.plugin import metadata_key  # type: ignore

from ethereum_test_base_types import Number, Wei
from ethereum_test_rpc import EthRPC
from ethereum_test_tools import EOA, Transaction


def pytest_addoption(parser):
    """Add command-line options to pytest."""
    sender_group = parser.getgroup(
        "sender",
        "Arguments for the sender key fixtures",
    )

    sender_group.addoption(
        "--seed-account-sweep-amount",
        action="store",
        dest="seed_account_sweep_amount",
        type=Wei,
        default=None,
        help="Amount of wei to sweep from the seed account to the sender account. "
        "Default=None (Entire balance)",
    )

    sender_group.addoption(
        "--sender-funding-txs-gas-price",
        action="store",
        dest="sender_funding_transactions_gas_price",
        type=Wei,
        default=None,
        help=("Gas price set for the funding transactions of each worker's sender key."),
    )

    sender_group.addoption(
        "--sender-fund-refund-gas-limit",
        action="store",
        dest="sender_fund_refund_gas_limit",
        type=Wei,
        default=21_000,
        help=("Gas limit set for the funding transactions of each worker's sender key."),
    )


@pytest.fixture(scope="session")
def sender_funding_transactions_gas_price(
    request: pytest.FixtureRequest, default_gas_price: int
) -> int:
    """Get the gas price for the funding transactions."""
    gas_price: int | None = request.config.option.sender_funding_transactions_gas_price
    if gas_price is None:
        gas_price = default_gas_price
    assert gas_price > 0, "Gas price must be greater than 0"
    return gas_price


@pytest.fixture(scope="session")
def sender_fund_refund_gas_limit(request: pytest.FixtureRequest) -> int:
    """Get the gas limit of the funding transactions."""
    return request.config.option.sender_fund_refund_gas_limit


@pytest.fixture(scope="session")
def seed_account_sweep_amount(request: pytest.FixtureRequest) -> int | None:
    """Get the seed account sweep amount."""
    return request.config.option.seed_account_sweep_amount


@pytest.fixture(scope="session")
def sender_key_initial_balance(
    seed_sender: EOA,
    eth_rpc: EthRPC,
    session_temp_folder: Path,
    worker_count: int,
    sender_funding_transactions_gas_price: int,
    sender_fund_refund_gas_limit: int,
    seed_account_sweep_amount: int | None,
) -> int:
    """
    Calculate the initial balance of each sender key.

    The way to do this is to fetch the seed sender balance and divide it by the number of
    workers. This way we can ensure that each sender key has the same initial balance.

    We also only do this once per session, because if we try to fetch the balance again, it
    could be that another worker has already sent a transaction and the balance is different.

    It's not really possible to calculate the transaction costs of each test that each worker
    is going to run, so we can't really calculate the initial balance of each sender key
    based on that.
    """
    base_name = "sender_key_initial_balance"
    base_file = session_temp_folder / base_name
    base_lock_file = session_temp_folder / f"{base_name}.lock"

    with FileLock(base_lock_file):
        if base_file.exists():
            with base_file.open("r") as f:
                sender_key_initial_balance = int(f.read())
        else:
            if seed_account_sweep_amount is None:
                seed_account_sweep_amount = eth_rpc.get_balance(seed_sender)
            seed_sender_balance_per_worker = seed_account_sweep_amount // worker_count
            assert seed_sender_balance_per_worker > 100, "Seed sender balance too low"
            # Subtract the cost of the transaction that is going to be sent to the seed sender
            sender_key_initial_balance = seed_sender_balance_per_worker - (
                sender_fund_refund_gas_limit * sender_funding_transactions_gas_price
            )

            with base_file.open("w") as f:
                f.write(str(sender_key_initial_balance))
    return sender_key_initial_balance


@pytest.fixture(scope="session")
def sender_key(
    request: pytest.FixtureRequest,
    seed_sender: EOA,
    sender_key_initial_balance: int,
    eoa_iterator: Iterator[EOA],
    eth_rpc: EthRPC,
    session_temp_folder: Path,
    sender_funding_transactions_gas_price: int,
    sender_fund_refund_gas_limit: int,
) -> Generator[EOA, None, None]:
    """
    Get the sender keys for all tests.

    The seed sender is going to be shared among different processes, so we need to lock it
    before we produce each funding transaction.
    """
    # For the seed sender we do need to keep track of the nonce because it is shared among
    # different processes, and there might not be a new block produced between the transactions.
    seed_sender_nonce_file_name = "seed_sender_nonce"
    seed_sender_lock_file_name = f"{seed_sender_nonce_file_name}.lock"
    seed_sender_nonce_file = session_temp_folder / seed_sender_nonce_file_name
    seed_sender_lock_file = session_temp_folder / seed_sender_lock_file_name

    sender = next(eoa_iterator)

    # prepare funding transaction
    with FileLock(seed_sender_lock_file):
        if seed_sender_nonce_file.exists():
            with seed_sender_nonce_file.open("r") as f:
                seed_sender.nonce = Number(f.read())
        fund_tx = Transaction(
            sender=seed_sender,
            to=sender,
            gas_limit=sender_fund_refund_gas_limit,
            gas_price=sender_funding_transactions_gas_price,
            value=sender_key_initial_balance,
        ).with_signature_and_sender()
        eth_rpc.send_transaction(fund_tx)
        with seed_sender_nonce_file.open("w") as f:
            f.write(str(seed_sender.nonce))
    eth_rpc.wait_for_transaction(fund_tx)

    yield sender

    # refund seed sender
    remaining_balance = eth_rpc.get_balance(sender)
    sender.nonce = Number(eth_rpc.get_transaction_count(sender))
    used_balance = sender_key_initial_balance - remaining_balance
    request.config.stash[metadata_key]["Senders"][str(sender)] = (
        f"Used balance={used_balance / 10**18:.18f}"
    )

    refund_gas_limit = sender_fund_refund_gas_limit
    # double the gas price to ensure the transaction is included and overwrites any other
    # transaction that might have been sent by the sender.
    refund_gas_price = sender_funding_transactions_gas_price * 2
    tx_cost = refund_gas_limit * refund_gas_price

    if (remaining_balance - 1) < tx_cost:
        return

    # Update the nonce of the sender in case one of the pre-alloc transactions failed
    sender.nonce = Number(eth_rpc.get_transaction_count(sender))

    refund_tx = Transaction(
        sender=sender,
        to=seed_sender,
        gas_limit=refund_gas_limit,
        gas_price=refund_gas_price,
        value=remaining_balance - tx_cost - 1,
    ).with_signature_and_sender()

    eth_rpc.send_wait_transaction(refund_tx)


def pytest_sessionstart(session):  # noqa: SC200
    """Reset the sender info before the session starts."""
    session.config.stash[metadata_key]["Senders"] = {}
