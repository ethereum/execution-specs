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


class InvalidJumpDestError(Exception):
    """
    Occurs when the destination of a jump operation doesn't meet any of the
    following criteria:

      * The jump destination is less than the length of the code.
      * The jump destination should have the `JUMPDEST` opcode (0x5B).
      * The jump destination shouldn't be part of the data corresponding to
        `PUSH-N` opcodes.
    """


class StackDepthLimitError(Exception):
    """
    Raised when the message depth is greater than `1024`
    """

    pass


class InsufficientFunds(Exception):
    """
    Raised when an account has insufficient funds to transfer the
    requested value.
    """

    pass


class WriteProtection(Exception):
    """
    Raised when an attempt is made to modify the state while operating inside
    of a STATICCALL context.
    """

    pass


class OutOfBoundsRead(Exception):
    """
    Raised when an attempt was made to read data beyond the
    boundaries of the buffer.
    """

    pass
