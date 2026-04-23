"""Tests for build_blob_combined_transactions."""

from typing import Any, Callable, Dict

import pytest

from .helpers import (
    broadcast_and_assert_receipts,
    build_blob_combined_transactions,
    spamoor_signer_context,
)


@pytest.mark.spamoor
def test_blob_combined_scenario(
    spamoor_config: Dict[str, Any],
    spamoor_rpc_client: Callable[[str, list], Any],
) -> None:
    """
    Exercise the blob-combined builder shape.

    ``broadcast_and_assert_receipts`` currently skips for type-3 txs:
    ``eth_sendRawTransaction`` needs EIP-4844 network-form RLP (with
    blobs/commitments/proofs sidecars), while EST's ``Transaction.rlp()``
    yields block-form (payload only). The test still exercises the
    builder end-to-end and the broadcast helper will skip cleanly.
    """
    ctx = spamoor_signer_context(spamoor_config, spamoor_rpc_client)

    txs = build_blob_combined_transactions(
        count=spamoor_config["count"],
        sidecars=spamoor_config["sidecars"],
        basefee=spamoor_config["basefee"],
        tip_fee=spamoor_config["tip_fee"],
        blob_fee=spamoor_config["blob_fee"],
        from_addr=spamoor_config["from_addr"],
        private_key=spamoor_config["private_key"],
        rpc_client=spamoor_rpc_client,
    )

    assert len(txs) == spamoor_config["count"]
    if spamoor_config["count"] > 0:
        tx0 = txs[0]
        assert tx0["type"] == 3
        assert tx0["gas"] == 21000
        assert tx0["maxFeePerBlobGas"] == spamoor_config["blob_fee"]
        expected_blobs = max(1, min(int(spamoor_config["sidecars"]), 6))
        assert len(tx0["blobVersionedHashes"]) == expected_blobs

    broadcast_and_assert_receipts(txs, ctx, spamoor_rpc_client)
