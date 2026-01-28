"""Test fixture post state (expect section) during state fixture generation."""

from typing import Any, Mapping, Type

import pytest

from execution_testing.base_types import (
    Account,
    Address,
    Bytes,
    Hash,
    Storage,
    TestAddress,
    TestPrivateKey,
)
from execution_testing.client_clis import TransitionTool
from execution_testing.exceptions import TransactionException
from execution_testing.fixtures import (
    BlockchainFixture,
    FixtureFormat,
    StateFixture,
)
from execution_testing.forks import Fork, get_deployed_forks
from execution_testing.specs import Block
from execution_testing.test_types import (
    Alloc,
    Environment,
    Transaction,
    TransactionLog,
    TransactionReceipt,
)

from ..blockchain import BlockchainEngineFixture, BlockchainTest
from ..helpers import (
    ExecutionExceptionMismatchError,
    LogMismatchError,
    TransactionReceiptMismatchError,
    UnexpectedExecutionFailError,
    UnexpectedExecutionSuccessError,
    verify_log,
)
from ..state import StateTest

ADDRESS_UNDER_TEST = Address(0x01)


@pytest.fixture
def tx() -> Transaction:
    """Fixture set from the test's indirectly parametrized `tx` parameter."""
    return Transaction(secret_key=TestPrivateKey)


@pytest.fixture
def pre(request: Any) -> Alloc:
    """Fixture set from the test's indirectly parametrized `pre` parameter."""
    extra_accounts = {}
    if hasattr(request, "param"):
        extra_accounts = request.param
    return Alloc(extra_accounts | {TestAddress: Account(balance=(10**18))})


@pytest.fixture
def post(request: Any) -> Alloc:  # noqa: D103
    """Fixture set from the test's indirectly parametrized `post` parameter."""
    extra_accounts = {}
    if hasattr(request, "param"):
        extra_accounts = request.param
    return Alloc(extra_accounts)


@pytest.fixture
def fork() -> Fork:  # noqa: D103
    return get_deployed_forks()[-1]


@pytest.fixture
def state_test(  # noqa: D103
    pre: Mapping[Any, Any],
    post: Mapping[Any, Any],
    tx: Transaction,
    fork: Fork,
) -> StateTest:
    return StateTest(
        env=Environment(),
        pre=pre,
        post=post,
        tx=tx,
        fork=fork,
    )


