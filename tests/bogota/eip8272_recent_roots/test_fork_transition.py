"""
Tests for
[EIP-8272: Recent Roots for Frame Transactions](https://eips.ethereum.org/EIPS/eip-8272)
across the fork that activates it.

The recent root contract is ordinary code and every opcode it runs
exists before the fork, so a root can be published before frame
transactions do. A recent root verifier frame in the first block of the
fork references such a root exactly as it would one published after it:
the slot clock does not reset at the fork.
"""

import json
from os.path import realpath
from pathlib import Path

import pytest
from execution_testing import (
    Account,
    Alloc,
    BalAccountExpectation,
    BalStorageChange,
    BalStorageSlot,
    Block,
    BlockAccessListExpectation,
    BlockchainTestFiller,
    Fork,
    FrameReceipt,
    Op,
    Transaction,
    TransactionReceipt,
)

from ..eip8141_frame_transactions.helpers import sender_frame, verify_frame
from ..eip8141_frame_transactions.spec import Spec as FrameSpec
from .helpers import recent_root_frame, validation_gas
from .spec import (
    Spec,
    entry_hash,
    ref_spec_8272,
    source_id,
    storage_key,
    validation_tuple,
    write_calldata,
)

REFERENCE_SPEC_GIT_PATH = ref_spec_8272.git_path
REFERENCE_SPEC_VERSION = ref_spec_8272.version

pytestmark = pytest.mark.valid_at_transition_to("Bogota")

FORK_TIMESTAMP = 15_000
"""Timestamp at which the transition fork activates EIP-8272."""

SLOT_EXECUTED = 0x01
"""Storage slot used by target contracts to record execution."""

WRITE_SLOT = 500
"""Slot of the last pre-fork block, in which the root is published."""

SALT = bytes(32)
ROOT = (0xF0).to_bytes(32, "big")

DEPLOY_TX_PATH = Path(realpath(__file__)).parent / "recent_root_deploy_tx.json"


def deployment_transaction() -> Transaction:
    """
    Return the pre-signed creation transaction the EIP publishes, as the
    deployment test generator reads it.
    """
    tx_json = json.loads(DEPLOY_TX_PATH.read_text())
    tx_json["gasLimit"] = tx_json.pop("gas")
    tx_json["protected"] = False
    return Transaction.model_validate(tx_json).with_signature_and_sender()


@pytest.mark.pre_alloc_mutable
def test_root_published_before_fork_verifies_after(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Deploy the contract and publish a root in the last pre-fork block,
    then verify the root through a recent root verifier frame in the
    block that activates the fork.

    The pre-fork block carries the deployment transaction itself, so the
    predeploy the transition fixture places in genesis is removed first.
    The write is a plain call from the pre-fork transaction types.
    """
    pre[Spec.RECENT_ROOT_ADDRESS] = Account(code=b"", nonce=0, balance=0)
    deploy_tx = deployment_transaction()
    deployer = deploy_tx.sender
    assert deployer == Spec.RECENT_ROOT_DEPLOYER
    assert deploy_tx.created_contract == Spec.RECENT_ROOT_ADDRESS
    gas_price = deploy_tx.gas_price
    assert gas_price is not None
    pre.fund_address(deployer, deploy_tx.gas_limit * gas_price)

    source = pre.fund_eoa()
    sender = pre.fund_eoa()
    target = pre.deploy_contract(code=Op.SSTORE(SLOT_EXECUTED, 1) + Op.STOP)
    source_identifier = source_id(source, SALT)
    key = storage_key(source_identifier, WRITE_SLOT)
    value = int.from_bytes(
        entry_hash(source_identifier, WRITE_SLOT, ROOT), "big"
    )

    publish = Transaction(
        sender=source,
        to=Spec.RECENT_ROOT_ADDRESS,
        data=write_calldata(SALT, ROOT),
    )
    verify = Transaction(
        sender=sender,
        frames=[
            recent_root_frame(
                validation_tuple(source_identifier, WRITE_SLOT, ROOT)
            ),
            verify_frame(),
            sender_frame(target=target),
        ],
        expected_receipt=TransactionReceipt(
            payer=sender,
            frame_receipts=[
                FrameReceipt(
                    status=FrameSpec.STATUS_SUCCESS,
                    gas_used=validation_gas(
                        fork.fork_at(timestamp=FORK_TIMESTAMP),
                        tuples=1,
                        cold_keys=1,
                    ),
                    state_gas_used=0,
                ),
                FrameReceipt(status=FrameSpec.STATUS_SUCCESS),
                FrameReceipt(status=FrameSpec.STATUS_SUCCESS),
            ],
        ),
    )

    blocks = [
        Block(
            timestamp=FORK_TIMESTAMP - 1,
            slot_number=WRITE_SLOT,
            txs=[deploy_tx, publish],
            expected_block_access_list=BlockAccessListExpectation(
                account_expectations={
                    Spec.RECENT_ROOT_ADDRESS: BalAccountExpectation(
                        storage_changes=[
                            BalStorageSlot(
                                slot=key,
                                slot_changes=[
                                    BalStorageChange(
                                        block_access_index=2,
                                        post_value=value,
                                    )
                                ],
                            )
                        ],
                    ),
                }
            ),
        ),
        Block(
            timestamp=FORK_TIMESTAMP,
            slot_number=WRITE_SLOT + 1,
            txs=[verify],
            expected_block_access_list=BlockAccessListExpectation(
                account_expectations={
                    Spec.RECENT_ROOT_ADDRESS: BalAccountExpectation(
                        storage_changes=[],
                        storage_reads=[key],
                    ),
                }
            ),
        ),
    ]
    post = {
        deployer: Account(nonce=1),
        Spec.RECENT_ROOT_ADDRESS: Account(
            nonce=Spec.RECENT_ROOT_NONCE,
            code=Spec.RECENT_ROOT_CODE,
            storage={key: value},
        ),
        target: Account(storage={SLOT_EXECUTED: 1}),
    }

    blockchain_test(pre=pre, blocks=blocks, post=post)
