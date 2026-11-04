"""Tests for build_uniswap_swaps_transactions, dispatched via the pool."""

from typing import Any, Callable, Dict

import pytest

from execution_testing.cli.pytest_commands.plugins.spamoor.wallet_pool import (
    WalletPool,
)

from .helpers import build_uniswap_swaps_transactions
from .pool_runner import submit_pool_workload


@pytest.mark.spamoor
def test_uniswap_swaps_scenario(
    spamoor_config: Dict[str, Any],
    spamoor_rpc_client: Callable[[str, list], Any],
    spamoor_wallet_pool: WalletPool,
) -> None:
    """Submit Uniswap V2 router swap calls against a placeholder router."""
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
        from_addr=None,
        private_key=None,
        rpc_client=None,
    )

    assert len(txs) == spamoor_config["count"]
    if spamoor_config["count"] > 0:
        selector = txs[0]["data"][2:10]
        assert selector in {"38ed1739", "7ff36ab5", "18cbafe5"}

    submit_pool_workload(
        spamoor_config=spamoor_config,
        rpc_client=spamoor_rpc_client,
        pool=spamoor_wallet_pool,
        tx_dicts=txs,
    )
