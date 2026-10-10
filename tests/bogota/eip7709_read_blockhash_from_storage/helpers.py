"""Helpers for testing EIP-7709."""

from execution_testing import Bytecode, Op

from .spec import Spec

HISTORY_RET_OFFSET = 32


def history_staticcall(query_block: int) -> Bytecode:
    """Return bytecode that queries the history contract for a block hash."""
    return Op.MSTORE(0, query_block) + Op.STATICCALL(
        Op.GAS,
        Spec.HISTORY_STORAGE_ADDRESS,
        0,
        32,
        HISTORY_RET_OFFSET,
        32,
    )
