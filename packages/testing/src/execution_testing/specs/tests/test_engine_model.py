"""Unit tests for the Engine API reference model used by reorg tests."""

from dataclasses import replace
from typing import Dict, Iterable, List

import pytest

from execution_testing.base_types import Address, Hash
from execution_testing.exceptions import EngineAPIError
from execution_testing.fixtures.blockchain import PayloadAttributes
from execution_testing.fixtures.reorg import (
    GENESIS_LABEL,
    AssertCanonicalStep,
    AssertHeadStep,
    AssertStateStep,
    ForkchoiceUpdatedStep,
    GetPayloadStep,
    NewPayloadStep,
    Outcome,
    Step,
)
from execution_testing.forks import Cancun

from ..engine_model import (
    ClientModel,
    DagBlock,
    ModelDag,
    Validity,
    annotate_steps,
)


def attributes() -> PayloadAttributes:
    """Build-request attributes; filling defaults the rest in place."""
    return PayloadAttributes(
        timestamp=0, prev_randao=Hash(0), suggested_fee_recipient=Address(0)
    )


def add_block(
    dag: ModelDag,
    label: str,
    parent: str,
    valid: bool = True,
    hash_invalid: bool = False,
) -> None:
    """Add a Cancun block 12 s after ``parent``."""
    dag.blocks[label] = DagBlock(
        parent=parent,
        timestamp=dag.blocks[parent].timestamp + 12,
        gas_limit=30_000_000,
        slot=0,
        fcu_version=3,
        new_payload_version=3,
        valid=valid,
        hash_invalid=hash_invalid,
    )


def make_dag(
    parents: Dict[str, str],
    invalid: Iterable[str] = (),
    hash_invalid: Iterable[str] = (),
) -> ModelDag:
    """A Cancun DAG from ``label -> parent``, parents listed first."""
    dag = ModelDag(
        blocks={
            GENESIS_LABEL: DagBlock(
                parent=None,
                timestamp=0,
                gas_limit=30_000_000,
                slot=0,
                fcu_version=3,
            )
        }
    )
    for label, parent in parents.items():
        add_block(
            dag,
            label,
            parent,
            valid=label not in invalid,
            hash_invalid=label in hash_invalid,
        )
    return dag


def dag_linear_with_fork(hash_invalid: Iterable[str] = ()) -> ModelDag:
    r"""
    Genesis <- a1 <- a2 <- a3.
                 \\- b2 <- b3      (b3 execution-invalid).
    """
    return make_dag(
        {"a1": "genesis", "a2": "a1", "a3": "a2", "b2": "a1", "b3": "b2"},
        invalid={"b3"},
        hash_invalid=hash_invalid,
    )


def ids(outcomes: List[Outcome]) -> List[str]:
    """Outcome ids."""
    return [o.id for o in outcomes]


def test_ancestry() -> None:  # noqa: D103
    dag = dag_linear_with_fork()
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
    model.known.update({"a1": Validity.VALID, "a2": Validity.VALID})
    model.head = "a2"
    assert ids(model.new_payload_outcomes("b2")) == ["valid", "accepted"]


def test_new_payload_invalid_block() -> None:  # noqa: D103
    model = ClientModel(dag=dag_linear_with_fork())
    model.known.update({"a1": Validity.VALID, "b2": Validity.VALID})
    model.head = "b2"
    outcomes = model.new_payload_outcomes("b3")
    assert ids(outcomes) == ["invalid"]
    assert outcomes[0].latest_valid_hash == "b2"
    assert outcomes[0].validation_error == "required"


def test_new_payload_child_of_known_invalid() -> None:  # noqa: D103
    dag = dag_linear_with_fork()
    add_block(dag, "b4", "b3")
    model = ClientModel(dag=dag)
    model.known.update(
        {"a1": Validity.VALID, "b2": Validity.VALID, "b3": Validity.INVALID}
    )
    outcomes = model.new_payload_outcomes("b4")
    assert ids(outcomes) == ["invalid", "syncing"]
    assert outcomes[0].latest_valid_hash == "b2"
    # A grandchild of the invalid block is also INVALID-or-SYNCING, never
    # SYNCING-only: clients with a bad-block cache answer INVALID.
    model.apply_new_payload("b4", outcomes[0])
    add_block(dag, "b5", "b4")
    outcomes = model.new_payload_outcomes("b5")
    assert ids(outcomes) == ["invalid", "syncing"]
    assert outcomes[0].latest_valid_hash == "b2"


