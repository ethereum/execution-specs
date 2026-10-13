"""Inclusion-list omission claims for fixtures."""

from collections.abc import Sequence

from pydantic import Field

from execution_testing.base_types import Bytes, CamelModel, Hash, HexNumber


class InclusionListClaim(CamelModel):
    """Identify an omitted transaction and its claimed evaluation index."""

    transaction_hash: Hash
    evaluation_index: HexNumber = Field(ge=0, lt=2**64)


def validate_inclusion_list_metadata(
    transactions: Sequence[Bytes],
    membership: Sequence[Bytes],
    claims: Sequence[InclusionListClaim] = (),
) -> None:
    """Validate the Engine API container without executing transactions."""
    if len(claims) > 4096:
        raise ValueError("Too many inclusion-list claims")
    if len(transactions) != len(membership):
        raise ValueError("Membership length differs from transaction count")
    if any(not transaction for transaction in transactions):
        raise ValueError("Empty inclusion-list transaction")
    if len(set(transactions)) != len(transactions):
        raise ValueError("Duplicate inclusion-list transaction")
    totals = [0] * 16
    for transaction, members in zip(transactions, membership, strict=True):
        if len(members) != 2 or not any(members):
            raise ValueError("Membership must be a nonzero 2-byte bitvector")
        bits = int.from_bytes(members, "little")
        for position in range(16):
            if bits & (1 << position):
                totals[position] += len(transaction)
                if totals[position] > 8192:
                    raise ValueError("Inclusion list exceeds its byte limit")
