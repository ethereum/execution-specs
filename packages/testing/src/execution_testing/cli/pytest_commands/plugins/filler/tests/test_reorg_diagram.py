"""Tests for the reorg diagrams of the test case reference."""

from typing import Any, Dict, List, Literal

import pytest

from execution_testing.base_types import Address, Hash, Number
from execution_testing.exceptions import EngineAPIError
from execution_testing.fixtures.blockchain import PayloadAttributes
from execution_testing.fixtures.reorg import (
    AssertCanonicalStep,
    AssertHeadStep,
    AwaitHeadStep,
    ForkchoiceUpdatedStep,
    GetPayloadStep,
    NewPayloadStep,
    Outcome,
    ServePeerStep,
    Step,
    StepBase,
)

from ..gen_test_doc import reorg_diagram
from ..gen_test_doc.gen_test_doc import reorg_case_title
from ..gen_test_doc.page_props import TestCase as DocTestCase
from ..gen_test_doc.reorg_diagram import (
    Fold,
    Forkchoice,
    Note,
    Row,
    Scenario,
    Split,
    render_section,
)


def valid(block: str) -> List[Outcome]:
    """Return the single VALID outcome of a payload."""
    return [Outcome(id="valid", status="VALID", latest_valid_hash=block)]


def new_payload(block: str) -> NewPayloadStep:
    """Return a filled `newPayload` step."""
    return NewPayloadStep(block=block, expect=valid(block))


def forkchoice(head: str, **kwargs: Any) -> ForkchoiceUpdatedStep:
    """Return a filled, applied `forkchoiceUpdated` step."""
    return ForkchoiceUpdatedStep(
        head=head,
        version=3,
        expect=[Outcome(id="applied", status="VALID", latest_valid_hash=head)],
        branches={"applied": [AssertHeadStep(latest=head, **kwargs)]},
    )


def linear(prefix: str, length: int, parent: str = "genesis") -> Dict:
    """Return the blocks of a chain `{prefix}1..` on `parent`."""
    blocks = {}
    for i in range(1, length + 1):
        blocks[f"{prefix}{i}"] = parent
        parent = f"{prefix}{i}"
    return blocks


def rows(scenario: Scenario) -> List[Row]:
    """Return the top-level step rows of a scenario."""
    return [item for item in scenario.items if isinstance(item, Row)]


def test_dag_layout_and_block_kinds() -> None:
    """
    Blocks sit in the column of their height, a side chain in a lane of
    its own, and are styled by how they reach the client.
    """
    blocks = {**linear("a", 3), "b2": "a1", "b3": "b2", "never": "a3"}
    steps: List[Step] = [
        new_payload("a1"),
        new_payload("b2"),
        GetPayloadStep(bind="built", version=3, parent="a1"),
    ]
    scenario = Scenario(blocks, steps, invalid={"b3": "BAD <root>"})

    place = {n.text: (n.column, n.lane) for n in scenario.nodes}
    assert place["genesis"] == (0, 0)
    assert place["a3"] == (3, 0)
    assert place["b2"] == (2, 1)
    assert place["b3"] == (3, 1)
    assert place["built"] == (2, 2)
    kinds = {n.text: n.kind for n in scenario.nodes}
    assert kinds["genesis"] == "genesis"
    assert kinds["a1"] == kinds["b2"] == "engine"
    assert kinds["built"] == "built"
    assert kinds["never"] == kinds["b3"] == "unsent"
    assert scenario.kinds_used() == [
        "genesis",
        "engine",
        "built",
        "unsent",
        "invalid",
    ]

    svg = scenario.svg()
    assert "rg-b--unsent rg-b--invalid" in svg
    assert "a client may report BAD &lt;root&gt;" in svg
    assert "BAD &lt;root&gt;" in scenario.html()


def test_frames_follow_the_asserted_forkchoice() -> None:
    """
    A frame shows the blocks delivered so far and the head, safe and
    finalized blocks the leading `assertHead` of the outcome names.
    """
    steps: List[Step] = [
        new_payload("a1"),
        forkchoice("a1"),
        new_payload("a2"),
        forkchoice("a2", safe="a1", finalized="a1"),
    ]
    first, second, third, fourth = rows(Scenario(linear("a", 2), steps))

    (frame,) = first.frames
    assert frame.present == {"genesis", "a1"}
    assert frame.target == "a1"
    assert frame.forkchoice.latest == "genesis"
    assert second.frames[0].forkchoice.latest == "a1"
    assert third.frames[0].forkchoice.latest == "a1"
    assert third.frames[0].present == {"genesis", "a1", "a2"}
    final = fourth.frames[0].forkchoice
    assert (final.latest, final.safe, final.finalized) == ("a2", "a1", "a1")


