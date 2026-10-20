"""
Test fee caps that do not fit in 64 or 128 bits under EIP-1559.

EIP-1559 only requires `max_fee_per_gas` to be below 2**256, so wider caps are
valid whenever the sender's balance covers them.
"""

import pytest
from execution_testing import (
    EOA,
    Account,
    Alloc,
    Environment,
    Fork,
    Op,
    StateTestFiller,
    Transaction,
    TransactionException,
)

from .spec import ref_spec_1559

REFERENCE_SPEC_GIT_PATH = ref_spec_1559.git_path
REFERENCE_SPEC_VERSION = ref_spec_1559.version

BASE_FEE_PER_GAS = 7
# Any limit that covers the call; the balance check multiplies it by the cap.
GAS_LIMIT = 1_000_000
MAX_BALANCE = 2**256 - 1

pytestmark = [
    pytest.mark.valid_from("London"),
    pytest.mark.with_all_typed_transactions(
        selector=lambda tx_type: tx_type >= 2,
    ),
    pytest.mark.execute(
        pytest.mark.skip(reason="Needs balances above any live chain's supply")
    ),
]


@pytest.fixture
def sender(pre: Alloc) -> EOA:
    """Return a sender funded only once the transaction's cost is known."""
    return pre.fund_eoa(amount=0)


@pytest.mark.parametrize(
    "fee_cap",
    [
        pytest.param(2**64 - 1, id="u64_max"),
        pytest.param(2**64, id="u64_max_plus_one"),
        pytest.param(2**128 - 1, id="u128_max"),
        pytest.param(2**128, id="u128_max_plus_one"),
    ],
)
@pytest.mark.parametrize("tip", ["one_wei", "equal_to_fee_cap"])
@pytest.mark.parametrize(
    "funding",
    [
        pytest.param("exact"),
        pytest.param("one_wei_short", marks=pytest.mark.exception_test),
    ],
)
def test_wide_fee_cap(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    sender: EOA,
    typed_transaction: Transaction,
    fee_cap: int,
    tip: str,
    funding: str,
) -> None:
    """
    Test fee caps on each side of the 64-bit and 128-bit limits.

    GASPRICE reads the effective gas price, and the balance check covers the
    full fee cap.
    """
    if tip == "one_wei":
        max_priority_fee_per_gas = 1
    elif tip == "equal_to_fee_cap":
        max_priority_fee_per_gas = fee_cap
    else:
        raise ValueError(f"Unknown tip: {tip}")

    if funding == "exact":
        shortfall = 0
        error = None
    elif funding == "one_wei_short":
        shortfall = 1
        error = TransactionException.INSUFFICIENT_ACCOUNT_FUNDS
    else:
        raise ValueError(f"Unknown funding: {funding}")

    witness = pre.deploy_contract(Op.SSTORE(0, Op.GASPRICE))
    tx = typed_transaction.copy(
        to=witness,
        gas_limit=GAS_LIMIT,
        max_fee_per_gas=fee_cap,
        max_priority_fee_per_gas=max_priority_fee_per_gas,
        error=error,
    )
    pre.fund_address(sender, tx.signer_minimum_balance(fork=fork) - shortfall)

    if error is None:
        effective_gas_price = min(
            fee_cap, BASE_FEE_PER_GAS + max_priority_fee_per_gas
        )
        post = {
            witness: Account(storage={0: effective_gas_price}),
            sender: Account(nonce=tx.nonce + 1),
        }
    else:
        post = {
            witness: Account(storage={}),
            sender: Account(nonce=tx.nonce),
        }

    state_test(
        env=Environment(base_fee_per_gas=BASE_FEE_PER_GAS),
        pre=pre,
        post=post,
        tx=tx,
    )


@pytest.mark.parametrize(
    "above_largest",
    [
        pytest.param(False, id="largest_affordable"),
        pytest.param(True, id="one_above", marks=pytest.mark.exception_test),
    ],
)
def test_fee_cap_at_balance_limit(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    sender: EOA,
    typed_transaction: Transaction,
    above_largest: bool,
) -> None:
    """
    Test the largest fee cap a 256-bit balance covers, and one above it.
    """
    max_priority_fee_per_gas = 1
    witness = pre.deploy_contract(Op.SSTORE(0, Op.GASPRICE))
    tx = typed_transaction.copy(
        to=witness,
        gas_limit=GAS_LIMIT,
        max_priority_fee_per_gas=max_priority_fee_per_gas,
    )
    # The value and any blob fee, which the fee cap does not scale.
    other_costs = tx.copy(max_fee_per_gas=0).signer_minimum_balance(fork=fork)
    largest_fee_cap = (MAX_BALANCE - other_costs) // tx.gas_limit

    if above_largest:
        # No balance covers this cost, so a client may reject it as an
        # overflow before it reads the balance.
        tx = tx.copy(
            max_fee_per_gas=largest_fee_cap + 1,
            error=[
                TransactionException.INSUFFICIENT_ACCOUNT_FUNDS,
                TransactionException.GASLIMIT_PRICE_PRODUCT_OVERFLOW,
            ],
        )
        assert tx.signer_minimum_balance(fork=fork) > MAX_BALANCE
        pre.fund_address(sender, MAX_BALANCE)
        post = {
            witness: Account(storage={}),
            sender: Account(nonce=tx.nonce),
        }
    else:
        tx = tx.copy(max_fee_per_gas=largest_fee_cap)
        upfront_cost = tx.signer_minimum_balance(fork=fork)
        assert upfront_cost <= MAX_BALANCE
        pre.fund_address(sender, upfront_cost)
        post = {
            witness: Account(
                storage={0: BASE_FEE_PER_GAS + max_priority_fee_per_gas}
            ),
            sender: Account(nonce=tx.nonce + 1),
        }

    state_test(
        env=Environment(base_fee_per_gas=BASE_FEE_PER_GAS),
        pre=pre,
        post=post,
        tx=tx,
    )
