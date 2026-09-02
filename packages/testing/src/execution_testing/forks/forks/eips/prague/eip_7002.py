"""
EIP-7002: Execution layer triggerable withdrawals.

Allow validators to trigger exits and partial withdrawals via their execution
layer (0x01) withdrawal credentials.

https://eips.ethereum.org/EIPS/eip-7002
"""

from typing import ClassVar, List, Literal, Mapping, Self, Type

from execution_testing.base_types import Address, BLSPublicKey, HexNumber

from ....base_fork import BaseFork, SystemCallPhase
from ....bytecode import load_contract_bytecode
from ....requests import FeeSystemContractRequest, SystemContractRequest

WITHDRAWAL_REQUEST_PREDEPLOY_ADDRESS = (
    0x00000961EF480EB55E80D19AD83579A64C007002
)
WITHDRAWAL_REQUEST_PREDEPLOY_BYTECODE = load_contract_bytecode(
    __name__, "withdrawal_request.bin"
)


class WithdrawalRequest(FeeSystemContractRequest):
    """Withdrawal request (EIP-7002)."""

    source_address: Address = Address(0)
    """
    The address of the execution layer account that made the withdrawal
    request.
    """
    validator_pubkey: BLSPublicKey
    """
    The current public key of the validator as it currently is in the beacon
    state.
    """
    amount: HexNumber
    """The amount in gwei to be withdrawn on the beacon chain."""

    type: ClassVar[int] = 1
    system_contract_address: ClassVar[Address] = Address(
        WITHDRAWAL_REQUEST_PREDEPLOY_ADDRESS,
        label="WITHDRAWAL_REQUEST_PREDEPLOY_ADDRESS",
    )
    max_per_block: ClassVar[int] = 16
    target_per_block: ClassVar[int] = 2
    min_fee: ClassVar[int] = 1
    fee_update_fraction: ClassVar[int] = 17
    excess_fee_processing: ClassVar[Literal["block", "call"]] = "block"
    # Source address, then the 48-byte validator pubkey and 8-byte amount.
    slots_per_request: ClassVar[int] = 3

    def __bytes__(self) -> bytes:
        """Return withdrawal's attributes as bytes."""
        return (
            bytes(self.source_address)
            + bytes(self.validator_pubkey)
            + self.amount.to_bytes(8, "little")
        )

    @property
    def calldata(self) -> bytes:
        """Return the 56-byte input: `validator_pubkey ++ amount`."""
        return self.calldata_modifier(
            self.validator_pubkey + self.amount.to_bytes(8, byteorder="big")
        )

    def with_source_address(self, source_address: Address) -> Self:
        """Return a copy with the source address set."""
        return self.copy(source_address=source_address)

    @classmethod
    def from_index(cls, index: int) -> Self:
        """Build a withdrawal request from a sequential index."""
        return cls(validator_pubkey=index, amount=0)


class EIP7002(BaseFork):
    """EIP-7002 class."""

    @classmethod
    def empty_block_bal_item_count(cls) -> int:
        """Add block-level access list elements for an empty block."""
        return (
            super(EIP7002, cls).empty_block_bal_item_count()
            + WithdrawalRequest.empty_block_bal_item_count()
        )

    @classmethod
    def system_contracts(cls) -> List[Address]:
        """Add the withdrawal request predeploy contract."""
        return [WithdrawalRequest.system_contract_address] + super(
            EIP7002, cls
        ).system_contracts()

    @classmethod
    def system_contract_call_phases(cls) -> Mapping[Address, SystemCallPhase]:
        """Call the withdrawal request predeploy after the transactions."""
        return {
            WithdrawalRequest.system_contract_address: (
                SystemCallPhase.AFTER_TRANSACTIONS
            ),
            **super(EIP7002, cls).system_contract_call_phases(),
        }

    @classmethod
    def system_contract_request_types(
        cls,
    ) -> List[Type[SystemContractRequest]]:
        """Add the withdrawal request type."""
        return [WithdrawalRequest] + super(
            EIP7002, cls
        ).system_contract_request_types()

    @classmethod
    def pre_allocation_blockchain(cls) -> Mapping:
        """Pre-allocate the withdrawal request contract."""
        return {
            WITHDRAWAL_REQUEST_PREDEPLOY_ADDRESS: {
                "nonce": 1,
                "code": WITHDRAWAL_REQUEST_PREDEPLOY_BYTECODE,
            },
            **super(EIP7002, cls).pre_allocation_blockchain(),
        }
