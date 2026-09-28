"""Test the transaction level validations applied from Frontier."""

import pytest
from execution_testing import (
    EOA,
    Account,
    Alloc,
    Op,
    RecipientType,
    StateTestFiller,
    Storage,
    Transaction,
    TransactionTestFiller,
    add_kzg_version,
)
from execution_testing.base_types.base_types import ZeroPaddedHexNumber
from execution_testing.exceptions.exceptions import (
    TransactionException,
    TransactionExceptionInstanceOrList,
)
from execution_testing.forks.base_fork import BaseFork
from execution_testing.specs.blockchain import (
    Block,
    BlockchainTestFiller,
    Header,
)
from execution_testing.test_types.block_types import Environment
from execution_testing.test_types.transaction_types import TransactionDefaults


@pytest.mark.inclusion_test
@pytest.mark.exception_test
@pytest.mark.eels_base_coverage
def test_tx_gas_limit(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    env: Environment,
) -> None:
    """
    Tests that if a tx gas limit is higher than the block gas limit,
    an exception is raised.

    The block gas limit is kept well above what an empty block's access
    list needs under the EIP-7928 item cap (`gas_limit // 2000` items,
    against the system-contract reads every Amsterdam block carries), so
    the transaction's gas allowance is the only thing wrong with the
    block and clients do not disagree on which check to report.
    """
    sender = pre.fund_eoa()
    to = pre.fund_eoa()

    block_gas_limit = 100_000
    tx = Transaction(
        gas_limit=block_gas_limit + 1,
        to=to,
        gas_price=0x10,  # Must be >= base fee to isolate gas limit validation
        sender=sender,
        protected=False,
        error=TransactionException.GAS_ALLOWANCE_EXCEEDED,
    )

    modified_fields = {"gas_limit": ZeroPaddedHexNumber(block_gas_limit)}
    env.gas_limit = ZeroPaddedHexNumber(block_gas_limit)

    block = Block(
        txs=[tx],
        rlp_modifier=Header(**modified_fields),
        exception=TransactionException.GAS_ALLOWANCE_EXCEEDED,
    )

    blockchain_test(pre=pre, post={}, blocks=[block], genesis_environment=env)