def test_outcomes_disputed_and_diverging_frames() -> None:
    """
    Every accepted outcome is listed with its dispute; outcomes leaving
    different heads get a frame each, captioned by their ids.
    """
    blocks = {**linear("a", 2), "b2": "a1"}
    steps: List[Step] = [
        new_payload("a1"),
        new_payload("a2"),
        forkchoice("a2"),
        new_payload("b2"),
        ForkchoiceUpdatedStep(
            head="b2",
            version=3,
            expect=[
                Outcome(id="applied", status="VALID", head_moved=True),
                Outcome(
                    id="refused",
                    error_code=EngineAPIError.TooDeepReorg,
                    disputed="spec#1: <why>",
                ),
            ],
            branches={
                "applied": [AssertHeadStep(latest="b2")],
                "refused": [AssertHeadStep(latest="a2")],
            },
        ),
    ]
    scenario = Scenario(blocks, steps)
    last = rows(scenario)[-1]

    assert [f.forkchoice.latest for f in last.frames] == ["b2", "a2"]
    assert [f.caption for f in last.frames] == [
        "after <code>applied</code>",
        "after <code>refused</code>",
    ]
    html = scenario.html()
    assert "error -38006" in html
    assert "TooDeepReorg" in html
    assert "head moved" in html
    assert '<span class="rg-tag">disputed</span>' in html
    assert "spec#1: &lt;why&gt;" in html
    assert "accepts the first match of" in html


def test_long_chains_are_folded_and_elided() -> None:
    """
    A run of look-alike steps keeps its first and last repetition, and the
    plain blocks in between are drawn as one box. The head before the
    last repetition, `a39`, stays a box of its own.
    """
    steps: List[Step] = []
    for i in range(1, 41):
        steps += [new_payload(f"a{i}"), forkchoice(f"a{i}")]
    scenario = Scenario(linear("a", 40), steps)

    numbers = [i.number for i in scenario.items if isinstance(i, Row)]
    assert numbers == [1, 2, 79, 80]
    (fold,) = [i for i in scenario.items if isinstance(i, Fold)]
    assert (fold.first, fold.last) == (3, 78)
    assert fold.blocks == [f"a{i}" for i in range(2, 40)]
    assert scenario.step_count == 80
    assert [n.text for n in scenario.nodes] == [
        "genesis",
        "a1",
        "a2 … a38",
        "a39",
        "a40",
    ]
    assert "repeat the same calls for 38 more blocks" in scenario.html()


def test_fold_ignores_the_engine_api_version() -> None:
    """Steps that differ only in their version fold like the others."""
    steps: List[Step] = []
    for i in range(1, 11):
        step = forkchoice(f"a{i}")
        step.version = Number(2 if i < 5 else 3)
        steps += [new_payload(f"a{i}"), step]
    scenario = Scenario(linear("a", 10), steps)

    assert [type(i) for i in scenario.items] == [Row, Row, Fold, Row, Row]


def test_many_plain_siblings_share_one_box() -> None:
    """
    Childless siblings no shown step names are drawn as one box; the ones
    a step names keep their own.
    """
    blocks = {"a1": "genesis", **{f"s{i}": "a1" for i in range(1, 21)}}
    steps: List[Step] = [new_payload("a1")]
    steps += [new_payload(f"s{i}") for i in range(1, 21)]
    scenario = Scenario(blocks, steps)

    # The steps for `a1` to `s20` fold; the last one keeps `s20` shown.
    assert [n.text for n in scenario.nodes] == [
        "genesis",
        "a1",
        "19 \u00d7 s1 \u2026 s19",
        "s20",
    ]
    assert scenario.lanes == 2


def test_blocks_on_an_invalid_block_are_marked() -> None:
    """Descendants of an invalid block are drawn as built on it."""
    blocks = {**linear("a", 2), "bad": "a1", "c3": "bad", "c4": "c3"}
    scenario = Scenario(blocks, [], invalid={"bad": "BAD"})

    tainted = {n.text for n in scenario.nodes if n.tainted}
    assert tainted == {"c3", "c4"}
    assert scenario.kinds_used() == ["genesis", "unsent", "invalid", "tainted"]
    assert "rg-b--tainted" in scenario.svg()
    assert "built on an invalid block" in render_section([("x", scenario)])


