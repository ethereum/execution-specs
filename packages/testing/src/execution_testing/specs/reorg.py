"""
Reorg test specification.

A ``ReorgTest`` describes a DAG of blocks (each block names its parent by
label, so side chains are first-class) and an ordered list of Engine API /
JSON-RPC steps that drive a client through reorganizations and verify the
observable results.

Every block is executed by the transition tool against the post-state of its
labeled parent, so sibling blocks and blocks built on top of an invalid block
have correct headers and payloads. Steps whose ``expect`` is left empty are
annotated by the Engine API reference model (``engine_model``), and every
``assertState`` on a fixture block is checked against that block's state.
"""

from typing import (
    Any,
    Callable,
    ClassVar,
    Dict,
    Generator,
    List,
    Sequence,
    Set,
    Tuple,
    Type,
)

from pydantic import Field

from execution_testing.base_types import Number
from execution_testing.client_clis import FillerBackend, LazyAlloc
from execution_testing.fixtures import (
    BlockchainEngineReorgFixture,
    FixtureFormat,
    LabeledFixtureFormat,
)
from execution_testing.fixtures.blockchain import (
    FixtureBlobSchedule,
    FixtureConfig,
    FixtureHeader,
    FixtureNewPayloadRequest,
)
from execution_testing.fixtures.reorg import (
    GENESIS_LABEL,
    ZERO_LABEL,
    BlockLabel,
    BlockRef,
    FixtureReorgBlock,
    GetPayloadStep,
    OutcomeStep,
    Step,
)
from execution_testing.test_types import Alloc, Environment

from .base import ExecuteFormat, FillResult
from .blockchain import (
    Block,
    BlockchainTest,
    apply_new_parent,
    environment_from_parent_header,
)
from .engine_model import ClientModel, DagBlock, ModelDag, annotate_steps
from .helpers import RecordedPostStateContext


class ReorgBlock(Block):
    """
    A block of the reorg DAG.

    ``parent`` names the parent block by label; when unset the block extends
    the previous block in the list (or genesis for the first block).
    """

    label: BlockLabel
    parent: BlockRef | None = None

    @property
    def payload_corrupted(self) -> bool:
        """Whether the engine payload's hashes are deliberately wrong."""
        return (
            self.engine_new_payload_block_hash is not None
            or self.engine_new_payload_parent_hash is not None
        )


