"""
Derive JSON-RPC responses from filled fixture data.

The expected value of an RPC call comes from the Python spec's own output
rather than from a recorded client response, so no client is the reference
and vectors can exist before any client implements a feature.

`types` defines the response objects the OpenRPC schema describes;
`projection` maps consensus data onto them.
"""

from .projection import (
    block_response,
    contract_address,
    effective_gas_price,
    receipt_responses,
)
from .types import RPCBlock, RPCLog, RPCReceipt, RPCResponseModel

__all__ = [
    "RPCBlock",
    "RPCLog",
    "RPCReceipt",
    "RPCResponseModel",
    "block_response",
    "contract_address",
    "effective_gas_price",
    "receipt_responses",
]
