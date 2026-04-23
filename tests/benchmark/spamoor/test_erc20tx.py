"""Tests for build_erc20tx_transactions."""

from typing import Any, Callable, Dict

import pytest

from .helpers import build_erc20tx_transactions


@pytest.mark.spamoor
def test_erc20tx_scenario_with_deploy(
    spamoor_config: Dict[str, Any],
    spamoor_rpc_client: Callable[[str, list], Any],
) -> None:
    """Exercise test_erc20tx_scenario_with_deploy."""
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

    # Deploy tx + count execution txs.
    assert len(txs) == spamoor_config["count"] + 1

    deploy = txs[0]
    assert deploy["type"] == 2
    assert deploy["to"] == ""
    assert deploy["data"].startswith("0x")

    if spamoor_config["count"] > 0:
        exec_tx = txs[1]
        assert exec_tx["type"] == 2
        assert exec_tx["to"] == (
            spamoor_config.get("contract_address")
            or "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        )
        assert exec_tx["value"] == 0
        assert exec_tx["gas"] == 100_000
        # selector(4) + address(32) + uint256(32) = 68 bytes.
        assert len(exec_tx["data"]) == 2 + 2 * 68
        assert exec_tx["data"].startswith("0x9d0f7cba")


@pytest.mark.spamoor
def test_erc20tx_scenario_no_deploy(
    spamoor_config: Dict[str, Any],
    spamoor_rpc_client: Callable[[str, list], Any],
) -> None:
    """Exercise test_erc20tx_scenario_no_deploy."""
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

    # No deploy tx when contract_code is None.
    assert len(txs) == spamoor_config["count"]
    if spamoor_config["count"] >= 2:
        # random_target should produce distinct recipients.
        addr_a = txs[0]["data"][10 : 10 + 64]
        addr_b = txs[1]["data"][10 : 10 + 64]
        assert addr_a != addr_b
