"""
Typed execution-layer requests and engine-API wire-form codecs.

The consensus layer defines ``ExecutionRequests`` as a typed Container
holding ``deposits``, ``withdrawals``, and ``consolidations`` lists. At
the engine-API boundary, that Container is flattened to a tuple of
opaque blobs of the form ``TYPE_BYTE || concat(serialize(item))``,
ordered ascending by type. This module exposes the typed Container and
the boundary codecs (mirrors CL's ``get_execution_requests_list()``).
"""

from dataclasses import dataclass
from typing import Sequence, Tuple

from ethereum_types.bytes import Bytes, Bytes32, Bytes48, Bytes96
from ethereum_types.frozen import slotted_freezable
from ethereum_types.numeric import U64

from ethereum.exceptions import InvalidBlock
from ethereum.state import Address

from ..requests import (
    CONSOLIDATION_REQUEST_TYPE,
    DEPOSIT_REQUEST_TYPE,
    WITHDRAWAL_REQUEST_TYPE,
)

DEPOSIT_REQUEST_SIZE = 48 + 32 + 8 + 96 + 8
WITHDRAWAL_REQUEST_SIZE = 20 + 48 + 8
CONSOLIDATION_REQUEST_SIZE = 20 + 48 + 48


@slotted_freezable
@dataclass
class DepositRequest:
    """A single EIP-6110 deposit request."""

    pubkey: Bytes48
    withdrawal_credentials: Bytes32
    amount: U64
    signature: Bytes96
    index: U64


@slotted_freezable
@dataclass
class WithdrawalRequest:
    """A single EIP-7002 withdrawal request."""

    source_address: Address
    validator_pubkey: Bytes48
    amount: U64


@slotted_freezable
@dataclass
class ConsolidationRequest:
    """A single EIP-7251 consolidation request."""

    source_address: Address
    source_pubkey: Bytes48
    target_pubkey: Bytes48


@slotted_freezable
@dataclass
class ExecutionRequests:
    """
    Typed engine-API container of execution-layer triggered requests.

    Mirrors the consensus-layer ``ExecutionRequests`` Container.
    """

    deposits: Tuple[DepositRequest, ...]
    withdrawals: Tuple[WithdrawalRequest, ...]
    consolidations: Tuple[ConsolidationRequest, ...]


def _encode_deposit(d: DepositRequest) -> Bytes:
    return Bytes(
        bytes(d.pubkey)
        + bytes(d.withdrawal_credentials)
        + bytes(d.amount.to_le_bytes8())
        + bytes(d.signature)
        + bytes(d.index.to_le_bytes8())
    )


def _encode_withdrawal(w: WithdrawalRequest) -> Bytes:
    return Bytes(
        bytes(w.source_address)
        + bytes(w.validator_pubkey)
        + bytes(w.amount.to_le_bytes8())
    )


def _encode_consolidation(c: ConsolidationRequest) -> Bytes:
    return Bytes(
        bytes(c.source_address)
        + bytes(c.source_pubkey)
        + bytes(c.target_pubkey)
    )


def _decode_deposit(payload: Bytes) -> DepositRequest:
    return DepositRequest(
        pubkey=Bytes48(payload[0:48]),
        withdrawal_credentials=Bytes32(payload[48:80]),
        amount=U64.from_le_bytes(payload[80:88]),
        signature=Bytes96(payload[88:184]),
        index=U64.from_le_bytes(payload[184:192]),
    )


def _decode_withdrawal(payload: Bytes) -> WithdrawalRequest:
    return WithdrawalRequest(
        source_address=Address(payload[0:20]),
        validator_pubkey=Bytes48(payload[20:68]),
        amount=U64.from_le_bytes(payload[68:76]),
    )


def _decode_consolidation(payload: Bytes) -> ConsolidationRequest:
    return ConsolidationRequest(
        source_address=Address(payload[0:20]),
        source_pubkey=Bytes48(payload[20:68]),
        target_pubkey=Bytes48(payload[68:116]),
    )


def encode_execution_requests(
    requests: ExecutionRequests,
) -> Tuple[Bytes, ...]:
    """
    Flatten a typed ``ExecutionRequests`` into the engine-API wire form.

    Each non-empty list is emitted as a single blob
    ``TYPE_BYTE || concat(serialize(item) for item)``, in ascending
    type order. Empty lists are omitted. Mirrors CL's
    ``get_execution_requests_list()``.
    """
    output: list[Bytes] = []
    if requests.deposits:
        body = b"".join(_encode_deposit(d) for d in requests.deposits)
        output.append(Bytes(DEPOSIT_REQUEST_TYPE + body))
    if requests.withdrawals:
        body = b"".join(_encode_withdrawal(w) for w in requests.withdrawals)
        output.append(Bytes(WITHDRAWAL_REQUEST_TYPE + body))
    if requests.consolidations:
        body = b"".join(
            _encode_consolidation(c) for c in requests.consolidations
        )
        output.append(Bytes(CONSOLIDATION_REQUEST_TYPE + body))
    return tuple(output)


def decode_execution_requests(
    wire: Sequence[Bytes],
) -> ExecutionRequests:
    """
    Parse the engine-API wire form into a typed ``ExecutionRequests``.

    Validates strict ascending type order, no duplicate type bytes, no
    unknown type bytes, and that each payload's length is a multiple of
    the per-type item size.
    """
    deposits: Tuple[DepositRequest, ...] = ()
    withdrawals: Tuple[WithdrawalRequest, ...] = ()
    consolidations: Tuple[ConsolidationRequest, ...] = ()

    last_type = -1
    for blob in wire:
        if len(blob) < 1:
            raise InvalidBlock("Empty execution request blob")
        type_byte = bytes(blob[0:1])
        body = bytes(blob[1:])
        type_int = type_byte[0]
        if type_int <= last_type:
            raise InvalidBlock(
                "Execution requests must be in strict ascending type order"
            )
        last_type = type_int

        if type_byte == DEPOSIT_REQUEST_TYPE:
            if len(body) % DEPOSIT_REQUEST_SIZE != 0:
                raise InvalidBlock("Invalid deposit request payload length")
            deposits = tuple(
                _decode_deposit(Bytes(body[i : i + DEPOSIT_REQUEST_SIZE]))
                for i in range(0, len(body), DEPOSIT_REQUEST_SIZE)
            )
        elif type_byte == WITHDRAWAL_REQUEST_TYPE:
            if len(body) % WITHDRAWAL_REQUEST_SIZE != 0:
                raise InvalidBlock("Invalid withdrawal request payload length")
            withdrawals = tuple(
                _decode_withdrawal(
                    Bytes(body[i : i + WITHDRAWAL_REQUEST_SIZE])
                )
                for i in range(0, len(body), WITHDRAWAL_REQUEST_SIZE)
            )
        elif type_byte == CONSOLIDATION_REQUEST_TYPE:
            if len(body) % CONSOLIDATION_REQUEST_SIZE != 0:
                raise InvalidBlock(
                    "Invalid consolidation request payload length"
                )
            consolidations = tuple(
                _decode_consolidation(
                    Bytes(body[i : i + CONSOLIDATION_REQUEST_SIZE])
                )
                for i in range(0, len(body), CONSOLIDATION_REQUEST_SIZE)
            )
        else:
            raise InvalidBlock(
                f"Unknown execution request type byte {type_byte!r}"
            )

    return ExecutionRequests(
        deposits=deposits,
        withdrawals=withdrawals,
        consolidations=consolidations,
    )
