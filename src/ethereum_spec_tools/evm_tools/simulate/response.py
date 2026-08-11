"""
Render simulated blocks as the `EthSimulateResult` the schema describes.

Each entry is a full `Block` object with a `calls` array appended, so
every field an ordinary `eth_getBlockByNumber` reports has to be filled
in for a block that was never mined. The values come from
`ethereum_spec_tools.evm_tools.simulate`; this module only formats them.
"""

from typing import Any, Dict, List

from ethereum_types.bytes import Bytes

from .context import EMPTY_OMMERS_HASH
from .errors import REVERT_ERROR_CODE, VM_ERROR_CODE


def _quantity(value: Any) -> str:
    """Format an integer as the schema's minimal hex."""
    return hex(int(value))


def _data(value: Any) -> str:
    """Format a byte string as hex."""
    return "0x" + bytes(value).hex()


def render_result(
    blocks: List[Any], *, full_transactions: bool = False
) -> List[Dict[str, Any]]:
    """Render the whole `EthSimulateResult`."""
    return [
        render_block(block, full_transactions=full_transactions)
        for block in blocks
    ]


def render_block(
    block: Any, *, full_transactions: bool = False
) -> Dict[str, Any]:
    """Render one simulated block, calls included."""
    header = block.header
    rendered: Dict[str, Any] = {
        "hash": _data(block.block_hash),
        "parentHash": _data(header.parent_hash),
        "sha3Uncles": _data(EMPTY_OMMERS_HASH),
        "miner": _data(header.coinbase),
        "stateRoot": _data(header.state_root),
        "transactionsRoot": _data(header.transactions_root),
        "receiptsRoot": _data(header.receipt_root),
        "logsBloom": _data(header.bloom),
        "difficulty": _quantity(header.difficulty),
        "number": _quantity(header.number),
        "gasLimit": _quantity(header.gas_limit),
        "gasUsed": _quantity(header.gas_used),
        "timestamp": _quantity(header.timestamp),
        "extraData": _data(header.extra_data),
        "mixHash": _data(header.prev_randao),
        "nonce": _data(header.nonce),
        "size": _quantity(block.size),
        "uncles": [],
        "transactions": (
            [
                render_transaction(transaction, result, block)
                for transaction, result in zip(
                    block.transactions, block.call_results, strict=False
                )
            ]
            if full_transactions
            else [
                _data(result.transaction_hash) for result in block.call_results
            ]
        ),
        "calls": [render_call(result, block) for result in block.call_results],
    }
    for name, attribute in (
        ("baseFeePerGas", "base_fee_per_gas"),
        ("withdrawalsRoot", "withdrawals_root"),
        ("blobGasUsed", "blob_gas_used"),
        ("excessBlobGas", "excess_blob_gas"),
        ("parentBeaconBlockRoot", "parent_beacon_block_root"),
        ("requestsHash", "requests_hash"),
    ):
        if hasattr(header, attribute):
            value = getattr(header, attribute)
            rendered[name] = (
                _data(value)
                if isinstance(value, (bytes, Bytes))
                else _quantity(value)
            )
    if hasattr(header, "withdrawals_root"):
        rendered["withdrawals"] = [
            render_withdrawal(withdrawal) for withdrawal in block.withdrawals
        ]
    return rendered


def render_withdrawal(withdrawal: Any) -> Dict[str, Any]:
    """Render one withdrawal a simulated block paid out."""
    return {
        "index": _quantity(withdrawal.index),
        "validatorIndex": _quantity(withdrawal.validator_index),
        "address": _data(withdrawal.address),
        "amount": _quantity(withdrawal.amount),
    }


def transaction_type(transaction: Any) -> int:
    """
    Return the envelope a synthetic transaction was built in.

    Read off the fields the class declares rather than carried
    alongside, so that the renderer and the transactions trie can never
    disagree about what was actually put in the block.
    """
    if not hasattr(transaction, "chain_id"):
        return 0
    if hasattr(transaction, "blob_versioned_hashes"):
        return 3
    if hasattr(transaction, "max_fee_per_gas"):
        return 2
    return 1


