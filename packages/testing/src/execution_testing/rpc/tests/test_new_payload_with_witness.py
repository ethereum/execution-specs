"""Tests for `NewPayloadWithWitnessResponse` SSZ and RLP decoding."""

import ethereum_rlp as eth_rlp
import pytest
from ethereum_rlp.rlp import Extended

from execution_testing.rpc.rpc_types import (
    NewPayloadWithWitnessResponse,
    PayloadStatusEnum,
)


def _offsets(parts: list[bytes]) -> bytes:
    """Build variable-field SSZ bytes independently of production schemas."""
    offset = 4 * len(parts)
    fixed = b""
    for part in parts:
        fixed += offset.to_bytes(4, "little")
        offset += len(part)
    return fixed + b"".join(parts)


def _build_inner_witness(
    state: list[bytes], codes: list[bytes], headers: list[bytes]
) -> bytes:
    return _offsets([_offsets(state), _offsets(codes), _offsets(headers)])


def _build_response(
    status: int,
    latest_valid_hash: bytes | None,
    validation_error: str | None,
    witness_bytes: bytes,
    public_keys: bytes = b"",
) -> bytes:
    latest = latest_valid_hash or b""
    error = (
        _offsets([validation_error.encode()])
        if validation_error is not None
        else b""
    )
    payload_status = (
        bytes([status])
        + (9).to_bytes(4, "little")
        + (9 + len(latest)).to_bytes(4, "little")
        + latest
        + error
    )
    witness = _offsets([witness_bytes]) if witness_bytes else b""
    return _offsets([payload_status, witness, public_keys])


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


@pytest.mark.parametrize("status", [0, 1, 2, 3])
def test_reject_noncanonical_offsets_and_trailing_bytes(status: int) -> None:
    """Reject offset gaps even when the library can decode the contents."""
    raw = _build_response(
        status,
        bytes(32) if status == 0 else None,
        None,
        _build_inner_witness([], [], [b"header"]) if status == 0 else b"",
    )
    # Move every outer offset by one without moving the actual contents.
    # The library previously ignored both the gap and the trailing byte.
    malformed = (
        b"".join(
            (int.from_bytes(raw[i : i + 4], "little") + 1).to_bytes(
                4, "little"
            )
            for i in (0, 4, 8)
        )
        + raw[12:]
        + b"\xff"
    )
    with pytest.raises(ValueError, match="Non-canonical SSZ"):
        NewPayloadWithWitnessResponse.from_ssz_bytes(malformed)


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


@pytest.mark.parametrize("status", [4, 255])
def test_removed_status_is_rejected(status: int) -> None:
    """Reject INVALID_BLOCK_HASH and unknown REST statuses."""
    with pytest.raises(ValueError, match="Unknown SSZ status"):
        NewPayloadWithWitnessResponse.from_ssz_bytes(
            _build_response(status, None, None, b"")
        )


def test_valid_requires_witness() -> None:
    """Reject missing witnesses even for already-known valid payloads."""
    with pytest.raises(ValueError, match="must contain a witness"):
        NewPayloadWithWitnessResponse.from_ssz_bytes(
            _build_response(0, bytes(32), None, b"")
        )


@pytest.mark.parametrize("error", [None, ""])
def test_optional_empty_error_is_distinct(error: str | None) -> None:
    """Distinguish no validation error from a present empty string."""
    result = NewPayloadWithWitnessResponse.from_ssz_bytes(
        _build_response(1, None, error, b"")
    )
    assert result.validation_error == error


@pytest.mark.parametrize("field,limit", [(0, 1024), (1, 65536), (2, 1024)])
@pytest.mark.parametrize("excess", [0, 1])
def test_witness_item_bounds(field: int, limit: int, excess: int) -> None:
    """Accept maximum-sized witness items and reject the next byte."""
    parts: list[list[bytes]] = [[], [], [b"header"]]
    parts[field] = [bytes(limit + excess)]
    raw = _build_response(0, bytes(32), None, _build_inner_witness(*parts))
    if excess:
        with pytest.raises(Exception, match="size bounds"):
            NewPayloadWithWitnessResponse.from_ssz_bytes(raw)
    else:
        assert NewPayloadWithWitnessResponse.from_ssz_bytes(raw).witness


@pytest.mark.parametrize("count", [0, 256, 257])
def test_header_count_bounds(count: int) -> None:
    """Require a parent header and at most 256 ancestor headers."""
    raw = _build_response(
        0,
        bytes(32),
        None,
        _build_inner_witness([], [], [b"header"] * count),
    )
    if count == 256:
        assert NewPayloadWithWitnessResponse.from_ssz_bytes(raw).witness
    else:
        with pytest.raises(Exception, match="parent header|count 257"):
            NewPayloadWithWitnessResponse.from_ssz_bytes(raw)


@pytest.mark.parametrize("status", [1, 2, 3])
def test_nonvalid_public_keys_rejected(status: int) -> None:
    """Non-VALID responses must omit public keys as well as witnesses."""
    raw = _build_response(status, None, None, b"", b"\x04" + bytes(64))
    with pytest.raises(ValueError, match="public keys"):
        NewPayloadWithWitnessResponse.from_ssz_bytes(raw)


def test_public_keys_decode_in_order_with_duplicates() -> None:
    """Preserve the fixed-size key list without per-key SSZ offsets."""
    keys = [b"\x04" + bytes([i]) * 64 for i in (1, 2, 1)]
    raw = _build_response(
        0,
        bytes(32),
        None,
        _build_inner_witness([], [], [b"header"]),
        b"".join(keys),
    )
    assert (
        list(NewPayloadWithWitnessResponse.from_ssz_bytes(raw).public_keys)
        == keys
    )


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