def test_fcu_unknown_head_is_syncing() -> None:  # noqa: D103
    model = ClientModel(dag=dag_linear_with_fork())
    step = ForkchoiceUpdatedStep(head="a1")
    assert ids(model.forkchoice_outcomes(step)) == ["syncing"]


def test_fcu_extend_head_is_applied_only() -> None:  # noqa: D103
    model = ClientModel(dag=dag_linear_with_fork())
    model.known["a1"] = Validity.VALID
    step = ForkchoiceUpdatedStep(head="a1")
    outcomes = model.forkchoice_outcomes(step)
    assert ids(outcomes) == ["applied"]
    model.apply_forkchoice(step, outcomes[0])
    assert model.head == "a1"


def test_fcu_side_chain_reorg_applied_or_refused() -> None:  # noqa: D103
    model = ClientModel(dag=dag_linear_with_fork())
    model.known.update(
        {"a1": Validity.VALID, "a2": Validity.VALID, "b2": Validity.VALID}
    )
    model.head = "a2"
    outcomes = model.forkchoice_outcomes(ForkchoiceUpdatedStep(head="b2"))
    assert ids(outcomes) == ["applied", "refused"]
    assert outcomes[1].error_code == EngineAPIError.TooDeepReorg


def test_fcu_rewind_to_canonical_ancestor_above_finalized() -> None:  # noqa: D103
    model = ClientModel(dag=dag_linear_with_fork())
    model.known.update(
        {"a1": Validity.VALID, "a2": Validity.VALID, "a3": Validity.VALID}
    )
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
    model.known.update(
        {
            "a1": Validity.VALID,
            "a2": Validity.VALID,
            "a3": Validity.VALID,
            "b2": Validity.VALID,
        }
    )
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
    model.known.update(
        {"a1": Validity.VALID, "a2": Validity.VALID, "a3": Validity.VALID}
    )
    model.head = "a3"
    model.finalized = "a2"
    outcomes = model.forkchoice_outcomes(
        ForkchoiceUpdatedStep(head="a1", finalized="a2")
    )
    assert ids(outcomes) == ["noop"]
    assert outcomes[0].status == "VALID"


def test_fcu_head_equals_finalized_is_disputed() -> None:  # noqa: D103
    model = ClientModel(dag=dag_linear_with_fork())
    model.known.update(
        {"a1": Validity.VALID, "a2": Validity.VALID, "a3": Validity.VALID}
    )
    model.head = "a3"
    model.finalized = "a2"
    outcomes = model.forkchoice_outcomes(
        ForkchoiceUpdatedStep(head="a2", finalized="a2")
    )
    assert ids(outcomes) == ["applied", "noop"]
    assert outcomes[1].disputed is not None


def test_fcu_inconsistent_finalized_is_error() -> None:  # noqa: D103
    model = ClientModel(dag=dag_linear_with_fork())
    model.known.update(
        {"a1": Validity.VALID, "a2": Validity.VALID, "b2": Validity.VALID}
    )
    model.head = "a2"
    outcomes = model.forkchoice_outcomes(
        ForkchoiceUpdatedStep(head="a2", finalized="b2")
    )
    assert ids(outcomes) == ["inconsistent"]
    assert outcomes[0].error_code == EngineAPIError.InvalidForkchoiceState


def test_fcu_invalid_head() -> None:  # noqa: D103
    model = ClientModel(dag=dag_linear_with_fork())
    model.known.update(
        {"a1": Validity.VALID, "b2": Validity.VALID, "b3": Validity.INVALID}
    )
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
    annotate_steps(steps, model, Cancun)

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
    model.known.update(
        {"a1": Validity.VALID, "a2": Validity.VALID, "b2": Validity.VALID}
    )
    model.head = "a2"
    step = ForkchoiceUpdatedStep(
        head="b2",
        version=3,
        expect=[Outcome(id="applied", status="VALID")],
    )
    annotate_steps([step], model, Cancun)
    assert ids(step.expect) == ["applied"]
    assert model.head == "b2"


