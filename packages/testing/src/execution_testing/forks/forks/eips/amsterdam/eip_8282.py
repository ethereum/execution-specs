"""
EIP-8282: Builder Execution Requests.

Predeploy builder deposit and exit request contracts for EIP-7732 builders,
queuing their requests for EIP-7685.

https://eips.ethereum.org/EIPS/eip-8282
"""

from typing import ClassVar, List, Literal, Mapping, Self, Type

from execution_testing.base_types import (
    Address,
    BLSPublicKey,
    BLSSignature,
    Hash,
    HexNumber,
)

from ....base_fork import BaseFork, SystemCallPhase
from ....bytecode import load_contract_bytecode
from ....requests import FeeSystemContractRequest, SystemContractRequest

BUILDER_DEPOSIT_CONTRACT_ADDRESS = 0x0000BFF46984E3725691FA540A8C7589300D8282
BUILDER_DEPOSIT_CONTRACT_BYTECODE = load_contract_bytecode(
    __name__, "builder_deposit_request.bin"
)

BUILDER_EXIT_CONTRACT_ADDRESS = 0x000064D678505AD48F8CCB093BC65613800E8282
BUILDER_EXIT_CONTRACT_BYTECODE = load_contract_bytecode(
    __name__, "builder_exit_request.bin"
)


class BuilderDepositRequest(FeeSystemContractRequest):
    """
    Builder deposit request (EIP-8282).

    Serves both a builder's first deposit and stake top-ups. The request pays
    the shared EIP-1559-style fee on top of the staked `amount`, so its call
    value is `fee + amount * 1 gwei`.
    """

    pubkey: BLSPublicKey
    """The public key of the beacon chain builder."""
    withdrawal_credentials: Hash
    """The withdrawal credentials of the beacon chain builder."""
    amount: HexNumber
    """The amount in gwei of the builder deposit."""
    signature: BLSSignature
    """
    The signature of the deposit using the builder's private key that matches
    the `pubkey`.
    """
    extra_wei: int = 0
    """
    Extra wei added to (or, if negative, subtracted from) the call value, used
    to test the predeploy's `value >= fee + amount * 1 gwei` check.
    """

    type: ClassVar[int] = 3
    system_contract_address: ClassVar[Address] = Address(
        BUILDER_DEPOSIT_CONTRACT_ADDRESS,
        label="BUILDER_DEPOSIT_CONTRACT_ADDRESS",
    )
    max_per_block: ClassVar[int] = 64
    target_per_block: ClassVar[int] = 8
    min_fee: ClassVar[int] = 1
    fee_update_fraction: ClassVar[int] = 17
    excess_fee_processing: ClassVar[Literal["block", "call"]] = "call"
    # The 184-byte deposit input: pubkey, withdrawal credentials, amount and
    # signature.
    slots_per_request: ClassVar[int] = 6
    min_deposit_wei: ClassVar[int] = 10**18
    """Minimum credited stake for a builder deposit, in wei (1 ETH)."""

    def __bytes__(self) -> bytes:
        """Return builder deposit's attributes as bytes."""
        return (
            bytes(self.pubkey)
            + bytes(self.withdrawal_credentials)
            + self.amount.to_bytes(8, "little")
            + bytes(self.signature)
        )

    @property
    def value(self) -> int:
        """Return the fee plus the staked amount in wei, plus `extra_wei`."""
        return self.fee + self.amount * 10**9 + self.extra_wei

    @property
    def calldata(self) -> bytes:
        """
        Return the 184-byte input: `pubkey ++ withdrawal_credentials ++ amount
        (big-endian) ++ signature`.
        """
        return self.calldata_modifier(
            bytes(self.pubkey)
            + bytes(self.withdrawal_credentials)
            + self.amount.to_bytes(8, "big")
            + bytes(self.signature)
        )

    def with_source_address(self, source_address: Address) -> Self:
        """Return a copy; deposit records carry no source address."""
        del source_address
        return self.copy()

    @classmethod
    def from_index(cls, index: int) -> Self:
        """Build a builder deposit request from a sequential index."""
        return cls(
            pubkey=index * 3,
            withdrawal_credentials=(index * 3) + 1,
            amount=cls.min_deposit_wei // 10**9,
            signature=(index * 3) + 2,
        )


