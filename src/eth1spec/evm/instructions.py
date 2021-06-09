from . import Evm, Environment
from .stack import pop, push
from .gas import GAS_VERY_LOW
from ..eth_types import U256


def add(evm: Evm) -> None:
    evm.gas_left -= GAS_VERY_LOW

    x = pop(evm.stack)
    y = pop(evm.stack)

    val = x + y

    push(evm.stack, val)


def sstore(evm: Evm) -> None:
    evm.gas_left -= 20000

    k = pop(evm.stack)
    v = pop(evm.stack)

    evm.env.state[evm.current].storage[k.to_bytes(32, "big")] = v.to_bytes(
        (2 ** v.bit_length() // 8) or 1, "big"
    )


def push1(evm: Evm) -> None:
    evm.gas_left -= GAS_VERY_LOW
    push(evm.stack, U256(evm.code[evm.pc + 1]))
    evm.pc += 1
