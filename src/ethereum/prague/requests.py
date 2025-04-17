"""
Requests were introduced in EIP-7685 as a a general purpose framework for
storing contract-triggered requests. It extends the execution header and
body with a single field each to store the request information.
This inherently exposes the requests to the consensus layer, which can
then process each one.

[EIP-7685]: https://eips.ethereum.org/EIPS/eip-7685
"""

from hashlib import sha256
from typing import List, Tuple, Union

from ethereum_types.bytes import Bytes
from ethereum_types.numeric import Uint, ulen

from ethereum.exceptions import InvalidBlock
from ethereum.utils.hexadecimal import hex_to_bytes32

from .blocks import Receipt, decode_receipt
from .utils.hexadecimal import hex_to_address

DEPOSIT_CONTRACT_ADDRESS = hex_to_address(
    "0x00000000219ab540356cbb839cbe05303d7705fa"
)
DEPOSIT_EVENT_SIGNATURE_HASH = hex_to_bytes32(
    "0x649bbc62d0e31342afea4e5cd82d4049e7e1ee912fc0889aa790803be39038c5"
)
DEPOSIT_REQUEST_TYPE = b"\x00"
WITHDRAWAL_REQUEST_TYPE = b"\x01"
CONSOLIDATION_REQUEST_TYPE = b"\x02"


DEPOSIT_EVENT_LENGTH = Uint(576)

PUBKEY_OFFSET = Uint(160)
WITHDRAWAL_CREDENTIALS_OFFSET = Uint(256)
AMOUNT_OFFSET = Uint(320)
SIGNATURE_OFFSET = Uint(384)
INDEX_OFFSET = Uint(512)

PUBKEY_SIZE = Uint(48)
WITHDRAWAL_CREDENTIALS_SIZE = Uint(32)
AMOUNT_SIZE = Uint(8)
SIGNATURE_SIZE = Uint(96)
INDEX_SIZE = Uint(8)


def extract_deposit_data(data: Bytes) -> Bytes:
    """
    Extracts Deposit Request from the DepositContract.DepositEvent data.

    Raises
    ------
    InvalidBlock :
        If the deposit contract did not produce a valid log.
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
        signature_offset
        + Uint(32) : signature_offset
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


def parse_deposit_requests_from_receipts(
    receipts: Tuple[Union[Bytes, Receipt], ...],
) -> Bytes:
    """
    Parse deposit requests from a receipt.
    """
    deposit_requests: Bytes = b""
    for receipt in receipts:
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
    Get the hash of the requests using the SHA2-256 algorithm.

    Parameters
    ----------
    requests : Bytes
        The requests to hash.

    Returns
    -------
    requests_hash : Bytes
        The hash of the requests.
    """
    m = sha256()
    for request in requests:
        m.update(sha256(request).digest())

    return m.digest()
