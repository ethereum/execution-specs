"""
Ethereum Network Upgrades
^^^^^^^^^^^^^^^^^^^^^^^^^

List of Ethereum network upgrades.
"""

from enum import Enum


class Fork(Enum):
    """
    List of Ethereum network upgrades.
    """

    FRONTIER = "frontier"
    HOMESTEAD = "homestead"
    DAO_FORK = "dao-fork"
    TANGERINE_WHISTLE = "tangerine-whistle"
    SPURIOUS_DRAGON = "spurious-dragon"
    BYZANTIUM = "byzantium"
    CONSTANTINOPLE = "constantinople"
    PETERSBURG = "petersburg"
    ISTANBUL = "istanbul"
    MUIR_GLACIER = "muir-glacier"
    BERLIN = "berlin"
    LONDON = "london"
