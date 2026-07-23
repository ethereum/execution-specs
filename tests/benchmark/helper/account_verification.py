"""Verification of snapshot-predeployed benchmark target accounts."""

from collections.abc import Callable, Hashable, Iterable
from dataclasses import dataclass

from execution_testing import Address, Alloc


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
        self, pre: Alloc, address: Address, *, label: str | None = None
    ) -> None:
        """
        Register verification expectation for address on pre-allocation.
        """
        pre.expect_account_state(
            address,
            is_existing_account=self.is_existing_account,
            is_contract=self.is_contract,
            min_balance=self.min_balance,
            code_prefix=self.code_prefix,
            label=label,
        )


def register_target_range(
    pre: Alloc,
    *,
    key: Hashable,
    count: int,
    expectation: AccountExpectation,
    addresses: Callable[[int, int], Iterable[Address]],
    verified_accounts: dict[Hashable, int],
    label: str | None = None,
    full: bool = False,
) -> None:
    """
    Register targets [0, count) for verification, deduped per family.
    """
    start = verified_accounts.get(key, 0)
    if count <= start:
        return
    if full or count - start <= 2:
        targets: Iterable[Address] = addresses(start, count)
    else:
        targets = [
            *addresses(start, start + 1),
            *addresses(count - 1, count),
        ]
    for address in targets:
        expectation.register(pre, address, label=label)
    verified_accounts[key] = count
