"""Ethereum transaction test spec definition and filler."""

from typing import Callable, ClassVar, Generator, Mapping, Sequence, Type

from execution_testing.client_clis import TransitionTool
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

    def _intrinsic_gas(self, fork: Fork) -> int:
        """Return the intrinsic gas of the transaction under test."""
        if self.tx.frames is not None:
            # EIP-8141: a frame transaction is priced from its frames
            # and its signature entries, whose raw bytes are part of
            # the price, so price it signed.
            signed = self.tx.with_signature_and_sender()
            assert signed.frames is not None
            assert signed.signatures is not None
            frame_intrinsic_gas_cost_calculator = (
                fork.frame_transaction_intrinsic_cost_calculator()
            )
            return frame_intrinsic_gas_cost_calculator(
                frames=signed.frames,
                signatures=signed.signatures,
                sender=signed.sender,
                return_cost_deducted_prior_execution=True,
            )
        intrinsic_gas_cost_calculator = (
            fork.transaction_intrinsic_cost_calculator()
        )
        return intrinsic_gas_cost_calculator(
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
            result = FixtureResult(
                exception=None,
                hash=self.tx.hash,
                intrinsic_gas=self._intrinsic_gas(fork),
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

    def generate(
        self,
        t8n: TransitionTool,
        fixture_format: FixtureFormat | LabeledFixtureFormat,
    ) -> FillResult:
        """Generate the TransactionTest fixture."""
        del t8n

        self.check_exception_test(exception=self.tx.error is not None)
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
