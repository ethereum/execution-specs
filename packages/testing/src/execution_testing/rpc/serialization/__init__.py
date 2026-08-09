"""
Derive JSON-RPC responses from filled fixture data.

The expected value of an RPC call comes from the Python spec's own output
rather than from a recorded client response, so no client is the reference
and vectors can exist before any client implements a feature.

`types` defines the response objects the OpenRPC schema describes;
`projection` maps consensus data onto them.
"""

from .derive import derive_rpc_calls, derive_rpc_calls_for_blocks
from .execution import (
    ACCESS_LIST_ROUNDS,
    CALL_GAS_LIMIT,
    EXECUTED_METHODS,
    REVERT_ERROR_CODE,
    AccessListOutcome,
    CallOutcome,
    CallReplay,
    CallSite,
    DeclaredAccessList,
    DeclaredCall,
    MessageResult,
    UnrunnableCallError,
    call_message,
    compute_declared_access_list,
    compute_declared_call,
    create_access_list,
    environment_at,
    run_call,
)
from .filters import (
    COMPUTABLE_METHODS,
    UncomputableCallError,
    compute_result,
    filter_logs,
)
from .projection import (
    block_access_list_response,
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
    partial_result_validator,
    result_validator,
    validate_partial_result,
    validate_result,
)
from .types import (
    RPCAccessListEntry,
    RPCAccountAccess,
    RPCAuthorization,
    RPCBlock,
    RPCCodeChange,
    RPCLog,
    RPCReceipt,
    RPCResponseModel,
    RPCSlotChanges,
    RPCStorageChange,
    RPCTransaction,
    RPCValueChange,
    RPCWithdrawal,
)

__all__ = [
    "ACCESS_LIST_ROUNDS",
    "CALL_GAS_LIMIT",
    "COMPUTABLE_METHODS",
    "EXECUTED_METHODS",
    "REVERT_ERROR_CODE",
    "AccessListOutcome",
    "CallOutcome",
    "CallReplay",
    "CallSite",
    "DeclaredAccessList",
    "DeclaredCall",
    "MessageResult",
    "UncomputableCallError",
    "UnrunnableCallError",
    "RPCAccessListEntry",
    "RPCAccountAccess",
    "RPCAuthorization",
    "RPCBlock",
    "RPCCodeChange",
    "RPCLog",
    "RPCReceipt",
    "RPCResponseModel",
    "RPCSlotChanges",
    "RPCStorageChange",
    "RPCTransaction",
    "RPCValueChange",
    "RPCWithdrawal",
    "SchemaViolationError",
    "block_access_list_response",
    "block_response",
    "contract_address",
    "call_message",
    "compute_declared_access_list",
    "compute_declared_call",
    "compute_result",
    "create_access_list",
    "derive_rpc_calls",
    "derive_rpc_calls_for_blocks",
    "effective_gas_price",
    "environment_at",
    "filter_logs",
    "openrpc_spec",
    "partial_result_validator",
    "receipt_responses",
    "result_validator",
    "run_call",
    "transaction_responses",
    "validate_partial_result",
    "validate_result",
    "withdrawal_responses",
]
