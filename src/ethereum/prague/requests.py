"""
Requests were introduced in EIP-7685 as a a general purpose framework for
storing contract-triggered requests. It extends the execution header and
body with a single field each to store the request information.
This inherently exposes the requests to the consensus layer, which can
then process each one.

[EIP-7685]: https://eips.ethereum.org/EIPS/eip-7685
"""

from dataclasses import dataclass
from typing import Tuple, Union

from .. import rlp
from ..base_types import (
    U64,
    Bytes,
    Bytes32,
    Bytes48,
    Bytes96,
    slotted_freezable,
)
from .blocks import Receipt, decode_receipt
from .fork_types import Address
from .utils.hexadecimal import hex_to_address

DEPOSIT_CONTRACT_ADDRESS = hex_to_address(
    "0x00000000219ab540356cbb839cbe05303d7705fa"
)
DEPOSIT_REQUEST_TYPE = b"\x00"
WITHDRAWAL_REQUEST_TYPE = b"\x01"
CONSOLIDATION_REQUEST_TYPE = b"\x02"
WITHDRAWAL_REQUEST_LENGTH = 76
CONSOLIDATION_REQUEST_LENGTH = 116


@slotted_freezable
@dataclass
class DepositRequest:
    """
    Requests for validator deposits on chain (See [EIP-6110]).

    [EIP-6110]: https://eips.ethereum.org/EIPS/eip-6110
    """

    pubkey: Bytes48
    withdrawal_credentials: Bytes32
    amount: U64
    signature: Bytes96
    index: U64


@slotted_freezable
@dataclass
class WithdrawalRequest:
    """
    Requests for execution layer withdrawals (See [EIP-7002]).

    [EIP-7002]: https://eips.ethereum.org/EIPS/eip-7002
    """

    source_address: Address
    validator_pubkey: Bytes48
    amount: U64


@slotted_freezable
@dataclass
class ConsolidationRequest:
    """
    Requests for validator consolidation (See [EIP-7251]).

    [EIP-7251]: https://eips.ethereum.org/EIPS/eip-7251
    """

    source_address: Address
    source_pubkey: Bytes48
    target_pubkey: Bytes48


Request = Union[DepositRequest, WithdrawalRequest, ConsolidationRequest]


def encode_request(req: Request) -> Bytes:
    """
    Serialize a `Request` into a byte sequence.

    `Request`s are encoded as a type byte followed by the RLP encoding
    of the request.
    """
    if isinstance(req, DepositRequest):
        return DEPOSIT_REQUEST_TYPE + rlp.encode(req)
    elif isinstance(req, WithdrawalRequest):
        return WITHDRAWAL_REQUEST_TYPE + rlp.encode(req)
    elif isinstance(req, ConsolidationRequest):
        return CONSOLIDATION_REQUEST_TYPE + rlp.encode(req)
    else:
        raise Exception("Unknown request type")


def decode_request(data: Bytes) -> Request:
    """
    Decode a request.
    """
    if data.startswith(DEPOSIT_REQUEST_TYPE):
        return rlp.decode_to(DepositRequest, data[1:])
    elif data.startswith(WITHDRAWAL_REQUEST_TYPE):
        return rlp.decode_to(WithdrawalRequest, data[1:])
    elif data.startswith(CONSOLIDATION_REQUEST_TYPE):
        return rlp.decode_to(ConsolidationRequest, data[1:])
    else:
        raise Exception("Unknown request type")


def parse_deposit_data(data: Bytes) -> DepositRequest:
    """
    Parses Deposit Request from the DepositContract.DepositEvent data.
    """
    return DepositRequest(
        pubkey=Bytes48(data[192:240]),
        withdrawal_credentials=Bytes32(data[288:320]),
        amount=U64.from_le_bytes(data[352:360]),
        signature=Bytes96(data[416:512]),
        index=U64.from_le_bytes(data[544:552]),
    )


def parse_deposit_requests_from_receipt(
    receipt: Union[Bytes, Receipt],
) -> Tuple[Bytes, ...]:
    """
    Parse deposit requests from a receipt.
    """
    deposit_requests: Tuple[Bytes, ...] = ()
    decoded_receipt = decode_receipt(receipt)
    for log in decoded_receipt.logs:
        if log.address == DEPOSIT_CONTRACT_ADDRESS:
            deposit_request = parse_deposit_data(log.data)
            deposit_requests += (encode_request(deposit_request),)

    return deposit_requests


def parse_withdrawal_data(data: Bytes) -> WithdrawalRequest:
    """
    Parses Withdrawal Request from the data.
    """
    assert len(data) == WITHDRAWAL_REQUEST_LENGTH
    return WithdrawalRequest(
        source_address=Address(data[:20]),
        validator_pubkey=Bytes48(data[20:68]),
        amount=U64.from_be_bytes(data[68:76]),
    )


def parse_withdrawal_requests_from_system_tx(
    evm_call_output: Bytes,
) -> Tuple[Bytes, ...]:
    """
    Parse withdrawal requests from the system transaction output.
    """
    count_withdrawal_requests = (
        len(evm_call_output) // WITHDRAWAL_REQUEST_LENGTH
    )

    withdrawal_requests: Tuple[Bytes, ...] = ()
    for i in range(count_withdrawal_requests):
        start = i * WITHDRAWAL_REQUEST_LENGTH
        withdrawal_request = parse_withdrawal_data(
            evm_call_output[start : start + WITHDRAWAL_REQUEST_LENGTH]
        )
        withdrawal_requests += (encode_request(withdrawal_request),)

    return withdrawal_requests


def parse_consolidation_data(data: Bytes) -> ConsolidationRequest:
    """
    Parses Consolidation Request from the data.
    """
    assert len(data) == CONSOLIDATION_REQUEST_LENGTH
    return ConsolidationRequest(
        source_address=Address(data[:20]),
        source_pubkey=Bytes48(data[20:68]),
        target_pubkey=Bytes48(data[68:116]),
    )


def parse_consolidation_requests_from_system_tx(
    evm_call_output: Bytes,
) -> Tuple[Bytes, ...]:
    """
    Parse consolidation requests from the system transaction output.
    """
    count_consolidation_requests = (
        len(evm_call_output) // CONSOLIDATION_REQUEST_LENGTH
    )

    consolidation_requests: Tuple[Bytes, ...] = ()
    for i in range(count_consolidation_requests):
        start = i * CONSOLIDATION_REQUEST_LENGTH
        consolidation_request = parse_consolidation_data(
            evm_call_output[start : start + CONSOLIDATION_REQUEST_LENGTH]
        )
        consolidation_requests += (encode_request(consolidation_request),)

    return consolidation_requests