def test_annotate_checks_each_forkchoice_before_its_own_branch() -> None:
    """Each FCU's head check precedes its branch's own steps."""
    dag = make_dag({"a1": "genesis", "p": "a1", "q": "a1"})
    model = ClientModel(dag=dag)
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
    annotate_steps(steps, model, Cancun)
    outer = steps[1]
    assert isinstance(outer, ForkchoiceUpdatedStep)
    outer_branch = outer.branches["applied"]
    head_check = outer_branch[0]
    assert isinstance(head_check, AssertHeadStep)
    assert head_check.latest == "a1"
    nested_fcu = outer_branch[-1]
    assert isinstance(nested_fcu, ForkchoiceUpdatedStep)
    nested_check = nested_fcu.branches["applied"][0]
    assert isinstance(nested_check, AssertHeadStep)
    assert nested_check.latest == "p"
    assert model.head == "p"


def test_annotate_marks_head_moved_for_applied_vs_noop() -> None:  # noqa: D103
    # head == finalized is the one position where both applying the update
    # and skipping it are legal, so they must be told apart by the head.
    model = ClientModel(dag=dag_linear_with_fork())
    model.known.update(
        {"a1": Validity.VALID, "a2": Validity.VALID, "a3": Validity.VALID}
    )
    model.head, model.finalized = "a3", "a1"
    steps = annotate_steps(
        [
            ForkchoiceUpdatedStep(
                head="a1",
                finalized="a1",
                version=3,
                payload_attributes=attributes(),
            )
        ],
        model,
        Cancun,
    )
    fcu = steps[0]
    assert isinstance(fcu, ForkchoiceUpdatedStep)
    by_id = {o.id: o for o in fcu.expect}
    assert by_id["applied"].head_moved is True
    assert by_id["applied"].payload_id == "nonNull"
    assert by_id["noop"].head_moved is False
    assert by_id["noop"].payload_id == "null"


@pytest.mark.parametrize(
    "timestamp,version,match",
    [
        pytest.param(12, 3, "not after the head's 12", id="same_timestamp"),
        pytest.param(24, 2, "take forkchoiceUpdatedV3, not V2", id="version"),
    ],
)
def test_annotate_refuses_to_generate_attribute_errors(
    timestamp: int, version: int, match: str
) -> None:
    """
    A build request the spec rejects (-38003, -38005) gets no generated
    successful build: the author sets its expected error.
    """
    model = ClientModel(dag=dag_linear_with_fork())
    model.known["a1"] = Validity.VALID
    step = ForkchoiceUpdatedStep(
        head="a1",
        version=version,
        payload_attributes=PayloadAttributes(
            timestamp=timestamp,
            prev_randao=Hash(0),
            suggested_fee_recipient=Address(0),
        ),
    )
    with pytest.raises(ValueError, match=match):
        annotate_steps([step], model, Cancun)


@pytest.mark.parametrize(
    "version,outcome_id", [(1, "invalid_block_hash"), (2, "invalid")]
)
def test_np_hash_invalid_precedes_parent_lookup(
    version: int, outcome_id: str
) -> None:
    """
    A payload that does not hash to its blockHash is rejected regardless of
    whether its parent is known: INVALID_BLOCK_HASH from newPayloadV1,
    INVALID from V2 on, both with a null latestValidHash.
    """
    dag = dag_linear_with_fork(hash_invalid={"b3"})
    dag.blocks["b3"] = replace(dag.blocks["b3"], new_payload_version=version)
    model = ClientModel(dag=dag)
    # b2, b3's parent, was never delivered.
    assert "b2" not in model.known
    outcomes = model.new_payload_outcomes("b3")
    assert ids(outcomes) == [outcome_id]
    assert outcomes[0].latest_valid_hash == "null"
    # Same answer once the parent is known and valid.
    model.known.update({"a1": Validity.VALID, "b2": Validity.VALID})
    assert ids(model.new_payload_outcomes("b3")) == [outcome_id]


