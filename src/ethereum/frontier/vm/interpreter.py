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

from typing import Tuple

from ethereum.base_types import U256, Uint
from ethereum.frontier.vm.error import InvalidOpcode

from ..eth_types import Address, Log, get_account, move_ether
from . import Environment, Evm
from .instructions import Ops, op_implementation
from .runtime import get_valid_jump_destinations

PC_CHANGING_OPS = {Ops.JUMP, Ops.JUMPI}


def process_call(
    caller: Address,
    target: Address,
    data: bytes,
    value: U256,
    gas: U256,
    depth: Uint,
    env: Environment,
) -> Tuple[U256, Tuple[Log, ...]]:
    """
    Executes a call from the `caller` to the `target` in a new EVM instance.

    Parameters
    ----------
    caller :
        Account which initiated this call.

    target :
        Account whose code will be executed.

    data :
        Array of bytes provided to the code in `target`.

    value :
        Value to be transferred.

    gas :
        Gas provided for the code in `target`.

    depth :
        Number of call/contract creation environments on the call stack.

    env :
        External items required for EVM execution.

    Returns
    -------
    output : `Tuple[U256, List[eth1spec.eth_types.Log]]`
        The tuple `(gas_left, logs)`, where `gas_left` is the remaining gas
        after execution, and logs is the list of `eth1spec.eth_types.Log`
        generated during execution.
    """
    code = get_account(env.state, target).code
    valid_jump_destinations = get_valid_jump_destinations(code)

    evm = Evm(
        pc=Uint(0),
        stack=[],
        memory=bytearray(),
        code=code,
        gas_left=gas,
        current=target,
        caller=caller,
        data=data,
        value=value,
        depth=depth,
        env=env,
        valid_jump_destinations=valid_jump_destinations,
        logs=(),
        refund_counter=Uint(0),
        running=True,
    )

    if evm.value != 0:
        move_ether(evm.env.state, evm.caller, evm.current, evm.value)

    while evm.running:
        try:
            op = Ops(evm.code[evm.pc])
        except ValueError:
            raise InvalidOpcode(evm.code[evm.pc])

        op_implementation[op](evm)

        if op not in PC_CHANGING_OPS:
            evm.pc += 1

        if evm.pc >= len(evm.code):
            evm.running = False

    gas_used = gas - evm.gas_left
    refund = min(gas_used // 2, evm.refund_counter)

    return evm.gas_left + refund, evm.logs
