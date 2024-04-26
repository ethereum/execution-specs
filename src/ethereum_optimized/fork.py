"""
Optimized Spec
^^^^^^^^^^^^^^

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

This module contains optimized POW functions can be monkey patched into the
`fork` module of a fork.
"""
from importlib import import_module
from typing import Any, Dict, cast

from ethereum.base_types import U256_CEIL_VALUE
from ethereum.ethash import epoch
from ethereum.exceptions import InvalidBlock

from .utils import add_item

try:
    import ethash
except ImportError as e:
    # Add a message, but keep it an ImportError.
    raise e from Exception(
        "Install with `pip install 'ethereum[optimized]'` to enable this "
        "package"
    )

Header_ = Any


def get_optimized_pow_patches(_fork_name: str) -> Dict[str, Any]:
    """
    Get a dictionary of patches to be patched into the fork to make it
    optimized.
    """
    patches: Dict[str, Any] = {}

    mod = cast(Any, import_module("ethereum." + _fork_name + ".fork"))

    if not hasattr(mod, "validate_proof_of_work"):
        raise Exception(
            "Attempted to get optimized pow patches for non-pow fork"
        )

    generate_header_hash_for_pow = mod.generate_header_hash_for_pow

    @add_item(patches)
    def validate_proof_of_work(header: Header_) -> None:
        """
        See `validate_proof_of_work`.
        """
        epoch_number = epoch(header.number)
        header_hash = generate_header_hash_for_pow(header)

        result = ethash.verify(
            int(epoch_number),
            header_hash,
            header.mix_digest,
            int.from_bytes(header.nonce, "big"),
            (U256_CEIL_VALUE // header.difficulty).to_be_bytes32(),
        )
        if not result:
            raise InvalidBlock

    return patches
