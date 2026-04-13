"""
[EIP-7685] generalizes how the execution layer communicates validator actions
to the consensus layer. Rather than adding a dedicated header field for each
new action type (as [EIP-4895] did for withdrawals), the execution header
commits to a single [`requests_hash`][rh] that aggregates an ordered list of
typed requests.

Each request is a type byte (see [`DEPOSIT_REQUEST_TYPE`][dt],
[`WITHDRAWAL_REQUEST_TYPE`][wt], and [`CONSOLIDATION_REQUEST_TYPE`][ct])
followed by an opaque payload. Deposit requests are discovered by scanning
transaction receipts for logs emitted by the deposit contract; withdrawal
and consolidation requests are produced by the corresponding system
contracts during block processing.

See [`parse_deposit_requests`][pd] for how deposit logs become request data,
[`compute_requests_hash`][crh] for how the list is hashed for inclusion in the
header, and [`process_general_purpose_requests`][pgpr] for how the requests are
processed.

[EIP-4895]: https://eips.ethereum.org/EIPS/eip-4895
[EIP-7685]: https://eips.ethereum.org/EIPS/eip-7685
[rh]: ref:ethereum.forks.bpo2.blocks.Header.requests_hash
[dt]: ref:ethereum.forks.bpo2.requests.DEPOSIT_REQUEST_TYPE
[wt]: ref:ethereum.forks.bpo2.requests.WITHDRAWAL_REQUEST_TYPE
[ct]: ref:ethereum.forks.bpo2.requests.CONSOLIDATION_REQUEST_TYPE
[pd]: ref:ethereum.forks.bpo2.requests.parse_deposit_requests
[crh]: ref:ethereum.forks.bpo2.requests.compute_requests_hash
[pgpr]: ref:ethereum.forks.bpo2.fork.process_general_purpose_requests
"""

from hashlib import sha256
from typing import List

from ethereum_types.bytes import Bytes
from ethereum_types.numeric import Uint, ulen

from ethereum.exceptions import InvalidBlock
from ethereum.utils.hexadecimal import hex_to_bytes32

from .blocks import decode_receipt
from .trie import trie_get
from .utils.hexadecimal import hex_to_address
from .vm import BlockOutput

DEPOSIT_CONTRACT_ADDRESS = hex_to_address(
    "0x00000000219ab540356cbb839cbe05303d7705fa"
)
"""
Mainnet address of the beacon chain deposit contract. Scanning block
receipts for logs emitted by this address is how the execution layer
discovers validator deposits, per [EIP-6110].

[EIP-6110]: https://eips.ethereum.org/EIPS/eip-6110
"""

DEPOSIT_EVENT_SIGNATURE_HASH = hex_to_bytes32(
    "0x649bbc62d0e31342afea4e5cd82d4049e7e1ee912fc0889aa790803be39038c5"
)
"""
First [log topic] of the deposit contract's `DepositEvent`, equal to the
keccak256 of its Solidity event signature. Logs whose first topic does not
match this are ignored when collecting deposit requests.

[log topic]: https://docs.soliditylang.org/en/latest/abi-spec.html#events
"""

DEPOSIT_REQUEST_TYPE = b"\x00"
"""
Request type byte identifying a deposit request, per [EIP-6110].

[EIP-6110]: https://eips.ethereum.org/EIPS/eip-6110
"""

WITHDRAWAL_REQUEST_TYPE = b"\x01"
"""
Request type byte identifying an execution-triggered withdrawal request,
per [EIP-7002].

[EIP-7002]: https://eips.ethereum.org/EIPS/eip-7002
"""

CONSOLIDATION_REQUEST_TYPE = b"\x02"
"""
Request type byte identifying a consolidation request, per [EIP-7251].

[EIP-7251]: https://eips.ethereum.org/EIPS/eip-7251
"""


