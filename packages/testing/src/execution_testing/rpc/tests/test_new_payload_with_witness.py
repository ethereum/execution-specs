"""Tests for `NewPayloadWithWitnessResponse` SSZ and RLP decoding."""

import ethereum_rlp as eth_rlp
import pytest
from ethereum_rlp.rlp import Extended
from remerkleable.basic import uint8
from remerkleable.byte_arrays import ByteList, ByteVector

from execution_testing.rpc.rpc_types import (
    MAX_WITNESS_BYTES,
    MAX_WITNESS_ITEM_BYTES,
    VALIDATION_ERROR_MAX,
    NewPayloadWithWitnessResponse,
    PayloadStatusEnum,
    _SSZExecutionWitness,
    _SSZNewPayloadWithWitnessResponse,
)


def _build_inner_witness(
    state: list[bytes], codes: list[bytes], headers: list[bytes]
) -> bytes:
    inner = _SSZExecutionWitness(
        state=[ByteList[MAX_WITNESS_ITEM_BYTES](b) for b in state],
        codes=[ByteList[MAX_WITNESS_ITEM_BYTES](b) for b in codes],
        headers=[ByteList[MAX_WITNESS_ITEM_BYTES](b) for b in headers],
    )
    return inner.encode_bytes()


def _build_response(
    status: int,
    latest_valid_hash: bytes | None,
    validation_error: str | None,
    witness_bytes: bytes,
) -> bytes:
    fields = _SSZNewPayloadWithWitnessResponse.fields()
    lvh_type = fields["latest_valid_hash"]
    ve_type = fields["validation_error"]

    if latest_valid_hash is None:
        lvh = lvh_type(selector=0, value=None)
    else:
        lvh = lvh_type(selector=1, value=ByteVector[32](latest_valid_hash))

    if validation_error is None:
        ve = ve_type(selector=0, value=None)
    else:
        ve = ve_type(
            selector=1,
            value=ByteList[VALIDATION_ERROR_MAX](
                validation_error.encode("utf-8")
            ),
        )

    resp = _SSZNewPayloadWithWitnessResponse(
        status=uint8(status),
        latest_valid_hash=lvh,
        validation_error=ve,
        witness=ByteList[MAX_WITNESS_BYTES](witness_bytes),
    )
    return resp.encode_bytes()


def test_decode_valid_with_witness() -> None:
    """A VALID response carries latestValidHash and a non-empty witness."""
    witness_bytes = _build_inner_witness(
        state=[b"\xaa\xaa", b"\xbb\xbb\xbb"],
        codes=[b"\x60\x01"],
        headers=[b"\xf9\x02"],
    )
    raw = _build_response(
        status=0,
        latest_valid_hash=b"\x11" * 32,
        validation_error=None,
        witness_bytes=witness_bytes,
    )

    decoded = NewPayloadWithWitnessResponse.from_ssz_bytes(raw)

    assert decoded.status == PayloadStatusEnum.VALID
    assert decoded.latest_valid_hash is not None
    assert bytes(decoded.latest_valid_hash) == b"\x11" * 32
    assert decoded.validation_error is None
    assert decoded.witness is not None
    assert [bytes(x) for x in decoded.witness.state] == [
        b"\xaa\xaa",
        b"\xbb\xbb\xbb",
    ]
    assert [bytes(x) for x in decoded.witness.codes] == [b"\x60\x01"]
    assert [bytes(x) for x in decoded.witness.headers] == [b"\xf9\x02"]


def test_decode_invalid_with_validation_error() -> None:
    """An INVALID response carries a validation_error string and no witness."""
    raw = _build_response(
        status=1,
        latest_valid_hash=None,
        validation_error="invalid state root",
        witness_bytes=b"",
    )

    decoded = NewPayloadWithWitnessResponse.from_ssz_bytes(raw)

    assert decoded.status == PayloadStatusEnum.INVALID
    assert decoded.latest_valid_hash is None
    assert decoded.validation_error == "invalid state root"
    assert decoded.witness is None


def test_decode_syncing_empty_witness() -> None:
    """A SYNCING response has no witness."""
    raw = _build_response(
        status=2,
        latest_valid_hash=None,
        validation_error=None,
        witness_bytes=b"",
    )

    decoded = NewPayloadWithWitnessResponse.from_ssz_bytes(raw)

    assert decoded.status == PayloadStatusEnum.SYNCING
    assert decoded.latest_valid_hash is None
    assert decoded.validation_error is None
    assert decoded.witness is None


def test_decode_unknown_status_byte_raises() -> None:
    """An unknown status uint8 raises a descriptive error."""
    raw = _build_response(
        status=99,
        latest_valid_hash=None,
        validation_error=None,
        witness_bytes=b"",
    )

    with pytest.raises(ValueError, match="Unknown SSZ status byte: 99"):
        NewPayloadWithWitnessResponse.from_ssz_bytes(raw)


def test_decode_invalid_with_witness_raises() -> None:
    """A non-VALID SSZ response must not carry witness bytes."""
    raw = _build_response(
        status=1,
        latest_valid_hash=None,
        validation_error="invalid state root",
        witness_bytes=_build_inner_witness(
            state=[b"\xaa"],
            codes=[],
            headers=[],
        ),
    )

    with pytest.raises(
        ValueError, match="INVALID SSZ response must not contain a witness"
    ):
        NewPayloadWithWitnessResponse.from_ssz_bytes(raw)


