"""
Utility Functions For Blocks
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

..contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

Blocks specific utility functions used in this application.
"""
from typing import Any, Dict, Tuple

from ethereum.frontier.eth_types import Block, Header
from ethereum.utils.header import json_to_header
from ethereum.utils.transaction import json_to_transactions


def json_to_block(
    block_json_data: Dict[Any, Any], ommers: Tuple[Header, ...]
) -> Block:
    """
    Convert json data to a block object with the help of ommer objects.

    Parameters
    ----------
    block_json_data :
        The block json data where the values are hexadecimals, which is used
        to derive the header and the transactions.
    ommers:
        The ommer headers required to form the current block object.

    Returns
    -------
    header : `Header`
        The header object obtained from the json data.
    """
    header = json_to_header(block_json_data)
    transactions = json_to_transactions(block_json_data)

    return Block(
        header=header,
        transactions=transactions,
        ommers=ommers,
    )
