"""Tests for build_erc20_bloater_transactions."""

from typing import Any, Callable, Dict

import pytest

from .helpers import (
    broadcast_and_assert_receipts,
    build_erc20_bloater_transactions,
    spamoor_signer_context,
)


@pytest.mark.spamoor
def test_erc20_bloater_scenario_with_deploy(
    spamoor_config: Dict[str, Any],
    spamoor_rpc_client: Callable[[str, list], Any],
) -> None:
    """Deploy ERC20Bloater stub + broadcast bloatStorage calls."""
    ctx = spamoor_signer_context(spamoor_config, spamoor_rpc_client)

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
        from_addr=spamoor_config["from_addr"],
        private_key=spamoor_config["private_key"],
        rpc_client=spamoor_rpc_client,
    )

    assert len(txs) == spamoor_config["count"] + 1
    assert txs[0]["type"] == 2
    assert txs[0]["to"] == ""
    if spamoor_config["count"] > 0:
        assert txs[1]["data"].startswith("0xc1926de5")

    # Bloater txs carry 16.7M gas limits → tight block packing on a 30M
    # cap. Give the node extra time to mine the batch.
    broadcast_and_assert_receipts(txs, ctx, spamoor_rpc_client, timeout=120)


@pytest.mark.spamoor
def test_erc20_bloater_scenario_existing_contract(
    spamoor_config: Dict[str, Any],
    spamoor_rpc_client: Callable[[str, list], Any],
) -> None:
    """Skip-deploy path: call bloatStorage on an existing address."""
    ctx = spamoor_signer_context(spamoor_config, spamoor_rpc_client)

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
        from_addr=spamoor_config["from_addr"],
        private_key=spamoor_config["private_key"],
        rpc_client=spamoor_rpc_client,
    )

    assert len(txs) == spamoor_config["count"]
    if spamoor_config["count"] > 0:
        assert txs[0]["to"] == "0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee"
        assert txs[0]["data"].startswith("0xc1926de5")

    broadcast_and_assert_receipts(txs, ctx, spamoor_rpc_client, timeout=120)
