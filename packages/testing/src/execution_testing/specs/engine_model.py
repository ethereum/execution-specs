"""
Engine API reference model used to annotate reorg tests.

The model simulates the forkchoice-relevant state of an execution client
(known blocks and their validity, head/safe/finalized) over the block DAG of a
reorg test, and derives the set of spec-legal outcomes for every
``newPayload`` / ``forkchoiceUpdated`` step whose ``expect`` was left empty.
It also appends ``assertHead`` steps to each outcome's ``branches`` so the
observable head is verified after every forkchoice update.

Rules follow `execution-apis` ``paris.md`` as amended by PR #786:

- ``newPayload``: payload that does not hash to its own ``blockHash`` →
  INVALID with a null ``latestValidHash`` (or ``INVALID_BLOCK_HASH``), checked
  before the parent is looked up; unknown parent → SYNCING; execution-invalid
  → INVALID with ``latestValidHash`` = last valid ancestor; child of a
  known-invalid block →
  INVALID (lvh = last valid ancestor) or SYNCING; extends head → VALID;
  known parent on a side chain → VALID or ACCEPTED.
- ``forkchoiceUpdated``: unknown head → SYNCING; invalid head → INVALID; safe
  or finalized not on head's chain → ``-38002``; head is a VALID ancestor of
  the latest known finalized block → VALID no-op; head extends current head →
  VALID; otherwise (rewind or side-chain reorg) → VALID (applied) or
  ``-38006`` (refused, implementation-specific depth cap). A call that ends in
  an error leaves the forkchoice state untouched, since every update resulting
  from the call has to be applied atomically.

Authors may always provide ``expect`` explicitly; the model never widens an
author-provided set.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

from execution_testing.base_types import Number
from execution_testing.exceptions import EngineAPIError
from execution_testing.fixtures.reorg import (
    GENESIS_LABEL,
    LATEST_VALID_HASH_ANY,
    LATEST_VALID_HASH_NULL,
    ZERO_LABEL,
    AssertHeadStep,
    ForkchoiceUpdatedStep,
    GetPayloadStep,
    NewPayloadStep,
    Outcome,
    Step,
)

DISPUTED_HEAD_EQUALS_FINALIZED = (
    "execution-apis#786: no-reorg shortcut applies to an *ancestor* of "
    "finalized; head == finalized is unspecified"
)


@dataclass
class ModelDag:
    """Block DAG known at fill time."""

    parent: Dict[str, str]
    """label -> parent label (``genesis`` has no entry)."""
    valid: Dict[str, bool]
    """label -> whether the block passes execution validation."""
    hash_invalid: Set[str] = field(default_factory=set)
    """
    Labels whose engine payload does not hash to its own ``blockHash``.

    Such a payload is rejected by the block-hash check, which the client has
    to run in all cases, before and independently of any parent lookup or
    execution.
    """

    def number(self, label: str) -> int:
        """Block height of a label."""
        n = 0
        while label != GENESIS_LABEL:
            label = self.parent[label]
            n += 1
        return n

    def ancestors(self, label: str) -> List[str]:
        """Labels from ``label`` (inclusive) back to genesis."""
        chain = [label]
        while label != GENESIS_LABEL:
            label = self.parent[label]
            chain.append(label)
        return chain

    def is_ancestor(self, ancestor: str, label: str) -> bool:
        """Whether ``ancestor`` is a strict ancestor of ``label``."""
        return ancestor in self.ancestors(label)[1:]

    def last_valid_ancestor(self, label: str) -> str:
        """
        Closest ancestor (inclusive) that is valid and whose ancestors are.
        """
        for candidate in self.ancestors(label):
            if self.fully_valid(candidate):
                return candidate
        return GENESIS_LABEL

    def fully_valid(self, label: str) -> bool:
        """Block and all its ancestors are execution-valid."""
        return all(self.valid.get(a, True) for a in self.ancestors(label))


@dataclass
class ClientModel:
    """Simulated client forkchoice state."""

    dag: ModelDag
    known: Dict[str, bool] = field(default_factory=dict)
    """label -> known validity (True valid, False invalid)."""
    head: str = GENESIS_LABEL
    safe: str = ZERO_LABEL
    finalized: str = ZERO_LABEL

    def __post_init__(self) -> None:
        """Genesis is always known and valid."""
        self.known.setdefault(GENESIS_LABEL, True)

    # -- newPayload -----------------------------------------------------

    def new_payload_outcomes(self, block: str) -> List[Outcome]:
        """Legal outcomes of ``newPayload(block)``."""
        parent = self.dag.parent[block]
        if block in self.dag.hash_invalid:
            # The block-hash check runs in all cases, so the answer does not
            # depend on the parent being known. Pre-Shanghai clients report
            # INVALID_BLOCK_HASH; from Shanghai on, INVALID with a null
            # latestValidHash, since no ancestor of an unhashable payload can
            # be determined.
            return [
                Outcome(
                    id="invalid",
                    status="INVALID",
                    latest_valid_hash=LATEST_VALID_HASH_NULL,
                ),
                Outcome(id="invalid_block_hash", status="INVALID_BLOCK_HASH"),
            ]
        if parent not in self.known:
            return [Outcome(id="syncing", status="SYNCING")]
        if not self.known[parent]:
            lva = self.dag.last_valid_ancestor(parent)
            return [
                Outcome(id="invalid", status="INVALID", latest_valid_hash=lva),
                Outcome(id="syncing", status="SYNCING"),
            ]
        if not self.dag.valid.get(block, True):
            # The spec only says validationError MAY be set; required here
            # (unlike the propagated-invalid-parent and FCU-invalid-head
            # cases) because this is the block a client itself executed and
            # rejected, matching the stricter check test_via_engine.py and
            # test_via_sync.py already apply to every own-block INVALID.
            return [
                Outcome(
                    id="invalid",
                    status="INVALID",
                    latest_valid_hash=parent,
                    validation_error="required",
                )
            ]
        if parent == self.head:
            return [
                Outcome(id="valid", status="VALID", latest_valid_hash=block)
            ]
        return [
            Outcome(id="valid", status="VALID", latest_valid_hash=block),
            Outcome(
                id="accepted",
                status="ACCEPTED",
                latest_valid_hash=LATEST_VALID_HASH_NULL,
            ),
        ]

    def apply_new_payload(self, block: str, outcomes: List[Outcome]) -> None:
        """
        Update model state after ``newPayload``.

        A block that may be INVALID (itself or via a known-invalid ancestor)
        is recorded as known-invalid: clients that cache bad blocks answer
        INVALID for its descendants, others SYNCING — both remain legal for
        every descendant, so the chain must never become canonical.
        """
        statuses = {o.status for o in outcomes}
        if statuses & {"VALID", "ACCEPTED"}:
            self.known[block] = True
        elif "INVALID" in statuses:
            self.known[block] = False
        # SYNCING-only: block remains unknown.

    # -- forkchoiceUpdated ----------------------------------------------

    def _on_chain(self, label: str, head: str) -> bool:
        """Whether ``label`` is ``zero``, ``head`` or an ancestor of it."""
        return (
            label == ZERO_LABEL
            or label == head
            or self.dag.is_ancestor(label, head)
        )

    def forkchoice_outcomes(
        self, step: ForkchoiceUpdatedStep
    ) -> List[Outcome]:
        """
        Legal outcomes of a ``forkchoiceUpdated`` step.

        When payload attributes are supplied, an applied VALID outcome must
        return a ``payloadId``; a no-op must not start a build.
        """
        outcomes = self._forkchoice_outcomes(step)
        if step.payload_attributes is not None:
            for outcome in outcomes:
                if outcome.id == "applied":
                    outcome.payload_id = "nonNull"
                elif outcome.id == "noop":
                    outcome.payload_id = "null"
        return outcomes

    def _forkchoice_outcomes(
        self, step: ForkchoiceUpdatedStep
    ) -> List[Outcome]:
        head = step.head
        if head not in self.known:
            return [Outcome(id="syncing", status="SYNCING")]
        if not self.known[head]:
            return [
                Outcome(
                    id="invalid",
                    status="INVALID",
                    latest_valid_hash=self.dag.last_valid_ancestor(head),
                )
            ]
        # Step 2: no-reorg shortcut for ancestors of the latest known
        # finalized.
        if self.finalized != ZERO_LABEL:
            if self.dag.is_ancestor(head, self.finalized):
                return [
                    Outcome(id="noop", status="VALID", latest_valid_hash=head)
                ]
            if head == self.finalized and head != self.head:
                return [
                    Outcome(
                        id="applied", status="VALID", latest_valid_hash=head
                    ),
                    Outcome(
                        id="noop",
                        status="VALID",
                        latest_valid_hash=head,
                        disputed=DISPUTED_HEAD_EQUALS_FINALIZED,
                    ),
                ]
        # Step 5: consistency of safe/finalized with head.
        if not self._on_chain(step.safe, head) or not self._on_chain(
            step.finalized, head
        ):
            return [
                Outcome(
                    id="inconsistent",
                    error_code=EngineAPIError.InvalidForkchoiceState,
                )
            ]
        # Extending the current head (or re-sending it): always applied.
        if head == self.head or self.dag.is_ancestor(self.head, head):
            return [
                Outcome(id="applied", status="VALID", latest_valid_hash=head)
            ]
        # Rewind to a canonical ancestor, or a side-chain reorg: the update is
        # applied, or refused with the client's own depth limit. Skipping it is
        # only legal for an ancestor of finalized, handled above.
        return [
            Outcome(id="applied", status="VALID", latest_valid_hash=head),
            Outcome(id="refused", error_code=EngineAPIError.TooDeepReorg),
        ]

    def apply_forkchoice(
        self, step: ForkchoiceUpdatedStep, outcome: Outcome
    ) -> None:
        """
        Update model state assuming ``outcome`` happened.

        Only an applied update changes the state: every update resulting from
        a ``forkchoiceUpdated`` call has to be made atomically, so a call that
        ends in an error leaves head, safe and finalized where they were.
        """
        if outcome.id == "applied":
            self.head = step.head
            self.safe = step.safe
            self.finalized = step.finalized

    def head_assertion(self) -> AssertHeadStep:
        """``assertHead`` for the current model state."""
        return AssertHeadStep(
            latest=self.head,
            safe=None if self.safe == ZERO_LABEL else self.safe,
            finalized=None if self.finalized == ZERO_LABEL else self.finalized,
        )

    def assign(self, other: "ClientModel") -> None:
        """Take over another model's state (same DAG)."""
        self.known = dict(other.known)
        self.head = other.head
        self.safe = other.safe
        self.finalized = other.finalized

    def copy(self) -> "ClientModel":
        """Independent copy for branch exploration."""
        return ClientModel(
            dag=self.dag,
            known=dict(self.known),
            head=self.head,
            safe=self.safe,
            finalized=self.finalized,
        )


