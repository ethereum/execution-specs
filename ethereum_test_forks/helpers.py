"""
Helper methods to resolve forks during test filling
"""
from typing import List

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


def get_deployed_forks():
    """
    Returns a list of all the fork classes implemented by `ethereum_test_forks`
    that have been deployed to mainnet, chronologically ordered by deployment.
    """
    return [fork for fork in get_forks() if fork.is_deployed()]


def get_development_forks():
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


def all_transition_forks() -> List[Fork]:
    """
    Returns all the transition forks
    """
    transition_forks: List[Fork] = []

    for fork_name in transition.__dict__:
        fork = transition.__dict__[fork_name]
        if not isinstance(fork, type):
            continue
        if issubclass(fork, TransitionBaseClass) and issubclass(
            fork, BaseFork
        ):
            transition_forks.append(fork)

    return transition_forks


def transition_fork_from_to(fork_from: Fork, fork_to: Fork) -> Fork | None:
    """
    Returns the transition fork that transitions to and from the specified
    forks.
    """
    for transition_fork in all_transition_forks():
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
    for transition_fork in all_transition_forks():
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


def is_fork(fork: Fork, which: Fork) -> bool:
    """
    Returns `True` if `fork` is `which` or beyond, `False otherwise.
    """
    prev_fork = fork

    while prev_fork != BaseFork:
        if prev_fork == which:
            return True

        prev_fork = prev_fork.__base__

    return False
