"""
HD-derived wallet pool for spamoor-style multi-wallet load generation.

Mirrors the upstream Go implementation at
``.lab/spamoor/spamoor/walletpool.go`` (``prepareChildWallet``,
``calculateFundingAmount``) and ``.lab/spamoor/spamoor/wallet.go``
(``GetNextNonce``, pending/confirmed split). The derivation is byte-for-byte
identical so a `(root_key, seed, count)` tuple yields the same child
addresses as the upstream binary — required for the EST committed-path
tests to enqueue from the same accounts as the spamoor-pytest path.
"""

from __future__ import annotations

import hashlib
import struct
import threading
from dataclasses import dataclass, field
from typing import Any, Callable, List, Optional

from execution_testing.test_types import EOA


# Defaults matching .lab/spamoor/scenario/txscenario.go:140-165 and
# .lab/spamoor/spamoor/walletpool_config.go.
DEFAULT_MAX_WALLETS_MIN = 10
DEFAULT_MAX_WALLETS_MAX = 1000
DEFAULT_REFILL_AMOUNT_WEI = 5 * 10**18
DEFAULT_REFILL_BALANCE_WEI = 1 * 10**18


def derive_child_key(root_key: bytes, idx: int, seed: str = "") -> bytes:
    """
    Derive a 32-byte child private key from the root key.

    Mirrors ``prepareChildWallet`` in walletpool.go:573-590:
    ``sha256(root_priv || u64_be(idx) || seed_bytes)``.
    """
    if len(root_key) != 32:
        raise ValueError(
            f"root_key must be 32 raw bytes, got {len(root_key)}"
        )
    payload = root_key + struct.pack(">Q", idx) + seed.encode("utf-8")
    return hashlib.sha256(payload).digest()


def default_max_wallets(total_count: int) -> int:
    """Match `txscenario.go:159-165`: clamp(total_count // 50, 10, 1000)."""
    proposed = max(1, total_count // 50)
    return max(DEFAULT_MAX_WALLETS_MIN, min(DEFAULT_MAX_WALLETS_MAX, proposed))


def _normalize_root_key(key: str | bytes) -> bytes:
    if isinstance(key, str):
        key = key.removeprefix("0x")
        key = bytes.fromhex(key)
    if len(key) != 32:
        raise ValueError(
            f"root key must be 32 bytes, got {len(key)}"
        )
    return key


@dataclass
class Wallet:
    """A single derived wallet with thread-safe nonce tracking.

    pending_nonce is the next nonce to hand out; confirmed_nonce is the
    highest nonce known to be mined. Mirrors the split in wallet.go:300-348.
    """

    eoa: EOA
    pending_nonce: int = 0
    confirmed_nonce: int = -1
    _lock: threading.Lock = field(
        default_factory=threading.Lock, repr=False, compare=False
    )

    @property
    def address(self) -> str:
        return str(self.eoa)

    @property
    def key_hex(self) -> str:
        assert self.eoa.key is not None
        return f"0x{bytes(self.eoa.key).hex()}"

    def next_nonce(self) -> int:
        """Atomically reserve the next pending nonce."""
        with self._lock:
            n = self.pending_nonce
            self.pending_nonce = n + 1
            return n

    def mark_confirmed(self, nonce: int) -> None:
        """Advance confirmed_nonce; never moves backward."""
        with self._lock:
            if nonce > self.confirmed_nonce:
                self.confirmed_nonce = nonce
            if nonce >= self.pending_nonce:
                self.pending_nonce = nonce + 1

    def in_flight(self) -> int:
        with self._lock:
            return max(0, self.pending_nonce - self.confirmed_nonce - 1)

    def sync_pending(self, pending_nonce: int) -> None:
        """Sync pending_nonce from chain (e.g. after a re-run)."""
        with self._lock:
            if pending_nonce > self.pending_nonce:
                self.pending_nonce = pending_nonce


@dataclass
class FundingTx:
    """A pending root → child transfer emitted by ``WalletPool.prepare()``."""

    to_address: str
    value_wei: int
    child_index: int


class WalletPool:
    """A deterministic pool of HD-derived child wallets."""

    def __init__(
        self,
        root_key: str | bytes,
        *,
        seed: str = "",
        count: int,
        refill_amount_wei: int = DEFAULT_REFILL_AMOUNT_WEI,
        refill_balance_wei: int = DEFAULT_REFILL_BALANCE_WEI,
    ) -> None:
        if count <= 0:
            raise ValueError("count must be positive")
        root_bytes = _normalize_root_key(root_key)
        self.root_key = root_bytes
        self.root_eoa = EOA(key=root_bytes)
        self.seed = seed
        self.refill_amount_wei = refill_amount_wei
        self.refill_balance_wei = refill_balance_wei

        self.wallets: List[Wallet] = [
            Wallet(eoa=EOA(key=derive_child_key(root_bytes, i, seed)))
            for i in range(count)
        ]
        self._rr_lock = threading.Lock()
        self._rr_idx = 0

    def __len__(self) -> int:
        return len(self.wallets)

    def by_index(self, idx: int) -> Wallet:
        return self.wallets[idx]

    def pick(self) -> Wallet:
        """Round-robin wallet selection."""
        with self._rr_lock:
            w = self.wallets[self._rr_idx % len(self.wallets)]
            self._rr_idx += 1
            return w

    def prepare(
        self,
        rpc_client: Callable[[str, List[Any]], Any],
    ) -> List[FundingTx]:
        """Compute funding transfers needed to bring each child up to balance.

        Mirrors ``calculateFundingAmount`` in walletpool.go:626-638:
        ``funding = max(refill_amount, refill_balance - current_balance)``
        when ``current_balance < refill_balance``; emit nothing otherwise.

        Also synchronizes each wallet's ``pending_nonce`` with whatever the
        EL already remembers — important on re-runs against a non-clean
        kurtosis enclave so we don't reuse mined nonces.
        """
        funding: List[FundingTx] = []
        for idx, wallet in enumerate(self.wallets):
            balance_hex = rpc_client(
                "eth_getBalance", [wallet.address, "pending"]
            )
            current = int(balance_hex, 16) if isinstance(balance_hex, str) \
                else 0
            nonce_hex = rpc_client(
                "eth_getTransactionCount", [wallet.address, "pending"]
            )
            if isinstance(nonce_hex, str):
                wallet.sync_pending(int(nonce_hex, 16))
                wallet.confirmed_nonce = wallet.pending_nonce - 1

            if current >= self.refill_balance_wei:
                continue
            need = self.refill_balance_wei - current
            amount = max(self.refill_amount_wei, need)
            funding.append(
                FundingTx(
                    to_address=wallet.address,
                    value_wei=amount,
                    child_index=idx,
                )
            )
        return funding


__all__ = [
    "DEFAULT_MAX_WALLETS_MAX",
    "DEFAULT_MAX_WALLETS_MIN",
    "DEFAULT_REFILL_AMOUNT_WEI",
    "DEFAULT_REFILL_BALANCE_WEI",
    "FundingTx",
    "Wallet",
    "WalletPool",
    "default_max_wallets",
    "derive_child_key",
]
