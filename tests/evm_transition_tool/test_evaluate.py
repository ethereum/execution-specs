import json
import os
from pathlib import Path

from evm_transition_tool import TransitionTool

FIXTURES_ROOT = Path("tests/evm_transition_tool/fixtures")


def test_t8n() -> None:
    t8n = TransitionTool()

    for test_dir in os.listdir(path=FIXTURES_ROOT):
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
