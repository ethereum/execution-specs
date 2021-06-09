"""
EVM Runtime Errors
---
"""


class StackUnderflowError(Exception):
    """
    Occurs when a pop is executed on an empty stack.
    """

    pass


class StackOverflowError(Exception):
    """
    Occurs when a push is executed on a stack at max capacity.
    """

    pass


class OutOfGasError(Exception):
    """
    Occurs when an operation costs more than the amount of gas left in the
    frame.
    """

    pass
