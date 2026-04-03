"""
End-to-end tests for the execute remote command.

Each test uses pytester to run an inline test module through the
pytest-execute.ini plugin stack, pointing at a real execution client
spawned via hive.

Requires HIVE_SIMULATOR to be set (e.g. start hive in --dev mode).
"""

import contextlib
import hashlib
import io
import json
import os
import random
import textwrap
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, Generator, List, cast

import pytest
import requests
from filelock import FileLock, Timeout
from hive.simulation import Simulation
from hive.testing import HiveTest, HiveTestResult, HiveTestSuite

from execution_testing.base_types import (
    Account,
    Address,
    EmptyOmmersRoot,
    EmptyTrieRoot,
    Hash,
    Number,
    to_json,
)
from execution_testing.cli.pytest_commands.plugins.consume.simulators.helpers.ruleset import (  # noqa: E501
    ruleset,
)
from execution_testing.fixtures.blockchain import FixtureHeader
from execution_testing.forks import Osaka
from execution_testing.rpc import EngineRPC, EthRPC
from execution_testing.test_types import (
    DETERMINISTIC_FACTORY_ADDRESS,
    DETERMINISTIC_FACTORY_BYTECODE,
    EOA,
    Alloc,
    ChainConfig,
    Environment,
    Requests,
    Transaction,
    Withdrawal,
    compute_deterministic_create2_address,
)
from execution_testing.tools import Initcode
from execution_testing.vm import Op

from ..pre_alloc import AddressStubs
from ..rpc.chain_builder_eth_rpc import ChainBuilderEthRPC, TestingRPC

# Number of seed keys to pre-fund (one per test case)
SEED_KEY_COUNT = 100
SEED_KEY_BALANCE = 10**26

# The fork to test with
TEST_FORK = Osaka


pytestmark = pytest.mark.skipif(
    os.environ.get("HIVE_SIMULATOR") is None,
    reason="HIVE_SIMULATOR not set; start hive in --dev mode to run",
)


@pytest.fixture(scope="module")
def seed_keys(testrun_uid: str) -> List[EOA]:
    """Generate seed keys for each test case."""
    start_index = int.from_bytes(
        hashlib.sha256(testrun_uid.encode()).digest(), byteorder="big"
    )
    return [
        EOA(key=i) for i in range(start_index, start_index + SEED_KEY_COUNT)
    ]


def _build_client_genesis(seed_keys: List[EOA]) -> dict:
    """Build a valid client genesis for the Hive-backed E2E tests."""
    alloc_dict: Dict = {
        DETERMINISTIC_FACTORY_ADDRESS: Account(
            nonce=1, code=DETERMINISTIC_FACTORY_BYTECODE
        ),
    }
    for key in seed_keys:
        alloc_dict[key] = Account(balance=SEED_KEY_BALANCE)

    env = Environment().set_fork_requirements(TEST_FORK)
    assert env.withdrawals is None or len(env.withdrawals) == 0, (
        "withdrawals must be empty at genesis"
    )
    assert (
        env.parent_beacon_block_root is None
        or env.parent_beacon_block_root == Hash(0)
    ), "parent_beacon_block_root must be empty at genesis"

    genesis_alloc = Alloc.merge(
        Alloc.model_validate(TEST_FORK.pre_allocation_blockchain()),
        Alloc(alloc_dict),
    )
    if empty_accounts := genesis_alloc.empty_accounts():
        raise Exception(f"Empty accounts in pre state: {empty_accounts}")

    block_number = 0
    timestamp = 1
    genesis_header = FixtureHeader(
        parent_hash=0,
        ommers_hash=EmptyOmmersRoot,
        fee_recipient=0,
        state_root=genesis_alloc.state_root(),
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
        if TEST_FORK.header_requests_required()
        else None,
        block_access_list_hash=Hash(EmptyTrieRoot)
        if TEST_FORK.header_bal_hash_required()
        else None,
    )

    client_genesis = to_json(genesis_header)
    alloc = to_json(genesis_alloc)
    client_genesis["alloc"] = {
        k.replace("0x", ""): v for k, v in alloc.items()
    }
    return client_genesis


