"""
Build the testing-side ``Result`` from an executed block.

All construction of ``Result`` and ``TransactionReceipt`` lives here
so the testing-package pydantic types stay isolated to one boundary
module.
"""

from typing import TYPE_CHECKING, Any, Dict, List, Optional

from ethereum_rlp import rlp

from ethereum.crypto.hash import keccak256
from ethereum.merkle_patricia_trie import root, trie_get

if TYPE_CHECKING:
    from execution_testing.client_clis.cli_types import (
        Result as TestingResult,
    )

    from . import T8N


def get_receipts_from_output(t8n: "T8N", block_output: Any) -> List[Any]:
    """Build testing-side `TransactionReceipt`s from the block output tries."""
    # Function-scoped: ``execution_testing/__init__`` eagerly imports
    # ``.specs`` which transitively imports ``client_clis``, which
    # imports ``ExecutionSpecsTransitionTool`` — top-level import would
    # cycle back into ``t8n``.
    from execution_testing.test_types.receipt_types import (
        FrameReceipt,
        TransactionLog,
        TransactionReceipt,
    )

    receipts: List[Any] = []
    for key in block_output.receipt_keys:
        tx = trie_get(block_output.transactions_trie, key)
        receipt = trie_get(block_output.receipts_trie, key)
        assert tx is not None
        assert receipt is not None

        tx_hash = t8n.fork.get_transaction_hash(tx)

        if hasattr(t8n.fork, "decode_receipt"):
            decoded_receipt = t8n.fork.decode_receipt(receipt)
        else:
            decoded_receipt = receipt

        if hasattr(decoded_receipt, "frame_receipts"):
            # EIP-8141 frame transaction receipt: no transaction-level
            # status and no consensus bloom — the logs are reported per
            # frame, and the bloom is derived from their concatenation
            # in frame order.
            all_logs = [
                log
                for frame_receipt in decoded_receipt.frame_receipts
                for log in frame_receipt.logs
            ]
            receipts.append(
                TransactionReceipt(
                    transaction_hash=tx_hash,
                    cumulative_gas_used=int(
                        decoded_receipt.cumulative_gas_used
                    ),
                    bloom=t8n.fork.logs_bloom(tuple(all_logs)),
                    logs=[
                        TransactionLog(
                            address=log.address,
                            topics=list(log.topics),
                            data=log.data,
                        )
                        for log in all_logs
                    ],
                    payer=decoded_receipt.payer,
                    frame_receipts=[
                        FrameReceipt(
                            status=int(frame_receipt.status),
                            gas_used=int(frame_receipt.gas_used),
                            logs=[
                                TransactionLog(
                                    address=log.address,
                                    topics=list(log.topics),
                                    data=log.data,
                                )
                                for log in frame_receipt.logs
                            ],
                        )
                        for frame_receipt in decoded_receipt.frame_receipts
                    ],
                )
            )
            continue

        receipt_kwargs: Dict[str, Any] = {
            "transaction_hash": tx_hash,
            "cumulative_gas_used": int(decoded_receipt.cumulative_gas_used),
            "bloom": decoded_receipt.bloom,
            "logs": [
                TransactionLog(
                    address=log.address,
                    topics=list(log.topics),
                    data=log.data,
                )
                for log in decoded_receipt.logs
            ],
        }
        if hasattr(decoded_receipt, "succeeded"):
            receipt_kwargs["status"] = int(decoded_receipt.succeeded)
        elif hasattr(decoded_receipt, "post_state"):
            receipt_kwargs["post_state"] = decoded_receipt.post_state
        receipts.append(TransactionReceipt(**receipt_kwargs))
    return receipts


def build_result(
    t8n: "T8N",
    block_env: Any,
    block_output: Any,
    block_exception: Optional[str],
    rejected_transactions: List[Any],
) -> "TestingResult":
    """Build the testing-side `Result` from the executed block."""
    # Function-scoped: see import-cycle note in ``get_receipts_from_output``.
    from execution_testing.client_clis.cli_types import Result as TestingResult

    diff = t8n.fork.extract_block_diff(t8n._block_state)
    state_root = t8n.alloc.compute_state_root(diff)

    arguments: Dict[str, Any] = {
        "state_root": state_root,
        "transactions_trie": root(block_output.transactions_trie),
        "receipts_root": root(block_output.receipts_trie),
        "logs_hash": keccak256(rlp.encode(block_output.block_logs)),
        "logs_bloom": t8n.fork.logs_bloom(block_output.block_logs),
        "receipts": get_receipts_from_output(t8n, block_output),
        "rejected_transactions": rejected_transactions,
        "gas_used": int(block_output.block_gas_used),
    }
    if hasattr(block_output, "block_state_gas_used"):
        if int(block_output.block_state_gas_used) > arguments["gas_used"]:
            arguments["gas_used"] = int(block_output.block_state_gas_used)
    if block_exception is not None:
        arguments["block_exception"] = block_exception
    if hasattr(block_env, "difficulty"):
        arguments["difficulty"] = int(block_env.difficulty)
    if hasattr(block_env, "base_fee_per_gas"):
        arguments["base_fee_per_gas"] = int(block_env.base_fee_per_gas)
    if hasattr(block_output, "withdrawals_trie"):
        arguments["withdrawals_root"] = root(block_output.withdrawals_trie)
    if hasattr(block_env, "excess_blob_gas"):
        arguments["excess_blob_gas"] = int(block_env.excess_blob_gas)
        arguments["blob_gas_used"] = int(block_output.blob_gas_used)
    if hasattr(block_output, "requests"):
        arguments["requests"] = list(block_output.requests)
        arguments["requests_hash"] = t8n.fork.compute_requests_hash(
            block_output.requests
        )
    if hasattr(block_output, "block_access_list"):
        arguments["block_access_list"] = rlp.encode(
            block_output.block_access_list
        )
        arguments["block_access_list_hash"] = t8n.fork.hash_block_access_list(
            block_output.block_access_list
        )

    context: Optional[Dict[str, Any]] = None
    if t8n.exception_mapper is not None:
        context = {"exception_mapper": t8n.exception_mapper}
    return TestingResult.model_validate(arguments, context=context)


def record_rejected_tx(t8n: "T8N", index: int, error: Exception) -> None:
    """Append a ``RejectedTransaction`` to ``t8n.rejected_transactions``."""
    # Function-scoped: see import-cycle note in ``get_receipts_from_output``.
    from execution_testing.client_clis.cli_types import RejectedTransaction

    context: Optional[Dict[str, Any]] = None
    if t8n.exception_mapper is not None:
        context = {"exception_mapper": t8n.exception_mapper}
    t8n.rejected_transactions.append(
        RejectedTransaction.model_validate(
            {"index": index, "error": f"Failed transaction: {error!r}"},
            context=context,
        )
    )


__all__ = [
    "build_result",
    "get_receipts_from_output",
    "record_rejected_tx",
]
