"""
Spec runner: run blocks of transactions against the spec and return the
results to the test.

Unlike `fill`, `evaluate` does not produce fixtures. A test runs the spec as
many times as it needs, with whatever inputs it needs, and asserts on the
results in plain Python. The outcome of the test is the result.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Sequence

from execution_testing.base_types import Address
from execution_testing.client_clis import LazyAlloc, TransitionTool
from execution_testing.client_clis.cli_types import Result, Traces
from execution_testing.fixtures import BlockchainFixture
from execution_testing.forks import Fork, TransitionFork
from execution_testing.test_types import (
    Alloc,
    Environment,
    Transaction,
    TransactionLog,
    TransactionReceipt,
)
from execution_testing.test_types.chain_config_types import (
    ChainConfigDefaults,
)

from .blockchain import (
    Block,
    BlockchainTest,
    BuiltBlock,
    apply_new_parent,
    environment_from_parent_header,
)


@dataclass(kw_only=True)
class SpecRun:
    """Result of one run of the spec over a list of blocks."""

    blocks: List[BuiltBlock]
    """Blocks as built by the transition tool, in order."""

    post: Alloc
    """State after the last valid block."""

    @property
    def results(self) -> List[Result]:
        """Transition tool result of each block."""
        return [block.result for block in self.blocks]

    @property
    def receipts(self) -> List[TransactionReceipt]:
        """Receipts of the transactions of all blocks, in order."""
        return [
            receipt
            for block in self.blocks
            for receipt in block.result.receipts
        ]

    @property
    def traces(self) -> List[Traces | None]:
        """Traces of each block (`None` unless run with `--traces`)."""
        return [block.result.traces for block in self.blocks]

    def logs(
        self, address: Address | int | str | None = None
    ) -> List[TransactionLog]:
        """Return the logs of all transactions, optionally by `address`."""
        logs = [log for receipt in self.receipts for log in receipt.logs or []]
        if address is None:
            return logs
        return [log for log in logs if log.address == Address(address)]

    def storage(self, address: Address | int | str, slot: int) -> int:
        """Return a storage slot of `address` after the run (0 if unset)."""
        account = self.post.get(Address(address))
        if account is None or slot not in account.storage:
            return 0
        return int(account.storage[slot])


@dataclass(kw_only=True)
class SpecRunner:
    """
    Run blocks of transactions against the spec for one fork.

    Every run starts from the `pre` it is given, so runs are independent
    and the order of runs does not matter. A transaction carries its nonce
    from when it was created: build the transactions once and vary them
    with `tx.copy(...)`, since creating a new transaction from the same
    sender increments the sender's nonce.
    """

    t8n: TransitionTool
    fork: Fork | TransitionFork
    chain_id: int = field(default_factory=lambda: ChainConfigDefaults.chain_id)
    records: Dict[str, Any] = field(default_factory=dict)
    run_count: int = 0

    def run(
        self,
        *,
        pre: Alloc,
        txs: Sequence[Transaction] | None = None,
        blocks: Sequence[Block] | None = None,
        genesis_environment: Environment | None = None,
    ) -> SpecRun:
        """
        Run `blocks` (or a single block with `txs`) on top of `pre`.

        The blocks form a chain on top of a genesis block, so their numbers
        are consecutive. If the first block sets `number=N` and
        `genesis_environment` sets no number, the genesis is block `N - 1`.

        A transaction or block that the spec rejects and that is not
        expected to fail (`error` / `exception`) raises an exception.
        """
        if (txs is None) == (blocks is None):
            raise ValueError("pass exactly one of `txs` or `blocks`")
        if blocks is None:
            assert txs is not None
            blocks = [Block(txs=list(txs))]
        genesis_environment = genesis_environment or Environment()
        first_number = blocks[0].number
        if (
            first_number is not None
            and "number" not in genesis_environment.model_fields_set
        ):
            genesis_environment = genesis_environment.copy(
                number=int(first_number) - 1
            )
        test = BlockchainTest(
            pre=pre,
            post=Alloc(),
            blocks=list(blocks),
            genesis_environment=genesis_environment,
            fork=self.fork,
            chain_id=self.chain_id,
        )
        alloc: Alloc | LazyAlloc
        alloc, genesis = test.make_genesis(BlockchainFixture)
        env = environment_from_parent_header(genesis.header)
        parent_number = int(genesis.header.number)
        built_blocks: List[BuiltBlock] = []
        for i, block in enumerate(test.blocks):
            if block.number is not None and int(block.number) != (
                parent_number + 1
            ):
                raise ValueError(
                    f"block {i} has number {int(block.number)}, but its "
                    f"parent is block {parent_number}: block numbers must be "
                    "consecutive. To start the chain at block N, set "
                    "`number=N` on the first block only, or pass "
                    "`genesis_environment=Environment(number=N - 1)`."
                )
            built_block = test.generate_block_data(
                t8n=self.t8n,
                block=block,
                previous_env=env,
                previous_alloc=alloc,
            )
            built_blocks.append(built_block)
            if block.exception is None:
                alloc = built_block.alloc
                env = apply_new_parent(built_block.env, built_block.header)
                parent_number = int(built_block.header.number)
        self.run_count += 1
        return SpecRun(
            blocks=built_blocks,
            post=alloc.materialize()
            if isinstance(alloc, LazyAlloc)
            else alloc,
        )

    def record(self, **values: Any) -> None:
        """Record values in the evaluation report of the current test."""
        self.records.update(values)
