"""Tests for build_storagespam_transactions."""

from typing import Any, Callable, Dict

import pytest

from .helpers import (
    broadcast_and_assert_receipts,
    build_storagespam_transactions,
    spamoor_signer_context,
)


@pytest.mark.spamoor
def test_storagespam_scenario_with_deploy(
    spamoor_config: Dict[str, Any],
    spamoor_rpc_client: Callable[[str, list], Any],
) -> None:
    """Deploy stub + broadcast setRandomForGas calls."""
    ctx = spamoor_signer_context(spamoor_config, spamoor_rpc_client)

    txs = build_storagespam_transactions(
        count=spamoor_config["count"],
        gas_units_to_burn=spamoor_config["gas_units_to_burn"],
        reuse_contract=False,
        contract_address=spamoor_config.get("contract_address"),
        contract_code=None,
        deploy_gas_limit=spamoor_config.get("deploy_gas_limit", 2_000_000),
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
        assert txs[1]["data"].startswith("0xfed72935")

    broadcast_and_assert_receipts(txs, ctx, spamoor_rpc_client)


@pytest.mark.spamoor
def test_storagespam_scenario_reuse_contract(
    spamoor_config: Dict[str, Any],
    spamoor_rpc_client: Callable[[str, list], Any],
) -> None:
    """Reuse-contract path: setRandomForGas calls only, no deploy."""
    ctx = spamoor_signer_context(spamoor_config, spamoor_rpc_client)

    txs = build_storagespam_transactions(
        count=spamoor_config["count"],
        gas_units_to_burn=spamoor_config["gas_units_to_burn"],
        reuse_contract=True,
        contract_address=spamoor_config.get("contract_address"),
        basefee=spamoor_config["basefee"],
        tip_fee=spamoor_config["tip_fee"],
        throughput=spamoor_config["throughput"],
        from_addr=spamoor_config["from_addr"],
        private_key=spamoor_config["private_key"],
        rpc_client=spamoor_rpc_client,
    )

    assert len(txs) == spamoor_config["count"]
    if spamoor_config["count"] > 0:
        assert txs[0]["data"].startswith("0xfed72935")

    broadcast_and_assert_receipts(txs, ctx, spamoor_rpc_client)