def test_fcu_to_hash_mismatched_payload_allows_syncing() -> None:
    """No block is stored under a rejected payload's hash: SYNCING is legal."""
    dag = dag_linear_with_fork(hash_invalid={"b3"})
    model = ClientModel(dag=dag)
    model.known.update({"a1": Validity.VALID, "b2": Validity.VALID})
    model.apply_new_payload("b3", Outcome(id="invalid", status="INVALID"))
    outcomes = model.forkchoice_outcomes(ForkchoiceUpdatedStep(head="b3"))
    assert ids(outcomes) == ["invalid", "syncing"]


def test_annotate_rejects_unmatched_new_payload_branch_key() -> None:
    """A branch key that names no newPayload outcome id is rejected."""
    model = ClientModel(dag=dag_linear_with_fork())
    steps: List[Step] = [
        NewPayloadStep(block="a1", branches={"valid_typo": []}),
    ]
    with pytest.raises(ValueError, match="valid_typo"):
        annotate_steps(steps, model, Cancun)


def test_annotate_rejects_unmatched_forkchoice_branch_key() -> None:
    """A branch key that names no forkchoiceUpdated outcome id is rejected."""
    model = ClientModel(dag=dag_linear_with_fork())
    model.known["a1"] = Validity.VALID
    steps: List[Step] = [
        ForkchoiceUpdatedStep(
            head="a1", version=3, branches={"applied_typo": []}
        ),
    ]
    with pytest.raises(ValueError, match="applied_typo"):
        annotate_steps(steps, model, Cancun)


def test_annotate_rejects_duplicate_outcome_ids() -> None:
    """
    Two outcomes sharing an id in one step's expect are rejected: both
    would modify the same branch, leaving it with contradictory assertions.
    """
    model = ClientModel(dag=dag_linear_with_fork())
    model.known["a1"] = Validity.VALID
    steps: List[Step] = [
        ForkchoiceUpdatedStep(
            head="a1",
            version=3,
            expect=[
                Outcome(id="either", status="VALID", latest_valid_hash="a1"),
                Outcome(id="either", error_code=EngineAPIError.TooDeepReorg),
            ],
        ),
    ]
    with pytest.raises(ValueError, match="either"):
        annotate_steps(steps, model, Cancun)


def test_forkchoice_effect_follows_head_moved_not_id() -> None:
    """An outcome moves the head when headMoved says so, whatever its id."""
    model = ClientModel(dag=dag_linear_with_fork())
    model.known.update({"a1": Validity.VALID, "b2": Validity.VALID})
    model.head = "a1"
    step = ForkchoiceUpdatedStep(head="b2", version=3)
    outcome = Outcome(
        id="ok", status="VALID", latest_valid_hash="b2", head_moved=True
    )
    model.apply_forkchoice(step, outcome)
    assert model.head == "b2"


def test_forkchoice_effect_applies_authored_valid_outcome() -> None:
    """An authored VALID outcome applies even where the model says -38002."""
    model = ClientModel(dag=dag_linear_with_fork())
    model.known.update(
        {
            "a1": Validity.VALID,
            "a2": Validity.VALID,
            "a3": Validity.VALID,
            "b2": Validity.VALID,
        }
    )
    model.head = "a3"
    model.finalized = "a3"
    step = ForkchoiceUpdatedStep(head="b2", safe="b2", finalized="a3")
    outcome = Outcome(
        id="applied", status="VALID", latest_valid_hash="b2", disputed="x"
    )
    model.apply_forkchoice(step, outcome)
    assert model.head == "b2"


