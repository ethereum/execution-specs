"""Tests for build_calltx_transactions."""

from typing import Any, Callable, Dict

import pytest

from .helpers import (
    broadcast_and_assert_receipts,
    build_calltx_transactions,
    spamoor_signer_context,
)


@pytest.mark.spamoor
def test_calltx_scenario_with_deploy(
    spamoor_config: Dict[str, Any],
    spamoor_rpc_client: Callable[[str, list], Any],
) -> None:
    """Build deploy + call txs, broadcast, assert receipts."""
    ctx = spamoor_signer_context(spamoor_config, spamoor_rpc_client)

    txs = build_calltx_transactions(
        count=spamoor_config["count"],
        throughput=spamoor_config["throughput"],
        amount=spamoor_config["amount"],
        basefee=spamoor_config["basefee"],
        from_addr=spamoor_config["from_addr"],
        private_key=spamoor_config["private_key"],
        contract_code="0x6001600055",
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

    assert len(txs) == spamoor_config["count"] + 1
    assert txs[0]["type"] == 2
    assert txs[0]["to"] == ""
    assert txs[0]["data"] == "0x6001600055"

    broadcast_and_assert_receipts(txs, ctx, spamoor_rpc_client)


@pytest.mark.spamoor
def test_calltx_scenario_no_deploy(
    spamoor_config: Dict[str, Any],
    spamoor_rpc_client: Callable[[str, list], Any],
) -> None:
    """Build call-only txs, broadcast, assert receipts."""
    ctx = spamoor_signer_context(spamoor_config, spamoor_rpc_client)

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

    assert len(txs) == spamoor_config["count"]
    assert txs[0]["type"] == 2
    assert txs[0]["data"] == "0x1234"

    broadcast_and_assert_receipts(txs, ctx, spamoor_rpc_client)