@pytest.fixture(scope="module")
def hive_client_ip(
    seed_keys: List[EOA],
    session_temp_folder: Path,
) -> Generator[str, None, None]:
    """
    Start a hive execution client for the duration of the module.

    Only one process initializes the hive suite and client; the rest
    read the client information from a shared file.  Each process
    registers itself in a counter file, and the last process to
    finish tears down the hive resources.
    """
    hive_info_name = "hive_e2e_client_info"
    hive_info_file = session_temp_folder / hive_info_name
    hive_info_lock = session_temp_folder / f"{hive_info_name}.lock"

    hive_users_name = "hive_e2e_client_users"
    hive_users_file = session_temp_folder / hive_users_name
    hive_users_lock = session_temp_folder / f"{hive_users_name}.lock"

    with FileLock(hive_info_lock):
        if hive_info_file.exists():
            with hive_info_file.open("r") as f:
                hive_info = json.load(f)
        else:
            url = os.environ["HIVE_SIMULATOR"]
            simulator = Simulation(url=url)
            client_type = simulator.client_types()[0]
            client_genesis = _build_client_genesis(seed_keys)

            assert TEST_FORK in ruleset, (
                f"fork '{TEST_FORK}' missing in hive ruleset"
            )
            hive_environment = {
                "HIVE_CHAIN_ID": str(ChainConfig().chain_id),
                "HIVE_FORK_DAO_VOTE": "1",
                "HIVE_NODETYPE": "full",
                **{k: f"{v:d}" for k, v in ruleset[TEST_FORK].items()},
            }
            suite: HiveTestSuite = simulator.start_suite(
                name="eels/execute-remote-e2e",
                description=("E2E tests for execute remote command"),
            )
            test: HiveTest = suite.start_test(
                name="execute-remote-e2e",
                description="E2E test client",
            )

            genesis_json = json.dumps(client_genesis)
            genesis_bytes = genesis_json.encode("utf-8")
            buffered = io.BufferedReader(
                cast(io.RawIOBase, io.BytesIO(genesis_bytes))
            )
            files = {"/genesis.json": buffered}

            client = test.start_client(
                client_type=client_type,
                environment=hive_environment,
                files=files,
            )
            assert client is not None, (
                f"Failed to start hive client ({client_type.name})"
            )

            hive_info = {
                "client_ip": f"{client.ip}",
                "client_url": client.url,
                "client_id": client.id,
                "suite": asdict(suite),
                "test": asdict(test),
            }
            with hive_info_file.open("w") as f:
                json.dump(hive_info, f)

    client_ip = hive_info["client_ip"]

    # Register this process as a user of the hive client.
    with FileLock(hive_users_lock):
        if hive_users_file.exists():
            with hive_users_file.open("r") as f:
                users = int(f.read())
        else:
            users = 0
        users += 1
        with hive_users_file.open("w") as f:
            f.write(str(users))

    yield client_ip

    # Deregister and tear down if this is the last user.
    with FileLock(hive_users_lock):
        with hive_users_file.open("r") as f:
            users = int(f.read())
        users -= 1
        with hive_users_file.open("w") as f:
            f.write(str(users))
        if users == 0:
            with hive_info_file.open("r") as f:
                hive_info = json.load(f)

            # Stop the client.
            stop_url = f"{hive_info['client_url']}/{hive_info['client_id']}"
            requests.delete(stop_url).raise_for_status()

            # End the test.
            test_obj = HiveTest(**hive_info["test"])
            test_obj.end(
                result=HiveTestResult(
                    test_pass=True,
                    details="E2E test completed",
                )
            )

            # End the suite.
            suite_obj = HiveTestSuite(**hive_info["suite"])
            suite_obj.end()

            # Clean up coordination files.
            hive_info_file.unlink(missing_ok=True)
            hive_users_file.unlink(missing_ok=True)


@pytest.fixture(scope="module")
def rpc_endpoint(hive_client_ip: str) -> str:
    """Return the JSON-RPC endpoint of the hive client."""
    return f"http://{hive_client_ip}:8545"


@pytest.fixture(scope="module")
def engine_endpoint(hive_client_ip: str) -> str:
    """Return the engine API endpoint of the hive client."""
    return f"http://{hive_client_ip}:8551"


