"""Tests for build_calltx_transactions."""

from typing import Any, Callable, Dict

import pytest

from .helpers import build_calltx_transactions


@pytest.mark.spamoor
def test_calltx_scenario_with_deploy(
    spamoor_config: Dict[str, Any],
    spamoor_rpc_client: Callable[[str, list], Any],
) -> None:
    """Exercise test_calltx_scenario_with_deploy."""
    txs = build_calltx_transactions(
        count=spamoor_config["count"],
        throughput=spamoor_config["throughput"],
        amount=spamoor_config["amount"],
        basefee=spamoor_config["basefee"],
        from_addr=spamoor_config["from_addr"],
        private_key=spamoor_config["private_key"],
        contract_code="0x6000600055",
        contract_address=spamoor_config.get("contract_address"),
        call_data=spamoor_config.get("call_data", ""),
        deploy_gas_limit=spamoor_config.get("deploy_gas_limit", 2000000),
        call_fn_sig=spamoor_config.get("call_fn_sig", ""),
        call_args=spamoor_config.get("call_args", "[]"),
        contract_args=spamoor_config.get("contract_args", "[]"),
        gas_limit=spamoor_config.get("gas_limit", 0),
        tip_fee=spamoor_config.get("tip_fee", 1_000_000_000),
        rpc_client=spamoor_rpc_client,
    )

    # With contract_code set, the first tx is deployment,
    # followed by `count` execution txs.
    assert len(txs) == spamoor_config["count"] + 1

    # Check deployment tx
    assert txs[0]["type"] == 2
    assert txs[0]["to"] == ""
    assert txs[0]["data"] == "0x6000600055"

    # Check execution tx
    if spamoor_config["count"] > 0:
        assert txs[1]["to"] == (
            spamoor_config.get("contract_address")
            or "0x1111111111111111111111111111111111111111"
        )
        # Use the gas_limit override when provided.
        expected_gas = (
            spamoor_config.get("gas_limit")
            if spamoor_config.get("gas_limit")
            else 500000
        )
        assert txs[1]["gas"] == expected_gas


@pytest.mark.spamoor
def test_calltx_scenario_no_deploy(
    spamoor_config: Dict[str, Any],
    spamoor_rpc_client: Callable[[str, list], Any],
) -> None:
    """Exercise test_calltx_scenario_no_deploy."""
    txs = build_calltx_transactions(
        count=spamoor_config["count"],
        throughput=spamoor_config["throughput"],
        amount=spamoor_config["amount"],
        basefee=spamoor_config["basefee"],
        from_addr=spamoor_config["from_addr"],
        private_key=spamoor_config["private_key"],
        contract_code=None,
        contract_address=spamoor_config.get("contract_address"),
        call_data=spamoor_config.get("call_data") or "0x1234",
        deploy_gas_limit=spamoor_config.get("deploy_gas_limit", 2000000),
        call_fn_sig=spamoor_config.get("call_fn_sig", ""),
        call_args=spamoor_config.get("call_args", "[]"),
        contract_args=spamoor_config.get("contract_args", "[]"),
        gas_limit=spamoor_config.get("gas_limit", 0),
        tip_fee=spamoor_config.get("tip_fee", 1_000_000_000),
        rpc_client=spamoor_rpc_client,
    )

    # If no contract_code, we only get `count` execution txs
    assert len(txs) == spamoor_config["count"]

    if spamoor_config["count"] > 0:
        assert txs[0]["type"] == 2
        assert txs[0]["to"] == (
            spamoor_config.get("contract_address")
            or "0x1111111111111111111111111111111111111111"
        )
        assert txs[0]["data"] == "0x1234"
        # Use the gas_limit override when provided.
        expected_gas = (
            spamoor_config.get("gas_limit")
            if spamoor_config.get("gas_limit")
            else 500000
        )
        assert txs[0]["gas"] == expected_gas
