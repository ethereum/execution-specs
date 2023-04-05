"""
Base objects used to define transition forks.
"""
from typing import Type

from .base_fork import Fork


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


def transition_fork(to_fork: Fork):
    """
    Decorator to mark a class as a transition fork.
    """

    def decorator(cls) -> Type[TransitionBaseClass]:
        class NewTransitionClass(cls, TransitionBaseClass):  # type: ignore
            pass

        NewTransitionClass.transitions_to = lambda: to_fork  # type: ignore

        return NewTransitionClass

    return decorator
