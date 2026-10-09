"""Post-state verification model for tracking fill-time checks."""

from __future__ import annotations

from typing import TYPE_CHECKING, Dict, Mapping

from execution_testing.base_types import (
    Address,
    Bytes,
    CamelModel,
    ZeroPaddedHexNumber,
)

if TYPE_CHECKING:
    from execution_testing.base_types import Alloc


class AccountCheck(CamelModel):
    """
    Capture which fields are verified for a single account.

    A ``None`` value means the field is not checked (it was not
    explicitly set by the test author).  A present value records the
    expected value that ``check_alloc`` would assert against.
    """

    nonce: ZeroPaddedHexNumber | None = None
    balance: ZeroPaddedHexNumber | None = None
    code: Bytes | None = None
    storage: Mapping[ZeroPaddedHexNumber, ZeroPaddedHexNumber] | None = None


class PostVerifications(CamelModel):
    """
    Record every post-state check performed during a fill session.

    Accounts mapped to ``None`` represent *should-not-exist* checks.
    """

    accounts: Dict[Address, AccountCheck | None]

    @classmethod
    def from_alloc(cls, alloc: Alloc) -> PostVerifications:
        """
        Derive verification checks from an expected post ``Alloc``.

        Walk each address/account pair and inspect
        ``model_fields_set`` to determine which fields will actually
        be compared by ``Account.check_alloc``.
        """
        accounts: Dict[Address, AccountCheck | None] = {}
        for address, account in alloc.root.items():
            if account is None:
                accounts[address] = None
                continue
            storage_checked = "storage" in account.model_fields_set
            storage: Mapping[ZeroPaddedHexNumber, ZeroPaddedHexNumber] | None
            if not storage_checked:
                storage = None
            elif account.storage is None:
                # Storage.EMPTY: storage must be completely empty.
                storage = {}
            else:
                storage = dict(account.storage.root)  # type: ignore[arg-type]
            accounts[address] = AccountCheck(
                nonce=(
                    account.nonce
                    if "nonce" in account.model_fields_set
                    else None
                ),
                balance=(
                    account.balance
                    if "balance" in account.model_fields_set
                    else None
                ),
                code=(
                    account.code
                    if "code" in account.model_fields_set
                    else None
                ),
                storage=storage,
            )
        return cls(accounts=accounts)
