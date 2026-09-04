"""Tests for build_factorydeploytx_transactions."""

from typing import Any, Callable, Dict

import pytest

from .helpers import (
    broadcast_and_assert_receipts,
    build_factorydeploytx_transactions,
    spamoor_signer_context,
)


@pytest.mark.spamoor
def test_factorydeploytx_scenario_with_deploy(
    spamoor_config: Dict[str, Any],
    spamoor_rpc_client: Callable[[str, list], Any],
) -> None:
    """Deploy factory bytecode + broadcast deploy(bytes32,bytes) calls."""
    ctx = spamoor_signer_context(spamoor_config, spamoor_rpc_client)

    txs = build_factorydeploytx_transactions(
        count=spamoor_config.get("count") or 10,
        init_code=spamoor_config.get("init_code") or "0x1234",
        start_salt=spamoor_config.get("start_salt") or 0,
        factory_address="",
        deploy_gas_limit=spamoor_config.get("deploy_gas_limit") or 2_000_000,
        gas_limit=spamoor_config.get("gas_limit") or 500_000,
        rpc_client=spamoor_rpc_client,
    )

    assert len(txs) == (spamoor_config.get("count") or 10) + 1
    assert txs[0]["type"] == 2
    assert txs[0]["to"] == ""
    assert txs[0]["data"].startswith("0x60806040")
    if (spamoor_config.get("count") or 10) > 0:
        assert txs[1]["data"].startswith("0x4c8c9ea1")

    broadcast_and_assert_receipts(txs, ctx, spamoor_rpc_client)


@pytest.mark.spamoor
def test_factorydeploytx_scenario_no_deploy(
    spamoor_config: Dict[str, Any],
    spamoor_rpc_client: Callable[[str, list], Any],
) -> None:
    """Skip-deploy path: deploy(bytes32,bytes) calls only."""
    ctx = spamoor_signer_context(spamoor_config, spamoor_rpc_client)

    txs = build_factorydeploytx_transactions(
        count=spamoor_config.get("count") or 10,
        init_code=spamoor_config.get("init_code") or "0x1234",
        start_salt=spamoor_config.get("start_salt") or 0,
        factory_address="0x3333333333333333333333333333333333333333",
        deploy_gas_limit=spamoor_config.get("deploy_gas_limit") or 2_000_000,
        gas_limit=spamoor_config.get("gas_limit") or 500_000,
        rpc_client=spamoor_rpc_client,
    )

    assert len(txs) == (spamoor_config.get("count") or 10)
    if (spamoor_config.get("count") or 10) > 0:
        assert txs[0]["type"] == 2
        assert txs[0]["to"] == "0x3333333333333333333333333333333333333333"
        assert txs[0]["data"].startswith("0x4c8c9ea1")

    broadcast_and_assert_receipts(txs, ctx, spamoor_rpc_client)
