import json
import os
from importlib import import_module
from typing import Any, List

from ethereum_rlp import rlp
from ethereum_types.numeric import U64, U256, Uint

from ethereum.crypto.hash import keccak256
from ethereum.utils.hexadecimal import (
    hex_to_bytes,
    hex_to_bytes32,
    hex_to_u256,
    hex_to_uint,
)
from ethereum.trace import BaseEvmTracer

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
        return import_module(f"ethereum.{self.fork_name}.{name}")

    def run_test(
        self, test_dir: str, test_file: str, check_gas_left: bool = True
    ) -> None:
        """
        Execute a test case and check its post state.
        """
        test_data = self.load_test(test_dir, test_file)
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
            if check_gas_left:
                assert output.gas_left == test_data["expected_gas_left"]
            assert (
                keccak256(rlp.encode(output.logs))
                == test_data["expected_logs_hash"]
            )
            # We are checking only the storage here and not the whole state, as the
            # balances in the testcases don't change even though some value is
            # transferred along with code invocation. But our evm execution transfers
            # the value as well as executing the code
            for addr in test_data["post_state_addresses"]:
                assert self.storage_root(
                    test_data["expected_post_state"], addr
                ) == self.storage_root(block_env.state, addr)
        else:
            assert output.error is not None
        self.close_state(block_env.state)
        self.close_state(test_data["expected_post_state"])

    def load_test(self, test_dir: str, test_file: str) -> Any:
        """
        Read tests from a file.
        """
        test_name = os.path.splitext(test_file)[0]
        path = os.path.join(test_dir, test_file)
        with open(path, "r") as fp:
            json_data = json.load(fp)[test_name]

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
            tracer=BaseEvmTracer(),
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
        # Some tests don't have the caller state defined in the test case. Hence
        # creating a dummy caller state.
        if caller_hex_address not in json_data["pre"]:
            value = json_data["exec"]["value"]
            json_data["pre"][
                caller_hex_address
            ] = self.get_dummy_account_state(value)

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

            self.set_account(state, addr, account)

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
