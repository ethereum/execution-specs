"""
Precompiled Contract Addresses
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

Mapping of precompiled contracts their implementations.
"""
from typing import Callable, Dict

from ...fork_types import Address
from . import (
    ALT_BN128_ADD_ADDRESS,
    ALT_BN128_MUL_ADDRESS,
    ALT_BN128_PAIRING_CHECK_ADDRESS,
    BLAKE2F_ADDRESS,
    BLS12_G1_ADD_ADDRESS,
    BLS12_G1_MSM_ADDRESS,
    BLS12_G2_ADD_ADDRESS,
    BLS12_G2_MSM_ADDRESS,
    BLS12_MAP_FP2_TO_G2_ADDRESS,
    BLS12_MAP_FP_TO_G1_ADDRESS,
    BLS12_PAIRING_ADDRESS,
    ECRECOVER_ADDRESS,
    IDENTITY_ADDRESS,
    MODEXP_ADDRESS,
    POINT_EVALUATION_ADDRESS,
    RIPEMD160_ADDRESS,
    SHA256_ADDRESS,
)
from .alt_bn128 import alt_bn128_add, alt_bn128_mul, alt_bn128_pairing_check
from .blake2f import blake2f
from .bls12_381.bls12_381_g1 import (
    bls12_g1_add,
    bls12_g1_msm,
    bls12_map_fp_to_g1,
)
from .bls12_381.bls12_381_g2 import (
    bls12_g2_add,
    bls12_g2_msm,
    bls12_map_fp2_to_g2,
)
from .bls12_381.bls12_381_pairing import bls12_pairing
from .ecrecover import ecrecover
from .identity import identity
from .modexp import modexp
from .point_evaluation import point_evaluation
from .ripemd160 import ripemd160
from .sha256 import sha256

PRE_COMPILED_CONTRACTS: Dict[Address, Callable] = {
    ECRECOVER_ADDRESS: ecrecover,
    SHA256_ADDRESS: sha256,
    RIPEMD160_ADDRESS: ripemd160,
    IDENTITY_ADDRESS: identity,
    MODEXP_ADDRESS: modexp,
    ALT_BN128_ADD_ADDRESS: alt_bn128_add,
    ALT_BN128_MUL_ADDRESS: alt_bn128_mul,
    ALT_BN128_PAIRING_CHECK_ADDRESS: alt_bn128_pairing_check,
    BLAKE2F_ADDRESS: blake2f,
    POINT_EVALUATION_ADDRESS: point_evaluation,
    BLS12_G1_ADD_ADDRESS: bls12_g1_add,
    BLS12_G1_MSM_ADDRESS: bls12_g1_msm,
    BLS12_G2_ADD_ADDRESS: bls12_g2_add,
    BLS12_G2_MSM_ADDRESS: bls12_g2_msm,
    BLS12_PAIRING_ADDRESS: bls12_pairing,
    BLS12_MAP_FP_TO_G1_ADDRESS: bls12_map_fp_to_g1,
    BLS12_MAP_FP2_TO_G2_ADDRESS: bls12_map_fp2_to_g2,
}
