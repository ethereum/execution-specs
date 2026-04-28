"""Tests for build_blob_combined_transactions.

Type-3 blob broadcast requires network-form RLP with the blob sidecars,
which EST's ``Transaction.rlp()`` does not currently emit. The submit
path therefore skips at runtime; the builder shape is still exercised.
"""

from typing import Any, Callable, Dict

import pytest

from execution_testing.cli.pytest_commands.plugins.spamoor.wallet_pool import (
    WalletPool,
)

from .helpers import build_blob_combined_transactions
from .pool_runner import submit_pool_workload


@pytest.mark.spamoor
def test_blob_combined_scenario(
    spamoor_config: Dict[str, Any],
    spamoor_rpc_client: Callable[[str, list], Any],
    spamoor_wallet_pool: WalletPool,
) -> None:
    """Exercise the blob-combined builder shape; submission is skipped."""
    txs = build_blob_combined_transactions(
        count=spamoor_config["count"],
        sidecars=spamoor_config["sidecars"],
        basefee=spamoor_config["basefee"],
        tip_fee=spamoor_config["tip_fee"],
        blob_fee=spamoor_config["blob_fee"],
        from_addr=None,
        private_key=None,
        rpc_client=None,
    )

    assert len(txs) == spamoor_config["count"]
    if spamoor_config["count"] > 0:
        tx0 = txs[0]
        assert tx0["type"] == 3
        assert tx0["gas"] == 21000
        assert tx0["maxFeePerBlobGas"] == spamoor_config["blob_fee"]
        expected_blobs = max(1, min(int(spamoor_config["sidecars"]), 6))
        assert len(tx0["blobVersionedHashes"]) == expected_blobs

    # Pool-runner skips when any tx is type-3 (network-form RLP needed).
    submit_pool_workload(
        spamoor_config=spamoor_config,
        rpc_client=spamoor_rpc_client,
        pool=spamoor_wallet_pool,
        tx_dicts=txs,
    )
