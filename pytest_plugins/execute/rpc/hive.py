"""
Pytest plugin to run the test-execute in hive-mode.
"""

import io
import json
import os
import time
from dataclasses import asdict, replace
from pathlib import Path
from random import randint
from typing import Any, Dict, Generator, List, Mapping, Tuple, cast

import pytest
from ethereum.crypto.hash import keccak256
from filelock import FileLock
from hive.client import Client, ClientType
from hive.simulation import Simulation
from hive.testing import HiveTest, HiveTestResult, HiveTestSuite
from pydantic import RootModel

from ethereum_test_base_types import EmptyOmmersRoot, EmptyTrieRoot, HexNumber, to_json
from ethereum_test_fixtures.blockchain import FixtureHeader
from ethereum_test_forks import Fork, get_forks
from ethereum_test_rpc import EngineRPC
from ethereum_test_rpc import EthRPC as BaseEthRPC
from ethereum_test_rpc.types import (
    ForkchoiceState,
    PayloadAttributes,
    PayloadStatusEnum,
    TransactionByHashResponse,
)
from ethereum_test_tools import (
    EOA,
    Account,
    Address,
    Alloc,
    Environment,
    Hash,
    Transaction,
    Withdrawal,
)
from ethereum_test_types import Requests
from pytest_plugins.consume.hive_simulators.ruleset import ruleset


class HashList(RootModel[List[Hash]]):
    """Hash list class"""

    root: List[Hash]

    def append(self, item: Hash):
        """Append an item to the list"""
        self.root.append(item)

    def clear(self):
        """Clear the list"""
        self.root.clear()

    def remove(self, item: Hash):
        """Remove an item from the list"""
        self.root.remove(item)

    def __contains__(self, item: Hash):
        """Check if an item is in the list"""
        return item in self.root

    def __len__(self):
        """Get the length of the list"""
        return len(self.root)

    def __iter__(self):
        """Iterate over the list"""
        return iter(self.root)


class AddressList(RootModel[List[Address]]):
    """Address list class"""

    root: List[Address]

    def append(self, item: Address):
        """Append an item to the list"""
        self.root.append(item)

    def clear(self):
        """Clear the list"""
        self.root.clear()

    def remove(self, item: Address):
        """Remove an item from the list"""
        self.root.remove(item)

    def __contains__(self, item: Address):
        """Check if an item is in the list"""
        return item in self.root

    def __len__(self):
        """Get the length of the list"""
        return len(self.root)

    def __iter__(self):
        """Iterate over the list"""
        return iter(self.root)


def get_fork_option(request, option_name: str) -> Fork | None:
    """Post-process get option to allow for external fork conditions."""
    option = request.config.getoption(option_name)
    if option := request.config.getoption(option_name):
        if option == "Merge":
            option = "Paris"
        for fork in get_forks():
            if option == fork.name():
                return fork
    return None


def pytest_addoption(parser):
    """
    Adds command-line options to pytest.
    """
    hive_rpc_group = parser.getgroup(
        "hive_rpc", "Arguments defining the hive RPC client properties for the test."
    )
    hive_rpc_group.addoption(
        "--transactions-per-block",
        action="store",
        dest="transactions_per_block",
        type=int,
        default=None,
        help=("Number of transactions to send before producing the next block."),
    )
    hive_rpc_group.addoption(
        "--get-payload-wait-time",
        action="store",
        dest="get_payload_wait_time",
        type=float,
        default=0.3,
        help=("Time to wait after sending a forkchoice_updated before getting the payload."),
    )
    hive_rpc_group.addoption(
        "--sender-key-initial-balance",
        action="store",
        dest="sender_key_initial_balance",
        type=int,
        default=10**26,
        help=(
            "Initial balance of each sender key. There is one sender key per worker process "
            "(`-n` option)."
        ),
    )
    hive_rpc_group.addoption(
        "--tx-wait-timeout",
        action="store",
        dest="tx_wait_timeout",
        type=int,
        default=10,  # Lowered from Remote RPC because of the consistent block production
        help="Maximum time in seconds to wait for a transaction to be included in a block",
    )


