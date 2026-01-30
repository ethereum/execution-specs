"""
Define t8n Payload class for parsing Engine API ExecutionPayload JSON.
"""
import json
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

from ethereum_types.bytes import Bytes, Bytes32
from ethereum_types.numeric import U64, U256, Uint

from ethereum.crypto.hash import Hash32
from ethereum.utils.hexadecimal import (
    hex_to_bytes,
    hex_to_bytes256,
    hex_to_hash,
    hex_to_u64,
    hex_to_u256,
    hex_to_uint,
)

from ..loaders.fork_loader import ForkLoad

if TYPE_CHECKING:
    from ethereum_spec_tools.evm_tools.t8n import T8N


class Payload:
    """
    Parses Engine API ExecutionPayload JSON and converts to the appropriate
    fork-specific ExecutionPayload dataclass.

    Handles field mapping from camelCase JSON to snake_case Python:
    - parentHash -> parent_hash
    - feeRecipient -> fee_recipient
    - stateRoot -> state_root
    - receiptsRoot -> receipts_root
    - logsBloom -> logs_bloom
    - prevRandao -> prev_randao
    - blockNumber -> block_number
    - gasLimit -> gas_limit
    - gasUsed -> gas_used
    - timestamp -> timestamp
    - extraData -> extra_data
    - baseFeePerGas -> base_fee_per_gas
    - blockHash -> block_hash
    - transactions -> transactions
    - withdrawals -> withdrawals (V2+)
    - blobGasUsed -> blob_gas_used (V3+)
    - excessBlobGas -> excess_blob_gas (V3+)
    """

    # V1 (Paris) base fields
    parent_hash: Hash32
    fee_recipient: Any  # Address (fork-specific type)
    state_root: Any  # Root (fork-specific type)
    receipts_root: Any  # Root (fork-specific type)
    logs_bloom: Any  # Bloom (fork-specific type)
    prev_randao: Bytes32
    block_number: Uint
    gas_limit: Uint
    gas_used: Uint
    timestamp: U256
    extra_data: Bytes
    base_fee_per_gas: Uint
    block_hash: Hash32
    transactions: Tuple[Bytes, ...]

    # V2 (Shanghai) fields
    withdrawals: Optional[Tuple[Any, ...]]

    # V3 (Cancun) fields
    blob_gas_used: Optional[U64]
    excess_blob_gas: Optional[U64]

    # V4 (Prague) fields - placeholder for execution requests
    execution_requests: Optional[List[Any]]

    def __init__(self, t8n: "T8N", stdin: Optional[Dict] = None) -> None:
        """
        Initialize Payload by parsing JSON from file or stdin.

        Parameters
        ----------
        t8n :
            The T8N instance containing options and fork information.
        stdin :
            Optional dict containing stdin data if input is from stdin.
        """
        # Load the payload JSON data
        if t8n.options.input_payload == "stdin":
            assert stdin is not None
            data = stdin.get("payload", stdin)
        else:
            with open(t8n.options.input_payload, "r") as f:
                data = json.load(f)

        self._parse_v1_fields(data, t8n)
        self._parse_v2_fields(data, t8n)
        self._parse_v3_fields(data)
        self._parse_v4_fields(data)

    def _parse_v1_fields(self, data: Dict[str, Any], t8n: "T8N") -> None:
        """Parse V1 (Paris) base fields."""
        # Hash fields
        self.parent_hash = hex_to_hash(data["parentHash"])
        self.block_hash = hex_to_hash(data["blockHash"])

        # Fork-specific address/root types
        self.fee_recipient = t8n.fork.hex_to_address(data["feeRecipient"])
        self.state_root = t8n.fork.hex_to_root(data["stateRoot"])
        self.receipts_root = t8n.fork.hex_to_root(data["receiptsRoot"])

        # Bloom (256 bytes)
        self.logs_bloom = t8n.fork.Bloom(hex_to_bytes256(data["logsBloom"]))

        # 32-byte prevRandao
        self.prev_randao = Bytes32(hex_to_bytes(data["prevRandao"]))

        # Numeric fields
        self.block_number = hex_to_uint(data["blockNumber"])
        self.gas_limit = hex_to_uint(data["gasLimit"])
        self.gas_used = hex_to_uint(data["gasUsed"])
        self.timestamp = hex_to_u256(data["timestamp"])
        self.base_fee_per_gas = hex_to_uint(data["baseFeePerGas"])

        # Extra data (variable length, max 32 bytes)
        self.extra_data = hex_to_bytes(data["extraData"])

        # Transactions: list of hex-encoded bytes strings
        self.transactions = tuple(
            hex_to_bytes(tx_hex) for tx_hex in data["transactions"]
        )

    def _parse_v2_fields(self, data: Dict[str, Any], t8n: "T8N") -> None:
        """Parse V2 (Shanghai) fields - withdrawals."""
        self.withdrawals = None
        if "withdrawals" in data:
            self.withdrawals = tuple(
                t8n.json_to_withdrawals(wd) for wd in data["withdrawals"]
            )

    def _parse_v3_fields(self, data: Dict[str, Any]) -> None:
        """Parse V3 (Cancun) fields - blob gas."""
        self.blob_gas_used = None
        self.excess_blob_gas = None
        if "blobGasUsed" in data:
            self.blob_gas_used = hex_to_u64(data["blobGasUsed"])
        if "excessBlobGas" in data:
            self.excess_blob_gas = hex_to_u64(data["excessBlobGas"])

    def _parse_v4_fields(self, data: Dict[str, Any]) -> None:
        """Parse V4 (Prague) fields - execution requests (placeholder)."""
        self.execution_requests = None
        if "executionRequests" in data:
            # Placeholder: store raw data for now
            self.execution_requests = data["executionRequests"]

    def get_version(self) -> int:
        """
        Detect payload version from present fields.

        Returns
        -------
        version :
            1 for V1 (Paris), 2 for V2 (Shanghai), 3 for V3 (Cancun),
            4 for V4 (Prague).
        """
        if self.execution_requests is not None:
            return 4
        if self.blob_gas_used is not None or self.excess_blob_gas is not None:
            return 3
        if self.withdrawals is not None:
            return 2
        return 1

    def to_execution_payload(self, fork: ForkLoad) -> Any:
        """
        Create the appropriate ExecutionPayload dataclass for the fork.

        Parameters
        ----------
        fork :
            The ForkLoad instance for accessing fork-specific classes.

        Returns
        -------
        payload :
            ExecutionPayloadV1, V2, or V3 depending on the fork and
            available fields.
        """
        # Build kwargs based on what fields this fork's payload expects
        kwargs = {
            "parent_hash": self.parent_hash,
            "fee_recipient": self.fee_recipient,
            "state_root": self.state_root,
            "receipts_root": self.receipts_root,
            "logs_bloom": self.logs_bloom,
            "prev_randao": self.prev_randao,
            "block_number": self.block_number,
            "gas_limit": self.gas_limit,
            "gas_used": self.gas_used,
            "timestamp": self.timestamp,
            "extra_data": self.extra_data,
            "base_fee_per_gas": self.base_fee_per_gas,
            "block_hash": self.block_hash,
            "transactions": self.transactions,
        }

        # Add withdrawals if fork supports them (Shanghai+)
        if fork.has_withdrawal:
            kwargs["withdrawals"] = (
                self.withdrawals if self.withdrawals is not None else ()
            )

        # Add blob gas fields if fork has beacon roots (Cancun+)
        if fork.has_beacon_roots_address:
            kwargs["blob_gas_used"] = (
                self.blob_gas_used if self.blob_gas_used is not None else U64(0)
            )
            kwargs["excess_blob_gas"] = (
                self.excess_blob_gas
                if self.excess_blob_gas is not None
                else U64(0)
            )

        # Get the ExecutionPayload class for this fork
        ExecutionPayload = fork.ExecutionPayload
        return ExecutionPayload(**kwargs)
