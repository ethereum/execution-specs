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
from functools import cached_property
from typing import (
    Any,
    Dict,
    List,
    Sequence,
    SupportsBytes,
    SupportsIndex,
)

from pydantic import BaseModel
from pydantic_core import PydanticSerializationError

from execution_testing.base_types import Address
from execution_testing.client_clis import TransitionTool
from execution_testing.client_clis.cli_types import (
    Result,
    Traces,
    TransactionTraces,
)
from execution_testing.fixtures import BlockchainFixture
from execution_testing.forks import Fork, TransitionFork
from execution_testing.test_types import (
    Alloc,
    Environment,
    Transaction,
    TransactionLog,
    TransactionReceipt,
)
from execution_testing.test_types.balance_expectations import (
    transaction_key,
)
from execution_testing.test_types.chain_config_types import (
    ChainConfigDefaults,
)

from .blockchain import Block, BlockchainTest, BuiltBlock
from .evaluate_trace import Trace, TraceError


@dataclass(kw_only=True)
class SpecRunTransaction:
    """A transaction of a run, and its outcome."""

    tx: Transaction
    """Transaction as the transition tool ran it."""

    receipt: TransactionReceipt | None
    """Receipt of the transaction (`None` when it was rejected)."""

    transaction_traces: TransactionTraces | None
    """Traces the transition tool reported for the transaction."""

    traced: bool
    """Whether the run collected traces."""

    @property
    def rejected(self) -> bool:
        """Whether the transaction was rejected, so it never ran."""
        return self.receipt is None

    @property
    def successful(self) -> bool:
        """
        Whether the transaction ran and succeeded.

        Receipts carry no status before Byzantium, so this raises there.
        """
        if self.receipt is None:
            return False
        if self.receipt.status is None:
            raise ValueError(
                "the receipt has no status (before Byzantium): check the "
                "post state instead"
            )
        return int(self.receipt.status) == 1

    @property
    def failed(self) -> bool:
        """Whether the transaction was rejected, reverted or halted."""
        return not self.successful

    @property
    def logs(self) -> List[TransactionLog]:
        """Logs the transaction emitted."""
        if self.receipt is None:
            return []
        return list(self.receipt.logs or [])

    @property
    def trace(self) -> Trace | None:
        """
        Trace of the transaction (`None` when it was rejected).

        Raises unless the run collected traces (`spec.run(traces=True)`).
        """
        if not self.traced:
            raise ValueError(
                "the run did not collect traces: pass `traces=True` to "
                "`spec.run`"
            )
        if self.receipt is None:
            return None
        if self.transaction_traces is None:
            raise ValueError("the transition tool reported no traces")
        return Trace.from_transaction(
            self.transaction_traces,
            address=Address(
                self.tx.to
                if self.tx.to is not None
                else self.tx.created_contract
            ),
        )

    @property
    def error(self) -> TraceError | None:
        """
        Error that stopped the transaction (`None` if it succeeded or was
        rejected).

        Raises unless the run collected traces.
        """
        trace = self.trace
        return None if trace is None else trace.error


@dataclass(kw_only=True)
class SpecRunBlock:
    """A block of a run, and its outcome."""

    built: BuiltBlock
    """Block as the transition tool built it."""

    txs: List[SpecRunTransaction]
    """Transactions of the block, in order."""

    @property
    def successful(self) -> bool:
        """Whether the block is valid and all its transactions succeeded."""
        return self.built.expected_exception is None and all(
            tx.successful for tx in self.txs
        )

    @property
    def failed(self) -> bool:
        """Whether the block is invalid or a transaction failed."""
        return not self.successful


