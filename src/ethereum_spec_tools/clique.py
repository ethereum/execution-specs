"""
Clique
^^^^^^

This file implements an alternative version of the `state_transition` function
that allows processing blocks with on chains using Clique consensus. We do not
check the Clique block validity rules, only disable POW rules that don't
apply to Clique.

NOTE: Clique is deprecated, but non-deprecated testnets (notably Goerli) have
historical clique blocks.
"""

import dataclasses
from typing import Any

from ethereum import rlp
from ethereum.base_types import U256
from ethereum.crypto.elliptic_curve import SECP256K1N, secp256k1_recover
from ethereum.crypto.hash import keccak256
from ethereum.exceptions import InvalidBlock
from ethereum.utils.ensure import ensure

from .forks import Hardfork


def validate_header(
    hardfork: Hardfork, header: Any, parent_header: Any
) -> None:
    """
    Verifies a Clique block header.

    Changes vs POW:
    * No difficulty checks
    * No POW validation
    * Extra data is longer
    """
    ensure(header.timestamp > parent_header.timestamp, InvalidBlock)
    ensure(header.number == parent_header.number + 1, InvalidBlock)
    ensure(
        hardfork.module("spec").check_gas_limit(
            header.gas_limit, parent_header.gas_limit
        ),
        InvalidBlock,
    )

    if header.number % 30000 == 0:
        ensure(len(header.extra_data) > 97, InvalidBlock)
    else:
        ensure(len(header.extra_data) == 97, InvalidBlock)

    block_parent_hash = keccak256(rlp.encode(parent_header))
    ensure(header.parent_hash == block_parent_hash, InvalidBlock)


def dont_pay_rewards(
    state: Any,
    block_number: Any,
    coinbase: Any,
    ommers: Any,
) -> None:
    """
    No block rewards are paid on Clique networks.
    """
    pass


def state_transition(hardfork: Any, chain: Any, block: Any) -> None:
    """
    Do a state transition for a Clique block.

    Changes vs POW:
    * Clique header validation
    * Coinbase is block signer (found in extra data)
    """
    parent_header = chain.blocks[-1].header
    validate_header(hardfork, block.header, parent_header)
    hardfork.module("spec").validate_ommers(block.ommers, block.header, chain)

    r = U256.from_be_bytes(block.header.extra_data[-65:-33])
    s = U256.from_be_bytes(block.header.extra_data[-33:-1])
    v = U256(block.header.extra_data[-1])

    ensure(v == 0 or v == 1, InvalidBlock)
    ensure(0 < r and r < SECP256K1N, InvalidBlock)
    ensure(0 < s and s < SECP256K1N, InvalidBlock)

    header_without_signature = dataclasses.replace(
        block.header, extra_data=block.header.extra_data[:-65]
    )

    signer_public_key = secp256k1_recover(
        r, s, v, keccak256(rlp.encode(header_without_signature))
    )
    signer_address = hardfork.module("eth_types").Address(
        keccak256(signer_public_key)[12:32]
    )

    pay_rewards_backup = hardfork.module("spec").pay_rewards
    hardfork.module("spec").pay_rewards = dont_pay_rewards

    (
        gas_used,
        transactions_root,
        receipt_root,
        block_logs_bloom,
        state,
    ) = hardfork.module("spec").apply_body(
        chain.state,
        hardfork.module("spec").get_last_256_block_hashes(chain),
        signer_address,
        block.header.number,
        block.header.gas_limit,
        block.header.timestamp,
        block.header.difficulty,
        block.transactions,
        block.ommers,
        chain.chain_id,
    )

    hardfork.module("spec").pay_rewards = pay_rewards_backup

    ensure(gas_used == block.header.gas_used, InvalidBlock)
    ensure(transactions_root == block.header.transactions_root, InvalidBlock)
    ensure(
        hardfork.module("spec").state_root(state) == block.header.state_root,
        InvalidBlock,
    )
    ensure(receipt_root == block.header.receipt_root, InvalidBlock)
    ensure(block_logs_bloom == block.header.bloom, InvalidBlock)

    chain.blocks.append(block)
    if len(chain.blocks) > 255:
        # Real clients have to store more blocks to deal with reorgs, but the
        # protocol only requires the last 255
        chain.blocks = chain.blocks[-255:]
