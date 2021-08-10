"""
Frontier Utilities Json
^^^^^^^^^^^^^^^^^^^^^^^

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

Json specific utilities used in this frontier version of specification.
"""
from typing import Any, Dict, Tuple

from ethereum.frontier.eth_types import Block, Header, Transaction
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


def json_to_transactions(json_data: Dict[Any, Any]) -> Tuple[Transaction, ...]:
    """
    Convert json data to tuple of transaction objects.

    Parameters
    ----------
    json_data :
        The transactions data where the values are hexadecimals.

    Returns
    -------
    transactions : `Tuple[Transaction, ...]`
        The transaction objects obtained from the json data.
    """
    transactions = []
    for transaction in json_data["transactions"]:
        tx = Transaction(
            nonce=hex_to_u256(transaction["nonce"]),
            gas_price=hex_to_u256(transaction["gasPrice"]),
            gas=hex_to_u256(transaction["gas"]),
            to=(
                None
                if transaction["to"] == ""
                else hex_to_address(transaction["to"])
            ),
            value=hex_to_u256(transaction["value"]),
            data=hex_to_bytes(transaction["input"]),
            v=hex_to_u256(transaction["v"]),
            r=hex_to_u256(transaction["r"]),
            s=hex_to_u256(transaction["s"]),
        )
        transactions.append(tx)

    return tuple(transactions)


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
