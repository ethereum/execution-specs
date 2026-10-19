"""Ethereum transaction test spec definition and filler."""

from typing import Callable, ClassVar, Generator, Mapping, Sequence, Type

from execution_testing.client_clis import TransitionTool
from execution_testing.execution import (
    BaseExecute,
    ExecuteFormat,
    LabeledExecuteFormat,
    MempoolAdmission,
)
from execution_testing.fixtures import (
    FixtureFormat,
    LabeledFixtureFormat,
    TransactionFixture,
)
from execution_testing.fixtures.transaction import FixtureResult
from execution_testing.forks import Fork, TransitionFork
from execution_testing.recipient_type import RecipientType
from execution_testing.test_types import (
    Alloc,
    MempoolTransaction,
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
            MempoolAdmission,
            "transaction_test",
            "An execute test sending the transaction to the client's "
            "public mempool, which must reject an invalid one",
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
        """
        Execute the transaction test by sending it to the client's public
        mempool, which must admit a valid transaction and reject an
        invalid one.
        """
        if execute_format == MempoolAdmission:
            return MempoolAdmission(
                txs=[
                    MempoolTransaction(
                        tx=self.tx, accepted=self.tx.error is None
                    )
                ],
                benchmark_mode=self.operation_mode == OpMode.BENCHMARKING,
            )
        raise Exception(f"Unsupported execute format: {execute_format}")


TransactionTestSpec = Callable[[str], Generator[TransactionTest, None, None]]
TransactionTestFiller = Type[TransactionTest]