# Storage value mismatch tests
@pytest.mark.parametrize(
    "pre,post,expected_exception",
    [
        (  # mismatch_1: 1:1 vs 1:2
            {ADDRESS_UNDER_TEST: Account(storage={"0x01": "0x01"}, nonce=1)},
            {ADDRESS_UNDER_TEST: Account(storage={"0x01": "0x02"})},
            Storage.KeyValueMismatchError(
                address=ADDRESS_UNDER_TEST, key=1, want=2, got=1
            ),
        ),
        (  # mismatch_2: 1:1 vs 2:1
            {ADDRESS_UNDER_TEST: Account(storage={"0x01": "0x01"}, nonce=1)},
            {ADDRESS_UNDER_TEST: Account(storage={"0x02": "0x01"})},
            Storage.KeyValueMismatchError(
                address=ADDRESS_UNDER_TEST, key=1, want=0, got=1
            ),
        ),
        (  # mismatch_2_a: 1:1 vs 0:0
            {ADDRESS_UNDER_TEST: Account(storage={"0x01": "0x01"}, nonce=1)},
            {ADDRESS_UNDER_TEST: Account(storage={"0x00": "0x00"})},
            Storage.KeyValueMismatchError(
                address=ADDRESS_UNDER_TEST, key=1, want=0, got=1
            ),
        ),
        (  # mismatch_2_b: 1:1 vs empty
            {ADDRESS_UNDER_TEST: Account(storage={"0x01": "0x01"}, nonce=1)},
            {ADDRESS_UNDER_TEST: Account(storage={})},
            Storage.KeyValueMismatchError(
                address=ADDRESS_UNDER_TEST, key=1, want=0, got=1
            ),
        ),
        (  # mismatch_3: 0:0 vs 1:2
            {ADDRESS_UNDER_TEST: Account(storage={"0x00": "0x00"}, nonce=1)},
            {ADDRESS_UNDER_TEST: Account(storage={"0x01": "0x02"})},
            Storage.KeyValueMismatchError(
                address=ADDRESS_UNDER_TEST, key=1, want=2, got=0
            ),
        ),
        (  # mismatch_3_a: empty vs 1:2
            {ADDRESS_UNDER_TEST: Account(storage={}, nonce=1)},
            {ADDRESS_UNDER_TEST: Account(storage={"0x01": "0x02"})},
            Storage.KeyValueMismatchError(
                address=ADDRESS_UNDER_TEST, key=1, want=2, got=0
            ),
        ),
        (  # mismatch_4: 0:3, 1:2 vs 1:2
            {
                ADDRESS_UNDER_TEST: Account(
                    storage={"0x00": "0x03", "0x01": "0x02"}, nonce=1
                )
            },
            {ADDRESS_UNDER_TEST: Account(storage={"0x01": "0x02"})},
            Storage.KeyValueMismatchError(
                address=ADDRESS_UNDER_TEST, key=0, want=0, got=3
            ),
        ),
        (  # mismatch_5: 1:2, 2:3 vs 1:2
            {
                ADDRESS_UNDER_TEST: Account(
                    storage={"0x01": "0x02", "0x02": "0x03"}, nonce=1
                )
            },
            {ADDRESS_UNDER_TEST: Account(storage={"0x01": "0x02"})},
            Storage.KeyValueMismatchError(
                address=ADDRESS_UNDER_TEST, key=2, want=0, got=3
            ),
        ),
        (  # mismatch_6: 1:2 vs 1:2, 2:3
            {ADDRESS_UNDER_TEST: Account(storage={"0x01": "0x02"}, nonce=1)},
            {
                ADDRESS_UNDER_TEST: Account(
                    storage={"0x01": "0x02", "0x02": "0x03"}
                )
            },
            Storage.KeyValueMismatchError(
                address=ADDRESS_UNDER_TEST, key=2, want=3, got=0
            ),
        ),
    ],
    indirect=["pre", "post"],
)
def test_post_storage_value_mismatch(
    expected_exception: Storage.KeyValueMismatchError,
    state_test: StateTest,
    default_t8n: TransitionTool,
) -> None:
    """
    Test post state `Account.storage` exceptions during state test fixture
    generation.
    """
    with pytest.raises(Storage.KeyValueMismatchError) as e_info:
        state_test.generate(t8n=default_t8n, fixture_format=StateFixture)
    assert e_info.value == expected_exception


# Nonce value mismatch tests
@pytest.mark.parametrize(
    "pre,post",
    [
        (
            {ADDRESS_UNDER_TEST: Account(nonce=1)},
            {ADDRESS_UNDER_TEST: Account(nonce=2)},
        ),
        (
            {ADDRESS_UNDER_TEST: Account(nonce=1)},
            {ADDRESS_UNDER_TEST: Account(nonce=0)},
        ),
        (
            {ADDRESS_UNDER_TEST: Account(nonce=1)},
            {ADDRESS_UNDER_TEST: Account()},
        ),
    ],
    indirect=["pre", "post"],
)
def test_post_nonce_value_mismatch(
    pre: Alloc,
    post: Alloc,
    state_test: StateTest,
    default_t8n: TransitionTool,
) -> None:
    """
    Test post state `Account.nonce` verification and exceptions during state
    test fixture generation.
    """
    pre_account = pre[ADDRESS_UNDER_TEST]
    post_account = post[ADDRESS_UNDER_TEST]
    assert pre_account is not None
    assert post_account is not None
    pre_nonce = pre_account.nonce
    post_nonce = post_account.nonce
    if "nonce" not in post_account.model_fields_set:  # no exception
        state_test.generate(t8n=default_t8n, fixture_format=StateFixture)
        return
    with pytest.raises(Account.NonceMismatchError) as e_info:
        state_test.generate(t8n=default_t8n, fixture_format=StateFixture)
    assert e_info.value == Account.NonceMismatchError(
        address=ADDRESS_UNDER_TEST, want=post_nonce, got=pre_nonce
    )


