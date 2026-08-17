"""
Tests for invalid EIP-8268 storage roots in block access lists.

Every deviation from the canonical encoding invalidates the block: a
wrong root value, the spelled-out canonical empty root where the empty
byte string is required, a missing root on a changed entry, and a root
on an accessed-but-unchanged entry.
"""

import pytest
from execution_testing import (
    Alloc,
    BalAccountExpectation,
    Block,
    BlockAccessListExpectation,
    BlockchainTestFiller,
    BlockException,
    Bytes,
    Op,
    Transaction,
    compute_storage_trie_root,
)
from execution_testing.test_types.block_access_list.modifiers import (
    modify_storage_root,
)

from .spec import ref_spec_8268

REFERENCE_SPEC_GIT_PATH = ref_spec_8268.git_path
REFERENCE_SPEC_VERSION = ref_spec_8268.version

pytestmark = [
    pytest.mark.valid_from("EIP8268"),
    pytest.mark.exception_test,
]

CANONICAL_EMPTY_TRIE_ROOT = Bytes(
    bytes.fromhex(
        "56e81f171bcc55a6ff8345e692c0f86e5b48e01b996cadc001622fb5e363b421"
    )
)


def test_canonical_empty_root_rejected(
    blockchain_test: BlockchainTestFiller, pre: Alloc
) -> None:
    """
    An empty trie spelled out as the 32-byte canonical root instead of
    the empty byte string invalidates the block.
    """
    recipient = pre.fund_eoa(amount=1)

    blockchain_test(
        pre=pre,
        post=pre,
        blocks=[
            Block(
                txs=[
                    Transaction(sender=pre.fund_eoa(), to=recipient, value=5)
                ],
                exception=BlockException.INVALID_BLOCK_ACCESS_LIST,
                expected_block_access_list=BlockAccessListExpectation(
                    account_expectations={
                        recipient: BalAccountExpectation(storage_root=b""),
                    }
                ).modify(
                    modify_storage_root(recipient, CANONICAL_EMPTY_TRIE_ROOT)
                ),
            )
        ],
    )


def test_wrong_storage_root_rejected(
    blockchain_test: BlockchainTestFiller, pre: Alloc
) -> None:
    """A root that does not commit to the written slots is rejected."""
    contract = pre.deploy_contract(code=Op.SSTORE(1, 2))

    blockchain_test(
        pre=pre,
        post=pre,
        blocks=[
            Block(
                txs=[Transaction(sender=pre.fund_eoa(), to=contract)],
                exception=BlockException.INVALID_BLOCK_ACCESS_LIST,
                expected_block_access_list=BlockAccessListExpectation(
                    account_expectations={
                        contract: BalAccountExpectation(
                            storage_root=compute_storage_trie_root({1: 2}),
                        ),
                    }
                ).modify(
                    modify_storage_root(
                        contract, compute_storage_trie_root({1: 0xDEAD})
                    )
                ),
            )
        ],
    )


def test_missing_storage_root_rejected(
    blockchain_test: BlockchainTestFiller, pre: Alloc
) -> None:
    """A changed entry without its storage root is rejected."""
    contract = pre.deploy_contract(code=Op.SSTORE(1, 2))

    blockchain_test(
        pre=pre,
        post=pre,
        blocks=[
            Block(
                txs=[Transaction(sender=pre.fund_eoa(), to=contract)],
                exception=BlockException.INVALID_BLOCK_ACCESS_LIST,
                expected_block_access_list=BlockAccessListExpectation(
                    account_expectations={
                        contract: BalAccountExpectation(
                            storage_root=compute_storage_trie_root({1: 2}),
                        ),
                    }
                ).modify(modify_storage_root(contract, None)),
            )
        ],
    )


def test_root_on_touched_only_entry_rejected(
    blockchain_test: BlockchainTestFiller, pre: Alloc
) -> None:
    """An accessed-but-unchanged entry carrying a root is rejected."""
    target = pre.deploy_contract(code=Op.STOP, storage={7: 8})
    reader = pre.deploy_contract(code=Op.POP(Op.BALANCE(target)))

    blockchain_test(
        pre=pre,
        post=pre,
        blocks=[
            Block(
                txs=[Transaction(sender=pre.fund_eoa(), to=reader)],
                exception=BlockException.INVALID_BLOCK_ACCESS_LIST,
                expected_block_access_list=BlockAccessListExpectation(
                    account_expectations={
                        target: BalAccountExpectation(storage_root=None),
                    }
                ).modify(
                    modify_storage_root(
                        target, compute_storage_trie_root({7: 8})
                    )
                ),
            )
        ],
    )