def pytest_configure(config):  # noqa: D103
    config.test_suite_scope = "session"


@pytest.fixture(scope="session")
def base_fork(request) -> Fork:
    """
    Get the base fork for all tests.
    """
    fork = get_fork_option(request, "single_fork")
    assert fork is not None, "invalid fork requested"
    return fork


@pytest.fixture(scope="session")
def seed_sender(session_temp_folder: Path) -> EOA:
    """
    Determine the seed sender account for the client's genesis.
    """
    base_name = "seed_sender"
    base_file = session_temp_folder / base_name
    base_lock_file = session_temp_folder / f"{base_name}.lock"

    with FileLock(base_lock_file):
        if base_file.exists():
            with base_file.open("r") as f:
                seed_sender_key = Hash(f.read())
            seed_sender = EOA(key=seed_sender_key)
        else:
            seed_sender = EOA(key=randint(0, 2**256))
            with base_file.open("w") as f:
                f.write(str(seed_sender.key))
    return seed_sender


@pytest.fixture(scope="session")
def base_pre(request, seed_sender: EOA, worker_count: int) -> Alloc:
    """
    Base pre-allocation for the client's genesis.
    """
    sender_key_initial_balance = request.config.getoption("sender_key_initial_balance")
    return Alloc(
        {seed_sender: Account(balance=(worker_count * sender_key_initial_balance) + 10**18)}
    )


@pytest.fixture(scope="session")
def base_pre_genesis(
    base_fork: Fork,
    base_pre: Alloc,
) -> Tuple[Alloc, FixtureHeader]:
    """
    Create a genesis block from the blockchain test definition.
    """
    env = Environment().set_fork_requirements(base_fork)
    assert (
        env.withdrawals is None or len(env.withdrawals) == 0
    ), "withdrawals must be empty at genesis"
    assert env.parent_beacon_block_root is None or env.parent_beacon_block_root == Hash(
        0
    ), "parent_beacon_block_root must be empty at genesis"

    pre_alloc = Alloc.merge(
        Alloc.model_validate(base_fork.pre_allocation_blockchain()),
        base_pre,
    )
    if empty_accounts := pre_alloc.empty_accounts():
        raise Exception(f"Empty accounts in pre state: {empty_accounts}")
    state_root = pre_alloc.state_root()
    block_number = 0
    timestamp = 1
    genesis = FixtureHeader(
        parent_hash=0,
        ommers_hash=EmptyOmmersRoot,
        fee_recipient=0,
        state_root=state_root,
        transactions_trie=EmptyTrieRoot,
        receipts_root=EmptyTrieRoot,
        logs_bloom=0,
        difficulty=0x20000 if env.difficulty is None else env.difficulty,
        number=block_number,
        gas_limit=env.gas_limit,
        gas_used=0,
        timestamp=timestamp,
        extra_data=b"\x00",
        prev_randao=0,
        nonce=0,
        base_fee_per_gas=env.base_fee_per_gas,
        blob_gas_used=env.blob_gas_used,
        excess_blob_gas=env.excess_blob_gas,
        withdrawals_root=Withdrawal.list_root(env.withdrawals)
        if env.withdrawals is not None
        else None,
        parent_beacon_block_root=env.parent_beacon_block_root,
        requests_hash=Requests(
            max_request_type=base_fork.max_request_type(
                block_number=block_number,
                timestamp=timestamp,
            ),
        )
        if base_fork.header_requests_required(block_number=block_number, timestamp=timestamp)
        else None,
    )

    return (pre_alloc, genesis)


@pytest.fixture(scope="session")
def base_genesis_header(base_pre_genesis: Tuple[Alloc, FixtureHeader]) -> FixtureHeader:
    """
    Return the genesis header for the current test fixture.
    """
    return base_pre_genesis[1]