# Code value mismatch tests
@pytest.mark.parametrize(
    "pre,post",
    [
        (
            {ADDRESS_UNDER_TEST: Account(code="0x02")},
            {ADDRESS_UNDER_TEST: Account(code="0x01")},
        ),
        (
            {ADDRESS_UNDER_TEST: Account(code="0x02")},
            {ADDRESS_UNDER_TEST: Account(code="0x")},
        ),
        (
            {ADDRESS_UNDER_TEST: Account(code="0x02")},
            {ADDRESS_UNDER_TEST: Account()},
        ),
    ],
    indirect=["pre", "post"],
)
def test_post_code_value_mismatch(
    pre: Alloc,
    post: Alloc,
    state_test: StateTest,
    default_t8n: TransitionTool,
) -> None:
    """
    Test post state `Account.code` verification and exceptions during state
    test fixture generation.
    """
    pre_account = pre[ADDRESS_UNDER_TEST]
    post_account = post[ADDRESS_UNDER_TEST]
    assert pre_account is not None
    assert post_account is not None
    pre_code = pre_account.code
    post_code = post_account.code
    if "code" not in post_account.model_fields_set:  # no exception
        state_test.generate(t8n=default_t8n, fixture_format=StateFixture)
        return
    with pytest.raises(Account.CodeMismatchError) as e_info:
        state_test.generate(t8n=default_t8n, fixture_format=StateFixture)
    assert e_info.value == Account.CodeMismatchError(
        address=ADDRESS_UNDER_TEST, want=post_code, got=pre_code
    )


# Balance value mismatch tests
@pytest.mark.parametrize(
    "pre,post",
    [
        (
            {ADDRESS_UNDER_TEST: Account(balance=1)},
            {ADDRESS_UNDER_TEST: Account(balance=2)},
        ),
        (
            {ADDRESS_UNDER_TEST: Account(balance=1)},
            {ADDRESS_UNDER_TEST: Account(balance=0)},
        ),
        (
            {ADDRESS_UNDER_TEST: Account(balance=1)},
            {ADDRESS_UNDER_TEST: Account()},
        ),
    ],
    indirect=["pre", "post"],
)
def test_post_balance_value_mismatch(
    pre: Alloc,
    post: Alloc,
    state_test: StateTest,
    default_t8n: TransitionTool,
) -> None:
    """
    Test post state `Account.balance` verification and exceptions during state
    test fixture generation.
    """
    pre_account = pre[ADDRESS_UNDER_TEST]
    post_account = post[ADDRESS_UNDER_TEST]
    assert pre_account is not None
    assert post_account is not None
    pre_balance = pre_account.balance
    post_balance = post_account.balance
    if "balance" not in post_account.model_fields_set:  # no exception
        state_test.generate(t8n=default_t8n, fixture_format=StateFixture)
        return
    with pytest.raises(Account.BalanceMismatchError) as e_info:
        state_test.generate(t8n=default_t8n, fixture_format=StateFixture)
    assert e_info.value == Account.BalanceMismatchError(
        address=ADDRESS_UNDER_TEST, want=post_balance, got=pre_balance
    )


# Account mismatch tests
@pytest.mark.parametrize(
    "pre,post,exception_type",
    [
        (
            {ADDRESS_UNDER_TEST: Account(balance=1)},
            {ADDRESS_UNDER_TEST: Account()},
            None,
        ),
        (
            {ADDRESS_UNDER_TEST: Account(balance=1)},
            {
                ADDRESS_UNDER_TEST: Account(balance=1),
                Address(0x02): Account(balance=1),
            },
            Alloc.MissingAccountError,
        ),
        (
            {ADDRESS_UNDER_TEST: Account(balance=1)},
            {},
            None,
        ),
        (
            {ADDRESS_UNDER_TEST: Account(balance=1)},
            {ADDRESS_UNDER_TEST: Account.NONEXISTENT},
            Alloc.UnexpectedAccountError,
        ),
    ],
    indirect=["pre", "post"],
)
def test_post_account_mismatch(
    state_test: StateTest,
    default_t8n: TransitionTool,
    exception_type: Type[Exception] | None,
) -> None:
    """
    Test post state `Account` verification and exceptions during state test
    fixture generation.
    """
    if exception_type is None:
        state_test.generate(t8n=default_t8n, fixture_format=StateFixture)
        return
    with pytest.raises(exception_type) as _:
        state_test.generate(t8n=default_t8n, fixture_format=StateFixture)


