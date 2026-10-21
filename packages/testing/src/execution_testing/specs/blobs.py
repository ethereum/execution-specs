"""Test specification for blob tests."""

from typing import (
    Callable,
    ClassVar,
    Generator,
    List,
    Mapping,
    Sequence,
    Type,
)

from pydantic import model_validator
from typing_extensions import Self

from execution_testing.base_types import Alloc
from execution_testing.base_types.base_types import Hash
from execution_testing.client_clis import TransitionTool
from execution_testing.execution import (
    BaseExecute,
    GetBlobs,
    MempoolAdmission,
)
from execution_testing.fixtures import (
    FixtureFormat,
    LabeledFixtureFormat,
)
from execution_testing.forks import Fork, TransitionFork
from execution_testing.test_types import (
    MempoolTransaction,
    NetworkWrappedTransaction,
    Transaction,
)

from .base import BaseTest, ExecuteFormat, FillResult, LabeledExecuteFormat


class BlobsTest(BaseTest):
    """
    Test specification for blob tests.

    Executing the test sends every transaction expecting the mempool to
    admit it, then checks the blobs via `engine_getBlobsV*`, as a
    `mempool_test` with a `GetBlobs` check does.
    """

    pre: Alloc
    txs: List[NetworkWrappedTransaction | Transaction]
    nonexisting_blob_hashes: List[Hash] | None = None
    interleave_nonexisting_blob_hashes: bool = False
    get_blobs_version: int | None = None
    cell_mask: int | None = None
    custody_columns_updates: List[bytes | None] | None = None
    """
    `custodyColumns` values to send in order, one
    `engine_forkchoiceUpdatedV4` each, before `engine_getBlobsV*`: a bitmap
    sends that value and `None` sends an explicit `null`. Leave unset to
    send no update.
    """

    @model_validator(mode="after")
    def _check_custody_columns_updates(self) -> Self:
        """Reject an empty update list, which would send nothing."""
        if self.custody_columns_updates is not None and not (
            self.custody_columns_updates
        ):
            raise ValueError(
                "custody_columns_updates must hold at least one update; "
                "leave it unset to send no custodyColumns update."
            )
        return self

    supported_execute_formats: ClassVar[Sequence[LabeledExecuteFormat]] = [
        LabeledExecuteFormat(
            MempoolAdmission,
            "blob_transaction_test",
            "A test that executes a blob transaction",
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
        if execute_format == MempoolAdmission:
            get_blobs = GetBlobs(
                version=self.get_blobs_version,
                nonexisting_blob_hashes=self.nonexisting_blob_hashes,
                interleave_nonexisting_blob_hashes=(
                    self.interleave_nonexisting_blob_hashes
                ),
                cell_mask=self.cell_mask,
                custody_columns_updates=self.custody_columns_updates,
            )
            return MempoolAdmission(
                txs=[
                    MempoolTransaction(tx=tx, accepted=True) for tx in self.txs
                ],
                checks=[get_blobs],
            )
        raise Exception(f"Unsupported execute format: {execute_format}")


BlobsTestSpec = Callable[[str], Generator[BlobsTest, None, None]]
BlobsTestFiller = Type[BlobsTest]
