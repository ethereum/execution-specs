"""
Balance expectations that resolve against where transactions landed.

A post-state `Account` can express its balance as a change relative to the
pre-state (`balance_change`). Most such changes are plain integers (value
transfers), but fees depend on the block in which a transaction was included:
its base fee, its blob gas price and its fee recipient. Those quantities are
expressed as terms (`GasFee`, `Tip`, `BlobFee`) which compose with integers
into a `BalanceExpression`:

```python
Account(balance_change=-value - GasFee(tx, gas=gas_used))
Account(balance_change=Tip(tx_a, gas=gas_a) + Tip(tx_b, gas=gas_b))
```

The expression is resolved when the post-state is verified, using a
`PostStateContext` that maps every included transaction to its
`TransactionLanding`. The gas amounts are always supplied by the test, never
read back from execution results, so the expectation remains an independent
check of the specification.

Gathering landings never costs more than the expectations need: each
context implementation obtains landing data only when a term asks for it.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Tuple

from pydantic import GetCoreSchemaHandler
from pydantic_core import CoreSchema, core_schema

from execution_testing.base_types import Address

if TYPE_CHECKING:
    from .transaction_types import Transaction

TransactionKey = Tuple[Address, int]
"""
Identify a transaction by its `(sender, nonce)` pair.

