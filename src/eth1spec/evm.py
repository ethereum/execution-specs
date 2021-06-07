"""
Ethereum Virtual Machine (EVM)
------------------------------

The abstract computer which runs the code stored in an
`eth1spec.eth_types.Account`.
"""

from dataclasses import dataclass
from typing import List, Tuple

from .eth_types import (
    U256,
    Address,
    Bytes32,
    EMPTY_ACCOUNT,
    Hash32,
    Log,
    State,
    Uint,
)


ops = {
    "ADD": b"\x01",
    "PUSH1": b"\x60",
    "SSTORE": b"\x55",
}


VERY_LOW = 3

gas_schedule = {
    "ADD": VERY_LOW,
    "PUSH1": VERY_LOW,
    "SSTORE": 20000,
}


@dataclass
class Environment:
    """
    Items external to the virtual machine itself, provided by the environment.
    """

    caller: Address
    block_hashes: List[Hash32]
    origin: Address
    coinbase: Address
    number: Uint
    gas_limit: Uint
    gas_price: Uint
    time: Uint
    difficulty: Uint
    state: State


@dataclass
class Evm:
    """The internal state of the virtual machine."""

    pc: Uint
    stack: List[U256]
    memory: bytes
    gas_left: Uint
    current: Address
    caller: Address
    data: bytes
    value: Uint
    depth: Uint
    env: Environment


def process_call(
    caller: Address,
    target: Address,
    data: bytes,
    value: Uint,
    gas: Uint,
    depth: Uint,
    env: Environment,
) -> Tuple[Uint, List[Log]]:
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

    value : `eth1spec.number.Uint`
        Value to be transferred.

    gas : `eth1spec.number.Uint`
        Gas provided for the code in `target`.

    depth : `eth1spec.number.Uint`
        Number of call/contract creation environments on the call stack.

    env : `Environment`
        External items required for EVM execution.

    Returns
    -------
    output : `Tuple[Uint, List[eth1spec.eth_types.Log]]`
        The tuple `(gas_left, logs)`, where `gas_left` is the remaining gas
        after execution, and logs is the list of `eth1spec.eth_types.Log`
        generated during execution.
    """
    evm = Evm(
        pc=Uint(0),
        stack=[],
        memory=b"",
        gas_left=gas,
        current=target,
        caller=caller,
        data=data,
        value=value,
        depth=depth,
        env=env,
    )

    account = evm.env.state.get(evm.current, EMPTY_ACCOUNT)
    code = account.code

    while evm.pc < len(code):
        op = bytes([code[evm.pc]])

        if op == ops["ADD"]:
            evm.gas_left -= gas_schedule["ADD"]
            x = evm.stack.pop()
            y = evm.stack.pop()
            evm.stack.append(x + y)
        elif op == ops["SSTORE"]:
            evm.gas_left -= gas_schedule["SSTORE"]
            k = evm.stack.pop()
            v = evm.stack.pop()
            account.storage[Bytes32(k)] = Bytes32(v)
        elif op == ops["PUSH1"]:
            evm.gas_left -= gas_schedule["PUSH1"]
            evm.stack.append(U256(code[evm.pc + 1]))
            evm.pc += 1

        evm.pc += 1

    return evm.gas_left, []
