"""Unit tests for the Engine API reference model used by reorg tests."""

from typing import List

import pytest
from pydantic import ValidationError

from execution_testing.exceptions import EngineAPIError
from execution_testing.fixtures.reorg import (
    AssertHeadStep,
    ForkchoiceUpdatedStep,
    NewPayloadStep,
    Outcome,
    Step,
)

from ..engine_model import ClientModel, ModelDag, annotate_steps


def dag_linear_with_fork() -> ModelDag:
    r"""
    Genesis <- a1 <- a2 <- a3.
                 \\- b2 <- b3      (b3 execution-invalid).
    """
    return ModelDag(
        parent={
            "a1": "genesis",
            "a2": "a1",
            "a3": "a2",
            "b2": "a1",
            "b3": "b2",
        },
        valid={"a1": True, "a2": True, "a3": True, "b2": True, "b3": False},
    )


def ids(outcomes: List[Outcome]) -> List[str]:
    """Outcome ids."""
    return [o.id for o in outcomes]


def test_number_and_ancestry() -> None:  # noqa: D103
    dag = dag_linear_with_fork()
    assert dag.number("genesis") == 0
    assert dag.number("a3") == 3
    assert dag.number("b3") == 3
    assert dag.is_ancestor("a1", "b3")
    assert not dag.is_ancestor("a2", "b3")
    assert not dag.is_ancestor("a3", "a3")
    assert dag.last_valid_ancestor("b3") == "b2"


def test_new_payload_unknown_parent_is_syncing() -> None:  # noqa: D103
    model = ClientModel(dag=dag_linear_with_fork())
    assert ids(model.new_payload_outcomes("a2")) == ["syncing"]


def test_new_payload_extends_head_is_valid_only() -> None:  # noqa: D103
    model = ClientModel(dag=dag_linear_with_fork())
    outcomes = model.new_payload_outcomes("a1")
    assert ids(outcomes) == ["valid"]
    assert outcomes[0].latest_valid_hash == "a1"


def test_new_payload_side_chain_valid_or_accepted() -> None:  # noqa: D103
    model = ClientModel(dag=dag_linear_with_fork())
    model.known.update({"a1": True, "a2": True})
    model.head = "a2"
    assert ids(model.new_payload_outcomes("b2")) == ["valid", "accepted"]


def test_new_payload_invalid_block() -> None:  # noqa: D103
    model = ClientModel(dag=dag_linear_with_fork())
    model.known.update({"a1": True, "b2": True})
    model.head = "b2"
    outcomes = model.new_payload_outcomes("b3")
    assert ids(outcomes) == ["invalid"]
    assert outcomes[0].latest_valid_hash == "b2"
    assert outcomes[0].validation_error == "required"


def test_new_payload_child_of_known_invalid() -> None:  # noqa: D103
    dag = dag_linear_with_fork()
    dag.parent["b4"] = "b3"
    dag.valid["b4"] = True
    model = ClientModel(dag=dag)
    model.known.update({"a1": True, "b2": True, "b3": False})
    outcomes = model.new_payload_outcomes("b4")
    assert ids(outcomes) == ["invalid", "syncing"]
    assert outcomes[0].latest_valid_hash == "b2"
    # A grandchild of the invalid block is also INVALID-or-SYNCING, never
    # SYNCING-only: clients with a bad-block cache answer INVALID.
    model.apply_new_payload("b4", outcomes)
    dag.parent["b5"] = "b4"
    dag.valid["b5"] = True
    outcomes = model.new_payload_outcomes("b5")
    assert ids(outcomes) == ["invalid", "syncing"]
    assert outcomes[0].latest_valid_hash == "b2"


def test_fcu_unknown_head_is_syncing() -> None:  # noqa: D103
    model = ClientModel(dag=dag_linear_with_fork())
    step = ForkchoiceUpdatedStep(head="a1")
    assert ids(model.forkchoice_outcomes(step)) == ["syncing"]