# --- JSON-RPC (RLP witness) decode ---


def _json_rpc_witness_rlp(
    headers: list[Extended],
    codes: list[bytes],
    state: list[bytes],
    *,
    legacy_keys: list[bytes] | None = None,
) -> bytes:
    """Build an RLP witness payload returned by the JSON-RPC endpoint."""
    fields: list[Extended] = [headers, codes, state]
    if legacy_keys is not None:
        fields.append(legacy_keys)
    return eth_rlp.encode(fields)


def test_decode_json_rpc_valid() -> None:
    """Round-trip a VALID JSON-RPC response with RLP witness."""
    # A minimal "header" RLP list with two short fields.
    header_list = [b"\x01" * 4, b"\x02" * 4]
    witness_hex = (
        "0x"
        + _json_rpc_witness_rlp(
            headers=[header_list],
            codes=[b"\x60\x01"],
            state=[b"\xaa\xaa", b"\xbb"],
        ).hex()
    )

    response_json = {
        "status": "VALID",
        "latestValidHash": "0x" + ("11" * 32),
        "validationError": None,
        "witness": witness_hex,
    }

    decoded = NewPayloadWithWitnessResponse.from_json_rpc_result(response_json)

    assert decoded.status == PayloadStatusEnum.VALID
    assert decoded.latest_valid_hash is not None
    assert bytes(decoded.latest_valid_hash) == b"\x11" * 32
    assert decoded.validation_error is None
    assert decoded.witness is not None
    assert [bytes(c) for c in decoded.witness.codes] == [b"\x60\x01"]
    assert sorted(bytes(s) for s in decoded.witness.state) == sorted(
        [b"\xaa\xaa", b"\xbb"]
    )
    # Headers must come back as re-encoded RLP bytes (matching the fixture
    # format), so encoding the decoded header recovers the original list.
    assert len(decoded.witness.headers) == 1
    assert eth_rlp.decode(bytes(decoded.witness.headers[0])) == header_list


def test_decode_json_rpc_ignores_legacy_keys() -> None:
    """A legacy fourth `keys` RLP field is ignored."""
    header_list = [b"\x01" * 4, b"\x02" * 4]
    witness_hex = (
        "0x"
        + _json_rpc_witness_rlp(
            headers=[header_list],
            codes=[b"\x60\x01"],
            state=[b"\xaa"],
            legacy_keys=[b"legacy-key"],
        ).hex()
    )

    decoded = NewPayloadWithWitnessResponse.from_json_rpc_result(
        {
            "status": "VALID",
            "latestValidHash": "0x" + ("11" * 32),
            "validationError": None,
            "witness": witness_hex,
        }
    )

    assert decoded.witness is not None
    assert [bytes(c) for c in decoded.witness.codes] == [b"\x60\x01"]
    assert [bytes(s) for s in decoded.witness.state] == [b"\xaa"]
    assert eth_rlp.decode(bytes(decoded.witness.headers[0])) == header_list


def test_decode_json_rpc_invalid_no_witness() -> None:
    """An INVALID JSON-RPC response has no witness payload."""
    response_json = {
        "status": "INVALID",
        "latestValidHash": None,
        "validationError": "block root mismatch",
        # The witness field may be omitted on INVALID.
    }

    decoded = NewPayloadWithWitnessResponse.from_json_rpc_result(response_json)

    assert decoded.status == PayloadStatusEnum.INVALID
    assert decoded.latest_valid_hash is None
    assert decoded.validation_error == "block root mismatch"
    assert decoded.witness is None


def test_decode_json_rpc_empty_witness_hex() -> None:
    """Parse an empty non-VALID witness as no witness."""
    response_json = {
        "status": "SYNCING",
        "latestValidHash": None,
        "validationError": None,
        "witness": "0x",
    }

    decoded = NewPayloadWithWitnessResponse.from_json_rpc_result(response_json)

    assert decoded.status == PayloadStatusEnum.SYNCING
    assert decoded.witness is None


def test_decode_json_rpc_witness_must_be_0x_prefixed() -> None:
    """Witness hex must use the JSON-RPC 0x prefix."""
    response_json = {
        "status": "VALID",
        "latestValidHash": "0x" + ("11" * 32),
        "validationError": None,
        "witness": _json_rpc_witness_rlp(
            headers=[],
            codes=[],
            state=[],
        ).hex(),
    }

    with pytest.raises(ValueError, match="0x-prefixed"):
        NewPayloadWithWitnessResponse.from_json_rpc_result(response_json)


def test_decode_json_rpc_rejects_non_list_witness_field() -> None:
    """Codes and state must be RLP lists, not bare byte strings."""
    header_list = [b"\x01" * 4, b"\x02" * 4]
    witness_hex = (
        "0x"
        + eth_rlp.encode(
            [
                [header_list],
                b"\x60\x01",
                [b"\xaa"],
            ]
        ).hex()
    )
    response_json = {
        "status": "VALID",
        "latestValidHash": "0x" + ("11" * 32),
        "validationError": None,
        "witness": witness_hex,
    }

    with pytest.raises(ValueError, match="codes must be an RLP list"):
        NewPayloadWithWitnessResponse.from_json_rpc_result(response_json)
