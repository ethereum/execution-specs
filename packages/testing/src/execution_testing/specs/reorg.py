"""
Reorg test specification.

A ``ReorgTest`` describes a DAG of blocks (each block names its parent by
label, so side chains are first-class) and an ordered list of Engine API /
JSON-RPC steps that drive a client through reorganizations and verify the
observable results.

Every block is executed by the transition tool against the post-state of its
labeled parent, so sibling blocks and blocks built on top of an invalid block
have correct headers and payloads. Steps whose ``expect`` is left empty are
annotated by the Engine API reference model (``engine_model``).
"""

from typing import (
    Any,
    Callable,
    ClassVar,
    Dict,
    Generator,
    List,
    Sequence,
    Type,
)

from pydantic import Field

from execution_testing.base_types import Hash, HexNumber
from execution_testing.client_clis import FillerBackend, LazyAlloc
from execution_testing.fixtures import (
    BlockchainEngineReorgFixture,
    FixtureFormat,
    LabeledFixtureFormat,
)
from execution_testing.fixtures.blockchain import (
    FixtureBlobSchedule,
    FixtureConfig,
)
from execution_testing.fixtures.post_verifications import PostVerifications
from execution_testing.fixtures.reorg import (
    GENESIS_LABEL,
    MAIN_CLIENT,
    ZERO_LABEL,
    AssertCanonicalStep,
    AssertHeadStep,
    AssertLogsStep,
    AssertReceiptStep,
    AssertStateStep,
    AssertTxStatusStep,
    FixtureClient,
    FixtureReorgBlock,
    ForkchoiceUpdatedStep,
    GetPayloadStep,
    NewPayloadStep,
    SendRawTransactionStep,
    Step,
    TxRef,
    WaitForHeadStep,
)
from execution_testing.test_types import Alloc, Environment

from .base import ExecuteFormat, FillResult
from .blockchain import (
    Block,
    BlockchainTest,
    apply_new_parent,
    environment_from_parent_header,
)
from .engine_model import ClientModel, ModelDag, annotate_steps


class ReorgBlock(Block):
    """
    A block of the reorg DAG.

    ``parent`` names the parent block by label; when unset the block extends
    the previous block in the list (or genesis for the first block).
    """

    label: str
    parent: str | None = None
    payload_block_hash: Hash | None = None
    """Override ``blockHash`` in the engine payload only (hash mismatch)."""
    payload_parent_hash: Hash | None = None
    """Override ``parentHash`` in the engine payload only."""

    @property
    def payload_corrupted(self) -> bool:
        """Whether the engine payload is deliberately inconsistent."""
        return (
            self.payload_block_hash is not None
            or self.payload_parent_hash is not None
        )