@pytest.fixture(scope="function")
def chain_builder_eth_rpc(
    rpc_endpoint: str,
    engine_endpoint: str,
    session_temp_folder: Path,
) -> EthRPC:
    """
    Return the chain builder ETH RPC to use for some tests that send
    transactions before the actual execute test starts.
    """
    return ChainBuilderEthRPC(
        rpc_endpoint=rpc_endpoint,
        fork=TEST_FORK,
        engine_rpc=EngineRPC(engine_endpoint),
        session_temp_folder=session_temp_folder,
        get_payload_wait_time=1,
        transaction_wait_timeout=20,
        max_transactions_per_batch=10,
        testing_rpc=TestingRPC(rpc_endpoint),
    )


class KeysPool:
    """
    A pool of keys safe for use across multiple processes.

    Each key is backed by a lock file inside `lock_dir`.  Calling `pop()`
    returns a context manager that:
      1. Blocks until a key is free (no other process holds it).
      2. Yields the EOA.
      3. Releases the lock automatically on exit.
    """

    def __init__(self, *, keys: List[EOA], session_temp_folder: Path) -> None:
        if not keys:
            raise ValueError("Key list must not be empty.")

        self._lock_dir = session_temp_folder / "key_locks"
        self._lock_dir.mkdir(parents=True, exist_ok=True)
        self._pool: Dict[EOA, FileLock] = {
            key: FileLock(self._lock_dir / f"{key}") for key in keys
        }

    @contextlib.contextmanager
    def pop(
        self, poll_interval: float = 0.5, timeout: float | None = None
    ) -> Generator[EOA, None, None]:
        """
        Acquire an available key and yield it as a context manager.
        """
        deadline = None if timeout is None else time.monotonic() + timeout

        while True:
            for key, lock in self._pool.items():
                try:
                    lock.acquire(timeout=0)
                except Timeout:
                    continue

                try:
                    yield key
                finally:
                    lock.release()
                return

            if deadline is not None and time.monotonic() >= deadline:
                raise Timeout(
                    f"No EOA key became available within {timeout}s "
                    f"(pool size: {len(self._pool)})."
                )
            time.sleep(poll_interval)


@pytest.fixture(scope="module", autouse=True)
def keys_pool(session_temp_folder: Path, seed_keys: List[EOA]) -> KeysPool:
    """
    Write all starting set of keys to the session coordinator folder.
    """
    return KeysPool(keys=seed_keys, session_temp_folder=session_temp_folder)


@pytest.fixture()
def test_seed_key(
    keys_pool: KeysPool, chain_builder_eth_rpc: EthRPC
) -> Generator[EOA, None, None]:
    """Return the seed key for the current test."""
    with keys_pool.pop() as key:
        current_nonce = chain_builder_eth_rpc.get_transaction_count(key)
        key.nonce = Number(current_nonce)
        yield key


@pytest.fixture(scope="session")
def fork_name() -> str:
    """Return the fork name string for CLI args."""
    return str(TEST_FORK)


@dataclass(kw_only=True)
class ExecuteRunner:
    """Formatted runner of a test."""

    testdir: pytest.Testdir
    monkeypatch: pytest.MonkeyPatch
    session_temp_folder: Path
    rpc_endpoint: str
    engine_endpoint: str
    test_seed_key: EOA
    fork_name: str

    def run_assert(
        self,
        *,
        test_method: str,
        stubs: AddressStubs | None = None,
        passed: int | None = None,
        failed: int | None = None,
        errors: int | None = None,
    ) -> None:
        """
        Run an inline test module through the execute remote plugin stack.

        Write the test module, copy the ini file, and invoke pytester.
        """
        tests_dir = self.testdir.mkdir("tests")
        test_file = tests_dir.join("test_module.py")
        test_module = (
            "from execution_testing import "
            + "Account, Address, Storage, Transaction, Op\n"
            + textwrap.dedent(test_method)
        )
        test_file.write(textwrap.dedent(test_module))

        self.testdir.copy_example(
            name="src/execution_testing/cli/pytest_commands/"
            "pytest_ini_files/pytest-execute.ini"
        )

        args = [
            "-c",
            "pytest-execute.ini",
            "-v",
            "--fork",
            self.fork_name,
            "--rpc-endpoint",
            self.rpc_endpoint,
            "--engine-endpoint",
            self.engine_endpoint,
            "--use-testing-build-block",
            "--rpc-seed-key",
            str(self.test_seed_key.key),
            "--rpc-chain-id",
            str(ChainConfig().chain_id),
            "--session-sync-folder",
            str(self.session_temp_folder),
            "--engine-jwt-secret",
            "secretsecretsecretsecretsecretse",
            "--no-html",
        ]
        if stubs:
            args.extend(["--address-stubs", stubs.model_dump_json(indent=0)])

        if all(x is None for x in (passed, failed, errors)):
            passed, failed, errors = (1, 0, 0)
        else:
            passed, failed, errors = (
                passed if passed is not None else 0,
                failed if failed is not None else 0,
                errors if errors is not None else 0,
            )
        self.monkeypatch.setenv("PYTEST_XDIST_WORKER_COUNT", "1")
        self.testdir.runpytest(*args).assert_outcomes(
            passed=passed, failed=failed, errors=errors
        )


