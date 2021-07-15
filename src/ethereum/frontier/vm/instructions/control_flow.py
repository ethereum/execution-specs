"""
Ethereum Virtual Machine (EVM) Control Flow Instructions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

Implementations of the EVM control flow instructions.
"""

from .. import Evm


def stop(evm: Evm) -> None:
    """
    Stop further execution of EVM code.

    Parameters
    ----------
    evm :
        The current EVM frame.
    """
    evm.running = False
