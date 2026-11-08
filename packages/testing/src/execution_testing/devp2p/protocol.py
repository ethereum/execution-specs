"""
Message encoding for the devp2p base protocol and the eth capability.

Only the subset a full syncing client asks of a serving peer is
implemented: the base protocol handshake and liveness messages, the eth
status exchange, and the header, body and range messages that carry
chain data. Every other message is ignored.
"""

import zlib
from dataclasses import dataclass
from enum import IntEnum
from typing import (
    List,
    Mapping,
    NamedTuple,
    Sequence,
    Tuple,
    Type,
    TypeVar,
)

import ethereum_rlp as eth_rlp
from ethereum_rlp.exceptions import DecodingError
from ethereum_rlp.rlp import RLP, decode_to
from ethereum_types.numeric import Uint

from execution_testing.base_types import Hash

P2P_VERSION = 5
"""
Base protocol version advertised to the remote node.

Version 5 Snappy-compresses every payload after Hello, once both sides
advertise it; a version 4 remote gets an uncompressed connection.
"""

ETH_OFFSET = 16
"""Message code offset of the first capability after the base protocol."""


class MessageCode(IntEnum):
    """
    The message codes this peer sends or answers.

    Base protocol codes come first; eth capability codes are already
    offset onto the wire by `ETH_OFFSET`. A code read from a peer stays
    an `int`, since a client may send any other code.
    """

    HELLO = 0x00
    DISCONNECT = 0x01
    PING = 0x02
    PONG = 0x03
    STATUS = ETH_OFFSET + 0x00
    GET_BLOCK_HEADERS = ETH_OFFSET + 0x03
    BLOCK_HEADERS = ETH_OFFSET + 0x04
    GET_BLOCK_BODIES = ETH_OFFSET + 0x05
    BLOCK_BODIES = ETH_OFFSET + 0x06
    GET_RECEIPTS = ETH_OFFSET + 0x0F
    RECEIPTS = ETH_OFFSET + 0x10
    BLOCK_RANGE_UPDATE = ETH_OFFSET + 0x11
    GET_BLOCK_ACCESS_LISTS = ETH_OFFSET + 0x12
    BLOCK_ACCESS_LISTS = ETH_OFFSET + 0x13


class EthVersion(IntEnum):
    """An implemented version of the eth capability."""

    ETH_69 = 69
    ETH_70 = 70
    ETH_71 = 71
    ETH_72 = 72


class ProtocolError(Exception):
    """Raised when a peer message cannot be decoded as expected."""


Shape = TypeVar("Shape", bound=RLP)


def _decode_shaped(shape: Type[Shape], payload: bytes, message: str) -> Shape:
    """
    Decode `payload` into the dataclass `shape`, or raise `ProtocolError`.

    The decoding is exact: a field of the wrong kind or length, a list
    of the wrong length, a non-canonical integer or trailing bytes are
    all refused with `message`.
    """
    try:
        return decode_to(shape, payload)
    except DecodingError as error:
        raise ProtocolError(message) from error


@dataclass
class _HashListRequest:
    """The `[request-id, [hash, ...]]` shape of a by-hash request."""

    request_id: Uint
    hashes: Tuple[Hash, ...]


@dataclass
class _OffsetHashListRequest:
    """The eth/70 GetReceipts shape, with the first block's offset."""

    request_id: Uint
    first_block_receipt_index: Uint
    hashes: Tuple[Hash, ...]


