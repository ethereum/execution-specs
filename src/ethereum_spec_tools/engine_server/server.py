"""
JSON-RPC transport for the execution engine specification.

Serves the [Engine API] and the `eth` namespace queries that a
consensus-layer driver — such as the hive `consume engine` and
`consume enginex` simulators — needs, for every post-merge fork. The
server is transport only: it decodes JSON into each fork's versioned
engine structures, routes calls to the fork's `execution_engine`
module by payload timestamp, and maps the spec's exceptions onto the
Engine API error codes. All semantics live in
`ethereum.forks.<fork>.execution_engine`.

The engine namespace is authenticated with a JWT bearer token as
described in the Engine API's authentication specification.

[Engine API]: https://github.com/ethereum/execution-apis/tree/main/src/engine
"""  # noqa: E501

import base64
import hashlib
import hmac
import json
import threading
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, List, Optional, Set, Tuple

from ethereum_rlp import rlp
from ethereum_types.bytes import Bytes, Bytes32
from ethereum_types.numeric import U64, U256, Uint
from typing_extensions import override

from ethereum.crypto.hash import Hash32, keccak256
from ethereum.exceptions import (
    InvalidEngineParamsError,
    UnsupportedForkError,
)
from ethereum.state import Address, Root

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

PAYLOAD_VERSION = {1: 1, 2: 2, 3: 3, 4: 3, 5: 4}
"""Payload structure version carried by each `engine_newPayloadVX`."""


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
    """JSON field set of one `ExecutionPayloadVX` structure."""

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
"""JSON field set per `engine_newPayloadVX` version."""

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


def _check_payload_keys(obj: Dict[str, Any], shape: PayloadShape) -> None:
    """Reject JSON fields outside the version's payload structure."""
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


def _typed_payload(spec: ForkSpec, version: int, obj: Dict[str, Any]) -> Any:
    """Decode a payload object into the fork's `ExecutionPayloadVX`."""
    if not isinstance(obj, dict):
        raise RpcError(INVALID_PARAMS, "executionPayload: expected object")
    _check_payload_keys(obj, PAYLOAD_SHAPES[version])
    payload_version = PAYLOAD_VERSION[version]

    transactions_json = _field(obj, "transactions")
    if not isinstance(transactions_json, list):
        raise RpcError(INVALID_PARAMS, "transactions: expected array")

    kwargs: Dict[str, Any] = {
        "parent_hash": Hash32(
            _decode_hex(_field(obj, "parentHash"), "parentHash", 32)
        ),
        "fee_recipient": Address(
            _decode_hex(_field(obj, "feeRecipient"), "feeRecipient", 20)
        ),
        "state_root": Root(
            _decode_hex(_field(obj, "stateRoot"), "stateRoot", 32)
        ),
        "receipts_root": Root(
            _decode_hex(_field(obj, "receiptsRoot"), "receiptsRoot", 32)
        ),
        "logs_bloom": _decode_hex(_field(obj, "logsBloom"), "logsBloom", 256),
        "prev_randao": Bytes32(
            _decode_hex(_field(obj, "prevRandao"), "prevRandao", 32)
        ),
        "block_number": Uint(
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
        "block_hash": Hash32(
            _decode_hex(_field(obj, "blockHash"), "blockHash", 32)
        ),
        "transactions": tuple(
            Bytes(_decode_hex(tx, "transaction")) for tx in transactions_json
        ),
    }
    if payload_version >= 2:
        withdrawals_json = _field(obj, "withdrawals")
        if not isinstance(withdrawals_json, list):
            raise RpcError(INVALID_PARAMS, "withdrawals: expected array")
        kwargs["withdrawals"] = tuple(
            spec.blocks.Withdrawal(
                index=U64(_decode_quantity(_field(w, "index"), "index")),
                validator_index=U64(
                    _decode_quantity(
                        _field(w, "validatorIndex"), "validatorIndex"
                    )
                ),
                address=Address(
                    _decode_hex(_field(w, "address"), "address", 20)
                ),
                amount=U64(_decode_quantity(_field(w, "amount"), "amount")),
            )
            for w in withdrawals_json
        )
    if payload_version >= 3:
        kwargs["blob_gas_used"] = U64(
            _decode_quantity(_field(obj, "blobGasUsed"), "blobGasUsed")
        )
        kwargs["excess_blob_gas"] = U64(
            _decode_quantity(_field(obj, "excessBlobGas"), "excessBlobGas")
        )
    if payload_version >= 4:
        kwargs["block_access_list"] = Bytes(
            _decode_hex(_field(obj, "blockAccessList"), "blockAccessList")
        )
        kwargs["slot_number"] = U64(
            _decode_quantity(_field(obj, "slotNumber"), "slotNumber")
        )
    payload_type = getattr(
        spec.engine, f"ExecutionPayloadV{payload_version}", None
    )
    if payload_type is None:
        raise RpcError(UNSUPPORTED_FORK, "Unsupported fork")
    return payload_type(**kwargs)


def _status_to_json(status: Any) -> Dict[str, Any]:
    """Serialize a `PayloadStatusV1` object."""
    return {
        "status": status.status.value,
        "latestValidHash": (
            _hex(status.latest_valid_hash)
            if status.latest_valid_hash is not None
            else None
        ),
        "validationError": status.validation_error,
    }


def _block_hash_of(block: Any) -> Hash32:
    """Compute the hash of a block's header."""
    return keccak256(rlp.encode(block.header))


def _block_to_json(block: Any) -> Dict[str, Any]:
    """
    Encode a block in the `eth_getBlockByNumber` response format.

    Transactions are always returned as hashes; optional fields follow
    the block's own header shape.
    """
    header = block.header

    def tx_hash(tx: Any) -> str:
        if isinstance(tx, (bytes, Bytes)):
            return _hex(keccak256(tx))
        return _hex(keccak256(rlp.encode(tx)))

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
        "transactions": [tx_hash(tx) for tx in block.transactions],
        "uncles": [],
    }
    quantities = {"blob_gas_used", "excess_blob_gas", "slot_number"}
    optional = {
        "withdrawals_root": "withdrawalsRoot",
        "blob_gas_used": "blobGasUsed",
        "excess_blob_gas": "excessBlobGas",
        "parent_beacon_block_root": "parentBeaconBlockRoot",
        "requests_hash": "requestsHash",
        "block_access_list_hash": "blockAccessListHash",
        "slot_number": "slotNumber",
    }
    for attr, key in optional.items():
        if hasattr(header, attr):
            value = getattr(header, attr)
            result[key] = (
                _hex_int(int(value)) if attr in quantities else _hex(value)
            )
    if hasattr(block, "withdrawals"):
        result["withdrawals"] = []
    return result


