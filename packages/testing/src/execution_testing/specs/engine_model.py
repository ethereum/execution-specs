"""
Engine API reference model used to annotate reorg tests.

The model simulates the forkchoice-relevant state of an execution client
(known blocks and their validity, head/safe/finalized) over the block DAG of a
reorg test, and derives the set of spec-legal outcomes for every
``newPayload`` / ``forkchoiceUpdated`` step whose ``expect`` was left empty.
It also prepends an ``assertHead`` step to each forkchoice outcome's
branch, so the head is verified after every forkchoice update.

Rules follow `execution-apis` ``paris.md`` as amended by PR #786:

- ``newPayload``: payload that does not hash to its own ``blockHash`` →
  INVALID with a null ``latestValidHash`` (or ``INVALID_BLOCK_HASH``), checked
  before the parent is looked up; unknown parent → SYNCING; execution-invalid
  → INVALID with ``latestValidHash`` = last valid ancestor; child of a
  known-invalid (confirmed, or received-but-unconfirmed and ground-truth
  invalid) block → INVALID (lvh = last valid ancestor) or SYNCING; extends
  head → VALID; known parent on a side chain → VALID or ACCEPTED.
- ``forkchoiceUpdated``: head whose payload failed the block-hash check →
  INVALID or SYNCING; unknown head → SYNCING; received-but-unconfirmed
  ground-truth-invalid head → INVALID or SYNCING; confirmed-invalid head →
  INVALID; head is a VALID ancestor of the latest known finalized block →
  VALID no-op only (the spec's MAY skip is read as the answer, ahead of
  ``-38002``/``-38006``: execution-apis#891); safe or finalized not on
  head's chain → ``-38002``; head extends current head → VALID; otherwise
  (rewind or side-chain reorg) → VALID (applied) or ``-38006`` (refused,
  implementation-specific depth cap). An error leaves the forkchoice state
  untouched (updates are atomic), except ``-38003``/``-38005`` (invalid
  payload attributes / unsupported fork): the state is updated before the
  attributes are validated.

Authors may always provide ``expect`` explicitly; the model never widens an
author-provided set.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Dict, List, Optional, Set, Tuple, Union

from execution_testing.base_types import Alloc, Hash, HexNumber, Number
from execution_testing.exceptions import EngineAPIError
from execution_testing.fixtures.blockchain import PayloadAttributes
from execution_testing.fixtures.reorg import (
    GENESIS_LABEL,
    LATEST_VALID_HASH_NULL,
    ZERO_LABEL,
    AssertHeadStep,
    AssertStateStep,
    ForkchoiceUpdatedStep,
    GetPayloadStep,
    NewPayloadStep,
    Outcome,
    Step,
)
from execution_testing.forks import Fork, TransitionFork

DISPUTED_HEAD_EQUALS_FINALIZED = (
    "execution-apis#891: whether head == finalized is covered by the "
    "no-reorg shortcut"
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
    post_state: Optional[Callable[[str], Optional[Alloc]]] = None
    """label -> that block's post-state (``None`` if unknown), if checked."""
    timestamp: Dict[str, int] = field(default_factory=dict)
    """label -> timestamp; with the next two, the build-request defaults."""
    gas_limit: Dict[str, int] = field(default_factory=dict)
    """label -> gas limit."""
    slot: Dict[str, int] = field(default_factory=dict)
    """label -> slot number (0 before Amsterdam)."""

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


class Validity(Enum):
    """
    What the model has learned about a block via ``newPayload`` responses.

    ``ACCEPTED`` never establishes execution validity by itself — it only
    means the client has *received* the payload, not validated it (e.g. an
    unlinked side-chain block). ``RECEIVED`` tracks that distinction so a
    later step targeting that block still gets the right legal outcomes;
    ``VALID``/``INVALID`` are the confirmed states.
    """

    RECEIVED = "received"
    VALID = "valid"
    INVALID = "invalid"


