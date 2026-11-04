"""Test the forks of unscheduled features."""

from typing import List, Type

from ethereum_spec_tools.unscheduled import Feature
from ethereum_spec_tools.utils import resolve_fork

from ..base_fork import BaseFork
from ..forks import unscheduled
from ..helpers import (
    forks_from,
    get_development_forks,
    get_forks,
    get_selected_fork_set,
    get_transition_forks,
    get_unscheduled_forks,
)


def feature_forks() -> List[Type[BaseFork]]:
    """Return every feature fork."""
    return get_unscheduled_forks()


def test_feature_forks_build_on_spec_base() -> None:
    """
    Every feature fork builds on the same fork as its specs: the feature's
    pinned `base`, or else the newest fork.
    """
    assert unscheduled.LatestFork is get_forks()[-1], (
        "move `LatestFork` in `forks/forks/unscheduled.py` to the newest fork"
    )
    features = {
        feature.title_case_name: feature for feature in Feature.discover()
    }
    assert feature_forks()
    for fork in feature_forks():
        feature = features[fork.name()]
        parent = fork.parent()
        assert parent is not None
        if feature.base is None:
            assert parent is unscheduled.LatestFork
        else:
            base = resolve_fork(parent.transition_tool_name())
            assert base.short_name == feature.base
        assert not fork.is_deployed()


def test_feature_forks_need_explicit_selection() -> None:
    """
    Filling up to the newest fork leaves out every feature fork, which only
    runs when selected with `--fork`.
    """
    up_to_latest = get_selected_fork_set(
        single_fork=set(),
        forks_from=set(),
        forks_until={unscheduled.LatestFork},
    )
    assert unscheduled.LatestFork in up_to_latest
    for fork in feature_forks():
        assert fork not in up_to_latest
        assert all(f.transitions_to() is not fork for f in up_to_latest)
        selected = get_selected_fork_set(
            single_fork={fork}, forks_from=set(), forks_until=set()
        )
        assert fork in selected
        assert all(f.transitions_to() is fork for f in selected)


def test_feature_forks_have_transitions() -> None:
    """
    Every feature fork has a transition fork from the fork it builds on,
    which `--fork` selects along with it.
    """
    for fork in feature_forks():
        transitions = [
            transition
            for transition in get_transition_forks()
            if transition.transitions_to() is fork
        ]
        assert len(transitions) == 1
        (transition,) = transitions
        assert transition.transitions_from() is fork.parent()
        selected = get_selected_fork_set(
            single_fork={fork}, forks_from=set(), forks_until=set()
        )
        assert transition in selected


def test_feature_forks_stay_out_of_fork_order() -> None:
    """
    Feature forks are not part of the chronological fork list, so nothing
    that walks it (development forks, `forks_from`, checklists, docs) picks
    them up.
    """
    for fork in feature_forks():
        parent = fork.parent()
        assert parent is not None
        assert fork not in get_forks()
        assert fork not in get_development_forks()
        assert fork not in forks_from(parent, deployed_only=False)
