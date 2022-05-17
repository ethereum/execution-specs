"""
Genesis Configuration
^^^^^^^^^^^^^^^^^^^^^

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

Functionalities and entities to obtain the genesis configurations for
different chains.
"""
import json
import pkgutil
from dataclasses import dataclass
from typing import Dict, cast

from ethereum.base_types import (
    U256,
    Bytes,
    Bytes8,
    Uint,
    Uint64,
    slotted_freezable,
)
from ethereum.utils.hexadecimal import (
    hex_to_bytes,
    hex_to_bytes8,
    hex_to_u256,
    hex_to_uint,
)

from .eth_types import Address
from .utils.hexadecimal import hex_to_address


@slotted_freezable
@dataclass
class GenesisConfiguration:
    """
    Configuration for the first block of an Ethereum chain.

    Specifies the allocation of ether set out in the pre-sale, and some of
    the fields of the genesis block.
    """

    chain_id: Uint64
    difficulty: Uint
    extra_data: Bytes
    gas_limit: Uint
    nonce: Bytes8
    timestamp: U256
    # Mapping between address and their initial balance
    initial_balances: Dict[Address, U256]


def genesis_configuration(genesis_file: str) -> GenesisConfiguration:
    """
    Obtain the genesis configuration from the given genesis json file.

    The genesis file should be present in the `assets` directory.

    Parameters
    ----------
    genesis_file :
        The json file which contains the parameters for the genesis block
        and the pre-sale allocation data.

    Returns
    -------
    configuration : `GenesisConfiguration`
        The genesis configuration obtained from the json genesis file.
    """
    genesis_str_data = cast(
        bytes, pkgutil.get_data("ethereum", f"assets/{genesis_file}")
    ).decode()
    genesis_data = json.loads(genesis_str_data)

    initial_balances = {
        hex_to_address(address): hex_to_u256(account["balance"])
        for address, account in genesis_data["alloc"].items()
    }

    return GenesisConfiguration(
        chain_id=Uint64(genesis_data["config"]["chainId"]),
        difficulty=hex_to_uint(genesis_data["difficulty"]),
        extra_data=hex_to_bytes(genesis_data["extraData"]),
        gas_limit=hex_to_uint(genesis_data["gasLimit"]),
        nonce=hex_to_bytes8(genesis_data["nonce"]),
        timestamp=hex_to_u256(genesis_data["timestamp"]),
        initial_balances=initial_balances,
    )
