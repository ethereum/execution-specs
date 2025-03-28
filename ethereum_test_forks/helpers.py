"""Helper methods to resolve forks during test filling."""

import re
from typing import Any, List, Optional, Set

from pydantic import BaseModel, ConfigDict, ValidatorFunctionWrapHandler, model_validator
from semver import Version

from .base_fork import BaseFork, Fork
from .forks import forks, transition
from .transition_base_fork import TransitionBaseClass


class InvalidForkError(Exception):
    """Invalid fork error raised when the fork specified is not found or incompatible."""

    def __init__(self, message):
        """Initialize the InvalidForkError exception."""
        super().__init__(message)


all_forks: List[Fork] = []
for fork_name in forks.__dict__:
    fork = forks.__dict__[fork_name]
    if not isinstance(fork, type):
        continue
    if issubclass(fork, BaseFork) and fork is not BaseFork:
        all_forks.append(fork)


def get_forks() -> List[Fork]:
    """
    Return list of all the fork classes implemented by
    `ethereum_test_forks` ordered chronologically by deployment.
    """
    return all_forks


def get_deployed_forks() -> List[Fork]:
    """
    Return list of all the fork classes implemented by `ethereum_test_forks`
    that have been deployed to mainnet, chronologically ordered by deployment.
    """
    return [fork for fork in get_forks() if fork.is_deployed()]


def get_development_forks() -> List[Fork]:
    """
    Return list of all the fork classes implemented by `ethereum_test_forks`
    that have been not yet deployed to mainnet and are currently under
    development. The list is ordered by their planned deployment date.
    """
    return [fork for fork in get_forks() if not fork.is_deployed()]


def get_parent_fork(fork: Fork) -> Fork:
    """Return parent fork of the specified fork."""
    parent_fork = fork.__base__
    if not parent_fork:
        raise InvalidForkError(f"Parent fork of {fork} not found.")
    return parent_fork


def get_forks_with_solc_support(solc_version: Version) -> List[Fork]:
    """Return list of all fork classes that are supported by solc."""
    return [fork for fork in get_forks() if solc_version >= fork.solc_min_version()]


def get_forks_without_solc_support(solc_version: Version) -> List[Fork]:
    """Return list of all fork classes that aren't supported by solc."""
    return [fork for fork in get_forks() if solc_version < fork.solc_min_version()]


def get_closest_fork_with_solc_support(fork: Fork, solc_version: Version) -> Optional[Fork]:
    """
    Return closest fork, potentially the provided fork itself, that has
    solc support.
    """
    if fork is BaseFork:
        return None
    return (
        fork
        if solc_version >= fork.solc_min_version()
        else get_closest_fork_with_solc_support(get_parent_fork(fork), solc_version)
    )


def get_transition_forks() -> Set[Fork]:
    """Return all the transition forks."""
    transition_forks: Set[Fork] = set()

    for fork_name in transition.__dict__:
        fork = transition.__dict__[fork_name]
        if not isinstance(fork, type):
            continue
        if issubclass(fork, TransitionBaseClass) and issubclass(fork, BaseFork):
            transition_forks.add(fork)

    return transition_forks


def get_transition_fork_predecessor(transition_fork: Fork) -> Fork:
    """Return the fork from which the transition fork transitions."""
    if not issubclass(transition_fork, TransitionBaseClass):
        raise InvalidForkError(f"{transition_fork} is not a transition fork.")
    return transition_fork.transitions_from()


def get_transition_fork_successor(transition_fork: Fork) -> Fork:
    """Return the fork to which the transition fork transitions."""
    if not issubclass(transition_fork, TransitionBaseClass):
        raise InvalidForkError(f"{transition_fork} is not a transition fork.")
    return transition_fork.transitions_to()


def get_from_until_fork_set(
    forks: Set[Fork], forks_from: Set[Fork], forks_until: Set[Fork]
) -> Set[Fork]:
    """Get fork range from forks_from to forks_until."""
    resulting_set = set()
    for fork_from in forks_from:
        for fork_until in forks_until:
            for fork in forks:
                if fork <= fork_until and fork >= fork_from:
                    resulting_set.add(fork)
    return resulting_set


def get_forks_with_no_parents(forks: Set[Fork]) -> Set[Fork]:
    """Get forks with no parents in the inheritance hierarchy."""
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
    """Get forks with no descendants in the inheritance hierarchy."""
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
    """Get last descendant of a class in the inheritance hierarchy."""
    resulting_forks: Set[Fork] = set()
    forks = get_forks_with_no_descendants(forks)
    for fork_from in forks_from:
        for fork in forks:
            if fork >= fork_from:
                resulting_forks = resulting_forks | {fork}
    return resulting_forks


