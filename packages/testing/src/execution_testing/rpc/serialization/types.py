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


class RPCAccessListEntry(RPCResponseModel):
    """An EIP-2930 access list entry as returned within a transaction."""

    address: Address
    storage_keys: List[Hash]


class RPCAuthorization(RPCResponseModel):
    """An EIP-7702 authorization as returned within a transaction."""

    chain_id: HexNumber
    address: Address
    nonce: HexNumber
    y_parity: HexNumber
    r: HexNumber
    s: HexNumber


class RPCTransaction(RPCResponseModel):
    """
    A transaction as returned by `eth_getTransactionByHash` and friends.

    One model covers every transaction type, with `conditional_fields`
    dropping what does not apply. The schema defines a separate variant per
    type and their requirements differ in ways that are easy to get wrong:
    legacy carries `v` while typed transactions carry `yParity`; 1559 and
    later require `gasPrice` *as well as* the fee caps, holding the
    effective price; and 4844 and 7702 cannot be creations, so `to` is
    required rather than nullable there.
    """

    conditional_fields: ClassVar[Tuple[str, ...]] = (
        "v",
        "y_parity",
        "chain_id",
        "access_list",
        "gas_price",
        "max_fee_per_gas",
        "max_priority_fee_per_gas",
        "max_fee_per_blob_gas",
        "blob_versioned_hashes",
        "authorization_list",
    )

    block_hash: Hash
    block_number: HexNumber
    block_timestamp: HexNumber
    transaction_index: HexNumber
    transaction_hash: Hash = Field(..., alias="hash")
    sender: Address = Field(..., alias="from")
    to: Address | None
    """Null for a creation; the schema forbids creations from 4844 and 7702."""
    value: HexNumber
    gas: HexNumber
    input: Bytes
    nonce: HexNumber
    ty: HexNumber = Field(..., alias="type")
    r: HexNumber
    s: HexNumber

    v: HexNumber | None = None
    """Legacy only; typed transactions report `yParity` instead."""
    y_parity: HexNumber | None = None
    """Typed transactions only."""
    chain_id: HexNumber | None = None
    """Absent from legacy transactions."""
    access_list: List[RPCAccessListEntry] | None = None
    """Absent from legacy transactions; may be empty from 2930 onwards."""
    gas_price: HexNumber | None = None
    """
    The price actually paid.

    Required from legacy through 1559 and later, where it holds the
    effective gas price rather than a field the sender set.
    """
    max_fee_per_gas: HexNumber | None = None
    """EIP-1559 and later."""
    max_priority_fee_per_gas: HexNumber | None = None
    """EIP-1559 and later."""
    max_fee_per_blob_gas: HexNumber | None = None
    """EIP-4844 only."""
    blob_versioned_hashes: List[Hash] | None = None
    """EIP-4844 only."""
    authorization_list: List[RPCAuthorization] | None = None
    """EIP-7702 only."""


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


class RPCValueChange(RPCResponseModel):
    """
    A balance or nonce an account held after one block access index.

    The schema describes balance and nonce changes as two titles with the
    same two fields, differing only in how wide the value may be — 256 bits
    against 64. Both are minimal hex, so one model serializes either, and
    the width is left to the schema to enforce rather than restated here.
    """

    index: HexNumber
    value: HexNumber


class RPCCodeChange(RPCResponseModel):
    """The code an account held after one block access index."""

    index: HexNumber
    code: Bytes


class RPCStorageChange(RPCResponseModel):
    """
    The value a storage slot held after one block access index.

    Unlike a balance or a nonce, the value is a full 32-byte word rather
    than a quantity, so it is padded rather than minimal.
    """

    index: HexNumber
    value: Hash


class RPCSlotChanges(RPCResponseModel):
    """Every change one storage slot underwent during a block."""

    key: Hash
    changes: List[RPCStorageChange]


class RPCAccountAccess(RPCResponseModel):
    """
    Everything one account did during a block, as the access list records it.

    The schema requires only `address` and forbids unknown properties, so
    the five change lists are always written even when empty. That matches
    the consensus encoding, where an account entry carries all five lists,
    and it keeps the absence of a change explicit rather than inferred from
    a missing key.
    """

    address: Address
    balance_changes: List[RPCValueChange]
    code_changes: List[RPCCodeChange]
    nonce_changes: List[RPCValueChange]
    storage_changes: List[RPCSlotChanges]
    storage_reads: List[Hash]


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
    transactions: List[Any]
    """
    Transaction hashes, or full objects when the request asked for them.

    Which form appears is chosen by the request's second parameter. The
    union is deliberately untyped: pydantic resolves `List[Hash] |
    List[Dict]` by trying `Hash` on each entry first, and `Hash` raises
    `TypeError` rather than a validation error, so the union never falls
    through to the object form. Shape is enforced by the schema instead.
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
