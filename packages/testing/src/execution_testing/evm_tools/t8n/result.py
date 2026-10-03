"""
Build the testing-side ``Result`` from an executed block.

All construction of ``Result`` and ``TransactionReceipt`` lives here
so the testing-package pydantic types stay isolated to one boundary
module.
"""

from typing import TYPE_CHECKING, Any, Dict, List, Optional

from ethereum.crypto.hash import Hash32, keccak256
from ethereum.exceptions import InvalidBlock
from ethereum.merkle_patricia_trie import root, trie_get
from ethereum.state import BlockDiff
from ethereum_rlp import rlp
from ethereum_types.bytes import Bytes

if TYPE_CHECKING:
    from execution_testing.client_clis.cli_types import (
        Result as TestingResult,
    )

    from . import T8N


def get_receipts_from_output(t8n: "T8N", block_output: Any) -> List[Any]:
    """Build testing-side `TransactionReceipt`s from the block output tries."""
    # Function-scoped: ``execution_testing/__init__`` eagerly imports
    # ``.specs`` -> ``client_clis`` -> ``ExecutionSpecsTransitionTool``,
    # which imports ``t8n`` to run it in-process. A top-level import here
    # would run while ``client_clis`` is still mid-initialization.
    from execution_testing.test_types.receipt_types import (
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


def _ordered_block_headers(t8n: "T8N") -> List[Bytes]:
    """
    Return the preceding block headers in increasing block-number order.

    Once header data is provided, require a contiguous sequence covering
    the available 256-block history, matching the legacy T8N behavior.
    """
    if not t8n.fork.has_execution_witness or not t8n.env.block_headers:
        return []

    headers_by_number = {
        int(number): Bytes(bytes(header))
        for number, header in t8n.env.block_headers.items()
    }
    block_number = int(t8n.env.number)
    max_count = min(256, block_number)
    headers: List[Bytes] = []
    for number in range(block_number - max_count, block_number):
        try:
            headers.append(headers_by_number[number])
        except KeyError:
            raise ValueError(
                f"missing block header for block {number}"
            ) from None
    return headers


def _build_execution_witness(
    t8n: "T8N",
    block_env: Any,
    state_root: Hash32,
) -> Any:
    """Build an execution witness against the still-unmodified pre-state."""
    # ``Alloc`` is the live PreState used during execution. Materialize an
    # independent MPT mirror here because the Amsterdam witness builder needs
    # the flat pre-state tries. ``T8N.run`` applies the block diff only after
    # ``build_result`` returns, so this is still the original pre-state.
    pre_state = t8n.alloc._materialize_state()
    return t8n.fork.build_execution_witness(
        block_env.state,
        expected_post_state_root=state_root,
        pre_state_accounts_data=pre_state._main_trie,
        pre_state_storages_data=pre_state._storage_tries,
        blockchain_headers=_ordered_block_headers(t8n),
    )


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
    try:
        state_root = t8n.alloc.compute_state_root(diff)
    except InvalidBlock as e:
        # The executed block produced state that cannot be committed
        # (e.g. a balance past the sixteen-byte basic data field). Such
        # a block is rejected and leaves the chain state unchanged, so
        # report the pre-state root.
        if block_exception is None:
            block_exception = f"{e}"
        state_root = t8n.alloc.compute_state_root(BlockDiff())

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

    if t8n.fork.has_execution_witness and not t8n.skip_stateless_validation:
        execution_witness = _build_execution_witness(
            t8n, block_env, state_root
        )
        arguments["execution_witness"] = {
            "state": [bytes(node) for node in execution_witness.state],
            "codes": [bytes(code) for code in execution_witness.codes],
            "headers": [bytes(header) for header in execution_witness.headers],
        }

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
