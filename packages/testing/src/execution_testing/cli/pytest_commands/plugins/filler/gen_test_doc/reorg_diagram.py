"""
Render a reorg fixture as inline SVG and HTML for the test case reference.

Everything is derived from one filled `blockchain_test_engine_reorg`
fixture: the block DAG from `blocks` (and the labels `getPayload` binds),
the ordered script from `steps` and their `branches`, the accepted outcomes
from each step's `expect`, and the head, safe and finalized positions from
the `assertHead` that leads every forkchoice outcome branch, and from
`awaitHead`, which names the head a client must reach by syncing from the
peer. Nothing here simulates a client; the one assumption is that the head
starts at genesis.
Hashes and most fork-specific values are left out. The exception is a
build request, drawn with its method version and its timestamp relative
to the head's, because tests accept different outcomes for those alone.

To support a new step type, first add it to the `Step` union of the
fixture format (fixtures with an unknown type do not load), then:

- add its call rendering to `STEP_RENDERERS`; without one the step is
  drawn generically from its fields;
- if it makes blocks reach the client, add an entry to `DELIVERIES` and
  the kind's legend to `BLOCK_KINDS`, plus a `.rg-b--<kind>` colour in
  `docs/stylesheets/reorg_diagram.css`;
- if it moves the head, or has outcomes and branches, extend `_flow`:
  only `assertHead`, `awaitHead` and the outcome branches of
  `newPayload` and `forkchoiceUpdated` move the markers today.

A frame only knows blocks the client has and blocks it lacks. What a
`servePeer` step offers is therefore not drawn: the blocks turn up with
the `awaitHead` that requires the client to have synced them.
"""

import json
from dataclasses import dataclass, field, replace
from html import escape
from typing import (
    Any,
    Callable,
    Dict,
    FrozenSet,
    List,
    Mapping,
    Sequence,
    Set,
    Tuple,
)

from pydantic import TypeAdapter

from execution_testing.fixtures.blockchain import PayloadStatusEnum
from execution_testing.fixtures.reorg import (
    GENESIS_LABEL,
    ZERO_LABEL,
    AssertCanonicalStep,
    AssertHeadStep,
    AssertLogsStep,
    AssertReceiptStep,
    AssertStateStep,
    AssertTxStatusStep,
    AwaitHeadStep,
    ForkchoiceUpdatedStep,
    GetPayloadStep,
    NewPayloadStep,
    Outcome,
    SendRawTransactionStep,
    ServePeerStep,
    Step,
    TxRef,
)

BLOCK_KINDS: Dict[str, str] = {
    "genesis": "genesis",
    "engine": "sent with <code>newPayload</code>",
    "built": "built by the client (<code>getPayload</code>)",
    "peer": "synced from the devp2p peer",
    "unsent": "never sent",
}
"""How a block reaches the client: CSS class suffix to legend text."""

BLOCK_MARKS: Dict[str, str] = {
    "invalid": "invalid",
    "tainted": "built on an invalid block",
}
"""Marks a block of any kind can carry: CSS class suffix to legend text."""

ParentMap = Mapping[str, str | None]


def _synced(step: AwaitHeadStep, parents: ParentMap) -> List[str]:
    """Return the awaited head, then its ancestors up to genesis."""
    chain: List[str] = []
    label: str | None = step.latest
    while label is not None and parents.get(label) is not None:
        chain.append(label)
        label = parents[label]
    return chain


DELIVERIES: Dict[
    str, Tuple[str, Callable[[Any, ParentMap], Sequence[str]]]
] = {
    "newPayload": ("engine", lambda step, _parents: [step.block]),
    "getPayload": ("built", lambda step, _parents: [step.bind]),
    "awaitHead": ("peer", _synced),
}
"""
Step type to the block kind it delivers and the labels it makes known to
the client. A block keeps the kind of the first step that delivers it.
"""

FOLD_MIN_REPEATS = 8
"""Fold a run of look-alike steps from this many repetitions on."""

ELIDE_MIN_COLUMNS = 5
"""Draw a run of plain chain blocks as one box from this many heights on."""

FAN_MIN_SIBLINGS = 6
"""Draw plain childless siblings as one box from this many on."""

WIDE = 430
"""A DAG wider than this gets the full page width for its frames."""

BULK_REFS = 6
"""Steps naming more blocks than this do not keep them from being elided."""

BLOCK_HEIGHT = 26
COLUMN_GAP = 20
LANE_PITCH = 68
CHAR_WIDTH = 6.7
PAD = 6
HEAD_ROOM = 15
AXIS_ROOM = 16


@dataclass(frozen=True)
class Forkchoice:
    """Where the fixture says latest, safe and finalized are."""

    latest: str | None = None
    safe: str | None = None
    finalized: str | None = None

    def labels(self) -> List[str]:
        """Return the blocks carrying a marker."""
        return [
            x
            for x in (self.latest, self.safe, self.finalized)
            if x is not None
        ]


@dataclass(frozen=True)
class Frame:
    """One drawing of the DAG: the state right after a step."""

    present: FrozenSet[str]
    forkchoice: Forkchoice
    target: str | None = None
    caption: str = ""