@pytest.fixture(scope="session")
def client_genesis(base_pre_genesis: Tuple[Alloc, FixtureHeader]) -> dict:
    """
    Convert the fixture's genesis block header and pre-state to a client genesis state.
    """
    genesis = to_json(base_pre_genesis[1])  # NOTE: to_json() excludes None values
    alloc = to_json(base_pre_genesis[0])
    # NOTE: nethermind requires account keys without '0x' prefix
    genesis["alloc"] = {k.replace("0x", ""): v for k, v in alloc.items()}
    return genesis


@pytest.fixture(scope="session")
def buffered_genesis(client_genesis: dict) -> io.BufferedReader:
    """
    Create a buffered reader for the genesis block header of the current test
    fixture.
    """
    genesis_json = json.dumps(client_genesis)
    genesis_bytes = genesis_json.encode("utf-8")
    return io.BufferedReader(cast(io.RawIOBase, io.BytesIO(genesis_bytes)))


@pytest.fixture(scope="session")
def client_files(
    buffered_genesis: io.BufferedReader,
) -> Mapping[str, io.BufferedReader]:
    """
    Define the files that hive will start the client with.

    For this type of test, only the genesis is passed
    """
    files = {}
    files["/genesis.json"] = buffered_genesis
    return files


@pytest.fixture(scope="session")
def environment(base_fork: Fork) -> dict:
    """
    Define the environment that hive will start the client with using the fork
    rules specific for the simulator.
    """
    assert base_fork.name() in ruleset, f"fork '{base_fork.name()}' missing in hive ruleset"
    return {
        "HIVE_CHAIN_ID": "1",
        "HIVE_FORK_DAO_VOTE": "1",
        "HIVE_NODETYPE": "full",
        **{k: f"{v:d}" for k, v in ruleset[base_fork.name()].items()},
    }


@pytest.fixture(scope="session")
def test_suite_name() -> str:
    """
    The name of the hive test suite used in this simulator.
    """
    return "EEST Execute Test, Hive Mode"


@pytest.fixture(scope="session")
def test_suite_description() -> str:
    """
    The description of the hive test suite used in this simulator.
    """
    return "Execute EEST tests using hive endpoint."


@pytest.fixture(autouse=True, scope="session")
def base_hive_test(
    request: pytest.FixtureRequest, test_suite: HiveTestSuite, session_temp_folder: Path
) -> Generator[HiveTest, None, None]:
    """
    Base test used to deploy the main client to be used throughout all tests.
    """
    base_name = "base_hive_test"
    base_file = session_temp_folder / base_name
    base_lock_file = session_temp_folder / f"{base_name}.lock"
    with FileLock(base_lock_file):
        if base_file.exists():
            with open(base_file, "r") as f:
                test = HiveTest(**json.load(f))
        else:
            test = test_suite.start_test(
                name="Base Hive Test",
                description=(
                    "Base test used to deploy the main client to be used throughout all tests."
                ),
            )
            with open(base_file, "w") as f:
                json.dump(asdict(test), f)

    users_file_name = f"{base_name}_users"
    users_file = session_temp_folder / users_file_name
    users_lock_file = session_temp_folder / f"{users_file_name}.lock"
    with FileLock(users_lock_file):
        if users_file.exists():
            with open(users_file, "r") as f:
                users = json.load(f)
        else:
            users = 0
        users += 1
        with open(users_file, "w") as f:
            json.dump(users, f)

    yield test

    test_pass = True
    test_details = "All tests have completed"
    if request.session.testsfailed > 0:  # noqa: SC200
        test_pass = False
        test_details = "One or more tests have failed"

    with FileLock(users_lock_file):
        with open(users_file, "r") as f:
            users = json.load(f)
        users -= 1
        with open(users_file, "w") as f:
            json.dump(users, f)
        if users == 0:
            test.end(result=HiveTestResult(test_pass=test_pass, details=test_details))
            base_file.unlink()
            users_file.unlink()


@pytest.fixture(scope="session")
def client_type(simulator: Simulation) -> ClientType:
    """
    The type of client to be used in the test.
    """
    return simulator.client_types()[0]


