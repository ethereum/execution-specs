"""
Decorators for the fork methods.
"""


def prefer_transition_to_method(method):
    """
    Decorator to mark a base method that must always call the `fork_to` implementation when
    transitioning.
    """
    method.__prefer_transition_to_method__ = True
    return method
