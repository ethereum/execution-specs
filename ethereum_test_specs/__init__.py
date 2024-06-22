"""
Test spec definitions and utilities.
"""

from typing import List, Type

from .base import BaseTest, TestSpec
from .blockchain import BlockchainTest, BlockchainTestFiller, BlockchainTestSpec
from .eof import (
    EOFStateTest,
    EOFStateTestFiller,
    EOFStateTestSpec,
    EOFTest,
    EOFTestFiller,
    EOFTestSpec,
)
from .state import StateTest, StateTestFiller, StateTestOnly, StateTestSpec

SPEC_TYPES: List[Type[BaseTest]] = [
    BlockchainTest,
    StateTest,
    StateTestOnly,
    EOFTest,
    EOFStateTest,
]


__all__ = (
    "SPEC_TYPES",
    "BaseTest",
    "BlockchainTest",
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
    "StateTestOnly",
    "StateTestSpec",
    "TestSpec",
)
