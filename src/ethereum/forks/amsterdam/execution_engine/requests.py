"""
Typed execution-layer requests and engine-API wire-form codecs.

The consensus layer defines ``ExecutionRequests`` as a typed Container
holding deposit, withdrawal, consolidation, builder deposit, and builder exit
lists.
"""

from dataclasses import dataclass
from typing import Annotated, Any, Dict, Sequence, Tuple, Type, final

from ethereum_types.bytes import Bytes, Bytes32, Bytes48, Bytes96
from ethereum_types.frozen import slotted_freezable
from ethereum_types.numeric import U64

from ethereum.exceptions import InvalidBlock
from ethereum.state import Address
from ethereum.utils.ssz import (
    ProgressiveSszContainer,
    SszContainer,
    progressive_list,
)

from ..requests import (
    BUILDER_DEPOSIT_REQUEST_TYPE,
    BUILDER_EXIT_REQUEST_TYPE,
    CONSOLIDATION_REQUEST_TYPE,
    DEPOSIT_REQUEST_TYPE,
    WITHDRAWAL_REQUEST_TYPE,
)

DEPOSIT_REQUEST_SIZE = 48 + 32 + 8 + 96 + 8
WITHDRAWAL_REQUEST_SIZE = 20 + 48 + 8
CONSOLIDATION_REQUEST_SIZE = 20 + 48 + 48
BUILDER_DEPOSIT_REQUEST_SIZE = 184
BUILDER_EXIT_REQUEST_SIZE = 68


@final
@slotted_freezable
@dataclass
class DepositRequest(SszContainer):
    """A single EIP-6110 deposit request."""

    pubkey: Bytes48
    withdrawal_credentials: Bytes32
    amount: U64
    signature: Bytes96
    index: U64


@final
@slotted_freezable
@dataclass
class WithdrawalRequest(SszContainer):
    """A single EIP-7002 withdrawal request."""

    source_address: Address
    validator_pubkey: Bytes48
    amount: U64


@final
@slotted_freezable
@dataclass
class ConsolidationRequest(SszContainer):
    """A single EIP-7251 consolidation request."""

    source_address: Address
    source_pubkey: Bytes48
    target_pubkey: Bytes48


@final
@slotted_freezable
@dataclass
class BuilderDepositRequest(SszContainer):
    """A single EIP-8282 builder deposit request."""

    pubkey: Bytes48
    withdrawal_credentials: Bytes32
    amount: U64
    signature: Bytes96


@final
@slotted_freezable
@dataclass
class BuilderExitRequest(SszContainer):
    """A single EIP-8282 builder exit request."""

    source_address: Address
    pubkey: Bytes48


@final
@slotted_freezable
@dataclass
class ExecutionRequests(ProgressiveSszContainer):
    """
    Typed engine-API container of execution-layer triggered requests.

    Mirrors the consensus-layer ``ExecutionRequests`` Container.
    """

    deposits: Annotated[Tuple[DepositRequest, ...], progressive_list()]
    withdrawals: Annotated[Tuple[WithdrawalRequest, ...], progressive_list()]
    consolidations: Annotated[
        Tuple[ConsolidationRequest, ...], progressive_list()
    ]
    builder_deposits: Annotated[
        Tuple[BuilderDepositRequest, ...], progressive_list()
    ]
    builder_exits: Annotated[
        Tuple[BuilderExitRequest, ...], progressive_list()
    ]


REQUEST_ITEM_TYPES: Dict[Bytes, Tuple[Type[SszContainer], int, str]] = {
    DEPOSIT_REQUEST_TYPE: (DepositRequest, DEPOSIT_REQUEST_SIZE, "deposit"),
    WITHDRAWAL_REQUEST_TYPE: (
        WithdrawalRequest,
        WITHDRAWAL_REQUEST_SIZE,
        "withdrawal",
    ),
    CONSOLIDATION_REQUEST_TYPE: (
        ConsolidationRequest,
        CONSOLIDATION_REQUEST_SIZE,
        "consolidation",
    ),
    BUILDER_DEPOSIT_REQUEST_TYPE: (
        BuilderDepositRequest,
        BUILDER_DEPOSIT_REQUEST_SIZE,
        "builder deposit",
    ),
    BUILDER_EXIT_REQUEST_TYPE: (
        BuilderExitRequest,
        BUILDER_EXIT_REQUEST_SIZE,
        "builder exit",
    ),
}
"""
Item type, serialized item size, and name used in error messages for each
known request type byte.
"""


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
    request_lists: Tuple[Tuple[Bytes, Sequence[SszContainer]], ...] = (
        (DEPOSIT_REQUEST_TYPE, requests.deposits),
        (WITHDRAWAL_REQUEST_TYPE, requests.withdrawals),
        (CONSOLIDATION_REQUEST_TYPE, requests.consolidations),
        (BUILDER_DEPOSIT_REQUEST_TYPE, requests.builder_deposits),
        (BUILDER_EXIT_REQUEST_TYPE, requests.builder_exits),
    )
    return tuple(
        request_type + b"".join(item.encode_bytes() for item in items)
        for request_type, items in request_lists
        if items
    )


def decode_execution_requests(
    wire: Sequence[Bytes],
) -> ExecutionRequests:
    """
    Parse the engine-API wire form into a typed ``ExecutionRequests``.

    Validates strict ascending type order, no duplicate type bytes, no
    unknown type bytes, and that each payload is non-empty with a length
    that is a multiple of the per-type item size. The wire form omits
    empty lists, so an empty payload has no typed equivalent.
    """
    decoded: Dict[Bytes, Tuple[Any, ...]] = {}

    last_type = -1
    for blob in wire:
        if len(blob) < 1:
            raise InvalidBlock("Empty execution request blob")
        request_type = blob[0:1]
        body = blob[1:]
        if blob[0] <= last_type:
            raise InvalidBlock(
                "Execution requests must be in strict ascending type order"
            )
        last_type = blob[0]

        if request_type not in REQUEST_ITEM_TYPES:
            raise InvalidBlock(
                f"Unknown execution request type byte {request_type!r}"
            )
        item_type, item_size, name = REQUEST_ITEM_TYPES[request_type]
        if len(body) == 0:
            raise InvalidBlock(f"Empty {name} request payload")
        if len(body) % item_size != 0:
            raise InvalidBlock(f"Invalid {name} request payload length")
        decoded[request_type] = tuple(
            item_type.decode_bytes(body[i : i + item_size])
            for i in range(0, len(body), item_size)
        )

    return ExecutionRequests(
        deposits=decoded.get(DEPOSIT_REQUEST_TYPE, ()),
        withdrawals=decoded.get(WITHDRAWAL_REQUEST_TYPE, ()),
        consolidations=decoded.get(CONSOLIDATION_REQUEST_TYPE, ()),
        builder_deposits=decoded.get(BUILDER_DEPOSIT_REQUEST_TYPE, ()),
        builder_exits=decoded.get(BUILDER_EXIT_REQUEST_TYPE, ()),
    )
