"""
Hardforks
^^^^^^^^^

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

Lists of hardfork blocks for Ethereum and its various testnets.
"""

from ethereum import (
    berlin,
    byzantium,
    constantinople,
    dao_fork,
    frontier,
    homestead,
    istanbul,
    muir_glacier,
    spurious_dragon,
    tangerine_whistle,
)

mainnet = {
    1: frontier,
    1150000: homestead,
    1920000: dao_fork,
    2463000: tangerine_whistle,
    2675000: spurious_dragon,
    4370000: byzantium,
    7280000: constantinople,
    9069000: istanbul,
    9200000: muir_glacier,
    12244000: berlin,
}

goerli = {
    1: constantinople,
    1561651: istanbul,
    4460644: berlin,
    #    5062605: london,
}
