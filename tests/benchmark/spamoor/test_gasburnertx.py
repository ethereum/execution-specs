"""Tests for build_gasburnertx_transactions."""

from typing import Any, Callable, Dict

import pytest

from .helpers import (
    broadcast_and_assert_receipts,
    build_gasburnertx_transactions,
    spamoor_signer_context,
)


@pytest.mark.spamoor
def test_gasburnertx_scenario(
    spamoor_config: Dict[str, Any],
    spamoor_rpc_client: Callable[[str, list], Any],
) -> None:
    """Deploy gas-burner + broadcast gas-burning calls."""
    ctx = spamoor_signer_context(spamoor_config, spamoor_rpc_client)

    txs = build_gasburnertx_transactions(
        count=spamoor_config["count"],
        gas_units_to_burn=spamoor_config["gas_units_to_burn"],
        basefee=spamoor_config["basefee"],
        tip_fee=spamoor_config["tip_fee"],
        throughput=spamoor_config["throughput"],
        deploy_gas_limit=spamoor_config["deploy_gas_limit"],
        contract_address=spamoor_config["contract_address"],
        from_addr=spamoor_config["from_addr"],
        private_key=spamoor_config["private_key"],
        rpc_client=spamoor_rpc_client,
    )

    assert len(txs) == spamoor_config["count"] + 1
    assert txs[0]["type"] == 2
    assert txs[0]["to"] == ""
    if spamoor_config["count"] > 0:
        assert txs[1]["data"] == "0x00000000"

    broadcast_and_assert_receipts(txs, ctx, spamoor_rpc_client)
