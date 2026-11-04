"""Tests for build_deploytx_transactions, dispatched via the wallet pool."""

from typing import Any, Callable, Dict

import pytest

from execution_testing.cli.pytest_commands.plugins.spamoor.wallet_pool import (
    WalletPool,
)

from .helpers import build_deploytx_transactions
from .pool_runner import submit_pool_workload


@pytest.mark.spamoor
def test_deploytx_default_bytecode(
    spamoor_config: Dict[str, Any],
    spamoor_rpc_client: Callable[[str, list], Any],
    spamoor_wallet_pool: WalletPool,
) -> None:
    """Submit contract-creation txs carrying the default bytecode."""
    txs = build_deploytx_transactions(
        count=spamoor_config["count"],
        bytecodes=spamoor_config["bytecodes"],
        bytecodes_file=spamoor_config["bytecodes_file"],
        gas_limit=spamoor_config["gas_limit"],
        basefee=spamoor_config["basefee"],
        tip_fee=spamoor_config["tip_fee"],
        throughput=spamoor_config["throughput"],
        from_addr=None,
        private_key=None,
        rpc_client=None,
    )

    assert len(txs) == spamoor_config["count"]
    for tx in txs:
        assert tx["type"] == 2
        assert tx["to"] == ""
        assert tx["value"] == 0
        assert tx["data"].startswith("0x")
    if (
        not spamoor_config["bytecodes"]
        and not spamoor_config["bytecodes_file"]
    ):
        assert txs[0]["data"] == "0x6001600055"

    submit_pool_workload(
        spamoor_config=spamoor_config,
        rpc_client=spamoor_rpc_client,
        pool=spamoor_wallet_pool,
        tx_dicts=txs,
    )


@pytest.mark.spamoor
def test_deploytx_cycles_bytecode_list(
    spamoor_config: Dict[str, Any],
    spamoor_rpc_client: Callable[[str, list], Any],
) -> None:
    """Cycling over a bytecode list is deterministic — shape check only."""
    txs = build_deploytx_transactions(
        count=max(3, spamoor_config["count"]),
        bytecodes="0x6001600055,0x60ff60005255",
        bytecodes_file="",
        gas_limit=spamoor_config["gas_limit"],
        basefee=spamoor_config["basefee"],
        tip_fee=spamoor_config["tip_fee"],
        throughput=spamoor_config["throughput"],
        from_addr=None,
        private_key=None,
        rpc_client=None,
    )

    assert txs[0]["data"] == "0x6001600055"
    assert txs[1]["data"] == "0x60ff60005255"
    assert txs[2]["data"] == txs[0]["data"]
