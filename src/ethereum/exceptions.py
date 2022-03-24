"""
Exceptions
^^^^^^^^^^

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

The Ethereum specification exception classes.
"""


class EthereumException(Exception):
    """
    The base class from which all exceptions thrown by the specification during
    normal operation derive.
    """


class InvalidBlock(EthereumException):
    """
    Thrown when a block being processed is found to be invalid.
    """


class RLPDecodingError(EthereumException):
    """
    Indicates that RLP decoding failed.
    """


class RLPEncodingError(EthereumException):
    """
    Indicates that RLP encoding failed.
    """