def test_wide_dags_get_the_full_width() -> None:
    """A DAG too wide for half the page is marked for the wide layout."""
    narrow = Scenario(linear("a", 3), [])
    named: List[Step] = [AssertHeadStep(latest=f"a{i}") for i in range(1, 13)]
    wide = Scenario(linear("a", 12), named)

    assert '<div class="rg">' in narrow.html()
    assert '<div class="rg rg--wide">' in wide.html()


def test_new_payload_branch_keeps_safe_and_finalized() -> None:
    """
    A head assertion leading a `newPayload` branch leaves the markers it
    does not name where they were.
    """
    steps: List[Step] = [
        new_payload("a1"),
        forkchoice("a1", safe="a1", finalized="a1"),
        NewPayloadStep(
            block="a2",
            expect=valid("a2"),
            branches={"valid": [AssertHeadStep(latest="a1")]},
        ),
    ]
    last = rows(Scenario(linear("a", 2), steps))[-1]

    forkchoice_after = last.frames[0].forkchoice
    assert (forkchoice_after.safe, forkchoice_after.finalized) == ("a1", "a1")


def test_short_chains_are_drawn_in_full() -> None:
    """Below the thresholds nothing is folded or elided."""
    steps: List[Step] = [new_payload(f"a{i}") for i in range(1, 5)]
    scenario = Scenario(linear("a", 4), steps)

    assert len(rows(scenario)) == 4
    assert len(scenario.nodes) == 5


def test_branches_with_the_same_follow_up_are_merged() -> None:
    """
    Outcomes sharing their follow-up steps continue as one script; the
    outcomes that end the test are named.
    """
    follow_up: List[Step] = [AssertCanonicalStep(blocks={1: "a1"})]

    def step(branches: Dict[str, List[Step]]) -> ForkchoiceUpdatedStep:
        return ForkchoiceUpdatedStep(
            head="a1",
            version=3,
            expect=[
                Outcome(id="applied", status="VALID"),
                Outcome(id="kept", status="VALID", head_moved=False),
                Outcome(id="syncing", status="SYNCING"),
            ],
            branches=branches,
        )

    blocks = linear("a", 1)
    merged = Scenario(
        blocks, [step({"applied": follow_up, "kept": follow_up})]
    )
    assert [type(i) for i in merged.items] == [Row, Note, Row]
    note = merged.items[1]
    assert isinstance(note, Note)
    assert "<code>applied</code> or <code>kept</code>" in note.html
    assert "after <code>syncing</code> the test ends here" in note.html

    other: List[Step] = [AssertCanonicalStep(blocks={1: None})]
    split = Scenario(blocks, [step({"applied": follow_up, "kept": other})])
    assert [type(i) for i in split.items] == [Row, Split]
    branches = split.items[1]
    assert isinstance(branches, Split)
    assert [ids for ids, _ in branches.branches] == [["applied"], ["kept"]]
    assert "After <code>kept</code>" in split.html()


class ImportStep(StepBase):
    """A step type the renderer does not know."""

    type: Literal["importChain"] = "importChain"
    head: str

    def label_refs(self) -> List[str]:
        """Return the served head."""
        return [self.head]


