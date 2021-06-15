"""
Ethereum Virtual Machine (EVM) Interpreter
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

A straightforward interpreter that executes EVM code.
"""

from typing import List, Tuple

from ..base_types import U256, Uint
from ..eth_types import Address, Log
from . import Environment, Evm
from .ops import op_implementation


def process_call(
    caller: Address,
    target: Address,
    data: bytes,
    value: U256,
    gas: U256,
    depth: Uint,
    env: Environment,
) -> Tuple[U256, List[Log]]:
    """
    Executes a call from the `caller` to the `target` in a new EVM instance.

    Parameters
    ----------
    caller : `eth1spec.eth_types.Address`
        Account which initiated this call.

    target : `eth1spec.eth_types.Address`
        Account whose code will be executed.

    data : `bytes`
        Array of bytes provided to the code in `target`.

    value : `eth1spec.base_types.Uint`
        Value to be transferred.

    gas : `eth1spec.base_types.Uint`
        Gas provided for the code in `target`.

    depth : `eth1spec.base_types.Uint`
        Number of call/contract creation environments on the call stack.

    env : `Environment`
        External items required for EVM execution.

    Returns
    -------
    output : `Tuple[U256, List[eth1spec.eth_types.Log]]`
        The tuple `(gas_left, logs)`, where `gas_left` is the remaining gas
        after execution, and logs is the list of `eth1spec.eth_types.Log`
        generated during execution.
    """
    evm = Evm(
        pc=Uint(0),
        stack=[],
        memory=b"",
        code=env.state[target].code,
        gas_left=gas,
        current=target,
        caller=caller,
        data=data,
        value=value,
        depth=depth,
        env=env,
    )

    logs: List[Log] = []

    if evm.value != 0:
        evm.env.state[evm.caller].balance -= evm.value
        evm.env.state[evm.current].balance += evm.value

    while evm.pc < len(evm.code):
        op = evm.code[evm.pc]
        op_implementation[op](evm)
        evm.pc += 1

    return evm.gas_left, logs