def test_fcu_extend_head_is_applied_only() -> None:  # noqa: D103
    model = ClientModel(dag=dag_linear_with_fork())
    model.known["a1"] = True
    step = ForkchoiceUpdatedStep(head="a1")
    outcomes = model.forkchoice_outcomes(step)
    assert ids(outcomes) == ["applied"]
    model.apply_forkchoice(step, outcomes[0])
    assert model.head == "a1"


def test_fcu_side_chain_reorg_applied_or_refused() -> None:  # noqa: D103
    model = ClientModel(dag=dag_linear_with_fork())
    model.known.update({"a1": True, "a2": True, "b2": True})
    model.head = "a2"
    outcomes = model.forkchoice_outcomes(ForkchoiceUpdatedStep(head="b2"))
    assert ids(outcomes) == ["applied", "refused"]
    assert outcomes[1].error_code == EngineAPIError.TooDeepReorg


def test_fcu_rewind_to_canonical_ancestor_above_finalized() -> None:  # noqa: D103
    model = ClientModel(dag=dag_linear_with_fork())
    model.known.update({"a1": True, "a2": True, "a3": True})
    model.head = "a3"
    model.finalized = "a1"
    # a2 is above finalized: the update has to be applied, or refused with
    # the client's own depth limit. Skipping it is not one of the options.
    outcomes = model.forkchoice_outcomes(
        ForkchoiceUpdatedStep(head="a2", finalized="a1")
    )
    assert ids(outcomes) == ["applied", "refused"]


def test_fcu_error_leaves_forkchoice_state_untouched() -> None:  # noqa: D103
    model = ClientModel(dag=dag_linear_with_fork())
    model.known.update({"a1": True, "a2": True, "a3": True, "b2": True})
    model.head, model.safe, model.finalized = "a3", "a2", "a1"
    step = ForkchoiceUpdatedStep(head="b2", safe="a3", finalized="a1")
    outcomes = model.forkchoice_outcomes(step)
    assert ids(outcomes) == ["inconsistent"]
    model.apply_forkchoice(step, outcomes[0])
    assertion = model.head_assertion()
    assert (assertion.latest, assertion.safe, assertion.finalized) == (
        "a3",
        "a2",
        "a1",
    )


def test_fcu_ancestor_of_finalized_is_noop() -> None:  # noqa: D103
    model = ClientModel(dag=dag_linear_with_fork())
    model.known.update({"a1": True, "a2": True, "a3": True})
    model.head = "a3"
    model.finalized = "a2"
    outcomes = model.forkchoice_outcomes(
        ForkchoiceUpdatedStep(head="a1", finalized="a2")
    )
    assert ids(outcomes) == ["noop"]
    assert outcomes[0].status == "VALID"


def test_fcu_head_equals_finalized_is_disputed() -> None:  # noqa: D103
    model = ClientModel(dag=dag_linear_with_fork())
    model.known.update({"a1": True, "a2": True, "a3": True})
    model.head = "a3"
    model.finalized = "a2"
    outcomes = model.forkchoice_outcomes(
        ForkchoiceUpdatedStep(head="a2", finalized="a2")
    )
    assert ids(outcomes) == ["applied", "noop"]
    assert outcomes[1].disputed is not None


def test_fcu_inconsistent_finalized_is_error() -> None:  # noqa: D103
    model = ClientModel(dag=dag_linear_with_fork())
    model.known.update({"a1": True, "a2": True, "b2": True})
    model.head = "a2"
    outcomes = model.forkchoice_outcomes(
        ForkchoiceUpdatedStep(head="a2", finalized="b2")
    )
    assert ids(outcomes) == ["inconsistent"]
    assert outcomes[0].error_code == EngineAPIError.InvalidForkchoiceState


def test_fcu_invalid_head() -> None:  # noqa: D103
    model = ClientModel(dag=dag_linear_with_fork())
    model.known.update({"a1": True, "b2": True, "b3": False})
    outcomes = model.forkchoice_outcomes(ForkchoiceUpdatedStep(head="b3"))
    assert ids(outcomes) == ["invalid"]
    assert outcomes[0].latest_valid_hash == "b2"


