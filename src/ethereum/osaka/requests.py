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

from .blocks import Receipt, decode_receipt
from .utils.hexadecimal import hex_to_address

DEPOSIT_CONTRACT_ADDRESS = hex_to_address(
    "0x00000000219ab540356cbb839cbe05303d7705fa"
)
DEPOSIT_REQUEST_TYPE = b"\x00"
WITHDRAWAL_REQUEST_TYPE = b"\x01"
CONSOLIDATION_REQUEST_TYPE = b"\x02"


def extract_deposit_data(data: Bytes) -> Bytes:
    """
    Extracts Deposit Request from the DepositContract.DepositEvent data.
    """
    return (
        data[192:240]  # public_key
        + data[288:320]  # withdrawal_credentials
        + data[352:360]  # amount
        + data[416:512]  # signature
        + data[544:552]  # index
    )


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