@dataclass
class OutcomeView:
    """An accepted outcome and the `assertHead` leading its branch."""

    outcome: Outcome
    after: AssertHeadStep | None = None


@dataclass
class Row:
    """A step of the script."""

    number: int
    step: Step
    outcomes: List[OutcomeView] = field(default_factory=list)
    frames: List[Frame] = field(default_factory=list)
    plain: bool = True
    """Whether no outcome of the step has follow-up steps of its own."""


@dataclass
class Fold:
    """A run of look-alike steps left out between two shown repetitions."""

    first: int
    last: int
    blocks: List[str]


@dataclass
class Note:
    """A remark on how the script continues."""

    html: str


@dataclass
class Split:
    """Follow-up steps that depend on which outcome occurred."""

    branches: List[Tuple[List[str], List["Item"]]]


Item = Row | Fold | Note | Split


@dataclass
class Node:
    """
    A drawn box: one block, a run of plain chain blocks, or a fan of plain
    childless siblings.
    """

    labels: List[str]
    parent: str | None
    kind: str
    invalid: str | None = None
    tainted: bool = False
    """Whether the block descends from an invalid block."""
    fan: bool = False
    column: int = 0
    lane: int = 0

    @property
    def text(self) -> str:
        """Return the text drawn in the box."""
        if len(self.labels) == 1:
            return self.labels[0]
        text = f"{self.labels[0]} \u2026 {self.labels[-1]}"
        return f"{len(self.labels)} \u00d7 {text}" if self.fan else text


@dataclass
class _State:
    """What the script has established so far."""

    present: Set[str]
    forkchoice: Forkchoice

    def copy(self) -> "_State":
        """Return an independent copy."""
        return _State(set(self.present), self.forkchoice)


STEPS_ADAPTER: TypeAdapter[List[Step]] = TypeAdapter(List[Step])


def _label(label: str | None) -> str:
    """Render a block label, or the absence of one."""
    if label is None:
        return '<span class="rg-none">none</span>'
    if label == ZERO_LABEL:
        return '<span class="rg-none">zero</span>'
    return f'<b class="rg-l">{escape(label)}</b>'


def _method(name: str, engine: bool = False) -> str:
    """Render the name of a call."""
    kind = "engine" if engine else "rpc"
    return f'<code class="rg-m rg-m--{kind}">{escape(name)}</code>'


def _tx(ref: TxRef) -> str:
    """Render a reference to a fixture transaction."""
    return f"transaction {int(ref.index)} of {_label(ref.block)}"


def _short_hex(value: Any) -> str:
    """Render a hex value, shortened in the middle when long."""
    text = str(value)
    if len(text) > 14:
        text = f"{text[:6]}…{text[-4:]}"
    return f"<code>{escape(text)}</code>"


def _join(parts: Sequence[str]) -> str:
    """Join fragments with a thin separator."""
    return ' <span class="rg-sep">·</span> '.join(parts)


def _new_payload(step: NewPayloadStep) -> str:
    return f"{_method('newPayload', True)} {_label(step.block)}"


def _forkchoice_updated(step: ForkchoiceUpdatedStep) -> str:
    parts = [
        f"head {_label(step.head)}",
        f"safe {_label(step.safe)}",
        f"finalized {_label(step.finalized)}",
    ]
    if step.payload_attributes is not None:
        request = "build request"
        if step.version is not None:
            request += f", sent as forkchoiceUpdatedV{int(step.version)}"
        parts.append(request)
    return f"{_method('forkchoiceUpdated', True)} {_join(parts)}"


def _get_payload(step: GetPayloadStep) -> str:
    parts = [f"binds {_label(step.bind)}", f"parent {_label(step.parent)}"]
    parts += [f"includes {_tx(t)}" for t in step.transactions_include]
    parts += [f"excludes {_tx(t)}" for t in step.transactions_exclude]
    return f"{_method('getPayload', True)} {_join(parts)}"


def _assert_head(step: AssertHeadStep) -> str:
    parts = [
        f"{tag} is {_label(value)}"
        for tag, value in (
            ("latest", step.latest),
            ("safe", step.safe),
            ("finalized", step.finalized),
        )
        if value is not None
    ]
    return f"{_method('assertHead')} {_join(parts)}"


def _assert_canonical(step: AssertCanonicalStep) -> str:
    parts = [
        f"height {int(number)} is {_label(label)}"
        for number, label in sorted(
            step.blocks.items(), key=lambda entry: int(entry[0])
        )
    ]
    if len(parts) > BULK_REFS:
        hidden = len(parts) - 4
        parts = parts[:2] + [f"… {hidden} more …"] + parts[-2:]
    return f"{_method('assertCanonical')} {_join(parts)}"


def _assert_state(step: AssertStateStep) -> str:
    accounts = []
    for address, want in step.accounts.items():
        fields = []
        if want.balance is not None:
            fields.append(f"balance {int(want.balance)}")
        if want.nonce is not None:
            fields.append(f"nonce {int(want.nonce)}")
        for key, value in (want.storage or {}).items():
            slot = int.from_bytes(key, "big")
            stored = int.from_bytes(value, "big")
            fields.append(f"storage[{slot}] = {stored}")
        if want.code is not None:
            size = len(want.code)
            fields.append(f"code of {size} bytes" if size else "no code")
        accounts.append(f"{_short_hex(address)} " + ", ".join(fields))
    at = "latest" if step.at == "latest" else _label(step.at)
    return f"{_method('assertState')} at {at}: {_join(accounts)}"