def annotate_steps(
    steps: List[Step],
    model: ClientModel,
    fcu_version: Optional[Dict[str, int]] = None,
) -> List[Step]:
    """
    Fill empty ``expect`` lists and ``version`` fields in ``steps`` using the
    model, appending an ``assertHead`` step to every forkchoice outcome branch.

    Branch step lists are annotated recursively with a copy of the model in
    which that outcome happened. Sibling steps after a multi-outcome step are
    annotated with the model of the first (canonical) outcome.

    ``getPayload`` binds a new label: it is added to the DAG as a valid child
    of its declared parent (the client builds it, so it is execution-valid).
    """
    for step in steps:
        if isinstance(step, NewPayloadStep):
            if not step.expect:
                step.expect = model.new_payload_outcomes(step.block)
            first_model: Optional[ClientModel] = None
            for outcome in step.expect:
                branch_model = model.copy()
                branch_model.apply_new_payload(step.block, [outcome])
                if outcome.id in step.branches:
                    annotate_steps(
                        step.branches[outcome.id], branch_model, fcu_version
                    )
                if first_model is None:
                    first_model = branch_model
            # Continuation: known-ness follows the whole outcome set (a block
            # that may be INVALID is treated as known-invalid), head follows
            # the first outcome's branch.
            model.apply_new_payload(step.block, step.expect)
            if first_model is not None and step.branches:
                known = dict(model.known)
                model.assign(first_model)
                model.known = known
        elif isinstance(step, ForkchoiceUpdatedStep):
            if step.version is None:
                if fcu_version is None:
                    raise ValueError(
                        "forkchoiceUpdated step without version and no "
                        "version map provided"
                    )
                step.version = Number(fcu_version[step.head])
            if not step.expect:
                step.expect = model.forkchoice_outcomes(step)
            ids = {o.id for o in step.expect}
            if {"applied", "noop"} <= ids:
                for outcome in step.expect:
                    if outcome.id == "applied":
                        outcome.head_moved = True
                    elif outcome.id == "noop":
                        outcome.head_moved = False
            first_model = None
            for outcome in step.expect:
                branch_model = model.copy()
                branch_model.apply_forkchoice(step, outcome)
                branch = step.branches.setdefault(outcome.id, [])
                annotate_steps(branch, branch_model, fcu_version)
                if outcome.status != "SYNCING":
                    branch.append(branch_model.head_assertion())
                if first_model is None:
                    first_model = branch_model
            # Sibling steps continue from the state after the first
            # (canonical) outcome's branch has executed.
            assert first_model is not None
            model.assign(first_model)
        elif isinstance(step, GetPayloadStep):
            model.dag.parent[step.bind] = step.parent
            model.dag.valid[step.bind] = True
            if fcu_version is not None:
                fcu_version.setdefault(step.bind, fcu_version[step.parent])
            if step.version is None:
                # Set by ReorgTest from the fork of the payload being built;
                # forkchoiceUpdated's version is not a valid substitute.
                raise ValueError("getPayload step without version")
    return steps


__all__ = [
    "ClientModel",
    "ModelDag",
    "annotate_steps",
    "LATEST_VALID_HASH_ANY",
]