@pytest.fixture(scope="function")
def execute_runner(
    testdir: pytest.Testdir,
    monkeypatch: pytest.MonkeyPatch,
    session_temp_folder: Path,
    rpc_endpoint: str,
    engine_endpoint: str,
    test_seed_key: EOA,
    fork_name: str,
) -> ExecuteRunner:
    """Return the runner of the test."""
    return ExecuteRunner(
        testdir=testdir,
        monkeypatch=monkeypatch,
        session_temp_folder=session_temp_folder,
        rpc_endpoint=rpc_endpoint,
        engine_endpoint=engine_endpoint,
        test_seed_key=test_seed_key,
        fork_name=fork_name,
    )


@dataclass(kw_only=True)
class ContractDeployer:
    """Formatted runner of a test."""

    chain_builder_eth_rpc: ChainBuilderEthRPC
    test_seed_key: EOA
    salt: int

    def deploy(self, code: str) -> Address:
        """Deploy a contract."""
        bytecode = eval(code, {"Op": Op})
        initcode = Initcode(deploy_code=bytecode)
        tx = Transaction(
            sender=self.test_seed_key,
            to=None,
            gas_limit=1_000_000,
            data=initcode,
        )
        self.chain_builder_eth_rpc.send_wait_transactions([tx])
        contract_address = tx.created_contract
        chain_code = self.chain_builder_eth_rpc.get_code(contract_address)
        assert chain_code == bytecode
        return contract_address

    def deterministic_deploy(self, code: str) -> Address:
        """Deploy a contract to a deterministic address."""
        bytecode = eval(code, {"Op": Op})
        initcode = Initcode(deploy_code=bytecode)
        deploy_address = compute_deterministic_create2_address(
            salt=self.salt, initcode=initcode, fork=TEST_FORK
        )
        chain_code = self.chain_builder_eth_rpc.get_code(deploy_address)
        if chain_code != b"":
            raise Exception(f"Contract already deployed: {deploy_address}")
        tx = Transaction(
            sender=self.test_seed_key,
            to=DETERMINISTIC_FACTORY_ADDRESS,
            gas_limit=1_000_000,
            data=Hash(self.salt) + bytes(initcode),
        )
        self.chain_builder_eth_rpc.send_wait_transactions([tx])
        chain_code = self.chain_builder_eth_rpc.get_code(deploy_address)
        assert chain_code == bytecode
        return deploy_address


@pytest.fixture(scope="function")
def contract_deployer(
    chain_builder_eth_rpc: ChainBuilderEthRPC,
    test_seed_key: EOA,
) -> ContractDeployer:
    """
    Contract deployer for the current test.

    Takes a string bytecode to be passed to `eval` (for convenience)
    and returns the address.
    """
    return ContractDeployer(
        chain_builder_eth_rpc=chain_builder_eth_rpc,
        test_seed_key=test_seed_key,
        salt=random.randint(0, 2**256),
    )


def test_simple_state_test(execute_runner: ExecuteRunner) -> None:
    """Execute a minimal state test against a live client."""
    test_method = """\
        def test_simple(state_test, pre) -> None:
            sender = pre.fund_eoa()
            state_test(
                pre=pre,
                post={{}},
                tx=Transaction(
                    sender=sender,
                    to=None,
                    gas_limit=100_000,
                ),
            )
    """.format()

    execute_runner.run_assert(test_method=test_method)


