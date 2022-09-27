"""
Testnet Configuration
^^^^^^^^^^^^^^^^^^^^^

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

This module contains code and configuration information enabling the
specification to be used with Ethereum testnets.

This module does not form part of the Ethereum specification.
"""

from ethereum import berlin, constantinople, istanbul, london

goerli = {
    0: constantinople,
    1561651: istanbul,
    4460644: berlin,
    5062605: london,
}
