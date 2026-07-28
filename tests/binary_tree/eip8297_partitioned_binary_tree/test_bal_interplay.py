"""
Block-access-list interplay tests for the EIP-8297 partitioned binary
tree: EIP-7928 BALs are built by the fork and validated by EEST at
fill time, even though the underlying commitment scheme has been
swapped from the Merkle Patricia Trie to the partitioned binary tree.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    BalAccountExpectation,
    BalBalanceChange,
    BalNonceChange,
    BalStorageChange,
    BalStorageSlot,
    Block,
    BlockAccessListExpectation,
    BlockchainTestFiller,
    Initcode,
    Op,
    Transaction,
)

from .helpers import create_contract_via_factory
from .spec import ref_spec_8297

REFERENCE_SPEC_GIT_PATH = ref_spec_8297.git_path
REFERENCE_SPEC_VERSION = ref_spec_8297.version

pytestmark = pytest.mark.valid_from("BinaryTree")


def test_bal_validates_multi_account_storage_writes(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """
    Verify a block whose transactions write storage across several
    accounts fills with its EIP-7928 block access list built and
    independently checked against expectations: the commitment swap
    must not perturb which addresses/slots the BAL records.
    """
    alice = pre.fund_eoa()
    bob = pre.fund_eoa()

    slot_a, value_a = 1, 0x1111
    slot_b, value_b = 2, 0x2222
    contract_a = pre.deploy_contract(code=Op.SSTORE(slot_a, value_a) + Op.STOP)
    contract_b = pre.deploy_contract(code=Op.SSTORE(slot_b, value_b) + Op.STOP)

    tx_a = Transaction(sender=alice, to=contract_a)
    tx_b = Transaction(sender=bob, to=contract_b)

    block = Block(
        txs=[tx_a, tx_b],
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                alice: BalAccountExpectation(
                    nonce_changes=[
                        BalNonceChange(block_access_index=1, post_nonce=1)
                    ],
                ),
                bob: BalAccountExpectation(
                    nonce_changes=[
                        BalNonceChange(block_access_index=2, post_nonce=1)
                    ],
                ),
                contract_a: BalAccountExpectation(
                    storage_changes=[
                        BalStorageSlot(
                            slot=slot_a,
                            slot_changes=[
                                BalStorageChange(
                                    block_access_index=1, post_value=value_a
                                )
                            ],
                        )
                    ],
                ),
                contract_b: BalAccountExpectation(
                    storage_changes=[
                        BalStorageSlot(
                            slot=slot_b,
                            slot_changes=[
                                BalStorageChange(
                                    block_access_index=2, post_value=value_b
                                )
                            ],
                        )
                    ],
                ),
            }
        ),
    )

    blockchain_test(
        pre=pre,
        blocks=[block],
        post={
            alice: Account(nonce=1),
            bob: Account(nonce=1),
            contract_a: Account(storage={slot_a: value_a}),
            contract_b: Account(storage={slot_b: value_b}),
        },
    )


def test_bal_validates_storage_creation_and_selfdestruct_mix(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """
    Verify a block mixing a plain storage write, a CREATE, and a
    SELFDESTRUCT still builds and validates its EIP-7928 block access
    list correctly.

    BALs record raw addresses and un-embedded slot numbers exactly as
    EIP-7928 defines them, never PBT tree keys, so the commitment swap
    must not leak into what the BAL records.
    """
    alice = pre.fund_eoa()
    bob = pre.fund_eoa()
    charlie = pre.fund_eoa()

    slot, value = 1, 0xAAAA
    writer = pre.deploy_contract(code=Op.SSTORE(slot, value) + Op.STOP)

    child_slot, child_value = 2, 0xBBBB
    deploy_code = Op.STOP
    initcode = Initcode(
        deploy_code=deploy_code,
        initcode_prefix=Op.SSTORE(child_slot, child_value),
    )
    factory, child = create_contract_via_factory(pre, initcode)

    beneficiary = pre.fund_eoa(amount=0)
    endowment = 500
    victim_code = Op.SELFDESTRUCT(beneficiary)
    victim = pre.deploy_contract(code=victim_code, balance=endowment)

    tx_write = Transaction(sender=alice, to=writer)
    tx_create = Transaction(sender=bob, to=factory)
    tx_destruct = Transaction(sender=charlie, to=victim)

    block = Block(
        txs=[tx_write, tx_create, tx_destruct],
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                writer: BalAccountExpectation(
                    storage_changes=[
                        BalStorageSlot(
                            slot=slot,
                            slot_changes=[
                                BalStorageChange(
                                    block_access_index=1, post_value=value
                                )
                            ],
                        )
                    ],
                ),
                child: BalAccountExpectation(
                    storage_changes=[
                        BalStorageSlot(
                            slot=child_slot,
                            slot_changes=[
                                BalStorageChange(
                                    block_access_index=2,
                                    post_value=child_value,
                                )
                            ],
                        )
                    ],
                ),
                victim: BalAccountExpectation(
                    balance_changes=[
                        BalBalanceChange(block_access_index=3, post_balance=0)
                    ],
                ),
                beneficiary: BalAccountExpectation(
                    balance_changes=[
                        BalBalanceChange(
                            block_access_index=3, post_balance=endowment
                        )
                    ],
                ),
            }
        ),
    )

    blockchain_test(
        pre=pre,
        blocks=[block],
        post={
            alice: Account(nonce=1),
            bob: Account(nonce=1),
            charlie: Account(nonce=1),
            writer: Account(storage={slot: value}),
            child: Account(
                code=deploy_code, storage={child_slot: child_value}
            ),
            factory: Account(nonce=2),
            victim: Account(balance=0, code=victim_code),
            beneficiary: Account(balance=endowment),
        },
    )
