"""Base objects used to define transition forks."""

from typing import Any, Callable, ClassVar, List, Type

from .base_fork import BaseFork

ALWAYS_TRANSITIONED_BLOCK_NUMBER = 10_000
ALWAYS_TRANSITIONED_BLOCK_TIMESTAMP = 10_000_000


class TransitionBaseMetaClass(type):
    """Metaclass for TransitionBaseClass."""

    def name(cls) -> str:
        """
        Return the name of the transition fork (e.g., Berlin), must be
        implemented by subclasses.
        """
        raise Exception("Not implemented")

    def __repr__(cls) -> str:
        """Print the name of the fork, instead of the class."""
        return cls.name()

    def __gt__(cls, other: "TransitionBaseMetaClass | Type[BaseFork]") -> bool:
        """Compare if a fork is newer than some other fork (cls > other)."""
        return False

    def __ge__(cls, other: "TransitionBaseMetaClass | Type[BaseFork]") -> bool:
        """
        Compare if a fork is newer than or equal to some other fork (cls >=
        other).
        """
        return False

    def __lt__(cls, other: "TransitionBaseMetaClass | Type[BaseFork]") -> bool:
        """Compare if a fork is older than some other fork (cls < other)."""
        # "Older" means other is a subclass of cls, but not the same.
        return False

    def __le__(cls, other: "TransitionBaseMetaClass | Type[BaseFork]") -> bool:
        """
        Compare if a fork is older than or equal to some other fork (cls <=
        other).
        """
        return False


class TransitionBaseClass(metaclass=TransitionBaseMetaClass):
    """Base class for transition forks."""

    is_transition_fork: ClassVar[bool] = True
    _ignore: ClassVar[bool] = False

    @classmethod
    def transitions_to(cls) -> Type[BaseFork]:
        """
        Return fork where the transition ends.

        If the fork transitions multiple times, this function always returns
        the last fork.
        """
        raise Exception("Not implemented")

    @classmethod
    def transitions_from(cls) -> Type[BaseFork]:
        """
        Return fork where the transition starts.

        If the fork transitions multiple times, this function always returns
        the first fork.
        """
        raise Exception("Not implemented")

    @classmethod
    def fork_at(
        cls, *, block_number: int = 0, timestamp: int = 0
    ) -> Type[BaseFork]:
        """
        Return fork at the given block number and timestamp.
        """
        del block_number, timestamp
        raise Exception("Not implemented")

    @classmethod
    def ignore(cls) -> bool:
        """Return whether the fork should be ignored during test generation."""
        return cls._ignore

    @classmethod
    def is_deployed(cls) -> bool:
        """
        Return whether the fork has been deployed to mainnet, or not.

        Must be overridden and return False for forks that are still under
        development.
        """
        return cls.transitions_to().is_deployed()


def base_fork_abstract_methods() -> List[str]:
    """
    Return list of all abstract methods that must be implemented by a fork.
    """
    return list(BaseFork.__abstractmethods__)


def transition_fork(
    to_fork: Type[BaseFork],
    from_fork: Type[BaseFork],
    at_block: int = 0,
    at_timestamp: int = 0,
    ignore: bool = False,
) -> Callable[[Type], Type[TransitionBaseClass]]:
    """Mark a class as a transition fork."""

    def decorator(cls: Type[Any]) -> Type[TransitionBaseClass]:
        transition_name = cls.__name__

        class NewTransitionClass(
            cls,
            TransitionBaseClass,
        ):
            _ignore = ignore

            @classmethod
            def transitions_to(cls) -> Type[BaseFork]:
                return to_fork

            @classmethod
            def transitions_from(cls) -> Type[BaseFork]:
                return from_fork

            @classmethod
            def fork_at(
                cls, *, block_number: int = 0, timestamp: int = 0
            ) -> Type[BaseFork]:
                return (
                    to_fork
                    if block_number >= at_block and timestamp >= at_timestamp
                    else from_fork
                )

            @classmethod
            def name(cls) -> str:
                """Return name of the transition fork."""
                return transition_name

        return NewTransitionClass

    return decorator
