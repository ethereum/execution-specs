"""
Message encoding for the devp2p base protocol and the eth capability.

Only the subset a full syncing client asks of a serving peer is
implemented: the base protocol handshake and liveness messages, the eth
status exchange, and the header, body and range messages that carry
chain data. Announcement and transaction pool messages are decoded far
enough to be recognized and ignored.
"""

import zlib
from dataclasses import dataclass
from typing import Dict, List, Mapping, Sequence, Tuple

import ethereum_rlp as eth_rlp
from ethereum_types.numeric import Uint

P2P_VERSION = 5
"""
Base protocol version advertised to the remote node.

Version 5 enables Snappy compression of every message payload after the
Hello exchange. Compression is negotiated: it is only used when both
sides advertise version 5 or higher, so a version 4 remote still gets
an uncompressed connection.
"""

ETH_OFFSET = 16
"""Message code offset of the first capability after the base protocol."""

# Base protocol message codes.
HELLO = 0x00
DISCONNECT = 0x01
PING = 0x02
PONG = 0x03

# eth capability message codes, already offset onto the wire.
STATUS = ETH_OFFSET + 0x00
TRANSACTIONS = ETH_OFFSET + 0x02
GET_BLOCK_HEADERS = ETH_OFFSET + 0x03
BLOCK_HEADERS = ETH_OFFSET + 0x04
GET_BLOCK_BODIES = ETH_OFFSET + 0x05
BLOCK_BODIES = ETH_OFFSET + 0x06
NEW_POOLED_TRANSACTION_HASHES = ETH_OFFSET + 0x08
GET_POOLED_TRANSACTIONS = ETH_OFFSET + 0x09
GET_RECEIPTS = ETH_OFFSET + 0x0F
RECEIPTS = ETH_OFFSET + 0x10
BLOCK_RANGE_UPDATE = ETH_OFFSET + 0x11
GET_BLOCK_ACCESS_LISTS = ETH_OFFSET + 0x12
BLOCK_ACCESS_LISTS = ETH_OFFSET + 0x13

MESSAGE_NAMES = {
    HELLO: "Hello",
    DISCONNECT: "Disconnect",
    PING: "Ping",
    PONG: "Pong",
    STATUS: "Status",
    TRANSACTIONS: "Transactions",
    GET_BLOCK_HEADERS: "GetBlockHeaders",
    BLOCK_HEADERS: "BlockHeaders",
    GET_BLOCK_BODIES: "GetBlockBodies",
    BLOCK_BODIES: "BlockBodies",
    NEW_POOLED_TRANSACTION_HASHES: "NewPooledTransactionHashes",
    GET_POOLED_TRANSACTIONS: "GetPooledTransactions",
    GET_RECEIPTS: "GetReceipts",
    RECEIPTS: "Receipts",
    BLOCK_RANGE_UPDATE: "BlockRangeUpdate",
    GET_BLOCK_ACCESS_LISTS: "GetBlockAccessLists",
    BLOCK_ACCESS_LISTS: "BlockAccessLists",
}
"""Human readable names used in the peer's request transcript."""


class ProtocolError(Exception):
    """Raised when a peer message cannot be decoded as expected."""


def encode_list(encoded_items: Sequence[bytes]) -> bytes:
    """
    Wrap already encoded RLP `encoded_items` in a list header.

    Chain data arrives pre-encoded: a fixture header knows its own RLP,
    and a legacy transaction is carried as the RLP list it already is.
    Re-encoding those through a generic encoder would nest them one level
    too deep, so lists of raw items are assembled here instead.
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


def fork_id(genesis_hash: bytes, fork_activations: Sequence[int]) -> List:
    """
    Return the EIP-2124 fork identifier `[fork-hash, fork-next]`.

    `fork_activations` holds the block numbers and timestamps at which
    forks activate after genesis, in order. Activations at genesis are
    part of the genesis rule set and must already be excluded.
    """
    checksum = zlib.crc32(genesis_hash)
    for activation in fork_activations:
        checksum = zlib.crc32(activation.to_bytes(8, "big"), checksum)
    return [checksum.to_bytes(4, "big"), Uint(0)]


def encode_hello(
    client_id: str,
    public_key: bytes,
    eth_versions: Sequence[int],
    listen_port: int = 0,
) -> bytes:
    """
    Encode the base protocol Hello message.

    One `("eth", version)` pair is advertised per entry of
    `eth_versions`, in ascending order. The remote applies the RLPx
    rule to the advertised set: the shared capability with the highest
    version wins.
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
    local_versions: Sequence[int],
    remote_capabilities: Sequence[Tuple[str, int]],
) -> int | None:
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
    common = remote_versions.intersection(local_versions)
    return max(common) if common else None


