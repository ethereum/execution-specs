"""Sender mutex class that allows sending transactions one at a time."""

from pathlib import Path
from typing import Generator, Iterator

import pytest
from filelock import FileLock
from pytest_metadata.plugin import metadata_key

from execution_testing.base_types import Number, Wei
from execution_testing.logging import get_logger
from execution_testing.rpc import EthRPC
from execution_testing.test_types import EOA, Transaction

logger = get_logger(__name__)


def pytest_addoption(parser: pytest.Parser) -> None:
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
        help="Amount of wei to sweep from the seed account to the sender account. "  # noqa: E501
        "Default=None (Entire balance)",
    )

    sender_group.addoption(
        "--sender-funding-txs-gas-price",
        action="store",
        dest="sender_funding_transactions_gas_price",
        type=Wei,
        default=None,
        help=(
            "Gas price set for the funding transactions of each worker's sender key. "
            "Default=None (1.5x current network gas price)"
        ),
    )

    sender_group.addoption(
        "--sender-fund-refund-gas-limit",
        action="store",
        dest="sender_fund_refund_gas_limit",
        type=Wei,
        default=21_000,
        help=(
            "Gas limit set for the funding transactions of each worker's sender key."  # noqa: E501
        ),
    )


@pytest.fixture(scope="session")
def sender_funding_transactions_gas_price(
    request: pytest.FixtureRequest,
    eth_rpc: EthRPC,
) -> int:
    """Get the gas price for the funding transactions."""
    gas_price: int | None = (
        request.config.option.sender_funding_transactions_gas_price
    )
    if gas_price is None:
        network_gas_price = eth_rpc.gas_price()
        gas_price = int(network_gas_price * 1.5)
        logger.info(
            f"Using calculated gas price: {gas_price / 10**9:.9f} Gwei "
            f"(1.5x network gas price: {network_gas_price / 10**9:.9f} Gwei)"
        )
    else:
        logger.info(f"Using specified gas price: {gas_price / 10**9:.9f} Gwei")
    assert gas_price > 0, "Gas price must be greater than 0"
    return gas_price


@pytest.fixture(scope="session")
def sender_fund_refund_gas_limit(request: pytest.FixtureRequest) -> int:
    """Get the gas limit of the funding transactions."""
    gas_limit = request.config.option.sender_fund_refund_gas_limit
    logger.info(f"Using gas limit for funding transactions: {gas_limit}")
    return gas_limit


@pytest.fixture(scope="session")
def seed_account_sweep_amount(request: pytest.FixtureRequest) -> int | None:
    """Get the seed account sweep amount."""
    sweep_amount = request.config.option.seed_account_sweep_amount
    if sweep_amount is not None:
        logger.info(
            f"Using specified seed account sweep amount: {sweep_amount / 10**18:.18f} ETH"
        )
    else:
        logger.info(
            "No seed account sweep amount specified, will sweep entire balance"
        )
    return sweep_amount


