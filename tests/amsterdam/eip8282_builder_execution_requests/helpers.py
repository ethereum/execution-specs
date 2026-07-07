"""Helpers for the EIP-8282 builder execution request tests."""

from typing import ClassVar, Literal, Self

from execution_testing import Address, FeeSystemContractRequest
from execution_testing import (
    BuilderDepositRequest as BuilderDepositRequestBase,
)
from execution_testing import (
    BuilderExitRequest as BuilderExitRequestBase,
)

from .spec import Spec


class BuilderDepositRequest(
    BuilderDepositRequestBase, FeeSystemContractRequest
):
    """
    Builder deposit request used in a test.

    Serves both a builder's first deposit and stake top-ups. The request pays
    the shared EIP-1559-style fee on top of the staked `amount`, so its call
    value is `fee + amount * 1 gwei`.
    """

    interaction_contract_address: ClassVar[Address] = Address(
        Spec.BUILDER_DEPOSIT_CONTRACT_ADDRESS
    )
    min_fee: ClassVar[int] = Spec.MIN_REQUEST_FEE
    update_fraction: ClassVar[int] = Spec.REQUEST_FEE_UPDATE_FRACTION
    target_per_block: ClassVar[int] = Spec.TARGET_DEPOSIT_REQUESTS_PER_BLOCK
    max_per_block: ClassVar[int] = Spec.MAX_DEPOSIT_REQUESTS_PER_BLOCK
    excess_fee_processing: ClassVar[Literal["block", "call"]] = "call"

    extra_wei: int = 0
    """
    Extra wei added to (or, if negative, subtracted from) the call value, used
    to test the predeploy's `value >= fee + amount * 1 gwei` check.
    """

    @property
    def value(self) -> int:
        """
        Return the value of the call, equal to the request fee plus the staked
        amount in wei (adjusted by `extra_wei`).
        """
        return self.fee + self.amount * 10**9 + self.extra_wei

    @property
    def calldata(self) -> bytes:
        """
        Return the 184-byte input calldata: `pubkey ++ withdrawal_credentials
        ++ amount (big-endian) ++ signature`.
        """
        return self.calldata_modifier(
            bytes(self.pubkey)
            + bytes(self.withdrawal_credentials)
            + self.amount.to_bytes(8, "big")
            + bytes(self.signature)
        )

    def with_source_address(
        self, source_address: Address
    ) -> "BuilderDepositRequest":
        """Return a copy; deposit records carry no source address."""
        del source_address
        return self.copy()

    @classmethod
    def from_index(cls, index: int) -> Self:
        """Build a builder deposit request from a sequential index."""
        return cls(
            pubkey=index * 3,
            withdrawal_credentials=(index * 3) + 1,
            amount=Spec.BUILDER_MIN_DEPOSIT // 10**9,
            signature=(index * 3) + 2,
        )


class BuilderExitRequest(BuilderExitRequestBase, FeeSystemContractRequest):
    """
    Builder exit request used in a test.

    Authorized by the caller's address (recorded as `source_address`); it
    stakes no value and only pays the shared request fee.
    """

    interaction_contract_address: ClassVar[Address] = Address(
        Spec.BUILDER_EXIT_CONTRACT_ADDRESS
    )
    min_fee: ClassVar[int] = Spec.MIN_REQUEST_FEE
    update_fraction: ClassVar[int] = Spec.REQUEST_FEE_UPDATE_FRACTION
    target_per_block: ClassVar[int] = Spec.TARGET_EXIT_REQUESTS_PER_BLOCK
    max_per_block: ClassVar[int] = Spec.MAX_EXIT_REQUESTS_PER_BLOCK
    excess_fee_processing: ClassVar[Literal["block", "call"]] = "call"

    @property
    def calldata(self) -> bytes:
        """Return the 48-byte input calldata: the builder `pubkey`."""
        return self.calldata_modifier(bytes(self.pubkey))

    def with_source_address(
        self, source_address: Address
    ) -> "BuilderExitRequest":
        """Return a copy with the source address set."""
        return self.copy(source_address=source_address)

    @classmethod
    def from_index(cls, index: int) -> Self:
        """Build a builder exit request from a sequential index."""
        return cls(pubkey=index)
