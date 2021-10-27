import json
import os
from pathlib import Path

from ethereum_evm_t8n import TransitionTool

FIXTURES_ROOT = Path("tests/ethereum_evm_t8n/fixtures")


def test_simple() -> None:
    t8n = TransitionTool()

    for test_dir in os.listdir(path=FIXTURES_ROOT):
        alloc_path = Path(FIXTURES_ROOT, test_dir, "alloc.json")
        txs_path = Path(FIXTURES_ROOT, test_dir, "txs.json")
        env_path = Path(FIXTURES_ROOT, test_dir, "env.json")
        expected_path = Path(FIXTURES_ROOT, test_dir, "exp.json")

        with open(alloc_path, "r") as alloc, open(txs_path, "r") as txs, open(
            env_path, "r"
        ) as env, open(expected_path, "r") as exp:
            alloc = json.load(alloc)
            txs = json.load(txs)
            env = json.load(env)
            expected = json.load(exp)

            (alloc, result) = t8n.evaluate(alloc, txs, env)
            assert alloc == expected.get("alloc")
            assert result == expected.get("result")
