"""Verification of snapshot-predeployed benchmark target accounts."""

from collections.abc import Callable, Hashable, Sequence
from dataclasses import dataclass
from typing import overload

from execution_testing import Address, Alloc


class AddressRange(Sequence[Address]):
    """
    Lazily-indexed range of target addresses.

    Backed by an index -> Address map, so sampling the endpoints costs
    O(1): checking only the first and last of a huge range never derives
    the addresses in between.
    """

    def __init__(
        self, start: int, stop: int, address_of: Callable[[int], Address]
    ) -> None:
        """Cover indices ``[start, stop)`` via ``address_of``."""
        self._start = start
        self._stop = stop
        self._address_of = address_of

    def __len__(self) -> int:
        """Return the number of addresses in the range."""
        return self._stop - self._start

    @overload
    def __getitem__(self, index: int) -> Address: ...

    @overload
    def __getitem__(self, index: slice) -> Sequence[Address]: ...

    def __getitem__(self, index: int | slice) -> Address | Sequence[Address]:
        """Derive the address at ``index`` (negatives and slices allowed)."""
        if isinstance(index, slice):
            return [self[i] for i in range(*index.indices(len(self)))]
        if index < 0:
            index += len(self)
        if not 0 <= index < len(self):
            raise IndexError(index)
        return self._address_of(self._start + index)


@dataclass(frozen=True)
class AccountExpectation:
    """
    Expected on-chain shape of a snapshot-predeployed target.

    Verified at `start_block`. Defaults skipped.
    `is_contract`: nonce >= 1. CREATE2: address binds code.
    `code_prefix`: on-chain code must start with given bytes.
    """

    is_existing_account: bool = True
    is_contract: bool = False
    min_balance: int | None = None
    code_prefix: bytes | None = None

    def register(
        self, pre: Alloc, addresses: Address | Sequence[Address]
    ) -> None:
        """Register this expectation for one address or a range."""
        pre.expect_account_state(
            addresses,
            is_existing_account=self.is_existing_account,
            is_contract=self.is_contract,
            min_balance=self.min_balance,
            code_prefix=self.code_prefix,
        )


def register_target_range(
    pre: Alloc,
    *,
    key: Hashable,
    count: int,
    expectation: AccountExpectation,
    address_of: Callable[[int], Address],
    verified_accounts: dict[Hashable, int],
) -> None:
    """
    Register targets ``[0, count)`` for verification, deduped per family.

    Only the newly-seen tail ``[high-water, count)`` is handed to the
    allocation; whether it samples the endpoints or checks every account
    is decided there, from ``--verify-full-accounts``.
    """
    start = verified_accounts.get(key, 0)
    if count <= start:
        return
    expectation.register(pre, AddressRange(start, count, address_of))
    verified_accounts[key] = count
