"""
Ethereum Logs Bloom.

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

This module defines the logs bloom of a block and of a receipt. Earlier forks
computed a 256 byte [Bloom filter] over the address and topics of every log,
so that blocks and receipts could be eliminated quickly when searching for a
particular log. [EIP-7668] removed the filter, leaving a logs bloom that is
always empty.

[Bloom filter]: https://en.wikipedia.org/wiki/Bloom_filter
[EIP-7668]: https://eips.ethereum.org/EIPS/eip-7668
"""

from typing import Tuple

from .blocks import Log
from .fork_types import Bloom


def logs_bloom(logs: Tuple[Log, ...]) -> Bloom:
    """
    Obtain the logs bloom from a list of log entries.

    Parameters
    ----------
    logs :
        List of logs for which the logs bloom is to be obtained.

    Returns
    -------
    logs_bloom : `Bloom`
        The empty logs bloom.

    """
    del logs

    return Bloom(b"")
