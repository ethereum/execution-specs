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

    @classmethod
    def transitions_from(cls) -> Fork:
        """
        Returns the fork where the transition starts.
        """
        raise Exception("Not implemented")


def transition_fork(to_fork: Fork):
    """
    Decorator to mark a class as a transition fork.
    """

    def decorator(cls) -> Type[TransitionBaseClass]:
        transition_name = cls.__name__

        class NewTransitionClass(cls, TransitionBaseClass):  # type: ignore
            @classmethod
            def name(cls) -> str:
                """
                Returns the name of the transition fork.
                """
                return transition_name

        NewTransitionClass.transitions_to = lambda: to_fork  # type: ignore
        NewTransitionClass.transitions_from = lambda: cls.__bases__[0]  # type: ignore

        return NewTransitionClass

    return decorator