# Transaction result mismatch tests
@pytest.mark.parametrize(
    "tx,exception_type",
    [
        pytest.param(
            Transaction(
                secret_key=TestPrivateKey,
                gas_limit=20_999,
                error=TransactionException.SENDER_NOT_EOA,
            ),
            ExecutionExceptionMismatchError,
            id="TransactionExecutionExceptionMismatchError",
        ),
        pytest.param(
            Transaction(
                secret_key=TestPrivateKey,
                error=TransactionException.INTRINSIC_GAS_TOO_LOW,
                expected_receipt=TransactionReceipt(
                    cumulative_gas_used=21_000
                ),
            ),
            UnexpectedExecutionSuccessError,
            id="TransactionUnexpectedExecutionSuccessError",
        ),
        pytest.param(
            Transaction(
                secret_key=TestPrivateKey,
                gas_limit=20_999,
                expected_receipt=TransactionReceipt(
                    cumulative_gas_used=21_000
                ),
            ),
            UnexpectedExecutionFailError,
            id="TransactionUnexpectedExecutionFailError",
        ),
        pytest.param(
            Transaction(
                secret_key=TestPrivateKey,
                expected_receipt=TransactionReceipt(
                    cumulative_gas_used=21_001
                ),
            ),
            TransactionReceiptMismatchError,
            id="TransactionReceiptMismatchError",
        ),
        pytest.param(
            Transaction(
                secret_key=TestPrivateKey,
                gas_limit=20_999,
                expected_receipt=TransactionReceipt(
                    cumulative_gas_used=21_001
                ),
            ),
            UnexpectedExecutionFailError,
            id="TransactionUnexpectedExecutionFailError+TransactionReceiptMismatchError",
        ),
        pytest.param(
            Transaction(
                secret_key=TestPrivateKey,
                error=TransactionException.INTRINSIC_GAS_TOO_LOW,
                expected_receipt=TransactionReceipt(
                    cumulative_gas_used=21_001
                ),
            ),
            UnexpectedExecutionSuccessError,
            id="TransactionUnexpectedExecutionSuccessError+TransactionReceiptMismatchError",
        ),
    ],
)
@pytest.mark.parametrize(
    "fixture_format",
    [
        StateFixture,
        BlockchainFixture,
    ],
)
def test_transaction_expectation(
    state_test: StateTest,
    default_t8n: TransitionTool,
    exception_type: Type[Exception] | None,
    fixture_format: FixtureFormat,
) -> None:
    """
    Test a transaction that has an unexpected error, expected error, or
    expected a specific value in its receipt.
    """
    if (
        exception_type == ExecutionExceptionMismatchError
        and not default_t8n.exception_mapper.reliable
    ):
        pytest.xfail(
            reason="Exceptions need to be better described in the t8n tool "
            f"({default_t8n.__class__.__name__})."
        )
    if exception_type is None:
        state_test.generate(t8n=default_t8n, fixture_format=fixture_format)
    else:
        with pytest.raises(exception_type) as _:
            state_test.generate(t8n=default_t8n, fixture_format=fixture_format)


@pytest.mark.parametrize(
    "intermediate_state,expected_exception",
    [
        pytest.param(
            {
                TestAddress: Account(nonce=1),
                Address(0x01): Account(balance=1),
            },
            None,
            id="NoException",
        ),
        pytest.param(
            {
                TestAddress: Account(nonce=2),
                Address(0x01): Account(balance=1),
            },
            Account.NonceMismatchError,
            id="NonceMismatchError",
        ),
        pytest.param(
            {
                TestAddress: Account(nonce=1),
                Address(0x01): Account(balance=2),
            },
            Account.BalanceMismatchError,
            id="BalanceMismatchError",
        ),
    ],
)
@pytest.mark.parametrize(
    "fixture_format",
    [
        BlockchainFixture,
        BlockchainEngineFixture,
    ],
)
def test_block_intermediate_state(
    pre: Alloc,
    default_t8n: TransitionTool,
    fork: Fork,
    fixture_format: FixtureFormat,
    intermediate_state: Mapping[Any, Any],
    expected_exception: Type[Exception] | None,
) -> None:
    """Validate the state when building blockchain."""
    env = Environment()

    to = Address(0x01)
    tx = Transaction(
        gas_limit=100_000, to=to, value=1, nonce=0, secret_key=TestPrivateKey
    )
    tx_2 = Transaction(
        gas_limit=100_000, to=to, value=1, nonce=1, secret_key=TestPrivateKey
    )

    block_1 = Block(
        txs=[tx],
        expected_post_state={
            TestAddress: Account(nonce=1),
            to: Account(balance=1),
        },
    )

    block_2 = Block(txs=[], expected_post_state=intermediate_state)

    block_3 = Block(
        txs=[tx_2],
        expected_post_state={
            TestAddress: Account(nonce=2),
            to: Account(balance=2),
        },
    )

    if expected_exception:
        with pytest.raises(expected_exception) as _:
            BlockchainTest(
                fork=fork,
                genesis_environment=env,
                pre=pre,
                post=block_3.expected_post_state,
                blocks=[block_1, block_2, block_3],
            ).generate(t8n=default_t8n, fixture_format=fixture_format)
        return
    else:
        BlockchainTest(
            fork=fork,
            genesis_environment=env,
            pre=pre,
            post=block_3.expected_post_state,
            blocks=[block_1, block_2, block_3],
        ).generate(t8n=default_t8n, fixture_format=fixture_format)