def test_deploy_contract(execute_runner: ExecuteRunner) -> None:
    """Execute a test that deploys a contract and checks storage."""
    test_method = """\
        def test_deploy(state_test, pre) -> None:
            code = Op.SSTORE(0, 1) + Op.STOP
            contract = pre.deploy_contract(code)
            sender = pre.fund_eoa()
            tx = Transaction(
                sender=sender,
                to=contract,
                gas_limit=100_000,
            )
            state_test(
                pre=pre,
                post={{
                    contract: Account(
                        storage=Storage({{0: 1}}),
                    ),
                }},
                tx=tx,
            )
    """.format()

    execute_runner.run_assert(test_method=test_method)


@pytest.mark.parametrize(
    "already_deployed",
    [
        pytest.param(True, id="already_deployed"),
        pytest.param(False, id="not_deployed"),
    ],
)
def test_deterministic_deploy_contract(
    execute_runner: ExecuteRunner,
    contract_deployer: ContractDeployer,
    test_seed_key: EOA,
    already_deployed: bool,
    chain_builder_eth_rpc: ChainBuilderEthRPC,
) -> None:
    """
    Execute a test that deploys a contract to a deterministic address
    and checks storage.
    """
    # We have to use a different salt because otherwise the multiple
    # parametrization makes different tests have the same contract already
    # deployed.
    code = "Op.SSTORE(0, Op.ADD(Op.SLOAD(0), 1)) + Op.STOP"
    expected_value = 1
    if already_deployed:
        deploy_address = contract_deployer.deterministic_deploy(code)
        # Send tx to increase the storage
        tx = Transaction(
            sender=test_seed_key,
            to=deploy_address,
            gas_limit=100_000,
        )
        chain_builder_eth_rpc.send_wait_transactions([tx])
        expected_value = 2
    test_method = """\
        def test_deploy(state_test, pre) -> None:
            code = {code}
            contract = pre.deterministic_deploy_contract(
                deploy_code=code, salt={salt}
            )
            sender = pre.fund_eoa()
            tx = Transaction(
                sender=sender,
                to=contract,
                gas_limit=100_000,
            )
            state_test(
                pre=pre,
                post={{
                    contract: Account(
                        storage=Storage({{0: {expected_value}}}),
                    ),
                }},
                tx=tx,
            )
    """.format(
        code=code,
        expected_value=expected_value,
        salt=contract_deployer.salt,
    )

    execute_runner.run_assert(test_method=test_method)


def test_multiple_tests_single_module(execute_runner: ExecuteRunner) -> None:
    """Execute multiple tests in a single module."""
    test_method = """\
        def test_one(state_test, pre) -> None:
            sender = pre.fund_eoa()
            state_test(
                pre=pre,
                post={{}},
                tx=Transaction(
                    sender=sender,
                    to=None,
                    gas_limit=100_000,
                ),
            )

        def test_two(state_test, pre) -> None:
            sender = pre.fund_eoa()
            state_test(
                pre=pre,
                post={{}},
                tx=Transaction(
                    sender=sender,
                    to=None,
                    gas_limit=100_000,
                ),
            )
    """.format()

    execute_runner.run_assert(test_method=test_method, passed=2)


def test_fund_address(execute_runner: ExecuteRunner) -> None:
    """Execute a test that uses fund_address for pre-existing addresses."""
    funded_address = "0x1234567890ABCDEF1234567890ABCDEF12345678"
    test_method = """\
        def test_fund(state_test, pre) -> None:
            sender = pre.fund_eoa()
            funded_address = Address({funded_address})
            pre.fund_address(funded_address, 10**18)
            state_test(
                pre=pre,
                post={{
                    funded_address: Account(
                        balance=10**18,
                    ),
                }},
                tx=Transaction(
                    sender=sender,
                    to=None,
                    gas_limit=100_000,
                ),
            )
    """.format(funded_address=funded_address)

    execute_runner.run_assert(test_method=test_method)


