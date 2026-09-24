"""Test REST witness requests, discovery, errors and sender verification."""

import json
from unittest.mock import Mock

import pytest
import requests
from coincurve import PrivateKey

from execution_testing.base_types import Address, Bloom, Bytes, Hash
from execution_testing.fixtures.blockchain import FixtureExecutionPayload
from execution_testing.forks import Amsterdam
from execution_testing.rpc import (
    EngineSSZRPC,
    EngineWitnessEndpointNotImplementedError,
)
from execution_testing.rpc.engine_ssz import (
    encode_witness_request,
    validate_public_keys,
)
from execution_testing.rpc.rpc_types import JSONRPCError
from execution_testing.test_types import Transaction


@pytest.fixture
def payload() -> FixtureExecutionPayload:
    """Return an empty Amsterdam payload with distinctive fixed fields."""
    return FixtureExecutionPayload(
        parent_hash=Hash(1),
        fee_recipient=Address(2),
        state_root=Hash(3),
        receipts_root=Hash(4),
        logs_bloom=Bloom(0),
        prev_randao=Hash(5),
        number=1,
        gas_limit=30_000_000,
        gas_used=0,
        timestamp=12,
        extra_data=Bytes(b"test"),
        base_fee_per_gas=7,
        block_hash=Hash(8),
        transactions=[],
        withdrawals=[],
        blob_gas_used=0,
        excess_blob_gas=0,
        block_access_list=Bytes(b"\xc0"),
        slot_number=1,
    )


def response(status: int, body: bytes, content_type: str) -> requests.Response:
    """Build an HTTP response without a network dependency."""
    result = requests.Response()
    result.status_code = status
    result._content = body
    result.headers["Content-Type"] = content_type
    return result


def test_envelope_offsets_and_fields(payload: FixtureExecutionPayload) -> None:
    """Use the normative envelope order and omit legacy blob hashes."""
    encoded = encode_witness_request(
        payload, Hash(9), [Bytes(b"\x00\x11")], Amsterdam
    )
    assert encoded[:4] == bytes.fromhex("28000000")
    assert encoded[4:36] == bytes(Hash(9))
    end = int.from_bytes(encoded[36:40], "little")
    assert (
        FixtureExecutionPayload.ssz_decode(encoded[40:end], Amsterdam)
        == payload
    )
    assert encoded[end:] == bytes.fromhex("040000000011")


def test_rest_bal_exceeds_fixture_limit(
    payload: FixtureExecutionPayload,
) -> None:
    """Send a wire-encodable BAL above the fixture's independent limit."""
    bal = Bytes(b"\x01" * (2**23 + 1))
    payload = payload.model_copy(update={"block_access_list": bal})
    encoded = encode_witness_request(payload, Hash(9), [], Amsterdam)
    # BAL is the payload's last variable field; requests are empty.
    assert encoded.endswith(bal)
    assert int.from_bytes(encoded[36:40], "little") == len(encoded)
    # REST must not change the SSZ schema used to serialize fixtures.
    with pytest.raises(Exception, match="cannot be more than limit"):
        payload.ssz_encode(Amsterdam)


def test_rest_request_and_repeated_submission(
    payload: FixtureExecutionPayload,
) -> None:
    """Send binary requests with fork/JWT headers, including known payloads."""
    rpc = EngineSSZRPC("http://client:8551")
    # SYNCING response: 3 outer offsets followed by a 9-byte PayloadStatus.
    raw = bytes.fromhex("0c0000001500000015000000020900000009000000")
    rpc.session = Mock()
    rpc.session.post.return_value = response(
        200, raw, "application/octet-stream"
    )
    for _ in range(2):
        rpc.new_payload_with_witness(payload, [Hash(99)], Hash(9), [])
    assert rpc.session.post.call_count == 2
    args, kwargs = rpc.session.post.call_args
    assert args == ("http://client:8551/engine/v1/payloads/witness",)
    assert kwargs["data"] == encode_witness_request(
        payload, Hash(9), [], Amsterdam
    )
    assert "json" not in kwargs
    assert kwargs["headers"]["Eth-Execution-Version"] == "amsterdam"
    assert kwargs["headers"]["Content-Type"] == "application/octet-stream"
    assert kwargs["headers"]["Accept"] == "application/octet-stream"
    assert kwargs["headers"]["Authorization"].startswith("Bearer ")


@pytest.mark.parametrize("advertised", [True, False])
def test_capability_discovery(advertised: bool) -> None:
    """Only test clients advertising both Amsterdam and witness support."""
    rpc = EngineSSZRPC("http://client:8551")
    rpc.session = Mock()
    body = {
        "supported_forks": ["amsterdam"],
        "fork_scoped_endpoints": ["payloads/witness"] if advertised else [],
    }
    rpc.session.get.return_value = response(
        200, json.dumps(body).encode(), "application/json"
    )
    if advertised:
        rpc.check_witness_capability(Amsterdam)
    else:
        with pytest.raises(EngineWitnessEndpointNotImplementedError):
            rpc.check_witness_capability(Amsterdam)
    assert rpc.session.get.call_args.args[0].endswith(
        "/engine/v1/capabilities"
    )


