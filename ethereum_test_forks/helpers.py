"""
Helper methods to resolve forks during test filling
"""
from typing import List

from .base_fork import BaseFork, Fork
from .forks import forks, upcoming
from .transition_base_fork import TransitionBaseClass


class LatestForkResolver:
    """
    Latest fork
    """

    def __init__(self):
        latest_fork_name = list(forks.__dict__.keys())[-1]
        self.latest_fork = forks.__dict__[latest_fork_name]


latest_fork_resolver = LatestForkResolver()


def set_latest_fork(fork: Fork):
    """
    Sets the latest fork
    """
    latest_fork_resolver.latest_fork = fork


def set_latest_fork_by_name(fork_name: str):
    """
    Sets the latest fork by name
    """
    if fork_name in forks.__dict__:
        set_latest_fork(forks.__dict__[fork_name])
    elif fork_name in upcoming.__dict__:
        set_latest_fork(upcoming.__dict__[fork_name])
    else:
        raise Exception(f'fork "{fork_name}" not found')


def get_parent_fork(fork: Fork) -> Fork:
    """
    Returns the parent fork of the specified fork
    """
    return fork.__base__


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


def forks_from(fork: Fork) -> List[Fork]:
    """
    Returns the specified fork and all forks after it
    """
    return forks_from_until(fork, latest_fork_resolver.latest_fork)


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


def fork_only(fork: Fork) -> List[Fork]:
    """
    Returns the specified fork only if it's a fork that precedes the latest
    """
    if issubclass(fork, TransitionBaseClass):
        if fork.transitions_to() is not None:
            if is_fork(
                latest_fork_resolver.latest_fork, fork.transitions_to()
            ):
                return [fork]
        return []
    if is_fork(latest_fork_resolver.latest_fork, fork):
        return [fork]
    return []
