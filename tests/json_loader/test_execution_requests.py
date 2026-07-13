"""Tests for Amsterdam typed execution request codecs."""

import pytest
from ethereum_types.bytes import Bytes, Bytes32, Bytes48, Bytes96
from ethereum_types.numeric import U64

from ethereum.exceptions import InvalidBlock
from ethereum.forks.amsterdam.execution_engine.requests import (
    BuilderDepositRequest,
    BuilderExitRequest,
    ConsolidationRequest,
    DepositRequest,
    ExecutionRequests,
    WithdrawalRequest,
    decode_execution_requests,
    encode_execution_requests,
)
from ethereum.state import Address


def _builder_deposit() -> BuilderDepositRequest:
    return BuilderDepositRequest(
        pubkey=Bytes48(b"\x11" * 48),
        withdrawal_credentials=Bytes32(b"\x22" * 32),
        amount=U64(0x0102030405060708),
        signature=Bytes96(b"\x33" * 96),
    )


def _builder_exit() -> BuilderExitRequest:
    return BuilderExitRequest(
        source_address=Address(b"\x44" * 20),
        pubkey=Bytes48(b"\x55" * 48),
    )


def _all_execution_requests() -> ExecutionRequests:
    return ExecutionRequests(
        deposits=(
            DepositRequest(
                pubkey=Bytes48(b"\x01" * 48),
                withdrawal_credentials=Bytes32(b"\x02" * 32),
                amount=U64(3),
                signature=Bytes96(b"\x04" * 96),
                index=U64(5),
            ),
        ),
        withdrawals=(
            WithdrawalRequest(
                source_address=Address(b"\x06" * 20),
                validator_pubkey=Bytes48(b"\x07" * 48),
                amount=U64(8),
            ),
        ),
        consolidations=(
            ConsolidationRequest(
                source_address=Address(b"\x09" * 20),
                source_pubkey=Bytes48(b"\x0a" * 48),
                target_pubkey=Bytes48(b"\x0b" * 48),
            ),
        ),
        builder_deposits=(_builder_deposit(),),
        builder_exits=(_builder_exit(),),
    )


def test_builder_deposit_encode_decode() -> None:
    """Builder deposit amounts use little-endian wire encoding."""
    request = _builder_deposit()
    requests = ExecutionRequests(
        deposits=(),
        withdrawals=(),
        consolidations=(),
        builder_deposits=(request,),
        builder_exits=(),
    )

    wire = encode_execution_requests(requests)

    assert wire == (
        Bytes(
            b"\x03"
            + bytes(request.pubkey)
            + bytes(request.withdrawal_credentials)
            + b"\x08\x07\x06\x05\x04\x03\x02\x01"
            + bytes(request.signature)
        ),
    )
    assert decode_execution_requests(wire) == requests


def test_builder_exit_encode_decode() -> None:
    """Builder exits encode the source address followed by the pubkey."""
    request = _builder_exit()
    requests = ExecutionRequests(
        deposits=(),
        withdrawals=(),
        consolidations=(),
        builder_deposits=(),
        builder_exits=(request,),
    )

    wire = encode_execution_requests(requests)

    assert wire == (
        Bytes(b"\x04" + bytes(request.source_address) + bytes(request.pubkey)),
    )
    assert decode_execution_requests(wire) == requests


def test_all_execution_request_types_roundtrip_in_order() -> None:
    """All five request types round trip in strict ascending order."""
    requests = _all_execution_requests()

    wire = encode_execution_requests(requests)

    assert tuple(blob[0] for blob in wire) == (0, 1, 2, 3, 4)
    assert decode_execution_requests(wire) == requests


@pytest.mark.parametrize(
    ("type_byte", "invalid_payload_size", "message"),
    [
        pytest.param(b"\x03", 183, "builder deposit", id="builder-deposit"),
        pytest.param(b"\x04", 67, "builder exit", id="builder-exit"),
    ],
)
def test_decode_rejects_invalid_builder_request_payload_length(
    type_byte: bytes,
    invalid_payload_size: int,
    message: str,
) -> None:
    """Builder request payloads must contain whole wire records."""
    wire = (Bytes(type_byte + b"\x00" * invalid_payload_size),)

    with pytest.raises(InvalidBlock, match=message):
        decode_execution_requests(wire)


def test_decode_rejects_non_ascending_builder_request_types() -> None:
    """Builder request types cannot be duplicated or misordered."""
    wire = encode_execution_requests(_all_execution_requests())

    with pytest.raises(InvalidBlock, match="strict ascending type order"):
        decode_execution_requests((*wire[:3], wire[4], wire[3]))