@pytest.fixture(scope="session")
def worker_key_funding_amount(
    seed_key: EOA,
    eth_rpc: EthRPC,
    session_temp_folder: Path,
    worker_count: int,
    sender_funding_transactions_gas_price: int,
    sender_fund_refund_gas_limit: int,
    seed_account_sweep_amount: int | None,
) -> int | None:
    """
    Calculate the initial balance of each worker key.

    The way to do this is to fetch the seed key balance and divide it by the
    number of workers. This way we can ensure that each worker key has the same
    initial balance.

    We also only do this once per session, because if we try to fetch the
    balance again, it could be that another worker has already sent a
    transaction and the balance is different.

    It's not really possible to calculate the transaction costs of each test
    that each worker is going to run, so we can't really calculate the initial
    balance of each sender key based on that.

    If we are not running tests in parallel, this method is skipped since
    all tests will run from the seed account.
    """
    if worker_count <= 1:
        return None

    base_name = "worker_key_funding_amount"
    base_file = session_temp_folder / base_name
    base_lock_file = session_temp_folder / f"{base_name}.lock"

    with FileLock(base_lock_file):
        if base_file.exists():
            # Some other worker already did this for us, use that value.
            cached_amount = int(base_file.read_text())
            logger.info(
                f"Using cached worker key funding amount: {cached_amount / 10**18:.18f} ETH"
            )
            return cached_amount

        logger.info("Calculating worker key funding amount")
        available_amount = (
            seed_account_sweep_amount
            if seed_account_sweep_amount is not None
            # No sweep amount specified, sweep the entire balance.
            else eth_rpc.get_balance(seed_key)
        )
        amount_source = (
            "Specified sweep amount"
            if seed_account_sweep_amount is not None
            else "Seed account balance"
        )
        logger.info(
            f"{amount_source}: {available_amount / 10**18:.18f} ETH, "
            f"distributing across {worker_count} workers"
        )
        seed_sender_balance_per_worker = available_amount // worker_count
        # Calculate the cost of the transaction to send the amount.
        funding_tx_cost = (
            sender_fund_refund_gas_limit
            * sender_funding_transactions_gas_price
        )
        logger.info(
            f"Funding transaction cost: {funding_tx_cost / 10**18:.18f} ETH "
            f"(gas_limit={sender_fund_refund_gas_limit}, "
            f"gas_price={sender_funding_transactions_gas_price / 10**9:.9f} Gwei)"
        )
        # Subtract the cost of the transaction that is going to be sent to
        # the seed sender
        worker_key_funding_amount = (
            seed_sender_balance_per_worker - funding_tx_cost
        )
        if worker_key_funding_amount <= 0:
            logger.error(
                f"{amount_source} is too low to distribute to {worker_count} workers. "
                f"Available: {available_amount / 10**18:.6f} ETH, "
                f"Funding cost: {funding_tx_cost / 10**18:.6f} ETH"
            )
            raise AssertionError(
                f"""
                {amount_source} is too low to distribute to the
                specified number of workers ({worker_count}).
                {available_amount / 10**18:.6f} ETH,
                when distributed across all workers, and subtracting the
                funding transaction cost
                ({funding_tx_cost / 10**18:.6f} ETH), results in a zero or
                negative value.
                """
            )
        logger.info(
            f"Calculated worker key funding amount: {worker_key_funding_amount / 10**18:.18f} ETH "
            f"({seed_sender_balance_per_worker / 10**18:.18f} ETH per worker - "
            f"{funding_tx_cost / 10**18:.18f} ETH transaction cost)"
        )
        # Write the value to the file for the rest of the workers to use.
        base_file.write_text(str(worker_key_funding_amount))
        return worker_key_funding_amount


