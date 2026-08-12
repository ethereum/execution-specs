"""
JSON-RPC server exposing the execution engine interface.

Serves the subset of the [Engine API] and `eth` namespace that a
consensus-layer driver — such as the hive `consume engine` and
`consume enginex` simulators — needs to feed blocks to the execution
layer specification, for every post-merge fork:

- `engine_newPayloadV1` … `V5` validate and execute payloads, choosing
  the fork by payload timestamp against the configured schedule.
- `engine_forkchoiceUpdatedV1` … `V4` acknowledge (and switch) the
  chain head.
- `eth_getBlockByNumber` and friends answer basic chain queries.

The Amsterdam behaviour mirrors the consensus-layer interface
specified in [`ethereum.forks.amsterdam.execution_engine`]; earlier
forks follow the same sequence with their smaller payload shapes.

The engine namespace is authenticated with a JWT bearer token as
described in the Engine API's authentication specification.

[Engine API]: https://github.com/ethereum/execution-apis/tree/main/src/engine
[`ethereum.forks.amsterdam.execution_engine`]:
    ref:ethereum.forks.amsterdam.execution_engine
"""  # noqa: E501

import base64
import hashlib
import hmac
import importlib
import json
import queue
import threading
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, List, Optional, Set, Tuple

from ethereum_rlp import rlp
from ethereum_rlp.exceptions import DecodingError
from ethereum_types.bytes import Bytes, Bytes8, Bytes32
from ethereum_types.numeric import U64, U256, Uint
from typing_extensions import override

from ethereum.crypto.hash import Hash32, keccak256
from ethereum.exceptions import EthereumException
from ethereum.merkle_patricia_trie import Trie, root, trie_set
from ethereum.state import Address, BlockDiff, Root
from ethereum.state_mpt import State, apply_changes_to_state, copy_state

from .forks import ForkSpec, Schedule, fork_at

# JSON-RPC and Engine API error codes.
PARSE_ERROR = -32700
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602
INTERNAL_ERROR = -32603
INVALID_PAYLOAD_ATTRIBUTES = -38003
UNSUPPORTED_FORK = -38005

DEFAULT_JWT_SECRET = b"secretsecretsecretsecretsecretse"
"""Default JWT secret used by hive."""

CLIENT_VERSION = "eels/execution-specs"
"""Version string reported by `web3_clientVersion`."""

EMPTY_OMMER_HASH = keccak256(rlp.encode([]))


