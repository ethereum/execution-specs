"""
Ethereum Virtual Machine (EVM) Exceptions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

Exceptions which cause the EVM to halt exceptionally.
"""

from ethereum.exceptions import EthereumException


class ExceptionalHalt(EthereumException):
    """
    Indicates that the EVM has experienced an exceptional halt. This causes
    execution to immediately end with all gas being consumed.
    """


class Revert(EthereumException):
    """
    Raised by the `REVERT` opcode.

    Unlike other EVM exceptions this does not result in the consumption of all
    gas.
    """

    pass


class StackUnderflowError(ExceptionalHalt):
    """
    Occurs when a pop is executed on an empty stack.
    """

    pass


class StackOverflowError(ExceptionalHalt):
    """
    Occurs when a push is executed on a stack at max capacity.
    """

    pass


class OutOfGasError(ExceptionalHalt):
    """
    Occurs when an operation costs more than the amount of gas left in the
    frame.
    """

    pass


class InvalidOpcode(ExceptionalHalt):
    """
    Raised when an invalid opcode is encountered.
    """

    pass


class InvalidJumpDestError(ExceptionalHalt):
    """
    Occurs when the destination of a jump operation doesn't meet any of the
    following criteria:

      * The jump destination is less than the length of the code.
      * The jump destination should have the `JUMPDEST` opcode (0x5B).
      * The jump destination shouldn't be part of the data corresponding to
        `PUSH-N` opcodes.
    """


class StackDepthLimitError(ExceptionalHalt):
    """
    Raised when the message depth is greater than `1024`
    """

    pass


class WriteInStaticContext(ExceptionalHalt):
    """
    Raised when an attempt is made to modify the state while operating inside
    of a STATICCALL context.
    """

    pass


class OutOfBoundsRead(ExceptionalHalt):
    """
    Raised when an attempt was made to read data beyond the
    boundaries of the buffer.
    """

    pass


class InvalidParameter(ExceptionalHalt):
    """
    Raised when invalid parameters are passed.
    """

    pass


class InvalidContractPrefix(ExceptionalHalt):
    """
    Raised when the new contract code starts with 0xEF.
    """

    pass
