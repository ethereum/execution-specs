"""Helpers for the EIP-7251 consolidation tests."""

from typing import ClassVar, Self

from execution_testing import Address, FeeSystemContractRequest
from execution_testing import (
    ConsolidationRequest as ConsolidationRequestBase,
)

from .spec import Spec


class ConsolidationRequest(ConsolidationRequestBase, FeeSystemContractRequest):
    """Class used to describe a consolidation request in a test."""

    interaction_contract_address: ClassVar[Address] = Address(
        Spec.CONSOLIDATION_REQUEST_PREDEPLOY_ADDRESS
    )
    min_fee: ClassVar[int] = Spec.MIN_CONSOLIDATION_REQUEST_FEE
    update_fraction: ClassVar[int] = (
        Spec.CONSOLIDATION_REQUEST_FEE_UPDATE_FRACTION
    )
    target_per_block: ClassVar[int] = (
        Spec.TARGET_CONSOLIDATION_REQUESTS_PER_BLOCK
    )
    max_per_block: ClassVar[int] = Spec.MAX_CONSOLIDATION_REQUESTS_PER_BLOCK

    @property
    def calldata(self) -> bytes:
        """
        Return the calldata needed to call the consolidation request contract
        and make the consolidation.
        """
        return self.calldata_modifier(self.source_pubkey + self.target_pubkey)

    def with_source_address(
        self, source_address: Address
    ) -> "ConsolidationRequest":
        """
        Return a new instance of the consolidation request with the source
        address set.
        """
        return self.copy(source_address=source_address)

    @classmethod
    def from_index(cls, index: int) -> Self:
        """Build a consolidation request from a sequential index."""
        return cls(source_pubkey=index * 2, target_pubkey=index * 2 + 1)
