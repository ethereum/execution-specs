"""
A `Block` is a single link in the chain that is Ethereum. Each `Block` contains
a `Header` and zero or more transactions. Each `Header` contains associated
metadata like the block number, parent block hash, and how much gas was
consumed by its transactions.

Together, these blocks form a cryptographically secure journal recording the
history of all state transitions that have happened since the genesis of the
chain.
"""
from dataclasses import dataclass
from typing import Tuple, Union

from ethereum.exceptions import InvalidBlock

from .. import rlp
from ..base_types import (
    U64,
    U256,
    Bytes,
    Bytes8,
    Bytes32,
    Bytes48,
    Bytes96,
    Uint,
    slotted_freezable,
)
from ..crypto.hash import Hash32
from .fork_types import Address, Bloom, Root
from .transactions import LegacyTransaction
from .utils.hexadecimal import hex_to_address

DEPOSIT_CONTRACT_ADDRESS = hex_to_address(
    "0x00000000219ab540356cbb839cbe05303d7705fa"
)
DEPOSIT_REQUEST_TYPE = b"\x00"


@slotted_freezable
@dataclass
class Withdrawal:
    """
    Withdrawals that have been validated on the consensus layer.
    """

    index: U64
    validator_index: U64
    address: Address
    amount: U256


@slotted_freezable
@dataclass
class Header:
    """
    Header portion of a block on the chain.
    """

    parent_hash: Hash32
    ommers_hash: Hash32
    coinbase: Address
    state_root: Root
    transactions_root: Root
    receipt_root: Root
    bloom: Bloom
    difficulty: Uint
    number: Uint
    gas_limit: Uint
    gas_used: Uint
    timestamp: U256
    extra_data: Bytes
    prev_randao: Bytes32
    nonce: Bytes8
    base_fee_per_gas: Uint
    withdrawals_root: Root
    blob_gas_used: U64
    excess_blob_gas: U64
    parent_beacon_block_root: Root
    requests_root: Root


@slotted_freezable
@dataclass
class Block:
    """
    A complete block.
    """

    header: Header
    transactions: Tuple[Union[Bytes, LegacyTransaction], ...]
    ommers: Tuple[Header, ...]
    withdrawals: Tuple[Withdrawal, ...]
    requests: Tuple[Bytes, ...]


@slotted_freezable
@dataclass
class Log:
    """
    Data record produced during the execution of a transaction.
    """

    address: Address
    topics: Tuple[Hash32, ...]
    data: bytes


@slotted_freezable
@dataclass
class Receipt:
    """
    Result of a transaction.
    """

    succeeded: bool
    cumulative_gas_used: Uint
    bloom: Bloom
    logs: Tuple[Log, ...]


def validate_requests(requests: Tuple[Bytes, ...]) -> bool:
    """
    Validate a list of requests.
    """
    current_request_type = b"\x00"
    for request in requests:
        if request[:1] < current_request_type:
            return False
        current_request_type = request[:1]
    return True


@slotted_freezable
@dataclass
class DepositRequest:
    """
    Requests for validator deposits on chain (See EIP-6110).
    """

    pubkey: Bytes48
    withdrawal_credentials: Bytes32
    amount: U64
    signature: Bytes96
    index: U64


Request = DepositRequest


def encode_request(req: Request) -> Bytes:
    """
    Encode a request.
    """
    if isinstance(req, DepositRequest):
        return DEPOSIT_REQUEST_TYPE + rlp.encode(req)
    else:
        raise Exception("Unknown request type")


def parse_deposit_data(data: Bytes) -> Bytes:
    """
    Parses Deposit Request from the DepositContract.DepositEvent data.
    """
    deposit_request = DepositRequest(
        pubkey=Bytes48(data[192:240]),
        withdrawal_credentials=Bytes32(data[288:320]),
        amount=U64.from_le_bytes(data[352:360]),
        signature=Bytes96(data[416:512]),
        index=U64.from_le_bytes(data[544:552]),
    )

    return encode_request(deposit_request)


def validate_deposit_requests(
    receipts: Tuple[Receipt, ...], requests: Tuple[Bytes, ...]
) -> None:
    """
    Validate a list of deposit requests.
    """
    # Retrieve all deposit requests from receipts.
    expected_deposit_requests = []
    for receipt in receipts:
        for log in receipt.logs:
            if log.address == DEPOSIT_CONTRACT_ADDRESS:
                deposit_request_rlp = parse_deposit_data(log.data)
                expected_deposit_requests.append(deposit_request_rlp)

    # Retrieve all deposit requests from block body
    deposit_requests = [
        req for req in requests if req[:1] == DEPOSIT_REQUEST_TYPE
    ]

    if deposit_requests != expected_deposit_requests:
        raise InvalidBlock("BlockException.INVALID_REQUESTS")
