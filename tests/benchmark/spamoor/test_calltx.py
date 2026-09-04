"""Tests for the calltx scenario, driven through the spamoor wallet pool.

Mirrors the upstream Go scenario at ``.lab/spamoor/scenarios/calltx``:
deploys a contract from the root wallet (when ``contract_code`` is set),
then submits ``count`` call transactions spread across the HD-derived
wallet pool, paced at the configured throughput and capped at
``max_pending`` in flight.
"""

from __future__ import annotations

import time
from typing import Any, Callable, Dict

import pytest

from execution_testing.cli.pytest_commands.plugins.spamoor.submitter import (
    submit_workload,
)
from execution_testing.cli.pytest_commands.plugins.spamoor.spamoor import (
    resolve_pool_sizing,
)
from execution_testing.cli.pytest_commands.plugins.spamoor.wallet_pool import (
    Wallet,
    WalletPool,
)


def _max_fee_per_gas(spamoor_config: Dict[str, Any]) -> int:
    """Suggested-fee math mirroring upstream spamoor's legacy strategy.

    See ``.lab/spamoor/spamoor/txpool.go:1616-1646`` ``GetSuggestedFees``:
    when the YAML supplies a non-zero ``base_fee_wei`` (or ``base_fee``)
    that value is used directly as ``feeCap`` — there is no throughput
    multiplier. EIP-1559 still requires ``feeCap >= tipCap``, so we
    clamp upward when the tip happens to exceed basefee.
    """
    basefee = int(spamoor_config.get("basefee") or 1_000_000_000)
    tip = int(spamoor_config.get("tip_fee") or 0)
    return max(basefee, tip)


def _execution_gas(spamoor_config: Dict[str, Any]) -> int:
    """Default to 500_000 when unspecified — matches helpers.py:342."""
    gas_limit = int(spamoor_config.get("gas_limit") or 0)
    return gas_limit if gas_limit > 0 else 500_000


def _calltx_dict(
    spamoor_config: Dict[str, Any],
    target_to: str,
    call_data: str,
) -> Dict[str, Any]:
    return {
        "type": 2,
        "to": target_to,
        "value": int(spamoor_config.get("amount") or 0),
        "data": call_data,
        "gas": _execution_gas(spamoor_config),
        "maxFeePerGas": _max_fee_per_gas(spamoor_config),
        "maxPriorityFeePerGas": int(
            spamoor_config.get("tip_fee") or 1_000_000_000
        ),
        "chainId": 1,  # overridden by tx_convert with the real chain id
        "accessList": [],
    }


def _resolved_target(spamoor_config: Dict[str, Any]) -> str:
    addr = spamoor_config.get("contract_address")
    if addr:
        return str(addr)
    return "0x1111111111111111111111111111111111111111"


def _send_root_deploy(
    spamoor_config: Dict[str, Any],
    pool: WalletPool,
    rpc_client: Callable[[str, list], Any],
    chain_id: int,
    contract_code: str,
) -> str:
    """Send a single deploy tx from the root wallet, return its tx hash.

    The deploy must complete before the call workload starts so children
    have a real contract to target. Mirrors the way the upstream Go
    scenario sequences ``deployContract`` ahead of the per-tx loop
    (``calltx.go:331-371``).
    """
    from execution_testing.cli.pytest_commands.plugins.testing_build_block.tx_convert import (  # noqa: E501
        spamoor_dict_to_transaction,
    )

    nonce_hex = rpc_client(
        "eth_getTransactionCount", [str(pool.root_eoa), "pending"]
    )
    assert isinstance(nonce_hex, str)
    nonce = int(nonce_hex, 16)
    tip = int(spamoor_config.get("tip_fee") or 1_000_000_000)
    tx_dict = {
        "type": 2,
        "to": "",
        "value": 0,
        "data": contract_code,
        "gas": int(
            spamoor_config.get("deploy_gas_limit") or 2_000_000
        ),
        "maxFeePerGas": max(_max_fee_per_gas(spamoor_config), tip * 2),
        "maxPriorityFeePerGas": tip,
        "chainId": 1,
        "accessList": [],
    }
    tx = spamoor_dict_to_transaction(
        tx_dict, pool.root_eoa, chain_id, nonce_override=nonce
    )
    raw = tx.rlp().hex()
    if not raw.startswith("0x"):
        raw = "0x" + raw
    tx_hash = rpc_client("eth_sendRawTransaction", [raw])
    assert isinstance(tx_hash, str) and tx_hash.startswith("0x"), tx_hash
    deadline = time.time() + 60.0
    while time.time() < deadline:
        receipt = rpc_client("eth_getTransactionReceipt", [tx_hash])
        if receipt is not None:
            return tx_hash
        time.sleep(1.0)
    raise AssertionError(f"deploy tx {tx_hash} never mined within 60s")


def _run_calltx(
    spamoor_config: Dict[str, Any],
    spamoor_rpc_client: Callable[[str, list], Any],
    spamoor_wallet_pool: WalletPool,
    *,
    call_data: str,
    contract_code: str | None,
) -> None:
    chain_hex = spamoor_rpc_client("eth_chainId", [])
    assert isinstance(chain_hex, str)
    chain_id = int(chain_hex, 16)

    if contract_code:
        _send_root_deploy(
            spamoor_config,
            spamoor_wallet_pool,
            spamoor_rpc_client,
            chain_id,
            contract_code,
        )

    target_to = _resolved_target(spamoor_config)
    template = _calltx_dict(spamoor_config, target_to, call_data)

    def builder(_wallet: Wallet, _idx: int, _nonce: int) -> Dict[str, Any]:
        return dict(template)

    sizing = resolve_pool_sizing(spamoor_config)
    submit_workload(
        builder=builder,
        pool=spamoor_wallet_pool,
        rpc_client=spamoor_rpc_client,
        chain_id=chain_id,
        total_count=int(spamoor_config["count"]),
        throughput=float(spamoor_config.get("throughput") or 1.0),
        max_pending=sizing["max_pending"],
        skip_assert=bool(spamoor_config.get("skip_assert", False)),
    )


@pytest.mark.spamoor
def test_calltx_scenario_with_deploy(
    spamoor_config: Dict[str, Any],
    spamoor_rpc_client: Callable[[str, list], Any],
    spamoor_wallet_pool: WalletPool,
) -> None:
    _run_calltx(
        spamoor_config,
        spamoor_rpc_client,
        spamoor_wallet_pool,
        call_data=spamoor_config.get("call_data", "") or "0x1234",
        contract_code="0x6001600055",
    )


@pytest.mark.spamoor
def test_calltx_scenario_no_deploy(
    spamoor_config: Dict[str, Any],
    spamoor_rpc_client: Callable[[str, list], Any],
    spamoor_wallet_pool: WalletPool,
) -> None:
    _run_calltx(
        spamoor_config,
        spamoor_rpc_client,
        spamoor_wallet_pool,
        call_data=spamoor_config.get("call_data", "") or "0x1234",
        contract_code=None,
    )