def test_fail_fund_address_twice(execute_runner: ExecuteRunner) -> None:
    """
    Execute a test that uses fund_address twice on the same account
    for pre-existing addresses.
    """
    funded_address = "0x1234567890ABCDEF1234567890ABCDEF12345678"
    test_method = """\
        def test_fund(state_test, pre) -> None:
            sender = pre.fund_eoa()
            funded_address = Address({funded_address})
            pre.fund_address(funded_address, 10**18)
            pre.fund_address(funded_address, 10**18)
            state_test(
                pre=pre,
                post={{
                    funded_address: Account(
                        balance=10**18,
                    ),
                }},
                tx=Transaction(
                    sender=sender,
                    to=None,
                    gas_limit=100_000,
                ),
            )
    """.format(funded_address=funded_address)

    execute_runner.run_assert(test_method=test_method, failed=1)


@pytest.mark.parametrize(
    "account_type",
    [
        "funded_eoa",
        "deployed_contract",
        "stubbed_contract",
        "deterministic_contract",
        "deterministic_contract_already_deployed",
    ],
)
def test_fail_fund_account_in_alloc(
    execute_runner: ExecuteRunner,
    account_type: str,
    contract_deployer: ContractDeployer,
) -> None:
    """Execute a test that uses fund_address on an account already in alloc."""
    stubs: AddressStubs | None = None
    code = "Op.SSTORE(0, 1) + Op.STOP"
    match account_type:
        case "funded_eoa":
            account_in_alloc = "pre.fund_eoa(amount=1)"
        case "deployed_contract":
            account_in_alloc = f"pre.deploy_contract({code})"
        case "stubbed_contract":
            stub_name = "stubbed_contract"
            stub_address = contract_deployer.deploy(code)
            stubs = AddressStubs({stub_name: stub_address})
            account_in_alloc = (
                f'pre.deploy_contract({code}, stub="{stub_name}")'
            )
        case "deterministic_contract":
            account_in_alloc = (
                f"pre.deterministic_deploy_contract(deploy_code={code}, "
                f"salt={contract_deployer.salt})"
            )
        case "deterministic_contract_already_deployed":
            contract_deployer.deterministic_deploy(code)
            account_in_alloc = (
                f"pre.deterministic_deploy_contract(deploy_code={code}, "
                f"salt={contract_deployer.salt})"
            )
        case _:
            raise Exception(f"account type not implemented: {account_type}")

    test_method = """\
        def test_fund_pre_deploy(state_test, pre) -> None:
            sender = pre.fund_eoa()
            account_in_alloc = {account_in_alloc}
            pre.fund_address(account_in_alloc, 1)
            state_test(
                pre=pre,
                post={{}},
                tx=Transaction(
                    sender=sender,
                    to=None,
                    gas_limit=100_000,
                ),
            )
    """.format(account_in_alloc=account_in_alloc)

    execute_runner.run_assert(test_method=test_method, stubs=stubs, failed=1)


def test_stubs(
    execute_runner: ExecuteRunner,
    contract_deployer: ContractDeployer,
) -> None:
    """Execute a test that uses stubs for pre-existing contracts."""
    code = "Op.SSTORE(0, 1) + Op.STOP"
    stub_address = contract_deployer.deploy(code)
    stub_name = "stubbed_contract"
    test_method = """\
        def test_stubs(state_test, pre) -> None:
            code = {code}
            contract = pre.deploy_contract(code, stub="{stub_name}")
            assert contract == Address("{stub_address}")
            sender = pre.fund_eoa()
            tx = Transaction(
                sender=sender,
                to=contract,
                gas_limit=100_000,
            )
            state_test(
                pre=pre,
                post={{
                    {stub_address}: Account(
                        storage=Storage({{0: 1}}),
                    ),
                }},
                tx=tx,
            )
    """.format(
        code=code,
        stub_name=stub_name,
        stub_address=f"{stub_address}",
    )

    stubs = AddressStubs({stub_name: stub_address})
    execute_runner.run_assert(test_method=test_method, stubs=stubs)


def test_fail_pre_mutation(execute_runner: ExecuteRunner) -> None:
    """Verify attempting to mutate the pre-allocation results in failure."""
    test_method = """\
        def test_simple(state_test, pre) -> None:
            sender = pre.fund_eoa()
            pre[0x1] = Account()
            state_test(
                pre=pre,
                post={{}},
                tx=Transaction(
                    sender=sender,
                    to=None,
                    gas_limit=100_000,
                ),
            )
    """.format()

    execute_runner.run_assert(test_method=test_method, failed=1)
