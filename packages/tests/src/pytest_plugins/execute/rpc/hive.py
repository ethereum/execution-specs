"""Pytest plugin to run the test-execute in hive-mode."""

import io
import json
from dataclasses import asdict, replace
from pathlib import Path
from random import randint
from typing import Generator, Mapping, Tuple, cast

import pytest
from filelock import FileLock
from hive.client import Client, ClientType
from hive.simulation import Simulation
from hive.testing import HiveTest, HiveTestResult, HiveTestSuite

from ethereum_test_base_types import EmptyOmmersRoot, EmptyTrieRoot, to_json
from ethereum_test_fixtures.blockchain import FixtureHeader
from ethereum_test_forks import Fork
from ethereum_test_rpc import EngineRPC, EthRPC
from ethereum_test_tools import (
    EOA,
    Account,
    Alloc,
    Environment,
    Hash,
    Withdrawal,
)
from ethereum_test_types import ChainConfig, Requests

from ...consume.simulators.helpers.ruleset import ruleset
from .chain_builder_eth_rpc import ChainBuilderEthRPC


def pytest_addoption(parser: pytest.Parser) -> None:
    """Add command-line options to pytest."""
    hive_rpc_group = parser.getgroup(
        "hive_rpc",
        "Arguments defining the hive RPC client properties for the test.",
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


@pytest.hookimpl(trylast=True)
def pytest_configure(config: pytest.Config) -> None:  # noqa: D103
    config.test_suite_scope = "session"  # type: ignore
    config.engine_rpc_supported = True  # type: ignore


@pytest.fixture(scope="session")
def seed_sender(session_temp_folder: Path) -> EOA:
    """Determine the seed sender account for the client's genesis."""
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
def base_pre(
    request: pytest.FixtureRequest,
    seed_sender: EOA,
    worker_count: int,
) -> Alloc:
    """Pre-allocation for the client's genesis."""
    sender_key_initial_balance = request.config.getoption(
        "sender_key_initial_balance"
    )
    return Alloc(
        {
            seed_sender: Account(
                balance=(worker_count * sender_key_initial_balance) + 10**18
            )
        }
    )


@pytest.fixture(scope="session")
def base_pre_genesis(
    session_fork: Fork,
    base_pre: Alloc,
) -> Tuple[Alloc, FixtureHeader]:
    """Create a genesis block from the blockchain test definition."""
    env = Environment().set_fork_requirements(session_fork)
    assert env.withdrawals is None or len(env.withdrawals) == 0, (
        "withdrawals must be empty at genesis"
    )
    assert (
        env.parent_beacon_block_root is None
        or env.parent_beacon_block_root == Hash(0)
    ), "parent_beacon_block_root must be empty at genesis"

    pre_alloc = Alloc.merge(
        Alloc.model_validate(session_fork.pre_allocation_blockchain()),
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
        withdrawals_root=(
            Withdrawal.list_root(env.withdrawals)
            if env.withdrawals is not None
            else None
        ),
        parent_beacon_block_root=env.parent_beacon_block_root,
        requests_hash=Requests()
        if session_fork.header_requests_required(
            block_number=block_number, timestamp=timestamp
        )
        else None,
    )

    return (pre_alloc, genesis)


@pytest.fixture(scope="session")
def client_genesis(base_pre_genesis: Tuple[Alloc, FixtureHeader]) -> dict:
    """
    Convert the fixture's genesis block header and pre-state to a client
    genesis state.
    """
    genesis = to_json(
        base_pre_genesis[1]
    )  # NOTE: to_json() excludes None values
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
def environment(session_fork: Fork, chain_config: ChainConfig) -> dict:
    """
    Define the environment that hive will start the client with using the fork
    rules specific for the simulator.
    """
    assert session_fork in ruleset, (
        f"fork '{session_fork}' missing in hive ruleset"
    )
    return {
        "HIVE_CHAIN_ID": str(chain_config.chain_id),
        "HIVE_FORK_DAO_VOTE": "1",
        "HIVE_NODETYPE": "full",
        **{k: f"{v:d}" for k, v in ruleset[session_fork].items()},
    }


@pytest.fixture(scope="session")
def test_suite_name() -> str:
    """The name of the hive test suite used in this simulator."""
    return "eest/execute, hive mode"


@pytest.fixture(scope="session")
def test_suite_description() -> str:
    """The description of the hive test suite used in this simulator."""
    return "Execute EEST tests using hive endpoint."


@pytest.fixture(autouse=True, scope="session")
def base_hive_test(
    request: pytest.FixtureRequest,
    test_suite: HiveTestSuite,
    session_temp_folder: Path,
) -> Generator[HiveTest, None, None]:
    """
    Test (base) used to deploy the main client to be used throughout all tests.
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
    if request.session.testsfailed > 0:
        test_pass = False
        test_details = "One or more tests have failed"

    with FileLock(users_lock_file):
        with open(users_file, "r") as f:
            users = json.load(f)
        users -= 1
        with open(users_file, "w") as f:
            json.dump(users, f)
        if users == 0:
            test.end(
                result=HiveTestResult(
                    test_pass=test_pass, details=test_details
                )
            )
            base_file.unlink()
            users_file.unlink()


@pytest.fixture(scope="session")
def client_type(simulator: Simulation) -> ClientType:
    """Type of client to be used in the test."""
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
                    client_type=client_type,
                    environment=environment,
                    files=client_files,
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


@pytest.fixture(scope="session")
def engine_rpc(client: Client) -> EngineRPC | None:
    """Return the engine RPC client."""
    return EngineRPC(f"http://{client.ip}:8551")


@pytest.fixture(autouse=True, scope="session")
def eth_rpc(
    request: pytest.FixtureRequest,
    client: Client,
    engine_rpc: EngineRPC,
    session_fork: Fork,
    transactions_per_block: int,
    session_temp_folder: Path,
) -> EthRPC:
    """Initialize ethereum RPC client for the execution client under test."""
    get_payload_wait_time = request.config.getoption("get_payload_wait_time")
    tx_wait_timeout = request.config.getoption("tx_wait_timeout")
    return ChainBuilderEthRPC(
        rpc_endpoint=f"http://{client.ip}:8545",
        fork=session_fork,
        engine_rpc=engine_rpc,
        transactions_per_block=transactions_per_block,
        session_temp_folder=session_temp_folder,
        get_payload_wait_time=get_payload_wait_time,
        transaction_wait_timeout=tx_wait_timeout,
    )
