from typing import List

from .error import StackOverflowError, StackUnderflowError
from ..eth_types import U256


def pop(stack: List[U256]) -> U256:
    if len(stack) == 0:
        raise StackUnderflowError

    return stack.pop()


def push(stack: List[U256], el: U256) -> None:
    if len(stack) == 1024:
        raise StackOverflowError

    return stack.append(el)
