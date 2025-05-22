"""Test specification for blob tests."""

from typing import Callable, ClassVar, Generator, List, Optional, Sequence, Type

from ethereum_clis import TransitionTool
from ethereum_test_base_types import Alloc
from ethereum_test_execution import BaseExecute, BlobTransaction
from ethereum_test_fixtures import (
    BaseFixture,
    FixtureFormat,
)
from ethereum_test_forks import Fork
from ethereum_test_types import NetworkWrappedTransaction, Transaction

from .base import BaseTest, ExecuteFormat, LabeledExecuteFormat


class BlobsTest(BaseTest):
    """Test specification for blob tests."""

    pre: Alloc
    txs: List[NetworkWrappedTransaction | Transaction]

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
        eips: Optional[List[int]] = None,
    ) -> BaseFixture:
        """Generate the list of test fixtures."""
        raise Exception(f"Unknown fixture format: {fixture_format}")

    def execute(
        self,
        *,
        fork: Fork,
        execute_format: ExecuteFormat,
        eips: Optional[List[int]] = None,
    ) -> BaseExecute:
        """Generate the list of test fixtures."""
        if execute_format == BlobTransaction:
            return BlobTransaction(
                txs=self.txs,
            )
        raise Exception(f"Unsupported execute format: {execute_format}")


BlobsTestSpec = Callable[[str], Generator[BlobsTest, None, None]]
BlobsTestFiller = Type[BlobsTest]
