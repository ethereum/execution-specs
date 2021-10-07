"""
Ensure (Assertion) Utilities
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

Functions that simplify checking assertions and raising exceptions.
"""

from typing import Callable


class EnsureError(Exception):
    """
    Represents a failed check.
    """


def ensure(
    value: bool, exception_class: Callable[[], Exception] = EnsureError
) -> None:
    """
    Does nothing if `value` is truthy, otherwise raises the exception returned
    by `exception_class`.

    Parameters
    ----------

    value :
        Value that should be true.

    exception_class :
        Constructor for the exception to raise.
    """
    if value:
        return
    raise exception_class()
