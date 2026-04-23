"""Tests for build_eoatx_transactions."""

from typing import Any, Callable, Dict

import pytest

from .helpers import (
    broadcast_and_assert_receipts,
    build_eoatx_transactions,
    spamoor_signer_context,
)


@pytest.mark.spamoor
def test_eoatx_scenario(
    spamoor_config: Dict[str, Any],
    spamoor_rpc_client: Callable[[str, list], Any],
) -> None:
    """Build, sign, broadcast EOA transfers and verify receipts."""
    ctx = spamoor_signer_context(spamoor_config, spamoor_rpc_client)

    raw_txs = build_eoatx_transactions(
        count=spamoor_config["count"],
        throughput=spamoor_config["throughput"],
        amount=spamoor_config["amount"],
        basefee=spamoor_config["basefee"],
        from_addr=spamoor_config["from_addr"],
        private_key=spamoor_config["private_key"],
        rpc_client=spamoor_rpc_client,
    )

    assert len(raw_txs) == spamoor_config["count"]
    assert raw_txs[0]["type"] == 2
    assert raw_txs[0]["value"] == spamoor_config["amount"]
    assert raw_txs[0]["gas"] == 21000

    broadcast_and_assert_receipts(raw_txs, ctx, spamoor_rpc_client)
