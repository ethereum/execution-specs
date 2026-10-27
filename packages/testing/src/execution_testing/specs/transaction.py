"""Ethereum transaction test spec definition and filler."""

from typing import Callable, ClassVar, Generator, Mapping, Sequence, Type

from ethereum.exceptions import EthereumException
from ethereum_rlp import rlp
from ethereum_rlp.exceptions import RLPException
from ethereum_spec_tools.utils import resolve_fork

from execution_testing.client_clis import (
    ExecutionSpecsTransitionTool,
    TransitionTool,
)
from execution_testing.exceptions import UndefinedException
from execution_testing.execution import (
    BaseExecute,
    ExecuteFormat,
    LabeledExecuteFormat,
    TransactionPost,
)
from execution_testing.fixtures import (
    FixtureFormat,
    LabeledFixtureFormat,
    TransactionFixture,
)
from execution_testing.fixtures.transaction import FixtureResult
from execution_testing.forks import Fork, TransitionFork
from execution_testing.recipient_type import RecipientType
from execution_testing.test_types import Alloc, Transaction

from .base import BaseTest, FillResult, OpMode
from .helpers import (
    ExecutionContext,
    UnexpectedExecutionFailError,
    UnexpectedExecutionSuccessError,
)


class TransactionTest(BaseTest):
    """
    Filler type that tests the transaction over the period of a single block.
    """

    tx: Transaction
    pre: Alloc | None = None

    supported_fixture_formats: ClassVar[
        Sequence[FixtureFormat | LabeledFixtureFormat]
    ] = [
        TransactionFixture,
    ]
    supported_execute_formats: ClassVar[Sequence[LabeledExecuteFormat]] = [
        LabeledExecuteFormat(
            TransactionPost,
            "transaction_test",
            "An execute test derived from a transaction test",
        ),
    ]

    @classmethod
    def genesis_pre_allocation(
        cls,
        *,
        fork: Fork | TransitionFork,
        fixture_format: FixtureFormat | LabeledFixtureFormat,
    ) -> Mapping:
        """Return no accounts: this spec has no genesis."""
        del fork, fixture_format
        return {}

    def make_transaction_test_fixture(
        self,
    ) -> FillResult:
        """Create a fixture from the transaction test definition."""
        fork = self.fork.transitions_from()
        if self.tx.error is not None:
            result = FixtureResult(
                exception=self.tx.error,
                hash=None,
                intrinsic_gas=0,
                sender=None,
            )
        else:
            intrinsic_gas_cost_calculator = (
                fork.transitions_from().transaction_intrinsic_cost_calculator()
            )
            intrinsic_gas = intrinsic_gas_cost_calculator(
                calldata=self.tx.data,
                contract_creation=self.tx.to is None,
                access_list=self.tx.access_list,
                authorization_list_or_count=self.tx.authorization_list,
                sends_value=self.tx.value > 0,
                recipient_type=(
                    RecipientType.SELF
                    if self.tx.to == self.tx.sender
                    else RecipientType.CONTRACT
                ),
            )
            result = FixtureResult(
                exception=None,
                hash=self.tx.hash,
                intrinsic_gas=intrinsic_gas,
                sender=self.tx.sender,
            )

        fixture = TransactionFixture(
            result={
                fork: result,
            },
            transaction=self.tx.with_signature_and_sender().rlp(),
        )
        return FillResult(
            fixture=fixture,
            gas_optimization=None,
            benchmark_gas_used=None,
            benchmark_opcode_count=None,
        )

    def check_reference_verdict(self) -> None:
        """
        Check the reference implementation's verdict on the fixture bytes.

        The fixture's transaction bytes are decoded with the reference
        implementation, and its verdict must agree with `tx.error`.

        A transaction fixture records `tx.error` without running any
        transition tool, and the t8n's JSON loader (`TransactionLoad`)
        rebuilds the transaction a block-based fill passes to the tool from
        its fields, ignoring `rlpOverride`. Without this check, a wrong
        expectation or a malformed override fills unchanged.

        Bytes the reference implementation cannot decode, including empty
        or truncated bytes, must be expected to fail. A legacy transaction
        (first byte 0xc0 or above, or any bytes before typed transactions)
        is decoded with the fork's legacy class; anything else goes through
        the fork's `decode_transaction`. A decoded frame transaction also
        runs through `validate_frame_transaction`, which applies every
        transaction-only rule except the chain ID (checked against the
        block's chain ID when the transaction is processed), so for it the
        check runs both ways: a transaction it accepts must be expected
        valid. A frame transaction whose only fault is its chain ID is
        therefore reported as an unexpected success. Other types have rules
        that need the sender's state or the block, which are not run here,
        so for them only a failed decode is conclusive.
        """
        expected = self.tx.error
        raw = bytes(self.tx.with_signature_and_sender().rlp())
        context = {"nonce": self.tx.nonce, "check": "reference decode"}
        fork = self.fork.transitions_from()
        hardfork = resolve_fork(fork.transition_tool_name())
        transactions = hardfork.module("transactions")
        decode_typed = getattr(transactions, "decode_transaction", None)
        try:
            # A slice, not `raw[0]`: empty bytes must reach the decoder.
            if decode_typed is None or raw[:1] >= b"\xc0":
                legacy = getattr(
                    transactions, "LegacyTransaction", transactions.Transaction
                )
                rlp.decode_to(legacy, raw)
                return
            decoded = decode_typed(raw)
            # `FrameTransaction` (EIP-8141) exists only on forks that ship
            # it; elsewhere this is a no-op.
            frame_transaction = getattr(transactions, "FrameTransaction", None)
            if frame_transaction is None or not isinstance(
                decoded, frame_transaction
            ):
                return
            hardfork.module(
                "transactions.frame_transaction"
            ).validate_frame_transaction(decoded)
        except (EthereumException, RLPException) as error:
            if expected is None:
                raise UnexpectedExecutionFailError(
                    execution_context=ExecutionContext.TRANSACTION,
                    message=str(error) or type(error).__name__,
                    exception=UndefinedException(type(error).__name__),
                    **context,
                ) from error
            return
        if expected is not None:
            raise UnexpectedExecutionSuccessError(
                execution_context=ExecutionContext.TRANSACTION,
                expected=expected,
                **context,
            )

    def generate(
        self,
        t8n: TransitionTool,
        fixture_format: FixtureFormat | LabeledFixtureFormat,
    ) -> FillResult:
        """Generate the TransactionTest fixture."""
        self.check_exception_test(exception=self.tx.error is not None)
        if isinstance(t8n, ExecutionSpecsTransitionTool):
            self.check_reference_verdict()
        if fixture_format == TransactionFixture:
            return self.make_transaction_test_fixture()

        raise Exception(f"Unknown fixture format: {fixture_format}")

    def execute(
        self,
        *,
        execute_format: ExecuteFormat | LabeledExecuteFormat,
    ) -> BaseExecute:
        """Execute the transaction test by sending it to the live network."""
        if execute_format == TransactionPost:
            benchmark_mode = self.operation_mode == OpMode.BENCHMARKING
            return TransactionPost(
                blocks=[[self.tx]],
                post={},
                benchmark_mode=benchmark_mode,
            )
        raise Exception(f"Unsupported execute format: {execute_format}")


TransactionTestSpec = Callable[[str], Generator[TransactionTest, None, None]]
TransactionTestFiller = Type[TransactionTest]
