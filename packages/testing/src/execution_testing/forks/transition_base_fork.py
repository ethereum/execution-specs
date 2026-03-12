"""Base objects used to define transition forks."""

from typing import Any, Callable, ClassVar, Dict, Type

from .base_fork import BaseFork


class TransitionBaseMetaClass(type):
    """Metaclass for TransitionBaseClass."""

    def name(cls) -> str:
        """
        Return the name of the transition fork (e.g., Berlin), must be
        implemented by subclasses.
        """
        raise Exception("Not implemented")

    def transitions_to(cls) -> Type[BaseFork]:
        """
        Return fork where the transition ends.

        If the fork transitions multiple times, this function always returns
        the last fork.
        """
        raise Exception("Not implemented")

    def transitions_from(cls) -> Type[BaseFork]:
        """
        Return fork where the transition starts.

        If the fork transitions multiple times, this function always returns
        the first fork.
        """
        raise Exception("Not implemented")

    def __repr__(cls) -> str:
        """Print the name of the fork, instead of the class."""
        return cls.name()

    def _other_fork(
        cls, other: "TransitionBaseMetaClass | Type[BaseFork]"
    ) -> Type[BaseFork]:
        """Return the fork to compare against for the other operand."""
        if isinstance(other, TransitionBaseMetaClass):
            return other.transitions_to()
        return other

    def __gt__(cls, other: "TransitionBaseMetaClass | Type[BaseFork]") -> bool:
        """Compare if a fork is newer than some other fork (cls > other)."""
        return cls.transitions_to() > cls._other_fork(other)

    def __ge__(cls, other: "TransitionBaseMetaClass | Type[BaseFork]") -> bool:
        """
        Compare if a fork is newer than or equal to some other fork (cls >=
        other).
        """
        return cls.transitions_to() >= cls._other_fork(other)

    def __lt__(cls, other: "TransitionBaseMetaClass | Type[BaseFork]") -> bool:
        """Compare if a fork is older than some other fork (cls < other)."""
        return cls.transitions_to() < cls._other_fork(other)

    def __le__(cls, other: "TransitionBaseMetaClass | Type[BaseFork]") -> bool:
        """
        Compare if a fork is older than or equal to some other fork (cls <=
        other).
        """
        return cls.transitions_to() <= cls._other_fork(other)


class TransitionBaseClass(metaclass=TransitionBaseMetaClass):
    """Base class for transition forks."""

    is_transition_fork: ClassVar[bool] = True
    at_block: ClassVar[int] = 0
    at_timestamp: ClassVar[int] = 0
    _ignore: ClassVar[bool] = False

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

    @classmethod
    def ruleset(cls) -> Dict[str, int]:
        """
        Return the ruleset used for fork configuration.
        """
        raise Exception("Not implemented")


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

        if to_fork._fork_by_timestamp:
            assert at_block == 0, f"Invalid block for {transition_name}"
            assert at_timestamp > 0, f"Invalid timestamp for {transition_name}"
        else:
            assert at_block > 0, f"Invalid block for {transition_name}"
            assert at_timestamp == 0, (
                f"Invalid timestamp for {transition_name}"
            )

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

            @classmethod
            def ruleset(cls) -> Dict[str, int]:
                """
                Return the ruleset used for fork configuration.
                """
                return to_fork.ruleset(
                    value=at_timestamp
                    if to_fork._fork_by_timestamp
                    else at_block
                )

        NewTransitionClass.__name__ = transition_name
        NewTransitionClass.at_block = at_block
        NewTransitionClass.at_timestamp = at_timestamp

        return NewTransitionClass

    return decorator
