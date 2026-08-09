"""
Derive JSON-RPC responses from filled fixture data.

The expected value of an RPC call comes from the Python spec's own output
rather than from a recorded client response, so no client is the reference
and vectors can exist before any client implements a feature.

`types` defines the response objects the OpenRPC schema describes;
`projection` maps consensus data onto them.
"""

from .derive import derive_rpc_calls, derive_rpc_calls_for_blocks
from .filters import (
    COMPUTABLE_METHODS,
    UncomputableCallError,
    compute_result,
    filter_logs,
)
from .projection import (
    block_response,
    contract_address,
    effective_gas_price,
    receipt_responses,
    transaction_responses,
    withdrawal_responses,
)
from .schema import (
    SchemaViolationError,
    openrpc_spec,
    result_validator,
    validate_result,
)
from .types import (
    RPCAccessListEntry,
    RPCAuthorization,
    RPCBlock,
    RPCLog,
    RPCReceipt,
    RPCResponseModel,
    RPCTransaction,
    RPCWithdrawal,
)

__all__ = [
    "COMPUTABLE_METHODS",
    "UncomputableCallError",
    "RPCAccessListEntry",
    "RPCAuthorization",
    "RPCBlock",
    "RPCLog",
    "RPCReceipt",
    "RPCResponseModel",
    "RPCTransaction",
    "RPCWithdrawal",
    "SchemaViolationError",
    "block_response",
    "contract_address",
    "compute_result",
    "derive_rpc_calls",
    "derive_rpc_calls_for_blocks",
    "effective_gas_price",
    "filter_logs",
    "openrpc_spec",
    "receipt_responses",
    "result_validator",
    "transaction_responses",
    "validate_result",
    "withdrawal_responses",
]
