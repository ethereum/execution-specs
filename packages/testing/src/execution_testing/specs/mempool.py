"""Test specification for public mempool admission tests."""

from typing import (
    Callable,
    ClassVar,
    Dict,
    Generator,
    List,
    Sequence,
    Tuple,
    Type,
)

from pydantic import Field, model_validator
from typing_extensions import Self

from execution_testing.client_clis import TransitionTool
from execution_testing.execution import (
    BaseExecute,
    ExecuteFormat,
    LabeledExecuteFormat,
)
from execution_testing.execution.mempool import MempoolAdmission
from execution_testing.fixtures import (
    FixtureFormat,
    LabeledFixtureFormat,
)
from execution_testing.test_types import (
    Alloc,
    Environment,
    MempoolTransaction,
    Transaction,
)

from .base import BaseTest, FillResult
from .blockchain import Block, BlockchainTest


class MempoolTest(BaseTest):
    """
    Test specification for public mempool admission.

    Executing the test sends the transactions in order to the client and
    checks that its public mempool admits or rejects each one. Filling
    the test places them in a single block that must be valid, showing
    that a rejection is mempool policy and not consensus.
    """

    pre: Alloc
    post: Alloc = Field(default_factory=Alloc)
    """Post state of the filled block; never checked by execute."""
    txs: List[MempoolTransaction]
    genesis_environment: Environment = Field(default_factory=Environment)

    supported_fixture_formats: ClassVar[
        Sequence[FixtureFormat | LabeledFixtureFormat]
    ] = [
        fixture_format.with_label_suffix(
            "from_mempool_test",
            f"A {fixture_format.format_id()} generated from a mempool_test",
        )
        for fixture_format in BlockchainTest.supported_fixture_formats
        if "Sync" not in fixture_format.format_class().__name__
    ]
    supported_execute_formats: ClassVar[Sequence[LabeledExecuteFormat]] = [
        LabeledExecuteFormat(
            MempoolAdmission,
            "mempool_test",
            "A test that sends transactions to the client's public mempool",
        ),
    ]

    @model_validator(mode="after")
    def _check_transactions(self) -> Self:
        """
        Reject transaction lists that cannot be both sent in order and
        filled as a valid block.
        """
        explicit: Dict[Tuple, int] = {}
        next_pool_nonce: Dict[Tuple, int] = {}
        signature_ids: Dict[int, int] = {}
        for index, entry in enumerate(self.txs):
            tx = entry.tx
            if tx.error is not None:
                raise ValueError(
                    f"tx {index} expects a consensus error; a mempool test "
                    "only holds transactions that are valid in a block."
                )
            key = entry.pool_key
            if entry.in_block:
                explicit[key] = explicit.get(key, 0) + 1
                if explicit[key] > 1:
                    raise ValueError(
                        f"tx {index} is the second transaction placed in "
                        "the block for the same sender and nonce."
                    )
            sender_key = key[:2]
            nonce = key[2]
            expected = next_pool_nonce.setdefault(sender_key, nonce)
            if nonce > expected:
                raise ValueError(
                    f"tx {index} leaves a nonce gap: no admitted "
                    f"transaction precedes nonce {nonce}."
                )
            if entry.accepted:
                next_pool_nonce[sender_key] = max(expected, nonce + 1)
            for signature in tx.signatures or []:
                owner = signature_ids.setdefault(id(signature), index)
                if owner != index:
                    raise ValueError(
                        f"tx {index} shares a signature entry with tx "
                        f"{owner}; build each transaction separately."
                    )
        return self

    def block_transactions(self) -> List[Transaction]:
        """
        Return the transactions placed in the filled block, in send
        order.

        Of the transactions sharing a sender and nonce, the block holds
        the one marked `in_block`, otherwise the last one the mempool
        admits, otherwise the first one. Transactions marked
        `in_block=False` are never placed.
        """
        groups: Dict[Tuple, List[int]] = {}
        for index, entry in enumerate(self.txs):
            groups.setdefault(entry.pool_key, []).append(index)
        chosen: List[int] = []
        for indexes in groups.values():
            explicit = [i for i in indexes if self.txs[i].in_block]
            if explicit:
                chosen.append(explicit[0])
                continue
            candidates = [i for i in indexes if self.txs[i].in_block is None]
            accepted = [i for i in candidates if self.txs[i].accepted]
            if accepted:
                chosen.append(accepted[-1])
            elif candidates:
                chosen.append(candidates[0])
        return [self.txs[i].tx for i in sorted(chosen)]

    def generate_blockchain_test(self) -> BlockchainTest:
        """Create a BlockchainTest holding the block of this test."""
        return BlockchainTest.from_test(
            base_test=self,
            genesis_environment=self.genesis_environment,
            pre=self.pre,
            post=self.post,
            blocks=[Block(txs=self.block_transactions())],
        )

    def get_genesis_environment(self) -> Environment:
        """Get the genesis environment for pre-allocation groups."""
        return self.generate_blockchain_test().get_genesis_environment()

    def generate(
        self,
        *,
        t8n: TransitionTool,
        fixture_format: FixtureFormat | LabeledFixtureFormat,
    ) -> FillResult:
        """Generate the blockchain test fixture."""
        self.check_exception_test(exception=False)
        if fixture_format in BlockchainTest.supported_fixture_formats:
            return self.generate_blockchain_test().generate(
                t8n=t8n, fixture_format=fixture_format
            )
        raise Exception(f"Unknown fixture format: {fixture_format}")

    def execute(
        self,
        *,
        execute_format: ExecuteFormat | LabeledExecuteFormat,
    ) -> BaseExecute:
        """Generate the list of test fixtures."""
        if execute_format == MempoolAdmission:
            return MempoolAdmission(txs=self.txs)
        raise Exception(f"Unsupported execute format: {execute_format}")


MempoolTestSpec = Callable[[str], Generator[MempoolTest, None, None]]
MempoolTestFiller = Type[MempoolTest]
