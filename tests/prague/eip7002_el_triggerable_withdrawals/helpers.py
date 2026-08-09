"""Helpers for the EIP-7002 withdrawal tests."""

from typing import ClassVar, Self

from execution_testing import Address, FeeSystemContractRequest
from execution_testing import (
    WithdrawalRequest as WithdrawalRequestBase,
)

from .spec import Spec


class WithdrawalRequest(WithdrawalRequestBase, FeeSystemContractRequest):
    """Class used to describe a withdrawal request in a test."""

    interaction_contract_address: ClassVar[Address] = Address(
        Spec.WITHDRAWAL_REQUEST_PREDEPLOY_ADDRESS
    )
    min_fee: ClassVar[int] = Spec.MIN_WITHDRAWAL_REQUEST_FEE
    update_fraction: ClassVar[int] = (
        Spec.WITHDRAWAL_REQUEST_FEE_UPDATE_FRACTION
    )
    target_per_block: ClassVar[int] = Spec.TARGET_WITHDRAWAL_REQUESTS_PER_BLOCK
    max_per_block: ClassVar[int] = Spec.MAX_WITHDRAWAL_REQUESTS_PER_BLOCK

    @property
    def calldata(self) -> bytes:
        """
        Return the calldata needed to call the withdrawal request contract and
        make the withdrawal.
        """
        return self.calldata_modifier(
            self.validator_pubkey + self.amount.to_bytes(8, byteorder="big")
        )

    def with_source_address(
        self, source_address: Address
    ) -> "WithdrawalRequest":
        """
        Return a new instance of the withdrawal request with the source address
        set.
        """
        return self.copy(source_address=source_address)

    @classmethod
    def from_index(cls, index: int) -> Self:
        """Build a withdrawal request from a sequential index."""
        return cls(validator_pubkey=index, amount=0)
