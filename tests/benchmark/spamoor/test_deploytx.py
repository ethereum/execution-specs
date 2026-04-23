"""Tests for build_deploytx_transactions."""

from typing import Any, Callable, Dict

import pytest

from .helpers import (
    broadcast_and_assert_receipts,
    build_deploytx_transactions,
    spamoor_signer_context,
)


@pytest.mark.spamoor
def test_deploytx_default_bytecode(
    spamoor_config: Dict[str, Any],
    spamoor_rpc_client: Callable[[str, list], Any],
) -> None:
    """Broadcast contract-creation txs carrying the default bytecode."""
    ctx = spamoor_signer_context(spamoor_config, spamoor_rpc_client)

    txs = build_deploytx_transactions(
        count=spamoor_config["count"],
        bytecodes=spamoor_config["bytecodes"],
        bytecodes_file=spamoor_config["bytecodes_file"],
        gas_limit=spamoor_config["gas_limit"],
        basefee=spamoor_config["basefee"],
        tip_fee=spamoor_config["tip_fee"],
        throughput=spamoor_config["throughput"],
        from_addr=spamoor_config["from_addr"],
        private_key=spamoor_config["private_key"],
        rpc_client=spamoor_rpc_client,
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

    broadcast_and_assert_receipts(txs, ctx, spamoor_rpc_client)


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
