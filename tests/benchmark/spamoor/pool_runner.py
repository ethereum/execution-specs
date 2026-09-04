"""
Shared runner that dispatches spamoor scenario tx-dicts through the
HD-derived wallet pool.

Each scenario's existing ``build_X_transactions`` helper produces a list
of EIP-1559 tx dicts in roughly the shape spamoor's Go scenarios emit.
Historically those dicts came with sequential nonces from a single
signer plus a throughput-multiplied ``maxFeePerGas`` — both wrong against
the spamoor parity goal. ``submit_pool_workload`` re-routes the same
list through the pool: it strips the per-tx nonce so the pool can assign
one (per-wallet sequential), rewrites fees to upstream's legacy strategy
(``feeCap = base_fee_wei`` directly), and submits via
:func:`submit_workload`.

Use ``root_setup_txs`` for any deploy/setup that must come from the root
EOA before the per-wallet workload starts (the calltx scenario does this
for the contract deploy that the call txs target).
"""

from __future__ import annotations

import time
from typing import Any, Callable, Dict, List, Optional

from execution_testing.cli.pytest_commands.plugins.spamoor.spamoor import (
    resolve_pool_sizing,
)
from execution_testing.cli.pytest_commands.plugins.spamoor.submitter import (
    submit_workload,
)
from execution_testing.cli.pytest_commands.plugins.spamoor.wallet_pool import (
    Wallet,
    WalletPool,
)


def upstream_fee(spamoor_config: Dict[str, Any]) -> tuple[int, int]:
    """``feeCap = max(base_fee_wei, tip)``; ``tipCap = tip_fee``.

    Mirrors ``.lab/spamoor/spamoor/txpool.go:1626-1631``.
    """
    basefee = int(spamoor_config.get("basefee") or 1_000_000_000)
    tip = int(spamoor_config.get("tip_fee") or 1_000_000_000)
    return max(basefee, tip), tip


def normalize_tx_dicts(
    tx_dicts: List[Dict[str, Any]], spamoor_config: Dict[str, Any]
) -> None:
    """Strip nonces and rewrite fees in place.

    The scenario builders set the nonce assuming a single signer; the
    pool runner re-assigns per-wallet nonces, so the pre-set value would
    just collide. Fees are coerced to upstream-style basefee.
    """
    max_fee, tip = upstream_fee(spamoor_config)
    for tx in tx_dicts:
        tx.pop("nonce", None)
        if int(tx.get("type", 2)) in (2, 3):
            tx["maxFeePerGas"] = max_fee
            tx["maxPriorityFeePerGas"] = tip


def _send_root_tx(
    *,
    rpc_client: Callable[[str, List[Any]], Any],
    pool: WalletPool,
    chain_id: int,
    tx_dict: Dict[str, Any],
    nonce: int,
    timeout: float = 60.0,
) -> int:
    """Sign-and-send a single tx from the root EOA, block until receipt.

    Returns the next root nonce. Raises if the EL never confirms within
    *timeout*; setup txs must complete before the workload starts.
    """
    from execution_testing.cli.pytest_commands.plugins.testing_build_block.tx_convert import (  # noqa: E501
        spamoor_dict_to_transaction,
    )

    tx_dict.pop("nonce", None)
    signed = spamoor_dict_to_transaction(
        tx_dict, pool.root_eoa, chain_id, nonce_override=nonce
    )
    raw = signed.rlp().hex()
    if not raw.startswith("0x"):
        raw = "0x" + raw
    tx_hash = rpc_client("eth_sendRawTransaction", [raw])
    if not (isinstance(tx_hash, str) and tx_hash.startswith("0x")):
        last_err = getattr(rpc_client, "last_error", None)
        raise RuntimeError(
            f"setup tx submission failed (response={tx_hash!r}, "
            f"last_error={last_err})"
        )
    deadline = time.time() + timeout
    while time.time() < deadline:
        if rpc_client("eth_getTransactionReceipt", [tx_hash]) is not None:
            return nonce + 1
        time.sleep(1.0)
    raise AssertionError(
        f"setup tx {tx_hash} not mined within {timeout}s"
    )


