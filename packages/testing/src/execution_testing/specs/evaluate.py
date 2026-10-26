"""
Spec runner: run blocks of transactions against the spec and return the
results to the test.

Unlike `fill`, `evaluate` does not produce fixtures. A test runs the spec as
many times as it needs, with whatever inputs it needs, and asserts on the
results in plain Python. The outcome of the test is the result.
"""

import operator
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Sequence, SupportsIndex

from pydantic import BaseModel

from execution_testing.base_types import Address
from execution_testing.client_clis import TransitionTool
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

from .blockchain import Block, BlockchainTest, BuiltBlock


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
        expected to fail (`error` / `exception`) raises an exception, as
        does a block whose `expected_post_state` does not match.
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
        parent_number = int(test.get_genesis_environment().number)
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
            if block.exception is None:
                parent_number += 1
        chain = test.run_blocks(
            self.t8n, BlockchainFixture, check_exception_test=False
        )
        self.run_count += 1
        return SpecRun(blocks=chain.blocks, post=chain.alloc)

    def record(self, **values: Any) -> None:
        """
        Record values in the evaluation report of the current test.

        Values are converted to built-in types as they are recorded, so a
        value of a type that cannot be converted fails the test here.
        """
        self.records.update(
            {name: _to_primitive(value) for name, value in values.items()}
        )


def _to_primitive(value: Any) -> Any:
    """
    Convert a recorded value to built-in types.

    Pytest-xdist workers send reports to the controller through execnet,
    which only serializes built-in types, so subclasses such as `HexNumber`
    or `Address` are converted to the built-in type they derive from,
    integer-like values such as `Uint` (anything that supports
    `operator.index`) to `int`, enums to their value and pydantic models to
    their JSON form. A value of any other type raises `TypeError`.
    """
    if value is None or type(value) in (bool, int, float, str):
        return value
    if isinstance(value, Enum):
        return _to_primitive(value.value)
    if isinstance(value, bool):
        return bool(value)
    if isinstance(value, SupportsIndex):
        return operator.index(value)
    if isinstance(value, float):
        return float(value)
    if isinstance(value, str):
        return str(value)
    if isinstance(value, bytes):
        return "0x" + bytes(value).hex()
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if isinstance(value, dict):
        return {str(k): _to_primitive(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set, frozenset)):
        return [_to_primitive(v) for v in value]
    raise TypeError(
        f"cannot record a value of type `{type(value).__name__}`: convert "
        "it to a built-in type first"
    )
