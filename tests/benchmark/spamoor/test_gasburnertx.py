"""Tests for build_gasburnertx_transactions, dispatched via the wallet pool."""

from typing import Any, Callable, Dict

import pytest

from execution_testing.cli.pytest_commands.plugins.spamoor.wallet_pool import (
    WalletPool,
)

from .helpers import build_gasburnertx_transactions
from .pool_runner import submit_pool_workload


@pytest.mark.spamoor
def test_gasburnertx_scenario(
    spamoor_config: Dict[str, Any],
    spamoor_rpc_client: Callable[[str, list], Any],
    spamoor_wallet_pool: WalletPool,
) -> None:
    """Deploy gas-burner from root, then submit gas-burning calls via pool."""
    txs = build_gasburnertx_transactions(
        count=spamoor_config["count"],
        gas_units_to_burn=spamoor_config["gas_units_to_burn"],
        basefee=spamoor_config["basefee"],
        tip_fee=spamoor_config["tip_fee"],
        throughput=spamoor_config["throughput"],
        deploy_gas_limit=spamoor_config["deploy_gas_limit"],
        contract_address=spamoor_config["contract_address"],
        from_addr=None,
        private_key=None,
        rpc_client=None,
    )

    assert len(txs) == spamoor_config["count"] + 1
    assert txs[0]["type"] == 2
    assert txs[0]["to"] == ""
    if spamoor_config["count"] > 0:
        assert txs[1]["data"] == "0x00000000"

    deploy_tx, exec_txs = txs[0], txs[1:]
    submit_pool_workload(
        spamoor_config=spamoor_config,
        rpc_client=spamoor_rpc_client,
        pool=spamoor_wallet_pool,
        tx_dicts=exec_txs,
        root_setup_txs=[deploy_tx],
    )