@pytest.mark.parametrize(
    "outcome_id,error_code",
    [
        ("bad_attributes", EngineAPIError.InvalidPayloadAttributes),
        ("invalid_timestamp", EngineAPIError.InvalidPayloadAttributes),
        ("unsupported_fork", EngineAPIError.UnsupportedFork),
    ],
)
def test_invalid_payload_attributes_still_applies_forkchoice(
    outcome_id: str, error_code: EngineAPIError
) -> None:
    """
    A -38003/-38005 branch asserts the updated head, whatever the outcome
    id.
    """
    model = ClientModel(dag=dag_linear_with_fork())
    model.known["a1"] = Validity.VALID
    step = ForkchoiceUpdatedStep(
        head="a1",
        version=3,
        payload_attributes=attributes(),
        expect=[Outcome(id=outcome_id, error_code=error_code)],
    )
    annotate_steps([step], model, Cancun)
    head_check = step.branches[outcome_id][0]
    assert isinstance(head_check, AssertHeadStep)
    assert head_check.latest == "a1"


@pytest.mark.parametrize(
    "version,attributes",
    [(2, attributes()), (3, None)],
    ids=["v2_with_attributes", "v3_without_attributes"],
)
def test_unordered_unsupported_fork_is_rejected(
    version: int, attributes: PayloadAttributes | None
) -> None:
    """
    A -38005 the spec does not order against the update leaves the head
    unknown, so filling rejects it.
    """
    model = ClientModel(dag=dag_linear_with_fork())
    model.known["a1"] = Validity.VALID
    step = ForkchoiceUpdatedStep(
        head="a1",
        version=version,
        payload_attributes=attributes,
        expect=[
            Outcome(
                id="unsupported", error_code=EngineAPIError.UnsupportedFork
            )
        ],
    )
    with pytest.raises(ValueError, match="head after it is unknown"):
        annotate_steps([step], model, Cancun)


def test_any_error_on_a_build_request_is_rejected() -> None:
    """AnyError cannot tell -38003, which still applies, from other errors."""
    model = ClientModel(dag=dag_linear_with_fork())
    model.known["a1"] = Validity.VALID
    step = ForkchoiceUpdatedStep(
        head="a1",
        version=3,
        payload_attributes=attributes(),
        expect=[Outcome(id="error", any_error=True)],
    )
    with pytest.raises(ValueError, match="set errorCode"):
        annotate_steps([step], model, Cancun)


BUILT = Outcome(id="built", status="VALID", payload_id="nonNull")


@pytest.mark.parametrize(
    "outcomes,parent,match",
    [
        pytest.param(
            [BUILT],
            "genesis",
            "on 'a1', not 'genesis'",
            id="build_on_another_parent",
        ),
        pytest.param(
            [Outcome(id="none", status="VALID", payload_id="null")],
            "a1",
            "no build in progress",
            id="no_build_in_progress",
        ),
        pytest.param(
            [
                BUILT,
                Outcome(
                    id="unsupported", error_code=EngineAPIError.UnsupportedFork
                ),
            ],
            "a1",
            "different payload builds",
            id="outcomes_leave_different_builds",
        ),
    ],
)
def test_get_payload_rejects_a_build_it_cannot_retrieve(
    outcomes: List[Outcome], parent: str, match: str
) -> None:
    """
    ``getPayload`` must retrieve the build in progress, on its parent, and
    one that does not depend on which outcome occurred.
    """
    model = ClientModel(dag=dag_linear_with_fork())
    model.known["a1"] = Validity.VALID
    steps: List[Step] = [
        ForkchoiceUpdatedStep(
            head="a1",
            version=3,
            payload_attributes=attributes(),
            expect=[o.model_copy() for o in outcomes],
        ),
        GetPayloadStep(bind="p", parent=parent, version=3),
    ]
    with pytest.raises(ValueError, match=match):
        annotate_steps(steps, model, Cancun)


def test_annotate_single_outcome_branch_updates_known_map() -> None:
    """Later steps see blocks learned inside a single-outcome branch."""
    dag = make_dag({"a1": "genesis", "p": "a1"})
    model = ClientModel(dag=dag)
    steps: List[Step] = [
        NewPayloadStep(
            block="a1", branches={"valid": [NewPayloadStep(block="p")]}
        ),
        ForkchoiceUpdatedStep(head="p"),
    ]
    annotate_steps(steps, model, Cancun)
    fcu = steps[1]
    assert isinstance(fcu, ForkchoiceUpdatedStep)
    assert ids(fcu.expect) == ["applied"]


