"""Ethereum transaction test spec definition and filler."""

from typing import Callable, ClassVar, Generator, Sequence, Type

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
from execution_testing.recipient_type import RecipientType
from execution_testing.test_types import (
    Alloc,
    EnvironmentDefaults,
    Transaction,
)

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

    def make_transaction_test_fixture(
        self,
    ) -> FillResult:
        """
        Create a fixture from the transaction test definition.

        Resolve omitted gas limits against the configured default block gas
        budget before signing the transaction.
        """
        fork = self.fork.transitions_from()
        tx = self.tx.with_gas_limit(
            max_gas_limit=EnvironmentDefaults.gas_limit,
            transaction_gas_limit_cap=fork.transaction_gas_limit_cap(),
            state_gas_reservoir_enabled=fork.state_gas_reservoir_enabled(),
        ).with_signature_and_sender()
        if tx.error is not None:
            result = FixtureResult(
                exception=tx.error,
                hash=None,
                intrinsic_gas=0,
                sender=None,
            )
        else:
            intrinsic_gas_cost_calculator = (
                fork.transitions_from().transaction_intrinsic_cost_calculator()
            )
            intrinsic_gas = intrinsic_gas_cost_calculator(
                calldata=tx.data,
                contract_creation=tx.to is None,
                access_list=tx.access_list,
                authorization_list_or_count=tx.authorization_list,
                sends_value=tx.value > 0,
                recipient_type=(
                    RecipientType.SELF
                    if tx.to == tx.sender
                    else RecipientType.CONTRACT
                ),
            )
            result = FixtureResult(
                exception=None,
                hash=tx.hash,
                intrinsic_gas=intrinsic_gas,
                sender=tx.sender,
            )

        fixture = TransactionFixture(
            result={
                fork: result,
            },
            transaction=tx.rlp(),
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
