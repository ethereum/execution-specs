"""Tests for build_eoatx_transactions, dispatched via the wallet pool."""

from typing import Any, Callable, Dict

import pytest

from execution_testing.cli.pytest_commands.plugins.spamoor.wallet_pool import (
    WalletPool,
)

from .helpers import build_eoatx_transactions
from .pool_runner import submit_pool_workload


@pytest.mark.spamoor
def test_eoatx_scenario(
    spamoor_config: Dict[str, Any],
    spamoor_rpc_client: Callable[[str, list], Any],
    spamoor_wallet_pool: WalletPool,
) -> None:
    """Build ``count`` EOA-to-EOA transfers and submit through the pool."""
    txs = build_eoatx_transactions(
        count=spamoor_config["count"],
        throughput=spamoor_config["throughput"],
        amount=spamoor_config["amount"],
        basefee=spamoor_config["basefee"],
        from_addr=None,
        private_key=None,
        rpc_client=None,
    )
    assert len(txs) == spamoor_config["count"]
    assert txs[0]["type"] == 2
    assert txs[0]["value"] == spamoor_config["amount"]
    assert txs[0]["gas"] == 21000

    submit_pool_workload(
        spamoor_config=spamoor_config,
        rpc_client=spamoor_rpc_client,
        pool=spamoor_wallet_pool,
        tx_dicts=txs,
    )