class RpcError(Exception):
    """JSON-RPC error raised by method handlers."""

    def __init__(self, code: int, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def _hex(data: bytes) -> str:
    """Encode bytes as a `0x`-prefixed hex string."""
    return "0x" + data.hex()


def _hex_int(value: int) -> str:
    """Encode an integer as a `0x`-prefixed hex quantity."""
    return hex(int(value))


def _decode_hex(value: Any, name: str, size: Optional[int] = None) -> bytes:
    """Decode a `0x`-prefixed hex string, validating its byte length."""
    if not isinstance(value, str) or not value.startswith("0x"):
        raise RpcError(INVALID_PARAMS, f"{name}: expected hex string")
    try:
        data = bytes.fromhex(value[2:])
    except ValueError as e:
        raise RpcError(INVALID_PARAMS, f"{name}: invalid hex: {e}") from e
    if size is not None and len(data) != size:
        raise RpcError(
            INVALID_PARAMS,
            f"{name}: expected {size} bytes, got {len(data)}",
        )
    return data


def _decode_quantity(value: Any, name: str) -> int:
    """Decode a `0x`-prefixed hex quantity."""
    if not isinstance(value, str) or not value.startswith("0x"):
        raise RpcError(INVALID_PARAMS, f"{name}: expected hex quantity")
    try:
        return int(value, 16)
    except ValueError as e:
        raise RpcError(INVALID_PARAMS, f"{name}: invalid quantity") from e


def _field(obj: Dict[str, Any], name: str) -> Any:
    """Fetch a required field from a JSON object."""
    if not isinstance(obj, dict) or name not in obj:
        raise RpcError(INVALID_PARAMS, f"missing field: {name}")
    return obj[name]


@dataclass(frozen=True)
class PayloadShape:
    """Field set of one `ExecutionPayloadVX` structure."""

    withdrawals: bool
    blobs: bool
    bal: bool
    empty_bal_ok: bool = False
    """
    Accept (and ignore) an empty `blockAccessList` value: an absent
    optional bytes field marshals as `0x`, so `V3`/`V4` handlers treat
    it as not present, while any non-empty value remains an unexpected
    field.
    """


PAYLOAD_SHAPES: Dict[int, PayloadShape] = {
    1: PayloadShape(withdrawals=False, blobs=False, bal=False),
    2: PayloadShape(withdrawals=True, blobs=False, bal=False),
    3: PayloadShape(
        withdrawals=True, blobs=True, bal=False, empty_bal_ok=True
    ),
    4: PayloadShape(
        withdrawals=True, blobs=True, bal=False, empty_bal_ok=True
    ),
    5: PayloadShape(withdrawals=True, blobs=True, bal=True),
}
"""Payload field set per `engine_newPayloadVX` version."""

_BASE_PAYLOAD_KEYS = {
    "parentHash",
    "feeRecipient",
    "stateRoot",
    "receiptsRoot",
    "logsBloom",
    "prevRandao",
    "blockNumber",
    "gasLimit",
    "gasUsed",
    "timestamp",
    "extraData",
    "baseFeePerGas",
    "blockHash",
    "transactions",
}


def _payload_keys(shape: PayloadShape) -> Set[str]:
    """Return the exact JSON key set of a payload shape."""
    keys = set(_BASE_PAYLOAD_KEYS)
    if shape.withdrawals:
        keys.add("withdrawals")
    if shape.blobs:
        keys.update({"blobGasUsed", "excessBlobGas"})
    if shape.bal:
        keys.update({"blockAccessList", "slotNumber"})
    return keys


@dataclass(frozen=True)
class Payload:
    """A decoded execution payload, independent of fork dataclasses."""

    fields: Dict[str, Any]
    transactions: Tuple[Bytes, ...]
    withdrawals_json: Tuple[Dict[str, Any], ...]
    block_hash: Hash32
    parent_hash: Hash32
    timestamp: int
    block_access_list: Optional[Bytes]


def _payload_from_json(obj: Any, shape: PayloadShape) -> Payload:
    """
    Decode an `ExecutionPayloadVX` structure for the given shape.

    Raise an invalid-params error for any missing, unexpected, or
    malformed field, per the Engine API requirement that structural
    failures are reported at the RPC layer rather than as an `INVALID`
    status.
    """
    if not isinstance(obj, dict):
        raise RpcError(INVALID_PARAMS, "executionPayload: expected object")
    allowed = _payload_keys(shape)
    for key in obj:
        if key in allowed:
            continue
        if (
            key == "blockAccessList"
            and shape.empty_bal_ok
            and _decode_hex(obj[key], "blockAccessList") == b""
        ):
            continue
        raise RpcError(INVALID_PARAMS, f"unexpected field: {key}")

    transactions_json = _field(obj, "transactions")
    if not isinstance(transactions_json, list):
        raise RpcError(INVALID_PARAMS, "transactions: expected array")
    transactions = tuple(
        Bytes(_decode_hex(tx, "transaction")) for tx in transactions_json
    )

    fields: Dict[str, Any] = {
        "parent_hash": Hash32(
            _decode_hex(_field(obj, "parentHash"), "parentHash", 32)
        ),
        "coinbase": Address(
            _decode_hex(_field(obj, "feeRecipient"), "feeRecipient", 20)
        ),
        "state_root": Root(
            _decode_hex(_field(obj, "stateRoot"), "stateRoot", 32)
        ),
        "receipt_root": Root(
            _decode_hex(_field(obj, "receiptsRoot"), "receiptsRoot", 32)
        ),
        "bloom": _decode_hex(_field(obj, "logsBloom"), "logsBloom", 256),
        "prev_randao": Bytes32(
            _decode_hex(_field(obj, "prevRandao"), "prevRandao", 32)
        ),
        "number": Uint(
            _decode_quantity(_field(obj, "blockNumber"), "blockNumber")
        ),
        "gas_limit": Uint(
            _decode_quantity(_field(obj, "gasLimit"), "gasLimit")
        ),
        "gas_used": Uint(_decode_quantity(_field(obj, "gasUsed"), "gasUsed")),
        "timestamp": U256(
            _decode_quantity(_field(obj, "timestamp"), "timestamp")
        ),
        "extra_data": Bytes(
            _decode_hex(_field(obj, "extraData"), "extraData")
        ),
        "base_fee_per_gas": Uint(
            _decode_quantity(_field(obj, "baseFeePerGas"), "baseFeePerGas")
        ),
        "difficulty": Uint(0),
        "ommers_hash": EMPTY_OMMER_HASH,
        "nonce": Bytes8(b"\x00" * 8),
    }

    withdrawals_json: Tuple[Dict[str, Any], ...] = ()
    if shape.withdrawals:
        withdrawals_field = _field(obj, "withdrawals")
        if not isinstance(withdrawals_field, list):
            raise RpcError(INVALID_PARAMS, "withdrawals: expected array")
        withdrawals_json = tuple(withdrawals_field)
    if shape.blobs:
        fields["blob_gas_used"] = U64(
            _decode_quantity(_field(obj, "blobGasUsed"), "blobGasUsed")
        )
        fields["excess_blob_gas"] = U64(
            _decode_quantity(_field(obj, "excessBlobGas"), "excessBlobGas")
        )
    block_access_list: Optional[Bytes] = None
    if shape.bal:
        block_access_list = Bytes(
            _decode_hex(_field(obj, "blockAccessList"), "blockAccessList")
        )
        fields["block_access_list_hash"] = Hash32(keccak256(block_access_list))
        fields["slot_number"] = U64(
            _decode_quantity(_field(obj, "slotNumber"), "slotNumber")
        )

    return Payload(
        fields=fields,
        transactions=transactions,
        withdrawals_json=withdrawals_json,
        block_hash=Hash32(
            _decode_hex(_field(obj, "blockHash"), "blockHash", 32)
        ),
        parent_hash=Hash32(fields["parent_hash"]),
        timestamp=int(fields["timestamp"]),
        block_access_list=block_access_list,
    )


def _decode_transaction(spec: ForkSpec, encoded: Bytes) -> Any:
    """
    Decode a wire-form transaction into the fork's transaction type.

    Raw legacy transactions (RLP lists) are decoded directly; typed
    transactions go through the fork's `decode_transaction`, which on
    older forks does not accept raw legacy bytes.
    """
    if encoded and encoded[0] >= 0xC0:
        return rlp.decode_to(spec.transactions.LegacyTransaction, encoded)
    return spec.transactions.decode_transaction(encoded)


def _withdrawal(spec: ForkSpec, obj: Dict[str, Any]) -> Any:
    """Decode a withdrawal object into the fork's `Withdrawal`."""
    return spec.blocks.Withdrawal(
        index=U64(_decode_quantity(_field(obj, "index"), "index")),
        validator_index=U64(
            _decode_quantity(_field(obj, "validatorIndex"), "validatorIndex")
        ),
        address=Address(_decode_hex(_field(obj, "address"), "address", 20)),
        amount=U64(_decode_quantity(_field(obj, "amount"), "amount")),
    )


def _ordered_trie_root(items: List[Bytes]) -> Root:
    """Compute the root of an index-keyed trie over encoded items."""
    trie: "Trie[Bytes, Optional[Bytes]]" = Trie(secured=False, default=None)
    for index, item in enumerate(items):
        trie_set(trie, rlp.encode(Uint(index)), item)
    return root(trie)


def _payload_block(
    spec: ForkSpec,
    payload: Payload,
    parent_beacon_block_root: Optional[Root],
    execution_requests: Optional[Tuple[Bytes, ...]],
) -> Any:
    """
    Convert a decoded payload into the fork's `Block`.

    The header's trie roots are computed from the payload contents; the
    wire-form execution requests are hashed as opaque items.
    """
    fields = dict(payload.fields)
    fields["transactions_root"] = _ordered_trie_root(
        list(payload.transactions)
    )

    withdrawals: Tuple[Any, ...] = ()
    if spec.has_withdrawals:
        withdrawals = tuple(
            _withdrawal(spec, w) for w in payload.withdrawals_json
        )
        fields["withdrawals_root"] = _ordered_trie_root(
            [rlp.encode(w) for w in withdrawals]
        )
    if spec.has_blobs:
        assert parent_beacon_block_root is not None
        fields["parent_beacon_block_root"] = parent_beacon_block_root
    if spec.has_requests:
        assert execution_requests is not None
        requests_module = importlib.import_module(
            f"ethereum.forks.{spec.package}.requests"
        )
        # The wire-form requests are hashed as opaque items; their
        # contents play no part in the block hash.
        fields["requests_hash"] = Hash32(
            requests_module.compute_requests_hash(list(execution_requests))
        )

    header = spec.blocks.Header(**fields)

    def to_block_transaction(encoded: Bytes) -> Any:
        if not encoded or encoded[0] < 0xC0:
            return encoded
        return _decode_transaction(spec, encoded)

    block_fields: Dict[str, Any] = {
        "header": header,
        "transactions": tuple(
            to_block_transaction(tx) for tx in payload.transactions
        ),
        "ommers": (),
    }
    if spec.has_withdrawals:
        block_fields["withdrawals"] = withdrawals
    return spec.blocks.Block(**block_fields)


def _computed_versioned_hashes(
    spec: ForkSpec, payload: Payload
) -> Optional[Tuple[Hash32, ...]]:
    """
    Compute blob versioned hashes from the payload's transactions.

    Return `None` when any transaction fails to decode.
    """
    hashes: List[Hash32] = []
    blob_transaction = getattr(spec.transactions, "BlobTransaction", None)
    try:
        for encoded in payload.transactions:
            transaction = _decode_transaction(spec, encoded)
            if blob_transaction is not None and isinstance(
                transaction, blob_transaction
            ):
                hashes.extend(transaction.blob_versioned_hashes)
    except Exception:
        # Any decoding failure means versioned hashes cannot be
        # verified.
        return None
    return tuple(hashes)


def _block_hash_of(block: Any) -> Hash32:
    """Compute the hash of a block's header."""
    return keccak256(rlp.encode(block.header))


def _transaction_hash(spec: ForkSpec, tx: Any) -> Hash32:
    """Compute the hash of a block transaction."""
    if isinstance(tx, spec.transactions.LegacyTransaction):
        return keccak256(rlp.encode(tx))
    return keccak256(tx)


def _block_to_json(spec: ForkSpec, block: Any) -> Dict[str, Any]:
    """
    Encode a block in the `eth_getBlockByNumber` response format.

    Transactions are always returned as hashes.
    """
    header = block.header
    result = {
        "number": _hex_int(int(header.number)),
        "hash": _hex(_block_hash_of(block)),
        "parentHash": _hex(header.parent_hash),
        "nonce": _hex(header.nonce),
        "sha3Uncles": _hex(header.ommers_hash),
        "logsBloom": _hex(header.bloom),
        "transactionsRoot": _hex(header.transactions_root),
        "stateRoot": _hex(header.state_root),
        "receiptsRoot": _hex(header.receipt_root),
        "miner": _hex(header.coinbase),
        "difficulty": _hex_int(int(header.difficulty)),
        "extraData": _hex(header.extra_data),
        "size": _hex_int(len(rlp.encode(block))),
        "gasLimit": _hex_int(int(header.gas_limit)),
        "gasUsed": _hex_int(int(header.gas_used)),
        "timestamp": _hex_int(int(header.timestamp)),
        "mixHash": _hex(header.prev_randao),
        "baseFeePerGas": _hex_int(int(header.base_fee_per_gas)),
        "transactions": [
            _hex(_transaction_hash(spec, tx)) for tx in block.transactions
        ],
        "uncles": [],
    }
    if spec.has_withdrawals:
        result["withdrawalsRoot"] = _hex(header.withdrawals_root)
        result["withdrawals"] = []
    if spec.has_blobs:
        result["blobGasUsed"] = _hex_int(int(header.blob_gas_used))
        result["excessBlobGas"] = _hex_int(int(header.excess_blob_gas))
        result["parentBeaconBlockRoot"] = _hex(header.parent_beacon_block_root)
    if spec.has_requests:
        result["requestsHash"] = _hex(header.requests_hash)
    if spec.has_bal:
        result["blockAccessListHash"] = _hex(header.block_access_list_hash)
        result["slotNumber"] = _hex_int(int(header.slot_number))
    return result


@dataclass
class _BlockRecord:
    """A validated block, its fork, parent link, and produced diff."""

    block: Any
    parent_hash: Optional[Hash32]
    fork: ForkSpec
    diff: Optional[BlockDiff]


class EngineBackend:
    """
    Chain state and JSON-RPC method handlers.

    Holds the `BlockChain` of the active branch, guarded by a lock so
    that concurrent HTTP requests observe a consistent chain. Every
    validated block is remembered in a block tree together with its
    fork and, on forks exposing `execute_block`, the [`BlockDiff`] it
    produced; a payload building on any known block (or a forkchoice
    update selecting one) reorgs by rebuilding the branch from the
    genesis snapshot — replaying diffs where available and re-executing
    blocks otherwise.

    [`BlockDiff`]: ref:ethereum.state.BlockDiff
    """

    def __init__(
        self, chain: Any, genesis_fork: ForkSpec, schedule: Schedule
    ) -> None:
        self.chain = chain
        self.schedule = schedule
        self.genesis_fork = genesis_fork
        self.head_fork = genesis_fork
        self.lock = threading.Lock()
        self.genesis_block = chain.blocks[0]
        self._genesis_state: State = copy_state(chain.state)
        # Block tree of every block ever validated; survives the active
        # branch's 255-block trim.
        self.records: Dict[Hash32, _BlockRecord] = {
            _block_hash_of(self.genesis_block): _BlockRecord(
                block=self.genesis_block,
                parent_hash=None,
                fork=genesis_fork,
                diff=None,
            )
        }
        # Reorgs back towards genesis need a fresh copy of the genesis
        # state; keep one prepared in the background so the copy is off
        # the request path (`_genesis_state` is never mutated, so the
        # copier thread needs no lock).
        self._genesis_copies: "queue.Queue[State]" = queue.Queue(maxsize=1)
        threading.Thread(target=self._prepare_copies, daemon=True).start()

    def _prepare_copies(self) -> None:
        """Keep one spare copy of the genesis state ready."""
        while True:
            self._genesis_copies.put(copy_state(self._genesis_state))

    def _fresh_genesis_state(self) -> State:
        """Take the prepared genesis state copy, or copy synchronously."""
        try:
            return self._genesis_copies.get_nowait()
        except queue.Empty:
            return copy_state(self._genesis_state)

    def head_hash(self) -> Hash32:
        """Return the hash of the current chain head."""
        return _block_hash_of(self.chain.blocks[-1])

    def _switch_fork(self, spec: ForkSpec) -> None:
        """Rewrap the active chain into `spec`'s `BlockChain`."""
        if spec is self.head_fork:
            return
        # Post-merge forks have no irregular state transitions, so the
        # upgrade is a rewrap of the same blocks and state.
        self.chain = spec.fork.BlockChain(
            blocks=list(self.chain.blocks),
            state=self.chain.state,
            chain_id=self.chain.chain_id,
        )
        self.head_fork = spec

    def _rebuild_to(self, target: Hash32) -> None:
        """
        Make `target` the chain head by rebuilding its branch.

        Collect the ancestry of `target` in the block tree, take a
        fresh genesis state, then reapply each block along the branch:
        by diff where one was recorded, by re-execution otherwise.
        """
        branch = []
        cursor: Optional[Hash32] = target
        while cursor is not None:
            record = self.records[cursor]
            branch.append(record)
            cursor = record.parent_hash
        branch.reverse()

        self.chain = self.genesis_fork.fork.BlockChain(
            blocks=[self.genesis_block],
            state=self._fresh_genesis_state(),
            chain_id=self.chain.chain_id,
        )
        self.head_fork = self.genesis_fork
        for record in branch[1:]:
            self._switch_fork(record.fork)
            if record.diff is not None:
                apply_changes_to_state(self.chain.state, record.diff)
                self.chain.blocks.append(record.block)
                if len(self.chain.blocks) > 255:
                    self.chain.blocks = self.chain.blocks[-255:]
            else:
                record.fork.fork.state_transition(self.chain, record.block)

    def handle(self, method: str, params: List[Any]) -> Any:
        """Dispatch a JSON-RPC method call."""
        if method.startswith("engine_newPayloadV"):
            version = method.removeprefix("engine_newPayloadV")
            if version in ("1", "2", "3", "4", "5"):
                return self.new_payload(int(version), params)
            raise RpcError(UNSUPPORTED_FORK, "Unsupported fork")
        if method.startswith("engine_forkchoiceUpdatedV"):
            version = method.removeprefix("engine_forkchoiceUpdatedV")
            if version in ("1", "2", "3", "4"):
                return self.forkchoice_updated(int(version), params)
            raise RpcError(UNSUPPORTED_FORK, "Unsupported fork")
        handlers = {
            "web3_clientVersion": self.client_version,
            "eth_chainId": self.chain_id,
            "eth_getBlockByNumber": self.get_block_by_number,
            "eth_getBlockByHash": self.get_block_by_hash,
            "engine_exchangeCapabilities": self.exchange_capabilities,
        }
        if method in handlers:
            return handlers[method](params)
        raise RpcError(METHOD_NOT_FOUND, f"the method {method} does not exist")

    def client_version(self, _params: List[Any]) -> str:
        """`web3_clientVersion`: identify this client."""
        return CLIENT_VERSION

    def chain_id(self, _params: List[Any]) -> str:
        """`eth_chainId`: return the chain id of the loaded chain."""
        return _hex_int(int(self.chain.chain_id))

    def exchange_capabilities(self, _params: List[Any]) -> List[str]:
        """`engine_exchangeCapabilities`: list supported engine methods."""
        return [
            "engine_exchangeCapabilities",
            *[f"engine_newPayloadV{v}" for v in (1, 2, 3, 4, 5)],
            *[f"engine_forkchoiceUpdatedV{v}" for v in (1, 2, 3, 4)],
        ]

    def _find_block(self, tag: Any) -> Optional[_BlockRecord]:
        """Resolve a block-number tag to a block record, if present."""
        with self.lock:
            if tag in ("latest", "safe", "finalized", "pending"):
                return self.records[self.head_hash()]
            if tag == "earliest":
                return self.records[_block_hash_of(self.genesis_block)]
            number = Uint(_decode_quantity(tag, "blockNumber"))
            for block in reversed(self.chain.blocks):
                if block.header.number == number:
                    return self.records[_block_hash_of(block)]
        return None

    def get_block_by_number(self, params: List[Any]) -> Any:
        """`eth_getBlockByNumber`: return a block by number or tag."""
        if len(params) != 2:
            raise RpcError(INVALID_PARAMS, "expected 2 params")
        record = self._find_block(params[0])
        if record is None:
            return None
        return _block_to_json(record.fork, record.block)

    def get_block_by_hash(self, params: List[Any]) -> Any:
        """`eth_getBlockByHash`: return a block by hash."""
        if len(params) != 2:
            raise RpcError(INVALID_PARAMS, "expected 2 params")
        block_hash = Hash32(_decode_hex(params[0], "blockHash", 32))
        with self.lock:
            record = self.records.get(block_hash)
            if record is not None:
                return _block_to_json(record.fork, record.block)
        return None

    def new_payload(self, version: int, params: List[Any]) -> Dict[str, Any]:
        """
        `engine_newPayloadVX`: validate and execute a payload.

        Follows the consensus-layer `verify_and_notify_new_payload`
        sequence, surfacing each failure as an `INVALID` payload status
        with a validation error message. Malformed parameters and the
        structural execution-request violations are JSON-RPC errors; a
        payload whose timestamp does not belong to this method
        version's fork is an unsupported-fork error.
        """
        expected_params = 1 if version < 3 else (3 if version == 3 else 4)
        if len(params) != expected_params:
            raise RpcError(
                INVALID_PARAMS, f"expected {expected_params} params"
            )

        payload = _payload_from_json(params[0], PAYLOAD_SHAPES[version])

        versioned_hashes: Optional[Tuple[Hash32, ...]] = None
        parent_beacon_block_root: Optional[Root] = None
        execution_requests: Optional[Tuple[Bytes, ...]] = None

        if version >= 3:
            hashes_json = params[1]
            if not isinstance(hashes_json, list):
                raise RpcError(
                    INVALID_PARAMS,
                    "expectedBlobVersionedHashes: expected array",
                )
            versioned_hashes = tuple(
                Hash32(_decode_hex(h, "versionedHash", 32))
                for h in hashes_json
            )
            parent_beacon_block_root = Root(
                _decode_hex(params[2], "parentBeaconBlockRoot", 32)
            )
        if version >= 4:
            requests_json = params[3]
            if not isinstance(requests_json, list):
                raise RpcError(
                    INVALID_PARAMS, "executionRequests: expected array"
                )
            execution_requests = tuple(
                Bytes(_decode_hex(r, "executionRequest"))
                for r in requests_json
            )
            # Per the Engine API, only structural violations of the
            # requests list are parameter errors: empty items, items
            # with no request data after the type byte, and type bytes
            # out of strictly ascending order. Any other malformed
            # content is hashed as opaque bytes and surfaces as an
            # INVALID payload.
            last_type = -1
            for item in execution_requests:
                if len(item) == 0:
                    raise RpcError(
                        INVALID_PARAMS,
                        "executionRequests: empty request item",
                    )
                if len(item) == 1:
                    raise RpcError(
                        INVALID_PARAMS,
                        "executionRequests: request item without data",
                    )
                if item[0] <= last_type:
                    raise RpcError(
                        INVALID_PARAMS,
                        "executionRequests: request types not in strictly "
                        "ascending order",
                    )
                last_type = item[0]
        if version >= 5:
            assert payload.block_access_list is not None
            bal_module = importlib.import_module(
                "ethereum.forks.amsterdam.block_access_lists"
            )
            try:
                rlp.decode_to(
                    bal_module.BlockAccessList, payload.block_access_list
                )
            except DecodingError as e:
                # A structurally undecodable block access list is an
                # invalid parameter, not an invalid block.
                raise RpcError(INVALID_PARAMS, f"blockAccessList: {e}") from e

        spec = fork_at(self.schedule, payload.timestamp)
        if spec.new_payload_version != version:
            raise RpcError(UNSUPPORTED_FORK, "Unsupported fork")

        with self.lock:
            return self._execute_payload(
                spec,
                payload,
                versioned_hashes,
                parent_beacon_block_root,
                execution_requests,
            )

    def _execute_payload(
        self,
        spec: ForkSpec,
        payload: Payload,
        versioned_hashes: Optional[Tuple[Hash32, ...]],
        parent_beacon_block_root: Optional[Root],
        execution_requests: Optional[Tuple[Bytes, ...]],
    ) -> Dict[str, Any]:
        """Run the new-payload validation sequence for one payload."""
        if b"" in payload.transactions:
            return _payload_status(
                "INVALID", None, "empty transaction in payload"
            )

        # The payload must reproduce its own declared block hash.
        try:
            block = _payload_block(
                spec, payload, parent_beacon_block_root, execution_requests
            )
        except Exception as e:
            return _payload_status(
                "INVALID", None, f"payload conversion failed: {e}"
            )
        if _block_hash_of(block) != payload.block_hash:
            return _payload_status("INVALID", None, "invalid block hash")

        if spec.has_blobs:
            assert versioned_hashes is not None
            computed = _computed_versioned_hashes(spec, payload)
            if computed is None or computed != versioned_hashes:
                return _payload_status(
                    "INVALID", None, "invalid blob versioned hashes"
                )

        parent_known = payload.parent_hash in self.records
        if parent_known and payload.parent_hash != self.head_hash():
            # The payload builds on a known non-head block: reorg the
            # active branch onto its parent before executing.
            self._rebuild_to(payload.parent_hash)

        try:
            self._switch_fork(spec)
            if spec.has_bal:
                chain_context = spec.fork.ChainContext(
                    chain_id=self.chain.chain_id,
                    block_hashes=spec.fork.get_last_256_block_hashes(
                        self.chain
                    ),
                    parent_header=self.chain.blocks[-1].header,
                )
                diff: Optional[BlockDiff] = spec.fork.execute_block(
                    block, self.chain.state, chain_context
                )
                assert diff is not None
                apply_changes_to_state(self.chain.state, diff)
                self.chain.blocks.append(block)
                if len(self.chain.blocks) > 255:
                    self.chain.blocks = self.chain.blocks[-255:]
            else:
                diff = None
                spec.fork.state_transition(self.chain, block)
        except EthereumException as e:
            latest_valid: Optional[Hash32] = (
                payload.parent_hash if parent_known else None
            )
            return _payload_status(
                "INVALID", latest_valid, f"{type(e).__name__}: {e}"
            )

        self.records[payload.block_hash] = _BlockRecord(
            block=block,
            parent_hash=payload.parent_hash,
            fork=spec,
            diff=diff,
        )
        return _payload_status("VALID", payload.block_hash, None)

    def forkchoice_updated(
        self, version: int, params: List[Any]
    ) -> Dict[str, Any]:
        """
        `engine_forkchoiceUpdatedVX`: acknowledge a forkchoice state.

        Payload building is not supported, so non-null payload
        attributes are rejected. The optional third parameter of `V4`
        (the EIP-8070 custody-column bitmap) is accepted and ignored.
        """
        allowed = (2, 3) if version == 4 else (2,)
        if len(params) not in allowed:
            raise RpcError(INVALID_PARAMS, "unexpected param count")
        forkchoice_state = params[0]
        payload_attributes = params[1]

        head = Hash32(
            _decode_hex(
                _field(forkchoice_state, "headBlockHash"),
                "headBlockHash",
                32,
            )
        )

        if payload_attributes is not None:
            raise RpcError(
                INVALID_PAYLOAD_ATTRIBUTES,
                "payload building is not supported",
            )

        with self.lock:
            if head not in self.records:
                return {
                    "payloadStatus": _payload_status("SYNCING", None, None),
                    "payloadId": None,
                }
            if head != self.head_hash():
                # Selecting a known non-head block as head is a reorg.
                self._rebuild_to(head)
        return {
            "payloadStatus": _payload_status("VALID", head, None),
            "payloadId": None,
        }


def _payload_status(
    status: str, latest_valid_hash: Optional[Hash32], error: Optional[str]
) -> Dict[str, Any]:
    """Encode a `PayloadStatusV1` object."""
    return {
        "status": status,
        "latestValidHash": (
            _hex(latest_valid_hash) if latest_valid_hash is not None else None
        ),
        "validationError": error,
    }


def _b64url_decode(data: str) -> bytes:
    """Decode unpadded base64url data."""
    return base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))


