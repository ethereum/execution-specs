"""Cache-invalidation stress coverage for the EIP-8297 BinaryTree fork."""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Block,
    BlockchainTestFiller,
    Op,
    Transaction,
)

from .spec import ref_spec_8297

REFERENCE_SPEC_GIT_PATH = ref_spec_8297.git_path
REFERENCE_SPEC_VERSION = ref_spec_8297.version

pytestmark = [pytest.mark.valid_from("BinaryTree"), pytest.mark.slow]

CACHE_INVALIDATION_HORIZON = 128
SLOT = 0
INITIAL_VALUE = 1
MID_VALUE = 2
FINAL_VALUE = 3

_WRITE_CODE = Op.SSTORE(SLOT, Op.CALLDATALOAD(0)) + Op.STOP


def _word(value: int) -> bytes:
    """Encode one calldata word for the cache-stress writer contract."""
    return value.to_bytes(32, byteorder="big")


def test_rpc_state_after_cache_invalidation_horizon(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
) -> None:
    """
    Keep one storage key alive across a 128-block cache horizon and mutate it
    on both sides of that boundary.

    The account starts at ``1`` in genesis, changes to ``2`` in block 1,
    remains untouched through block 128, and changes to ``3`` in block 129.
    When the generated engine fixture includes ``postVerifications``, the Hive
    engine consumer primes this exact storage RPC at genesis and verifies it
    again after the final forkchoice update. A stale state/RPC cache returning
    either the genesis value or the pre-flush value therefore fails even when
    block execution and state-root validation themselves succeeded.

    ``BinaryTree`` currently commits through PBT from genesis. This test
    exercises the post-flip cache horizon available on the branch today; it
    deliberately does not pretend to model the future MPT-to-PBT activation
    boundary.
    """
    contract = pre.deploy_contract(
        code=_WRITE_CODE,
        storage={SLOT: INITIAL_VALUE},
    )
    sender = pre.fund_eoa()

    first_write = Block(
        txs=[
            Transaction(
                sender=sender,
                to=contract,
                data=_word(MID_VALUE),
            )
        ]
    )
    quiet_blocks = [Block() for _ in range(CACHE_INVALIDATION_HORIZON - 1)]
    post_horizon_write = Block(
        txs=[
            Transaction(
                sender=sender,
                to=contract,
                data=_word(FINAL_VALUE),
            )
        ]
    )

    blocks = [first_write, *quiet_blocks, post_horizon_write]
    assert len(blocks) == CACHE_INVALIDATION_HORIZON + 1

    blockchain_test(
        pre=pre,
        blocks=blocks,
        post={contract: Account(storage={SLOT: FINAL_VALUE})},
    )
