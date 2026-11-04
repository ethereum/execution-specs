"""Tests for build_erc20tx_transactions, dispatched via the wallet pool."""

from typing import Any, Callable, Dict

import pytest

from execution_testing.cli.pytest_commands.plugins.spamoor.wallet_pool import (
    WalletPool,
)

from .helpers import build_erc20tx_transactions
from .pool_runner import submit_pool_workload


@pytest.mark.spamoor
def test_erc20tx_scenario_with_deploy(
    spamoor_config: Dict[str, Any],
    spamoor_rpc_client: Callable[[str, list], Any],
    spamoor_wallet_pool: WalletPool,
) -> None:
    """Deploy stub ERC20 from root, then submit transferMint calls via pool."""
    txs = build_erc20tx_transactions(
        count=spamoor_config["count"],
        amount=spamoor_config["amount"],
        random_target=spamoor_config["random_target"],
        random_amount=spamoor_config["random_amount"],
        contract_address=spamoor_config.get("contract_address"),
        contract_code="0x6001600055",
        deploy_gas_limit=spamoor_config.get("deploy_gas_limit", 2_000_000),
        gas_limit=100_000,
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
        assert txs[1]["data"].startswith("0x9d0f7cba")

    deploy_tx, exec_txs = txs[0], txs[1:]
    submit_pool_workload(
        spamoor_config=spamoor_config,
        rpc_client=spamoor_rpc_client,
        pool=spamoor_wallet_pool,
        tx_dicts=exec_txs,
        root_setup_txs=[deploy_tx],
    )


@pytest.mark.spamoor
def test_erc20tx_scenario_no_deploy(
    spamoor_config: Dict[str, Any],
    spamoor_rpc_client: Callable[[str, list], Any],
    spamoor_wallet_pool: WalletPool,
) -> None:
    """Skip-deploy path: submit transferMint calls only via pool."""
    txs = build_erc20tx_transactions(
        count=spamoor_config["count"],
        amount=spamoor_config["amount"],
        random_target=True,
        random_amount=False,
        contract_address=spamoor_config.get("contract_address"),
        contract_code=None,
        gas_limit=100_000,
        basefee=spamoor_config["basefee"],
        tip_fee=spamoor_config["tip_fee"],
        throughput=spamoor_config["throughput"],
        from_addr=None,
        private_key=None,
        rpc_client=None,
    )

    assert len(txs) == spamoor_config["count"]
    if spamoor_config["count"] >= 2:
        addr_a = txs[0]["data"][10 : 10 + 64]
        addr_b = txs[1]["data"][10 : 10 + 64]
        assert addr_a != addr_b

    submit_pool_workload(
        spamoor_config=spamoor_config,
        rpc_client=spamoor_rpc_client,
        pool=spamoor_wallet_pool,
        tx_dicts=txs,
    )