def test_annotate_fills_expect_and_head_assertions() -> None:  # noqa: D103
    model = ClientModel(dag=dag_linear_with_fork())
    steps: List[Step] = [
        NewPayloadStep(block="a1"),
        ForkchoiceUpdatedStep(head="a1"),
        NewPayloadStep(block="a2"),
        ForkchoiceUpdatedStep(head="a2"),
        NewPayloadStep(block="b2"),
        ForkchoiceUpdatedStep(head="b2"),
    ]
    versions = {"a1": 3, "a2": 3, "b2": 3}
    annotate_steps(steps, model, versions)

    np_a1, fcu_a1, np_a2, fcu_a2, np_b2, fcu_b2 = steps
    assert isinstance(np_a1, NewPayloadStep)
    assert ids(np_a1.expect) == ["valid"]
    assert isinstance(fcu_a1, ForkchoiceUpdatedStep)
    assert fcu_a1.version == 3
    assert ids(fcu_a1.expect) == ["applied"]
    applied = fcu_a1.branches["applied"]
    assert isinstance(applied[-1], AssertHeadStep)
    assert applied[-1].latest == "a1"
    assert isinstance(np_b2, NewPayloadStep)
    assert ids(np_b2.expect) == ["valid", "accepted"]
    assert isinstance(fcu_b2, ForkchoiceUpdatedStep)
    assert ids(fcu_b2.expect) == ["applied", "refused"]
    # applied branch asserts the new head, refused branch asserts the old.
    assert fcu_b2.branches["applied"][-1].latest == "b2"  # type: ignore
    assert fcu_b2.branches["refused"][-1].latest == "a2"  # type: ignore


def test_annotate_does_not_widen_author_expectations() -> None:  # noqa: D103
    model = ClientModel(dag=dag_linear_with_fork())
    model.known.update({"a1": True, "a2": True, "b2": True})
    model.head = "a2"
    step = ForkchoiceUpdatedStep(
        head="b2",
        version=3,
        expect=[Outcome(id="applied", status="VALID")],
    )
    annotate_steps([step], model)
    assert ids(step.expect) == ["applied"]
    assert model.head == "b2"


def test_annotate_requires_version_map_when_unset() -> None:  # noqa: D103
    model = ClientModel(dag=dag_linear_with_fork())
    model.known["a1"] = True
    with pytest.raises(ValueError):
        annotate_steps([ForkchoiceUpdatedStep(head="a1")], model)


def test_annotate_continues_from_first_branch_state() -> None:
    """
    Steps after a branching step run after that branch; the model must carry
    the branch's effects (a nested reorg) into the continuation.
    """
    dag = ModelDag(
        parent={"a1": "genesis", "p": "a1", "q": "a1"},
        valid={"a1": True, "p": True, "q": True},
    )
    model = ClientModel(dag=dag)
    versions = {"genesis": 3, "a1": 3, "p": 3, "q": 3}
    steps: List[Step] = [
        NewPayloadStep(block="a1"),
        ForkchoiceUpdatedStep(
            head="a1",
            branches={
                "applied": [
                    NewPayloadStep(block="p"),
                    ForkchoiceUpdatedStep(head="p"),
                ]
            },
        ),
    ]
    annotate_steps(steps, model, versions)
    outer = steps[1]
    assert isinstance(outer, ForkchoiceUpdatedStep)
    tail = outer.branches["applied"][-1]
    # The outer branch's trailing head assertion reflects the nested reorg.
    assert isinstance(tail, AssertHeadStep) and tail.latest == "p"
    assert model.head == "p"


def test_annotate_marks_head_moved_for_applied_vs_noop() -> None:  # noqa: D103
    # head == finalized is the one position where both applying the update
    # and skipping it are legal, so they must be told apart by the head.
    model = ClientModel(dag=dag_linear_with_fork())
    model.known.update({"a1": True, "a2": True, "a3": True})
    model.head, model.finalized = "a3", "a1"
    steps = annotate_steps(
        [ForkchoiceUpdatedStep(head="a1", finalized="a1", version=3)], model
    )
    fcu = steps[0]
    assert isinstance(fcu, ForkchoiceUpdatedStep)
    by_id = {o.id: o for o in fcu.expect}
    assert by_id["applied"].head_moved is True
    assert by_id["noop"].head_moved is False


