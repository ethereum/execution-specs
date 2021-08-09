"""
Utility Functions For Addresses
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

..contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

Address specific utility functions used in this application.
"""
from typing import Union

from ethereum.base_types import U256, Uint
from ethereum.frontier.eth_types import Address


def to_address(data: Union[Uint, U256]) -> Address:
    """
    Convert a Uint or U256 value to a valid address (20 bytes).

    Parameters
    ----------
    data :
        The string to be converted to bytes.

    Returns
    -------
    address : `Address`
        The obtained address.
    """
    return data.to_be_bytes32()[-20:]
