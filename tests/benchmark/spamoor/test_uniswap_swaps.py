"""Tests for build_uniswap_swaps_transactions."""

from typing import Any, Callable, Dict

import pytest

from .helpers import (
    broadcast_and_assert_receipts,
    build_uniswap_swaps_transactions,
    spamoor_signer_context,
)


@pytest.mark.spamoor
def test_uniswap_swaps_scenario(
    spamoor_config: Dict[str, Any],
    spamoor_rpc_client: Callable[[str, list], Any],
) -> None:
    """Broadcast Uniswap V2 router swap calls against a placeholder router."""
    ctx = spamoor_signer_context(spamoor_config, spamoor_rpc_client)

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
        selector = txs[0]["data"][2:10]
        assert selector in {"38ed1739", "7ff36ab5", "18cbafe5"}

    # swapExactETHForTokens carries non-zero value to the placeholder. All
    # calls land on an empty address → succeed as no-ops.
    broadcast_and_assert_receipts(txs, ctx, spamoor_rpc_client)
