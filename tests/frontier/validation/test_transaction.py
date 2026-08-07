"""Test the transaction level validations applied from Frontier."""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Op,
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
    """
    sender = pre.fund_eoa()
    to = pre.fund_eoa()

    tx = Transaction(
        gas_limit=21001,
        to=to,
        gas_price=0x10,  # Must be >= base fee to isolate gas limit validation
        sender=sender,
        protected=False,
        error=TransactionException.GAS_ALLOWANCE_EXCEEDED,
    )

    modified_fields = {"gas_limit": ZeroPaddedHexNumber(21000)}
    env.gas_limit = ZeroPaddedHexNumber(21000)

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
