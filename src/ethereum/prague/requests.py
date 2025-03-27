"""
Requests were introduced in EIP-7685 as a a general purpose framework for
storing contract-triggered requests. It extends the execution header and
body with a single field each to store the request information.
This inherently exposes the requests to the consensus layer, which can
then process each one.

[EIP-7685]: https://eips.ethereum.org/EIPS/eip-7685
"""

from hashlib import sha256
from typing import List, Union

from ethereum_types.bytes import Bytes

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


DEPOSIT_EVENT_LENGTH = 576

PUBKEY_OFFSET = 160
WITHDRAWAL_CREDENTIALS_OFFSET = 256
AMOUNT_OFFSET = 320
SIGNATURE_OFFSET = 384
INDEX_OFFSET = 512

PUBKEY_SIZE = 48
WITHDRAWAL_CREDENTIALS_SIZE = 32
AMOUNT_SIZE = 8
SIGNATURE_SIZE = 96
INDEX_SIZE = 8


def extract_deposit_data(data: Bytes) -> Bytes:
    """
    Extracts Deposit Request from the DepositContract.DepositEvent data.

    Raises
    ------
    InvalidBlock :
        If the deposit contract did not produce a valid log.
    """
    if len(data) != DEPOSIT_EVENT_LENGTH:
        raise InvalidBlock("Invalid deposit event data length")

    # Check that all the offsets are in order
    pubkey_offset = int.from_bytes(data[0:32], "big")
    if pubkey_offset != PUBKEY_OFFSET:
        raise InvalidBlock("Invalid pubkey offset in deposit log")

    withdrawal_credentials_offset = int.from_bytes(data[32:64], "big")
    if withdrawal_credentials_offset != WITHDRAWAL_CREDENTIALS_OFFSET:
        raise InvalidBlock(
            "Invalid withdrawal credentials offset in deposit log"
        )

    amount_offset = int.from_bytes(data[64:96], "big")
    if amount_offset != AMOUNT_OFFSET:
        raise InvalidBlock("Invalid amount offset in deposit log")

    signature_offset = int.from_bytes(data[96:128], "big")
    if signature_offset != SIGNATURE_OFFSET:
        raise InvalidBlock("Invalid signature offset in deposit log")

    index_offset = int.from_bytes(data[128:160], "big")
    if index_offset != INDEX_OFFSET:
        raise InvalidBlock("Invalid index offset in deposit log")

    # Check that all the sizes are in order
    pubkey_size = int.from_bytes(
        data[pubkey_offset : pubkey_offset + 32], "big"
    )
    if pubkey_size != PUBKEY_SIZE:
        raise InvalidBlock("Invalid pubkey size in deposit log")

    pubkey = data[pubkey_offset + 32 : pubkey_offset + 32 + PUBKEY_SIZE]

    withdrawal_credentials_size = int.from_bytes(
        data[
            withdrawal_credentials_offset : withdrawal_credentials_offset + 32
        ],
        "big",
    )
    if withdrawal_credentials_size != WITHDRAWAL_CREDENTIALS_SIZE:
        raise InvalidBlock(
            "Invalid withdrawal credentials size in deposit log"
        )

    withdrawal_credentials = data[
        withdrawal_credentials_offset
        + 32 : withdrawal_credentials_offset
        + 32
        + WITHDRAWAL_CREDENTIALS_SIZE
    ]

    amount_size = int.from_bytes(
        data[amount_offset : amount_offset + 32], "big"
    )
    if amount_size != AMOUNT_SIZE:
        raise InvalidBlock("Invalid amount size in deposit log")

    amount = data[amount_offset + 32 : amount_offset + 32 + AMOUNT_SIZE]

    signature_size = int.from_bytes(
        data[signature_offset : signature_offset + 32], "big"
    )
    if signature_size != SIGNATURE_SIZE:
        raise InvalidBlock("Invalid signature size in deposit log")

    signature = data[
        signature_offset + 32 : signature_offset + 32 + SIGNATURE_SIZE
    ]

    index_size = int.from_bytes(data[index_offset : index_offset + 32], "big")
    if index_size != INDEX_SIZE:
        raise InvalidBlock("Invalid index size in deposit log")

    index = data[index_offset + 32 : index_offset + 32 + INDEX_SIZE]

    return pubkey + withdrawal_credentials + amount + signature + index


def parse_deposit_requests_from_receipt(
    receipt: Union[Bytes, Receipt],
) -> Bytes:
    """
    Parse deposit requests from a receipt.
    """
    deposit_requests: Bytes = b""
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
