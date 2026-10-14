"""Inclusion-list omission claims for fixtures."""

from collections.abc import Sequence

from pydantic import Field

from execution_testing.base_types import Bytes, CamelModel, Hash, HexNumber


class OmissionClaim(CamelModel):
    """Identify an omitted transaction and its claimed evaluation index."""

    transaction_hash: Hash
    evaluation_index: HexNumber = Field(ge=0, lt=2**64)


def validate_inclusion_list_metadata(
    inclusion_lists: Sequence[Sequence[Bytes]],
    claims: Sequence[OmissionClaim] = (),
) -> None:
    """Validate the Engine API container without executing transactions."""
    if len(claims) > 4096:
        raise ValueError("Too many omission claims")
    if len(inclusion_lists) != 16:
        raise ValueError("Expected one inclusion list per committee position")
    for transactions in inclusion_lists:
        if any(not transaction for transaction in transactions):
            raise ValueError("Empty inclusion-list transaction")
        if sum(map(len, transactions)) > 8192:
            raise ValueError("Inclusion list exceeds its byte limit")
