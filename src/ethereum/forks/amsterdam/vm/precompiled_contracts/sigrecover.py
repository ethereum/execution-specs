"""
Implementation of the SIGRECOVER precompile defined from EIP-7932.
"""

from ethereum_types.numeric import U8

from ethereum.utils.byte import left_pad_zero_bytes

from ...algorithms import (
    algorithm_registry,
    calculate_penalty,
    exceptions,
    pubkey_to_address,
    validate_signature,
    verify_signature,
)
from ...vm import Evm
from ...vm.gas import GAS_SIGRECOVER_BASE, charge_gas


def sigrecover(evm: Evm) -> None:
    """
    Takes an opaque signature and signing data and returns
    the address of the signer if valid.

    Parameters
    ----------
    evm :
        The current EVM frame.

    """
    data = evm.message.data

    # GAS
    charge_gas(evm, GAS_SIGRECOVER_BASE)

    # OPERATION
    if len(data) == 0:
        evm.output = left_pad_zero_bytes(b"", 32)
        return

    if U8(data[0]) not in algorithm_registry:
        evm.output = left_pad_zero_bytes(b"", 32)
        return

    size = algorithm_registry[U8(data[0])].size

    if len(data) <= int(size):
        evm.output = left_pad_zero_bytes(b"", 32)
        return

    signature = data[:size]
    signing_data = data[size:]

    charge_gas(evm, calculate_penalty(U8(data[0]), signing_data))

    try:
        validate_signature(signature)
        pubkey = verify_signature(signing_data, signature)
    except exceptions.AlgorithmValidationError:
        evm.output = left_pad_zero_bytes(b"", 32)
        return
    except exceptions.AlgorithmVerificationError:
        evm.output = left_pad_zero_bytes(b"", 32)
        return
    except AssertionError:
        evm.output = left_pad_zero_bytes(b"", 32)
        return

    addr = pubkey_to_address(pubkey, U8(signature[0]))
    evm.output = left_pad_zero_bytes(addr, 32)
    return
