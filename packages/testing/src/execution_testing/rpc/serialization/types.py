"""
JSON-RPC response types, as defined by the vendored OpenRPC schema.

These differ from the consensus types in `fixtures.common` in three ways
that matter for conformance:

1. Quantities use minimal hex. The schema's `uint` pattern is
   `^0x(0|[1-9a-f][0-9a-f]*)$`, so the zero-padded form the fixtures use
   (`0x01`) is invalid here. `HexNumber` produces the correct form;
   `ZeroPaddedHexNumber` does not.
2. Several fields exist only in the RPC view. `blockHash`, `logIndex` and
   `effectiveGasPrice` are absent from consensus data and must be derived;
   see `projection.py`.
3. Absent and null are distinct. Some fields are omitted entirely when
   inapplicable (`status` before Byzantium, `blobGasUsed` for non-blob
   transactions), while others are always present and merely null (`to`
   and `contractAddress` on a receipt). `to_rpc` implements that split,
   which `model_dump(exclude_none=True)` cannot express on its own.
"""

from typing import Any, ClassVar, Dict, List, Tuple

from pydantic import Field

from execution_testing.base_types import (
    Address,
    Bloom,
    Bytes,
    CamelModel,
    Hash,
    HexNumber,
)


class RPCResponseModel(CamelModel):
    """Base for RPC response objects, handling the absent/null split."""

    conditional_fields: ClassVar[Tuple[str, ...]] = ()
    """
    Fields omitted from the response entirely when their value is `None`.

    Every other `None` is serialized as an explicit null, because the schema
    describes those fields as present-but-null rather than optional.
    """

    def to_rpc(self) -> Dict[str, Any]:
        """
        Return the response as a JSON-RPC result object.

        Serialization uses JSON mode so quantities become minimal-hex
        strings rather than Python integers, as the schema requires.
        """
        dumped = self.model_dump(by_alias=True, mode="json")
        for field_name in self.conditional_fields:
            alias = self.__class__.model_fields[field_name].alias
            assert alias is not None, f"{field_name} has no alias"
            if dumped.get(alias) is None:
                dumped.pop(alias, None)
        return dumped


class RPCLog(RPCResponseModel):
    """A log entry as returned by `eth_getTransactionReceipt`."""

    address: Address
    topics: List[Hash]
    data: Bytes

    block_hash: Hash
    block_number: HexNumber
    block_timestamp: HexNumber
    transaction_hash: Hash
    transaction_index: HexNumber
    log_index: HexNumber
    removed: bool = False
    """Always false here; only a reorged log is removed."""


class RPCWithdrawal(RPCResponseModel):
    """A withdrawal as returned within a block object."""

    index: HexNumber
    validator_index: HexNumber
    address: Address
    amount: HexNumber


class RPCReceipt(RPCResponseModel):
    """A transaction receipt as returned by `eth_getTransactionReceipt`."""

    conditional_fields: ClassVar[Tuple[str, ...]] = (
        "status",
        "root",
        "blob_gas_used",
        "blob_gas_price",
    )

    transaction_hash: Hash
    transaction_index: HexNumber
    block_hash: Hash
    block_number: HexNumber
    sender: Address = Field(..., alias="from")
    to: Address | None
    """Null for a contract creation."""
    cumulative_gas_used: HexNumber
    gas_used: HexNumber
    contract_address: Address | None
    """Null unless the transaction created a contract."""
    logs: List[RPCLog]
    logs_bloom: Bloom
    ty: HexNumber = Field(..., alias="type")
    effective_gas_price: HexNumber

    status: HexNumber | None = None
    """Absent before Byzantium, where `root` is returned instead."""
    root: Hash | None = None
    """Absent from Byzantium onwards, where `status` is returned instead."""
    blob_gas_used: HexNumber | None = None
    """Absent for non-blob transactions."""
    blob_gas_price: HexNumber | None = None
    """Absent for non-blob transactions."""


class RPCBlock(RPCResponseModel):
    """A block as returned by `eth_getBlockByNumber`/`eth_getBlockByHash`."""

    conditional_fields: ClassVar[Tuple[str, ...]] = (
        "base_fee_per_gas",
        "withdrawals_root",
        "blob_gas_used",
        "excess_blob_gas",
        "parent_beacon_block_root",
        "requests_hash",
        "withdrawals",
    )

    block_hash: Hash = Field(..., alias="hash")
    parent_hash: Hash
    ommers_hash: Hash = Field(..., alias="sha3Uncles")
    fee_recipient: Address = Field(..., alias="miner")
    state_root: Hash
    transactions_root: Hash
    receipts_root: Hash
    logs_bloom: Bloom
    difficulty: HexNumber
    number: HexNumber
    gas_limit: HexNumber
    gas_used: HexNumber
    timestamp: HexNumber
    extra_data: Bytes
    prev_randao: Hash = Field(..., alias="mixHash")
    nonce: Bytes
    size: HexNumber
    """Length of the RLP-encoded block, which the header does not carry."""
    transactions: List[Hash]
    """
    Transaction hashes.

    The full-object form, returned when the request sets `fullTransactions`,
    is not implemented yet.
    """
    uncles: List[Hash] = Field(default_factory=list)

    base_fee_per_gas: HexNumber | None = None
    """Absent before London."""
    withdrawals_root: Hash | None = None
    """Absent before Shanghai."""
    blob_gas_used: HexNumber | None = None
    """Absent before Cancun."""
    excess_blob_gas: HexNumber | None = None
    """Absent before Cancun."""
    parent_beacon_block_root: Hash | None = None
    """Absent before Cancun."""
    requests_hash: Hash | None = None
    """Absent before Prague."""
    withdrawals: List[RPCWithdrawal] | None = None
    """
    Absent before Shanghai.

    An empty list is meaningful and is not omitted: from Shanghai onwards
    a block always reports its withdrawals, even when there are none.
    """
