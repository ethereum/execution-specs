"""
EIP-7251: Increase the MAX_EFFECTIVE_BALANCE.

Allow validators to consolidate via execution layer requests.

https://eips.ethereum.org/EIPS/eip-7251
"""

from typing import ClassVar, List, Literal, Mapping, Self, Type

from execution_testing.base_types import Address, BLSPublicKey

from ....base_fork import BaseFork, SystemCallPhase
from ....bytecode import load_contract_bytecode
from ....requests import FeeSystemContractRequest, SystemContractRequest

CONSOLIDATION_REQUEST_PREDEPLOY_ADDRESS = (
    0x0000BBDDC7CE488642FB579F8B00F3A590007251
)
CONSOLIDATION_REQUEST_PREDEPLOY_BYTECODE = load_contract_bytecode(
    __name__, "consolidation_request.bin"
)


class ConsolidationRequest(FeeSystemContractRequest):
    """Consolidation request (EIP-7251)."""

    source_address: Address = Address(0)
    """
    The address of the execution layer account that made the consolidation
    request.
    """
    source_pubkey: BLSPublicKey
    """
    The public key of the source validator as it currently is in the beacon
    state.
    """
    target_pubkey: BLSPublicKey
    """
    The public key of the target validator as it currently is in the beacon
    state.
    """

    type: ClassVar[int] = 2
    system_contract_address: ClassVar[Address] = Address(
        CONSOLIDATION_REQUEST_PREDEPLOY_ADDRESS,
        label="CONSOLIDATION_REQUEST_PREDEPLOY_ADDRESS",
    )
    max_per_block: ClassVar[int] = 2
    target_per_block: ClassVar[int] = 1
    min_fee: ClassVar[int] = 1
    fee_update_fraction: ClassVar[int] = 17
    excess_fee_processing: ClassVar[Literal["block", "call"]] = "block"
    # Source address, then the 48-byte source and target validator pubkeys.
    slots_per_request: ClassVar[int] = 4

    def __bytes__(self) -> bytes:
        """Return consolidation's attributes as bytes."""
        return (
            bytes(self.source_address)
            + bytes(self.source_pubkey)
            + bytes(self.target_pubkey)
        )

    @property
    def calldata(self) -> bytes:
        """Return the 96-byte input: `source_pubkey ++ target_pubkey`."""
        return self.calldata_modifier(self.source_pubkey + self.target_pubkey)

    def with_source_address(self, source_address: Address) -> Self:
        """Return a copy with the source address set."""
        return self.copy(source_address=source_address)

    @classmethod
    def from_index(cls, index: int) -> Self:
        """Build a consolidation request from a sequential index."""
        return cls(source_pubkey=index * 2, target_pubkey=index * 2 + 1)


class EIP7251(BaseFork):
    """EIP-7251 class."""

    @classmethod
    def empty_block_bal_item_count(cls) -> int:
        """Add block-level access list elements for an empty block."""
        return (
            super(EIP7251, cls).empty_block_bal_item_count()
            + ConsolidationRequest.empty_block_bal_item_count()
        )

    @classmethod
    def system_contracts(cls) -> List[Address]:
        """Add the consolidation request predeploy contract."""
        return [ConsolidationRequest.system_contract_address] + super(
            EIP7251, cls
        ).system_contracts()

    @classmethod
    def system_contract_call_phases(cls) -> Mapping[Address, SystemCallPhase]:
        """Call the consolidation request predeploy after the transactions."""
        return {
            ConsolidationRequest.system_contract_address: (
                SystemCallPhase.AFTER_TRANSACTIONS
            ),
            **super(EIP7251, cls).system_contract_call_phases(),
        }

    @classmethod
    def system_contract_request_types(
        cls,
    ) -> List[Type[SystemContractRequest]]:
        """Add the consolidation request type."""
        return [ConsolidationRequest] + super(
            EIP7251, cls
        ).system_contract_request_types()

    @classmethod
    def pre_allocation_blockchain(cls) -> Mapping:
        """Pre-allocate the consolidation request contract."""
        return {
            CONSOLIDATION_REQUEST_PREDEPLOY_ADDRESS: {
                "nonce": 1,
                "code": CONSOLIDATION_REQUEST_PREDEPLOY_BYTECODE,
            },
            **super(EIP7251, cls).pre_allocation_blockchain(),
        }
