from dataclasses import dataclass
from typing import List, Tuple

from .eth_types import U256, Address, Hash32, Log, State, Uint

ADD = "\x01"


@dataclass
class Environment:
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


def proccess_call(
    caller: Address,
    target: Address,
    data: bytes,
    value: Uint,
    gas: Uint,
    depth: Uint,
    env: Environment,
) -> Tuple[Uint, List[Log]]:
    evm = Evm(
        pc=0,
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

    # code = get_code(evm.env.state, evm.current)

    return [], evm.gas_left

    #  while(pc < len(code)):
    #      op = code[pc]

    #      switch(op):
    #          case ADD:
    #              x = evm.stack.pop()
    #              y = evm.stack.pop()
    #              evm.stack.append(x + y)
