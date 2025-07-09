"""
Blob Gas Calculations
^^^^^^^^^^^^^^^^^^^^^

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

Blob gas calculations for blocks and transactions.
"""

from ethereum_types.numeric import U64, Uint

from .blocks import Header
from .transactions import BlobTransaction, Transaction
from .utils.numeric import taylor_exponential

# Blob gas constants
TARGET_BLOB_GAS_PER_BLOCK = U64(786432)
GAS_PER_BLOB = U64(2**17)
MIN_BLOB_GASPRICE = Uint(1)
BLOB_BASE_FEE_UPDATE_FRACTION = Uint(5007716)
MAX_BLOB_GAS_PER_BLOCK = U64(786432)


def calculate_excess_blob_gas(parent_header: Header) -> U64:
    """
    Calculated the excess blob gas for the current block based
    on the gas used in the parent block.

    Parameters
    ----------
    parent_header :
        The parent block of the current block.

    Returns
    -------
    excess_blob_gas: `ethereum.base_types.U64`
        The excess blob gas for the current block.
    """
    # At the fork block, these are defined as zero.
    excess_blob_gas = U64(0)
    blob_gas_used = U64(0)

    if isinstance(parent_header, Header):
        # After the fork block, read them from the parent header.
        excess_blob_gas = parent_header.excess_blob_gas
        blob_gas_used = parent_header.blob_gas_used

    parent_blob_gas = excess_blob_gas + blob_gas_used
    if parent_blob_gas < TARGET_BLOB_GAS_PER_BLOCK:
        return U64(0)
    else:
        return parent_blob_gas - TARGET_BLOB_GAS_PER_BLOCK


def calculate_total_blob_gas(tx: Transaction) -> U64:
    """
    Calculate the total blob gas for a transaction.

    Parameters
    ----------
    tx :
        The transaction for which the blob gas is to be calculated.

    Returns
    -------
    total_blob_gas: `ethereum.base_types.Uint`
        The total blob gas for the transaction.
    """
    if isinstance(tx, BlobTransaction):
        return GAS_PER_BLOB * U64(len(tx.blob_versioned_hashes))
    else:
        return U64(0)


def calculate_blob_gas_price(excess_blob_gas: U64) -> Uint:
    """
    Calculate the blob gasprice for a block.

    Parameters
    ----------
    excess_blob_gas :
        The excess blob gas for the block.

    Returns
    -------
    blob_gasprice: `Uint`
        The blob gasprice.
    """
    return taylor_exponential(
        MIN_BLOB_GASPRICE,
        Uint(excess_blob_gas),
        BLOB_BASE_FEE_UPDATE_FRACTION,
    )


def calculate_data_fee(excess_blob_gas: U64, tx: Transaction) -> Uint:
    """
    Calculate the blob data fee for a transaction.

    Parameters
    ----------
    excess_blob_gas :
        The excess_blob_gas for the execution.
    tx :
        The transaction for which the blob data fee is to be calculated.

    Returns
    -------
    data_fee: `Uint`
        The blob data fee.
    """
    return Uint(calculate_total_blob_gas(tx)) * calculate_blob_gas_price(
        excess_blob_gas
    ) 