"""
Test Fixture
^^^^^^^^^^^^

Cross-client compatible Ethereum test fixture.
"""

from typing import List, Mapping
from ethereum.crypto import Hash32
from ethereum.frontier.eth_types import Address, Account, Block

from .fork import Fork


class Fixture:
    """
    Cross-client compatible Ethereum test fixture.
    """

    blocks: List[Block]
    genesis: Block
    head: Hash32
    fork: Fork
    preState: Mapping[Address, Account]
    postState: Mapping[Address, Account]
    sealEngine: str
