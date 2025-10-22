"""Test specification for blob tests."""

from typing import Callable, ClassVar, Generator, List, Sequence, Type

from ethereum_execution_tests.client_clis import TransitionTool
from ethereum_execution_tests.base_types import Alloc
from ethereum_execution_tests.base_types.base_types import Hash
from ethereum_execution_tests.execution import BaseExecute, BlobTransaction
from ethereum_execution_tests.fixtures import (
    BaseFixture,
    FixtureFormat,
)
from ethereum_execution_tests.forks import Fork
from ethereum_execution_tests.test_types import (
    NetworkWrappedTransaction,
    Transaction,
)

from .base import BaseTest, ExecuteFormat, LabeledExecuteFormat


class BlobsTest(BaseTest):
    """Test specification for blob tests."""

    pre: Alloc
    txs: List[NetworkWrappedTransaction | Transaction]
    nonexisting_blob_hashes: List[Hash] | None = None

    supported_execute_formats: ClassVar[Sequence[LabeledExecuteFormat]] = [
        LabeledExecuteFormat(
            BlobTransaction,
            "blob_transaction_test",
            "A test that executes a blob transaction",
        ),
    ]

    def generate(
        self,
        *,
        t8n: TransitionTool,
        fork: Fork,
        fixture_format: FixtureFormat,
    ) -> BaseFixture:
        """Generate the list of test fixtures."""
        del t8n, fork
        raise Exception(f"Unknown fixture format: {fixture_format}")

    def execute(
        self,
        *,
        fork: Fork,
        execute_format: ExecuteFormat,
    ) -> BaseExecute:
        """Generate the list of test fixtures."""
        del fork

        if execute_format == BlobTransaction:
            return BlobTransaction(
                txs=self.txs,
                nonexisting_blob_hashes=self.nonexisting_blob_hashes,
            )
        raise Exception(f"Unsupported execute format: {execute_format}")


BlobsTestSpec = Callable[[str], Generator[BlobsTest, None, None]]
BlobsTestFiller = Type[BlobsTest]
