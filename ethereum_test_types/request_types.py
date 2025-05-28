"""Request types for Ethereum tests."""

from abc import abstractmethod
from collections import defaultdict
from typing import ClassVar, Dict, List, SupportsBytes

from ethereum_test_base_types import (
    Address,
    BLSPublicKey,
    BLSSignature,
    Bytes,
    CamelModel,
    Hash,
    HexNumber,
)


class RequestBase:
    """Base class for requests."""

    type: ClassVar[int]

    @abstractmethod
    def __bytes__(self) -> bytes:
        """Return request's attributes as bytes."""
        ...


class DepositRequest(RequestBase, CamelModel):
    """Deposit Request type."""

    pubkey: BLSPublicKey
    """
    The public key of the beacon chain validator.
    """
    withdrawal_credentials: Hash
    """
    The withdrawal credentials of the beacon chain validator.
    """
    amount: HexNumber
    """
    The amount in gwei of the deposit.
    """
    signature: BLSSignature
    """
    The signature of the deposit using the validator's private key that matches the
    `pubkey`.
    """
    index: HexNumber
    """
    The index of the deposit.
    """

    type: ClassVar[int] = 0

    def __bytes__(self) -> bytes:
        """Return deposit's attributes as bytes."""
        return (
            bytes(self.pubkey)
            + bytes(self.withdrawal_credentials)
            + self.amount.to_bytes(8, "little")
            + bytes(self.signature)
            + self.index.to_bytes(8, "little")
        )


class WithdrawalRequest(RequestBase, CamelModel):
    """Withdrawal Request type."""

    source_address: Address = Address(0)
    """
    The address of the execution layer account that made the withdrawal request.
    """
    validator_pubkey: BLSPublicKey
    """
    The current public key of the validator as it currently is in the beacon state.
    """
    amount: HexNumber
    """
    The amount in gwei to be withdrawn on the beacon chain.
    """

    type: ClassVar[int] = 1

    def __bytes__(self) -> bytes:
        """Return withdrawal's attributes as bytes."""
        return (
            bytes(self.source_address)
            + bytes(self.validator_pubkey)
            + self.amount.to_bytes(8, "little")
        )


class ConsolidationRequest(RequestBase, CamelModel):
    """Consolidation Request type."""

    source_address: Address = Address(0)
    """
    The address of the execution layer account that made the consolidation request.
    """
    source_pubkey: BLSPublicKey
    """
    The public key of the source validator as it currently is in the beacon state.
    """
    target_pubkey: BLSPublicKey
    """
    The public key of the target validator as it currently is in the beacon state.
    """

    type: ClassVar[int] = 2

    def __bytes__(self) -> bytes:
        """Return consolidation's attributes as bytes."""
        return bytes(self.source_address) + bytes(self.source_pubkey) + bytes(self.target_pubkey)


def requests_list_to_bytes(requests_list: List[RequestBase] | Bytes | SupportsBytes) -> Bytes:
    """Convert list of requests to bytes."""
    if not isinstance(requests_list, list):
        return Bytes(requests_list)
    return Bytes(b"".join([bytes(r) for r in requests_list]))


class Requests:
    """Requests for the transition tool."""

    requests_list: List[Bytes]

    def __init__(
        self,
        *requests: RequestBase,
        requests_lists: List[List[RequestBase] | Bytes] | None = None,
    ):
        """Initialize requests object."""
        if requests_lists is not None:
            assert len(requests) == 0, "requests must be empty if list is provided"
            self.requests_list = []
            for requests_list in requests_lists:
                self.requests_list.append(requests_list_to_bytes(requests_list))
            return
        else:
            lists: Dict[int, List[RequestBase]] = defaultdict(list)
            for r in requests:
                lists[r.type].append(r)

            self.requests_list = [
                Bytes(bytes([request_type]) + requests_list_to_bytes(lists[request_type]))
                for request_type in sorted(lists.keys())
            ]

    def __bytes__(self) -> bytes:
        """Return requests hash."""
        s: bytes = b"".join(r.sha256() for r in self.requests_list)
        return Bytes(s).sha256()