class BuilderExitRequest(FeeSystemContractRequest):
    """
    Builder exit request (EIP-8282).

    Authorized by the caller's address (recorded as `source_address`); it
    stakes no value and only pays the shared request fee.
    """

    source_address: Address = Address(0)
    """
    The address of the execution layer account that made the builder exit
    request.
    """
    pubkey: BLSPublicKey
    """The public key of the builder to exit."""

    type: ClassVar[int] = 4
    system_contract_address: ClassVar[Address] = Address(
        BUILDER_EXIT_CONTRACT_ADDRESS,
        label="BUILDER_EXIT_CONTRACT_ADDRESS",
    )
    max_per_block: ClassVar[int] = 16
    target_per_block: ClassVar[int] = 2
    min_fee: ClassVar[int] = 1
    fee_update_fraction: ClassVar[int] = 17
    excess_fee_processing: ClassVar[Literal["block", "call"]] = "call"
    # Source address, then the 48-byte builder pubkey.
    slots_per_request: ClassVar[int] = 3

    def __bytes__(self) -> bytes:
        """Return builder exit's attributes as bytes."""
        return bytes(self.source_address) + bytes(self.pubkey)

    @property
    def calldata(self) -> bytes:
        """Return the 48-byte input: the builder `pubkey`."""
        return self.calldata_modifier(bytes(self.pubkey))

    def with_source_address(self, source_address: Address) -> Self:
        """Return a copy with the source address set."""
        return self.copy(source_address=source_address)

    @classmethod
    def from_index(cls, index: int) -> Self:
        """Build a builder exit request from a sequential index."""
        return cls(pubkey=index)


class EIP8282(BaseFork):
    """EIP-8282 class."""

    @classmethod
    def max_request_type(cls) -> int:
        """
        Two request types are introduced: builder deposit requests (0x03)
        and builder exit requests (0x04).
        """
        return super(EIP8282, cls).max_request_type() + 2

    @classmethod
    def empty_block_bal_item_count(cls) -> int:
        """Add block-level access list elements for an empty block."""
        return (
            super(EIP8282, cls).empty_block_bal_item_count()
            + BuilderDepositRequest.empty_block_bal_item_count()
            + BuilderExitRequest.empty_block_bal_item_count()
        )

    @classmethod
    def system_contracts(cls) -> List[Address]:
        """Add the builder deposit and exit request predeploy contracts."""
        return [
            BuilderDepositRequest.system_contract_address,
            BuilderExitRequest.system_contract_address,
        ] + super(EIP8282, cls).system_contracts()

    @classmethod
    def system_contract_call_phases(cls) -> Mapping[Address, SystemCallPhase]:
        """Call the builder request predeploys after the transactions."""
        return {
            BuilderDepositRequest.system_contract_address: (
                SystemCallPhase.AFTER_TRANSACTIONS
            ),
            BuilderExitRequest.system_contract_address: (
                SystemCallPhase.AFTER_TRANSACTIONS
            ),
            **super(EIP8282, cls).system_contract_call_phases(),
        }

    @classmethod
    def system_contract_request_types(
        cls,
    ) -> List[Type[SystemContractRequest]]:
        """Add the builder deposit and exit request types."""
        request_types: List[Type[SystemContractRequest]] = [
            BuilderDepositRequest,
            BuilderExitRequest,
        ]
        return (
            request_types + super(EIP8282, cls).system_contract_request_types()
        )

    @classmethod
    def pre_allocation_blockchain(cls) -> Mapping:
        """Pre-allocate the builder deposit and exit request contracts."""
        return {
            BUILDER_DEPOSIT_CONTRACT_ADDRESS: {
                "nonce": 1,
                "code": BUILDER_DEPOSIT_CONTRACT_BYTECODE,
            },
            BUILDER_EXIT_CONTRACT_ADDRESS: {
                "nonce": 1,
                "code": BUILDER_EXIT_CONTRACT_BYTECODE,
            },
            **super(EIP8282, cls).pre_allocation_blockchain(),
        }
