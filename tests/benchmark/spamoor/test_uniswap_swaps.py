"""Tests for build_uniswap_swaps_transactions."""

from typing import Any, Callable, Dict

import pytest

from .helpers import build_uniswap_swaps_transactions


@pytest.mark.spamoor
def test_uniswap_swaps_scenario(
    spamoor_config: Dict[str, Any],
    spamoor_rpc_client: Callable[[str, list], Any],
) -> None:
    """Exercise test_uniswap_swaps_scenario."""
    txs = build_uniswap_swaps_transactions(
        count=spamoor_config["count"],
        pair_count=spamoor_config["pair_count"],
        min_swap_amount=spamoor_config["min_swap_amount"],
        max_swap_amount=spamoor_config["max_swap_amount"],
        buy_ratio=spamoor_config["buy_ratio"],
        slippage=spamoor_config["slippage"],
        basefee=spamoor_config["basefee"],
        tip_fee=spamoor_config["tip_fee"],
        throughput=spamoor_config["throughput"],
        from_addr=spamoor_config["from_addr"],
        private_key=spamoor_config["private_key"],
        rpc_client=spamoor_rpc_client,
    )

    assert len(txs) == spamoor_config["count"]
    if spamoor_config["count"] > 0:
        tx0 = txs[0]
        assert tx0["type"] == 2
        assert tx0["to"] == "0x4444444444444444444444444444444444444444"
        assert tx0["gas"] == 200_000
        # Data carries a 4-byte Uniswap V2 Router02 selector then ABI args.
        assert tx0["data"].startswith("0x")
        selector = tx0["data"][2:10]
        assert selector in {"38ed1739", "7ff36ab5", "18cbafe5"}

    # Buy-ratio mix: first N * buy_ratio / 100 txs should target a
    # buy selector (either swapExactTokensForTokens or swapExactETHForTokens).
    if spamoor_config["count"] >= 5 and spamoor_config["buy_ratio"] > 0:
        buys_seen = 0
        sells_seen = 0
        for tx in txs:
            selector = tx["data"][2:10]
            if selector in {"38ed1739", "7ff36ab5"}:
                buys_seen += 1
            elif selector == "18cbafe5":
                sells_seen += 1
        assert buys_seen > 0
        if spamoor_config["buy_ratio"] < 100:
            assert sells_seen > 0

    # swapExactETHForTokens carries msg.value; others do not.
    for tx in txs:
        selector = tx["data"][2:10]
        if selector == "7ff36ab5":
            assert tx["value"] > 0
        else:
            assert tx["value"] == 0