def test_accepted_does_not_establish_validity() -> None:
    """ACCEPTED leaves a later FCU to an invalid block able to fail."""
    dag = make_dag({"a1": "genesis", "bad": "a1"}, invalid={"bad"})
    model = ClientModel(dag=dag)
    model.known["a1"] = Validity.VALID
    model.apply_new_payload("bad", Outcome(id="accepted", status="ACCEPTED"))
    assert model.known["bad"] == Validity.RECEIVED
    outcomes = model.forkchoice_outcomes(ForkchoiceUpdatedStep(head="bad"))
    assert ids(outcomes) == ["invalid", "syncing"]
    assert outcomes[0].latest_valid_hash == "a1"


def test_received_ground_truth_valid_acts_like_valid() -> None:
    """A truly valid ACCEPTED block has a VALID block's outcomes."""
    dag = make_dag({"a1": "genesis", "b1": "a1", "b2": "b1"})
    model = ClientModel(dag=dag)
    model.known["a1"] = Validity.VALID
    model.apply_new_payload("b1", Outcome(id="accepted", status="ACCEPTED"))
    assert model.known["b1"] == Validity.RECEIVED
    fcu_outcomes = model.forkchoice_outcomes(ForkchoiceUpdatedStep(head="b1"))
    assert ids(fcu_outcomes) == ["applied"]
    np_outcomes = model.new_payload_outcomes("b2")
    assert ids(np_outcomes) == ["valid", "accepted"]


def test_annotate_rejects_diverging_multi_outcome_continuation() -> None:
    """A later step cannot follow outcomes that leave different heads."""
    dag = make_dag({"a1": "genesis", "p": "a1"})
    model = ClientModel(dag=dag)
    model.known["a1"] = Validity.VALID
    steps: List[Step] = [
        ForkchoiceUpdatedStep(
            head="p",
            version=3,
            expect=[
                Outcome(id="applied", status="VALID", latest_valid_hash="p"),
                Outcome(id="refused", error_code=EngineAPIError.TooDeepReorg),
            ],
        ),
        AssertHeadStep(latest="p"),
    ]
    with pytest.raises(ValueError, match="different forkchoice states"):
        annotate_steps(steps, model, Cancun)


def test_annotate_allows_agreeing_multi_outcome_continuation() -> None:
    """VALID and ACCEPTED leave a truly valid block in one effective state."""
    dag = make_dag({"a1": "genesis", "b2": "a1"})
    model = ClientModel(dag=dag)
    model.known["a1"] = Validity.VALID
    steps: List[Step] = [
        NewPayloadStep(block="b2"),
        ForkchoiceUpdatedStep(head="b2", version=3),
    ]
    annotate_steps(steps, model, Cancun)
    np_step, fcu = steps
    assert isinstance(np_step, NewPayloadStep)
    assert isinstance(fcu, ForkchoiceUpdatedStep)
    assert ids(np_step.expect) == ["valid", "accepted"]
    assert ids(fcu.expect) == ["applied"]


@pytest.mark.parametrize(
    "order",
    [
        pytest.param(["syncing", "valid"], id="syncing_first"),
        pytest.param(["valid", "syncing"], id="valid_first"),
    ],
)
def test_annotate_rejects_outcomes_of_a_diverged_block(
    order: List[str],
) -> None:
    """Generated outcomes may not depend on a block left ambiguous."""
    outcomes = {
        "syncing": Outcome(id="syncing", status="SYNCING"),
        "valid": Outcome(id="valid", status="VALID", latest_valid_hash="a1"),
    }
    model = ClientModel(dag=make_dag({"a1": "genesis"}))
    steps: List[Step] = [
        NewPayloadStep(block="a1", expect=[outcomes[o] for o in order]),
        ForkchoiceUpdatedStep(head="a1", version=3),
    ]
    with pytest.raises(ValueError, match="'a1' in different states"):
        annotate_steps(steps, model, Cancun)


