import json
import os
from pathlib import Path
from typing import Dict, Optional

import pytest

from evm_transition_tool import EvmTransitionTool, TransitionTool

FIXTURES_ROOT = Path(os.path.join("tests", "evm_transition_tool", "fixtures"))


class TestEnv:
    base_fee: Optional[int]

    def __init__(self, base_fee: Optional[int] = None):
        self.base_fee = base_fee


@pytest.mark.parametrize("t8n", [EvmTransitionTool()])
@pytest.mark.parametrize("fork", ["London", "Istanbul"])
@pytest.mark.parametrize(
    "alloc,env,hash",
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
            TestEnv(7),
            "0x51e7c7508e76dca0",
        ),
        (
            {
                "0x1000000000000000000000000000000000000000": {
                    "balance": "0x0BA1A9CE0BA1A9CE",
                },
            },
            TestEnv(),
            "0x51e7c7508e76dca0",
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
            TestEnv(),
            "0x37c2dedbdea6b3af",
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
            TestEnv(),
            "0x096122e88929baec",
        ),
    ],
)
def test_calc_state_root(
    t8n: TransitionTool, fork: str, alloc: Dict, env: TestEnv, hash: str
) -> None:
    assert t8n.calc_state_root(env, alloc, fork).startswith(hash)


@pytest.mark.parametrize("t8n", [EvmTransitionTool()])
@pytest.mark.parametrize("test_dir", os.listdir(path=FIXTURES_ROOT))
def test_evm_t8n(t8n: TransitionTool, test_dir: str) -> None:

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
        env = json.load(env)
        expected = json.load(exp)

        (alloc, result) = t8n.evaluate(alloc, txs, env, "Berlin")
        print(result)
        assert alloc == expected.get("alloc")
        assert result == expected.get("result")
