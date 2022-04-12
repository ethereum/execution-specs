"""
Optimized Spec
^^^^^^^^^^^^^^

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

This module contains functions can be monkey patched into
`ethereum.constantinople.spec` to use alternate optimized implementations.
"""
from ethereum.base_types import U256_CEIL_VALUE
from ethereum.constantinople.eth_types import Header
from ethereum.constantinople.spec import generate_header_hash_for_pow
from ethereum.ethash import epoch
from ethereum.exceptions import InvalidBlock
from ethereum.utils.ensure import ensure

try:
    import ethash
except ImportError as e:
    # Add a message, but keep it an ImportError.
    raise e from Exception(
        "Install with `pip install 'ethereum[optimized]'` to enable this "
        "package"
    )


def validate_proof_of_work(header: Header) -> None:
    """
    See `ethereum.constantinople.spec.validate_proof_of_work`.
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

    ensure(result, InvalidBlock)
