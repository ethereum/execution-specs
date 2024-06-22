import json  # noqa: D100
import os
from pathlib import Path
from shutil import which
from typing import Dict, List

import pytest
from pydantic import TypeAdapter

from ethereum_test_base_types import to_json
from ethereum_test_forks import Berlin, Fork, Istanbul, London
from ethereum_test_types import Alloc, Environment, Transaction
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
    assert Alloc(alloc).state_root().startswith(hash)


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


transaction_type_adapter = TypeAdapter(List[Transaction])


@pytest.fixture
def alloc(test_dir: str) -> Alloc:  # noqa: D103
    alloc_path = Path(FIXTURES_ROOT, test_dir, "alloc.json")
    with open(alloc_path, "r") as f:
        return Alloc.model_validate_json(f.read())


@pytest.fixture
def txs(test_dir: str) -> List[Transaction]:  # noqa: D103
    txs_path = Path(FIXTURES_ROOT, test_dir, "txs.json")
    with open(txs_path, "r") as f:
        return transaction_type_adapter.validate_json(f.read())


@pytest.fixture
def env(test_dir: str) -> Environment:  # noqa: D103
    env_path = Path(FIXTURES_ROOT, test_dir, "env.json")
    with open(env_path, "r") as f:
        return Environment.model_validate_json(f.read())


@pytest.mark.parametrize("t8n", [GethTransitionTool()])
@pytest.mark.parametrize("test_dir", os.listdir(path=FIXTURES_ROOT))
def test_evm_t8n(  # noqa: D103
    t8n: TransitionTool,
    alloc: Alloc,
    txs: List[Transaction],
    env: Environment,
    test_dir: str,
) -> None:
    expected_path = Path(FIXTURES_ROOT, test_dir, "exp.json")

    with open(expected_path, "r") as exp:
        expected = json.load(exp)

        t8n_output = t8n.evaluate(
            alloc=alloc,
            txs=txs,
            env=env,
            fork=Berlin,
        )
        assert to_json(t8n_output.alloc) == expected.get("alloc")
        assert to_json(t8n_output.result) == expected.get("result")
