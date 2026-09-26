"""Tests for build_evm_fuzz_transactions, dispatched via the wallet pool."""

from typing import Any, Callable, Dict

import pytest

from execution_testing.cli.pytest_commands.plugins.spamoor.wallet_pool import (
    WalletPool,
)

from .helpers import build_evm_fuzz_transactions
from .pool_runner import submit_pool_workload


@pytest.mark.spamoor
def test_evm_fuzz_scenario(
    spamoor_config: Dict[str, Any],
    spamoor_rpc_client: Callable[[str, list], Any],
    spamoor_wallet_pool: WalletPool,
) -> None:
    """Submit random-bytecode contract creations through the pool."""
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
        from_addr=None,
        private_key=None,
        rpc_client=None,
    )

    assert len(txs) == spamoor_config["count"]
    for tx in txs:
        assert tx["type"] == 2
        assert tx["to"] == ""
        assert tx["data"].startswith("0x")

    # Random bytecode reverts by design — landing on-chain is the success
    # criterion for this scenario, not execution status.
    submit_pool_workload(
        spamoor_config={**spamoor_config, "allow_revert": True},
        rpc_client=spamoor_rpc_client,
        pool=spamoor_wallet_pool,
        tx_dicts=txs,
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