@pytest.fixture(autouse=True, scope="session")
def client(
    base_hive_test: HiveTest,
    client_files: dict,
    environment: dict,
    client_type: ClientType,
    session_temp_folder: Path,
) -> Generator[Client, None, None]:
    """
    Initialize the client with the appropriate files and environment variables.
    """
    base_name = "hive_client"
    base_file = session_temp_folder / base_name
    base_error_file = session_temp_folder / f"{base_name}.err"
    base_lock_file = session_temp_folder / f"{base_name}.lock"
    client: Client | None = None
    with FileLock(base_lock_file):
        if not base_error_file.exists():
            if base_file.exists():
                with open(base_file, "r") as f:
                    client = Client(**json.load(f))
            else:
                base_error_file.touch()  # Assume error
                client = base_hive_test.start_client(
                    client_type=client_type, environment=environment, files=client_files
                )
                if client is not None:
                    base_error_file.unlink()  # Success
                    with open(base_file, "w") as f:
                        json.dump(
                            asdict(replace(client, config=None)),  # type: ignore
                            f,
                        )

    error_message = (
        f"Unable to connect to the client container ({client_type.name}) via Hive during test "
        "setup. Check the client or Hive server logs for more information."
    )
    assert client is not None, error_message

    users_file_name = f"{base_name}_users"
    users_file = session_temp_folder / users_file_name
    users_lock_file = session_temp_folder / f"{users_file_name}.lock"
    with FileLock(users_lock_file):
        if users_file.exists():
            with open(users_file, "r") as f:
                users = json.load(f)
        else:
            users = 0
        users += 1
        with open(users_file, "w") as f:
            json.dump(users, f)

    yield client

    with FileLock(users_lock_file):
        with open(users_file, "r") as f:
            users = json.load(f)
        users -= 1
        with open(users_file, "w") as f:
            json.dump(users, f)
        if users == 0:
            client.stop()
            base_file.unlink()
            users_file.unlink()


