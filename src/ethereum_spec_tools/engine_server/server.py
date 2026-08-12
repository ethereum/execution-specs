"""
JSON-RPC server exposing the Amsterdam execution engine interface.

Serves the subset of the [Engine API] and `eth` namespace that a
consensus-layer driver — such as the hive `consume engine` simulator —
needs to feed blocks to the execution layer specification:

- `engine_newPayloadV5` validates and executes a payload through
  [`ethereum.forks.amsterdam.execution_engine`].
- `engine_forkchoiceUpdatedV4` acknowledges the chain head.
- `eth_getBlockByNumber` and friends answer basic chain queries.

The engine namespace is authenticated with a JWT bearer token as
described in the Engine API's authentication specification.

[Engine API]: https://github.com/ethereum/execution-apis/blob/main/src/engine/amsterdam.md
"""  # noqa: E501

import base64
import hashlib
import hmac
import json
import queue
import threading
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, List, Optional, Tuple

from ethereum_rlp import rlp
from ethereum_rlp.exceptions import DecodingError
from ethereum_types.bytes import Bytes, Bytes32
from ethereum_types.numeric import U64, U256, Uint
from typing_extensions import override

from ethereum.crypto.hash import Hash32, keccak256
from ethereum.exceptions import EthereumException
from ethereum.forks.amsterdam.block_access_lists import BlockAccessList
from ethereum.forks.amsterdam.blocks import Block, Withdrawal
from ethereum.forks.amsterdam.execution_engine import (
    ExecutionPayload,
    NewPayloadRequest,
    is_valid_block_hash,
    is_valid_versioned_hashes,
)
from ethereum.forks.amsterdam.execution_engine.validation_helpers import (
    _payload_block,
)
from ethereum.forks.amsterdam.fork import (
    BlockChain,
    ChainContext,
    execute_block,
    get_last_256_block_hashes,
)
from ethereum.forks.amsterdam.fork_types import Bloom, VersionedHash
from ethereum.forks.amsterdam.transactions import LegacyTransaction
from ethereum.state import Address, BlockDiff, Root
from ethereum.state_mpt import State, apply_changes_to_state, copy_state

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

CLIENT_VERSION = "eels/execution-specs/amsterdam"
"""Version string reported by `web3_clientVersion`."""


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


def _withdrawal_from_json(obj: Dict[str, Any]) -> Withdrawal:
    """Decode a withdrawal object."""
    return Withdrawal(
        index=U64(_decode_quantity(_field(obj, "index"), "index")),
        validator_index=U64(
            _decode_quantity(_field(obj, "validatorIndex"), "validatorIndex")
        ),
        address=Address(_decode_hex(_field(obj, "address"), "address", 20)),
        amount=U64(_decode_quantity(_field(obj, "amount"), "amount")),
    )


