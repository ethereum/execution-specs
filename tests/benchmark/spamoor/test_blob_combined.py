import pytest

from .helpers import build_blob_combined_transactions


@pytest.mark.spamoor
def test_blob_combined_scenario(spamoor_config, spamoor_rpc_client):
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
        assert tx0["value"] == 0
        assert "maxFeePerGas" in tx0
        assert "maxPriorityFeePerGas" in tx0
        assert "maxFeePerBlobGas" in tx0
        assert tx0["maxFeePerBlobGas"] == spamoor_config["blob_fee"]
        assert isinstance(tx0["blobVersionedHashes"], list)
        expected_blobs = max(1, min(int(spamoor_config["sidecars"]), 6))
        assert len(tx0["blobVersionedHashes"]) == expected_blobs