def transition_fork_from_to(fork_from: Fork, fork_to: Fork) -> Fork | None:
    """
    Return transition fork that transitions to and from the specified
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


def transition_fork_to(fork_to: Fork) -> Set[Fork]:
    """Return transition fork that transitions to the specified fork."""
    transition_forks: Set[Fork] = set()
    for transition_fork in get_transition_forks():
        if not issubclass(transition_fork, TransitionBaseClass):
            continue
        if transition_fork.transitions_to() == fork_to:
            transition_forks.add(transition_fork)

    return transition_forks


def forks_from_until(fork_from: Fork, fork_until: Fork) -> List[Fork]:
    """
    Return specified fork and all forks after it until and including the
    second specified fork.
    """
    prev_fork = fork_until

    forks: List[Fork] = []

    while prev_fork != BaseFork and prev_fork != fork_from:
        forks.insert(0, prev_fork)

        prev_fork = get_parent_fork(prev_fork)

    if prev_fork == BaseFork:
        return []

    forks.insert(0, fork_from)

    return forks


def forks_from(fork: Fork, deployed_only: bool = True) -> List[Fork]:
    """Return specified fork and all forks after it."""
    if deployed_only:
        latest_fork = get_deployed_forks()[-1]
    else:
        latest_fork = get_forks()[-1]
    return forks_from_until(fork, latest_fork)


def get_relative_fork_markers(fork_identifier: Fork | str, strict_mode: bool = True) -> list[str]:
    """
    Return a list of marker names for a given fork.

    For a base fork (e.g. `Shanghai`), return [ `Shanghai` ].
    For a transition fork (e.g. `ShanghaiToCancunAtTime15k` which transitions to `Cancun`),
    return [ `ShanghaiToCancunAtTime15k`, `Cancun` ].

    If `strict_mode` is set to `True`, raise an `InvalidForkError` if the fork is not found,
    otherwise, simply return the provided (str) `fork_identifier` (this is required to run
    `consume` with forks that are unknown to EEST).
    """
    all_forks = set(get_forks()) | set(get_transition_forks())
    if isinstance(fork_identifier, str):
        fork_class = None
        for candidate in all_forks:
            if candidate.name() == fork_identifier:
                fork_class = candidate
                break
        if strict_mode and fork_class is None:
            raise InvalidForkError(f"Unknown fork: {fork_identifier}")
        return [fork_identifier]
    else:
        fork_class = fork_identifier

    if issubclass(fork_class, TransitionBaseClass):
        return [fork_class.name(), fork_class.transitions_to().name()]
    else:
        return [fork_class.name()]


def get_fork_by_name(fork_name: str) -> Fork | None:
    """Get a fork by name."""
    for fork in get_forks():
        if fork.name() == fork_name:
            return fork
    return None


class ForkRangeDescriptor(BaseModel):
    """Fork descriptor parsed from string normally contained in ethereum/tests fillers."""

    greater_equal: Fork | None = None
    less_than: Fork | None = None
    model_config = ConfigDict(frozen=True)

    def fork_in_range(self, fork: Fork) -> bool:
        """Return whether the given fork is within range."""
        if self.greater_equal is not None and fork < self.greater_equal:
            return False
        if self.less_than is not None and fork >= self.less_than:
            return False
        return True

    @model_validator(mode="wrap")
    @classmethod
    def validate_fork_range_descriptor(cls, v: Any, handler: ValidatorFunctionWrapHandler):
        """
        Validate the fork range descriptor from a string.

        Examples:
        - ">=Osaka" validates to {greater_equal=Osaka, less_than=None}
        - ">=Prague<Osaka" validates to {greater_equal=Prague, less_than=Osaka}

        """
        if isinstance(v, str):
            # Decompose the string into its parts
            descriptor_string = re.sub(r"\s+", "", v.strip())
            v = {}
            if m := re.search(r">=(\w+)", descriptor_string):
                fork: Fork | None = get_fork_by_name(m.group(1))
                if fork is None:
                    raise Exception(f"Unable to parse fork name: {m.group(1)}")
                v["greater_equal"] = fork
                descriptor_string = re.sub(r">=(\w+)", "", descriptor_string)
            if m := re.search(r"<(\w+)", descriptor_string):
                fork = get_fork_by_name(m.group(1))
                if fork is None:
                    raise Exception(f"Unable to parse fork name: {m.group(1)}")
                v["less_than"] = fork
                descriptor_string = re.sub(r"<(\w+)", "", descriptor_string)
            if descriptor_string:
                raise Exception(
                    "Unable to completely parse fork range descriptor. "
                    + f'Remaining string: "{descriptor_string}"'
                )
        return handler(v)
