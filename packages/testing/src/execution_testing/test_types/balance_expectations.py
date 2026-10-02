"""
Balance expectations that resolve against where transactions landed.

A post-state `Account` can express its balance as a change relative to the
pre-state (`balance_change`). Most such changes are plain integers (value
transfers), but fees depend on the block in which a transaction was included:
its base fee, its blob gas price and its fee recipient. Those quantities are
expressed as terms (`GasCost`, `Tip`, `BlobCost`) which compose with integers
into a `BalanceExpression`:

```python
Account(balance_change=-value - GasCost(tx, gas=gas_used))
Account(balance_change=Tip(tx_a, gas=gas_a) + Tip(tx_b, gas=gas_b))
```

The expression is resolved when the post-state is verified, using a
`PostStateContext` that maps every included transaction to its
`TransactionLanding`. The gas amounts are always supplied by the test, never
read back from execution results, so the expectation remains an independent
check of the specification.

Gathering landings can be costly (in execute mode it takes several RPC
calls), so the context is only built when some expectation contains a fee
term; plain integer changes resolve without it.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Dict, Tuple

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
    return (Address(sender), int(tx.nonce))


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


@dataclass(frozen=True, kw_only=True)
class TransactionLanding:
    """Pricing of the block in which a transaction was included."""

    effective_gas_price: int
    base_fee_per_gas: int
    blob_gas_price: int | None
    fee_recipient: Address


@dataclass(kw_only=True)
class PostStateContext:
    """Landings of the transactions executed before a post-state check."""

    landings: Dict[TransactionKey, TransactionLanding] = field(
        default_factory=dict
    )

    class TransactionNotLandedError(Exception):
        """An expectation referenced a transaction that was not included."""

    def add_landing(
        self,
        tx: "Transaction",
        *,
        base_fee_per_gas: int | None,
        blob_gas_price: int | None,
        fee_recipient: Address,
        effective_gas_price_override: int | None = None,
    ) -> None:
        """
        Record that `tx` was included in a block with the given pricing.

        Before the London fork there is no base fee, which is equivalent to a
        base fee of zero: the fee recipient receives the whole gas price.
        """
        base_fee = int(base_fee_per_gas) if base_fee_per_gas else 0
        price = (
            effective_gas_price_override
            if effective_gas_price_override is not None
            else effective_gas_price(tx, base_fee)
        )
        self.landings[transaction_key(tx)] = TransactionLanding(
            effective_gas_price=price,
            base_fee_per_gas=base_fee,
            blob_gas_price=blob_gas_price,
            fee_recipient=fee_recipient,
        )

    def landing(self, key: TransactionKey) -> TransactionLanding:
        """Return the landing of the transaction identified by `key`."""
        if key not in self.landings:
            sender, nonce = key
            raise PostStateContext.TransactionNotLandedError(
                f"transaction from {sender} with nonce {nonce} was not "
                "included in any block, so its fees cannot be resolved"
            )
        return self.landings[key]


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


class GasCost(BalanceTerm):
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
        return self.gas * context.landing(self.key).effective_gas_price

    def __str__(self) -> str:
        """Describe the term."""
        return f"GasCost({self._transaction_label()}, gas={self.gas})"


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

    def resolve(self, context: PostStateContext) -> int:
        """Return the priority fee in wei."""
        landing = context.landing(self.key)
        return self.gas * (
            landing.effective_gas_price - landing.base_fee_per_gas
        )

    def __str__(self) -> str:
        """Describe the term."""
        return f"Tip({self._transaction_label()}, gas={self.gas})"


class BlobCost(BalanceTerm):
    """Blob fee paid by the sender: `blob_gas × blob_gas_price`."""

    blob_gas: int

    def __init__(self, tx: "Transaction", *, blob_gas: int) -> None:
        """Create the term for `blob_gas` units consumed by `tx`."""
        super().__init__(tx)
        self.blob_gas = blob_gas

    def resolve(self, context: PostStateContext) -> int:
        """Return the blob fee in wei."""
        blob_gas_price = context.landing(self.key).blob_gas_price
        assert blob_gas_price is not None, (
            f"{self._transaction_label()} landed in a block without blob "
            "gas pricing"
        )
        return self.blob_gas * blob_gas_price

    def __str__(self) -> str:
        """Describe the term."""
        return (
            f"BlobCost({self._transaction_label()}, blob_gas={self.blob_gas})"
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

    @property
    def requires_context(self) -> bool:
        """Return whether resolving needs a `PostStateContext`."""
        return len(self.terms) > 0

    def resolve(self, context: PostStateContext | None) -> int:
        """
        Return the value of the expression in `context`.

        `context` may be `None` only when the expression has no fee terms.
        """
        if not self.terms:
            return self.constant
        assert context is not None, (
            f"balance expectation `{self}` requires a post-state context, "
            "but none was built; the framework should have detected this "
            "with `Alloc.requires_post_state_context()`"
        )
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
        """Describe the expression, e.g. `-1000 - GasCost(...)`."""
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