def decode_hello(
    payload: bytes,
) -> Tuple[int, str, List[Tuple[str, int]]]:
    """
    Return the remote base protocol version, client identifier and
    capabilities.
    """
    fields = eth_rlp.decode(payload)
    if not isinstance(fields, list) or len(fields) < 3:
        raise ProtocolError("malformed Hello message")
    version = int.from_bytes(bytes(fields[0]), "big")
    name = bytes(fields[1]).decode(errors="replace")
    capabilities = []
    for capability in fields[2]:
        capabilities.append(
            (
                bytes(capability[0]).decode(errors="replace"),
                int.from_bytes(bytes(capability[1]), "big"),
            )
        )
    return version, name, capabilities


def decode_disconnect(payload: bytes) -> int:
    """Return the reason code of a Disconnect message."""
    fields = eth_rlp.decode(payload)
    if isinstance(fields, bytes):
        return int.from_bytes(fields, "big")
    if isinstance(fields, list) and fields:
        return int.from_bytes(bytes(fields[0]), "big")
    return -1


@dataclass
class Status:
    """The content of the eth capability handshake message."""

    network_id: int
    genesis_hash: bytes
    fork_activations: Sequence[int]
    earliest_block: int
    latest_block: int
    latest_block_hash: bytes


@dataclass
class GetReceiptsRequest:
    """A decoded GetReceipts request."""

    request_id: int
    block_hashes: List[bytes]
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

    A protocol object owns exactly the things versions change: the
    version number, the codecs whose wire shape differs between
    versions, and the set of requests this peer deliberately leaves
    unanswered. Everything version independent - RLP helpers, the fork
    id, the header and body request codecs, which have been stable
    since eth/66 - stays at module level.
    """

    version: int

    receipts_request_has_offset: bool
    """
    Whether GetReceipts carries `firstBlockReceiptIndex` between the
    request id and the block hashes. Added by eth/70 (EIP-7975) so a
    receipts response can be resumed mid-block.
    """

    unanswered_requests: Mapping[int, str]
    """
    Wire code to message name of every request this peer deliberately
    never answers. Receipts, and from eth/71 block access lists, are
    data a client could import instead of deriving by execution;
    serving either would let a failing test pass with no coverage, so
    the silence is a recorded decision per message type rather than an
    omission.
    """

    def encode_status(self, status: Status) -> bytes:
        """
        Encode the Status message.

        The layout was set by eth/69 (EIP-7642) and is unchanged
        through eth/72 - the later versions' deltas live in other
        messages - so all implemented versions share this codec and
        differ only in the version they declare.
        """
        return eth_rlp.encode(
            [
                Uint(self.version),
                Uint(status.network_id),
                status.genesis_hash,
                fork_id(status.genesis_hash, status.fork_activations),
                Uint(status.earliest_block),
                Uint(status.latest_block),
                status.latest_block_hash,
            ]
        )

    def decode_get_receipts(self, payload: bytes) -> GetReceiptsRequest:
        """Decode a GetReceipts request as this version shapes it."""
        fields = eth_rlp.decode(payload)
        expected = 3 if self.receipts_request_has_offset else 2
        if not isinstance(fields, list) or len(fields) != expected:
            raise ProtocolError(
                f"malformed GetReceipts message for eth/{self.version}"
            )
        request_id = int.from_bytes(bytes(fields[0]), "big")
        if self.receipts_request_has_offset:
            first_index = int.from_bytes(bytes(fields[1]), "big")
            hashes = fields[2]
        else:
            first_index = None
            hashes = fields[1]
        return GetReceiptsRequest(
            request_id=request_id,
            block_hashes=[bytes(item) for item in hashes],
            first_block_receipt_index=first_index,
        )


ETH_PROTOCOLS: Dict[int, EthProtocol] = {
    69: EthProtocol(
        version=69,
        receipts_request_has_offset=False,
        unanswered_requests={GET_RECEIPTS: "GetReceipts"},
    ),
    70: EthProtocol(
        version=70,
        receipts_request_has_offset=True,
        unanswered_requests={GET_RECEIPTS: "GetReceipts"},
    ),
    71: EthProtocol(
        version=71,
        receipts_request_has_offset=True,
        unanswered_requests={
            GET_RECEIPTS: "GetReceipts",
            GET_BLOCK_ACCESS_LISTS: "GetBlockAccessLists",
        },
    ),
}
"""
Every eth capability version this peer implements, by version number.

