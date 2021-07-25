"""
Utility Functions For Transactions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

..contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

Transactions specific utility functions used in this application.
"""
from typing import Any, Dict, Tuple

from ethereum.base_types import Bytes0
from ethereum.frontier.eth_types import Transaction
from ethereum.frontier.utils.hexadecimal import hex_to_address
from ethereum.utils.hexadecimal import hex_to_bytes, hex_to_u256


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
                Bytes0(b"")
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
