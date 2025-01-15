"""Ethereum test fixture format definitions."""

from typing import Dict

from .base import BaseFixture, FixtureFormat
from .blockchain import BlockchainEngineFixture, BlockchainFixture, BlockchainFixtureCommon
from .collector import FixtureCollector, TestInfo
from .eof import Fixture as EOFFixture
from .state import StateFixture
from .transaction import Fixture as TransactionFixture
from .verify import FixtureVerifier

FIXTURE_FORMATS: Dict[str, FixtureFormat] = {
    f.fixture_format_name: f  # type: ignore
    for f in [
        BlockchainFixture,
        BlockchainEngineFixture,
        EOFFixture,
        StateFixture,
        TransactionFixture,
    ]
}
__all__ = [
    "FIXTURE_FORMATS",
    "BaseFixture",
    "BlockchainFixture",
    "BlockchainFixtureCommon",
    "BlockchainEngineFixture",
    "EOFFixture",
    "FixtureCollector",
    "FixtureFormat",
    "FixtureVerifier",
    "StateFixture",
    "TestInfo",
    "TransactionFixture",
]
