"""Tests for build_evm_fuzz_transactions."""

from typing import Any, Callable, Dict

import pytest

from .helpers import (
    broadcast_and_assert_receipts,
    build_evm_fuzz_transactions,
    spamoor_signer_context,
)


@pytest.mark.spamoor
def test_evm_fuzz_scenario(
    spamoor_config: Dict[str, Any],
    spamoor_rpc_client: Callable[[str, list], Any],
) -> None:
    """Broadcast random-bytecode contract creations. Reverts are OK."""
    ctx = spamoor_signer_context(spamoor_config, spamoor_rpc_client)

    txs = build_evm_fuzz_transactions(
        count=spamoor_config["count"],
        gas_limit=spamoor_config["gas_limit"],
        min_code_size=spamoor_config["min_code_size"],
        max_code_size=spamoor_config["max_code_size"],
        payload_seed=spamoor_config["payload_seed"],
        tx_id_offset=spamoor_config["tx_id_offset"],
        fuzz_mode=spamoor_config["fuzz_mode"],
        basefee=spamoor_config["basefee"],
        tip_fee=spamoor_config["tip_fee"],
        throughput=spamoor_config["throughput"],
        from_addr=spamoor_config["from_addr"],
        private_key=spamoor_config["private_key"],
        rpc_client=spamoor_rpc_client,
    )

    assert len(txs) == spamoor_config["count"]
    for tx in txs:
        assert tx["type"] == 2
        assert tx["to"] == ""
        assert tx["data"].startswith("0x")

    # Random init code typically reverts — we only assert inclusion.
    broadcast_and_assert_receipts(
        txs, ctx, spamoor_rpc_client, allow_reverts=True
    )


@pytest.mark.spamoor
def test_evm_fuzz_is_deterministic(
    spamoor_config: Dict[str, Any],
    spamoor_rpc_client: Callable[[str, list], Any],
) -> None:
    """Determinism check: same inputs yield same bytecodes. No broadcast."""
    kwargs = dict(
        count=max(2, spamoor_config["count"]),
        gas_limit=spamoor_config["gas_limit"],
        min_code_size=spamoor_config["min_code_size"],
        max_code_size=spamoor_config["max_code_size"],
        payload_seed="0x1234",
        tx_id_offset=0,
        fuzz_mode=spamoor_config["fuzz_mode"],
        basefee=spamoor_config["basefee"],
        tip_fee=spamoor_config["tip_fee"],
        throughput=spamoor_config["throughput"],
        from_addr=None,
        private_key=None,
        rpc_client=None,
    )
    a = build_evm_fuzz_transactions(**kwargs)
    b = build_evm_fuzz_transactions(**kwargs)
    assert [t["data"] for t in a] == [t["data"] for t in b]