def render_transaction(
    transaction: Any, result: Any, block: Any
) -> Dict[str, Any]:
    """
    Render a synthetic transaction as `returnFullTransactions` asks.

    The signature fields are reported as the zeroes they were built
    with, and `gasPrice` holds the effective price rather than anything
    the caller set — the same convention an ordinary transaction follows
    over RPC.
    """
    kind = transaction_type(transaction)
    signature_parity = transaction.v if kind == 0 else transaction.y_parity
    rendered: Dict[str, Any] = {
        "hash": _data(result.transaction_hash),
        "blockHash": _data(block.block_hash),
        "blockNumber": _quantity(block.header.number),
        "blockTimestamp": _quantity(block.header.timestamp),
        "transactionIndex": _quantity(result.transaction_index),
        "from": _data(result.sender),
        "to": (_data(transaction.to) if len(bytes(transaction.to)) else None),
        "gas": _quantity(transaction.gas),
        "gasPrice": _quantity(block.header.base_fee_per_gas),
        "input": _data(transaction.data),
        "nonce": _quantity(transaction.nonce),
        "value": _quantity(transaction.value),
        "type": _quantity(kind),
        "v": _quantity(signature_parity),
        "r": _quantity(transaction.r),
        "s": _quantity(transaction.s),
    }
    if kind >= 1:
        rendered["chainId"] = _quantity(transaction.chain_id)
        rendered["yParity"] = _quantity(transaction.y_parity)
        rendered["accessList"] = [
            {
                "address": _data(access.account),
                "storageKeys": [_data(slot) for slot in access.slots],
            }
            for access in transaction.access_list
        ]
    if kind >= 2:
        rendered["maxFeePerGas"] = _quantity(transaction.max_fee_per_gas)
        rendered["maxPriorityFeePerGas"] = _quantity(
            transaction.max_priority_fee_per_gas
        )
    if kind == 3:
        rendered["maxFeePerBlobGas"] = _quantity(
            transaction.max_fee_per_blob_gas
        )
        rendered["blobVersionedHashes"] = [
            _data(entry) for entry in transaction.blob_versioned_hashes
        ]
    return rendered


def render_call(result: Any, block: Any) -> Dict[str, Any]:
    """
    Render one call result.

    A failure reports `error` and no `logs`; a success reports `logs`
    and no `error`. The two are separate schema variants and a response
    carrying both satisfies neither.
    """
    rendered: Dict[str, Any] = {
        "status": _quantity(result.status),
        "returnData": (
            _data(result.return_data) if result.status == 1 else "0x"
        ),
        "gasUsed": _quantity(result.gas_used),
        "maxUsedGas": _quantity(result.max_used_gas),
        "logs": [
            render_log(log, block, result, result.first_log_index + index)
            for index, log in enumerate(result.logs)
        ],
    }
    if result.status == 0 and result.reverted:
        # A revert reports its data under `error`, not `returnData`, and
        # `returnData` is empty even though the frame did return bytes.
        # Nothing in the schema says so; it is read off the client.
        error: Dict[str, Any] = {
            "code": REVERT_ERROR_CODE,
            "message": "execution reverted",
        }
        if result.return_data:
            error["data"] = _data(result.return_data)
        rendered["error"] = error
    elif result.status == 0:
        rendered["error"] = {
            "code": VM_ERROR_CODE,
            "message": "vm execution error",
        }
    return rendered


def render_log(
    log: Any, block: Any, result: Any, index: int
) -> Dict[str, Any]:
    """Render one log, with the positional fields consensus data lacks."""
    return {
        "address": _data(log.address),
        "topics": [_data(topic) for topic in log.topics],
        "data": _data(log.data),
        "blockNumber": _quantity(block.header.number),
        "blockHash": _data(block.block_hash),
        "blockTimestamp": _quantity(block.header.timestamp),
        "transactionHash": _data(result.transaction_hash),
        "transactionIndex": _quantity(result.transaction_index),
        "logIndex": _quantity(index),
        "removed": False,
    }


__all__ = [
    "render_block",
    "render_call",
    "render_log",
    "render_result",
    "render_transaction",
    "transaction_type",
    "render_withdrawal",
]
