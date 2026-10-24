"""Tests for build_storagerefundtx_transactions."""

from typing import Any, Callable, Dict

import pytest

from .helpers import (
    broadcast_and_assert_receipts,
    build_storagerefundtx_transactions,
    spamoor_signer_context,
)


@pytest.mark.spamoor
def test_storagerefundtx_scenario_with_deploy(
    spamoor_config: Dict[str, Any],
    spamoor_rpc_client: Callable[[str, list], Any],
) -> None:
    """Deploy stub + broadcast execute(slotsPerCall) calls."""
    ctx = spamoor_signer_context(spamoor_config, spamoor_rpc_client)

    txs = build_storagerefundtx_transactions(
        count=spamoor_config["count"],
        slots_per_call=spamoor_config["slots_per_call"],
        gas_limit=spamoor_config["gas_limit"],
        contract_address=None,
        contract_code=None,
        deploy_gas_limit=spamoor_config["deploy_gas_limit"],
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
        assert txs[1]["data"].startswith("0xfe0d94c1")

    broadcast_and_assert_receipts(txs, ctx, spamoor_rpc_client)


@pytest.mark.spamoor
def test_storagerefundtx_scenario_existing_contract(
    spamoor_config: Dict[str, Any],
    spamoor_rpc_client: Callable[[str, list], Any],
) -> None:
    """Skip-deploy path: execute() calls against a supplied address."""
    ctx = spamoor_signer_context(spamoor_config, spamoor_rpc_client)

    txs = build_storagerefundtx_transactions(
        count=spamoor_config["count"],
        slots_per_call=spamoor_config["slots_per_call"],
        gas_limit=0,
        contract_address="0xffffffffffffffffffffffffffffffffffffffff",
        basefee=spamoor_config["basefee"],
        tip_fee=spamoor_config["tip_fee"],
        throughput=spamoor_config["throughput"],
        from_addr=spamoor_config["from_addr"],
        private_key=spamoor_config["private_key"],
        rpc_client=spamoor_rpc_client,
    )

    assert len(txs) == spamoor_config["count"]
    if spamoor_config["count"] > 0:
        assert txs[0]["to"] == "0xffffffffffffffffffffffffffffffffffffffff"
        assert txs[0]["data"].startswith("0xfe0d94c1")

    broadcast_and_assert_receipts(txs, ctx, spamoor_rpc_client)