def encode_list(encoded_items: Sequence[bytes]) -> bytes:
    """
    Wrap already encoded RLP `encoded_items` in a list header.

    Fixture headers and legacy transactions arrive as RLP; encoding them
    again would nest them one level too deep.
    """
    payload = b"".join(encoded_items)
    if len(payload) < 56:
        return bytes([0xC0 + len(payload)]) + payload
    length = len(payload).to_bytes((len(payload).bit_length() + 7) // 8, "big")
    return bytes([0xF7 + len(length)]) + length + payload


def encode_transactions(transactions: Sequence[bytes]) -> bytes:
    """
    Encode a block's transactions as they appear in a block body.

    A legacy transaction is an RLP list and is spliced in unchanged; a
    typed transaction is an opaque byte string holding its type prefix
    and payload, and is encoded as such.
    """
    items = []
    for transaction in transactions:
        if transaction and transaction[0] >= 0xC0:
            items.append(transaction)
        else:
            items.append(eth_rlp.encode(transaction))
    return encode_list(items)


@dataclass(frozen=True)
class ForkSchedule:
    """
    When a network's forks activate: by block number, then by timestamp.

    The order and repetition of the activations do not matter, and one
    at or before genesis is part of the genesis rule set, so a network
    that runs one fork from genesis has the empty schedule.
    """

    block_numbers: Tuple[int, ...] = ()
    timestamps: Tuple[int, ...] = ()


GENESIS_FORK_ONLY = ForkSchedule()
"""The schedule of a network that runs one fork from genesis."""


class ForkId(NamedTuple):
    """The EIP-2124 fork identifier, `[fork-hash, fork-next]` on the wire."""

    fork_hash: bytes
    """The CRC32 of the genesis hash and every fork activation passed."""
    fork_next: Uint
    """The first fork activation not yet passed, or 0 if there is none."""


def fork_id(
    genesis_hash: bytes,
    schedule: ForkSchedule,
    *,
    genesis_timestamp: int,
    head_number: int,
    head_timestamp: int,
) -> ForkId:
    """
    Return the EIP-2124 fork identifier of a chain at its head.

    The identifier is computed as go-ethereum's `forkid.NewID` computes
    it: the block forks past genesis and then the time forks past the
    genesis timestamp, each sorted without repeats, are folded into the
    checksum while the head has passed them (reached them, inclusive);
    the first one it has not passed is the next fork.
    """
    block_forks = sorted(
        {number for number in schedule.block_numbers if number > 0}
    )
    time_forks = sorted(
        {time for time in schedule.timestamps if time > genesis_timestamp}
    )
    checksum = zlib.crc32(genesis_hash)
    for activation, head in [
        *((number, head_number) for number in block_forks),
        *((time, head_timestamp) for time in time_forks),
    ]:
        if activation > head:
            return ForkId(checksum.to_bytes(4, "big"), Uint(activation))
        checksum = zlib.crc32(activation.to_bytes(8, "big"), checksum)
    return ForkId(checksum.to_bytes(4, "big"), Uint(0))


def encode_hello(
    client_id: str,
    public_key: bytes,
    eth_versions: Sequence[int],
    listen_port: int = 0,
) -> bytes:
    """
    Encode the base protocol Hello message.

    One `("eth", version)` pair is advertised per entry of
    `eth_versions`, in ascending order.
    """
    return eth_rlp.encode(
        [
            Uint(P2P_VERSION),
            client_id.encode(),
            [[b"eth", Uint(version)] for version in sorted(eth_versions)],
            Uint(listen_port),
            public_key,
        ]
    )


def highest_common_eth_version(
    local_versions: Sequence[EthVersion],
    remote_capabilities: Sequence[Tuple[str, int]],
) -> EthVersion | None:
    """
    Return the eth version RLPx negotiation selects, if any.

    Both sides list `(name, version)` pairs in Hello and the shared
    capability with the highest version wins. Capabilities other than
    eth (e.g. snap) are not implemented and never join the count, so
    message-id offsets stay fixed at `ETH_OFFSET`.
    """
    remote_versions = {
        version for name, version in remote_capabilities if name == "eth"
    }
    common = [
        version for version in local_versions if version in remote_versions
    ]
    return max(common) if common else None


def decode_hello(
    payload: bytes,
) -> Tuple[int, str, List[Tuple[str, int]]]:
    """
    Return the remote base protocol version, client identifier and
    capabilities.
    """
    try:
        fields = eth_rlp.decode(payload)
    except DecodingError as error:
        raise ProtocolError("malformed Hello message") from error
    # EIP-8: elements past the ones read here are ignored, so the list is
    # checked field by field rather than decoded to an exact shape.
    if not isinstance(fields, list) or len(fields) < 3:
        raise ProtocolError("malformed Hello message")
    version, name, advertised = fields[0], fields[1], fields[2]
    if (
        not isinstance(version, bytes)
        or not isinstance(name, bytes)
        or not isinstance(advertised, list)
    ):
        raise ProtocolError("malformed Hello message")
    capabilities = []
    for capability in advertised:
        if (
            not isinstance(capability, list)
            or len(capability) < 2
            or not isinstance(capability[0], bytes)
            or not isinstance(capability[1], bytes)
        ):
            raise ProtocolError("malformed Hello capability")
        capabilities.append(
            (
                capability[0].decode(errors="replace"),
                int.from_bytes(capability[1], "big"),
            )
        )
    return (
        int.from_bytes(version, "big"),
        name.decode(errors="replace"),
        capabilities,
    )


def decode_disconnect(payload: bytes) -> int | None:
    """
    Return the reason code of a Disconnect message.

    `None` means the message carries no reason (an empty list).
    """
    fields = eth_rlp.decode(payload)
    if isinstance(fields, bytes):
        return int.from_bytes(fields, "big")
    if isinstance(fields, list) and fields:
        return int.from_bytes(bytes(fields[0]), "big")
    return None


@dataclass
class Status:
    """The content of the eth capability handshake message."""

    network_id: int
    genesis_hash: Hash
    fork_id: ForkId
    earliest_block: int
    latest_block: int
    latest_block_hash: Hash


@dataclass
class GetReceiptsRequest:
    """A decoded GetReceipts request."""

    request_id: int
    block_hashes: List[Hash]
    first_block_receipt_index: int | None
    """
    Receipt offset into the first block, letting a response continue a
    block whose receipt list exceeded one message. Added by eth/70
    (EIP-7975); `None` on eth/69.
    """

    def describe(self) -> str:
        """Return a one line description for the request transcript."""
        offset = (
            ""
            if self.first_block_receipt_index is None
            else f" from receipt {self.first_block_receipt_index}"
        )
        return f"receipts for {len(self.block_hashes)} hashes{offset}"


@dataclass(frozen=True)
class EthProtocol:
    """
    One implemented version of the eth capability.

    It holds only what differs between versions; everything version
    independent stays at module level.
    """

    version: EthVersion

    receipts_request_has_offset: bool
    """Whether GetReceipts carries the eth/70 receipt offset."""

    has_bals: bool
    """Whether the version has GetBlockAccessLists (eth/71, EIP-8159)."""

    def encode_status(self, status: Status) -> bytes:
        """Encode the Status message (one eth/69 layout for every version)."""
        return eth_rlp.encode(
            [
                Uint(self.version),
                Uint(status.network_id),
                status.genesis_hash,
                status.fork_id,
                Uint(status.earliest_block),
                Uint(status.latest_block),
                status.latest_block_hash,
            ]
        )

    def decode_get_receipts(self, payload: bytes) -> GetReceiptsRequest:
        """Decode a GetReceipts request as this version shapes it."""
        message = f"malformed GetReceipts message for eth/{self.version}"
        if self.receipts_request_has_offset:
            with_offset = _decode_shaped(
                _OffsetHashListRequest, payload, message
            )
            return GetReceiptsRequest(
                request_id=int(with_offset.request_id),
                block_hashes=list(with_offset.hashes),
                first_block_receipt_index=int(
                    with_offset.first_block_receipt_index
                ),
            )
        request = _decode_shaped(_HashListRequest, payload, message)
        return GetReceiptsRequest(
            request_id=int(request.request_id),
            block_hashes=list(request.hashes),
            first_block_receipt_index=None,
        )

    def encode_no_receipts(self, request_id: int) -> bytes:
        """
        Encode a Receipts response that holds no receipts.

        An empty list is how a peer says it holds none of the requested
        blocks' receipts. From eth/70 the response also carries the
        `lastBlockIncomplete` flag, which is 0 for an empty list.
        """
        if self.receipts_request_has_offset:
            return eth_rlp.encode([Uint(request_id), Uint(0), []])
        return eth_rlp.encode([Uint(request_id), []])


ETH_PROTOCOLS: Mapping[EthVersion, EthProtocol] = {
    EthVersion.ETH_69: EthProtocol(
        version=EthVersion.ETH_69,
        receipts_request_has_offset=False,
        has_bals=False,
    ),
    EthVersion.ETH_70: EthProtocol(
        version=EthVersion.ETH_70,
        receipts_request_has_offset=True,
        has_bals=False,
    ),
    EthVersion.ETH_71: EthProtocol(
        version=EthVersion.ETH_71,
        receipts_request_has_offset=True,
        has_bals=True,
    ),
    EthVersion.ETH_72: EthProtocol(
        version=EthVersion.ETH_72,
        receipts_request_has_offset=True,
        has_bals=True,
    ),
}
"""
Every eth capability version this peer implements, by version number.

eth/70 (EIP-7975) changes only the receipts messages, which this peer
answers with no receipts. eth/71 (EIP-8159) adds the BAL request pair (see
`MockPeer._answer_bals`). eth/72 (EIP-8070) changes only mempool blob
propagation, which this peer takes no part in.
"""


def encode_block_range_update(
    earliest_block: int, latest_block: int, latest_block_hash: Hash
) -> bytes:
    """Encode the range of blocks whose bodies this peer can serve."""
    return eth_rlp.encode(
        [Uint(earliest_block), Uint(latest_block), latest_block_hash]
    )


@dataclass
class BlockHeadersRequest:
    """A decoded GetBlockHeaders request."""

    request_id: int
    origin_hash: Hash | None
    origin_number: int | None
    amount: int
    skip: int
    reverse: bool

    def describe(self) -> str:
        """Return a one line description for the request transcript."""
        origin = (
            f"#{self.origin_number}"
            if self.origin_hash is None
            else self.origin_hash.hex()[:14]
        )
        direction = "reverse" if self.reverse else "forward"
        return (
            f"headers from {origin} amount={self.amount} "
            f"skip={self.skip} {direction}"
        )


def decode_get_block_headers(payload: bytes) -> BlockHeadersRequest:
    """Decode a GetBlockHeaders request."""
    # Not decoded to an exact shape: the origin is a hash or a number,
    # which only its length tells apart.
    try:
        fields = eth_rlp.decode(payload)
    except DecodingError as error:
        raise ProtocolError("malformed GetBlockHeaders message") from error
    if (
        not isinstance(fields, list)
        or len(fields) != 2
        or not isinstance(fields[0], bytes)
        or fields[0][:1] == b"\x00"
    ):
        raise ProtocolError("malformed GetBlockHeaders message")
    request_id, query = fields
    if (
        not isinstance(query, list)
        or len(query) != 4
        or not all(isinstance(field, bytes) for field in query)
    ):
        raise ProtocolError("malformed GetBlockHeaders query")

    origin, amount, skip, reverse = query
    by_hash = len(origin) == 32
    # Integers are canonical (no leading zero) and `reverse` is 0 or 1,
    # as geth's decoder requires. A hash may start with a zero byte.
    if (
        (not by_hash and origin[:1] == b"\x00")
        or amount[:1] == b"\x00"
        or skip[:1] == b"\x00"
        or (reverse != b"" and reverse != b"\x01")
    ):
        raise ProtocolError("malformed GetBlockHeaders query")
    return BlockHeadersRequest(
        request_id=int.from_bytes(request_id, "big"),
        origin_hash=Hash(origin) if by_hash else None,
        origin_number=None if by_hash else int.from_bytes(origin, "big"),
        amount=int.from_bytes(amount, "big"),
        skip=int.from_bytes(skip, "big"),
        reverse=reverse == b"\x01",
    )


def _decode_hash_list_request(
    payload: bytes, name: str
) -> Tuple[int, List[Hash]]:
    """
    Decode a `[request-id, [hash, ...]]` shaped request.

    Decoded by hand, not with `decode_to`, because `decode_to` resolves
    type hints on every call and this runs for every body and BAL
    request.
    """
    message = f"malformed {name} message"
    try:
        decoded = eth_rlp.decode(payload)
    except DecodingError as error:
        raise ProtocolError(message) from error
    if not isinstance(decoded, (list, tuple)) or len(decoded) != 2:
        raise ProtocolError(message)
    request_id, hashes = decoded
    if not isinstance(request_id, bytes) or request_id[:1] == b"\x00":
        raise ProtocolError(message)
    if not isinstance(hashes, (list, tuple)):
        raise ProtocolError(message)
    block_hashes = []
    for block_hash in hashes:
        if not isinstance(block_hash, bytes) or len(block_hash) != 32:
            raise ProtocolError(message)
        block_hashes.append(Hash(block_hash))
    return int.from_bytes(request_id, "big"), block_hashes


def decode_get_block_bodies(payload: bytes) -> Tuple[int, List[Hash]]:
    """Decode a GetBlockBodies request into its identifier and hashes."""
    return _decode_hash_list_request(payload, "GetBlockBodies")


def decode_get_block_access_lists(payload: bytes) -> Tuple[int, List[Hash]]:
    """Decode a GetBlockAccessLists request (eth/71)."""
    return _decode_hash_list_request(payload, "GetBlockAccessLists")


def encode_response(request_id: int, encoded_items: Sequence[bytes]) -> bytes:
    """Encode a request identifier and a list of pre-encoded items."""
    return encode_list(
        [eth_rlp.encode(Uint(request_id)), encode_list(encoded_items)]
    )