@pytest.mark.parametrize(
    "error,status,code",
    [
        ("parse-error", 400, -32700),
        ("invalid-request", 400, -32600),
        ("invalid-body", 422, -32602),
        ("unsupported-fork", 400, -38005),
        ("method-not-found", 404, -32601),
        ("unknown-payload", 404, -38001),
        ("invalid-forkchoice", 409, -38002),
        ("reorg-too-deep", 409, -38006),
        ("request-too-large", 413, -38004),
        ("invalid-attributes", 422, -38003),
        ("internal", 500, -32603),
    ],
)
@pytest.mark.parametrize("correct_status", [True, False])
def test_problem_error_mapping(
    payload: FixtureExecutionPayload,
    error: str,
    status: int,
    code: int,
    correct_status: bool,
) -> None:
    """Map specified REST error equivalents for negative Engine fixtures."""
    rpc = EngineSSZRPC("http://client:8551")
    rpc.session = Mock()
    body = json.dumps(
        {"type": f"/engine-api/errors/{error}", "detail": "failure"}
    ).encode()
    rpc.session.post.return_value = response(
        status if correct_status else (500 if status != 500 else 400),
        body,
        "application/problem+json",
    )
    if not correct_status:
        with pytest.raises(ValueError, match="Unexpected HTTP status"):
            rpc.new_payload_with_witness(payload, [], Hash(0), [])
        return
    with pytest.raises(JSONRPCError) as exc:
        rpc.new_payload_with_witness(payload, [], Hash(0), [])
    assert exc.value.code == code


@pytest.mark.parametrize("status", [201, 202, 204, 301, 302, 307])
def test_witness_requires_http_200(
    payload: FixtureExecutionPayload, status: int
) -> None:
    """Reject other success codes and redirects despite a valid SSZ body."""
    rpc = EngineSSZRPC("http://client:8551")
    rpc.session = Mock()
    raw = bytes.fromhex("0c0000001500000015000000020900000009000000")
    rpc.session.post.return_value = response(
        status, raw, "application/octet-stream"
    )
    with pytest.raises(ValueError, match="Unexpected HTTP status"):
        rpc.new_payload_with_witness(payload, [], Hash(0), [])


def test_raw_witness_request() -> None:
    """Send malformed bytes unchanged for endpoint conformance tests."""
    rpc = EngineSSZRPC("http://client:8551")
    rpc.session = Mock()
    reply = response(
        400,
        b'{"type":"/engine-api/errors/ssz-decode-error"}',
        "application/problem+json",
    )
    rpc.session.post.return_value = reply
    assert rpc.post_witness_request(b"\x28", fork=Amsterdam) is reply
    args, kwargs = rpc.session.post.call_args
    assert args == ("http://client:8551/engine/v1/payloads/witness",)
    assert kwargs["data"] == b"\x28"
    assert kwargs["allow_redirects"] is False
    assert kwargs["headers"]["Eth-Execution-Version"] == "amsterdam"
    assert kwargs["headers"]["Content-Type"] == "application/octet-stream"
    assert kwargs["headers"]["Authorization"].startswith("Bearer ")


@pytest.mark.parametrize(
    "error,status",
    [("ssz-decode-error", 400), ("unsupported-media-type", 415)],
)
@pytest.mark.parametrize("correct_status", [True, False])
def test_new_rest_error_remains_http_failure(
    payload: FixtureExecutionPayload,
    error: str,
    status: int,
    correct_status: bool,
) -> None:
    """Check REST-only errors without inventing legacy error codes."""
    rpc = EngineSSZRPC("http://client:8551")
    rpc.session = Mock()
    rpc.session.post.return_value = response(
        status if correct_status else 500,
        json.dumps({"type": f"/engine-api/errors/{error}"}).encode(),
        "application/problem+json",
    )
    if not correct_status:
        with pytest.raises(ValueError, match="Unexpected HTTP status"):
            rpc.new_payload_with_witness(payload, [], Hash(0), [])
        return
    with pytest.raises(requests.HTTPError):
        rpc.new_payload_with_witness(payload, [], Hash(0), [])


@pytest.mark.parametrize("tx_type", [0, 1, 2, 3, 4])
def test_public_key_matches_signature(tx_type: int) -> None:
    """Check signature recovery across every supported transaction type."""
    tx = Transaction(
        ty=tx_type,
        secret_key=Hash(1),
        to=Address(2),
        gas_limit=100_000,
        blob_versioned_hashes=[] if tx_type == 3 else None,
    ).with_signature_and_sender()
    key = Bytes(PrivateKey(bytes(Hash(1))).public_key.format(compressed=False))
    validate_public_keys([tx.rlp(), tx.rlp()], [key, key])
    with pytest.raises(ValueError, match="one public key"):
        validate_public_keys([tx.rlp()], [])
    wrong = Bytes(
        PrivateKey(bytes(Hash(2))).public_key.format(compressed=False)
    )
    with pytest.raises(ValueError, match="transaction 0"):
        validate_public_keys([tx.rlp()], [wrong])


def test_public_key_order_and_recovery_parity() -> None:
    """Reject reordered keys and another valid signature recovery candidate."""
    transactions = [
        Transaction(
            secret_key=Hash(i), to=Address(3), gas_limit=21_000
        ).with_signature_and_sender()
        for i in (1, 2)
    ]
    keys = [
        Bytes(PrivateKey(bytes(Hash(i))).public_key.format(compressed=False))
        for i in (1, 2)
    ]
    validate_public_keys([tx.rlp() for tx in transactions], keys)
    with pytest.raises(ValueError, match="transaction 0"):
        validate_public_keys([tx.rlp() for tx in transactions], keys[::-1])
    tx = transactions[0]
    flipped = (
        tx.model_copy(update={"v": int(tx.v) ^ 1})
        if tx.ty
        else tx.model_copy(
            update={"v": int(tx.v) + (1 if int(tx.v) % 2 else -1)}
        )
    )
    with pytest.raises(ValueError, match="transaction 0"):
        validate_public_keys([flipped.rlp()], [keys[0]])
