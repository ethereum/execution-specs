"""Test specification for blob tests."""

from typing import Callable, ClassVar, Generator, List, Sequence, Type

from execution_testing.base_types import Alloc
from execution_testing.base_types.base_types import Hash
from execution_testing.client_clis import TransitionTool
from execution_testing.execution import BaseExecute, BlobTransaction
from execution_testing.fixtures import (
    FixtureFormat,
    LabeledFixtureFormat,
)
from execution_testing.test_types import (
    NetworkWrappedTransaction,
    Transaction,
)

from .base import BaseTest, ExecuteFormat, FillResult, LabeledExecuteFormat


class BlobsTest(BaseTest):
    """Test specification for blob tests."""

    pre: Alloc
    txs: List[NetworkWrappedTransaction | Transaction]
    nonexisting_blob_hashes: List[Hash] | None = None
    interleave_nonexisting_blob_hashes: bool = False
    get_blobs_version: int | None = None
    cell_mask: int | None = None
    custody_columns: bytes | None = None

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
        fixture_format: FixtureFormat | LabeledFixtureFormat,
    ) -> FillResult:
        """Generate the list of test fixtures."""
        del t8n
        raise Exception(f"Unknown fixture format: {fixture_format}")

    def execute(
        self,
        *,
        execute_format: ExecuteFormat | LabeledExecuteFormat,
    ) -> BaseExecute:
        """Generate the list of test fixtures."""
        if execute_format == BlobTransaction:
            return BlobTransaction(
                txs=self.txs,
                nonexisting_blob_hashes=self.nonexisting_blob_hashes,
                interleave_nonexisting_blob_hashes=(
                    self.interleave_nonexisting_blob_hashes
                ),
                get_blobs_version=self.get_blobs_version,
                cell_mask=self.cell_mask,
                custody_columns=self.custody_columns,
            )
        raise Exception(f"Unsupported execute format: {execute_format}")


BlobsTestSpec = Callable[[str], Generator[BlobsTest, None, None]]
BlobsTestFiller = Type[BlobsTest]
