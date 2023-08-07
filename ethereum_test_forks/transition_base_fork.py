"""
Base objects used to define transition forks.
"""
from typing import List, Type

from .base_fork import BaseFork, Fork

ALWAYS_TRANSITIONED_BLOCK_NUMBER = 10_000
ALWAYS_TRANSITIONED_BLOCK_TIMESTAMP = 10_000_000


class TransitionBaseClass:
    """
    Base class for transition forks.
    """

    @classmethod
    def transitions_to(cls) -> Fork:
        """
        Returns the fork where the transition ends.
        """
        raise Exception("Not implemented")

    @classmethod
    def transitions_from(cls) -> Fork:
        """
        Returns the fork where the transition starts.
        """
        raise Exception("Not implemented")


def base_fork_abstract_methods() -> List[str]:
    """
    Returns a list of all abstract methods that must be implemented by a fork.
    """
    return list(getattr(BaseFork, "__abstractmethods__"))


def transition_fork(to_fork: Fork, at_block: int = 0, at_timestamp: int = 0):
    """
    Decorator to mark a class as a transition fork.
    """

    def decorator(cls) -> Type[TransitionBaseClass]:
        transition_name = cls.__name__
        from_fork = cls.__bases__[0]
        assert issubclass(from_fork, BaseFork)

        class NewTransitionClass(cls, TransitionBaseClass, BaseFork):  # type: ignore
            pass

        NewTransitionClass.name = lambda: transition_name  # type: ignore

        def make_transition_method(base_method, from_fork_method, to_fork_method):
            def transition_method(
                cls,
                block_number: int = ALWAYS_TRANSITIONED_BLOCK_NUMBER,
                timestamp: int = ALWAYS_TRANSITIONED_BLOCK_TIMESTAMP,
            ):
                if getattr(base_method, "__prefer_transition_to_method__", False):
                    return to_fork_method(block_number, timestamp)
                return (
                    to_fork_method(block_number, timestamp)
                    if block_number >= at_block and timestamp >= at_timestamp
                    else from_fork_method(block_number, timestamp)
                )

            return classmethod(transition_method)

        for method_name in base_fork_abstract_methods():
            setattr(
                NewTransitionClass,
                method_name,
                make_transition_method(
                    getattr(BaseFork, method_name),
                    getattr(from_fork, method_name),
                    getattr(to_fork, method_name),
                ),
            )

        NewTransitionClass.transitions_to = lambda: to_fork  # type: ignore
        NewTransitionClass.transitions_from = lambda: from_fork  # type: ignore

        return NewTransitionClass

    return decorator
