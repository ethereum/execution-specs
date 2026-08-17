"""
Tests for [EIP-8268: Storage Roots in Block Access Lists](https://eips.ethereum.org/EIPS/eip-8268).

Pin the `storage_root` each kind of entry must carry, derived
independently of the transition tool: the root of the written slots,
the untouched pre-existing trie, the empty byte string for empty
tries, and no field at all for accessed-but-unchanged accounts.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    BalAccountExpectation,
    Block,
    BlockAccessListExpectation,
    BlockchainTestFiller,
    Op,
    Transaction,
    compute_storage_trie_root,
)

from .spec import ref_spec_8268

REFERENCE_SPEC_GIT_PATH = ref_spec_8268.git_path
REFERENCE_SPEC_VERSION = ref_spec_8268.version

pytestmark = pytest.mark.valid_from("EIP8268")


def test_written_slots_root(
    blockchain_test: BlockchainTestFiller, pre: Alloc
) -> None:
    """The root commits to exactly the slots the block wrote."""
    contract = pre.deploy_contract(code=Op.SSTORE(1, 2) + Op.SSTORE(3, 4))

    blockchain_test(
        pre=pre,
        post={contract: Account(storage={1: 2, 3: 4})},
        blocks=[
            Block(
                txs=[Transaction(sender=pre.fund_eoa(), to=contract)],
                expected_block_access_list=BlockAccessListExpectation(
                    account_expectations={
                        contract: BalAccountExpectation(
                            storage_root=compute_storage_trie_root(
                                {1: 2, 3: 4}
                            ),
                        ),
                    }
                ),
            )
        ],
    )


def test_untouched_pre_existing_storage_root(
    blockchain_test: BlockchainTestFiller, pre: Alloc
) -> None:
    """
    A balance-only change to a contract with storage commits to the
    pre-existing trie: the root is not a function of the diff alone.
    """
    contract = pre.deploy_contract(code=Op.STOP, storage={5: 6})
    transfer_value = 7

    blockchain_test(
        pre=pre,
        post={contract: Account(balance=transfer_value, storage={5: 6})},
        blocks=[
            Block(
                txs=[
                    Transaction(
                        sender=pre.fund_eoa(),
                        to=contract,
                        value=transfer_value,
                    )
                ],
                expected_block_access_list=BlockAccessListExpectation(
                    account_expectations={
                        contract: BalAccountExpectation(
                            storage_root=compute_storage_trie_root({5: 6}),
                        ),
                    }
                ),
            )
        ],
    )


def test_eoa_balance_change_empty_root(
    blockchain_test: BlockchainTestFiller, pre: Alloc
) -> None:
    """
    An EOA balance change carries the empty byte string, never the
    canonical empty trie root.
    """
    recipient = pre.fund_eoa(amount=1)

    blockchain_test(
        pre=pre,
        post={recipient: Account(balance=1 + 5)},
        blocks=[
            Block(
                txs=[
                    Transaction(sender=pre.fund_eoa(), to=recipient, value=5)
                ],
                expected_block_access_list=BlockAccessListExpectation(
                    account_expectations={
                        recipient: BalAccountExpectation(
                            storage_root=b"",
                        ),
                    }
                ),
            )
        ],
    )


def test_cleared_storage_empty_root(
    blockchain_test: BlockchainTestFiller, pre: Alloc
) -> None:
    """A trie emptied by the block encodes as the empty byte string."""
    contract = pre.deploy_contract(code=Op.SSTORE(1, 0), storage={1: 2})

    blockchain_test(
        pre=pre,
        post={contract: Account(storage={})},
        blocks=[
            Block(
                txs=[Transaction(sender=pre.fund_eoa(), to=contract)],
                expected_block_access_list=BlockAccessListExpectation(
                    account_expectations={
                        contract: BalAccountExpectation(
                            storage_root=b"",
                        ),
                    }
                ),
            )
        ],
    )


def test_touched_only_account_has_no_root(
    blockchain_test: BlockchainTestFiller, pre: Alloc
) -> None:
    """An accessed-but-unchanged account carries no storage root."""
    target = pre.deploy_contract(code=Op.STOP, storage={7: 8})
    reader = pre.deploy_contract(code=Op.POP(Op.BALANCE(target)))

    blockchain_test(
        pre=pre,
        post={target: Account(storage={7: 8})},
        blocks=[
            Block(
                txs=[Transaction(sender=pre.fund_eoa(), to=reader)],
                expected_block_access_list=BlockAccessListExpectation(
                    account_expectations={
                        target: BalAccountExpectation(
                            storage_root=None,
                        ),
                    }
                ),
            )
        ],
    )