def submit_pool_workload(
    *,
    spamoor_config: Dict[str, Any],
    rpc_client: Callable[[str, List[Any]], Any],
    pool: WalletPool,
    tx_dicts: List[Dict[str, Any]],
    root_setup_txs: Optional[List[Dict[str, Any]]] = None,
    fork: Any | None = None,
    blob_seed: int = 0,
) -> None:
    """End-to-end: optional root setup, then per-wallet submission.

    Skips the test (via ``pytest.skip``) when *tx_dicts* is empty so the
    common ``count=0`` no-op case stays uniform with the original
    ``broadcast_and_assert_receipts`` semantics.
    """
    import pytest

    def _tx_cost(tx: Dict[str, Any]) -> int:
        gas = int(tx.get("gas") or 0)
        max_fee = int(tx.get("maxFeePerGas") or 0)
        value = int(tx.get("value") or 0)
        return gas * max_fee + value

    if not tx_dicts:
        pytest.skip("scenario produced no transactions")
    if any(int(tx.get("type", 0)) == 3 for tx in tx_dicts):
        # eth_sendRawTransaction needs EIP-4844 network-form RLP with
        # blobs/commitments/proofs sidecars; ``Transaction.rlp()`` only
        # produces block-form (payload only). Mirrors the skip path in
        # ``broadcast_and_assert_receipts``.
        pytest.skip(
            "type-3 blob broadcast needs network-form RLP with sidecars"
        )

    chain_hex = rpc_client("eth_chainId", [])
    if not isinstance(chain_hex, str):
        pytest.skip("spamoor endpoint unreachable (eth_chainId failed)")
    chain_id = int(chain_hex, 16)

    normalize_tx_dicts(tx_dicts, spamoor_config)
    if root_setup_txs:
        normalize_tx_dicts(root_setup_txs, spamoor_config)

    if root_setup_txs:
        root_nonce_hex = rpc_client(
            "eth_getTransactionCount", [str(pool.root_eoa), "pending"]
        )
        if not isinstance(root_nonce_hex, str):
            pytest.skip("eth_getTransactionCount(root) failed")
        root_nonce = int(root_nonce_hex, 16)
        for tx in root_setup_txs:
            root_nonce = _send_root_tx(
                rpc_client=rpc_client,
                pool=pool,
                chain_id=chain_id,
                tx_dict=tx,
                nonce=root_nonce,
            )

    # Per-wallet top-up: scan the workload to compute each wallet's
    # cumulative cost (gas reservation + value), then send a root → child
    # transfer to cover any deficit. The fixture's static refill_amount
    # only covers a uniform-cost workload; scenarios like uniswap-swaps
    # carry random per-tx ``value`` up to thousands of ETH and would
    # otherwise blow past the 5 ETH default refill mid-run.
    n_wallets = len(pool)
    cost_by_wallet: List[int] = [0] * n_wallets
    for i, tx in enumerate(tx_dicts):
        cost_by_wallet[i % n_wallets] += _tx_cost(tx)

    deficits: List[tuple[int, int]] = []
    for idx in range(n_wallets):
        try:
            balance_hex = rpc_client(
                "eth_getBalance", [pool.by_index(idx).address, "latest"]
            )
            balance = int(balance_hex, 16) if isinstance(balance_hex, str) else 0
        except Exception:
            balance = 0
        # 1.25× headroom covers basefee bumps between funding tx and
        # the workload's last tx.
        needed = int(cost_by_wallet[idx] * 1.25)
        if balance < needed:
            deficits.append((idx, needed - balance))

    if deficits:
        max_fee, tip = upstream_fee(spamoor_config)
        funding_max_fee = max(max_fee, tip * 2)
        root_nonce_hex = rpc_client(
            "eth_getTransactionCount", [str(pool.root_eoa), "pending"]
        )
        if not isinstance(root_nonce_hex, str):
            pytest.skip("eth_getTransactionCount(root) failed (top-up)")
        root_nonce = int(root_nonce_hex, 16)
        for child_idx, amount in deficits:
            root_nonce = _send_root_tx(
                rpc_client=rpc_client,
                pool=pool,
                chain_id=chain_id,
                tx_dict={
                    "type": 2,
                    "to": pool.by_index(child_idx).address,
                    "value": amount,
                    "data": "",
                    "gas": 21000,
                    "maxFeePerGas": funding_max_fee,
                    "maxPriorityFeePerGas": tip,
                    "chainId": 1,
                    "accessList": [],
                },
                nonce=root_nonce,
            )

    sizing = resolve_pool_sizing(spamoor_config)
    submit_workload(
        builder=lambda _w, i, _n: tx_dicts[i],
        pool=pool,
        rpc_client=rpc_client,
        chain_id=chain_id,
        total_count=len(tx_dicts),
        throughput=float(spamoor_config.get("throughput") or 1.0),
        max_pending=sizing["max_pending"],
        skip_assert=bool(spamoor_config.get("skip_assert", False)),
        allow_revert=bool(spamoor_config.get("allow_revert", False)),
        fork=fork,
        blob_seed=blob_seed,
    )


__all__ = [
    "normalize_tx_dicts",
    "submit_pool_workload",
    "upstream_fee",
]