DEPOSIT_EVENT_LENGTH = Uint(576)
"""
Total length in bytes of the ABI-encoded `DepositEvent` data payload. Every
well-formed event has this exact length.
"""

PUBKEY_OFFSET = Uint(160)
"""
Position within the event payload of the validator public key's length
prefix, as emitted by the Solidity ABI encoder.
"""

WITHDRAWAL_CREDENTIALS_OFFSET = Uint(256)
"""
Position within the event payload of the withdrawal credentials' length
prefix.
"""

AMOUNT_OFFSET = Uint(320)
"""
Position within the event payload of the deposit amount's length prefix.
"""

SIGNATURE_OFFSET = Uint(384)
"""
Position within the event payload of the deposit signature's length prefix.
"""

INDEX_OFFSET = Uint(512)
"""
Position within the event payload of the deposit index's length prefix.
"""

PUBKEY_SIZE = Uint(48)
"""
Length of the BLS12-381 public key that identifies the validator receiving
the deposit.
"""

WITHDRAWAL_CREDENTIALS_SIZE = Uint(32)
"""
Length of the withdrawal credentials, which determine where the staked
ether may eventually be withdrawn.
"""

AMOUNT_SIZE = Uint(8)
"""
Length of the little-endian Gwei amount being deposited.
"""

SIGNATURE_SIZE = Uint(96)
"""
Length of the BLS12-381 signature over the deposit message.
"""

INDEX_SIZE = Uint(8)
"""
Length of the monotonically-increasing deposit index assigned by the
deposit contract when it emits the event.
"""


def extract_deposit_data(data: Bytes) -> Bytes:
    """
    Strip the Solidity ABI framing from a `DepositEvent` payload and return
    the concatenated raw fields in the order consumed by the consensus
    layer: public key, withdrawal credentials, amount, signature, and
    deposit index.

    Because each field has a fixed length, every well-formed event has an
    identical byte layout. Any deviation indicates a misbehaving or
    compromised deposit contract, so this function raises [`InvalidBlock`]
    rather than silently accepting unexpected data.

    [`InvalidBlock`]: ref:ethereum.exceptions.InvalidBlock
    """
    if ulen(data) != DEPOSIT_EVENT_LENGTH:
        raise InvalidBlock("Invalid deposit event data length")

    # Check that all the offsets are in order
    pubkey_offset = Uint.from_be_bytes(data[0:32])
    if pubkey_offset != PUBKEY_OFFSET:
        raise InvalidBlock("Invalid pubkey offset in deposit log")

    withdrawal_credentials_offset = Uint.from_be_bytes(data[32:64])
    if withdrawal_credentials_offset != WITHDRAWAL_CREDENTIALS_OFFSET:
        raise InvalidBlock(
            "Invalid withdrawal credentials offset in deposit log"
        )

    amount_offset = Uint.from_be_bytes(data[64:96])
    if amount_offset != AMOUNT_OFFSET:
        raise InvalidBlock("Invalid amount offset in deposit log")

    signature_offset = Uint.from_be_bytes(data[96:128])
    if signature_offset != SIGNATURE_OFFSET:
        raise InvalidBlock("Invalid signature offset in deposit log")

    index_offset = Uint.from_be_bytes(data[128:160])
    if index_offset != INDEX_OFFSET:
        raise InvalidBlock("Invalid index offset in deposit log")

    # Check that all the sizes are in order
    pubkey_size = Uint.from_be_bytes(
        data[pubkey_offset : pubkey_offset + Uint(32)]
    )
    if pubkey_size != PUBKEY_SIZE:
        raise InvalidBlock("Invalid pubkey size in deposit log")

    pubkey = data[
        pubkey_offset + Uint(32) : pubkey_offset + Uint(32) + PUBKEY_SIZE
    ]

    withdrawal_credentials_size = Uint.from_be_bytes(
        data[
            withdrawal_credentials_offset : withdrawal_credentials_offset
            + Uint(32)
        ],
    )
    if withdrawal_credentials_size != WITHDRAWAL_CREDENTIALS_SIZE:
        raise InvalidBlock(
            "Invalid withdrawal credentials size in deposit log"
        )

    withdrawal_credentials = data[
        withdrawal_credentials_offset
        + Uint(32) : withdrawal_credentials_offset
        + Uint(32)
        + WITHDRAWAL_CREDENTIALS_SIZE
    ]

    amount_size = Uint.from_be_bytes(
        data[amount_offset : amount_offset + Uint(32)]
    )
    if amount_size != AMOUNT_SIZE:
        raise InvalidBlock("Invalid amount size in deposit log")

    amount = data[
        amount_offset + Uint(32) : amount_offset + Uint(32) + AMOUNT_SIZE
    ]

    signature_size = Uint.from_be_bytes(
        data[signature_offset : signature_offset + Uint(32)]
    )
    if signature_size != SIGNATURE_SIZE:
        raise InvalidBlock("Invalid signature size in deposit log")

    signature = data[
        signature_offset + Uint(32) : signature_offset
        + Uint(32)
        + SIGNATURE_SIZE
    ]

    index_size = Uint.from_be_bytes(
        data[index_offset : index_offset + Uint(32)]
    )
    if index_size != INDEX_SIZE:
        raise InvalidBlock("Invalid index size in deposit log")

    index = data[
        index_offset + Uint(32) : index_offset + Uint(32) + INDEX_SIZE
    ]

    return pubkey + withdrawal_credentials + amount + signature + index