def verify_jwt(token: str, secret: bytes) -> bool:
    """
    Verify an HS256 JWT signature.

    Only the signature is checked; `iat` freshness is intentionally not
    enforced.
    """
    parts = token.split(".")
    if len(parts) != 3:
        return False
    signing_input = f"{parts[0]}.{parts[1]}".encode()
    try:
        header = json.loads(_b64url_decode(parts[0]))
        signature = _b64url_decode(parts[2])
    except (ValueError, UnicodeDecodeError):
        return False
    if header.get("alg") != "HS256":
        return False
    expected = hmac.new(secret, signing_input, hashlib.sha256).digest()
    return hmac.compare_digest(signature, expected)


class _RpcHandler(BaseHTTPRequestHandler):
    """HTTP handler translating JSON-RPC requests to backend calls."""

    backend: "EngineBackend"
    jwt_secret: Optional[bytes] = None

    @override
    def log_message(self, format: str, *args: Any) -> None:
        """Suppress default request logging."""

    def _respond(self, status: int, body: Dict[str, Any] | List[Any]) -> None:
        data = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _authorized(self) -> bool:
        if self.jwt_secret is None:
            return True
        authorization = self.headers.get("Authorization", "")
        if not authorization.startswith("Bearer "):
            return False
        return verify_jwt(
            authorization.removeprefix("Bearer "), self.jwt_secret
        )

    def _handle_single(self, request: Any) -> Dict[str, Any]:
        request_id = request.get("id") if isinstance(request, dict) else None
        response: Dict[str, Any] = {"jsonrpc": "2.0", "id": request_id}
        if not isinstance(request, dict) or "method" not in request:
            response["error"] = {
                "code": INVALID_REQUEST,
                "message": "invalid request",
            }
            return response
        try:
            response["result"] = self.backend.handle(
                request["method"], request.get("params", [])
            )
        except RpcError as e:
            response["error"] = {"code": e.code, "message": e.message}
        except Exception as e:  # noqa: BLE001
            response["error"] = {
                "code": INTERNAL_ERROR,
                "message": f"{type(e).__name__}: {e}",
            }
        return response

    def do_POST(self) -> None:  # noqa: N802
        """Serve one JSON-RPC request or batch."""
        if not self._authorized():
            self._respond(
                401,
                {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {
                        "code": INVALID_REQUEST,
                        "message": "missing or invalid JWT",
                    },
                },
            )
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            request = json.loads(self.rfile.read(length))
        except (ValueError, json.JSONDecodeError):
            self._respond(
                200,
                {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {
                        "code": PARSE_ERROR,
                        "message": "parse error",
                    },
                },
            )
            return
        if isinstance(request, list):
            self._respond(200, [self._handle_single(item) for item in request])
        else:
            self._respond(200, self._handle_single(request))


def serve(
    backend: EngineBackend,
    address: str,
    rpc_port: int,
    engine_port: int,
    jwt_secret: bytes,
) -> Tuple[ThreadingHTTPServer, ThreadingHTTPServer]:
    """
    Start the `eth` and authenticated `engine` HTTP listeners.

    Both listeners dispatch to the same backend; only the engine
    listener requires JWT authentication. Returns the two servers with
    their serving threads already running.
    """

    class EthHandler(_RpcHandler):
        pass

    class EngineHandler(_RpcHandler):
        pass

    EthHandler.backend = backend
    EthHandler.jwt_secret = None
    EngineHandler.backend = backend
    EngineHandler.jwt_secret = jwt_secret

    rpc_server = ThreadingHTTPServer((address, rpc_port), EthHandler)
    engine_server = ThreadingHTTPServer((address, engine_port), EngineHandler)

    for http_server in (rpc_server, engine_server):
        thread = threading.Thread(
            target=http_server.serve_forever, daemon=True
        )
        thread.start()

    return rpc_server, engine_server