def test_annotate_redelivery_resolves_a_diverged_block() -> None:
    """A definite outcome for a diverged block settles its state."""
    model = ClientModel(dag=make_dag({"a1": "genesis"}))
    steps: List[Step] = [
        NewPayloadStep(
            block="a1",
            expect=[
                Outcome(id="syncing", status="SYNCING"),
                Outcome(id="valid", status="VALID", latest_valid_hash="a1"),
            ],
        ),
        NewPayloadStep(block="a1"),
        ForkchoiceUpdatedStep(head="a1", version=3),
    ]
    annotate_steps(steps, model, Cancun)
    fcu = steps[2]
    assert isinstance(fcu, ForkchoiceUpdatedStep)
    assert ids(fcu.expect) == ["applied"]


def test_annotate_rejects_divergence_used_by_enclosing_continuation() -> None:
    """A step after the enclosing branch counts as a later step."""
    dag = make_dag({"a1": "genesis", "p": "a1"})
    model = ClientModel(dag=dag)
    model.known["a1"] = Validity.VALID
    steps: List[Step] = [
        ForkchoiceUpdatedStep(
            head="a1",
            version=3,
            branches={
                "applied": [
                    ForkchoiceUpdatedStep(
                        head="p",
                        version=3,
                        expect=[
                            Outcome(
                                id="applied",
                                status="VALID",
                                latest_valid_hash="p",
                            ),
                            Outcome(
                                id="refused",
                                error_code=EngineAPIError.TooDeepReorg,
                            ),
                        ],
                    ),
                ]
            },
        ),
        AssertHeadStep(latest="p"),
    ]
    with pytest.raises(ValueError, match="different forkchoice states"):
        annotate_steps(steps, model, Cancun)


@pytest.mark.parametrize(
    "assertion,match",
    [
        pytest.param(
            AssertHeadStep(latest="b2"), "assertHead latest", id="head"
        ),
        pytest.param(
            AssertCanonicalStep(blocks={2: "b2"}),
            "assertCanonical 2",
            id="canonical_sibling",
        ),
        pytest.param(
            AssertCanonicalStep(blocks={3: "a3"}),
            "assertCanonical 3",
            id="canonical_above_head",
        ),
        pytest.param(
            AssertStateStep(at="b2", accounts={}),
            "not canonical",
            id="state_at_sibling",
        ),
    ],
)
def test_annotate_rejects_assertions_the_model_contradicts(
    assertion: Step, match: str
) -> None:
    """An authored assertion no conformant client can pass fails filling."""
    model = ClientModel(dag=dag_linear_with_fork())
    model.known.update({"a1": Validity.VALID, "a2": Validity.VALID})
    model.head = "a2"
    annotate_steps(
        [AssertCanonicalStep(blocks={2: "a2", 3: None})], model, Cancun
    )
    with pytest.raises(ValueError, match=match):
        annotate_steps([assertion], model, Cancun)


def test_new_payload_resent_valid_block_is_valid_only() -> None:
    """A fully validated payload cannot be answered ACCEPTED again."""
    model = ClientModel(dag=dag_linear_with_fork())
    model.known.update(
        {"a1": Validity.VALID, "a2": Validity.VALID, "b2": Validity.VALID}
    )
    model.head = "a2"
    assert ids(model.new_payload_outcomes("b2")) == ["valid"]


def test_generated_outcomes_refuse_a_connectable_syncing_block() -> None:
    """
    Once the parent of a payload answered SYNCING is known, a client may
    have connected the payload, so a generated FCU to it is refused.
    """
    model = ClientModel(dag=dag_linear_with_fork())
    model.apply_new_payload("a2", Outcome(id="syncing", status="SYNCING"))
    assert ids(
        model.forkchoice_outcomes(ForkchoiceUpdatedStep(head="a2"))
    ) == ["syncing"]
    model.apply_new_payload("a1", Outcome(id="valid", status="VALID"))
    with pytest.raises(ValueError, match="may have connected it"):
        model.forkchoice_outcomes(ForkchoiceUpdatedStep(head="a2"))


def test_annotate_defaults_version_of_a_zero_head() -> None:
    """An FCU to the zero hash takes the current head's method version."""
    model = ClientModel(dag=dag_linear_with_fork())
    step = ForkchoiceUpdatedStep(head="zero")
    annotate_steps([step], model, Cancun)
    assert step.version == 3
    assert ids(step.expect) == ["syncing"]
