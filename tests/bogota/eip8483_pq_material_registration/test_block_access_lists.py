"""
Block access list tests for
[EIP-8483: Post-Quantum Material Registration](https://eips.ethereum.org/EIPS/eip-8483).
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
    FeeSystemContractRequest,
    Header,
    Requests,
    Transaction,
)

from .helpers import PQRequestClass, record_storage, with_both_registrations
from .spec import PROOFS_OF_POSSESSION, Spec, ref_spec_8483

REFERENCE_SPEC_GIT_PATH = ref_spec_8483.git_path
REFERENCE_SPEC_VERSION = ref_spec_8483.version

pytestmark = [
    pytest.mark.valid_from("Bogota"),
    pytest.mark.execute(
        pytest.mark.skip(reason="Assumes the predeploys' genesis state")
    ),
]


def slot_changes(slot: int, *changes: tuple[int, int]) -> BalStorageSlot:
    """Return `(block_access_index, post_value)` changes for one slot."""
    return BalStorageSlot(
        slot=slot,
        slot_changes=[
            BalStorageChange(block_access_index=index, post_value=value)
            for index, value in changes
        ],
    )


@with_both_registrations
def test_bal_registration(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    request_class: type[FeeSystemContractRequest],
) -> None:
    """
    A registration writes the count, the tail and the record, and the system
    call resets the count and the tail. The verifier is in the block access
    list without changes, and only for the block of the registration.
    """
    predeploy = request_class.system_contract_address
    # Index 1 gives a validator a nonzero last word, so every record slot
    # changes.
    request = request_class.from_index(1).copy(fee=request_class.get_fee(0))
    sender = pre.fund_eoa()
    record = request.with_source_address(sender)
    record_changes = [
        slot_changes(slot, (1, value))
        for slot, value in record_storage(record, 0).items()
    ]
    assert all(change.slot_changes[0].post_value for change in record_changes)

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[
                    Transaction(
                        sender=sender,
                        to=predeploy,
                        value=request.value,
                        data=request.calldata,
                    )
                ],
                header_verify=Header(requests_hash=Requests(record)),
                expected_block_access_list=BlockAccessListExpectation(
                    account_expectations={
                        sender: BalAccountExpectation(
                            nonce_changes=[
                                BalNonceChange(
                                    block_access_index=1, post_nonce=1
                                )
                            ],
                        ),
                        predeploy: BalAccountExpectation(
                            balance_changes=[
                                BalBalanceChange(
                                    block_access_index=1,
                                    post_balance=request.value,
                                )
                            ],
                            storage_reads=[
                                request_class.excess_slot,
                                request_class.queue_head_slot,
                            ],
                            storage_changes=[
                                slot_changes(
                                    request_class.count_slot, (1, 1), (2, 0)
                                ),
                                slot_changes(
                                    request_class.queue_tail_slot,
                                    (1, 1),
                                    (2, 0),
                                ),
                                *record_changes,
                            ],
                        ),
                        Spec.VERIFIER: BalAccountExpectation.empty(),
                    }
                ),
            ),
            Block(
                header_verify=Header(requests_hash=Requests()),
                expected_block_access_list=BlockAccessListExpectation(
                    account_expectations={
                        predeploy: BalAccountExpectation(
                            storage_reads=[
                                request_class.excess_slot,
                                request_class.count_slot,
                                request_class.queue_head_slot,
                                request_class.queue_tail_slot,
                            ],
                            storage_changes=[],
                        ),
                        Spec.VERIFIER: None,
                    }
                ),
            ),
        ],
        post={
            predeploy: Account(
                balance=request.value, storage=record_storage(record, 0)
            )
        },
    )


@with_both_registrations
def test_bal_rejected_registration(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    request_class: PQRequestClass,
) -> None:
    """
    A registration whose proof the verifier rejects reverts after the
    predeploy reads the excess and the count, so it changes nothing, but the
    verifier it called is in the block access list.
    """
    predeploy = request_class.system_contract_address
    request = request_class.from_proof(PROOFS_OF_POSSESSION.wrong_leaf).copy(
        fee=request_class.get_fee(0)
    )
    sender = pre.fund_eoa()

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[
                    Transaction(
                        sender=sender,
                        to=predeploy,
                        value=request.value,
                        data=request.calldata,
                    )
                ],
                header_verify=Header(requests_hash=Requests()),
                expected_block_access_list=BlockAccessListExpectation(
                    account_expectations={
                        predeploy: BalAccountExpectation(
                            balance_changes=[],
                            storage_reads=[
                                request_class.excess_slot,
                                request_class.count_slot,
                                request_class.queue_head_slot,
                                request_class.queue_tail_slot,
                            ],
                            storage_changes=[],
                        ),
                        Spec.VERIFIER: BalAccountExpectation.empty(),
                    }
                ),
            ),
        ],
        # The reverted call returned the fee and wrote nothing.
        post={predeploy: Account(balance=0, storage={})},
    )
