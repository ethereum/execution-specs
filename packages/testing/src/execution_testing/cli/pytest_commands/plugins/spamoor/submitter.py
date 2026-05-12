"""
Rate-limited concurrent transaction submitter for the spamoor pytest path.

Mirrors the upstream Go implementation:

- Token-bucket rate limiter sized off ``throughput / slot_seconds``
  (``.lab/spamoor/scenario/txscenario.go:115-312``).
- ``max_pending`` cap enforced by a counting semaphore + condition
  variable (same file, lines 230-313).
- Per-tx watcher thread polls receipts, advances per-wallet
  confirmed_nonce, and rebroadcasts stale txs with bounded retries
  (``.lab/spamoor/spamoor/submitter.go``).

The submitter takes a *builder* callable that receives an assigned
:class:`Wallet` plus the global tx index and returns a raw tx dict
matching the existing ``tests/benchmark/spamoor/helpers.py`` shape.
The submitter signs each tx with the assigned wallet and broadcasts it
via ``eth_sendRawTransaction``.
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from .wallet_pool import Wallet, WalletPool


SLOT_SECONDS = 12.0
DEFAULT_REBROADCAST_AFTER_SLOTS = 1
MAX_REBROADCASTS = 4


# --- Rate limiter ------------------------------------------------------------


class _TokenBucket:
    """Simple monotonic-clock token bucket.

    `rate_per_sec` tokens per real-time second, with a 1-second burst
    capacity. ``acquire()`` blocks until a token is available.
    """

    def __init__(self, rate_per_sec: float) -> None:
        if rate_per_sec <= 0:
            raise ValueError("rate_per_sec must be > 0")
        self.rate = rate_per_sec
        self.capacity = max(rate_per_sec, 1.0)
        self._tokens = self.capacity
        self._last = time.monotonic()
        self._lock = threading.Lock()
        self._cond = threading.Condition(self._lock)

    def _refill_locked(self) -> None:
        now = time.monotonic()
        delta = now - self._last
        if delta > 0:
            self._tokens = min(self.capacity, self._tokens + delta * self.rate)
            self._last = now

    def acquire(self, stop_event: threading.Event) -> bool:
        """Block until a token is available (or stop_event is set)."""
        with self._cond:
            while not stop_event.is_set():
                self._refill_locked()
                if self._tokens >= 1.0:
                    self._tokens -= 1.0
                    return True
                missing = 1.0 - self._tokens
                wait = missing / self.rate
                self._cond.wait(timeout=wait)
        return False


# --- Result types ------------------------------------------------------------


@dataclass
class TxRecord:
    index: int
    wallet_address: str
    nonce: int
    tx_hash: str
    submitted_at: float
    confirmed_at: Optional[float] = None
    rebroadcasts: int = 0
    receipt: Optional[Dict[str, Any]] = None
    failed: bool = False
    reverted: bool = False
    error: Optional[str] = None


@dataclass
class WorkloadResult:
    submitted: int = 0
    confirmed: int = 0
    failed: int = 0
    pending: int = 0
    reverted: int = 0
    wall_clock_seconds: float = 0.0
    records: List[TxRecord] = field(default_factory=list)

    def asserts_pass(self) -> bool:
        return (
            self.failed == 0
            and self.pending == 0
            and self.reverted == 0
        )


def _receipt_status_ok(receipt: Dict[str, Any]) -> bool:
    """Return ``True`` if the receipt reports a successful execution.

    Pre-Byzantium receipts use ``root`` instead of ``status``; lacking
    either, we treat the receipt as successful since we cannot prove
    otherwise.
    """
    status = receipt.get("status")
    if status is None:
        return True
    if isinstance(status, int):
        return status == 1
    if isinstance(status, str):
        return int(status, 16) == 1
    return False


# --- Submitter --------------------------------------------------------------


def _sign_and_serialize(
    tx_dict: Dict[str, Any],
    wallet: Wallet,
    chain_id: int,
    nonce: int,
    fork: Any | None,
    blob_seed: int,
) -> str:
    # Imported lazily to keep this module light when only the rate limiter
    # is used (e.g. unit tests of the rate limiter alone).
    from execution_testing.cli.pytest_commands.plugins.testing_build_block.tx_convert import (  # noqa: E501
        spamoor_dict_to_transaction,
    )
    tx = spamoor_dict_to_transaction(
        tx_dict,
        wallet.eoa,
        chain_id,
        nonce_override=nonce,
        fork=fork,
        blob_seed=blob_seed,
    )
    raw = tx.rlp().hex()
    if not raw.startswith("0x"):
        raw = "0x" + raw
    return raw


def submit_workload(
    *,
    builder: Callable[[Wallet, int, int], Dict[str, Any]],
    pool: WalletPool,
    rpc_client: Callable[[str, List[Any]], Any],
    chain_id: int,
    total_count: int,
    throughput: float,
    max_pending: int,
    rebroadcast_after: float = SLOT_SECONDS * DEFAULT_REBROADCAST_AFTER_SLOTS,
    poll_interval: float = 1.0,
    drain_timeout: Optional[float] = None,
    fork: Any | None = None,
    blob_seed: int = 0,
    skip_assert: bool = False,
    allow_revert: bool = False,
) -> WorkloadResult:
    """
    Drive ``total_count`` transactions across the wallet pool.

    The caller supplies *builder*, invoked as
    ``builder(wallet, global_index, nonce)`` and returning a raw tx dict
    (the existing ``helpers.py`` shape: ``type``, ``to``, ``value``,
    ``data``, ``gas``, ``maxFeePerGas``, ``maxPriorityFeePerGas``,
    ``accessList``).

    Submission is paced at ``throughput`` tx/sec and capped at
    ``max_pending`` in-flight transactions. Each watcher polls
    ``eth_getTransactionReceipt`` every ``poll_interval`` seconds and
    rebroadcasts the same raw bytes after ``rebroadcast_after`` seconds
    of silence (up to ``MAX_REBROADCASTS`` times) before marking the tx
    failed.

    Returns a :class:`WorkloadResult`. With ``skip_assert=True`` the
    function never raises on partial inclusion — used for bloat-style
    load runs where dropped/pending receipts are expected.
    """
    if total_count <= 0:
        return WorkloadResult()
    if max_pending <= 0:
        raise ValueError("max_pending must be positive")

    if drain_timeout is None:
        # Empirically the kurtosis EL confirms ~16 tx/sec on this workload
        # (~50 tx/block × 6 s slot under preset:minimal); a 1.5× safety
        # factor leaves headroom for funding-warmup and basefee bumps.
        # The 120 s floor covers the cold-start case where the first
        # block lands a slot late.
        expected_secs = (total_count / 10.0) + 60.0
        drain_timeout = max(120.0, expected_secs)

    limiter = _TokenBucket(throughput) if throughput > 0 else None
    pending_sem = threading.BoundedSemaphore(max_pending)
    stop_event = threading.Event()
    rpc_lock = threading.Lock()

    records: List[TxRecord] = []
    records_lock = threading.Lock()
    confirmed_event = threading.Event()
    watcher_threads: List[threading.Thread] = []

    def call_rpc(method: str, params: List[Any]) -> Any:
        with rpc_lock:
            return rpc_client(method, params)

    def watch(record: TxRecord, raw_hex: str, wallet: Wallet) -> None:
        deadline = record.submitted_at + drain_timeout
        next_rebroadcast = record.submitted_at + rebroadcast_after
        while not stop_event.is_set():
            now = time.monotonic()
            if now >= deadline:
                record.failed = True
                record.error = "drain_timeout"
                break
            try:
                receipt = call_rpc(
                    "eth_getTransactionReceipt", [record.tx_hash]
                )
            except Exception as exc:  # pragma: no cover - defensive
                receipt = None
                record.error = f"poll_error: {exc}"
            if receipt:
                record.receipt = receipt
                record.confirmed_at = time.monotonic()
                if not _receipt_status_ok(receipt) and not allow_revert:
                    record.reverted = True
                    record.error = (
                        f"reverted: status={receipt.get('status')!r}"
                    )
                wallet.mark_confirmed(record.nonce)
                break
            if (
                time.monotonic() >= next_rebroadcast
                and record.rebroadcasts < MAX_REBROADCASTS
            ):
                # Skip the rebroadcast when the tx is still known to the
                # node (mempool or chain) — Nethermind replies
                # ``AlreadyKnown`` and the resend just spams the log.
                # ``eth_getTransactionByHash`` returns the tx for both
                # pending and mined states; only ``None`` means the node
                # has forgotten the tx and we need to re-send.
                try:
                    known = call_rpc(
                        "eth_getTransactionByHash", [record.tx_hash]
                    )
                except Exception:  # pragma: no cover - defensive
                    known = None
                if known is None:
                    try:
                        call_rpc("eth_sendRawTransaction", [raw_hex])
                    except Exception:  # already-known is fine
                        pass
                    record.rebroadcasts += 1
                next_rebroadcast = time.monotonic() + rebroadcast_after
            time.sleep(poll_interval)
        try:
            pending_sem.release()
        except ValueError:
            # Already released because of an early submission failure.
            pass
        confirmed_event.set()

    start = time.monotonic()
    submitted = 0
    for i in range(total_count):
        if limiter is not None and not limiter.acquire(stop_event):
            break
        pending_sem.acquire()
        wallet = pool.pick()
        nonce = wallet.next_nonce()
        try:
            tx_dict = builder(wallet, i, nonce)
            raw_hex = _sign_and_serialize(
                tx_dict, wallet, chain_id, nonce, fork, blob_seed
            )
            tx_hash = call_rpc("eth_sendRawTransaction", [raw_hex])
            if not (isinstance(tx_hash, str) and tx_hash.startswith("0x")):
                # rpc_client may stash a structured error here; surface it.
                last_err = getattr(rpc_client, "last_error", None)
                detail = f"; last_error={last_err}" if last_err else ""
                raise RuntimeError(
                    f"eth_sendRawTransaction returned {tx_hash!r}{detail}"
                )
        except Exception as exc:
            with records_lock:
                rec = TxRecord(
                    index=i,
                    wallet_address=wallet.address,
                    nonce=nonce,
                    tx_hash="",
                    submitted_at=time.monotonic(),
                    failed=True,
                    error=f"submit_error: {exc}",
                )
                records.append(rec)
            pending_sem.release()
            continue

        record = TxRecord(
            index=i,
            wallet_address=wallet.address,
            nonce=nonce,
            tx_hash=tx_hash,
            submitted_at=time.monotonic(),
        )
        with records_lock:
            records.append(record)
        submitted += 1
        t = threading.Thread(
            target=watch, args=(record, raw_hex, wallet), daemon=True
        )
        t.start()
        watcher_threads.append(t)

    deadline = time.monotonic() + drain_timeout
    for t in watcher_threads:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            break
        t.join(timeout=remaining)
    stop_event.set()

    confirmed = sum(
        1
        for r in records
        if r.receipt is not None and not r.failed and not r.reverted
    )
    failed = sum(1 for r in records if r.failed)
    reverted = sum(1 for r in records if r.reverted)
    pending = sum(
        1 for r in records if r.receipt is None and not r.failed
    )
    result = WorkloadResult(
        submitted=submitted,
        confirmed=confirmed,
        failed=failed,
        pending=pending,
        reverted=reverted,
        wall_clock_seconds=time.monotonic() - start,
        records=records,
    )
    if not skip_assert and not result.asserts_pass():
        sample = next(
            (r.error for r in records if r.error), "<no error captured>"
        )
        raise AssertionError(
            f"workload incomplete: submitted={result.submitted} "
            f"confirmed={result.confirmed} pending={result.pending} "
            f"failed={result.failed} reverted={result.reverted}; "
            f"first error: {sample}"
        )
    return result


__all__ = [
    "MAX_REBROADCASTS",
    "SLOT_SECONDS",
    "TxRecord",
    "WorkloadResult",
    "submit_workload",
]
