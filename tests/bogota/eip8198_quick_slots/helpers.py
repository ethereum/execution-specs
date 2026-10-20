"""Shared helpers for the EIP-8198 tests."""

from typing import List

from execution_testing import (
    Address,
    Alloc,
    Fork,
    Op,
    Transaction,
)

BLOCK_GAS_LIMIT = 30_000_000
"""
Block gas limit used by the base fee and gas limit tests.

Its gas target lies below the transaction gas limit cap, so a single
transaction can bring a block to its target, and two can fill it.
"""

MAX_FEE_PER_GAS = 10**12
"""Maximum fee per gas that covers every base fee the tests reach."""


def gas_spending_transactions(
    *,
    pre: Alloc,
    sender: Address,
    fork: Fork,
    gas: int,
) -> List[Transaction]:
    """
    Return transactions that together use exactly `gas`.

    Each transaction calls a contract that halts exceptionally, which consumes
    all of the transaction's gas.
    """
    if gas == 0:
        return []
    gas_spender = pre.deploy_contract(code=Op.INVALID)
    cap = fork.transaction_gas_limit_cap() or gas
    chunks = []
    remaining = gas
    while remaining > 0:
        chunk = min(remaining, cap)
        chunks.append(chunk)
        remaining -= chunk
    return [
        Transaction(
            to=gas_spender,
            gas_limit=chunk,
            max_fee_per_gas=MAX_FEE_PER_GAS,
            max_priority_fee_per_gas=0,
            sender=sender,
        )
        for chunk in chunks
    ]