@dataclass(kw_only=True)
class SpecRun:
    """Result of one run of the spec over a list of blocks."""

    blocks: List[BuiltBlock]
    """Blocks as built by the transition tool, in order."""

    post: Alloc
    """State after the last valid block."""

    source_blocks: List[Block] = field(default_factory=list, repr=False)
    """Blocks the run was given, in the order of `blocks`."""

    traced: bool = False
    """Whether the run collected traces."""

    @cached_property
    def outcomes(self) -> List[SpecRunBlock]:
        """Outcome of each block, and of each of its transactions."""
        outcomes: List[SpecRunBlock] = []
        for block in self.blocks:
            result = block.result
            rejected = {int(r.index) for r in result.rejected_transactions}
            receipts = iter(result.receipts)
            traces = iter(result.traces.root if result.traces else [])
            txs: List[SpecRunTransaction] = []
            for index, tx in enumerate(block.txs):
                receipt = None
                transaction_traces = None
                if index not in rejected:
                    # Receipts and traces follow the transactions that ran.
                    receipt = next(receipts)
                    transaction_traces = next(traces, None)
                    assert receipt.transaction_hash in (None, tx.hash), (
                        f"receipt of transaction {index} does not match it"
                    )
                txs.append(
                    SpecRunTransaction(
                        tx=tx,
                        receipt=receipt,
                        transaction_traces=transaction_traces,
                        traced=self.traced,
                    )
                )
            outcomes.append(SpecRunBlock(built=block, txs=txs))
        return outcomes

    @property
    def txs(self) -> List[SpecRunTransaction]:
        """Transactions of all blocks, in order."""
        return [tx for block in self.outcomes for tx in block.txs]

    @property
    def successful(self) -> bool:
        """Whether every block is valid and every transaction succeeded."""
        return all(block.successful for block in self.outcomes)

    @property
    def failed(self) -> bool:
        """Whether a block is invalid or a transaction failed."""
        return not self.successful

    def tx(self, tx: Transaction) -> SpecRunTransaction:
        """
        Return the outcome of `tx`.

        The transition tool runs copies of the transactions it is given
        (signed, with a gas limit), so `tx` is found by its sender and
        nonce.
        """
        key = transaction_key(tx)
        matches = [t for t in self.txs if transaction_key(t.tx) == key]
        if not matches:
            sender, nonce = key
            raise KeyError(
                f"no transaction from {sender} with nonce {nonce} in the run"
            )
        if len(matches) > 1:
            raise ValueError(
                "several transactions of the run have the sender and nonce "
                "of `tx`: use `run.block(block).txs` instead"
            )
        return matches[0]

    def block(self, block: Block) -> SpecRunBlock:
        """Return the outcome of `block`, one of the blocks of the run."""
        for source, outcome in zip(
            self.source_blocks, self.outcomes, strict=True
        ):
            if source is block:
                return outcome
        raise KeyError("the block is not one of the blocks of the run")

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
        """Traces of each block (`None` unless run with `traces=True`)."""
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
        traces: bool = False,
    ) -> SpecRun:
        """
        Run `blocks` (or a single block with `txs`) on top of `pre`.

        The blocks form a chain on top of a genesis block, so their numbers
        are consecutive. If the first block sets `number=N` and
        `genesis_environment` sets no number, the genesis is block `N - 1`.

        A transaction or block that the spec rejects and that is not
        expected to fail (`error` / `exception`) raises an exception, as
        does a block whose `expected_post_state` does not match.

        With `traces=True`, the run collects the traces of its transactions
        (`run.tx(tx).trace`). Only the run decides, so its outcome does not
        depend on how the session was started.
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
        previous_trace = self.t8n.trace
        self.t8n.trace = traces
        try:
            chain = test.run_blocks(
                self.t8n, BlockchainFixture, check_exception_test=False
            )
        finally:
            self.t8n.trace = previous_trace
        self.run_count += 1
        return SpecRun(
            blocks=chain.blocks,
            post=chain.alloc,
            source_blocks=list(blocks),
            traced=traces,
        )

    def record(self, **values: Any) -> None:
        """
        Record values in the evaluation report of the current test.

        Values are converted to built-in types as they are recorded, so a
        value of a type that cannot be converted fails the test here.
        """
        self.records.update(
            {name: to_primitive(value) for name, value in values.items()}
        )


def to_primitive(value: Any) -> Any:
    """
    Convert a recorded value to built-in types.

    Pytest-xdist workers send reports to the controller through execnet,
    which only serializes built-in types, so subclasses such as `HexNumber`
    or `Address` are converted to the built-in type they derive from,
    integer-like values such as `Uint` (anything that supports
    `operator.index`) to `int`, enums to their value, values that convert
    to bytes, such as `Bytecode` or a request, to hex and other pydantic
    models to their JSON form. A value of any other type, or a model that
    cannot be serialized, raises `TypeError`.
    """
    if value is None or type(value) in (bool, int, float, str):
        return value
    if isinstance(value, Enum):
        return to_primitive(value.value)
    if isinstance(value, bool):
        return bool(value)
    if isinstance(value, SupportsIndex):
        return operator.index(value)
    if isinstance(value, float):
        return float(value)
    if isinstance(value, str):
        return str(value)
    if isinstance(value, (bytes, SupportsBytes)):
        return "0x" + bytes(value).hex()
    if isinstance(value, BaseModel):
        try:
            return value.model_dump(mode="json")
        except PydanticSerializationError as e:
            raise TypeError(
                f"cannot record a `{type(value).__name__}`: {e}"
            ) from e
    if isinstance(value, dict):
        return {str(k): to_primitive(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set, frozenset)):
        return [to_primitive(v) for v in value]
    raise TypeError(
        f"cannot record a value of type `{type(value).__name__}`: convert "
        "it to a built-in type first"
    )
