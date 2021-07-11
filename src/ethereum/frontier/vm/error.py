"""
Ethereum Virtual Machine (EVM) Errors
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

Errors which cause the EVM to halt exceptionally.
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


class InvalidOpcode(Exception):
    """
    Raised when an invalid opcode is encountered.
    """

    pass
