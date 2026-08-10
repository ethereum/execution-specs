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
from typing import List, Sequence, Tuple

import ethereum_rlp as eth_rlp
from ethereum_types.numeric import Uint

P2P_VERSION = 4
"""
Base protocol version advertised to the remote node.

Version 5 enables Snappy compression of every frame. Advertising 4 keeps
the connection uncompressed, which current clients honour because they
select compression from the version their peer announces.
"""

ETH_VERSION = 69
"""The eth capability version this peer implements."""

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
    client_id: str, public_key: bytes, listen_port: int = 0
) -> bytes:
    """Encode the base protocol Hello message."""
    return eth_rlp.encode(
        [
            Uint(P2P_VERSION),
            client_id.encode(),
            [[b"eth", Uint(ETH_VERSION)]],
            Uint(listen_port),
            public_key,
        ]
    )


def decode_hello(payload: bytes) -> Tuple[str, List[Tuple[str, int]]]:
    """Return the remote client identifier and its capabilities."""
    fields = eth_rlp.decode(payload)
    if not isinstance(fields, list) or len(fields) < 3:
        raise ProtocolError("malformed Hello message")
    name = bytes(fields[1]).decode(errors="replace")
    capabilities = []
    for capability in fields[2]:
        capabilities.append(
            (
                bytes(capability[0]).decode(errors="replace"),
                int.from_bytes(bytes(capability[1]), "big"),
            )
        )
    return name, capabilities


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
    """The eth capability handshake message, as of eth/69."""

    network_id: int
    genesis_hash: bytes
    fork_activations: Sequence[int]
    earliest_block: int
    latest_block: int
    latest_block_hash: bytes

    def encode(self) -> bytes:
        """Encode the Status message."""
        return eth_rlp.encode(
            [
                Uint(ETH_VERSION),
                Uint(self.network_id),
                self.genesis_hash,
                fork_id(self.genesis_hash, self.fork_activations),
                Uint(self.earliest_block),
                Uint(self.latest_block),
                self.latest_block_hash,
            ]
        )


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


def decode_get_block_bodies(payload: bytes) -> Tuple[int, List[bytes]]:
    """Decode a GetBlockBodies request into its identifier and hashes."""
    fields = eth_rlp.decode(payload)
    if not isinstance(fields, list) or len(fields) != 2:
        raise ProtocolError("malformed GetBlockBodies message")
    request_id = int.from_bytes(bytes(fields[0]), "big")
    hashes = [bytes(item) for item in fields[1]]
    return request_id, hashes


def encode_response(request_id: int, encoded_items: Sequence[bytes]) -> bytes:
    """Encode a request identifier and a list of pre-encoded items."""
    return encode_list(
        [eth_rlp.encode(Uint(request_id)), encode_list(encoded_items)]
    )
