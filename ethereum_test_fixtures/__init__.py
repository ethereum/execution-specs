"""
Ethereum test fixture format definitions.
"""

from typing import List, Type

from .base import BaseFixture
from .blockchain import EngineFixture as BlockchainEngineFixture
from .blockchain import Fixture as BlockchainFixture
from .blockchain import FixtureCommon as BlockchainFixtureCommon
from .collector import FixtureCollector, TestInfo
from .eof import Fixture as EOFFixture
from .formats import FixtureFormats
from .state import Fixture as StateFixture
from .verify import FixtureVerifier

FIXTURE_TYPES: List[Type[BaseFixture]] = [
    BlockchainFixture,
    BlockchainEngineFixture,
    EOFFixture,
    StateFixture,
]
__all__ = [
    "FIXTURE_TYPES",
    "BaseFixture",
    "BlockchainFixture",
    "BlockchainFixtureCommon",
    "BlockchainEngineFixture",
    "EOFFixture",
    "FixtureCollector",
    "FixtureFormats",
    "FixtureVerifier",
    "StateFixture",
    "TestInfo",
]
