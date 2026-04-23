"""Tests for build_deploytx_transactions."""

from typing import Any, Callable, Dict

import pytest

from .helpers import build_deploytx_transactions


@pytest.mark.spamoor
def test_deploytx_default_bytecode(
    spamoor_config: Dict[str, Any],
    spamoor_rpc_client: Callable[[str, list], Any],
) -> None:
    """Exercise test_deploytx_default_bytecode."""
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
    if spamoor_config["count"] == 0:
        return

    expected_gas = (
        spamoor_config["gas_limit"]
        if spamoor_config["gas_limit"]
        else 1_000_000
    )
    for tx in txs:
        assert tx["type"] == 2
        assert tx["to"] == ""
        assert tx["value"] == 0
        assert tx["gas"] == expected_gas
        assert tx["data"].startswith("0x")
    # When neither --spamoor-bytecodes nor --spamoor-bytecodes-file is
    # set, every tx carries the default tiny bytecode.
    if (
        not spamoor_config["bytecodes"]
        and not spamoor_config["bytecodes_file"]
    ):
        assert txs[0]["data"] == "0x6001600055"


@pytest.mark.spamoor
def test_deploytx_cycles_bytecode_list(
    spamoor_config: Dict[str, Any],
    spamoor_rpc_client: Callable[[str, list], Any],
) -> None:
    """Exercise test_deploytx_cycles_bytecode_list."""
    # Force a two-entry list so we can check cycling even when the CLI
    # doesn't provide bytecodes.
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
    assert txs[2]["data"] == txs[0]["data"]  # cycles every 2
