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
from .transactions import (
    AccessListTransaction,
    BlobTransaction,
    FeeMarketTransaction,
    LegacyTransaction,
    Transaction,
)
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


def encode_receipt(tx: Transaction, receipt: Receipt) -> Union[Bytes, Receipt]:
    """
    Encodes a receipt.
    """
    if isinstance(tx, AccessListTransaction):
        return b"\x01" + rlp.encode(receipt)
    elif isinstance(tx, FeeMarketTransaction):
        return b"\x02" + rlp.encode(receipt)
    elif isinstance(tx, BlobTransaction):
        return b"\x03" + rlp.encode(receipt)
    else:
        return receipt


def decode_receipt(receipt: Union[Bytes, Receipt]) -> Receipt:
    """
    Decodes a receipt.
    """
    if isinstance(receipt, Bytes):
        assert receipt[0] in (b"\x01", b"\x02", b"\x03")
        return rlp.decode_to(Receipt, receipt[1:])
    else:
        return receipt


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


@slotted_freezable
@dataclass
class WithdrawalRequest:
    """
    Requests for execution layer withdrawals (See EIP-7002).
    """

    source_address: Address
    validator_pubkey: Bytes48
    amount: U64


@slotted_freezable
@dataclass
class ConsolidationRequest:
    """
    Requests for validator consolidation (See EIP-7251).
    """

    source_address: Address
    source_pubkey: Bytes48
    target_pubkey: Bytes48


Request = Union[DepositRequest, WithdrawalRequest, ConsolidationRequest]


def encode_request(req: Request) -> Bytes:
    """
    Encode a request.
    """
    if isinstance(req, DepositRequest):
        return DEPOSIT_REQUEST_TYPE + rlp.encode(req)
    elif isinstance(req, WithdrawalRequest):
        return WITHDRAWAL_REQUEST_TYPE + rlp.encode(req)
    elif isinstance(req, ConsolidationRequest):
        return CONSOLIDATION_REQUEST_TYPE + rlp.encode(req)
    else:
        raise Exception("Unknown request type")


def parse_deposit_data(data: Bytes) -> DepositRequest:
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

    return deposit_request


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
    req = WithdrawalRequest(
        source_address=Address(data[:20]),
        validator_pubkey=Bytes48(data[20:68]),
        amount=U64.from_be_bytes(data[68:76]),
    )

    return req


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
    req = ConsolidationRequest(
        source_address=Address(data[:20]),
        source_pubkey=Bytes48(data[20:68]),
        target_pubkey=Bytes48(data[68:116]),
    )

    return req


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
