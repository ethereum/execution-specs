import json
import os
from typing import Any

import pytest

from ethereum.base_types import U256, Uint
from ethereum.crypto import keccak256
from ethereum.frontier import rlp
from ethereum.frontier.eth_types import Account, State
from ethereum.frontier.vm import Environment
from ethereum.frontier.vm.interpreter import process_call

from ..helpers import hex2address, hex2bytes, hex2bytes32, hex2u256, hex2uint


@pytest.mark.parametrize(
    "test_file",
    [
        "add0.json",
        "add1.json",
        "add2.json",
        "add3.json",
        "add4.json",
    ],
)
def test_add(test_file: str) -> None:
    run_test(test_file)


@pytest.mark.parametrize(
    "test_file",
    [
        "sub0.json",
        "sub1.json",
        "sub2.json",
        "sub3.json",
        "sub4.json",
    ],
)
def test_sub(test_file: str) -> None:
    run_test(test_file)


@pytest.mark.parametrize(
    "test_file",
    [
        "mul0.json",
        "mul1.json",
        "mul2.json",
        "mul3.json",
        "mul4.json",
        "mul5.json",
        "mul6.json",
        # TODO: Uncomment mul7.json once MLOAD, MSTORE is implemented
        # "mul7.json",
    ],
)
def test_mul(test_file: str) -> None:
    run_test(test_file)


@pytest.mark.parametrize(
    "test_file",
    [
        # TODO: Uncomment div1.json file once MSTORE is implemented
        # "div1.json",
        "divBoostBug.json",
        "divByNonZero0.json",
        "divByNonZero1.json",
        "divByNonZero2.json",
        "divByNonZero3.json",
        "divByZero.json",
        "divByZero_2.json",
    ],
)
def test_div(test_file: str) -> None:
    run_test(test_file)


@pytest.mark.parametrize(
    "test_file",
    [
        "sdiv0.json",
        "sdiv1.json",
        "sdiv2.json",
        "sdiv3.json",
        "sdiv4.json",
        "sdiv5.json",
        "sdiv6.json",
        "sdiv7.json",
        "sdiv8.json",
        "sdiv9.json",
        "sdivByZero0.json",
        "sdivByZero1.json",
        "sdivByZero2.json",
        "sdiv_i256min.json",
        "sdiv_i256min2.json",
        "sdiv_i256min3.json",
        # TODO: Run sdiv_dejavu.json once DUP series has been implemented
        # "sdiv_dejavu.json",
    ],
)
def test_sdiv(test_file: str) -> None:
    run_test(test_file)


@pytest.mark.parametrize(
    "test_file",
    [
        "mod0.json",
        "mod1.json",
        "mod2.json",
        "mod3.json",
        "mod4.json",
        "modByZero.json",
    ],
)
def test_mod(test_file: str) -> None:
    run_test(test_file)


@pytest.mark.parametrize(
    "test_file",
    [
        "smod0.json",
        "smod1.json",
        "smod2.json",
        "smod3.json",
        "smod4.json",
        "smod5.json",
        "smod6.json",
        "smod7.json",
        "smod8_byZero.json",
        "smod_i256min1.json",
        "smod_i256min2.json",
    ],
)
def test_smod(test_file: str) -> None:
    run_test(test_file)


@pytest.mark.parametrize(
    "test_file",
    [
        "addmod0.json",
        "addmod1.json",
        "addmod1_overflow2.json",
        "addmod1_overflow3.json",
        "addmod1_overflow4.json",
        "addmod1_overflowDiff.json",
        "addmod2.json",
        # TODO: Test files 'addmod2_1.json', 'addmod3_0.json' after implementing EQ
        # TODO: Test file 'addmod2_0.json' after implementing EQ
        # "addmod2_0.json",
        # "addmod2_1.json",
        "addmod3.json",
        # "addmod3_0.json",
    ],
)
def test_addmod(test_file: str) -> None:
    run_test(test_file)


@pytest.mark.parametrize(
    "test_file",
    [
        "mulmod0.json",
        "mulmod1.json",
        "mulmod1_overflow.json",
        "mulmod1_overflow2.json",
        "mulmod1_overflow3.json",
        "mulmod1_overflow4.json",
        "mulmod2.json",
        # TODO: Test files 'mulmod2_1.json', 'mulmod3_0.json' after implementing EQ
        # TODO: Test file 'mulmod2_0.json' after implementing SMOD
        # TODO: Test file 'mulmod4.json' after implementing MSTORE8
        # "mulmod2_0.json",
        # "mulmod2_1.json",
        "mulmod3.json",
        # "mulmod3_0.json",
        # "mulmod4.json",
    ],
)
def test_mulmod(test_file: str) -> None:
    run_test(test_file)


@pytest.mark.parametrize(
    "test_file",
    [
        "exp0.json",
        "exp1.json",
        "exp2.json",
        "exp3.json",
        "exp4.json",
        "exp5.json",
        "exp6.json",
        "exp7.json",
        "exp8.json",
        # TODO: Run expXY.json, expXY_success.json when CALLDATALOAD is implemented
        # "expXY.json",
        # "expXY_success.json",
    ],
)
def test_exp(test_file: str) -> None:
    run_test(test_file)


@pytest.mark.parametrize("exponent", ([2, 4, 8, 16, 32, 64, 128, 256]))
def test_exp_power_2(exponent: int) -> None:
    run_test(f"expPowerOf2_{exponent}.json")


def test_exp_power_256() -> None:
    for i in range(1, 34):
        run_test(f"expPowerOf256_{i}.json")

    for i in range(34):
        run_test(f"expPowerOf256Of256_{i}.json")


@pytest.mark.parametrize(
    "test_file",
    [
        "signextend_0_BigByte.json",
        "signextend_00.json",
        "signextend_AlmostBiggestByte.json",
        "signextend_BigByte_0.json",
        "signextend_BigByteBigByte.json",
        "signextend_BigBytePlus1_2.json",
        "signextend_bigBytePlus1.json",
        "signextend_BitIsNotSet.json",
        "signextend_BitIsNotSetInHigherByte.json",
        "signextend_bitIsSet.json",
        "signextend_BitIsSetInHigherByte.json",
        # TODO: Run the below commented test after implementing JUMP opcode
        # "signextend_Overflow_dj42.json",
        "signextendInvalidByteNumber.json",
    ],
)
def test_signextend(test_file: str) -> None:
    run_test(test_file)


def test_stop() -> None:
    run_test("stop.json")


#
# Test helpers
#
def run_test(test_file: str) -> None:
    test_data = load_test(test_file)
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


def load_test(test_file: str) -> Any:
    test_name = os.path.splitext(test_file)[0]
    path = os.path.join(
        "tests/fixtures/LegacyTests/Constantinople/VMTests/vmArithmeticTest/",
        test_file,
    )
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
        "expected_gas_left": hex2u256(json_data["gas"]),
        "expected_logs_hash": hex2bytes(json_data["logs"]),
        "expected_post_state": json_to_state(json_data["post"]),
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
