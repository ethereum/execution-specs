import json
import os
from pathlib import Path

import pytest

from evm_block_builder import BlockBuilder, EvmBlockBuilder

FIXTURES_ROOT = Path(os.path.join("tests", "evm_block_builder", "fixtures"))


@pytest.mark.parametrize("b11r", [EvmBlockBuilder()])
def test_evm_simple(b11r: BlockBuilder) -> None:

    for test_dir in os.listdir(path=FIXTURES_ROOT):
        env_path = Path(FIXTURES_ROOT, test_dir, "header.json")
        txs_path = Path(FIXTURES_ROOT, test_dir, "txs.rlp")
        ommers_path = Path(FIXTURES_ROOT, test_dir, "ommers.json")
        expected_path = Path(FIXTURES_ROOT, test_dir, "exp.json")

        with open(env_path, "r") as env, open(txs_path, "r") as txs, open(
            ommers_path, "r"
        ) as ommers, open(expected_path, "r") as exp:
            env = json.load(env)
            txs = json.load(txs)
            ommers = json.load(ommers)
            expected = json.load(exp)

            (rlp, h) = b11r.build(env, txs, ommers, None)
            assert rlp == expected.get("rlp")
            assert h == expected.get("hash")
