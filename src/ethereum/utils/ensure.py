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

from typing import Callable, Union


def ensure(
    value: bool, exception: Union[Callable[[], BaseException], BaseException]
) -> None:
    """
    Does nothing if `value` is truthy, otherwise raises the exception returned
    by `exception_class`.

    Parameters
    ----------

    value :
        Value that should be true.

    exception :
        Constructor for the exception to raise.
    """
    if value:
        return
    raise exception  # type: ignore
