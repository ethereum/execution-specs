"""
Instruction Encoding (Opcodes)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

Machine readable representations of EVM instructions, and a mapping to their
implementations.
"""

from .instructions import add, push1, sstore

ADD = 0x01
PUSH1 = 0x60
SSTORE = 0x55

op_implementation = {
    ADD: add,
    SSTORE: sstore,
    PUSH1: push1,
}