class PendingTxHashes:
    """
    A class to manage the pending transaction hashes in a multi-process environment.

    It uses a lock file to ensure that only one process can access the pending hashes file at a
    time.
    """

    pending_hashes_file: Path
    pending_hashes_lock: Path
    pending_tx_hashes: HashList | None
    lock: FileLock | None

    def __init__(self, temp_folder: Path):
        self.pending_hashes_file = temp_folder / "pending_tx_hashes"
        self.pending_hashes_lock = temp_folder / "pending_tx_hashes.lock"
        self.pending_tx_hashes = None
        self.lock = None

    def __enter__(self):
        """
        Lock the pending hashes file and load it.
        """
        assert self.lock is None, "Lock already acquired"
        self.lock = FileLock(self.pending_hashes_lock, timeout=-1)
        self.lock.acquire()
        assert self.pending_tx_hashes is None, "Pending transaction hashes already loaded"
        if self.pending_hashes_file.exists():
            with open(self.pending_hashes_file, "r") as f:
                self.pending_tx_hashes = HashList.model_validate_json(f.read())
        else:
            self.pending_tx_hashes = HashList([])
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Flush the pending hashes to the file and release the lock.
        """
        assert self.lock is not None, "Lock not acquired"
        assert self.pending_tx_hashes is not None, "Pending transaction hashes not loaded"
        with open(self.pending_hashes_file, "w") as f:
            f.write(self.pending_tx_hashes.model_dump_json())
        self.lock.release()
        self.lock = None
        self.pending_tx_hashes = None

    def append(self, tx_hash: Hash):
        """
        Add a transaction hash to the pending list.
        """
        assert self.lock is not None, "Lock not acquired"
        assert self.pending_tx_hashes is not None, "Pending transaction hashes not loaded"
        self.pending_tx_hashes.append(tx_hash)

    def clear(self):
        """
        Remove a transaction hash from the pending list.
        """
        assert self.lock is not None, "Lock not acquired"
        self.pending_tx_hashes.clear()

    def remove(self, tx_hash: Hash):
        """
        Remove a transaction hash from the pending list.
        """
        assert self.lock is not None, "Lock not acquired"
        assert self.pending_tx_hashes is not None, "Pending transaction hashes not loaded"
        self.pending_tx_hashes.remove(tx_hash)

    def __contains__(self, tx_hash: Hash):
        """
        Check if a transaction hash is in the pending list.
        """
        assert self.lock is not None, "Lock not acquired"
        assert self.pending_tx_hashes is not None, "Pending transaction hashes not loaded"
        return tx_hash in self.pending_tx_hashes

    def __len__(self):
        """
        Get the number of pending transaction hashes.
        """
        assert self.lock is not None, "Lock not acquired"
        assert self.pending_tx_hashes is not None, "Pending transaction hashes not loaded"
        return len(self.pending_tx_hashes)

    def __iter__(self):
        """
        Iterate over the pending transaction hashes.
        """
        assert self.lock is not None, "Lock not acquired"
        assert self.pending_tx_hashes is not None, "Pending transaction hashes not loaded"
        return iter(self.pending_tx_hashes)


class EthRPC(BaseEthRPC):
    """
    Ethereum RPC client for the hive simulator which automatically sends Engine API requests to
    generate blocks after a certain number of transactions have been sent.
    """

    fork: Fork
    engine_rpc: EngineRPC
    transactions_per_block: int
    get_payload_wait_time: float
    pending_tx_hashes: PendingTxHashes

    def __init__(
        self,
        *,
        client: Client,
        fork: Fork,
        base_genesis_header: FixtureHeader,
        transactions_per_block: int,
        session_temp_folder: Path,
        get_payload_wait_time: float,
        initial_forkchoice_update_retries: int = 5,
        transaction_wait_timeout: int = 60,
    ):
        """
        Initialize the Ethereum RPC client for the hive simulator.
        """
        super().__init__(
            f"http://{client.ip}:8545",
            transaction_wait_timeout=transaction_wait_timeout,
        )
        self.fork = fork
        self.engine_rpc = EngineRPC(f"http://{client.ip}:8551")
        self.transactions_per_block = transactions_per_block
        self.pending_tx_hashes = PendingTxHashes(session_temp_folder)
        self.get_payload_wait_time = get_payload_wait_time

        # Send initial forkchoice updated only if we are the first worker
        base_name = "eth_rpc_forkchoice_updated"
        base_file = session_temp_folder / base_name
        base_error_file = session_temp_folder / f"{base_name}.err"
        base_lock_file = session_temp_folder / f"{base_name}.lock"

        with FileLock(base_lock_file):
            if base_error_file.exists():
                raise Exception("Error occurred during initial forkchoice_updated")
            if not base_file.exists():
                base_error_file.touch()  # Assume error
                # Send initial forkchoice updated
                forkchoice_state = ForkchoiceState(
                    head_block_hash=base_genesis_header.block_hash,
                )
                forkchoice_version = self.fork.engine_forkchoice_updated_version()
                assert (
                    forkchoice_version is not None
                ), "Fork does not support engine forkchoice_updated"
                for _ in range(initial_forkchoice_update_retries):
                    response = self.engine_rpc.forkchoice_updated(
                        forkchoice_state,
                        None,
                        version=forkchoice_version,
                    )
                    if response.payload_status.status == PayloadStatusEnum.VALID:
                        break
                    time.sleep(0.5)
                else:
                    raise Exception("Initial forkchoice_updated was invalid")
                base_error_file.unlink()  # Success
                base_file.touch()

    def generate_block(self: "EthRPC"):
        """
        Generate a block using the Engine API.
        """
        # Get the head block hash
        head_block = self.get_block_by_number("latest")

        forkchoice_state = ForkchoiceState(
            head_block_hash=head_block["hash"],
        )
        parent_beacon_block_root = Hash(0) if self.fork.header_beacon_root_required(0, 0) else None
        payload_attributes = PayloadAttributes(
            timestamp=HexNumber(head_block["timestamp"]) + 1,
            prev_randao=Hash(0),
            suggested_fee_recipient=Address(0),
            withdrawals=[] if self.fork.header_withdrawals_required() else None,
            parent_beacon_block_root=parent_beacon_block_root,
        )
        forkchoice_updated_version = self.fork.engine_forkchoice_updated_version()
        assert (
            forkchoice_updated_version is not None
        ), "Fork does not support engine forkchoice_updated"
        response = self.engine_rpc.forkchoice_updated(
            forkchoice_state,
            payload_attributes,
            version=forkchoice_updated_version,
        )
        assert response.payload_status.status == PayloadStatusEnum.VALID, "Payload was invalid"
        assert response.payload_id is not None, "payload_id was not returned by the client"
        time.sleep(self.get_payload_wait_time)
        get_payload_version = self.fork.engine_get_payload_version()
        assert get_payload_version is not None, "Fork does not support engine get_payload"
        new_payload = self.engine_rpc.get_payload(
            response.payload_id,
            version=get_payload_version,
        )
        new_payload_args: List[Any] = [new_payload.execution_payload]
        if new_payload.blobs_bundle is not None:
            new_payload_args.append(new_payload.blobs_bundle.blob_versioned_hashes())
        if parent_beacon_block_root is not None:
            new_payload_args.append(parent_beacon_block_root)
        if new_payload.execution_requests is not None:
            new_payload_args.append(new_payload.execution_requests)
        new_payload_version = self.fork.engine_new_payload_version()
        assert new_payload_version is not None, "Fork does not support engine new_payload"
        new_payload_response = self.engine_rpc.new_payload(
            *new_payload_args, version=new_payload_version
        )
        assert new_payload_response.status == PayloadStatusEnum.VALID, "Payload was invalid"

        new_forkchoice_state = ForkchoiceState(
            head_block_hash=new_payload.execution_payload.block_hash,
        )
        response = self.engine_rpc.forkchoice_updated(
            new_forkchoice_state,
            None,
            version=forkchoice_updated_version,
        )
        assert response.payload_status.status == PayloadStatusEnum.VALID, "Payload was invalid"
        for tx in new_payload.execution_payload.transactions:
            tx_hash = Hash(keccak256(tx))
            if tx_hash in self.pending_tx_hashes:
                self.pending_tx_hashes.remove(tx_hash)

    def send_transaction(self, transaction: Transaction) -> Hash:
        """
        `eth_sendRawTransaction`: Send a transaction to the client.
        """
        returned_hash = super().send_transaction(transaction)
        with self.pending_tx_hashes:
            self.pending_tx_hashes.append(transaction.hash)
            if len(self.pending_tx_hashes) >= self.transactions_per_block:
                self.generate_block()
        return returned_hash

    def wait_for_transaction(self, transaction: Transaction) -> TransactionByHashResponse:
        """
        Wait for a specific transaction to be included in a block.

        Waits for a specific transaction to be included in a block by polling
        `eth_getTransactionByHash` until it is confirmed or a timeout occurs.

        Args:
            transaction: The transaction to track.

        Returns:
            The transaction details after it is included in a block.
        """
        return self.wait_for_transactions([transaction])[0]

    def wait_for_transactions(
        self, transactions: List[Transaction]
    ) -> List[TransactionByHashResponse]:
        """
        Wait for all transactions in the provided list to be included in a block.

        Waits for all transactions in the provided list to be included in a block
        by polling `eth_getTransactionByHash` until they are confirmed or a
        timeout occurs.

        Args:
            transactions: A list of transactions to track.

        Returns:
            A list of transaction details after they are included in a block.

        Raises:
            Exception: If one or more transactions are not included in a block
                within the timeout period.
        """
        tx_hashes = [tx.hash for tx in transactions]
        responses: List[TransactionByHashResponse] = []
        pending_responses: Dict[Hash, TransactionByHashResponse] = {}

        start_time = time.time()
        pending_transactions_handler = PendingTransactionHandler(self)
        while True:
            tx_id = 0
            pending_responses = {}
            while tx_id < len(tx_hashes):
                tx_hash = tx_hashes[tx_id]
                tx = self.get_transaction_by_hash(tx_hash)
                if tx.block_number is not None:
                    responses.append(tx)
                    tx_hashes.pop(tx_id)
                else:
                    pending_responses[tx_hash] = tx
                    tx_id += 1

            if not tx_hashes:
                return responses

            pending_transactions_handler.handle()

            if (time.time() - start_time) > self.transaction_wait_timeout:
                break
            time.sleep(0.1)

        missing_txs_strings = [
            f"{tx.hash} ({tx.model_dump_json()})" for tx in transactions if tx.hash in tx_hashes
        ]

        pending_tx_responses_string = "\n".join(
            [f"{tx_hash}: {tx.model_dump_json()}" for tx_hash, tx in pending_responses.items()]
        )
        raise Exception(
            f"Transactions {', '.join(missing_txs_strings)} were not included in a block "
            f"within {self.transaction_wait_timeout} seconds:\n"
            f"{pending_tx_responses_string}"
        )


class PendingTransactionHandler:
    """Manages block generation based on the number of pending transactions or a block generation
    interval.

    Attributes:
        block_generation_interval: The number of iterations after which a block
            is generated if no new transactions are added (default: 10).
    """

    eth_rpc: EthRPC
    block_generation_interval: int
    last_pending_tx_hashes_count: int | None = None
    i: int = 0

    def __init__(self, eth_rpc: EthRPC, block_generation_interval: int = 10):
        """Initialize the pending transaction handler."""
        self.eth_rpc = eth_rpc
        self.block_generation_interval = block_generation_interval

    def handle(self):
        """Handle pending transactions and generate blocks if necessary.

        If the number of pending transactions reaches the limit, a block is generated.

        If no new transactions have been added to the pending list and the block
        generation interval has been reached, a block is generated to avoid potential
        deadlock.
        """
        with self.eth_rpc.pending_tx_hashes:
            if len(self.eth_rpc.pending_tx_hashes) >= self.eth_rpc.transactions_per_block:
                self.eth_rpc.generate_block()
            else:
                if (
                    self.last_pending_tx_hashes_count is not None
                    and len(self.eth_rpc.pending_tx_hashes) == self.last_pending_tx_hashes_count
                    and self.i % self.block_generation_interval == 0
                ):
                    # If no new transactions have been added to the pending list,
                    # generate a block to avoid potential deadlock.
                    self.eth_rpc.generate_block()
            self.last_pending_tx_hashes_count = len(self.eth_rpc.pending_tx_hashes)
            self.i += 1


@pytest.fixture(scope="session")
def transactions_per_block(request) -> int:  # noqa: D103
    if transactions_per_block := request.config.getoption("transactions_per_block"):
        return transactions_per_block

    # Get the number of workers for the test
    worker_count_env = os.environ.get("PYTEST_XDIST_WORKER_COUNT")
    if not worker_count_env:
        return 1
    return max(int(worker_count_env), 1)


@pytest.fixture(scope="session")
def chain_id() -> int:
    """
    Returns the chain id where the tests will be executed.
    """
    return 1


@pytest.fixture(autouse=True, scope="session")
def eth_rpc(
    request: pytest.FixtureRequest,
    client: Client,
    base_genesis_header: FixtureHeader,
    base_fork: Fork,
    transactions_per_block: int,
    session_temp_folder: Path,
) -> EthRPC:
    """
    Initialize ethereum RPC client for the execution client under test.
    """
    get_payload_wait_time = request.config.getoption("get_payload_wait_time")
    tx_wait_timeout = request.config.getoption("tx_wait_timeout")
    return EthRPC(
        client=client,
        fork=base_fork,
        base_genesis_header=base_genesis_header,
        transactions_per_block=transactions_per_block,
        session_temp_folder=session_temp_folder,
        get_payload_wait_time=get_payload_wait_time,
        transaction_wait_timeout=tx_wait_timeout,
    )