@dataclass
class ClientModel:
    """Simulated client forkchoice state."""

    dag: ModelDag
    known: Dict[str, Validity] = field(default_factory=dict)
    """label -> what the model has learned about it (see ``Validity``)."""
    diverged: Dict[str, str] = field(default_factory=dict)
    """
    label -> the step whose outcomes leave that block in different states;
    generating an outcome that depends on it is rejected.
    """
    head: str = GENESIS_LABEL
    safe: str = ZERO_LABEL
    finalized: str = ZERO_LABEL
    build: Optional[Tuple[str, PayloadAttributes]] = None
    """
    Parent label and attributes of the build ``getPayload`` retrieves: the
    consumer keeps the ``payloadId`` of the last ``forkchoiceUpdated`` that
    did not error, so that response decides it.
    """
    build_diverged: Optional[str] = None
    """
    The step whose outcomes leave different builds; a ``getPayload`` that
    depends on it is rejected.
    """

    def __post_init__(self) -> None:
        """Genesis is always known and valid."""
        self.known.setdefault(GENESIS_LABEL, Validity.VALID)

    # -- newPayload -----------------------------------------------------

    def _known(self, label: str) -> Optional[Validity]:
        """What the model has learned about ``label``, if unambiguous."""
        if label in self.diverged:
            raise ValueError(
                f"{self.diverged[label]}; a later step's generated outcomes "
                "depend on it: author that step's expect or move it into "
                "each branch"
            )
        return self.known.get(label)

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
        parent_state = self._known(parent)
        if parent_state is None:
            return [Outcome(id="syncing", status="SYNCING")]
        if parent_state == Validity.RECEIVED and not self.dag.fully_valid(
            parent
        ):
            parent_state = Validity.INVALID
        if parent_state == Validity.INVALID:
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

    def apply_new_payload(self, block: str, outcome: Outcome) -> None:
        """
        Record what ``outcome`` reveals about ``block``: VALID and INVALID
        confirm it, ACCEPTED only that it was received, SYNCING nothing.
        """
        if outcome.status == "VALID":
            self.known[block] = Validity.VALID
        elif outcome.status == "INVALID":
            self.known[block] = Validity.INVALID
        elif outcome.status == "ACCEPTED":
            self.known[block] = Validity.RECEIVED
        else:
            return
        self.diverged.pop(block, None)

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
                if outcome.status == "VALID":
                    applied = self._forkchoice_effect(step, outcome)
                    outcome.payload_id = "nonNull" if applied else "null"
        return outcomes

    def _forkchoice_outcomes(
        self, step: ForkchoiceUpdatedStep
    ) -> List[Outcome]:
        head = step.head
        if head in self.dag.hash_invalid:
            # No block is stored under the payload's claimed hash; the client
            # answers INVALID only if it remembers rejecting that hash.
            return [
                Outcome(id="invalid", status="INVALID"),
                Outcome(id="syncing", status="SYNCING"),
            ]
        head_state = self._known(head)
        if head_state is None:
            return [Outcome(id="syncing", status="SYNCING")]
        if head_state == Validity.RECEIVED:
            if not self.dag.fully_valid(head):
                lva = self.dag.last_valid_ancestor(head)
                return [
                    Outcome(
                        id="invalid", status="INVALID", latest_valid_hash=lva
                    ),
                    Outcome(id="syncing", status="SYNCING"),
                ]
            # Ground-truth valid: SYNCING is never legal once received, so
            # this falls through to the same outcomes as a confirmed VALID.
            head_state = Validity.VALID
        if head_state == Validity.INVALID:
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
                        id="applied",
                        status="VALID",
                        latest_valid_hash=head,
                        head_moved=True,
                    ),
                    Outcome(
                        id="noop",
                        status="VALID",
                        latest_valid_hash=head,
                        head_moved=False,
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

    def _forkchoice_effect(
        self, step: ForkchoiceUpdatedStep, outcome: Outcome
    ) -> bool:
        """
        Whether ``outcome`` means the requested update was applied.

        Derived from the outcome's constraints and the no-reorg shortcut
        (step 2), never from ``outcome.id``. ``-38003``/``-38005`` still
        apply: the state is updated before the attributes are validated
        (step 8 of ``paris.md``, extended by ``cancun.md``/``amsterdam.md``).
        """
        if outcome.error_code in (
            EngineAPIError.InvalidPayloadAttributes,
            EngineAPIError.UnsupportedFork,
        ):
            return True
        if outcome.any_error and step.payload_attributes is not None:
            raise ValueError(
                f"forkchoiceUpdated(head={step.head!r}): outcome "
                f"{outcome.id!r} accepts any error, but -38003/-38005 "
                "apply the update and other errors do not; set errorCode "
                "instead"
            )
        if outcome.error_code is not None or outcome.any_error:
            return False
        if outcome.status in ("SYNCING", "INVALID"):
            return False
        if outcome.head_moved is not None:
            return outcome.head_moved
        # VALID with no explicit headMoved: apply step 2's no-reorg
        # shortcut for a validated ancestor of finalized; head == finalized
        # is genuinely ambiguous (see DISPUTED_HEAD_EQUALS_FINALIZED) and
        # needs headMoved to disambiguate.
        if self.finalized != ZERO_LABEL and self.dag.is_ancestor(
            step.head, self.finalized
        ):
            return False
        if step.head == self.finalized and step.head != self.head:
            raise ValueError(
                f"forkchoiceUpdated(head={step.head!r}): outcome "
                f"{outcome.id!r} is VALID with no headMoved, but applying "
                "and skipping the update are both legal when head == "
                "finalized; set headMoved to disambiguate"
            )
        return True

    def apply_forkchoice(
        self, step: ForkchoiceUpdatedStep, outcome: Outcome
    ) -> None:
        """
        Update model state assuming ``outcome`` happened. A response that is
        not an error replaces the build ``getPayload`` retrieves: with this
        request's if it returns a ``payloadId``, else with none.
        """
        applied = self._forkchoice_effect(step, outcome)
        attrs = step.payload_attributes
        if outcome.error_code is None and not outcome.any_error:
            self.build = None
            self.build_diverged = None
            if attrs is not None and (
                outcome.payload_id == "nonNull"
                or (outcome.payload_id is None and applied)
            ):
                self.build = (step.head, attrs)
        if applied:
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
        self.diverged = dict(other.diverged)
        self.head = other.head
        self.safe = other.safe
        self.finalized = other.finalized
        self.build = other.build
        self.build_diverged = other.build_diverged

    def copy(self) -> "ClientModel":
        """Independent copy for branch exploration."""
        return ClientModel(
            dag=self.dag,
            known=dict(self.known),
            diverged=dict(self.diverged),
            head=self.head,
            safe=self.safe,
            finalized=self.finalized,
            build=self.build,
            build_diverged=self.build_diverged,
        )


def _reject_unmatched_branches(
    step: Union[NewPayloadStep, ForkchoiceUpdatedStep], where: str
) -> None:
    """
    Reject a ``branches`` key that names no outcome id, once ``expect`` is
    final. A typo or partial rename here would otherwise silently drop the
    authored assertions under that key.
    """
    ids = {o.id for o in step.expect}
    unmatched = sorted(set(step.branches) - ids)
    if unmatched:
        raise ValueError(
            f"{where}: branches key(s) {unmatched} match no outcome id "
            f"(outcomes: {sorted(ids)})"
        )


def _reject_duplicate_outcome_ids(
    step: Union[NewPayloadStep, ForkchoiceUpdatedStep], where: str
) -> None:
    """
    Reject two outcomes sharing an id in the same step's ``expect``, once it
    is final. Both would modify the same ``branches`` entry, producing a
    branch that asserts the state of whichever outcome actually matched
    (PR3556-F3-02).
    """
    seen: Set[str] = set()
    duplicates: Set[str] = set()
    for outcome in step.expect:
        if outcome.id in seen:
            duplicates.add(outcome.id)
        else:
            seen.add(outcome.id)
    if duplicates:
        raise ValueError(
            f"{where}: repeated outcome id(s) {sorted(duplicates)}"
        )


def _state_class(model: ClientModel, label: str) -> Optional[Validity]:
    """``model.known[label]``, counting a truly valid RECEIVED as VALID."""
    state = model.known.get(label)
    if state == Validity.RECEIVED and model.dag.fully_valid(label):
        return Validity.VALID
    return state


def _continue(
    model: ClientModel,
    where: str,
    branches: List[Tuple[str, ClientModel]],
    has_continuation: bool,
) -> None:
    """
    Continue from the first outcome's branch.

    When a later step follows, every branch must leave the same
    head/safe/finalized; a block they leave in different states is marked
    diverged, and so is the build when they leave different ones.
    """
    ids = [oid for oid, _ in branches]
    states = {(m.head, m.safe, m.finalized) for _, m in branches}
    if has_continuation and len(states) > 1:
        raise ValueError(
            f"{where}: outcomes {ids} leave different forkchoice states "
            f"{sorted(states)}, but a later step depends on which one "
            "occurred; restructure so each branch's own continuation is "
            "self-contained"
        )
    model.assign(branches[0][1])
    for _, other in branches[1:]:
        model.diverged = {**other.diverged, **model.diverged}
    labels = set().union(*(m.known.keys() for _, m in branches))
    for label in labels - model.diverged.keys():
        if len({_state_class(m, label) for _, m in branches}) > 1:
            model.diverged[label] = (
                f"{where}: outcomes {ids} leave block {label!r} in "
                "different states"
            )
    reasons = [m.build_diverged for _, m in branches if m.build_diverged]
    if reasons:
        model.build_diverged = reasons[0]
    elif any(m.build != model.build for _, m in branches[1:]):
        model.build_diverged = (
            f"{where}: outcomes {ids} leave different payload builds"
        )


def _default_build_request(
    step: ForkchoiceUpdatedStep,
    dag: ModelDag,
    fork: Fork | TransitionFork,
) -> None:
    """
    Fill a build request's unset attribute fields, and its version, from
    the head block and the fork of the requested timestamp.
    """
    attrs = step.payload_attributes
    assert attrs is not None
    if int(attrs.timestamp) == 0:
        attrs.timestamp = HexNumber(dag.timestamp[step.head] + 12)
    attrs_fork = fork.fork_at(block_number=0, timestamp=int(attrs.timestamp))
    if attrs.withdrawals is None and attrs_fork.header_withdrawals_required():
        attrs.withdrawals = []
    if (
        attrs.parent_beacon_block_root is None
        and attrs_fork.header_beacon_root_required()
    ):
        attrs.parent_beacon_block_root = Hash(0xBEAC0)
    if (
        attrs.slot_number is None
        and attrs_fork.engine_payload_attribute_slot_number()
    ):
        attrs.slot_number = HexNumber(dag.slot[step.head] + 1)
    if (
        attrs.target_gas_limit is None
        and attrs_fork.engine_payload_attribute_target_gas_limit()
    ):
        attrs.target_gas_limit = HexNumber(dag.gas_limit[step.head])
    if step.version is None:
        version = attrs_fork.engine_forkchoice_updated_version()
        assert version is not None
        step.version = Number(version)


def _bind_payload(
    step: GetPayloadStep,
    model: ClientModel,
    fork: Fork | TransitionFork | None,
) -> None:
    """
    Add the payload ``getPayload`` binds to the DAG as a valid child of its
    parent (the client built it), with the timestamp, slot and gas limit
    of the build it retrieves, and fill its version from that build's
    fork.
    """
    where = f"getPayload({step.bind!r})"
    if model.build_diverged is not None:
        raise ValueError(
            f"{model.build_diverged}; {where} depends on which occurred: "
            "move it into each branch"
        )
    if model.build is None:
        raise ValueError(
            f"{where}: no build in progress; the last forkchoiceUpdated "
            "that did not error started none"
        )
    parent, attrs = model.build
    if parent != step.parent:
        raise ValueError(
            f"{where}: the build in progress is on {parent!r}, not "
            f"{step.parent!r}"
        )
    dag = model.dag
    dag.parent[step.bind] = parent
    dag.valid[step.bind] = True
    dag.timestamp[step.bind] = int(attrs.timestamp)
    dag.slot[step.bind] = (
        0 if attrs.slot_number is None else int(attrs.slot_number)
    )
    dag.gas_limit[step.bind] = (
        dag.gas_limit[parent]
        if attrs.target_gas_limit is None
        else int(attrs.target_gas_limit)
    )
    if step.version is None:
        if fork is None:
            raise ValueError(f"{where} without version and no fork provided")
        version = fork.fork_at(
            block_number=0, timestamp=int(attrs.timestamp)
        ).engine_get_payload_version()
        assert version is not None
        step.version = Number(version)


def annotate_steps(
    steps: List[Step],
    model: ClientModel,
    fcu_version: Optional[Dict[str, int]] = None,
    fork: Fork | TransitionFork | None = None,
    more_follow: bool = False,
) -> List[Step]:
    """
    Fill empty ``expect`` lists and ``version`` fields in ``steps`` using the
    model, and prepend to every forkchoice outcome branch an ``assertHead``
    for the state that outcome leaves.

    Each outcome's branch is annotated with its own copy of the model;
    ``more_follow`` says a step follows in an enclosing list (see
    ``_continue``). With ``fork``, build requests get their unset attribute
    fields and version from it. ``getPayload`` binds the build its
    preceding steps leave in progress (see ``ClientModel.build``).
    ``assertState`` is checked against the DAG's post-states where they
    are known.
    """
    for i, step in enumerate(steps):
        has_continuation = i + 1 < len(steps) or more_follow
        if isinstance(step, NewPayloadStep):
            if not step.expect:
                step.expect = model.new_payload_outcomes(step.block)
            _reject_unmatched_branches(step, f"newPayload({step.block!r})")
            _reject_duplicate_outcome_ids(step, f"newPayload({step.block!r})")
            branches: List[Tuple[str, ClientModel]] = []
            for outcome in step.expect:
                branch_model = model.copy()
                branch_model.apply_new_payload(step.block, outcome)
                if outcome.id in step.branches:
                    annotate_steps(
                        step.branches[outcome.id],
                        branch_model,
                        fcu_version,
                        fork,
                        has_continuation,
                    )
                branches.append((outcome.id, branch_model))
            _continue(
                model,
                f"newPayload({step.block!r})",
                branches,
                has_continuation,
            )
        elif isinstance(step, ForkchoiceUpdatedStep):
            if step.payload_attributes is not None and fork is not None:
                _default_build_request(step, model.dag, fork)
            if step.version is None:
                if fcu_version is None:
                    raise ValueError(
                        "forkchoiceUpdated step without version and no "
                        "version map provided"
                    )
                step.version = Number(fcu_version[step.head])
            if not step.expect:
                step.expect = model.forkchoice_outcomes(step)
            _reject_unmatched_branches(
                step, f"forkchoiceUpdated(head={step.head!r})"
            )
            _reject_duplicate_outcome_ids(
                step, f"forkchoiceUpdated(head={step.head!r})"
            )
            branches = []
            for outcome in step.expect:
                branch_model = model.copy()
                branch_model.apply_forkchoice(step, outcome)
                branch = step.branches.setdefault(outcome.id, [])
                if outcome.status != "SYNCING":
                    branch.insert(0, branch_model.head_assertion())
                annotate_steps(
                    branch, branch_model, fcu_version, fork, has_continuation
                )
                branches.append((outcome.id, branch_model))
            _continue(
                model,
                f"forkchoiceUpdated(head={step.head!r})",
                branches,
                has_continuation,
            )
        elif isinstance(step, AssertStateStep) and model.dag.post_state:
            label = model.head if step.at == "latest" else step.at
            state = model.dag.post_state(label)
            if state is not None:
                step.verify(label, state)
        elif isinstance(step, GetPayloadStep):
            _bind_payload(step, model, fork)
            if fcu_version is not None:
                fcu_version.setdefault(step.bind, fcu_version[step.parent])
    return steps


__all__ = [
    "ClientModel",
    "ModelDag",
    "annotate_steps",
]