class ReorgTest(BlockchainTest):
    """
    Filler type for Engine API reorg tests: a block DAG plus a step script.
    """

    blocks: List[ReorgBlock]  # type: ignore[assignment]
    steps: List[Step]
    post: Alloc = Field(default_factory=Alloc)
    """Must stay empty: a DAG has no single final block."""
    min_reorg_depth: Number | None = None
    """
    Minimum side-chain reorg depth (in blocks) the client must apply
    without refusing for capacity reasons; the consumer sets the client's
    cap to it.
    """

    supported_fixture_formats: ClassVar[
        Sequence[FixtureFormat | LabeledFixtureFormat]
    ] = [BlockchainEngineReorgFixture]
    supported_execute_formats: ClassVar[Sequence] = []
    supported_markers: ClassVar[Dict[str, str]] = {}

    def model_post_init(self, __context: Any, /) -> None:
        """
        Reject inherited inputs a DAG cannot honor: inclusion tests and a
        fixture-wide ``post`` assume one final block, a block's Engine API
        error belongs on the ``newPayload`` step that delivers it, and an
        invalid block's ``expected_post_state`` would be compared with the
        state its rejected execution left, not its parent's.
        """
        if self.is_inclusion_test:
            raise ValueError("ReorgTest does not support inclusion tests")
        if self.post.root:
            raise ValueError(
                "ReorgTest does not support a fixture-wide `post` "
                "allocation; verify state per block via "
                "`ReorgBlock.expected_post_state` or `assertState` steps"
            )
        for block in self.blocks:
            if block.engine_api_error_code is not None:
                raise ValueError(
                    f"block {block.label!r}: engine_api_error_code is not "
                    "supported; expect the error on the newPayload step "
                    "that delivers this block instead"
                )
            if block.expected_post_state and (
                block.exception is not None or block.payload_corrupted
            ):
                raise ValueError(
                    f"block {block.label!r}: expected_post_state on an "
                    "invalid block is not supported; check the parent's "
                    "state with an assertState step instead"
                )
        super().model_post_init(__context)

    def validate_dag(self) -> None:
        """Check labels are unique and every reference resolves."""
        seen = {GENESIS_LABEL}
        tx_counts: Dict[str, int] = {}
        for block in self.blocks:
            if block.label in seen:
                raise ValueError(f"duplicate block label: {block.label}")
            if block.parent is not None and block.parent not in seen:
                raise ValueError(
                    f"block {block.label!r} references unknown parent "
                    f"{block.parent!r} (parents must be defined earlier)"
                )
            seen.add(block.label)
            tx_counts[block.label] = len(block.txs)
        self._validate_step_labels(self.steps, seen, tx_counts)

    def _validate_step_labels(
        self,
        steps: List[Step],
        labels: Set[str],
        tx_counts: Dict[str, int],
    ) -> None:
        for step in steps:
            if isinstance(step, GetPayloadStep) and step.bind in labels:
                raise ValueError(
                    f"getPayload bind label {step.bind!r} already used"
                )
            for ref in step.label_refs():
                if ref not in labels and ref != ZERO_LABEL:
                    raise ValueError(f"step references unknown label {ref!r}")
            for tx_ref in step.tx_refs():
                if tx_ref.block not in labels:
                    raise ValueError(
                        f"step references transaction of unknown block "
                        f"{tx_ref.block!r}"
                    )
                if int(tx_ref.index) < 0:
                    raise ValueError(
                        f"step references negative transaction index "
                        f"{tx_ref.index} of block {tx_ref.block!r}"
                    )
                count = tx_counts.get(tx_ref.block)
                if count is not None and int(tx_ref.index) >= count:
                    raise ValueError(
                        f"step references transaction index {tx_ref.index} "
                        f"of block {tx_ref.block!r}, which has only "
                        f"{count} transaction(s)"
                    )
            if isinstance(step, GetPayloadStep):
                labels.add(step.bind)
            if isinstance(step, OutcomeStep):
                for branch in step.branches.values():
                    self._validate_step_labels(branch, set(labels), tx_counts)

    def make_reorg_fixture(self, t8n: FillerBackend) -> FillResult:
        """Execute every block against its labeled parent, emit fixture."""
        self.validate_dag()
        pre, genesis = self.make_genesis(BlockchainEngineReorgFixture)
        fixture_blocks, dag_blocks, post_states = self._build_blocks(
            t8n, pre, genesis.header
        )

        def post_state(label: str) -> Alloc | None:
            alloc = post_states.get(label)
            if isinstance(alloc, LazyAlloc):
                return alloc.materialize()
            return alloc

        model = ClientModel(
            dag=ModelDag(blocks=dag_blocks, post_state=post_state)
        )
        steps = annotate_steps(
            [s.model_copy(deep=True) for s in self.steps], model, self.fork
        )
        fixture = BlockchainEngineReorgFixture(
            fork=self.fork,
            genesis=genesis.header,
            pre=pre,
            blocks=fixture_blocks,
            steps=steps,
            min_reorg_depth=self.min_reorg_depth,
            config=FixtureConfig(
                fork=self.fork,
                chain_id=self.chain_id,
                blob_schedule=FixtureBlobSchedule.from_blob_schedule(
                    self.fork.transitions_to().blob_schedule()
                ),
            ),
        )
        return FillResult(
            fixture=fixture,
            gas_optimization=None,
        )

    def _build_blocks(
        self, t8n: FillerBackend, pre: Alloc, genesis: FixtureHeader
    ) -> Tuple[
        Dict[str, FixtureReorgBlock],
        Dict[str, DagBlock],
        Dict[str, Alloc | LazyAlloc],
    ]:
        """
        Execute every block on its labeled parent's post-state; return the
        fixture blocks, the reference model's record of each block, and each
        label's post-state.
        """
        genesis_fcu = (
            self.fork.transitions_from().engine_forkchoice_updated_version()
        )
        assert genesis_fcu is not None, "reorg tests require the Engine API"
        dag_blocks: Dict[str, DagBlock] = {
            GENESIS_LABEL: DagBlock(
                parent=None,
                timestamp=int(genesis.timestamp),
                gas_limit=int(genesis.gas_limit),
                slot=int(genesis.slot_number or 0),
                fcu_version=genesis_fcu,
            )
        }
        # Per-label state needed to build children: environment of the next
        # block and post-state allocation.
        child_env: Dict[str, Environment] = {
            GENESIS_LABEL: environment_from_parent_header(genesis)
        }
        child_alloc: Dict[str, Alloc | LazyAlloc] = {GENESIS_LABEL: pre}
        # Landings of the transactions in each label's post-state: siblings
        # can include the same transaction at different prices, so each
        # block resolves fees against its own ancestry only.
        child_landings: Dict[str, RecordedPostStateContext] = {
            GENESIS_LABEL: RecordedPostStateContext()
        }
        fixture_blocks: Dict[str, FixtureReorgBlock] = {}

        previous_label = GENESIS_LABEL
        for block in self.blocks:
            parent = block.parent or previous_label
            built = self.generate_block_data(
                t8n=t8n,
                block=block,
                previous_env=child_env[parent],
                previous_alloc=child_alloc[parent],
            )
            if self.verifications:
                self.run_block_verifications(
                    result=built.result,
                    block_number=int(built.header.number),
                )
            payload = built.get_fixture_engine_new_payload()
            fixture_blocks[block.label] = FixtureReorgBlock(
                parent=parent,
                payload=FixtureNewPayloadRequest(
                    params=payload.params,
                    new_payload_version=payload.new_payload_version,
                ),
            )
            dag_blocks[block.label] = DagBlock(
                parent=parent,
                timestamp=int(built.header.timestamp),
                gas_limit=int(built.header.gas_limit),
                slot=int(built.header.slot_number or 0),
                fcu_version=int(payload.forkchoice_updated_version),
                valid=block.exception is None and not block.payload_corrupted,
                hash_invalid=block.payload_corrupted,
            )
            # Children of an invalid block are built on the (correct)
            # post-state of its execution and on its (modified) header.
            child_env[block.label] = apply_new_parent(built.env, built.header)
            child_alloc[block.label] = built.alloc
            child_landings[block.label] = RecordedPostStateContext(
                landings=dict(child_landings[parent].landings)
            )
            built.record_landings(child_landings[block.label])
            if block.expected_post_state:
                self.verify_post_state(
                    t8n=t8n,
                    pre_alloc=pre,
                    got_alloc=built.alloc.materialize()
                    if isinstance(built.alloc, LazyAlloc)
                    else built.alloc,
                    context=child_landings[block.label],
                    expected_state=block.expected_post_state,
                )
            previous_label = block.label
        return fixture_blocks, dag_blocks, child_alloc

    def generate(
        self,
        t8n: FillerBackend,
        fixture_format: FixtureFormat | LabeledFixtureFormat,
    ) -> FillResult:
        """Generate the reorg fixture."""
        if fixture_format == BlockchainEngineReorgFixture:
            return self.make_reorg_fixture(t8n)
        raise Exception(f"Unknown fixture format: {fixture_format}")

    def execute(self, *, execute_format: ExecuteFormat) -> None:  # type: ignore[override]
        """Reorg tests cannot be executed against a live network."""
        raise Exception(f"Unsupported execute format: {execute_format}")


ReorgTestSpec = Callable[[str], Generator[ReorgTest, None, None]]
ReorgTestFiller = Type[ReorgTest]

__all__ = [
    "ReorgBlock",
    "ReorgTest",
    "ReorgTestFiller",
    "ReorgTestSpec",
]