The pair is stable across the copies the framework makes of a transaction
(gas limit adjustment, signing), unlike the transaction hash.
"""


def transaction_key(tx: "Transaction") -> TransactionKey:
    """Return the `(sender, nonce)` pair that identifies `tx`."""
    sender = tx.sender
    if sender is None:
        sender = tx.with_signature_and_sender().sender
    assert sender is not None, "unable to determine transaction sender"
    return Address(sender), int(tx.nonce)


def effective_gas_price(tx: "Transaction", base_fee_per_gas: int) -> int:
    """Return the price per gas that `tx` pays given the block base fee."""
    if tx.gas_price is not None:
        return int(tx.gas_price)
    assert tx.max_fee_per_gas is not None
    assert tx.max_priority_fee_per_gas is not None
    return min(
        int(tx.max_fee_per_gas),
        base_fee_per_gas + int(tx.max_priority_fee_per_gas),
    )


class TransactionLanding(ABC):
    """
    Pricing of the block in which a transaction was included.

    Each value is a method so that implementations can obtain it lazily:
    execute fetches only what the expectations being resolved require.
    """

    @abstractmethod
    def effective_gas_price(self) -> int:
        """Return the price per gas the transaction paid."""

    @abstractmethod
    def base_fee_per_gas(self) -> int:
        """Return the block base fee, or zero before the London fork."""

    @abstractmethod
    def blob_gas_price(self) -> int | None:
        """Return the block blob gas price, if blobs are supported."""

    @abstractmethod
    def fee_recipient(self) -> Address:
        """Return the block fee recipient."""


class PostStateContext(ABC):
    """
    Source of transaction landings for resolving post-state expectations.

    Each test format provides its own implementation: filled tests record
    landings while building blocks, while execute fetches them from the
    network on demand.
    """

    class TransactionNotLandedError(Exception):
        """An expectation referenced a transaction that was not included."""

        def __init__(self, key: TransactionKey) -> None:
            """Initialize the exception for the transaction `key`."""
            sender, nonce = key
            super().__init__(
                f"transaction from {sender} with nonce {nonce} was not "
                "included in any block, so its fees cannot be resolved"
            )

    @abstractmethod
    def landing(self, key: TransactionKey) -> TransactionLanding:
        """
        Return the landing of the transaction identified by `key`.

        Raise `TransactionNotLandedError` if it was not included.
        """


class EmptyPostStateContext(PostStateContext):
    """
    Context in which no transaction landed.

    Used where an allocation is verified without executing transactions;
    any fee term resolved against it fails as not landed.
    """

    def landing(self, key: TransactionKey) -> TransactionLanding:
        """Raise, since no transaction landed."""
        raise PostStateContext.TransactionNotLandedError(key)


class BalanceTerm(ABC):
    """A balance quantity that depends on where a transaction landed."""

    key: TransactionKey

    def __init__(self, tx: "Transaction") -> None:
        """Identify the transaction this term is resolved against."""
        self.key = transaction_key(tx)

    @abstractmethod
    def resolve(self, context: PostStateContext) -> int:
        """Return the value of the term in `context`."""

    def _transaction_label(self) -> str:
        sender, nonce = self.key
        label = f" ({sender.label})" if sender.label is not None else ""
        return f"tx {sender}{label} nonce {nonce}"

    def __add__(self, other: "BalanceChangeType") -> "BalanceExpression":
        """Return `self + other`."""
        return BalanceExpression.of(self) + other

    def __radd__(self, other: "BalanceChangeType") -> "BalanceExpression":
        """Return `other + self`."""
        return BalanceExpression.of(other) + self

    def __sub__(self, other: "BalanceChangeType") -> "BalanceExpression":
        """Return `self - other`."""
        return BalanceExpression.of(self) - other

    def __rsub__(self, other: "BalanceChangeType") -> "BalanceExpression":
        """Return `other - self`."""
        return BalanceExpression.of(other) - self

    def __neg__(self) -> "BalanceExpression":
        """Return `-self`."""
        return -BalanceExpression.of(self)

    def __mul__(self, factor: int) -> "BalanceExpression":
        """Return `self * factor`."""
        return BalanceExpression.of(self) * factor

    def __rmul__(self, factor: int) -> "BalanceExpression":
        """Return `factor * self`."""
        return BalanceExpression.of(self) * factor


class GasFee(BalanceTerm):
    """
    Fee paid by the sender for `gas` units: `gas × effective_gas_price`.

    Use a negative sign for the sender's balance change, since the fee is
    deducted from it.
    """

    gas: int

    def __init__(self, tx: "Transaction", *, gas: int) -> None:
        """Create the term for `gas` units consumed by `tx`."""
        super().__init__(tx)
        self.gas = gas

    def resolve(self, context: PostStateContext) -> int:
        """Return the fee in wei."""
        return self.gas * context.landing(self.key).effective_gas_price()

    def __str__(self) -> str:
        """Describe the term."""
        return f"GasFee({self._transaction_label()}, gas={self.gas})"


class Tip(BalanceTerm):
    """
    Priority fee received by the fee recipient for `gas` units.

    Equal to `gas × (effective_gas_price - base_fee_per_gas)`; the base fee
    portion is burned.
    """

    gas: int

    def __init__(self, tx: "Transaction", *, gas: int) -> None:
        """Create the term for `gas` units consumed by `tx`."""
        super().__init__(tx)
        self.gas = gas

    class WrongRecipientError(Exception):
        """A tip was expected on an account that is not the fee recipient."""

    def resolve(self, context: PostStateContext) -> int:
        """Return the priority fee in wei."""
        landing = context.landing(self.key)
        return self.gas * (
            landing.effective_gas_price() - landing.base_fee_per_gas()
        )

    def check_recipient(
        self, recipient: Address, context: PostStateContext
    ) -> None:
        """
        Raise unless `recipient` is the fee recipient of the block in which
        the transaction landed.
        """
        fee_recipient = context.landing(self.key).fee_recipient()
        if fee_recipient != recipient:
            raise Tip.WrongRecipientError(
                f"{self} is expected on {recipient}, but the transaction "
                f"landed in a block whose fee recipient is {fee_recipient}"
            )

    def __str__(self) -> str:
        """Describe the term."""
        return f"Tip({self._transaction_label()}, gas={self.gas})"


class BlobFee(BalanceTerm):
    """Blob fee paid by the sender: `blob_gas × blob_gas_price`."""

    blob_gas: int

    def __init__(self, tx: "Transaction", *, blob_gas: int) -> None:
        """Create the term for `blob_gas` units consumed by `tx`."""
        super().__init__(tx)
        self.blob_gas = blob_gas

    def resolve(self, context: PostStateContext) -> int:
        """Return the blob fee in wei."""
        blob_gas_price = context.landing(self.key).blob_gas_price()
        assert blob_gas_price is not None, (
            f"{self._transaction_label()} landed in a block without blob "
            "gas pricing"
        )
        return self.blob_gas * blob_gas_price

    def __str__(self) -> str:
        """Describe the term."""
        return (
            f"BlobFee({self._transaction_label()}, blob_gas={self.blob_gas})"
        )


@dataclass(frozen=True)
class BalanceExpression:
    """
    Linear combination of balance terms: `constant + Σ factor × term`.

    Integers and terms are lifted into expressions by the arithmetic
    operators, so expressions are rarely constructed directly.
    """

    constant: int = 0
    terms: Tuple[Tuple[int, BalanceTerm], ...] = ()

    @classmethod
    def of(cls, value: "BalanceChangeType") -> "BalanceExpression":
        """Lift an integer, term or expression into an expression."""
        if isinstance(value, BalanceExpression):
            return value
        if isinstance(value, BalanceTerm):
            return cls(terms=((1, value),))
        if isinstance(value, str):
            return cls(constant=int(value, 0))
        return cls(constant=int(value))

    def resolve(self, context: PostStateContext) -> int:
        """Return the value of the expression in `context`."""
        return self.constant + sum(
            factor * term.resolve(context) for factor, term in self.terms
        )

    def __add__(self, other: "BalanceChangeType") -> "BalanceExpression":
        """Return `self + other`."""
        other = BalanceExpression.of(other)
        return BalanceExpression(
            self.constant + other.constant, self.terms + other.terms
        )

    def __radd__(self, other: "BalanceChangeType") -> "BalanceExpression":
        """Return `other + self`; also lets `sum()` start from zero."""
        return BalanceExpression.of(other) + self

    def __neg__(self) -> "BalanceExpression":
        """Return `-self`."""
        return self * -1

    def __sub__(self, other: "BalanceChangeType") -> "BalanceExpression":
        """Return `self - other`."""
        return self + -BalanceExpression.of(other)

    def __rsub__(self, other: "BalanceChangeType") -> "BalanceExpression":
        """Return `other - self`."""
        return BalanceExpression.of(other) + -self

    def __mul__(self, factor: int) -> "BalanceExpression":
        """Return `self * factor`."""
        return BalanceExpression(
            self.constant * factor,
            tuple((f * factor, term) for f, term in self.terms),
        )

    def __rmul__(self, factor: int) -> "BalanceExpression":
        """Return `factor * self`."""
        return self * factor

    def __bool__(self) -> bool:
        """Return whether the expression is anything other than zero."""
        return self.constant != 0 or len(self.terms) > 0

    def __str__(self) -> str:
        """Describe the expression, e.g. `-1000 - GasFee(...)`."""
        parts: list[str] = []
        if self.constant != 0 or not self.terms:
            parts.append(str(self.constant))
        for factor, term in self.terms:
            sign = "-" if factor < 0 else "+"
            magnitude = abs(factor)
            text = str(term) if magnitude == 1 else f"{magnitude} * {term}"
            if not parts:
                parts.append(text if sign == "+" else f"-{text}")
            else:
                parts.append(f"{sign} {text}")
        return " ".join(parts)

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        """Accept integers, terms and expressions, normalized on input."""
        del source_type, handler
        return core_schema.no_info_plain_validator_function(cls.of)


BalanceChangeType = int | str | BalanceTerm | BalanceExpression
"""Values accepted wherever a balance change is expected."""