def _assert_receipt(step: AssertReceiptStep) -> str:
    if step.block is None:
        where = "has no receipt"
    else:
        where = f"has a receipt in {_label(step.block)}"
    if step.status is not None:
        where += f" with status {int(step.status)}"
    return f"{_method('assertReceipt')} {_tx(step.tx)} {where}"


def _assert_logs(step: AssertLogsStep) -> str:
    blocks = ", ".join(_label(b) for b in step.blocks) or "no block"
    parts = [f"logs come from {blocks}"]
    if step.address is not None:
        parts.append(f"address {_short_hex(step.address)}")
    return f"{_method('assertLogs')} {_join(parts)}"


def _send_raw_transaction(step: SendRawTransactionStep) -> str:
    expect = " or ".join(step.expect)
    return f"{_method('sendRawTransaction')} {_tx(step.tx)} is {expect}"


def _assert_tx_status(step: AssertTxStatusStep) -> str:
    text = f"{_tx(step.tx)} is {' or '.join(step.expect)}"
    if step.included_in is not None:
        text += f" (if included, in {_label(step.included_in)})"
    return f"{_method('assertTxStatus')} {text}"


def _serve_peer(step: ServePeerStep) -> str:
    chain = f"the chain from genesis to {_label(step.head)}"
    return f"{_method('servePeer')} a devp2p peer serves {chain}"


def _await_head(step: AwaitHeadStep) -> str:
    text = (
        f"the client syncs from the peer until latest is {_label(step.latest)}"
    )
    return f"{_method('awaitHead')} {text}"


STEP_RENDERERS: Dict[str, Callable[[Any], str]] = {
    "newPayload": _new_payload,
    "forkchoiceUpdated": _forkchoice_updated,
    "getPayload": _get_payload,
    "assertHead": _assert_head,
    "assertCanonical": _assert_canonical,
    "assertState": _assert_state,
    "assertReceipt": _assert_receipt,
    "assertLogs": _assert_logs,
    "sendRawTransaction": _send_raw_transaction,
    "assertTxStatus": _assert_tx_status,
    "servePeer": _serve_peer,
    "awaitHead": _await_head,
}
"""Step type to the function rendering its call as HTML."""


def _dump(step: Any) -> Dict[str, Any]:
    """Return a step as its fixture JSON."""
    dumped: Dict[str, Any] = step.model_dump(
        mode="json", by_alias=True, exclude_none=True
    )
    return dumped


def _generic_step(step: Any) -> str:
    """Render a step of a type without a renderer of its own."""
    fields = [
        f"{escape(str(key))} <code>{escape(json.dumps(value))}</code>"
        for key, value in _dump(step).items()
        if key not in ("type", "expect", "branches", "description")
    ]
    return f"{_method(str(step.type))} {_join(fields)}"


def render_call(step: Any) -> str:
    """Render the call a step makes."""
    return STEP_RENDERERS.get(str(step.type), _generic_step)(step)


def _after(step: AssertHeadStep) -> str:
    """Render the head assertion that follows an outcome."""
    parts = [
        f"{tag} {_label(value)}"
        for tag, value in (
            ("latest", step.latest),
            ("safe", step.safe),
            ("finalized", step.finalized),
        )
        if value is not None
    ]
    return "then " + ", ".join(parts)


def render_outcome(view: OutcomeView) -> str:
    """Render one accepted outcome of a step."""
    outcome = view.outcome
    details = []
    if outcome.error_code is not None:
        css = "error"
        code = outcome.error_code
        title = f"error {int(code)}"
        details.append(escape(code.name))
    elif outcome.any_error:
        css, title = "error", "any JSON-RPC error"
    elif outcome.status is not None:
        css = {
            PayloadStatusEnum.VALID: "valid",
            PayloadStatusEnum.INVALID: "invalid",
            PayloadStatusEnum.INVALID_BLOCK_HASH: "invalid",
        }.get(outcome.status, "open")
        title = outcome.status.value
    else:
        css, title = "open", "any status"
    if outcome.latest_valid_hash is not None:
        value = outcome.latest_valid_hash
        shown = value if value in ("any", "null") else _label(value)
        details.append(f"latestValidHash {shown}")
    if outcome.head_moved is not None:
        details.append("head moved" if outcome.head_moved else "head kept")
    if outcome.validation_error is not None:
        details.append(f"validationError {outcome.validation_error}")
    if outcome.payload_id is not None:
        has_id = outcome.payload_id == "nonNull"
        details.append("payloadId returned" if has_id else "no payloadId")
    if view.after is not None:
        details.append(_after(view.after))
    html = (
        f'<li class="rg-o rg-o--{css}">'
        f'<b class="rg-o-status">{escape(title)}</b>'
    )
    if outcome.disputed is not None:
        html += ' <span class="rg-tag">disputed</span>'
    html += f' <code class="rg-o-id">{escape(outcome.id)}</code>'
    if details:
        html += f'<span class="rg-o-more">{_join(details)}</span>'
    if outcome.disputed is not None:
        html += f'<span class="rg-why">{escape(outcome.disputed)}</span>'
    return html + "</li>"


