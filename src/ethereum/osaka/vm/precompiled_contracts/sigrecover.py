"""
Ethereum Virtual Machine (EVM) Sigrecover PRECOMPILED CONTRACT
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

Implementation of the `Sigrecover` precompiled contract.
"""
from ...vm import Evm
from ...vm.gas import GAS_SIGRECOVER, charge_gas
from ..exceptions import InvalidParameter

from ...sig_algorithms import algorithm_from_type

from ethereum_types.bytes import Bytes20
from ethereum_types.numeric import U8, U256, Uint

NULL_ADDRESS = Bytes20.fromhex("0x0000000000000000000000000000000000000000")
COST_PER_ADDITIONAL_AUTH_BYTE = Uint(16)

def sigrecover(evm: Evm) -> None:
    """
    Recovers the EIP-7932 signature and writes the address to output.

    Parameters
    ----------
    evm :
        The current EVM frame.
    """
    charge_gas(evm, GAS_SIGRECOVER)

    data = evm.message.data
    
    if len(data) < 64:
        raise InvalidParameter
    
    hash = data[:32]
    alg_type = U8(data[32])
    sig_length = U256(int.from_bytes(data[33:64], "little"))

    if alg_type == U8(0xff):
        evm.output = NULL_ADDRESS
        return

    try:
        alg = algorithm_from_type(alg_type)
    except Exception:
        evm.output = NULL_ADDRESS
        return

    if sig_length > U256(alg.max_length) or sig_length < U256(len(data) - 64):
        evm.output = NULL_ADDRESS
        return
    
    charge_gas(evm, (Uint(max(0, int(sig_length) - 65)) * COST_PER_ADDITIONAL_AUTH_BYTE) + Uint(alg.gas_penalty))
    
    evm.output = alg.verify(data[64:64 + int(sig_length)], hash)
