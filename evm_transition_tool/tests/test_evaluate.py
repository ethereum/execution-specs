import json  # noqa: D100
import os
from pathlib import Path
from shutil import which
from typing import Dict

import pytest

from ethereum_test_forks import Berlin, Fork, Istanbul, London
from evm_transition_tool import GethTransitionTool, TransitionTool

FIXTURES_ROOT = Path(os.path.join("src", "evm_transition_tool", "tests", "fixtures"))


@pytest.mark.parametrize("t8n", [GethTransitionTool()])
@pytest.mark.parametrize("fork", [London, Istanbul])
@pytest.mark.parametrize(
    "alloc,base_fee,hash",
    [
        (
            {
                "0x1000000000000000000000000000000000000000": {
                    "balance": "0x0BA1A9CE0BA1A9CE",
                    "code": "0x",
                    "nonce": "0",
                    "storage": {},
                },
            },
            7,
            bytes.fromhex("51e7c7508e76dca0"),
        ),
        (
            {
                "0x1000000000000000000000000000000000000000": {
                    "balance": "0x0BA1A9CE0BA1A9CE",
                },
            },
            None,
            bytes.fromhex("51e7c7508e76dca0"),
        ),
        (
            {
                "0x1000000000000000000000000000000000000000": {
                    "balance": "0x0BA1A9CE0BA1A9CE",
                    "code": "0x",
                    "nonce": "1",
                    "storage": {},
                },
            },
            None,
            bytes.fromhex("37c2dedbdea6b3af"),
        ),
        (
            {
                "0x1000000000000000000000000000000000000000": {
                    "balance": "0",
                    "storage": {
                        "0x01": "0x01",
                    },
                },
            },
            None,
            bytes.fromhex("096122e88929baec"),
        ),
    ],
)
def test_calc_state_root(  # noqa: D103
    t8n: TransitionTool,
    fork: Fork,
    alloc: Dict,
    base_fee: int | None,
    hash: bytes,
) -> None:
    class TestEnv:
        base_fee: int | None

    env = TestEnv()
    env.base_fee = base_fee
    assert t8n.calc_state_root(alloc=alloc, fork=fork).startswith(hash)


@pytest.mark.parametrize("evm_tool", [GethTransitionTool])
@pytest.mark.parametrize("binary_arg", ["no_binary_arg", "path_type", "str_type"])
def test_evm_tool_binary_arg(evm_tool, binary_arg):  # noqa: D103
    if binary_arg == "no_binary_arg":
        evm_tool().version()
        return
    elif binary_arg == "path_type":
        evm_bin = which("evm")
        if not evm_bin:
            # typing: Path can not take None; but if it is None, we may as well fail explicitly.
            raise Exception("Failed to find 'evm' in the PATH via which")
        evm_tool(binary=Path(evm_bin)).version()
        return
    elif binary_arg == "str_type":
        evm_tool(binary=str(which("evm"))).version()
        return
    raise Exception("unknown test parameter")


@pytest.mark.parametrize("t8n", [GethTransitionTool()])
@pytest.mark.parametrize("test_dir", os.listdir(path=FIXTURES_ROOT))
def test_evm_t8n(t8n: TransitionTool, test_dir: str) -> None:  # noqa: D103
    alloc_path = Path(FIXTURES_ROOT, test_dir, "alloc.json")
    txs_path = Path(FIXTURES_ROOT, test_dir, "txs.json")
    env_path = Path(FIXTURES_ROOT, test_dir, "env.json")
    expected_path = Path(FIXTURES_ROOT, test_dir, "exp.json")

    with open(alloc_path, "r") as alloc, open(txs_path, "r") as txs, open(
        env_path, "r"
    ) as env, open(expected_path, "r") as exp:
        print(expected_path)
        alloc = json.load(alloc)
        txs = json.load(txs)
        env_json = json.load(env)
        expected = json.load(exp)

        result_alloc, result = t8n.evaluate(
            alloc=alloc,
            txs=txs,
            env=env_json,
            fork_name=Berlin.fork(
                block_number=int(env_json["currentNumber"], 0),
                timestamp=int(env_json["currentTimestamp"], 0),
            ),
        )
        print(result)
        print(expected.get("result"))
        assert result_alloc == expected.get("alloc")
        assert result == expected.get("result")
