"""Test spec definitions and utilities."""

from typing import List, Type

from .base import BaseTest, TestSpec
from .base_static import BaseStaticTest
from .blockchain import (
    BlockchainTest,
    BlockchainTestFiller,
    BlockchainTestSpec,
)
from .eof import (
    EOFStateTest,
    EOFStateTestFiller,
    EOFStateTestSpec,
    EOFTest,
    EOFTestFiller,
    EOFTestSpec,
)
from .state import StateTest, StateTestFiller, StateTestSpec
from .transaction import TransactionTest, TransactionTestFiller, TransactionTestSpec

SPEC_TYPES: List[Type[BaseTest]] = [
    BlockchainTest,
    EOFStateTest,
    EOFTest,
    StateTest,
    TransactionTest,
]


__all__ = (
    "SPEC_TYPES",
    "BaseStaticTest",
    "BaseTest",
    "BlockchainTest",
    "BlockchainTestEngineFiller",
    "BlockchainTestEngineSpec",
    "BlockchainTestFiller",
    "BlockchainTestSpec",
    "EOFStateTest",
    "EOFStateTestFiller",
    "EOFStateTestSpec",
    "EOFTest",
    "EOFTestFiller",
    "EOFTestSpec",
    "StateTest",
    "StateTestFiller",
    "StateTestSpec",
    "TestSpec",
    "TransactionTest",
    "TransactionTestFiller",
    "TransactionTestSpec",
)
