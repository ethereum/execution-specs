"""
Utility Functions For Headers
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

..contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

Headers specific utility functions used in this application.
"""
from typing import Any, Dict

from ethereum.frontier.eth_types import Header
from ethereum.utils.hexadecimal import (
    hex_to_address,
    hex_to_bloom,
    hex_to_bytes,
    hex_to_bytes8,
    hex_to_bytes32,
    hex_to_hash,
    hex_to_root,
    hex_to_u256,
    hex_to_uint,
)


def json_to_header(json_data: Dict[Any, Any]) -> Header:
    """
    Convert json data to block header.

    Parameters
    ----------
    json_data :
        The header data where the values are hexadecimals.

    Returns
    -------
    header : `Header`
        The header object obtained from the json data.
    """
    return Header(
        parent_hash=hex_to_hash(json_data["parentHash"]),
        ommers_hash=hex_to_hash(json_data["sha3Uncles"]),
        coinbase=hex_to_address(json_data["miner"]),
        state_root=hex_to_root(json_data["stateRoot"]),
        transactions_root=hex_to_root(json_data["transactionsRoot"]),
        receipt_root=hex_to_root(json_data["receiptsRoot"]),
        bloom=hex_to_bloom(json_data["logsBloom"]),
        difficulty=hex_to_uint(json_data["difficulty"]),
        number=hex_to_uint(json_data["number"]),
        gas_limit=hex_to_uint(json_data["gasLimit"]),
        gas_used=hex_to_uint(json_data["gasUsed"]),
        timestamp=hex_to_u256(json_data["timestamp"]),
        extra_data=hex_to_bytes(json_data["extraData"]),
        mix_digest=hex_to_bytes32(json_data["mixHash"]),
        nonce=hex_to_bytes8(json_data["nonce"]),
    )
