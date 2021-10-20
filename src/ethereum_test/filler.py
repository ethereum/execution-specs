from dataclasses import dataclass
from typing import Callable, List, Mapping
from ethereum.frontier.eth_types import Address, Account

from .types import Environment, Fixture, Transaction


@dataclass
class StateTest():
    env: Environment
    pre: Mapping[Address, Account]
    post: Mapping[Address, Account]
    txs: List[Transaction]


def test_from(fork: str) -> Callable[[Callable[[], StateTest]], Fixture]:
    def decorator(func: Callable[[], StateTest]) -> Fixture:
        return Fixture()
    return decorator


def test_only(fork: str) -> Callable[[Callable[[], StateTest]], Fixture]:
    def decorator(func: Callable[[], StateTest]) -> Fixture:
        return Fixture()
    return decorator