def _reported(errors: str) -> str:
    """
    Render the exceptions a client may report for an invalid block, given
    in the fixture as alternatives separated by `|`.
    """
    names = [f"<code>{escape(name)}</code>" for name in errors.split("|")]
    if len(names) > 3:
        names = names[:3] + [f"one of {len(names) - 3} others"]
    if len(names) == 1:
        return names[0]
    return ", ".join(names[:-1]) + " or " + names[-1]


def _ids(ids: Sequence[str]) -> str:
    """Render outcome ids as an alternative."""
    return " or ".join(f"<code>{escape(i)}</code>" for i in ids)


class Scenario:
    """One reorg test case, laid out for rendering."""

    def __init__(
        self,
        blocks: Mapping[str, str],
        steps: Sequence[Step],
        invalid: Mapping[str, str] | None = None,
        min_reorg_depth: int | None = None,
        timestamps: Mapping[str, int] | None = None,
    ) -> None:
        """
        Lay out the DAG and the script.

        `blocks` maps each block label to its parent's label in fixture
        order, `invalid` the label of each invalid block to the reason.
        """
        self.invalid = dict(invalid or {})
        self.min_reorg_depth = min_reorg_depth
        self.timestamps = dict(timestamps or {})
        self.parents: Dict[str, str | None] = {GENESIS_LABEL: None}
        self.parents.update(blocks)
        self.kinds: Dict[str, str] = {GENESIS_LABEL: "genesis"}
        self._collect(steps)
        self._counter = 0
        self.items = self._flow(
            steps, _State({GENESIS_LABEL}, Forkchoice(latest=GENESIS_LABEL))
        )
        self.step_count = self._counter
        self._layout(self._kept_labels(self.items))

    @classmethod
    def from_fixture(cls, fixture: Mapping[str, Any]) -> "Scenario":
        """Build the scenario of a fixture given as parsed JSON."""
        return cls(
            blocks={
                label: block["parent"]
                for label, block in fixture["blocks"].items()
            },
            steps=STEPS_ADAPTER.validate_python(fixture["steps"]),
            invalid={
                label: block["validationError"]
                for label, block in fixture["blocks"].items()
                if block.get("validationError")
            },
            timestamps={
                label: int(block["payload"]["params"][0]["timestamp"], 16)
                for label, block in fixture["blocks"].items()
            },
            min_reorg_depth=(
                None
                if fixture.get("minReorgDepth") is None
                else int(fixture["minReorgDepth"])
            ),
        )

    # The script

    def _collect(self, steps: Sequence[Step]) -> None:
        """Record the blocks bound by, and the kind delivered by, steps."""
        for step in steps:
            if isinstance(step, GetPayloadStep):
                self.parents.setdefault(step.bind, step.parent)
            delivery = DELIVERIES.get(str(step.type))
            if delivery is not None:
                kind, labels = delivery
                for label in labels(step, self.parents):
                    self.kinds.setdefault(label, kind)
            for branch in getattr(step, "branches", {}).values():
                self._collect(branch)

    def _flow(
        self, steps: Sequence[Step], state: _State, more_follow: bool = False
    ) -> List[Item]:
        """
        Flatten `steps` and their outcome branches into display order,
        tracking in `state` what the fixture asserts as it goes.

        `more_follow` says that a step follows in an enclosing list.
        """
        items: List[Item] = []
        for index, step in enumerate(steps):
            follows = more_follow or index + 1 < len(steps)
            self._counter += 1
            row = Row(self._counter, step)
            items.append(row)
            delivery = DELIVERIES.get(str(step.type))
            delivered = (
                list(delivery[1](step, self.parents)) if delivery else []
            )
            state.present.update(delivered)
            if isinstance(step, AssertHeadStep):
                state.forkchoice = replace(
                    state.forkchoice,
                    **{
                        tag: value
                        for tag in ("latest", "safe", "finalized")
                        if (value := getattr(step, tag)) is not None
                    },
                )
            if isinstance(step, AwaitHeadStep):
                # The forkchoice update the client now applies kept safe
                # and finalized, so only the head moves.
                state.forkchoice = replace(
                    state.forkchoice, latest=step.latest
                )
            if not isinstance(step, (NewPayloadStep, ForkchoiceUpdatedStep)):
                if delivered:
                    row.frames.append(self._frame(state, delivered[0]))
                continue
            items.extend(self._outcomes(row, step, state, follows))
        return self._fold(items)

    def _outcomes(
        self,
        row: Row,
        step: NewPayloadStep | ForkchoiceUpdatedStep,
        state: _State,
        follows: bool,
    ) -> List[Item]:
        """
        Fill in a step's outcomes and frames; return its follow-up items.

        `follows` says that the script has a later step whatever the
        outcome.

        `state` moves on to what the first outcome leaves, the one the
        fill-time model continues from.
        """
        if isinstance(step, ForkchoiceUpdatedStep):
            target = step.head
        else:
            target = step.block
        states: Dict[str, _State] = {}
        groups: Dict[str, Tuple[List[str], List[Step]]] = {}
        for outcome in step.expect:
            branch = step.branches.get(outcome.id, [])
            view = OutcomeView(outcome)
            after = state.copy()
            if branch and isinstance(branch[0], AssertHeadStep):
                view.after, branch = branch[0], branch[1:]
                before = after.forkchoice
                # The model's assertion after a forkchoice outcome names
                # every marker that is set. It adds none after SYNCING,
                # so one found there is the author's and may name fewer:
                # there, as after a payload, unnamed markers stay put.
                keep = (
                    not isinstance(step, ForkchoiceUpdatedStep)
                    or outcome.status == PayloadStatusEnum.SYNCING
                )
                after.forkchoice = Forkchoice(
                    latest=view.after.latest or before.latest,
                    safe=view.after.safe or (before.safe if keep else None),
                    finalized=view.after.finalized
                    or (before.finalized if keep else None),
                )
            row.outcomes.append(view)
            states[outcome.id] = after
            if branch:
                # Outcomes share their follow-up steps only if they also
                # leave the same markers.
                key = json.dumps(
                    [
                        [_dump(s) for s in branch],
                        after.forkchoice.latest,
                        after.forkchoice.safe,
                        after.forkchoice.finalized,
                    ],
                    sort_keys=True,
                )
                groups.setdefault(key, ([], branch))[0].append(outcome.id)
        by_forkchoice: Dict[Forkchoice, List[str]] = {}
        for outcome_id, after in states.items():
            by_forkchoice.setdefault(after.forkchoice, []).append(outcome_id)
        for forkchoice, ids in by_forkchoice.items():
            caption = f"after {_ids(ids)}" if len(by_forkchoice) > 1 else ""
            row.frames.append(
                Frame(
                    present=frozenset(state.present),
                    forkchoice=forkchoice,
                    target=None if target == ZERO_LABEL else target,
                    caption=caption,
                )
            )
        row.plain = not groups
        first = step.expect[0].id if step.expect else None
        if first is not None:
            state.forkchoice = states[first].forkchoice
        flows: List[Tuple[List[str], List[Item]]] = []
        for ids, branch in groups.values():
            branch_state = states[ids[0]].copy()
            flows.append((ids, self._flow(branch, branch_state, follows)))
            if first in ids:
                state.present = branch_state.present
                state.forkchoice = branch_state.forkchoice
        if not flows:
            return []
        ids, flow = flows[0]
        ended = [o.id for o in step.expect if o.id not in ids]
        if len(flows) > 1 or (ended and follows):
            return [Split(flows)]
        if not ended:
            return flow
        note = (
            f"The script goes on after {_ids(ids)}; "
            f"after {_ids(ended)} the test ends here."
        )
        return [Note(note), *flow]

    def _frame(self, state: _State, target: str | None) -> Frame:
        """Return a frame of the current state."""
        return Frame(frozenset(state.present), state.forkchoice, target)

    def _signature(self, row: Row) -> str | None:
        """
        Return a row's step with its own block and that block's parent
        replaced by placeholders, or `None` if the row cannot be folded.
        """
        step = row.step
        if isinstance(step, NewPayloadStep):
            target = step.block
        elif isinstance(step, ForkchoiceUpdatedStep):
            target = step.head
        else:
            return None
        if not row.plain or len(row.frames) != 1:
            return None
        parent = self.parents.get(target)

        def relabel(value: Any) -> Any:
            if isinstance(value, dict):
                return {k: relabel(v) for k, v in value.items()}
            if isinstance(value, list):
                return [relabel(v) for v in value]
            if value == target:
                return "@"
            if parent is not None and value == parent:
                return "^"
            return value

        # The Engine API version changes at a fork boundary, not the call.
        dumped = {k: v for k, v in _dump(step).items() if k != "version"}
        return json.dumps(relabel(dumped), sort_keys=True)

    def _fold(self, items: List[Item]) -> List[Item]:
        """
        Replace the middle of each run of look-alike steps by a `Fold`,
        keeping the first and the last repetition.
        """
        signatures = [
            self._signature(item) if isinstance(item, Row) else None
            for item in items
        ]
        folded: List[Item] = []
        i = 0
        while i < len(items):
            for period in (1, 2):
                unit = signatures[i : i + period]
                if len(unit) < period or None in unit:
                    continue
                repeats = 1
                while (
                    signatures[
                        i + repeats * period : i + (repeats + 1) * period
                    ]
                    == unit
                ):
                    repeats += 1
                if repeats < FOLD_MIN_REPEATS:
                    continue
                end = i + repeats * period
                hidden = [
                    item
                    for item in items[i + period : end - period]
                    if isinstance(item, Row)
                ]
                blocks: List[str] = []
                for row in hidden:
                    target = row.frames[0].target
                    if target is not None and target not in blocks:
                        blocks.append(target)
                folded.extend(items[i : i + period])
                folded.append(
                    Fold(hidden[0].number, hidden[-1].number, blocks)
                )
                folded.extend(items[end - period : end])
                i = end
                break
            else:
                folded.append(items[i])
                i += 1
        return folded

    def _kept_labels(self, items: Sequence[Item]) -> Set[str]:
        """Return the blocks the shown steps name."""
        kept: Set[str] = set()
        for item in items:
            if isinstance(item, Split):
                for branch in item.branches:
                    kept |= self._kept_labels(branch[1])
            if not isinstance(item, Row):
                continue
            refs = item.step.label_refs()
            if len(refs) <= BULK_REFS:
                kept.update(refs)
            for view in item.outcomes:
                kept.add(str(view.outcome.latest_valid_hash))
                if view.after is not None:
                    kept.update(view.after.label_refs())
            for frame in item.frames:
                kept.update(frame.forkchoice.labels())
                kept.add(str(frame.target))
        return kept

    # The DAG

    def _layout(self, kept: Set[str]) -> None:
        """Group blocks into nodes and place them in columns and lanes."""
        children: Dict[str, List[str]] = {label: [] for label in self.parents}
        heights: Dict[str, int] = {}
        for label, parent in self.parents.items():
            if parent is None:
                heights[label] = 0
            else:
                children[parent].append(label)
                heights[label] = heights[parent] + 1

        def plain(label: str) -> bool:
            parent = self.parents[label]
            return (
                parent is not None
                and len(children[label]) == 1
                and len(children[parent]) == 1
                and label not in kept
                and label not in self.invalid
            )

        tallest = max(heights.values())
        plain_heights = [True] * (tallest + 1)
        for label, height in heights.items():
            plain_heights[height] &= plain(label)
        # Map each height to a column; a long enough run of plain heights
        # shares one.
        self.column_heights: List[List[int]] = []
        height = 0
        while height <= tallest:
            end = height
            while end <= tallest and plain_heights[end]:
                end += 1
            if end - height >= ELIDE_MIN_COLUMNS:
                self.column_heights.append(list(range(height, end)))
                height = end
            else:
                self.column_heights.append([height])
                height += 1
        column_of = {
            h: column
            for column, hs in enumerate(self.column_heights)
            for h in hs
        }

        def leaf(label: str) -> bool:
            return (
                not children[label]
                and label not in kept
                and label not in self.invalid
            )

        self.nodes: List[Node] = []
        self.node_of: Dict[str, Node] = {}
        fans: Dict[Tuple[str, str], Node] = {}
        for label, parent in self.parents.items():
            column = column_of[heights[label]]
            kind = self.kinds.get(label, "unsent")
            run = self.node_of.get(parent) if parent is not None else None
            in_fan = (
                parent is not None
                and leaf(label)
                and sum(leaf(c) for c in children[parent]) >= FAN_MIN_SIBLINGS
            )
            if in_fan and parent is not None and (parent, kind) in fans:
                run = fans[(parent, kind)]
                run.labels.append(label)
            elif run is not None and run.column == column:
                run.labels.append(label)
            else:
                run = Node(
                    labels=[label],
                    parent=parent,
                    kind=kind,
                    invalid=self.invalid.get(label),
                    tainted=parent is not None
                    and (
                        parent in self.invalid or self.node_of[parent].tainted
                    ),
                    fan=in_fan,
                    column=column,
                )
                self.nodes.append(run)
                if in_fan and parent is not None:
                    fans[(parent, kind)] = run
            self.node_of[label] = run

        node_children: Dict[int, List[Node]] = {
            id(node): [] for node in self.nodes
        }
        for node in self.nodes:
            if node.parent is not None:
                node_children[id(self.node_of[node.parent])].append(node)
        taken: Set[Tuple[int, int]] = set()

        def place(start: Node, parent_lane: int) -> None:
            path = [start]
            while node_children[id(path[-1])]:
                path.append(node_children[id(path[-1])][0])
            lane = parent_lane
            first = start.column
            while any((lane, n.column) in taken for n in path) or any(
                (between, first) in taken and (between, first - 1) in taken
                for between in range(parent_lane + 1, lane)
            ):
                lane += 1
            for node in path:
                node.lane = lane
                taken.add((lane, node.column))
            for node in path:
                for child in node_children[id(node)][1:]:
                    place(child, lane + 1)

        place(self.nodes[0], 0)
        self.lanes = 1 + max(node.lane for node in self.nodes)
        widths = [0.0] * len(self.column_heights)
        for node in self.nodes:
            width = max(46.0, CHAR_WIDTH * len(node.text) + 16)
            widths[node.column] = max(widths[node.column], width)
        self.column_width = widths
        self.column_x: List[float] = []
        x = float(PAD)
        for width in widths:
            self.column_x.append(x)
            x += width + COLUMN_GAP
        self.width = x - COLUMN_GAP + PAD

    def _ancestors(self, label: str | None) -> Set[str]:
        """Return `label` and its ancestors."""
        chain: Set[str] = set()
        while label is not None and label in self.parents:
            chain.add(label)
            label = self.parents[label]
        return chain

    def svg(self, frame: Frame | None = None) -> str:
        """
        Draw the DAG: every block when `frame` is `None`, else the state
        the frame holds.
        """
        overview = frame is None
        present = set(self.parents) if frame is None else frame.present
        forkchoice = Forkchoice() if frame is None else frame.forkchoice
        target = None if frame is None else frame.target
        canonical = self._ancestors(forkchoice.latest)
        height = self.lanes * LANE_PITCH + (AXIS_ROOM if overview else PAD)
        edges: List[str] = []
        boxes: List[str] = []
        texts: List[str] = []

        def box(node: Node) -> Tuple[float, float, float]:
            x = self.column_x[node.column]
            y = PAD + HEAD_ROOM + node.lane * LANE_PITCH
            return x, y, self.column_width[node.column]

        for node in self.nodes:
            x, y, width = box(node)
            middle = y + BLOCK_HEIGHT / 2
            here = all(label in present for label in node.labels)
            if node.parent is not None:
                parent = self.node_of[node.parent]
                px, py, pwidth = box(parent)
                start = px + pwidth
                classes = ["rg-e"]
                if not here:
                    classes.append("rg-e--ghost")
                elif node.labels[-1] in canonical:
                    classes.append("rg-e--canon")
                if parent.lane == node.lane:
                    path = f"M{start:g} {middle:g}H{x:g}"
                else:
                    bend = (start + x) / 2
                    start_y = py + BLOCK_HEIGHT / 2
                    path = (
                        f"M{start:g} {start_y:g}C{bend:g} {start_y:g} "
                        f"{bend:g} {middle:g} {x:g} {middle:g}"
                    )
                edges.append(f'<path class="{" ".join(classes)}" d="{path}"/>')
            classes = ["rg-b", f"rg-b--{node.kind}"]
            if node.invalid is not None:
                classes.append("rg-b--invalid")
            elif node.tainted:
                classes.append("rg-b--tainted")
            if not here:
                classes.append("rg-b--ghost")
            if target is not None and target in node.labels:
                classes.append("rg-b--target")
            title = ""
            if node.invalid is not None:
                title = (
                    "<title>invalid; a client may report "
                    f"{escape(node.invalid)}</title>"
                )
            elif len(node.labels) > 1:
                title = f"<title>{len(node.labels)} blocks</title>"
            boxes.append(
                f'<rect class="{" ".join(classes)}" x="{x:g}" y="{y:g}" '
                f'width="{width:g}" height="{BLOCK_HEIGHT}" rx="7">'
                f"{title}</rect>"
            )
            center = x + width / 2
            css = "rg-t rg-t--ghost" if not here else "rg-t"
            texts.append(
                f'<text class="{css}" x="{center:g}" y="{middle + 4:g}">'
                f"{escape(node.text)}</text>"
            )
            if node.invalid is not None:
                texts.append(
                    f'<text class="rg-x" x="{x + width - 3:g}" y="{y - 3:g}">'
                    "invalid</text>"
                )

            def marker(tag: str, label: str | None, node: Node = node) -> str:
                if label is None or label not in node.labels:
                    return ""
                if len(node.labels) > 1:
                    return f"{tag} {label}"
                return tag

            head = marker("head", forkchoice.latest)
            if head:
                texts.append(
                    f'<text class="rg-h" x="{center:g}" y="{y - 4:g}">'
                    f"{escape(head)}</text>"
                )
            below = [
                text
                for text in (
                    marker("safe", forkchoice.safe),
                    marker("finalized", forkchoice.finalized),
                )
                if text
            ]
            for line, text in enumerate(below):
                text_y = y + BLOCK_HEIGHT + 11 + 11 * line
                texts.append(
                    f'<text class="rg-s" x="{center:g}" y="{text_y:g}">'
                    f"{escape(text)}</text>"
                )
        if overview:
            axis_y = height - 4
            for column, heights in enumerate(self.column_heights):
                text = str(heights[0])
                if len(heights) > 1:
                    text += f"–{heights[-1]}"
                center = self.column_x[column] + self.column_width[column] / 2
                texts.append(
                    f'<text class="rg-a" x="{center:g}" y="{axis_y:g}">'
                    f"{text}</text>"
                )
        css = "rg-svg" if overview else "rg-svg rg-svg--frame"
        return (
            f'<svg class="{css}" viewBox="0 0 {self.width:g} {height:g}" '
            f'width="{self.width:g}" height="{height:g}" role="img" '
            f'aria-label="{escape(self._describe(frame))}">'
            f"{''.join(edges)}{''.join(boxes)}{''.join(texts)}</svg>"
        )

    def _describe(self, frame: Frame | None) -> str:
        """Return the text alternative of a drawing."""
        if frame is None:
            chains = ", ".join(
                f"{label} on {parent}"
                for label, parent in self.parents.items()
                if parent is not None
            )
            return f"Block DAG: {chains}"
        parts = [
            f"{tag} {label}"
            for tag, label in (
                ("head", frame.forkchoice.latest),
                ("safe", frame.forkchoice.safe),
                ("finalized", frame.forkchoice.finalized),
            )
            if label is not None
        ]
        return "State after the step: " + ", ".join(parts)

    # The page

    def kinds_used(self) -> List[str]:
        """Return the block kinds and marks drawn, in legend order."""
        used = {node.kind for node in self.nodes}
        kinds = [kind for kind in BLOCK_KINDS if kind in used]
        if self.invalid:
            kinds.append("invalid")
        if any(node.tainted for node in self.nodes):
            kinds.append("tainted")
        return kinds

    def _row_html(self, row: Row) -> str:
        """Render one step."""
        step = row.step
        html = '<li class="rg-step"><div class="rg-call">'
        html += f'<span class="rg-n">{row.number}</span> {render_call(step)}'
        if step.description:
            html += f'<div class="rg-desc">{escape(step.description)}</div>'
        build = self._build_timestamp(step)
        if build:
            html += f'<div class="rg-desc">{build}</div>'
        if row.outcomes:
            several = len(row.outcomes) > 1
            head = "accepts the first match of" if several else "accepts"
            outcomes = "".join(render_outcome(view) for view in row.outcomes)
            html += (
                f'<div class="rg-expect"><span class="rg-expect-h">{head}'
                f'</span><ul class="rg-os">{outcomes}</ul></div>'
            )
        html += "</div>"
        if row.frames:
            html += '<div class="rg-frames">'
            for frame in row.frames:
                html += '<div class="rg-frame">'
                if frame.caption:
                    html += f'<div class="rg-cap">{frame.caption}</div>'
                html += f"{self.svg(frame)}</div>"
            html += "</div>"
        return html + "</li>"

    def _build_timestamp(self, step: Step) -> str:
        """
        Say how the timestamp of a build request relates to its head's,
        when the fixture holds both.
        """
        if (
            not isinstance(step, ForkchoiceUpdatedStep)
            or step.payload_attributes is None
            or step.head not in self.timestamps
        ):
            return ""
        ahead = (
            int(step.payload_attributes.timestamp) - self.timestamps[step.head]
        )
        if ahead == 0:
            relation = "equal to the head's"
        elif ahead > 0:
            relation = f"{ahead} s after the head's"
        else:
            relation = f"{-ahead} s before the head's"
        return f"payload attributes: timestamp {relation}"

    def _items_html(self, items: Sequence[Item]) -> str:
        """Render a list of script items."""
        html = '<ol class="rg-steps">'
        for item in items:
            if isinstance(item, Row):
                html += self._row_html(item)
            elif isinstance(item, Fold):
                count = len(item.blocks)
                html += (
                    '<li class="rg-fold">⋮ steps '
                    f"{item.first} to {item.last} repeat the same calls "
                    f"for {count} more block{'s' if count != 1 else ''}, "
                    f"{_label(item.blocks[0])} to {_label(item.blocks[-1])}"
                    "</li>"
                )
            elif isinstance(item, Note):
                html += f'<li class="rg-note">{item.html}</li>'
            else:
                html += '<li class="rg-split">'
                for ids, flow in item.branches:
                    html += (
                        '<div class="rg-branch"><div class="rg-branch-h">'
                        f"After {_ids(ids)}</div>{self._items_html(flow)}"
                        "</div>"
                    )
                html += "</li>"
        return html + "</ol>"

    def html(self) -> str:
        """Render the scenario: the DAG, then the script."""
        blocks = len(self.parents) - 1
        summary = (
            f"{blocks} block{'s' if blocks != 1 else ''} and "
            f"{self.step_count} step{'s' if self.step_count != 1 else ''}"
        )
        if self.min_reorg_depth is not None:
            summary += (
                ", with the client set to apply reorgs at least "
                f"{self.min_reorg_depth} blocks deep"
            )
        invalid = "".join(
            f"<li>{_label(label)} is invalid; a client may report "
            f"{_reported(reason)}</li>"
            for label, reason in self.invalid.items()
        )
        if invalid:
            invalid = f'<ul class="rg-invalid">{invalid}</ul>'
        return (
            f'<div class="rg{" rg--wide" if self.width > WIDE else ""}">'
            f'<div class="rg-dag"><div class="rg-dag-h">Block DAG '
            f'<span class="rg-sum">{summary}</span></div>'
            f'<div class="rg-scroll">{self.svg()}</div>{invalid}</div>'
            f"{self._items_html(self.items)}</div>"
        )


