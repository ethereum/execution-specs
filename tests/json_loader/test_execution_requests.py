"""Tests for typed execution request codecs."""

from typing import Any

import pytest
from ethereum_types.bytes import Bytes, Bytes32, Bytes48, Bytes96
from ethereum_types.numeric import U64

from ethereum.exceptions import InvalidBlock
from ethereum.state import Address

from .stateless_forks import STATELESS_FORKS


@pytest.fixture(params=STATELESS_FORKS, ids=lambda fork: fork.short_name)
def spec(request: pytest.FixtureRequest) -> Any:
    """Return the `execution_engine.requests` module of each fork."""
    return request.param.module("execution_engine.requests")


def _builder_deposit(spec: Any) -> Any:
    return spec.BuilderDepositRequest(
        pubkey=Bytes48(b"\x11" * 48),
        withdrawal_credentials=Bytes32(b"\x22" * 32),
        amount=U64(0x0102030405060708),
        signature=Bytes96(b"\x33" * 96),
    )


def _builder_exit(spec: Any) -> Any:
    return spec.BuilderExitRequest(
        source_address=Address(b"\x44" * 20),
        pubkey=Bytes48(b"\x55" * 48),
    )


def _all_execution_requests(spec: Any) -> Any:
    return spec.ExecutionRequests(
        deposits=(
            spec.DepositRequest(
                pubkey=Bytes48(b"\x01" * 48),
                withdrawal_credentials=Bytes32(b"\x02" * 32),
                amount=U64(3),
                signature=Bytes96(b"\x04" * 96),
                index=U64(5),
            ),
        ),
        withdrawals=(
            spec.WithdrawalRequest(
                source_address=Address(b"\x06" * 20),
                validator_pubkey=Bytes48(b"\x07" * 48),
                amount=U64(8),
            ),
        ),
        consolidations=(
            spec.ConsolidationRequest(
                source_address=Address(b"\x09" * 20),
                source_pubkey=Bytes48(b"\x0a" * 48),
                target_pubkey=Bytes48(b"\x0b" * 48),
            ),
        ),
        builder_deposits=(_builder_deposit(spec),),
        builder_exits=(_builder_exit(spec),),
    )


def test_builder_deposit_encode_decode(spec: Any) -> None:
    """Builder deposit amounts use little-endian wire encoding."""
    request = _builder_deposit(spec)
    requests = spec.ExecutionRequests(
        deposits=(),
        withdrawals=(),
        consolidations=(),
        builder_deposits=(request,),
        builder_exits=(),
    )

    wire = spec.encode_execution_requests(requests)

    assert wire == (
        Bytes(
            b"\x03"
            + bytes(request.pubkey)
            + bytes(request.withdrawal_credentials)
            + b"\x08\x07\x06\x05\x04\x03\x02\x01"
            + bytes(request.signature)
        ),
    )
    assert spec.decode_execution_requests(wire) == requests


def test_builder_exit_encode_decode(spec: Any) -> None:
    """Builder exits encode the source address followed by the pubkey."""
    request = _builder_exit(spec)
    requests = spec.ExecutionRequests(
        deposits=(),
        withdrawals=(),
        consolidations=(),
        builder_deposits=(),
        builder_exits=(request,),
    )

    wire = spec.encode_execution_requests(requests)

    assert wire == (
        Bytes(b"\x04" + bytes(request.source_address) + bytes(request.pubkey)),
    )
    assert spec.decode_execution_requests(wire) == requests


def test_all_execution_request_types_roundtrip_in_order(spec: Any) -> None:
    """All five request types round trip in strict ascending order."""
    requests = _all_execution_requests(spec)

    wire = spec.encode_execution_requests(requests)

    assert tuple(blob[0] for blob in wire) == (0, 1, 2, 3, 4)
    assert spec.decode_execution_requests(wire) == requests


@pytest.mark.parametrize(
    ("type_byte", "invalid_payload_size", "message"),
    [
        pytest.param(b"\x03", 183, "builder deposit", id="builder-deposit"),
        pytest.param(b"\x04", 67, "builder exit", id="builder-exit"),
    ],
)
def test_decode_rejects_invalid_builder_request_payload_length(
    spec: Any,
    type_byte: bytes,
    invalid_payload_size: int,
    message: str,
) -> None:
    """Builder request payloads must contain whole wire records."""
    wire = (Bytes(type_byte + b"\x00" * invalid_payload_size),)

    with pytest.raises(InvalidBlock, match=message):
        spec.decode_execution_requests(wire)


@pytest.mark.parametrize(
    ("spec", "type_byte", "name"),
    [
        pytest.param(
            fork,
            type_byte,
            name,
            id=f"{fork.short_name}-{name.replace(' ', '-')}",
        )
        for fork in STATELESS_FORKS
        for type_byte, (_, _, name) in fork.module(
            "execution_engine.requests"
        ).REQUEST_ITEM_TYPES.items()
    ],
    indirect=["spec"],
)
def test_decode_rejects_empty_request_payload(
    spec: Any,
    type_byte: Bytes,
    name: str,
) -> None:
    """A type byte without data has no typed equivalent."""
    with pytest.raises(InvalidBlock, match=f"Empty {name} request payload"):
        spec.decode_execution_requests((type_byte,))


def test_decode_rejects_non_ascending_builder_request_types(spec: Any) -> None:
    """Builder request types cannot be duplicated or misordered."""
    wire = spec.encode_execution_requests(_all_execution_requests(spec))

    with pytest.raises(InvalidBlock, match="strict ascending type order"):
        spec.decode_execution_requests((*wire[:3], wire[4], wire[3]))