@pytest.fixture(scope="session")
def session_worker_key(
    request: pytest.FixtureRequest,
    seed_key: EOA,
    worker_count: int,
    worker_key_funding_amount: int | None,
    eoa_iterator: Iterator[EOA],
    eth_rpc: EthRPC,
    session_temp_folder: Path,
    sender_funding_transactions_gas_price: int,
    sender_fund_refund_gas_limit: int,
    dry_run: bool,
) -> Generator[EOA, None, None]:
    """
    Get the key for this worker in this session that will be the account
    that funds all EOAs and contracts in the tests that this worker executes.

    Each worker will have a different key, but coordination is required
    because all worker keys come from the same seed key.

    If we are not running tests in parallel, this method simply returns the
    seed account directly.
    """
    if worker_count <= 1:
        logger.info("Not running tests in parallel, using seed key directly")
        starting_balance = eth_rpc.get_balance(seed_key)
        yield seed_key

        remaining_balance = eth_rpc.get_balance(seed_key)
        used_balance = starting_balance - remaining_balance
        logger.info(
            f"Seed {seed_key} used balance: {used_balance / 10**18:.18f} ETH "
            f"(remaining: {remaining_balance / 10**18:.18f} ETH)"
        )
        request.config.stash[metadata_key]["Senders"][str(seed_key)] = (
            f"Used balance={used_balance / 10**18:.18f}"
        )
        return None

    assert worker_key_funding_amount is not None, (
        "`worker_key_funding_amount` is None"
    )
    # For the seed sender we do need to keep track of the nonce because it is
    # shared among different processes, and there might not be a new block
    # produced between the transactions.
    seed_sender_nonce_file_name = "seed_sender_nonce"
    seed_sender_lock_file_name = f"{seed_sender_nonce_file_name}.lock"
    seed_sender_nonce_file = session_temp_folder / seed_sender_nonce_file_name
    seed_sender_lock_file = session_temp_folder / seed_sender_lock_file_name

    worker_key = next(eoa_iterator)
    logger.info(f"Allocated worker key: {worker_key}")

    # Prepare funding transaction for this specific worker.
    # Each worker locks the next nonce by using a file lock to coordinate.
    with FileLock(seed_sender_lock_file):
        if seed_sender_nonce_file.exists():
            with seed_sender_nonce_file.open("r") as f:
                seed_key.nonce = Number(f.read())
                logger.debug(
                    f"Loaded seed key nonce from file: {seed_key.nonce}"
                )
        else:
            logger.debug(
                "No existing seed key nonce file, using current nonce"
            )
        fund_tx = Transaction(
            sender=seed_key,
            to=worker_key,
            gas_limit=sender_fund_refund_gas_limit,
            gas_price=sender_funding_transactions_gas_price,
            value=worker_key_funding_amount,
        ).with_signature_and_sender()
        logger.info(
            f"Preparing funding transaction: {worker_key_funding_amount / 10**18:.18f} ETH "
            f"from {seed_key} to {worker_key} (nonce={seed_key.nonce})"
        )
        if not dry_run:
            eth_rpc.send_transaction(fund_tx)
            logger.info(f"Sent funding transaction: {fund_tx.hash}")
        else:
            logger.info("Dry run: skipping funding transaction send")
        with seed_sender_nonce_file.open("w") as f:
            f.write(str(seed_key.nonce))
    if not dry_run:
        logger.info(
            f"Waiting for funding transaction to be mined: {fund_tx.hash}"
        )
        eth_rpc.wait_for_transaction(fund_tx)
        logger.info(f"Funding transaction confirmed: {fund_tx.hash}")

    # Run all tests for this worker.
    yield worker_key

    # All tests for this worker have completed, refund seed key.
    logger.info(
        f"All tests completed for worker {worker_key}, preparing refund"
    )
    remaining_balance = eth_rpc.get_balance(worker_key)
    worker_key.nonce = Number(eth_rpc.get_transaction_count(worker_key))
    used_balance = worker_key_funding_amount - remaining_balance
    logger.info(
        f"Worker {worker_key} used balance: {used_balance / 10**18:.18f} ETH "
        f"(remaining: {remaining_balance / 10**18:.18f} ETH)"
    )
    request.config.stash[metadata_key]["Senders"][str(worker_key)] = (
        f"Used balance={used_balance / 10**18:.18f}"
    )

    refund_gas_limit = sender_fund_refund_gas_limit
    # double the gas price to ensure the transaction is included and overwrites
    # any other transaction that might have been sent by the sender.
    refund_gas_price = sender_funding_transactions_gas_price * 2
    tx_cost = refund_gas_limit * refund_gas_price
    logger.debug(
        f"Refund transaction cost: {tx_cost / 10**18:.18f} ETH "
        f"(gas_limit={refund_gas_limit}, gas_price={refund_gas_price / 10**9:.9f} Gwei)"
    )

    if (remaining_balance - 1) < tx_cost:
        logger.warning(
            f"Insufficient balance for refund: {remaining_balance / 10**18:.18f} ETH < "
            f"{tx_cost / 10**18:.18f} ETH (transaction cost). Skipping refund."
        )
        return

    # Update the nonce of the sender in case one of the pre-alloc transactions
    # failed
    worker_key.nonce = Number(eth_rpc.get_transaction_count(worker_key))
    refund_value = remaining_balance - tx_cost - 1
    logger.info(
        f"Preparing refund transaction: {refund_value / 10**18:.18f} ETH "
        f"from {worker_key} to {seed_key} (nonce={worker_key.nonce})"
    )

    refund_tx = Transaction(
        sender=worker_key,
        to=seed_key,
        gas_limit=refund_gas_limit,
        gas_price=refund_gas_price,
        value=refund_value,
    ).with_signature_and_sender()

    logger.info(
        f"Sending and waiting for refund transaction: {refund_tx.hash}"
    )
    eth_rpc.send_wait_transaction(refund_tx)
    logger.info(f"Refund transaction confirmed: {refund_tx.hash}")


@pytest.fixture(scope="function")
def worker_key(
    eth_rpc: EthRPC, session_worker_key: EOA
) -> Generator[EOA, None, None]:
    """Prepare the worker key for the current test."""
    logger.debug(f"Preparing worker key {session_worker_key} for test")
    rpc_nonce = Number(
        eth_rpc.get_transaction_count(
            session_worker_key, block_number="pending"
        )
    )
    if rpc_nonce != session_worker_key.nonce:
        logger.info(
            f"Worker key nonce mismatch: {session_worker_key.nonce} != {rpc_nonce}"
        )
        logger.info(f"Updating worker key nonce to {rpc_nonce}")
        session_worker_key.nonce = rpc_nonce

    # Record the start balance of the worker key
    worker_key_start_balance = eth_rpc.get_balance(session_worker_key)
    logger.debug(
        f"Worker key start balance: {worker_key_start_balance / 10**18:.18f} ETH"
    )

    yield session_worker_key

    logger.debug(
        f"Test completed, checking worker key {session_worker_key} balance"
    )
    final_balance = eth_rpc.get_balance(session_worker_key)
    used_balance = worker_key_start_balance - final_balance
    logger.info(
        f"Worker key {session_worker_key} used balance: {used_balance / 10**18:.18f} ETH "
        f"(start: {worker_key_start_balance / 10**18:.18f} ETH, "
        f"final: {final_balance / 10**18:.18f} ETH)"
    )


def pytest_sessionstart(session: pytest.Session) -> None:
    """Reset the sender info before the session starts."""
    session.config.stash[metadata_key]["Senders"] = {}
