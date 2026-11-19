"""Tests for resolving the `--state.fork` name of the evm tools."""

import json
from io import StringIO
from pathlib import Path
from types import SimpleNamespace

import pytest
from ethereum_spec_tools.forks import Hardfork
from ethereum_spec_tools.utils import find_fork

from execution_testing.evm_tools import main

pytestmark = pytest.mark.evm_tools

BPO_FORKS = ("BPO1", "BPO2", "BPO3", "BPO4", "BPO5")


@pytest.mark.parametrize("fork_name", BPO_FORKS)
def test_find_fork_resolves_bpo_fork_module(fork_name: str) -> None:
    """Resolve every BPO fork name to its own spec module."""
    options = SimpleNamespace(state_fork=fork_name, input_env="stdin")
    stdin = {"env": {"currentNumber": "0x1"}}
    fork, fork_block = find_fork(Hardfork.discover(), options, stdin)
    assert fork.short_name == fork_name.lower()
    assert fork_block is None


@pytest.mark.parametrize("fork_name", BPO_FORKS)
def test_t8n_applies_bpo_blob_target(fork_name: str, tmp_path: Path) -> None:
    """
    Derive the excess blob gas with the blob target of the BPO fork.

    The parent used ten blobs: above the Osaka target of six, but below
    the target of fourteen that BPO2 onwards set. BPO1 sets a target of
    ten, so every BPO fork leaves no excess blob gas.
    """
    env = {
        "currentCoinbase": "0x" + "00" * 20,
        "currentGasLimit": "0x1000000",
        "currentNumber": "0x1",
        "currentTimestamp": "0x1000",
        "currentRandom": "0x" + "00" * 32,
        "currentBaseFee": "0x7",
        "parentBaseFee": "0x7",
        "parentBeaconBlockRoot": "0x" + "00" * 32,
        "withdrawals": [],
        "blockHashes": {"0": "0x" + "11" * 32},
        "parentExcessBlobGas": "0x0",
        "parentBlobGasUsed": hex(10 * 2**17),
    }
    out = StringIO()
    exit_code = main(
        args=[
            "t8n",
            "--input.alloc=stdin",
            "--input.env=stdin",
            "--input.txs=stdin",
            "--output.result=stdout",
            "--output.alloc=stdout",
            f"--output.basedir={tmp_path}",
            f"--state.fork={fork_name}",
        ],
        out_file=out,
        in_file=StringIO(json.dumps({"alloc": {}, "env": env, "txs": []})),
    )
    assert exit_code == 0
    result = json.loads(out.getvalue())["result"]
    assert int(result["currentExcessBlobGas"], 16) == 0
