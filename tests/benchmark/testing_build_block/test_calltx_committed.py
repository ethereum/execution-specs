"""End-to-end: commit blocks of calltx workload using the wallet pool.

The committed-path test mirrors the spamoor-pytest flow in
``tests/benchmark/spamoor/test_calltx.py``: the same root key derives
the same HD-wallet pool (so child addresses match upstream spamoor
byte-for-byte), the root funds underfunded children before the
workload, and call transactions are signed by per-wallet round-robin
with per-wallet nonce sequencing. The only structural difference from
the spamoor pytest path is that here txs are committed via
``bloat_commit_block`` rather than broadcast through the EL mempool.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Sequence

import pytest
from execution_testing.base_types import Address, Hash
from execution_testing.cli.pytest_commands.plugins.spamoor.spamoor import (
    resolve_pool_sizing,
)
from execution_testing.cli.pytest_commands.plugins.spamoor.wallet_pool import (
    DEFAULT_REFILL_AMOUNT_WEI,
    DEFAULT_REFILL_BALANCE_WEI,
    WalletPool,
)
from execution_testing.cli.pytest_commands.plugins.testing_build_block.testing_build_block import (  # noqa: E501
    BloatConfig,
)
from execution_testing.cli.pytest_commands.plugins.testing_build_block.tx_convert import (  # noqa: E501
    spamoor_dict_to_transaction,
)
from execution_testing.rpc import EthRPC
from execution_testing.rpc.rpc_types import JSONRPCError
from execution_testing.test_types import EOA, Transaction


def _calltx_template(spamoor_config: Dict[str, Any]) -> Dict[str, Any]:
    """Match upstream spamoor's legacy fee strategy: feeCap = base_fee
    directly, with an EIP-1559 ``feeCap >= tip`` safety clamp.
    """
    basefee = int(spamoor_config.get("basefee") or 1_000_000_000)
    tip = int(spamoor_config.get("tip_fee") or 1_000_000_000)
    gas_limit = int(spamoor_config.get("gas_limit") or 0) or 500_000
    target = (
        spamoor_config.get("contract_address")
        or "0x1111111111111111111111111111111111111111"
    )
    call_data = spamoor_config.get("call_data") or "0x1234"
    return {
        "type": 2,
        "to": str(target),
        "value": int(spamoor_config.get("amount") or 0),
        "data": call_data,
        "gas": gas_limit,
        "maxFeePerGas": max(basefee, tip),
        "maxPriorityFeePerGas": tip,
        "chainId": 1,
        "accessList": [],
    }


def _build_pool(
    bloat_config: BloatConfig,
    bloat_eth_rpc: EthRPC,
    spamoor_config: Dict[str, Any],
) -> WalletPool:
    sizing = resolve_pool_sizing(spamoor_config)
    seed = str(spamoor_config.get("wallet_seed") or "")
    pool = WalletPool(
        bloat_config.signer_key,
        seed=seed,
        count=sizing["max_wallets"],
        refill_amount_wei=int(
            spamoor_config.get("refill_amount_wei") or 0
        ) or DEFAULT_REFILL_AMOUNT_WEI,
        refill_balance_wei=int(
            spamoor_config.get("refill_balance_wei") or 0
        ) or DEFAULT_REFILL_BALANCE_WEI,
    )
    for w in pool.wallets:
        try:
            n = bloat_eth_rpc.get_transaction_count(
                EOA(Address(w.address)), "latest"
            )
        except Exception:
            n = 0
        w.pending_nonce = int(n)
        w.confirmed_nonce = int(n) - 1
    return pool


def _funding_txs(
    pool: WalletPool,
    bloat_signer: EOA,
    bloat_config: BloatConfig,
    spamoor_config: Dict[str, Any],
    bloat_eth_rpc: EthRPC,
) -> List[Transaction]:
    """Emit root → child transfer txs sufficient to top each child to
    refill_balance_wei (mirrors WalletPool.prepare's math).
    """
    txs: List[Transaction] = []
    refill_amount = int(
        spamoor_config.get("refill_amount_wei") or 0
    ) or DEFAULT_REFILL_AMOUNT_WEI
    refill_balance = int(
        spamoor_config.get("refill_balance_wei") or 0
    ) or DEFAULT_REFILL_BALANCE_WEI
    tip = int(spamoor_config.get("tip_fee") or 1_000_000_000)
    basefee = int(spamoor_config.get("basefee") or 1_000_000_000)
    max_fee = max(int(basefee * 2), tip * 2)

    nonce = int(bloat_signer.nonce)
    for w in pool.wallets:
        try:
            balance = bloat_eth_rpc.get_balance(
                EOA(Address(w.address)), "latest"
            )
        except Exception:
            balance = 0
        if int(balance) >= refill_balance:
            continue
        amount = max(refill_amount, refill_balance - int(balance))
        funding_dict = {
            "type": 2,
            "to": w.address,
            "value": amount,
            "data": "",
            "gas": 21000,
            "maxFeePerGas": max_fee,
            "maxPriorityFeePerGas": tip,
            "chainId": 1,
            "accessList": [],
        }
        txs.append(
            spamoor_dict_to_transaction(
                funding_dict,
                bloat_signer,
                bloat_config.chain_id,
                nonce_override=nonce,
            )
        )
        nonce += 1
    return txs


def _deploy_tx(
    bloat_signer: EOA,
    bloat_config: BloatConfig,
    spamoor_config: Dict[str, Any],
    deploy_nonce: int,
) -> Transaction:
    tip = int(spamoor_config.get("tip_fee") or 1_000_000_000)
    basefee = int(spamoor_config.get("basefee") or 1_000_000_000)
    throughput = float(spamoor_config.get("throughput") or 1.0)
    deploy_dict = {
        "type": 2,
        "to": "",
        "value": 0,
        "data": spamoor_config.get("contract_code") or "",
        "gas": int(spamoor_config.get("deploy_gas_limit") or 2_000_000),
        "maxFeePerGas": max(int(basefee * (1.0 + throughput)), tip * 2),
        "maxPriorityFeePerGas": tip,
        "chainId": 1,
        "accessList": [],
    }
    return spamoor_dict_to_transaction(
        deploy_dict,
        bloat_signer,
        bloat_config.chain_id,
        nonce_override=deploy_nonce,
    )


def _build_call_txs(
    pool: WalletPool,
    bloat_config: BloatConfig,
    spamoor_config: Dict[str, Any],
) -> List[Transaction]:
    template = _calltx_template(spamoor_config)
    count = int(spamoor_config.get("count") or 0)
    out: List[Transaction] = []
    for _ in range(count):
        wallet = pool.pick()
        nonce = wallet.next_nonce()
        out.append(
            spamoor_dict_to_transaction(
                dict(template),
                wallet.eoa,
                bloat_config.chain_id,
                nonce_override=nonce,
            )
        )
    return out


def _chunk_by_gas(
    txs: Sequence[Transaction], block_gas_limit: int
) -> List[List[Transaction]]:
    chunks: List[List[Transaction]] = []
    current: List[Transaction] = []
    current_gas = 0
    for tx in txs:
        tx_gas = int(tx.gas_limit)
        if current and current_gas + tx_gas > block_gas_limit:
            chunks.append(current)
            current = []
            current_gas = 0
        current.append(tx)
        current_gas += tx_gas
    if current:
        chunks.append(current)
    return chunks


@pytest.mark.spamoor
@pytest.mark.testing_build_block
def test_calltx_committed(
    spamoor_config: Dict[str, Any],
    bloat_config: BloatConfig,
    bloat_signer: EOA,
    bloat_eth_rpc: EthRPC,
    bloat_commit_block: Callable[[Sequence[Transaction]], Hash],
) -> None:
    """Commit calltx workload across HD-derived wallet pool.

    Pre-funds each child wallet from the root signer, optionally deploys
    a contract from the root, then signs ``count`` call transactions with
    per-wallet round-robin sequencing. Order of txs handed to
    ``bloat_commit_block`` exactly matches what the spamoor pytest path
    submits to the EL mempool.
    """
    pool = _build_pool(bloat_config, bloat_eth_rpc, spamoor_config)

    funding = _funding_txs(
        pool, bloat_signer, bloat_config, spamoor_config, bloat_eth_rpc
    )
    deploy_nonce = int(bloat_signer.nonce) + len(funding)
    deploy: List[Transaction] = []
    if spamoor_config.get("contract_code"):
        deploy = [
            _deploy_tx(
                bloat_signer, bloat_config, spamoor_config, deploy_nonce
            )
        ]

    call_txs = _build_call_txs(pool, bloat_config, spamoor_config)
    if not call_txs and not funding and not deploy:
        pytest.skip("no transactions to commit")

    prev_head = bloat_eth_rpc.get_block_by_number("latest")
    assert prev_head is not None
    prev_number = int(prev_head["number"], 16)
    block_gas_limit = int(prev_head["gasLimit"], 16)

    all_txs: List[Transaction] = [*funding, *deploy, *call_txs]
    chunks = _chunk_by_gas(all_txs, block_gas_limit)

    skip_assert = bool(spamoor_config.get("skip_assert", False))
    new_head_hash: Hash | None = None
    committed = 0
    for chunk in chunks:
        try:
            new_head_hash = bloat_commit_block(chunk)
            committed += 1
        except JSONRPCError as exc:
            if not skip_assert:
                raise
            print(
                f"[skip_assert] bloat_commit_block failed on chunk of "
                f"{len(chunk)} tx(s): {exc}"
            )

    if skip_assert:
        return

    assert new_head_hash is not None
    new_head = bloat_eth_rpc.get_block_by_hash(new_head_hash)
    assert new_head is not None
    assert int(new_head["number"], 16) >= prev_number + committed