def test_np_hash_invalid_precedes_parent_lookup() -> None:
    """
    A payload that does not hash to its blockHash is rejected regardless of
    whether its parent is known.
    """
    dag = dag_linear_with_fork()
    dag.hash_invalid.add("b3")
    model = ClientModel(dag=dag)
    # b2, b3's parent, was never delivered.
    assert "b2" not in model.known
    outcomes = model.new_payload_outcomes("b3")
    assert ids(outcomes) == ["invalid", "invalid_block_hash"]
    assert outcomes[0].latest_valid_hash == "null"
    # Same answer once the parent is known and valid.
    model.known.update({"a1": True, "b2": True})
    assert ids(model.new_payload_outcomes("b3")) == [
        "invalid",
        "invalid_block_hash",
    ]


def test_outcome_rejects_unknown_status() -> None:
    """A misspelled status can never match an observed response."""
    with pytest.raises(ValidationError):
        Outcome(id="typo", status="Valid")


def test_outcome_rejects_unknown_error_code() -> None:
    """An error code outside the shared Engine API enum is rejected."""
    with pytest.raises(ValidationError):
        Outcome(id="typo", error_code=-1)


def test_outcome_error_code_serializes_as_decimal_string() -> None:
    """``errorCode`` round-trips through the shared int-enum serializer."""
    outcome = Outcome(id="x", error_code=EngineAPIError.TooDeepReorg)
    dumped = outcome.model_dump(by_alias=True, exclude_none=True)
    assert dumped["errorCode"] == "-38006"


def test_annotate_rejects_unmatched_new_payload_branch_key() -> None:
    """A branch key that names no newPayload outcome id is rejected."""
    model = ClientModel(dag=dag_linear_with_fork())
    steps: List[Step] = [
        NewPayloadStep(block="a1", branches={"applide": []}),
    ]
    with pytest.raises(ValueError, match="applide"):
        annotate_steps(steps, model)


def test_annotate_rejects_unmatched_forkchoice_branch_key() -> None:
    """A branch key that names no forkchoiceUpdated outcome id is rejected."""
    model = ClientModel(dag=dag_linear_with_fork())
    model.known["a1"] = True
    steps: List[Step] = [
        ForkchoiceUpdatedStep(
            head="a1", version=3, branches={"aplied": []}
        ),
    ]
    with pytest.raises(ValueError, match="aplied"):
        annotate_steps(steps, model)


def test_forkchoice_effect_follows_head_moved_not_id() -> None:
    """
    The effect follows the outcome's own constraints, never its id: an
    author-chosen id of "ok" (not "applied") still moves the head when
    headMoved says so.
    """
    model = ClientModel(dag=dag_linear_with_fork())
    model.known.update({"a1": True, "b2": True})
    model.head = "a1"
    step = ForkchoiceUpdatedStep(head="b2", version=3)
    outcome = Outcome(
        id="ok", status="VALID", latest_valid_hash="b2", head_moved=True
    )
    model.apply_forkchoice(step, outcome)
    assert model.head == "b2"


def test_forkchoice_effect_applies_reth_disputed_fork_behind_finalized() -> (
    None
):
    """
    A disputed VALID/applied outcome for a request the model would only
    classify as inconsistent (-38002) still applies, because the effect is
    derived from FCU spec step 2 directly, not from the model's own
    (narrower) classification of the request.
    """
    model = ClientModel(dag=dag_linear_with_fork())
    model.known.update({"a1": True, "a2": True, "a3": True, "b2": True})
    model.head = "a3"
    model.finalized = "a3"
    step = ForkchoiceUpdatedStep(head="b2", safe="b2", finalized="a3")
    # The model's own set at this request would be `[inconsistent]` only
    # (b2 does not share a3 as an ancestor); this simulates an author (or a
    # trusting client, per reth) overriding with a disputed VALID/applied.
    outcome = Outcome(
        id="applied", status="VALID", latest_valid_hash="b2", disputed="x"
    )
    model.apply_forkchoice(step, outcome)
    assert model.head == "b2"
