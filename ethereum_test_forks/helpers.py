"""
Helper methods to resolve forks during test filling
"""
from typing import List, Optional, Set

from semver import Version

from .base_fork import BaseFork, Fork
from .forks import forks, transition
from .transition_base_fork import TransitionBaseClass


class InvalidForkError(Exception):
    """
    Invalid fork error raised when the fork specified by command-line option
    --latest-fork is not found.
    """

    def __init__(self, message):
        super().__init__(message)


def get_forks() -> List[Fork]:
    """
    Returns a list of all the fork classes implemented by
    `ethereum_test_forks` ordered chronologically by deployment.
    """
    all_forks: List[Fork] = []
    for fork_name in forks.__dict__:
        fork = forks.__dict__[fork_name]
        if not isinstance(fork, type):
            continue
        if issubclass(fork, BaseFork) and fork is not BaseFork:
            all_forks.append(fork)
    return all_forks


def get_deployed_forks() -> List[Fork]:
    """
    Returns a list of all the fork classes implemented by `ethereum_test_forks`
    that have been deployed to mainnet, chronologically ordered by deployment.
    """
    return [fork for fork in get_forks() if fork.is_deployed()]


def get_development_forks() -> List[Fork]:
    """
    Returns a list of all the fork classes implemented by `ethereum_test_forks`
    that have been not yet deployed to mainnet and are currently under
    development. The list is ordered by their planned deployment date.
    """
    return [fork for fork in get_forks() if not fork.is_deployed()]


def get_parent_fork(fork: Fork) -> Fork:
    """
    Returns the parent fork of the specified fork
    """
    return fork.__base__


def get_forks_with_solc_support(solc_version: Version) -> List[Fork]:
    """
    Returns a list of all fork classes that are supported by solc.
    """
    return [fork for fork in get_forks() if solc_version >= fork.solc_min_version()]


def get_forks_without_solc_support(solc_version: Version) -> List[Fork]:
    """
    Returns a list of all fork classes that aren't supported by solc.
    """
    return [fork for fork in get_forks() if solc_version < fork.solc_min_version()]


def get_closest_fork_with_solc_support(fork: Fork, solc_version: Version) -> Optional[Fork]:
    """
    Returns the closest fork, potentially the provided fork itself, that has
    solc support.
    """
    if fork is BaseFork:
        return None
    return (
        fork
        if solc_version >= fork.solc_min_version()
        else get_closest_fork_with_solc_support(get_parent_fork(fork), solc_version)
    )


def get_transition_forks() -> List[Fork]:
    """
    Returns all the transition forks
    """
    transition_forks: List[Fork] = []

    for fork_name in transition.__dict__:
        fork = transition.__dict__[fork_name]
        if not isinstance(fork, type):
            continue
        if issubclass(fork, TransitionBaseClass) and issubclass(fork, BaseFork):
            transition_forks.append(fork)

    return transition_forks


def get_from_until_fork_set(
    forks: Set[Fork], forks_from: Set[Fork], forks_until: Set[Fork]
) -> Set[Fork]:
    """
    Get the fork range from forks_from to forks_until.
    """
    resulting_set = set()
    for fork_from in forks_from:
        for fork_until in forks_until:
            for fork in forks:
                if fork <= fork_until and fork >= fork_from:
                    resulting_set.add(fork)
    return resulting_set


def get_forks_with_no_parents(forks: Set[Fork]) -> Set[Fork]:
    """
    Get the forks with no parents in the inheritance hierarchy.
    """
    resulting_forks: Set[Fork] = set()
    for fork in forks:
        parents = False
        for next_fork in forks - {fork}:
            if next_fork < fork:
                parents = True
                break
        if not parents:
            resulting_forks = resulting_forks | {fork}
    return resulting_forks


def get_forks_with_no_descendants(forks: Set[Fork]) -> Set[Fork]:
    """
    Get the forks with no descendants in the inheritance hierarchy.
    """
    resulting_forks: Set[Fork] = set()
    for fork in forks:
        descendants = False
        for next_fork in forks - {fork}:
            if next_fork > fork:
                descendants = True
                break
        if not descendants:
            resulting_forks = resulting_forks | {fork}
    return resulting_forks


def get_last_descendants(forks: Set[Fork], forks_from: Set[Fork]) -> Set[Fork]:
    """
    Get the last descendant of a class in the inheritance hierarchy.
    """
    resulting_forks: Set[Fork] = set()
    forks = get_forks_with_no_descendants(forks)
    for fork_from in forks_from:
        for fork in forks:
            if fork >= fork_from:
                resulting_forks = resulting_forks | {fork}
    return resulting_forks


def transition_fork_from_to(fork_from: Fork, fork_to: Fork) -> Fork | None:
    """
    Returns the transition fork that transitions to and from the specified
    forks.
    """
    for transition_fork in get_transition_forks():
        if not issubclass(transition_fork, TransitionBaseClass):
            continue
        if (
            transition_fork.transitions_to() == fork_to
            and transition_fork.transitions_from() == fork_from
        ):
            return transition_fork

    return None


def transition_fork_to(fork_to: Fork) -> List[Fork]:
    """
    Returns the transition fork that transitions to the specified fork.
    """
    transition_forks: List[Fork] = []
    for transition_fork in get_transition_forks():
        if not issubclass(transition_fork, TransitionBaseClass):
            continue
        if transition_fork.transitions_to() == fork_to:
            transition_forks.append(transition_fork)

    return transition_forks


def forks_from_until(fork_from: Fork, fork_until: Fork) -> List[Fork]:
    """
    Returns the specified fork and all forks after it until and including the
    second specified fork
    """
    prev_fork = fork_until

    forks: List[Fork] = []

    while prev_fork != BaseFork and prev_fork != fork_from:
        forks.insert(0, prev_fork)

        prev_fork = prev_fork.__base__

    if prev_fork == BaseFork:
        return []

    forks.insert(0, fork_from)

    return forks


def forks_from(fork: Fork, deployed_only: bool = True) -> List[Fork]:
    """
    Returns the specified fork and all forks after it.
    """
    if deployed_only:
        latest_fork = get_deployed_forks()[-1]
    else:
        latest_fork = get_forks()[-1]
    return forks_from_until(fork, latest_fork)
