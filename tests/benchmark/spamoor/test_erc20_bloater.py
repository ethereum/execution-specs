"""Tests for build_erc20_bloater_transactions, dispatched via the pool."""

from typing import Any, Callable, Dict

import pytest

from execution_testing.cli.pytest_commands.plugins.spamoor.wallet_pool import (
    WalletPool,
)

from .helpers import build_erc20_bloater_transactions
from .pool_runner import submit_pool_workload


@pytest.mark.spamoor
def test_erc20_bloater_scenario_with_deploy(
    spamoor_config: Dict[str, Any],
    spamoor_rpc_client: Callable[[str, list], Any],
    spamoor_wallet_pool: WalletPool,
) -> None:
    """Deploy ERC20Bloater stub from root, then submit bloatStorage via pool."""
    txs = build_erc20_bloater_transactions(
        count=spamoor_config["count"],
        addresses_per_tx=spamoor_config["addresses_per_tx"],
        start_address_index=spamoor_config["start_address_index"],
        gas_limit=spamoor_config["gas_limit"],
        contract_address=None,
        contract_code=None,
        deploy_gas_limit=spamoor_config["deploy_gas_limit"],
        basefee=spamoor_config["basefee"],
        tip_fee=spamoor_config["tip_fee"],
        throughput=spamoor_config["throughput"],
        from_addr=None,
        private_key=None,
        rpc_client=None,
    )

    assert len(txs) == spamoor_config["count"] + 1
    assert txs[0]["type"] == 2
    assert txs[0]["to"] == ""
    if spamoor_config["count"] > 0:
        assert txs[1]["data"].startswith("0xc1926de5")

    deploy_tx, exec_txs = txs[0], txs[1:]
    submit_pool_workload(
        spamoor_config=spamoor_config,
        rpc_client=spamoor_rpc_client,
        pool=spamoor_wallet_pool,
        tx_dicts=exec_txs,
        root_setup_txs=[deploy_tx],
    )


@pytest.mark.spamoor
def test_erc20_bloater_scenario_existing_contract(
    spamoor_config: Dict[str, Any],
    spamoor_rpc_client: Callable[[str, list], Any],
    spamoor_wallet_pool: WalletPool,
) -> None:
    """Skip-deploy path: call bloatStorage on an existing address."""
    txs = build_erc20_bloater_transactions(
        count=spamoor_config["count"],
        addresses_per_tx=spamoor_config["addresses_per_tx"],
        start_address_index=spamoor_config["start_address_index"],
        gas_limit=0,
        contract_address="0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
        contract_code=None,
        basefee=spamoor_config["basefee"],
        tip_fee=spamoor_config["tip_fee"],
        throughput=spamoor_config["throughput"],
        from_addr=None,
        private_key=None,
        rpc_client=None,
    )

    assert len(txs) == spamoor_config["count"]
    if spamoor_config["count"] > 0:
        assert txs[0]["to"] == "0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee"
        assert txs[0]["data"].startswith("0xc1926de5")

    submit_pool_workload(
        spamoor_config=spamoor_config,
        rpc_client=spamoor_rpc_client,
        pool=spamoor_wallet_pool,
        tx_dicts=txs,
    )