def _payload_from_json(obj: Any) -> ExecutionPayload:
    """
    Decode an `ExecutionPayloadV4` structure.

    Raise an invalid-params error for any missing or malformed field,
    per the Engine API requirement that structural failures are
    reported at the RPC layer rather than as an `INVALID` status.
    """
    if not isinstance(obj, dict):
        raise RpcError(INVALID_PARAMS, "executionPayload: expected object")
    withdrawals = _field(obj, "withdrawals")
    transactions = _field(obj, "transactions")
    if not isinstance(withdrawals, list) or not isinstance(transactions, list):
        raise RpcError(INVALID_PARAMS, "expected array")
    return ExecutionPayload(
        parent_hash=Hash32(
            _decode_hex(_field(obj, "parentHash"), "parentHash", 32)
        ),
        fee_recipient=Address(
            _decode_hex(_field(obj, "feeRecipient"), "feeRecipient", 20)
        ),
        state_root=Root(
            _decode_hex(_field(obj, "stateRoot"), "stateRoot", 32)
        ),
        receipts_root=Root(
            _decode_hex(_field(obj, "receiptsRoot"), "receiptsRoot", 32)
        ),
        logs_bloom=Bloom(
            _decode_hex(_field(obj, "logsBloom"), "logsBloom", 256)
        ),
        prev_randao=Bytes32(
            _decode_hex(_field(obj, "prevRandao"), "prevRandao", 32)
        ),
        block_number=Uint(
            _decode_quantity(_field(obj, "blockNumber"), "blockNumber")
        ),
        gas_limit=Uint(_decode_quantity(_field(obj, "gasLimit"), "gasLimit")),
        gas_used=Uint(_decode_quantity(_field(obj, "gasUsed"), "gasUsed")),
        timestamp=U256(
            _decode_quantity(_field(obj, "timestamp"), "timestamp")
        ),
        extra_data=Bytes(_decode_hex(_field(obj, "extraData"), "extraData")),
        base_fee_per_gas=Uint(
            _decode_quantity(_field(obj, "baseFeePerGas"), "baseFeePerGas")
        ),
        block_hash=Hash32(
            _decode_hex(_field(obj, "blockHash"), "blockHash", 32)
        ),
        transactions=tuple(
            Bytes(_decode_hex(tx, "transaction")) for tx in transactions
        ),
        withdrawals=tuple(_withdrawal_from_json(w) for w in withdrawals),
        blob_gas_used=U64(
            _decode_quantity(_field(obj, "blobGasUsed"), "blobGasUsed")
        ),
        excess_blob_gas=U64(
            _decode_quantity(_field(obj, "excessBlobGas"), "excessBlobGas")
        ),
        block_access_list=Bytes(
            _decode_hex(_field(obj, "blockAccessList"), "blockAccessList")
        ),
        slot_number=U64(
            _decode_quantity(_field(obj, "slotNumber"), "slotNumber")
        ),
    )


def _block_hash(block: Block) -> Hash32:
    """Compute the hash of a block's header."""
    return keccak256(rlp.encode(block.header))


def _transaction_hash(tx: Any) -> Hash32:
    """Compute the hash of a block transaction."""
    if isinstance(tx, LegacyTransaction):
        return keccak256(rlp.encode(tx))
    return keccak256(tx)


def _block_to_json(block: Block) -> Dict[str, Any]:
    """
    Encode a block in the `eth_getBlockByNumber` response format.

    Transactions are always returned as hashes.
    """
    header = block.header
    return {
        "number": _hex_int(int(header.number)),
        "hash": _hex(_block_hash(block)),
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
        "withdrawalsRoot": _hex(header.withdrawals_root),
        "blobGasUsed": _hex_int(int(header.blob_gas_used)),
        "excessBlobGas": _hex_int(int(header.excess_blob_gas)),
        "parentBeaconBlockRoot": _hex(header.parent_beacon_block_root),
        "requestsHash": _hex(header.requests_hash),
        "blockAccessListHash": _hex(header.block_access_list_hash),
        "slotNumber": _hex_int(int(header.slot_number)),
        "transactions": [
            _hex(_transaction_hash(tx)) for tx in block.transactions
        ],
        "withdrawals": [],
        "uncles": [],
    }


@dataclass
class _BlockRecord:
    """A validated block, its parent link, and the diff it produced."""

    block: Block
    parent_hash: Optional[Hash32]
    diff: Optional[BlockDiff]


