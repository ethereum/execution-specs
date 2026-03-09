"""Helper class to load and run VM tests."""

from importlib import import_module
from pathlib import Path
from typing import Any, Dict, Generator, List, Tuple

import pytest
from _pytest.config import Config
from _pytest.nodes import Item
from ethereum_rlp import rlp
from ethereum_types.numeric import U64, U256, Uint
from pytest import Collector

from ethereum.crypto.hash import keccak256
from ethereum.utils.hexadecimal import (
    hex_to_bytes,
    hex_to_bytes32,
    hex_to_u256,
    hex_to_uint,
)

from ..hardfork import TestHardfork
from ..stash_keys import desired_forks_key
from .exceptional_test_patterns import exceptional_vm_test_patterns
from .fixtures import Fixture, FixturesFile, FixtureTestItem


def _get_vm_forks() -> List[TestHardfork]:
    """
    Get the list of forks for which VM tests should run.

    VM tests are only run for legacy forks up to Constantinople.
    """
    all_forks = list(TestHardfork.discover())
    constantinople = next(
        f for f in all_forks if f.short_name == "constantinople"
    )
    return [f for f in all_forks if f.criteria <= constantinople.criteria]


VM_FORKS: List[TestHardfork] = _get_vm_forks()


class VmTestLoader:
    """
    All the methods and imports required to run the VM tests.
    """

    def __init__(self, network: str, fork_name: str):
        self.network = network
        self.fork_name = fork_name

        # Import relevant items from fork
        self.fork = self._module("fork")
        self.BlockChain = self.fork.BlockChain
        self.get_last_256_block_hashes = self.fork.get_last_256_block_hashes

        self.state = self._module("state")
        self.State = self.state.State
        self.close_state = self.state.close_state
        self.set_account = self.state.set_account
        self.set_storage = self.state.set_storage
        self.storage_root = self.state.storage_root

        self.fork_types = self._module("fork_types")
        self.Account = self.fork_types.Account
        self.Address = self.fork_types.Address

        self.transactions = self._module("transactions")
        self.Transaction = self.transactions.Transaction

        self.hexadecimal = self._module("utils.hexadecimal")
        self.hex_to_address = self.hexadecimal.hex_to_address

        self.message = self._module("utils.message")
        self.prepare_message = self.message.prepare_message

        self.vm = self._module("vm")
        self.BlockEnvironment = self.vm.BlockEnvironment
        self.TransactionEnvironment = self.vm.TransactionEnvironment

        self.interpreter = self._module("vm.interpreter")
        self.process_message_call = self.interpreter.process_message_call

    def _module(self, name: str) -> Any:
        return import_module(f"ethereum.forks.{self.fork_name}.{name}")

    def run_test_from_dict(self, json_data: Dict[str, Any]) -> None:
        """
        Execute a test case from parsed JSON data and check its post state.
        """
        test_data = self.prepare_test_data(json_data)
        block_env = test_data["block_env"]
        tx_env = test_data["tx_env"]
        tx = test_data["tx"]

        message = self.prepare_message(
            block_env=block_env,
            tx_env=tx_env,
            tx=tx,
        )

        output = self.process_message_call(message)

        if test_data["has_post_state"]:
            assert (
                keccak256(rlp.encode(output.logs))
                == test_data["expected_logs_hash"]
            )
            # We are checking only the storage here and not the whole state,
            # as the balances in the testcases don't change even though
            # some value is transferred along with code invocation.
            # But our evm execution transfers the value as well
            # as executing the code
            for addr in test_data["post_state_addresses"]:
                assert self.storage_root(
                    test_data["expected_post_state"], addr
                ) == self.storage_root(block_env.state, addr)
        else:
            assert output.error is not None
        self.close_state(block_env.state)
        self.close_state(test_data["expected_post_state"])

    def prepare_test_data(self, json_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare test data from parsed JSON.
        """
        block_env = self.json_to_block_env(json_data)

        tx = self.Transaction(
            nonce=U256(0),
            gas_price=hex_to_u256(json_data["exec"]["gasPrice"]),
            gas=hex_to_uint(json_data["exec"]["gas"]),
            to=self.hex_to_address(json_data["exec"]["address"]),
            value=hex_to_u256(json_data["exec"]["value"]),
            data=hex_to_bytes(json_data["exec"]["data"]),
            v=U256(0),
            r=U256(0),
            s=U256(0),
        )

        tx_env = self.TransactionEnvironment(
            origin=self.hex_to_address(json_data["exec"]["caller"]),
            gas_price=tx.gas_price,
            gas=tx.gas,
            index_in_block=Uint(0),
            tx_hash=b"56e81f171bcc55a6ff8345e692c0f86e5b48e01b996cadc001622fb5e363b421",
        )

        return {
            "block_env": block_env,
            "tx_env": tx_env,
            "tx": tx,
            "expected_gas_left": hex_to_u256(json_data.get("gas", "0x64")),
            "expected_logs_hash": hex_to_bytes(json_data.get("logs", "0x00")),
            "expected_post_state": self.json_to_state(
                json_data.get("post", {})
            ),
            "post_state_addresses": self.json_to_addrs(
                json_data.get("post", {})
            ),
            "has_post_state": bool(json_data.get("post", {})),
        }

    def json_to_block_env(self, json_data: Any) -> Any:
        """
        Deserialize a `BlockEnvironment` instance from JSON.
        """
        caller_hex_address = json_data["exec"]["caller"]
        # Some tests don't have the caller state defined in the test case.
        # Hence creating a dummy caller state.
        if caller_hex_address not in json_data["pre"]:
            value = json_data["exec"]["value"]
            dummy_state = self.get_dummy_account_state(value)
            json_data["pre"][caller_hex_address] = dummy_state

        current_state = self.json_to_state(json_data["pre"])

        chain = self.BlockChain(
            blocks=[],
            state=current_state,
            chain_id=U64(1),
        )

        return self.BlockEnvironment(
            chain_id=chain.chain_id,
            state=current_state,
            block_hashes=self.get_last_256_block_hashes(chain),
            coinbase=self.hex_to_address(json_data["env"]["currentCoinbase"]),
            number=hex_to_uint(json_data["env"]["currentNumber"]),
            block_gas_limit=hex_to_uint(json_data["env"]["currentGasLimit"]),
            time=hex_to_u256(json_data["env"]["currentTimestamp"]),
            difficulty=hex_to_uint(json_data["env"]["currentDifficulty"]),
        )

    def json_to_state(self, raw: Any) -> Any:
        """
        Deserialize a `State` from JSON.
        """
        state = self.State()
        for addr_hex, acc_state in raw.items():
            addr = self.hex_to_address(addr_hex)
            account = self.Account(
                nonce=hex_to_uint(acc_state.get("nonce", "0x0")),
                balance=U256(hex_to_uint(acc_state.get("balance", "0x0"))),
                code=hex_to_bytes(acc_state.get("code", "")),
            )
            self.set_account(state, addr, account)

            for k, v in acc_state.get("storage", {}).items():
                self.set_storage(
                    state,
                    addr,
                    hex_to_bytes32(k),
                    U256.from_be_bytes(hex_to_bytes32(v)),
                )

        return state

    def json_to_addrs(self, raw: Any) -> List[Any]:
        """
        Deserialize a list of `Address` from JSON.
        """
        addrs = []
        for addr_hex in raw:
            addrs.append(self.hex_to_address(addr_hex))
        return addrs

    def get_dummy_account_state(self, min_balance: str) -> Any:
        """
        Initial state for the dummy account.
        """
        # dummy account balance is the min balance needed plus 1 eth for gas
        # cost
        account_balance = hex_to_uint(min_balance) + Uint(10**18)

        return {
            "balance": hex(account_balance),
            "code": "",
            "nonce": "0x00",
            "storage": {},
        }


class VmTest(FixtureTestItem):
    """Single VM test case item for a specific fork."""

    fork_name: str
    eels_fork: str

    def __init__(
        self,
        *args: Any,
        fork_name: str,
        eels_fork: str,
        **kwargs: Any,
    ) -> None:
        """Initialize a single VM test case item."""
        super().__init__(*args, **kwargs)
        self.fork_name = fork_name
        self.eels_fork = eels_fork
        self.add_marker(pytest.mark.fork(self.fork_name))
        self.add_marker("vm_test")

        # Mark tests with exceptional markers
        test_patterns = exceptional_vm_test_patterns(fork_name, eels_fork)
        if any(x.search(self.nodeid) for x in test_patterns.slow):
            self.add_marker("slow")

    @property
    def vm_test_fixture(self) -> "VmTestFixture":
        """Return the VM test fixture this test belongs to."""
        parent = self.parent
        assert parent is not None
        assert isinstance(parent, VmTestFixture)
        return parent

    @property
    def test_key(self) -> str:
        """Return the key of the VM test fixture in the fixture file."""
        return self.vm_test_fixture.test_key

    @property
    def fixtures_file(self) -> FixturesFile:
        """Fixtures file from which the test fixture was collected."""
        return self.vm_test_fixture.fixtures_file

    @property
    def test_dict(self) -> Dict[str, Any]:
        """Load test from disk."""
        loaded_file = self.fixtures_file.data
        return loaded_file[self.test_key]

    def runtest(self) -> None:
        """Run a VM test from JSON test case data."""
        loader = VmTestLoader(self.fork_name, self.eels_fork)
        loader.run_test_from_dict(self.test_dict)

    def reportinfo(self) -> Tuple[Path, int, str]:
        """Return information for test reporting."""
        return self.path, 1, self.name


class VmTestFixture(Fixture, Collector):
    """
    VM test fixture from a JSON file that yields test items for each
    supported fork.
    """

    @classmethod
    def is_format(cls, test_dict: Dict[str, Any]) -> bool:
        """Return true if the object can be parsed as a VM test fixture."""
        # VM tests have exec, env, and pre keys
        if "exec" not in test_dict:
            return False
        if "env" not in test_dict:
            return False
        if "pre" not in test_dict:
            return False
        if "logs" not in test_dict:
            return False
        # Make sure it's not a state test (which has "transaction" and "post")
        if "transaction" in test_dict:
            return False
        return True

    @property
    def fixtures_file(self) -> FixturesFile:
        """Fixtures file from which the test fixture was collected."""
        parent = self.parent
        assert parent is not None
        assert isinstance(parent, FixturesFile)
        return parent

    @property
    def test_dict(self) -> Dict[str, Any]:
        """Load test from disk."""
        loaded_file = self.fixtures_file.data
        return loaded_file[self.test_key]

    def collect(self) -> Generator[Item | Collector, None, None]:
        """Collect VM test cases for each supported fork."""
        desired_forks: List[str] = self.config.stash.get(desired_forks_key, [])

        for fork in VM_FORKS:
            if fork.json_test_name not in desired_forks:
                continue
            yield VmTest.from_parent(
                parent=self,
                name=fork.json_test_name,
                fork_name=fork.json_test_name,
                eels_fork=fork.short_name,
            )

    @classmethod
    def has_desired_fork(
        cls,
        test_dict: Dict[str, Any],  # noqa: ARG003
        config: Config,
    ) -> bool:
        """
        Check if any of the VM test forks are in the desired forks list.
        """
        desired_forks = config.stash.get(desired_forks_key, None)
        if desired_forks is None:
            return True

        # Check if any VM fork is in the desired forks
        for fork in VM_FORKS:
            if fork.json_test_name in desired_forks:
                return True
        return False