@pytest.mark.inclusion_test
@pytest.mark.parametrize(
    "nonce_diff, expected_exception",
    [
        pytest.param(
            -1,
            TransactionException.NONCE_MISMATCH_TOO_LOW,
            marks=pytest.mark.exception_test,
        ),
        (0, None),  # Valid case - no exception
        pytest.param(
            1,
            TransactionException.NONCE_MISMATCH_TOO_HIGH,
            marks=pytest.mark.exception_test,
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
@pytest.mark.eels_base_coverage
def test_tx_nonce(
    state_test: StateTestFiller,
    pre: Alloc,
    nonce_diff: int,
    expected_exception: TransactionException | None,
) -> None:
    """
    Tests that the tx nonce matches the account nonce.
    """
    sender = pre.fund_eoa(nonce=5)
    to = pre.fund_eoa()

    tx = Transaction(
        to=to,
        nonce=sender.nonce + nonce_diff,
        sender=sender,
        protected=False,
        error=expected_exception,
    )

    state_test(pre=pre, post={}, tx=tx)


@pytest.mark.inclusion_test
@pytest.mark.pre_alloc_mutable
@pytest.mark.exception_test
@pytest.mark.eels_base_coverage
def test_tx_max_nonce(state_test: StateTestFiller, pre: Alloc) -> None:
    """
    Test that a transaction with the maximum nonce value (`2**64 - 1`) is
    rejected, as the maximum usable nonce is `2**64 - 2`.

    The sender account is funded at the same nonce so that clients which
    check nonce equality first reach the max-nonce check instead of
    rejecting the transaction with a nonce mismatch.
    """
    max_nonce = 2**64 - 1
    sender = pre.fund_eoa(nonce=max_nonce)
    to = pre.nonexistent_account()

    tx = Transaction(
        to=to,
        nonce=max_nonce,
        sender=sender,
        protected=False,
        error=TransactionException.NONCE_IS_MAX,
    )

    state_test(pre=pre, post={sender: Account(nonce=max_nonce)}, tx=tx)


@pytest.mark.inclusion_test
@pytest.mark.exception_test
def test_tx_nonce_overflow(
    transaction_test: TransactionTestFiller,
    pre: Alloc,
    fork: BaseFork,
) -> None:
    """
    Test that a transaction with a nonce that does not fit in 64 bits is
    rejected at deserialization.
    """
    tx = Transaction(
        to=pre.nonexistent_account(),
        nonce=2**64,
        gas_limit=fork.transaction_intrinsic_cost_calculator()(),
        sender=pre.fund_eoa(),
        protected=False,
        error=TransactionException.NONCE_OVERFLOW,
    )

    transaction_test(pre=pre, tx=tx)


@pytest.mark.inclusion_test
@pytest.mark.parametrize(
    "balance_diff, expected_exception",
    [
        pytest.param(
            -1,
            TransactionException.INSUFFICIENT_ACCOUNT_FUNDS,
            marks=pytest.mark.exception_test,
        ),
        (0, None),  # Valid case - no exception
        (1, None),
    ],
)
@pytest.mark.eels_base_coverage
def test_sender_balance(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    env: Environment,
    fork: BaseFork,
    balance_diff: int,
    expected_exception: TransactionException | None,
) -> None:
    """
    Tests that the sender has sufficient balance.
    """
    to = pre.fund_eoa()

    intrinsic_cost = fork.transaction_intrinsic_cost_calculator()
    tx_gas_limit = intrinsic_cost()
    tx_gas_price = TransactionDefaults.gas_price
    tx_value = 0

    # Calculate required balance from tx fields and fund sender
    required_balance = tx_gas_limit * tx_gas_price + tx_value
    sender = pre.fund_eoa(amount=required_balance + balance_diff)

    # Create transaction first with defaults
    tx = Transaction(
        sender=sender,
        gas_limit=tx_gas_limit,
        gas_price=tx_gas_price,
        value=tx_value,
        to=to,
        protected=False,
        error=expected_exception,
    )

    block = Block(
        txs=[tx],
        exception=expected_exception,
    )

    blockchain_test(pre=pre, post={}, blocks=[block], genesis_environment=env)


@pytest.mark.inclusion_test
@pytest.mark.valid_from("Frontier")
@pytest.mark.state_test_only
@pytest.mark.exception_test
@pytest.mark.eels_base_coverage
def test_sender_balance_insufficient_state_test(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    A legacy transaction from a sender that cannot afford `gas * gasPrice`
    must be rejected, exercised through the state-test code path.
    """
    storage = Storage()
    # If the transaction were (incorrectly) executed, this SSTORE would land a
    # non-default value in slot 0, diverging the post-state root from the
    # rejected (pre == post) outcome.
    contract = pre.deploy_contract(
        code=Op.SSTORE(storage.store_next(0, "must_stay_unset"), 0x1)
        + Op.STOP,
    )
    # Zero balance, unable to cover any gas cost.
    sender = pre.fund_eoa(amount=0)

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=100_000,
        gas_price=10,
        protected=False,  # legacy tx
        error=TransactionException.INSUFFICIENT_ACCOUNT_FUNDS,
    )

    state_test(
        env=Environment(),
        pre=pre,
        # Transaction rejected: contract storage stays empty.
        post={contract: Account(storage=storage)},
        tx=tx,
    )


SECP256K1N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141


@pytest.mark.inclusion_test
@pytest.mark.valid_from("Frontier")
@pytest.mark.exception_test
@pytest.mark.eels_base_coverage
@pytest.mark.with_all_tx_types
@pytest.mark.parametrize(
    ("v", "r", "s"),
    [
        # Other than 27/28, anything less than 35 for v is invalid.
        (34, 1, 1),
        # Equal to or above these values are invalid.
        (27, SECP256K1N, 1),
        pytest.param(27, 1, SECP256K1N, id="s=SECP256K1N"),
        pytest.param(
            27,
            1,
            (SECP256K1N // 2) + 1,
            id="s=SECP256K1N//2+1",
            marks=pytest.mark.valid_from("Homestead"),
        ),
    ],
)
def test_bad_v_r_s(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_type: int,
    v: int,
    r: int,
    s: int,
) -> None:
    """
    The v/y_parity component of a signature must be 35 or greater (if it isn't
    27/28).
    """
    to = pre.fund_eoa(0xDEADBEEE)

    error: TransactionExceptionInstanceOrList = (
        TransactionException.INVALID_SIGNATURE_VRS
    )
    if tx_type == 0 and v not in (27, 28):
        # A legacy transaction encodes its chain id within v, so a client that
        # derives the chain id from an out-of-range v rejects the transaction
        # with a chain id mismatch instead of an invalid signature.
        error = [
            TransactionException.INVALID_SIGNATURE_VRS,
            TransactionException.INVALID_CHAINID,
        ]

    blob_versioned_hashes = add_kzg_version([0], 1) if tx_type == 3 else None
    tx = Transaction(
        sender=pre.fund_eoa(),
        to=to,
        error=error,
        ty=tx_type,
        blob_versioned_hashes=blob_versioned_hashes,
        value=1,
        v=v,
        r=r,
        s=s,
    )

    state_test(
        pre=pre,
        post={to: Account(balance=0xDEADBEEE)},
        tx=tx,
    )


# The smallest x-coordinate that is NOT on the secp256k1 curve: x**3 + 7 is a
# quadratic non-residue mod p, so no point (x, y) exists and public-key
# recovery has no solution for r == 5.
UNRECOVERABLE_R = 5


@pytest.mark.inclusion_test
@pytest.mark.valid_from("Frontier")
@pytest.mark.exception_test
@pytest.mark.eels_base_coverage
@pytest.mark.parametrize(
    "tx_type",
    [
        pytest.param(0, id="legacy"),
        pytest.param(1, id="eip2930", marks=pytest.mark.valid_from("Berlin")),
        pytest.param(2, id="eip1559", marks=pytest.mark.valid_from("London")),
    ],
)
def test_unrecoverable_signature(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_type: int,
) -> None:
    """
    A signature whose components are each individually in range but which
    recovers no public key must be rejected.

    `test_bad_v_r_s` covers the RANGE rules (`v` below 27/35, `r` or `s` at or
    above secp256k1n, `s` above the EIP-2 halfway point). This is the distinct
    failure that lies inside those ranges: `r` is read as the x-coordinate of
    the ephemeral point R, and only about half of the values in [1, n) are
    x-coordinates of a curve point at all. For the other half there is no R,
    hence no public key and no sender -- with no range check violated anywhere.

    A client that guards recovery by range-checking alone, or that treats the
    two failures as different kinds of error, reaches this case through an
    unintended path.
    """
    to = pre.fund_eoa(0xDEADBEEE)

    tx = Transaction(
        sender=pre.fund_eoa(),
        to=to,
        error=TransactionException.INVALID_SIGNATURE_VRS,
        ty=tx_type,
        value=1,
        # Legacy encodes the (unprotected) recovery id in v; typed
        # transactions carry the parity bit directly.
        v=27 if tx_type == 0 else 0,
        r=UNRECOVERABLE_R,
        s=1,
    )

    state_test(
        pre=pre,
        # Transaction rejected: the recipient keeps exactly its funded balance.
        post={to: Account(balance=0xDEADBEEE)},
        tx=tx,
    )


@pytest.mark.valid_from("Frontier")
@pytest.mark.invalid_tx_not_last
@pytest.mark.exception_test
@pytest.mark.parametrize(
    "nonces,invalid_index",
    [
        pytest.param((1, 0), 0, id="reversed_pair"),
        pytest.param((0, 2, 1), 1, id="gap_then_fill"),
    ],
)
def test_tx_nonce_order_in_block(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    nonces: tuple[int, ...],
    invalid_index: int,
) -> None:
    """
    Transactions from one sender arrive with a nonce out of order, so the
    block is invalid at the first misplaced nonce even though the
    transactions after it would make the sequence whole.

    A client that executes transactions in parallel and resolves the nonce
    dependency out of block order accepts the block.
    """
    sender = pre.fund_eoa()
    bob_balance = 10**18
    bob = pre.fund_eoa(amount=bob_balance)

    txs = [
        Transaction(
            sender=sender,
            nonce=nonce,
            to=bob,
            value=1,
            protected=False,
            error=(
                TransactionException.NONCE_MISMATCH_TOO_HIGH
                if i == invalid_index
                else None
            ),
        )
        for i, nonce in enumerate(nonces)
    ]

    blockchain_test(
        pre=pre,
        post={bob: Account(balance=bob_balance)},
        blocks=[
            Block(
                txs=txs, exception=TransactionException.NONCE_MISMATCH_TOO_HIGH
            )
        ],
    )


@pytest.mark.valid_from("Frontier")
@pytest.mark.invalid_tx_not_last
@pytest.mark.exception_test
def test_tx_invalid_first_in_block(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
) -> None:
    """
    The first transaction of a block has an unfunded sender and the one
    after it, valid on its own, would have funded that sender; the block
    is rejected at the first transaction.

    A client that applies the later credit before checking the first
    transaction accepts the block. The later transaction also puts the
    sender in the block access list, which a client reading state through
    the list needs before it can reach the funds check at all.
    """
    unfunded = pre.fund_eoa(amount=0)
    carol = pre.fund_eoa()
    bob_balance = 10**18
    bob = pre.fund_eoa(amount=bob_balance)

    txs = [
        Transaction(
            sender=unfunded,
            to=bob,
            value=1,
            protected=False,
            error=TransactionException.INSUFFICIENT_ACCOUNT_FUNDS,
        ),
        Transaction(sender=carol, to=unfunded, value=10**18, protected=False),
    ]

    blockchain_test(
        pre=pre,
        post={
            unfunded: Account.NONEXISTENT,
            bob: Account(balance=bob_balance),
        },
        blocks=[
            Block(
                txs=txs,
                exception=TransactionException.INSUFFICIENT_ACCOUNT_FUNDS,
            )
        ],
    )


@pytest.mark.valid_from("Frontier")
@pytest.mark.parametrize(
    "funding",
    [
        pytest.param("exact", id="exact"),
        pytest.param(
            "one_wei_short",
            id="one_wei_short",
            marks=[
                pytest.mark.invalid_tx_not_last,
                pytest.mark.exception_test,
            ],
        ),
    ],
)
def test_tx_sender_funds_spent_by_earlier_tx(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: BaseFork,
    funding: str,
) -> None:
    """
    A sender's second transaction is affordable only against the balance
    its first one left behind, and a third sender's transaction follows.

    Against the pre-block balance both of the sender's transactions pass
    the upfront check; one wei short and the block is invalid at the
    second one, which a client checking against the pre-block state
    accepts.
    """
    gas_limit = fork.transaction_intrinsic_cost_calculator()(
        sends_value=True, recipient_type=RecipientType.EOA
    )
    gas_price = TransactionDefaults.gas_price
    value = 1
    tx_cost = gas_limit * gas_price + value
    if funding == "exact":
        sender_balance = 2 * tx_cost
        error = None
    elif funding == "one_wei_short":
        sender_balance = 2 * tx_cost - 1
        error = TransactionException.INSUFFICIENT_ACCOUNT_FUNDS
    else:
        raise ValueError(f"unknown funding: {funding}")

    sender = pre.fund_eoa(amount=sender_balance)
    carol = pre.fund_eoa()
    bob_balance = 10**18
    bob = pre.fund_eoa(amount=bob_balance)

    txs = [
        Transaction(
            sender=sender,
            to=bob,
            value=value,
            gas_limit=gas_limit,
            gas_price=gas_price,
            protected=False,
        ),
        Transaction(
            sender=sender,
            to=bob,
            value=value,
            gas_limit=gas_limit,
            gas_price=gas_price,
            protected=False,
            error=error,
        ),
        Transaction(sender=carol, to=bob, value=value, protected=False),
    ]

    if funding == "exact":
        post = {
            sender: Account(nonce=2, balance=0),
            bob: Account(balance=bob_balance + 3 * value),
        }
    elif funding == "one_wei_short":
        post = {
            sender: Account(nonce=0, balance=sender_balance),
            bob: Account(balance=bob_balance),
        }
    else:
        raise ValueError(f"unknown funding: {funding}")

    blockchain_test(
        pre=pre,
        post=post,
        blocks=[Block(txs=txs, exception=error)],
    )


@pytest.mark.valid_from("Frontier")
@pytest.mark.exception_test
@pytest.mark.parametrize(
    "rejected_block",
    [
        pytest.param("invalid_tx_alone", id="invalid_tx_alone"),
        pytest.param(
            "invalid_tx_then_valid",
            id="invalid_tx_then_valid",
            marks=pytest.mark.invalid_tx_not_last,
        ),
    ],
)
def test_rejected_block_leaves_no_trace(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: BaseFork,
    rejected_block: str,
) -> None:
    """
    A block rejected for an unaffordable transaction leaves the sender's
    nonce and balance untouched, so the next block spends the same nonce
    and the exact balance the rejected transaction claimed to need.

    In the `invalid_tx_then_valid` arm a valid transaction from a second
    sender follows the rejected one and is replayed at the same nonce in
    the next block, so the trailing transaction leaves no trace either.
    """
    gas_limit = fork.transaction_intrinsic_cost_calculator()(
        sends_value=True, recipient_type=RecipientType.EOA
    )
    gas_price = TransactionDefaults.gas_price
    value = 1
    sender = pre.fund_eoa(amount=gas_limit * gas_price + value)
    carol = pre.fund_eoa()
    bob_balance = 10**18
    bob = pre.fund_eoa(amount=bob_balance)

    def transfer(
        origin: EOA, amount: int, error: TransactionException | None = None
    ) -> Transaction:
        return Transaction(
            sender=origin,
            nonce=0,
            to=bob,
            value=amount,
            gas_limit=gas_limit,
            gas_price=gas_price,
            protected=False,
            error=error,
        )

    # One wei more than the sender holds after gas.
    unaffordable = transfer(
        sender, value + 1, TransactionException.INSUFFICIENT_ACCOUNT_FUNDS
    )
    if rejected_block == "invalid_tx_alone":
        rejected_txs = [unaffordable]
        valid_txs = [transfer(sender, value)]
        carol_post = Account(nonce=0)
        bob_post = Account(balance=bob_balance + value)
    elif rejected_block == "invalid_tx_then_valid":
        rejected_txs = [unaffordable, transfer(carol, value)]
        valid_txs = [transfer(sender, value), transfer(carol, value)]
        carol_post = Account(nonce=1)
        bob_post = Account(balance=bob_balance + 2 * value)
    else:
        raise ValueError(f"unknown rejected_block: {rejected_block}")

    blockchain_test(
        pre=pre,
        post={
            sender: Account(nonce=1, balance=0),
            carol: carol_post,
            bob: bob_post,
        },
        blocks=[
            Block(
                txs=rejected_txs,
                exception=TransactionException.INSUFFICIENT_ACCOUNT_FUNDS,
            ),
            Block(txs=valid_txs),
        ],
    )
