"""Test balance expectations resolved against transaction landings."""

from typing import Dict

import pytest

from execution_testing.base_types import Address

from ..account_types import EOA, Account, Alloc
from ..balance_expectations import (
    BalanceExpression,
    BlobFee,
    EmptyPostStateContext,
    GasFee,
    PostStateContext,
    Tip,
    TransactionKey,
    TransactionLanding,
    effective_gas_price,
    transaction_key,
)
from ..transaction_types import Transaction

SENDER = EOA(key=1)
FEE_RECIPIENT = Address(0xC0FFEE)
BASE_FEE = 7


def legacy_tx(*, nonce: int = 0, gas_price: int = 10) -> Transaction:
    """Return a legacy transaction from `SENDER`."""
    return Transaction(sender=SENDER, nonce=nonce, gas_price=gas_price)


def dynamic_fee_tx(
    *, nonce: int = 0, max_fee: int = 100, max_priority_fee: int = 3
) -> Transaction:
    """Return a dynamic fee transaction from `SENDER`."""
    return Transaction(
        sender=SENDER,
        nonce=nonce,
        max_fee_per_gas=max_fee,
        max_priority_fee_per_gas=max_priority_fee,
    )


class FixedTransactionLanding(TransactionLanding):
    """Landing with fixed pricing."""

    def __init__(
        self,
        *,
        effective_gas_price: int,
        base_fee_per_gas: int,
        blob_gas_price: int | None,
    ) -> None:
        """Store the pricing."""
        self.values = (effective_gas_price, base_fee_per_gas, blob_gas_price)

    def effective_gas_price(self) -> int:
        """Return the effective gas price."""
        return self.values[0]

    def base_fee_per_gas(self) -> int:
        """Return the base fee."""
        return self.values[1]

    def blob_gas_price(self) -> int | None:
        """Return the blob gas price."""
        return self.values[2]

    def fee_recipient(self) -> Address:
        """Return the fee recipient."""
        return FEE_RECIPIENT


class DictPostStateContext(PostStateContext):
    """Minimal context backed by a dictionary of landings."""

    def __init__(self, landings: Dict[TransactionKey, TransactionLanding]):
        """Store the landings."""
        self.landings = landings

    def landing(self, key: TransactionKey) -> TransactionLanding:
        """Return the landing of `key`."""
        if key not in self.landings:
            raise PostStateContext.TransactionNotLandedError(key)
        return self.landings[key]


def context_for(
    *txs: Transaction,
    base_fee_per_gas: int | None = BASE_FEE,
    blob_gas_price: int | None = None,
) -> PostStateContext:
    """Return a context where all `txs` landed in the same block."""
    base_fee = base_fee_per_gas or 0
    return DictPostStateContext(
        {
            transaction_key(tx): FixedTransactionLanding(
                effective_gas_price=effective_gas_price(tx, base_fee),
                base_fee_per_gas=base_fee,
                blob_gas_price=blob_gas_price,
            )
            for tx in txs
        }
    )


@pytest.mark.parametrize(
    ["tx", "base_fee_per_gas", "expected_cost", "expected_tip"],
    [
        pytest.param(legacy_tx(), 7, 210, 63, id="legacy"),
        pytest.param(legacy_tx(), None, 210, 210, id="legacy_pre_london"),
        pytest.param(dynamic_fee_tx(), 7, 100, 30, id="dynamic_fee_tip"),
        pytest.param(
            dynamic_fee_tx(max_fee=8), 7, 80, 10, id="dynamic_fee_capped"
        ),
    ],
)
def test_fee_terms(
    tx: Transaction,
    base_fee_per_gas: int | None,
    expected_cost: int,
    expected_tip: int,
) -> None:
    """Test that fee terms resolve against the landing base fee."""
    gas = 21 if tx.gas_price is not None else 10
    context = context_for(tx, base_fee_per_gas=base_fee_per_gas)
    assert GasFee(tx, gas=gas).resolve(context) == expected_cost
    assert Tip(tx, gas=gas).resolve(context) == expected_tip


def test_blob_cost() -> None:
    """Test that the blob fee uses the landing blob gas price."""
    tx = legacy_tx()
    context = context_for(tx, blob_gas_price=3)
    assert BlobFee(tx, blob_gas=131072).resolve(context) == 3 * 131072


def test_blob_cost_without_blob_pricing() -> None:
    """Test that a blob fee cannot resolve without blob gas pricing."""
    tx = legacy_tx()
    with pytest.raises(AssertionError):
        BlobFee(tx, blob_gas=1).resolve(context_for(tx))


def test_expression_arithmetic() -> None:
    """Test composing integers and terms into a linear expression."""
    tx_a = legacy_tx(nonce=0, gas_price=10)
    tx_b = legacy_tx(nonce=1, gas_price=20)
    context = context_for(tx_a, tx_b)

    expression = -1000 - GasFee(tx_a, gas=5) - 2 * GasFee(tx_b, gas=3)
    assert isinstance(expression, BalanceExpression)
    assert expression.resolve(context) == -1000 - 50 - 2 * 60

    tips = sum(Tip(tx, gas=1) for tx in (tx_a, tx_b))
    assert isinstance(tips, BalanceExpression)
    assert tips.resolve(context) == (10 - BASE_FEE) + (20 - BASE_FEE)

    assert (5 + GasFee(tx_a, gas=1) - 5).resolve(context) == 10
    assert (-(GasFee(tx_a, gas=1) - 1)).resolve(context) == -9