class EngineBackend:
    """
    Chain state and JSON-RPC method handlers.

    Holds the [`BlockChain`] of the active branch, guarded by a lock so
    that concurrent HTTP requests observe a consistent chain. Every
    validated block is remembered in a block tree together with the
    [`BlockDiff`] it produced, so a payload building on any known block
    (or a forkchoice update selecting one) reorgs by rebuilding the
    branch state from the genesis snapshot.

    [`BlockChain`]: ref:ethereum.forks.amsterdam.fork.BlockChain
    [`BlockDiff`]: ref:ethereum.state.BlockDiff
    """

    def __init__(self, chain: BlockChain) -> None:
        self.chain = chain
        self.lock = threading.Lock()
        self.genesis_block = chain.blocks[0]
        self._genesis_state: State = copy_state(chain.state)
        # Block tree of every block ever validated; survives the active
        # branch's 255-block trim.
        self.records: Dict[Hash32, _BlockRecord] = {
            _block_hash(self.genesis_block): _BlockRecord(
                block=self.genesis_block, parent_hash=None, diff=None
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
        return _block_hash(self.chain.blocks[-1])

    def _rebuild_to(self, target: Hash32) -> None:
        """
        Make `target` the chain head by rebuilding its branch.

        Collect the ancestry of `target` in the block tree, take a fresh
        genesis state, and reapply each block's diff along the branch.
        """
        branch = []
        cursor: Optional[Hash32] = target
        while cursor is not None:
            record = self.records[cursor]
            branch.append(record)
            cursor = record.parent_hash
        branch.reverse()

        state = self._fresh_genesis_state()
        for record in branch[1:]:
            assert record.diff is not None
            apply_changes_to_state(state, record.diff)

        self.chain = BlockChain(
            blocks=[record.block for record in branch][-255:],
            state=state,
            chain_id=self.chain.chain_id,
        )

    def handle(self, method: str, params: List[Any]) -> Any:
        """Dispatch a JSON-RPC method call."""
        handlers = {
            "web3_clientVersion": self.client_version,
            "eth_chainId": self.chain_id,
            "eth_getBlockByNumber": self.get_block_by_number,
            "eth_getBlockByHash": self.get_block_by_hash,
            "engine_exchangeCapabilities": self.exchange_capabilities,
            "engine_newPayloadV5": self.new_payload_v5,
            "engine_forkchoiceUpdatedV4": self.forkchoice_updated_v4,
        }
        if method in handlers:
            return handlers[method](params)
        # Earlier versions of the supported engine methods exist, but
        # target forks preceding Amsterdam.
        if method.startswith("engine_newPayloadV") or method.startswith(
            "engine_forkchoiceUpdatedV"
        ):
            raise RpcError(UNSUPPORTED_FORK, "Unsupported fork")
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
            "engine_newPayloadV5",
            "engine_forkchoiceUpdatedV4",
        ]

    def _find_block(self, tag: Any) -> Optional[Block]:
        """Resolve a block-number tag to a block, if present."""
        with self.lock:
            if tag in ("latest", "safe", "finalized", "pending"):
                return self.chain.blocks[-1]
            if tag == "earliest":
                return self.genesis_block
            number = Uint(_decode_quantity(tag, "blockNumber"))
            if number == self.genesis_block.header.number:
                return self.genesis_block
            for block in self.chain.blocks:
                if block.header.number == number:
                    return block
        return None

    def get_block_by_number(self, params: List[Any]) -> Any:
        """`eth_getBlockByNumber`: return a block by number or tag."""
        if len(params) != 2:
            raise RpcError(INVALID_PARAMS, "expected 2 params")
        block = self._find_block(params[0])
        if block is None:
            return None
        return _block_to_json(block)

    def get_block_by_hash(self, params: List[Any]) -> Any:
        """`eth_getBlockByHash`: return a block by hash."""
        if len(params) != 2:
            raise RpcError(INVALID_PARAMS, "expected 2 params")
        block_hash = Hash32(_decode_hex(params[0], "blockHash", 32))
        with self.lock:
            record = self.records.get(block_hash)
            if record is not None:
                return _block_to_json(record.block)
        return None

    def new_payload_v5(self, params: List[Any]) -> Dict[str, Any]:
        """
        `engine_newPayloadV5`: validate and execute a payload.

        Follows the consensus-layer `verify_and_notify_new_payload`
        sequence, surfacing each failure as an `INVALID` payload status
        with a validation error message. Malformed parameters and
        execution-request violations are JSON-RPC errors instead.
        """
        if len(params) != 4:
            raise RpcError(INVALID_PARAMS, "expected 4 params")
        payload_json, hashes_json, beacon_root_json, requests_json = params

        payload = _payload_from_json(payload_json)
        try:
            rlp.decode_to(BlockAccessList, payload.block_access_list)
        except DecodingError as e:
            # A structurally undecodable block access list is an
            # invalid parameter, not an invalid block.
            raise RpcError(INVALID_PARAMS, f"blockAccessList: {e}") from e
        if not isinstance(hashes_json, list):
            raise RpcError(
                INVALID_PARAMS, "expectedBlobVersionedHashes: expected array"
            )
        versioned_hashes = tuple(
            VersionedHash(_decode_hex(h, "versionedHash", 32))
            for h in hashes_json
        )
        parent_beacon_block_root = Root(
            _decode_hex(beacon_root_json, "parentBeaconBlockRoot", 32)
        )
        if not isinstance(requests_json, list):
            raise RpcError(INVALID_PARAMS, "executionRequests: expected array")
        execution_requests = tuple(
            Bytes(_decode_hex(r, "executionRequest")) for r in requests_json
        )
        # Per the Engine API, only structural violations of the requests
        # list are parameter errors: empty items, items with no request
        # data after the type byte, and type bytes out of strictly
        # ascending order. Any other malformed content is hashed as
        # opaque bytes and surfaces as an INVALID payload.
        last_type = -1
        for item in execution_requests:
            if len(item) == 0:
                raise RpcError(
                    INVALID_PARAMS, "executionRequests: empty request item"
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

        request = NewPayloadRequest(
            execution_payload=payload,
            versioned_hashes=versioned_hashes,
            parent_beacon_block_root=parent_beacon_block_root,
            execution_requests=execution_requests,
        )

        with self.lock:
            return self._execute_payload(request)

    def _execute_payload(self, request: NewPayloadRequest) -> Dict[str, Any]:
        """Run the new-payload validation sequence for one request."""
        payload = request.execution_payload

        if b"" in payload.transactions:
            return _payload_status(
                "INVALID", None, "empty transaction in payload"
            )

        if not is_valid_block_hash(
            payload,
            request.parent_beacon_block_root,
            request.execution_requests,
        ):
            return _payload_status("INVALID", None, "invalid block hash")

        if not is_valid_versioned_hashes(request):
            return _payload_status(
                "INVALID", None, "invalid blob versioned hashes"
            )

        parent_hash = Hash32(payload.parent_hash)
        parent_known = parent_hash in self.records
        if parent_known and parent_hash != self.head_hash():
            # The payload builds on a known non-head block: reorg the
            # active branch onto its parent before executing.
            self._rebuild_to(parent_hash)

        try:
            block = _payload_block(
                payload,
                request.parent_beacon_block_root,
                request.execution_requests,
            )
            chain_context = ChainContext(
                chain_id=self.chain.chain_id,
                block_hashes=get_last_256_block_hashes(self.chain),
                parent_header=self.chain.blocks[-1].header,
            )
            diff = execute_block(block, self.chain.state, chain_context)
        except EthereumException as e:
            latest_valid: Optional[Hash32] = (
                parent_hash if parent_known else None
            )
            return _payload_status(
                "INVALID", latest_valid, f"{type(e).__name__}: {e}"
            )

        apply_changes_to_state(self.chain.state, diff)
        self.chain.blocks.append(block)
        if len(self.chain.blocks) > 255:
            self.chain.blocks = self.chain.blocks[-255:]

        block_hash = Hash32(payload.block_hash)
        self.records[block_hash] = _BlockRecord(
            block=block, parent_hash=parent_hash, diff=diff
        )
        return _payload_status("VALID", block_hash, None)

    def forkchoice_updated_v4(self, params: List[Any]) -> Dict[str, Any]:
        """
        `engine_forkchoiceUpdatedV4`: acknowledge a forkchoice state.

        Payload building is not supported, so non-null payload
        attributes are rejected. The optional third parameter (the
        EIP-8070 custody-column bitmap) is accepted and ignored.
        """
        if len(params) not in (2, 3):
            raise RpcError(INVALID_PARAMS, "expected 2 or 3 params")
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
