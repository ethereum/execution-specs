"""
Requests were introduced in EIP-7685 as a a general purpose framework for
storing contract-triggered requests. It extends the execution header and
body with a single field each to store the request information.
This inherently exposes the requests to the consensus layer, which can
then process each one.

[EIP-7685]: https://eips.ethereum.org/EIPS/eip-7685
"""

from typing import Union

from ..base_types import Bytes
from .blocks import Receipt, decode_receipt
from .utils.hexadecimal import hex_to_address

DEPOSIT_CONTRACT_ADDRESS = hex_to_address(
    "0x00000000219ab540356cbb839cbe05303d7705fa"
)
DEPOSIT_REQUEST_TYPE = b"\x00"
WITHDRAWAL_REQUEST_TYPE = b"\x01"
CONSOLIDATION_REQUEST_TYPE = b"\x02"
WITHDRAWAL_REQUEST_LENGTH = 76
CONSOLIDATION_REQUEST_LENGTH = 116


def parse_deposit_data(data: Bytes) -> Bytes:
    """
    Parses Deposit Request from the DepositContract.DepositEvent data.
    """
    return (
        DEPOSIT_REQUEST_TYPE
        + data[192:240]  # public_key
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
            deposit_requests += parse_deposit_data(log.data)

    return deposit_requests


def parse_withdrawal_requests_from_system_tx(
    evm_call_output: Bytes,
) -> Bytes:
    """
    Parse withdrawal requests from the system transaction output.
    """
    count_withdrawal_requests = (
        len(evm_call_output) // WITHDRAWAL_REQUEST_LENGTH
    )

    withdrawal_requests: Bytes = b""
    for i in range(count_withdrawal_requests):
        start = i * WITHDRAWAL_REQUEST_LENGTH
        withdrawal_requests += (
            WITHDRAWAL_REQUEST_TYPE
            + evm_call_output[start : start + WITHDRAWAL_REQUEST_LENGTH]
        )

    return withdrawal_requests


def parse_consolidation_requests_from_system_tx(
    evm_call_output: Bytes,
) -> Bytes:
    """
    Parse consolidation requests from the system transaction output.
    """
    count_consolidation_requests = (
        len(evm_call_output) // CONSOLIDATION_REQUEST_LENGTH
    )

    consolidation_requests: Bytes = b""
    for i in range(count_consolidation_requests):
        start = i * CONSOLIDATION_REQUEST_LENGTH
        consolidation_requests += (
            CONSOLIDATION_REQUEST_TYPE
            + evm_call_output[start : start + CONSOLIDATION_REQUEST_LENGTH]
        )

    return consolidation_requests
