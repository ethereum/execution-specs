"""
Precompiled Contract Addresses
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

Addresses of precompiled contracts and mappings to their
implementations.
"""

from ...utils.hexadecimal import hex_to_address

__all__ = (
    "ECRECOVER_ADDRESS",
    "SHA256_ADDRESS",
    "RIPEMD160_ADDRESS",
    "IDENTITY_ADDRESS",
    "MODEXP_ADDRESS",
    "ALT_BN128_ADD_ADDRESS",
    "ALT_BN128_MUL_ADDRESS",
    "ALT_BN128_PAIRING_CHECK_ADDRESS",
    "BLAKE2F_ADDRESS",
    "POINT_EVALUATION_ADDRESS",
    "BLS12_G1_ADD_ADDRESS",
    "BLS12_G1_MULTIPLY_ADDRESS",
    "BLS12_G1_MSM_ADDRESS",
    "BLS12_G2_ADD_ADDRESS",
    "BLS12_G2_MULTIPLY_ADDRESS",
    "BLS12_G2_MSM_ADDRESS",
    "BLS12_PAIRING_ADDRESS",
)

ECRECOVER_ADDRESS = hex_to_address("0x01")
SHA256_ADDRESS = hex_to_address("0x02")
RIPEMD160_ADDRESS = hex_to_address("0x03")
IDENTITY_ADDRESS = hex_to_address("0x04")
MODEXP_ADDRESS = hex_to_address("0x05")
ALT_BN128_ADD_ADDRESS = hex_to_address("0x06")
ALT_BN128_MUL_ADDRESS = hex_to_address("0x07")
ALT_BN128_PAIRING_CHECK_ADDRESS = hex_to_address("0x08")
BLAKE2F_ADDRESS = hex_to_address("0x09")
POINT_EVALUATION_ADDRESS = hex_to_address("0x0a")
BLS12_G1_ADD_ADDRESS = hex_to_address("0x0b")
BLS12_G1_MULTIPLY_ADDRESS = hex_to_address("0x0c")
BLS12_G1_MSM_ADDRESS = hex_to_address("0x0d")
BLS12_G2_ADD_ADDRESS = hex_to_address("0x0e")
BLS12_G2_MULTIPLY_ADDRESS = hex_to_address("0x0f")
BLS12_G2_MSM_ADDRESS = hex_to_address("0x10")
BLS12_PAIRING_ADDRESS = hex_to_address("0x11")
