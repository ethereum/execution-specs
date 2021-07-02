import json
import os
from typing import Any

from ethereum.base_types import U256, Uint
from ethereum.crypto import keccak256
from ethereum.frontier import rlp
from ethereum.frontier.eth_types import Account, State
from ethereum.frontier.vm import Environment
from ethereum.frontier.vm.interpreter import process_call
from tests.frontier.helpers import (
    hex2address,
    hex2bytes,
    hex2bytes32,
    hex2u256,
    hex2uint,
)


def run_test(test_dir: str, test_file: str) -> None:
    test_data = load_test(test_dir, test_file)
    target = test_data["target"]
    env = test_data["env"]

    gas_left, logs = process_call(
        caller=test_data["caller"],
        target=target,
        data=test_data["data"],
        value=test_data["value"],
        gas=test_data["gas"],
        depth=test_data["depth"],
        env=env,
    )

    assert gas_left == test_data["expected_gas_left"]
    assert keccak256(rlp.encode(logs)) == test_data["expected_logs_hash"]
    # We are checking only the storage here and not the whole state, as the
    # balances in the testcases don't change even though some value is
    # transferred along with code invokation. But our evm execution transfers
    # the value as well as executing the code.
    assert (
        env.state[target].storage
        == test_data["expected_post_state"][target].storage
    )


def load_test(test_dir: str, test_file: str) -> Any:
    test_name = os.path.splitext(test_file)[0]
    path = os.path.join(test_dir, test_file)
    with open(path, "r") as fp:
        json_data = json.load(fp)[test_name]

    env = json_to_env(json_data)

    return {
        "caller": hex2address(json_data["exec"]["caller"]),
        "target": hex2address(json_data["exec"]["address"]),
        "data": hex2bytes(json_data["exec"]["data"]),
        "value": hex2u256(json_data["exec"]["value"]),
        "gas": hex2u256(json_data["exec"]["gas"]),
        "depth": Uint(0),
        "env": env,
        "expected_gas_left": hex2u256(json_data.get("gas", "0x64")),
        "expected_logs_hash": hex2bytes(json_data.get("logs", "0x00")),
        "expected_post_state": json_to_state(json_data.get("post", {})),
    }


def json_to_env(json_data: Any) -> Environment:
    caller_hex_address = json_data["exec"]["caller"]
    # Some tests don't have the caller state defined in the test case. Hence
    # creating a dummy caller state.
    if caller_hex_address not in json_data["pre"]:
        value = json_data["exec"]["value"]
        json_data["pre"][caller_hex_address] = get_dummy_account_state(value)

    current_state = json_to_state(json_data["pre"])

    return Environment(
        caller=hex2address(json_data["exec"]["caller"]),
        origin=hex2address(json_data["exec"]["origin"]),
        block_hashes=[],
        coinbase=hex2address(json_data["env"]["currentCoinbase"]),
        number=hex2uint(json_data["env"]["currentNumber"]),
        gas_limit=hex2uint(json_data["env"]["currentGasLimit"]),
        gas_price=hex2u256(json_data["exec"]["gasPrice"]),
        time=hex2u256(json_data["env"]["currentTimestamp"]),
        difficulty=hex2uint(json_data["env"]["currentDifficulty"]),
        state=current_state,
    )


def json_to_state(raw: Any) -> State:
    state = {}
    for (addr, acc_state) in raw.items():
        account = Account(
            nonce=hex2uint(acc_state.get("nonce", "0x0")),
            balance=hex2uint(acc_state.get("balance", "0x0")),
            code=hex2bytes(acc_state.get("code", "")),
            storage={},
        )

        for (k, v) in acc_state.get("storage", {}).items():
            account.storage[hex2bytes32(k)] = U256.from_be_bytes(
                hex2bytes32(v)
            )

        state[hex2address(addr)] = account

    return state


def get_dummy_account_state(min_balance: str) -> Any:
    # dummy account balance is the min balance needed plus 1 eth for gas
    # cost
    account_balance = hex2uint(min_balance) + (10 ** 18)

    return {
        "balance": hex(account_balance),
        "code": "",
        "nonce": "0x00",
        "storage": {},
    }
