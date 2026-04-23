"""Tests for build_erc20tx_transactions."""

from typing import Any, Callable, Dict

import pytest

from .helpers import (
    broadcast_and_assert_receipts,
    build_erc20tx_transactions,
    spamoor_signer_context,
)


@pytest.mark.spamoor
def test_erc20tx_scenario_with_deploy(
    spamoor_config: Dict[str, Any],
    spamoor_rpc_client: Callable[[str, list], Any],
) -> None:
    """Deploy stub ERC20 + broadcast transferMint calls."""
    ctx = spamoor_signer_context(spamoor_config, spamoor_rpc_client)

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
        from_addr=spamoor_config["from_addr"],
        private_key=spamoor_config["private_key"],
        rpc_client=spamoor_rpc_client,
    )

    assert len(txs) == spamoor_config["count"] + 1
    assert txs[0]["type"] == 2
    assert txs[0]["to"] == ""
    if spamoor_config["count"] > 0:
        assert txs[1]["data"].startswith("0x9d0f7cba")

    broadcast_and_assert_receipts(txs, ctx, spamoor_rpc_client)


@pytest.mark.spamoor
def test_erc20tx_scenario_no_deploy(
    spamoor_config: Dict[str, Any],
    spamoor_rpc_client: Callable[[str, list], Any],
) -> None:
    """Skip-deploy path: broadcast transferMint calls only."""
    ctx = spamoor_signer_context(spamoor_config, spamoor_rpc_client)

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
        from_addr=spamoor_config["from_addr"],
        private_key=spamoor_config["private_key"],
        rpc_client=spamoor_rpc_client,
    )

    assert len(txs) == spamoor_config["count"]
    if spamoor_config["count"] >= 2:
        addr_a = txs[0]["data"][10 : 10 + 64]
        addr_b = txs[1]["data"][10 : 10 + 64]
        assert addr_a != addr_b

    broadcast_and_assert_receipts(txs, ctx, spamoor_rpc_client)