def parse_deposit_requests(block_output: BlockOutput) -> Bytes:
    """
    Walk the receipts produced during block execution, concatenating the
    raw payload of every valid deposit event into a single byte string.

    A log is considered a deposit when it originates from
    [`DEPOSIT_CONTRACT_ADDRESS`][addr] and its first topic matches
    [`DEPOSIT_EVENT_SIGNATURE_HASH`][sig]. The returned bytes are the
    direct concatenation of the unframed deposit fields, ready to be
    prefixed with [`DEPOSIT_REQUEST_TYPE`][dt] before being appended to
    the block's request list.

    [addr]: ref:ethereum.forks.bpo2.requests.DEPOSIT_CONTRACT_ADDRESS
    [sig]: ref:ethereum.forks.bpo2.requests.DEPOSIT_EVENT_SIGNATURE_HASH
    [dt]: ref:ethereum.forks.bpo2.requests.DEPOSIT_REQUEST_TYPE
    """
    deposit_requests: Bytes = b""
    for key in block_output.receipt_keys:
        receipt = trie_get(block_output.receipts_trie, key)
        assert receipt is not None
        decoded_receipt = decode_receipt(receipt)
        for log in decoded_receipt.logs:
            if log.address == DEPOSIT_CONTRACT_ADDRESS:
                if (
                    len(log.topics) > 0
                    and log.topics[0] == DEPOSIT_EVENT_SIGNATURE_HASH
                ):
                    request = extract_deposit_data(log.data)
                    deposit_requests += request

    return deposit_requests


def compute_requests_hash(requests: List[Bytes]) -> Bytes:
    """
    Compute the [SHA2-256] commitment over an ordered list of
    type-prefixed requests, as defined by [EIP-7685].

    The commitment is the SHA2-256 hash of the concatenation of the
    SHA2-256 hashes of each individual request. This is what the
    execution header's [`requests_hash`][rh] stores, and what the
    consensus layer re-derives to validate that both layers observed the
    same set of requests.

    [EIP-7685]: https://eips.ethereum.org/EIPS/eip-7685
    [SHA2-256]: https://en.wikipedia.org/wiki/SHA-2
    [rh]: ref:ethereum.forks.bpo2.blocks.Header.requests_hash
    """
    m = sha256()
    for request in requests:
        m.update(sha256(request).digest())

    return m.digest()