class EngineBackend:
    """
    Transport-side holder of the spec `ExecutionEngine` object.

    Requests are decoded into the fork's versioned structures, routed
    to the fork's engine module by payload timestamp, and answered from
    the module's `PayloadStatusV1` results; a lock serializes access.
    """

    def __init__(
        self, engine: Any, genesis_spec: ForkSpec, schedule: Schedule
    ) -> None:
        self.engine = engine
        self.genesis_spec = genesis_spec
        self.schedule = schedule
        self.lock = threading.Lock()

    def _spec_of_block(self, block: Any) -> ForkSpec:
        return fork_at(self.schedule, int(block.header.timestamp))

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
        return _hex_int(int(self.engine.chain.chain_id))

    def exchange_capabilities(self, _params: List[Any]) -> List[str]:
        """`engine_exchangeCapabilities`: list supported engine methods."""
        return [
            "engine_exchangeCapabilities",
            *[f"engine_newPayloadV{v}" for v in (1, 2, 3, 4, 5)],
            *[f"engine_forkchoiceUpdatedV{v}" for v in (1, 2, 3, 4)],
        ]

    def _find_block(self, tag: Any) -> Optional[Any]:
        """Resolve a block-number tag to a block, if present."""
        with self.lock:
            chain = self.engine.chain
            if tag in ("latest", "safe", "finalized", "pending"):
                return chain.blocks[-1]
            if tag == "earliest":
                return self.engine.genesis_block
            number = Uint(_decode_quantity(tag, "blockNumber"))
            if number == self.engine.genesis_block.header.number:
                return self.engine.genesis_block
            for block in reversed(chain.blocks):
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
            block = self.engine.validated_blocks.get(block_hash)
            if block is not None:
                return _block_to_json(block)
        return None

    def new_payload(self, version: int, params: List[Any]) -> Dict[str, Any]:
        """
        `engine_newPayloadVX`: decode, route, and delegate.

        The payload's fork is chosen by timestamp; the fork module's
        `new_payload_vX` carries the version rules and returns the
        payload status. Spec exceptions map onto the Engine API error
        codes.
        """
        expected_params = 1 if version < 3 else (3 if version == 3 else 4)
        if len(params) != expected_params:
            raise RpcError(
                INVALID_PARAMS, f"expected {expected_params} params"
            )

        payload_json = params[0]
        if not isinstance(payload_json, dict):
            raise RpcError(INVALID_PARAMS, "executionPayload: expected object")
        timestamp = _decode_quantity(
            _field(payload_json, "timestamp"), "timestamp"
        )
        spec = fork_at(self.schedule, timestamp)
        method = getattr(spec.engine, f"new_payload_v{version}", None)
        if method is None:
            raise RpcError(UNSUPPORTED_FORK, "Unsupported fork")

        args: List[Any] = [_typed_payload(spec, version, payload_json)]
        if version >= 3:
            hashes_json = params[1]
            if not isinstance(hashes_json, list):
                raise RpcError(
                    INVALID_PARAMS,
                    "expectedBlobVersionedHashes: expected array",
                )
            args.append(
                tuple(
                    Hash32(_decode_hex(h, "versionedHash", 32))
                    for h in hashes_json
                )
            )
            args.append(
                Root(_decode_hex(params[2], "parentBeaconBlockRoot", 32))
            )
        if version >= 4:
            requests_json = params[3]
            if not isinstance(requests_json, list):
                raise RpcError(
                    INVALID_PARAMS, "executionRequests: expected array"
                )
            args.append(
                tuple(
                    Bytes(_decode_hex(r, "executionRequest"))
                    for r in requests_json
                )
            )

        with self.lock:
            try:
                status = method(self.engine, *args)
            except UnsupportedForkError as e:
                raise RpcError(UNSUPPORTED_FORK, str(e)) from e
            except InvalidEngineParamsError as e:
                raise RpcError(INVALID_PARAMS, str(e)) from e
        return _status_to_json(status)

    def forkchoice_updated(
        self, version: int, params: List[Any]
    ) -> Dict[str, Any]:
        """
        `engine_forkchoiceUpdatedVX`: decode, route, and delegate.

        The call is routed to the module of the adopted head's fork;
        payload building is not supported, so non-null payload
        attributes are rejected.
        """
        allowed = (2, 3) if version == 4 else (2,)
        if len(params) not in allowed:
            raise RpcError(INVALID_PARAMS, "unexpected param count")
        forkchoice_json = params[0]
        payload_attributes = params[1]

        if payload_attributes is not None:
            raise RpcError(
                INVALID_PAYLOAD_ATTRIBUTES,
                "payload building is not supported",
            )

        head = Hash32(
            _decode_hex(
                _field(forkchoice_json, "headBlockHash"), "headBlockHash", 32
            )
        )

        with self.lock:
            block = self.engine.validated_blocks.get(head)
            spec = (
                self._spec_of_block(block)
                if block is not None
                else self.genesis_spec
            )
            module = spec.engine
            call_version = version
            while not hasattr(module, f"forkchoice_updated_v{call_version}"):
                call_version -= 1
            state = module.ForkchoiceStateV1(
                head_block_hash=head,
                safe_block_hash=Hash32(
                    _decode_hex(
                        _field(forkchoice_json, "safeBlockHash"),
                        "safeBlockHash",
                        32,
                    )
                ),
                finalized_block_hash=Hash32(
                    _decode_hex(
                        _field(forkchoice_json, "finalizedBlockHash"),
                        "finalizedBlockHash",
                        32,
                    )
                ),
            )
            args: List[Any] = [self.engine, state, None]
            if call_version == 4:
                args.append(None)
            response = getattr(module, f"forkchoice_updated_v{call_version}")(
                *args
            )

        return {
            "payloadStatus": _status_to_json(response.payload_status),
            "payloadId": None,
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

    # Keep-alive avoids a fresh TCP connection per request; responses
    # always carry Content-Length, which HTTP/1.1 persistence requires.
    protocol_version = "HTTP/1.1"

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
