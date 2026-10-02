"""Test balance expectations resolved against transaction landings."""

import pytest

from execution_testing.base_types import Address

from ..account_types import EOA, Account, Alloc
from ..balance_expectations import (
    BalanceExpression,
    BlobCost,
    GasCost,
    PostStateContext,
    Tip,
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


def context_for(
    *txs: Transaction,
    base_fee_per_gas: int | None = BASE_FEE,
    blob_gas_price: int | None = None,
) -> PostStateContext:
    """Return a context where all `txs` landed in the same block."""
    context = PostStateContext()
    for tx in txs:
        context.add_landing(
            tx,
            base_fee_per_gas=base_fee_per_gas,
            blob_gas_price=blob_gas_price,
            fee_recipient=FEE_RECIPIENT,
        )
    return context


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
    assert GasCost(tx, gas=gas).resolve(context) == expected_cost
    assert Tip(tx, gas=gas).resolve(context) == expected_tip


def test_blob_cost() -> None:
    """Test that the blob fee uses the landing blob gas price."""
    tx = legacy_tx()
    context = context_for(tx, blob_gas_price=3)
    assert BlobCost(tx, blob_gas=131072).resolve(context) == 3 * 131072


def test_blob_cost_without_blob_pricing() -> None:
    """Test that a blob fee cannot resolve without blob gas pricing."""
    tx = legacy_tx()
    with pytest.raises(AssertionError):
        BlobCost(tx, blob_gas=1).resolve(context_for(tx))


def test_expression_arithmetic() -> None:
    """Test composing integers and terms into a linear expression."""
    tx_a = legacy_tx(nonce=0, gas_price=10)
    tx_b = legacy_tx(nonce=1, gas_price=20)
    context = context_for(tx_a, tx_b)

    expression = -1000 - GasCost(tx_a, gas=5) - 2 * GasCost(tx_b, gas=3)
    assert isinstance(expression, BalanceExpression)
    assert expression.resolve(context) == -1000 - 50 - 2 * 60

    tips = sum(Tip(tx, gas=1) for tx in (tx_a, tx_b))
    assert isinstance(tips, BalanceExpression)
    assert tips.resolve(context) == (10 - BASE_FEE) + (20 - BASE_FEE)

    assert (5 + GasCost(tx_a, gas=1) - 5).resolve(context) == 10
    assert (-(GasCost(tx_a, gas=1) - 1)).resolve(context) == -9


def test_expression_description() -> None:
    """Test that expressions describe their terms."""
    tx = legacy_tx()
    assert str(BalanceExpression.of(0)) == "0"
    assert str(-GasCost(tx, gas=5)) == (
        f"-GasCost(tx {Address(SENDER)} nonce 0, gas=5)"
    )
    assert str(100 - 2 * Tip(tx, gas=1)) == (
        f"100 - 2 * Tip(tx {Address(SENDER)} nonce 0, gas=1)"
    )


def test_transaction_identity_survives_copies() -> None:
    """Test that a term resolves against a modified, signed copy."""
    tx = legacy_tx()
    landed = tx.copy(gas_limit=50_000).with_signature_and_sender()
    context = context_for(landed)
    assert GasCost(tx, gas=1).resolve(context) == 10


def test_transaction_not_landed() -> None:
    """Test that a term for a transaction that never landed fails."""
    with pytest.raises(PostStateContext.TransactionNotLandedError):
        GasCost(legacy_tx(), gas=1).resolve(PostStateContext())


def test_account_balance_change_resolves() -> None:
    """Test `Account.check_alloc` with a fee-dependent balance change."""
    tx = legacy_tx()
    context = context_for(tx)
    expected = Account(balance_change=-1 - GasCost(tx, gas=21_000))
    pre = Account(balance=10**18)
    post = Account(balance=10**18 - 1 - 21_000 * 10)
    expected.check_alloc(
        address=Address(1), pre_account=pre, account=post, context=context
    )
    with pytest.raises(Account.BalanceMismatchError, match="GasCost"):
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
                nonce_change=1, balance_change=-GasCost(tx, gas=21_000)
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


def test_requires_post_state_context() -> None:
    """Test detecting whether a post-state needs a context."""
    tx = legacy_tx()
    assert not Alloc(
        {
            Address(1): Account(balance_change=5, nonce_change=1),
            Address(2): Account(balance=1),
            Address(3): None,
        }
    ).requires_post_state_context()
    assert Alloc(
        {
            Address(1): Account(balance_change=5),
            Address(2): Account(balance_change=-GasCost(tx, gas=1)),
        }
    ).requires_post_state_context()


def test_missing_required_context() -> None:
    """Test that a fee term without a context fails loudly."""
    expected = Account(balance_change=-GasCost(legacy_tx(), gas=1))
    with pytest.raises(AssertionError, match="requires a post-state context"):
        expected.check_alloc(
            address=Address(1),
            pre_account=Account(balance=10),
            account=Account(balance=0),
        )