def test_new_step_type_and_block_kind(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    An unknown step type is rendered from its fields; one registry entry
    each gives it a rendering of its own and a block kind it delivers.
    """
    blocks = linear("a", 3)
    steps: List[Any] = [ImportStep(head="a2"), new_payload("a3")]

    generic = Scenario(blocks, steps)
    assert (
        "importChain</code> head <code>&quot;a2&quot;</code>" in generic.html()
    )
    assert {n.text: n.kind for n in generic.nodes}["a1"] == "unsent"

    def imported(step: ImportStep, parents: Any) -> List[str]:
        chain = []
        label: str | None = step.head
        while label is not None and parents[label] is not None:
            chain.append(label)
            label = parents[label]
        return chain

    monkeypatch.setitem(reorg_diagram.BLOCK_KINDS, "file", "read from a file")
    monkeypatch.setitem(
        reorg_diagram.DELIVERIES, "importChain", ("file", imported)
    )
    monkeypatch.setitem(
        reorg_diagram.STEP_RENDERERS,
        "importChain",
        lambda step: f"imports up to {step.head}",
    )
    scenario = Scenario(blocks, steps)
    kinds = {n.text: n.kind for n in scenario.nodes}
    assert (kinds["a1"], kinds["a2"], kinds["a3"]) == (
        "file",
        "file",
        "engine",
    )
    assert scenario.kinds_used() == ["genesis", "engine", "file"]
    assert "read from a file" in render_section([("x", scenario)])
    html = scenario.html()
    assert "imports up to a2" in html
    assert "rg-b--file" in html
    (frame,) = rows(scenario)[0].frames
    assert frame.present == {"genesis", "a1", "a2"}


def test_from_fixture_and_deterministic_output() -> None:
    """
    A scenario is read from fixture JSON alone, and rendering it twice
    gives the same single block of HTML.
    """
    fixture = {
        "minReorgDepth": "72",
        "blocks": {
            "a1": {
                "parent": "genesis",
                "payload": {"params": [{"timestamp": "0xc"}]},
            },
            "b1": {
                "parent": "genesis",
                "payload": {"params": [{"timestamp": "0xc"}]},
                "validationError": "BlockException.BAD",
            },
        },
        "steps": [
            {
                "type": "newPayload",
                "block": "a1",
                "expect": [{"id": "valid", "status": "VALID"}],
                "branches": {},
            },
            {
                "type": "forkchoiceUpdated",
                "head": "a1",
                "safe": "zero",
                "finalized": "zero",
                "version": "3",
                "expect": [{"id": "applied", "status": "VALID"}],
                "branches": {
                    "applied": [{"type": "assertHead", "latest": "a1"}]
                },
            },
        ],
    }
    html = Scenario.from_fixture(fixture).html()

    assert html == Scenario.from_fixture(fixture).html()
    assert "\n" not in html
    assert "rg-b--invalid" in html
    assert "BlockException.BAD" in html
    assert "at least 72 blocks deep" in html
    # Fork-specific values stay out.
    assert "version" not in html


def test_render_section_uses_tabs_for_several_parameter_sets() -> None:
    """One scenario is rendered as is, several as content tabs."""
    scenario = Scenario(linear("a", 1), [new_payload("a1")])

    single = render_section([("scenario", scenario)])
    assert "===" not in single
    assert single.count('<div class="rg">') == 1

    tabbed = render_section([("depth_1", scenario), ('depth_"2"', scenario)])
    assert '=== "depth_1"\n\n    <div class="rg">' in tabbed
    assert '=== "depth_\\"2\\""' in tabbed
    assert tabbed.count('<div class="rg-legend">') == 1


@pytest.mark.parametrize(
    "abbreviated_id,title",
    [
        ("fork_Prague-blockchain_test_engine_reorg-depth_8", "depth_8"),
        (
            "fork_Prague-blockchain_test_engine_reorg-from_a1-invalid_index_1",
            "from_a1-invalid_index_1",
        ),
        ("fork_Prague-blockchain_test_engine_reorg", "scenario"),
    ],
)
def test_reorg_case_title(abbreviated_id: str, title: str) -> None:
    """The title of a parameter set drops the fork and fixture format."""
    case = DocTestCase(
        full_id=f"tests/reorg/test_x.py::test_x[{abbreviated_id}]",
        abbreviated_id=abbreviated_id,
        fork="Prague",
        fixture_type="blockchain_test_engine_reorg",
        params={},
    )
    assert reorg_case_title(case) == title


def test_syncing_forkchoice_keeps_safe_and_finalized() -> None:
    """
    An authored head assertion after a SYNCING forkchoice answer names
    only the head: safe and finalized stay, and the assertion is shown.
    """
    steps: List[Step] = [
        new_payload("a1"),
        new_payload("a2"),
        forkchoice("a2", safe="a1", finalized="a1"),
        ForkchoiceUpdatedStep(
            head="u",
            version=3,
            expect=[Outcome(id="syncing", status="SYNCING")],
            branches={"syncing": [AssertHeadStep(latest="a2")]},
        ),
    ]
    scenario = Scenario({**linear("a", 2), "u": "a2"}, steps)

    after = rows(scenario)[-1].frames[0].forkchoice
    assert (after.latest, after.safe, after.finalized) == ("a2", "a1", "a1")
    assert 'then latest <b class="rg-l">a2</b>' in scenario.html()


def test_outcomes_leaving_different_heads_are_not_merged() -> None:
    """
    Outcomes with the same follow-up steps but different heads keep a
    branch each, drawn from the head each one leaves.
    """
    follow_up: List[Step] = [new_payload("x")]
    steps: List[Step] = [
        ForkchoiceUpdatedStep(
            head="b1",
            version=3,
            expect=[
                Outcome(id="applied", status="VALID"),
                Outcome(id="refused", error_code=EngineAPIError.TooDeepReorg),
            ],
            branches={
                "applied": [AssertHeadStep(latest="b1"), *follow_up],
                "refused": [AssertHeadStep(latest="a1"), *follow_up],
            },
        ),
    ]
    blocks = {"a1": "genesis", "b1": "genesis", "x": "genesis"}
    scenario = Scenario(blocks, steps)

    split = scenario.items[1]
    assert isinstance(split, Split)
    heads = []
    for _, flow in split.branches:
        (row,) = flow
        assert isinstance(row, Row)
        heads.append(row.frames[0].forkchoice.latest)
    assert heads == ["b1", "a1"]


def test_extra_steps_of_one_outcome_do_not_end_the_test() -> None:
    """
    When later steps follow whatever the outcome, steps only one outcome
    has are drawn as its branch, not as the end of the test for the others.
    """
    steps: List[Step] = [
        NewPayloadStep(
            block="a1",
            expect=[
                Outcome(id="valid", status="VALID"),
                Outcome(id="accepted", status="ACCEPTED"),
            ],
            branches={"valid": [AssertCanonicalStep(blocks={1: None})]},
        ),
        forkchoice("a1"),
    ]
    scenario = Scenario(linear("a", 1), steps)

    assert [type(i) for i in scenario.items] == [Row, Split, Row]
    assert "the test ends here" not in scenario.html()


def test_invalid_block_lists_what_a_client_may_report() -> None:
    """The exceptions of an invalid block are shown as alternatives."""
    two = Scenario(linear("a", 1), [], invalid={"a1": "E.A|E.B"})
    many = Scenario(linear("a", 1), [], invalid={"a1": "E.A|E.B|E.C|E.D|E.E"})

    assert (
        "is invalid; a client may report <code>E.A</code> or "
        "<code>E.B</code>" in two.html()
    )
    assert "<code>E.C</code> or one of 2 others" in many.html()


def test_build_request_shows_version_and_relative_timestamp() -> None:
    """
    Build requests that differ only in method version or timestamp are
    told apart.
    """

    def build(version: int, timestamp: int) -> ForkchoiceUpdatedStep:
        return ForkchoiceUpdatedStep(
            head="a1",
            version=version,
            payload_attributes=PayloadAttributes(
                timestamp=timestamp,
                prev_randao=Hash(0),
                suggested_fee_recipient=Address(0),
            ),
            expect=[Outcome(id="applied", status="VALID")],
        )

    scenario = Scenario(
        linear("a", 1),
        [build(3, 24), build(4, 12)],
        timestamps={"a1": 12},
    )
    html = scenario.html()

    assert "build request, sent as forkchoiceUpdatedV3" in html
    assert "build request, sent as forkchoiceUpdatedV4" in html
    assert "timestamp 12 s after the head's" in html
    assert "timestamp equal to the head's" in html


def test_blocks_synced_from_the_peer() -> None:
    """
    `awaitHead` moves the head and brings in the ancestors the client was
    never sent, as blocks of their own kind; `servePeer` changes nothing
    the client has.
    """
    syncing = Outcome(id="syncing", status="SYNCING")
    steps: List[Any] = [
        ForkchoiceUpdatedStep(
            head="genesis",
            version=3,
            expect=[Outcome(id="applied", status="VALID")],
            branches={
                "applied": [
                    AssertHeadStep(
                        latest="genesis", safe="genesis", finalized="genesis"
                    )
                ]
            },
        ),
        NewPayloadStep(block="a3", expect=[syncing]),
        ForkchoiceUpdatedStep(head="a3", version=3, expect=[syncing]),
        ServePeerStep(head="a3"),
        AwaitHeadStep(latest="a3"),
    ]
    scenario = Scenario(linear("a", 3), steps)

    kinds = {n.text: n.kind for n in scenario.nodes}
    assert kinds == {
        "genesis": "genesis",
        "a1": "peer",
        "a2": "peer",
        "a3": "engine",
    }
    assert scenario.kinds_used() == ["genesis", "engine", "peer"]

    *_, serve, wait = rows(scenario)
    assert serve.frames == []
    (frame,) = wait.frames
    assert frame.present == {"genesis", "a1", "a2", "a3"}
    assert frame.target == "a3"
    assert frame.forkchoice == Forkchoice(
        latest="a3", safe="genesis", finalized="genesis"
    )

    html = scenario.html()
    assert "a devp2p peer serves the chain from genesis to" in html
    assert "the client syncs from the peer until latest is" in html
    assert "rg-b--peer" in html
    assert "synced from the devp2p peer" in render_section([("x", scenario)])