class ReorgTest(BlockchainTest):
    """
    Filler type for Engine API reorg tests: a block DAG plus a step script.
    """

    blocks: List[ReorgBlock]  # type: ignore[assignment]
    steps: List[Step]
    post: Alloc = Field(default_factory=Alloc)
    """Optional; ``assertState`` steps are the primary state verification."""
    requires: Dict[str, str] | None = None
    """Client environment variables (``HIVE_*``) required by this test."""
    clients: Dict[str, FixtureClient] = Field(default_factory=dict)
    """
    Additional clients (peers of ``main``) used by ``on``/``waitForHead``.
    """
    meta: Dict[str, str | int] = Field(default_factory=dict)

    supported_fixture_formats: ClassVar[
        Sequence[FixtureFormat | LabeledFixtureFormat]
    ] = [BlockchainEngineReorgFixture]
    supported_execute_formats: ClassVar[Sequence] = []
    supported_markers: ClassVar[Dict[str, str]] = {}

    def model_post_init(self, __context: Any, /) -> None:
        """
        Run static checks.

        ``BlockchainTest``'s inclusion-test check assumes ``self.blocks`` is
        a linear chain (only the last block may carry the trailing invalid
        transaction); a labeled DAG has no single "last" block, so the
        marker that requests it is rejected here instead of silently
        checking it against list order. Verify inclusion with
        ``assertTxStatus``/``assertReceipt`` steps instead.
        """
        if self.is_inclusion_test:
            raise ValueError("ReorgTest does not support inclusion tests")
        super().model_post_init(__context)

    def validate_dag(self) -> None:
        """
        Check labels are unique, reserved names unused, parents resolvable.
        """
        seen = {GENESIS_LABEL}
        for block in self.blocks:
            if block.label in (GENESIS_LABEL, ZERO_LABEL, "null", "any"):
                raise ValueError(f"reserved block label: {block.label}")
            if block.label in seen:
                raise ValueError(f"duplicate block label: {block.label}")
            if block.parent is not None and block.parent not in seen:
                raise ValueError(
                    f"block {block.label!r} references unknown parent "
                    f"{block.parent!r} (parents must be defined earlier)"
                )
            seen.add(block.label)
        self._validate_step_labels(self.steps, seen)

    def _validate_step_labels(self, steps: List[Step], labels: set) -> None:
        clients = {MAIN_CLIENT, *self.clients}
        for step in steps:
            if step.on not in clients:
                raise ValueError(f"step targets unknown client {step.on!r}")
            refs: List[str] = []
            tx_refs: List[TxRef] = []
            if isinstance(step, NewPayloadStep):
                refs = [step.block]
            elif isinstance(step, ForkchoiceUpdatedStep):
                refs = [step.head, step.safe, step.finalized]
            elif isinstance(step, GetPayloadStep):
                refs = [step.parent]
                if step.bind in labels or step.bind in (
                    ZERO_LABEL,
                    "null",
                    "any",
                ):
                    raise ValueError(
                        f"getPayload bind label {step.bind!r} already used"
                    )
                tx_refs = step.transactions_include + step.transactions_exclude
            elif isinstance(step, (AssertHeadStep,)):
                refs = [
                    x
                    for x in (step.latest, step.safe, step.finalized)
                    if x is not None
                ]
            elif isinstance(step, WaitForHeadStep):
                refs = [step.latest]
            elif isinstance(step, AssertCanonicalStep):
                refs = [x for x in step.blocks.values() if x is not None]
            elif isinstance(step, AssertStateStep):
                refs = [] if step.at == "latest" else [step.at]
            elif isinstance(step, AssertReceiptStep):
                refs = [step.block] if step.block is not None else []
                tx_refs = [step.tx]
            elif isinstance(step, AssertLogsStep):
                refs = list(step.blocks)
            elif isinstance(step, SendRawTransactionStep):
                tx_refs = [step.tx]
            elif isinstance(step, AssertTxStatusStep):
                refs = [step.included_in] if step.included_in else []
                tx_refs = [step.tx]
            for ref in refs:
                if ref not in labels and ref != ZERO_LABEL:
                    raise ValueError(f"step references unknown label {ref!r}")
            for tx_ref in tx_refs:
                if tx_ref.block not in labels or tx_ref.block == GENESIS_LABEL:
                    raise ValueError(
                        f"step references transaction of unknown block "
                        f"{tx_ref.block!r}"
                    )
            if isinstance(step, GetPayloadStep):
                labels.add(step.bind)
            for branch in getattr(step, "branches", {}).values():
                self._validate_step_labels(branch, set(labels))

    def _resolve_payload_attributes(
        self, steps: List[Step], timestamps: Dict[str, int]
    ) -> None:
        """
        Fill defaults of ``forkchoiceUpdated.payload_attributes``: a zero
        timestamp becomes ``parent + 12``; Shanghai+ gets empty withdrawals;
        Cancun+ gets a deterministic parent beacon block root. Bound labels
        (client-built payloads) get ``parent + 12`` relative to the parent of
        the build request, which is the previous step's head.
        """
        for step in steps:
            if isinstance(step, GetPayloadStep):
                # Best effort: bound payloads inherit their parent's slot + 12.
                if step.parent in timestamps:
                    timestamps[step.bind] = timestamps[step.parent] + 12
            if isinstance(step, ForkchoiceUpdatedStep):
                attrs = step.payload_attributes
                if attrs is not None:
                    if int(attrs.timestamp) == 0:
                        attrs.timestamp = HexNumber(timestamps[step.head] + 12)
                    fork = self.fork.fork_at(
                        block_number=0, timestamp=int(attrs.timestamp)
                    )
                    if (
                        attrs.withdrawals is None
                        and fork.header_withdrawals_required()
                    ):
                        attrs.withdrawals = []
                    if (
                        attrs.parent_beacon_block_root is None
                        and fork.header_beacon_root_required()
                    ):
                        attrs.parent_beacon_block_root = Hash(0xBEAC0)
            for branch in getattr(step, "branches", {}).values():
                self._resolve_payload_attributes(branch, timestamps)

    def make_reorg_fixture(self, t8n: FillerBackend) -> FillResult:
        """Execute every block against its labeled parent, emit fixture."""
        self.validate_dag()

        pre, genesis = self.make_genesis(apply_pre_allocation_blockchain=True)

        # Per-label state needed to build children: environment of the next
        # block and post-state allocation.
        child_env: Dict[str, Environment] = {
            GENESIS_LABEL: environment_from_parent_header(genesis.header)
        }
        child_alloc: Dict[str, Alloc | LazyAlloc] = {GENESIS_LABEL: pre}
        fixture_blocks: Dict[str, FixtureReorgBlock] = {}
        dag_parent: Dict[str, str] = {}
        dag_valid: Dict[str, bool] = {}
        fcu_version: Dict[str, int] = {}

        genesis_fcu = (
            self.fork.transitions_from().engine_forkchoice_updated_version()
        )
        assert genesis_fcu is not None, "reorg tests require the Engine API"
        fcu_version[GENESIS_LABEL] = genesis_fcu

        previous_label = GENESIS_LABEL
        for block in self.blocks:
            parent = block.parent or previous_label
            built = self.generate_block_data(
                t8n=t8n,
                block=block,
                previous_env=child_env[parent],
                previous_alloc=child_alloc[parent],
            )
            if built.result.receipts:
                self.validate_receipt_status(
                    receipts=built.result.receipts,
                    block_number=int(built.header.number),
                )
            payload = built.get_fixture_engine_new_payload()
            if block.payload_corrupted:
                overrides: Dict[str, Hash] = {}
                if block.payload_block_hash is not None:
                    overrides["block_hash"] = block.payload_block_hash
                if block.payload_parent_hash is not None:
                    overrides["parent_hash"] = block.payload_parent_hash
                params: List[Any] = list(payload.params)
                params[0] = params[0].model_copy(update=overrides)
                payload = payload.model_copy(update={"params": tuple(params)})
            fixture_blocks[block.label] = FixtureReorgBlock(
                parent=parent, payload=payload
            )
            dag_parent[block.label] = parent
            dag_valid[block.label] = (
                block.exception is None and not block.payload_corrupted
            )
            fcu_version[block.label] = int(payload.forkchoice_updated_version)
            # Children of an invalid block are built on the (correct)
            # post-state of its execution and on its (modified) header.
            child_env[block.label] = apply_new_parent(built.env, built.header)
            child_alloc[block.label] = built.alloc
            previous_label = block.label

        timestamps: Dict[str, int] = {
            GENESIS_LABEL: int(genesis.header.timestamp),
            **{
                label: int(b.payload.params[0].timestamp)
                for label, b in fixture_blocks.items()
            },
        }
        steps = [s.model_copy(deep=True) for s in self.steps]
        self._resolve_payload_attributes(steps, timestamps)
        model = ClientModel(dag=ModelDag(parent=dag_parent, valid=dag_valid))
        steps = annotate_steps(steps, model, fcu_version)

        fixture = BlockchainEngineReorgFixture(
            fork=self.fork,
            genesis=genesis.header,
            pre=pre,
            blocks=fixture_blocks,
            steps=steps,
            requires=self.requires,
            clients=dict(self.clients),
            meta=dict(self.meta),
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
            post_verifications=PostVerifications.from_alloc(self.post),
        )

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
    "Hash",
]