def test_expression_description() -> None:
    """Test that expressions describe their terms."""
    tx = legacy_tx()
    assert str(BalanceExpression.of(0)) == "0"
    assert str(-GasFee(tx, gas=5)) == (
        f"-GasFee(tx {Address(SENDER)} nonce 0, gas=5)"
    )
    assert str(100 - 2 * Tip(tx, gas=1)) == (
        f"100 - 2 * Tip(tx {Address(SENDER)} nonce 0, gas=1)"
    )


def test_transaction_identity_survives_copies() -> None:
    """Test that a term resolves against a modified, signed copy."""
    tx = legacy_tx()
    landed = tx.copy(gas_limit=50_000).with_signature_and_sender()
    context = context_for(landed)
    assert GasFee(tx, gas=1).resolve(context) == 10


def test_transaction_not_landed() -> None:
    """Test that a term for a transaction that never landed fails."""
    with pytest.raises(PostStateContext.TransactionNotLandedError):
        GasFee(legacy_tx(), gas=1).resolve(EmptyPostStateContext())


def test_account_balance_change_resolves() -> None:
    """Test `Account.check_alloc` with a fee-dependent balance change."""
    tx = legacy_tx()
    context = context_for(tx)
    expected = Account(balance_change=-1 - GasFee(tx, gas=21_000))
    pre = Account(balance=10**18)
    post = Account(balance=10**18 - 1 - 21_000 * 10)
    expected.check_alloc(
        address=Address(1), pre_account=pre, account=post, context=context
    )
    with pytest.raises(Account.BalanceMismatchError, match="GasFee"):
        expected.check_alloc(
            address=Address(1),
            pre_account=pre,
            account=Account(balance=10**18),
            context=context,
        )


def test_account_integer_balance_change() -> None:
    """Test that integer changes still work, relative to an empty pre."""
    expected = Account(balance_change=5, nonce_change=1)
    expected.check_alloc(
        address=Address(1),
        pre_account=None,
        account=Account(balance=5, nonce=1),
        context=EmptyPostStateContext(),
    )


def test_account_absolute_and_relative_are_exclusive() -> None:
    """Test that an absolute value and a change cannot both be expected."""
    with pytest.raises(ValueError, match="mutually exclusive"):
        Account(balance=1, balance_change=1)
    with pytest.raises(ValueError, match="mutually exclusive"):
        Account(nonce=1, nonce_change=1)


def test_verify_post_alloc_with_context() -> None:
    """Test `Alloc.verify_post_alloc` resolving changes for two accounts."""
    tx = legacy_tx()
    context = context_for(tx)
    sender_address = Address(SENDER)
    pre = Alloc({sender_address: Account(balance=10**18)})
    post = Alloc(
        {
            sender_address: Account(
                nonce_change=1, balance_change=-GasFee(tx, gas=21_000)
            ),
            FEE_RECIPIENT: Account(balance_change=Tip(tx, gas=21_000)),
        }
    )
    got = Alloc(
        {
            sender_address: Account(nonce=1, balance=10**18 - 210_000),
            FEE_RECIPIENT: Account(balance=21_000 * (10 - BASE_FEE)),
        }
    )
    post.verify_post_alloc(pre_alloc=pre, got_alloc=got, context=context)


def test_tip_on_account_other_than_fee_recipient() -> None:
    """Test that a tip is only accepted on the block's fee recipient."""
    tx = legacy_tx()
    expected = Account(balance_change=Tip(tx, gas=21_000))
    with pytest.raises(Tip.WrongRecipientError):
        expected.check_alloc(
            address=Address(1),
            pre_account=None,
            account=Account(balance=21_000 * (10 - BASE_FEE)),
            context=context_for(tx),
        )


def test_empty_context() -> None:
    """Test that a fee term cannot resolve in an empty context."""
    expected = Account(balance_change=-GasFee(legacy_tx(), gas=1))
    with pytest.raises(PostStateContext.TransactionNotLandedError):
        expected.check_alloc(
            address=Address(1),
            pre_account=Account(balance=10),
            account=Account(balance=0),
            context=EmptyPostStateContext(),
        )


@pytest.mark.parametrize(
    ["expected", "pre_account", "error"],
    [
        pytest.param(Account(balance_change=0), None, None, id="zero_change"),
        pytest.param(
            Account(balance_change=0, nonce_change=0),
            None,
            None,
            id="zero_balance_and_nonce_change",
        ),
        pytest.param(
            Account(balance_change=1),
            None,
            Account.BalanceMismatchError,
            id="nonzero_change",
        ),
        pytest.param(
            Account(balance_change=0),
            Account(balance=1),
            Alloc.MissingAccountError,
            id="non_empty_pre",
        ),
        pytest.param(
            Account(balance=0),
            None,
            Alloc.MissingAccountError,
            id="absolute_expectation",
        ),
    ],
)
def test_missing_account_with_relative_expectation(
    expected: Account,
    pre_account: Account | None,
    error: type[Exception] | None,
) -> None:
    """Test a post account that is absent from the resulting allocation."""
    address = Address(0x1234)
    pre = Alloc({address: pre_account} if pre_account is not None else {})
    post = Alloc({address: expected})
    if error is None:
        post.verify_post_alloc(
            pre_alloc=pre, got_alloc=Alloc(), context=EmptyPostStateContext()
        )
    else:
        with pytest.raises(error):
            post.verify_post_alloc(
                pre_alloc=pre,
                got_alloc=Alloc(),
                context=EmptyPostStateContext(),
            )
