"""
Test spec definitions and utilities.
"""
from typing import List, Type

from .base.base_test import BaseFixture, BaseTest, TestSpec, verify_post_alloc
from .blockchain.blockchain_test import BlockchainTest, BlockchainTestFiller, BlockchainTestSpec
from .fixture_collector import FixtureCollector, TestInfo
from .state.state_test import StateTest, StateTestFiller, StateTestSpec

SPEC_TYPES: List[Type[BaseTest]] = [BlockchainTest, StateTest]

__all__ = (
    "SPEC_TYPES",
    "BaseFixture",
    "BaseTest",
    "BlockchainTest",
    "BlockchainTestFiller",
    "BlockchainTestSpec",
    "FixtureCollector",
    "StateTest",
    "StateTestFiller",
    "StateTestSpec",
    "TestInfo",
    "TestSpec",
    "verify_post_alloc",
)
