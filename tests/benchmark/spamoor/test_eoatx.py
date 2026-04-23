"""Tests for build_eoatx_transactions."""

from typing import Any, Callable, Dict

import pytest

from .helpers import build_eoatx_transactions


@pytest.mark.spamoor
def test_eoatx_scenario(
    spamoor_config: Dict[str, Any],
    spamoor_rpc_client: Callable[[str, list], Any],
) -> None:
    """Exercise test_eoatx_scenario."""
    txs = build_eoatx_transactions(
        count=spamoor_config["count"],
        throughput=spamoor_config["throughput"],
        amount=spamoor_config["amount"],
        basefee=spamoor_config["basefee"],
        from_addr=spamoor_config["from_addr"],
        private_key=spamoor_config["private_key"],
        rpc_client=spamoor_rpc_client,
    )

    assert len(txs) == spamoor_config["count"]
    if spamoor_config["count"] > 0:
        assert txs[0]["type"] == 2
        assert txs[0]["value"] == spamoor_config["amount"]
        assert txs[0]["gas"] == 21000
        assert "maxFeePerGas" in txs[0]
        assert "maxPriorityFeePerGas" in txs[0]