eth/70 (EIP-7975) changes only the receipts pair, which this peer never
serves, so implementing it means decoding the new request shape. eth/71
(EIP-8159) adds the block access list request pair; a block access list
carries post-state values a client could import instead of executing,
so the receipts rule generalizes and the requests are counted but never
answered.
"""


def encode_block_range_update(
    earliest_block: int, latest_block: int, latest_block_hash: bytes
) -> bytes:
    """Encode the range of blocks whose bodies this peer can serve."""
    return eth_rlp.encode(
        [Uint(earliest_block), Uint(latest_block), latest_block_hash]
    )


@dataclass
class BlockHeadersRequest:
    """A decoded GetBlockHeaders request."""

    request_id: int
    origin_hash: bytes | None
    origin_number: int | None
    amount: int
    skip: int
    reverse: bool

    def describe(self) -> str:
        """Return a one line description for the request transcript."""
        origin = (
            f"#{self.origin_number}"
            if self.origin_hash is None
            else f"0x{self.origin_hash.hex()[:12]}"
        )
        direction = "reverse" if self.reverse else "forward"
        return (
            f"headers from {origin} amount={self.amount} "
            f"skip={self.skip} {direction}"
        )


def decode_get_block_headers(payload: bytes) -> BlockHeadersRequest:
    """Decode a GetBlockHeaders request."""
    fields = eth_rlp.decode(payload)
    if not isinstance(fields, list) or len(fields) != 2:
        raise ProtocolError("malformed GetBlockHeaders message")
    request_id = int.from_bytes(bytes(fields[0]), "big")
    query = fields[1]
    if not isinstance(query, list) or len(query) != 4:
        raise ProtocolError("malformed GetBlockHeaders query")

    origin = bytes(query[0])
    return BlockHeadersRequest(
        request_id=request_id,
        origin_hash=origin if len(origin) == 32 else None,
        origin_number=(
            None if len(origin) == 32 else int.from_bytes(origin, "big")
        ),
        amount=int.from_bytes(bytes(query[1]), "big"),
        skip=int.from_bytes(bytes(query[2]), "big"),
        reverse=bool(int.from_bytes(bytes(query[3]), "big")),
    )


def _decode_hash_list_request(
    payload: bytes, name: str
) -> Tuple[int, List[bytes]]:
    """Decode a `[request-id, [hash, ...]]` shaped request."""
    fields = eth_rlp.decode(payload)
    if not isinstance(fields, list) or len(fields) != 2:
        raise ProtocolError(f"malformed {name} message")
    request_id = int.from_bytes(bytes(fields[0]), "big")
    hashes = [bytes(item) for item in fields[1]]
    return request_id, hashes


def decode_get_block_bodies(payload: bytes) -> Tuple[int, List[bytes]]:
    """Decode a GetBlockBodies request into its identifier and hashes."""
    return _decode_hash_list_request(payload, "GetBlockBodies")


def decode_get_block_access_lists(payload: bytes) -> Tuple[int, List[bytes]]:
    """
    Decode a GetBlockAccessLists request (eth/71, EIP-8159) into its
    identifier and block hashes.
    """
    return _decode_hash_list_request(payload, "GetBlockAccessLists")


def encode_response(request_id: int, encoded_items: Sequence[bytes]) -> bytes:
    """Encode a request identifier and a list of pre-encoded items."""
    return encode_list(
        [eth_rlp.encode(Uint(request_id)), encode_list(encoded_items)]
    )