# Log verification tests
@pytest.mark.parametrize(
    "expected_log,actual_log,should_raise",
    [
        pytest.param(
            TransactionLog(
                address=Address(0x100),
                topics=[Hash(b"\x01" * 32)],
                data=Bytes(b"\x02" * 32),
            ),
            TransactionLog(
                address=Address(0x100),
                topics=[Hash(b"\x01" * 32)],
                data=Bytes(b"\x02" * 32),
            ),
            False,
            id="matching_logs",
        ),
        pytest.param(
            TransactionLog(
                address=Address(0x100),
            ),
            TransactionLog(
                address=Address(0x200),
                topics=[Hash(b"\x01" * 32)],
                data=Bytes(b"\x02" * 32),
            ),
            True,
            id="address_mismatch",
        ),
        pytest.param(
            TransactionLog(
                topics=[Hash(b"\x01" * 32)],
            ),
            TransactionLog(
                address=Address(0x100),
                topics=[Hash(b"\x02" * 32)],
                data=Bytes(b"\x02" * 32),
            ),
            True,
            id="topics_mismatch",
        ),
        pytest.param(
            TransactionLog(
                data=Bytes(b"\x01" * 32),
            ),
            TransactionLog(
                address=Address(0x100),
                topics=[Hash(b"\x01" * 32)],
                data=Bytes(b"\x02" * 32),
            ),
            True,
            id="data_mismatch",
        ),
        pytest.param(
            TransactionLog(
                address=None,
                topics=None,
                data=None,
            ),
            TransactionLog(
                address=Address(0x100),
                topics=[Hash(b"\x01" * 32)],
                data=Bytes(b"\x02" * 32),
            ),
            False,
            id="no_fields_specified",
        ),
    ],
)
def test_verify_log(
    expected_log: TransactionLog,
    actual_log: TransactionLog,
    should_raise: bool,
) -> None:
    """Test verify_log function for log field mismatches."""
    if should_raise:
        with pytest.raises(LogMismatchError):
            verify_log(0, 0, expected_log, actual_log)
    else:
        verify_log(0, 0, expected_log, actual_log)


# Log mismatch integration tests using Amsterdam fork (EIP-7708)
@pytest.mark.parametrize(
    "mismatch_type",
    [
        pytest.param("address", id="log_address_mismatch"),
        pytest.param("topics", id="log_topics_mismatch"),
        pytest.param("data", id="log_data_mismatch"),
    ],
)
def test_log_mismatch_during_generation(
    default_t8n: TransitionTool,
    mismatch_type: str,
) -> None:
    """
    Test that log mismatches raise LogMismatchError during test generation.
    """
    from execution_testing.forks import Amsterdam

    # EIP-7708 transfer log constants
    system_address = Address(0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE)

    # Create a simple transfer transaction
    recipient = Address(0x100)
    transfer_value = 1000

    # Create intentionally wrong expected logs based on mismatch type
    if mismatch_type == "address":
        wrong_log = TransactionLog(
            address=Address(0x1234),  # Wrong address, should be system_address
        )
    elif mismatch_type == "topics":
        wrong_log = TransactionLog(
            address=system_address,
            topics=[Hash(b"\x00" * 32)],  # Wrong topic
        )
    else:  # data
        wrong_log = TransactionLog(
            address=system_address,
            data=Bytes((9999).to_bytes(32, "big")),  # Wrong data
        )

    tx = Transaction(
        secret_key=TestPrivateKey,
        to=recipient,
        value=transfer_value,
        expected_receipt=TransactionReceipt(logs=[wrong_log]),
    )

    pre = Alloc({TestAddress: Account(balance=10**18)})

    state_test = StateTest(
        env=Environment(),
        pre=pre,
        post={},  # Empty post to skip post-state verification
        tx=tx,
        fork=Amsterdam,
    )

    with pytest.raises(LogMismatchError):
        state_test.generate(t8n=default_t8n, fixture_format=StateFixture)