def render_legend(kinds: Sequence[str]) -> str:
    """Render the legend for the block kinds in `kinds`."""
    texts = {**BLOCK_KINDS, **BLOCK_MARKS}
    entries = [
        f'<span><i class="rg-sw rg-sw--{kind}"></i>{texts[kind]}</span>'
        for kind in kinds
    ]
    entries.append(
        '<span><i class="rg-sw rg-sw--ghost"></i>not sent yet</span>'
    )
    entries.append(
        '<span><i class="rg-sw rg-sw--target"></i>block the step names</span>'
    )
    entries.append('<span><i class="rg-line"></i>chain of the head</span>')
    return f'<div class="rg-legend">{"".join(entries)}</div>'


def render_section(scenarios: Sequence[Tuple[str, Scenario]]) -> str:
    """
    Render the scenarios of one test function as Markdown: the legend, then
    each scenario, in content tabs named by parameter set if several.
    """
    kinds = [
        kind
        for kind in (*BLOCK_KINDS, *BLOCK_MARKS)
        if any(kind in scenario.kinds_used() for _, scenario in scenarios)
    ]
    lines = [render_legend(kinds), ""]
    if len(scenarios) == 1:
        lines.append(scenarios[0][1].html())
    else:
        for title, scenario in scenarios:
            safe_title = title.replace("\\", "\\\\").replace('"', '\\"')
            lines += [f'=== "{safe_title}"', "", f"    {scenario.html()}", ""]
    return "\n".join(lines)
