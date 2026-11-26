"""
Tests of the values the excess slot holds when it isn't an excess, for
[EIP-8483: Post-Quantum Material Registration](https://eips.ethereum.org/EIPS/eip-8483).

`EXCESS_INHIBITOR` disables the queue, and `EXCESS_PRE_FORK`, which the
constructor stores, charges a fixed fee until the first system call. Either
way the next system call starts again from a zero excess.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Block,
    BlockchainTestFiller,
    EIPChecklist,
    FeeSystemContractRequest,
    Header,
    Requests,
    Transaction,
)

from .helpers import (
    call_results_relay,
    deploy_fee_getter,
    record_storage,
    with_both_registrations,
)
from .spec import Spec, ref_spec_8483

REFERENCE_SPEC_GIT_PATH = ref_spec_8483.git_path
REFERENCE_SPEC_VERSION = ref_spec_8483.version

pytestmark = [
    pytest.mark.valid_from("Bogota"),
    pytest.mark.pre_alloc_mutable,
]


def stale_count(request_class: type[FeeSystemContractRequest]) -> int:
    """
    Return a request count high enough that, if the system call kept it or
    added it to the excess, the next block's fee would be above the minimum.
    """
    return (
        request_class.target_per_block
        + request_class.get_n_fee_increments(1)[0]
    )


@with_both_registrations
def test_inhibitor_disables_registrations(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    request_class: type[FeeSystemContractRequest],
) -> None:
    """
    While the excess slot holds the inhibitor, a registration reverts. The
    system call zeroes the excess and the count, and a registration paying
    the minimum fee is accepted in the next block.
    """
    predeploy = request_class.system_contract_address
    pre.update_account(
        predeploy,
        storage={
            request_class.excess_slot: Spec.EXCESS_INHIBITOR,
            request_class.count_slot: stale_count(request_class),
        },
    )
    fee = request_class.get_fee(0)
    inhibited = request_class.from_index(0).copy(fee=fee)
    enabled = request_class.from_index(1).copy(fee=fee)
    inhibited_relay, inhibited_data, inhibited_storage = call_results_relay(
        pre, [(predeploy, inhibited.calldata, fee, False)]
    )
    enabled_relay, enabled_data, enabled_storage = call_results_relay(
        pre, [(predeploy, enabled.calldata, fee, True)]
    )
    record = enabled.with_source_address(enabled_relay)
    sender = pre.fund_eoa()

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[
                    Transaction(
                        sender=sender, to=inhibited_relay, data=inhibited_data
                    )
                ],
                header_verify=Header(requests_hash=Requests()),
            ),
            Block(
                txs=[
                    Transaction(
                        sender=sender, to=enabled_relay, data=enabled_data
                    )
                ],
                header_verify=Header(requests_hash=Requests(record)),
            ),
        ],
        # The excess and the count are back to zero, so only the record's
        # slots hold values.
        post={
            inhibited_relay: Account(storage=inhibited_storage),
            enabled_relay: Account(storage=enabled_storage),
            predeploy: Account(balance=fee, storage=record_storage(record, 0)),
        },
    )


@with_both_registrations
@EIPChecklist.SystemContract.Test.ValueTransfer.Fee.Under()
@EIPChecklist.SystemContract.Test.ValueTransfer.Fee.Exact()
@EIPChecklist.SystemContract.Test.InputLengths.Zero()
def test_pre_fork_fee(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    request_class: type[FeeSystemContractRequest],
) -> None:
    """
    While the excess slot holds the constructor's value, the fee getter
    returns the fixed pre-fork fee and a registration must pay it, however
    many were made before. The system call then starts the dynamic fee from
    a zero excess, without counting them.
    """
    predeploy = request_class.system_contract_address
    pre.update_account(
        predeploy,
        storage={
            request_class.excess_slot: Spec.EXCESS_PRE_FORK,
            request_class.count_slot: stale_count(request_class),
        },
    )
    min_fee = request_class.get_fee(0)
    underpaid = request_class.from_index(0).copy(fee=Spec.PRE_FORK_FEE - 1)
    pre_fork = [
        request_class.from_index(i).copy(fee=Spec.PRE_FORK_FEE) for i in (1, 2)
    ]
    post_fork = request_class.from_index(3).copy(fee=min_fee)

    pre_fork_getter, pre_fork_getter_storage = deploy_fee_getter(
        pre, predeploy, Spec.PRE_FORK_FEE
    )
    pre_fork_relay, pre_fork_data, pre_fork_relay_storage = call_results_relay(
        pre,
        [
            (predeploy, underpaid.calldata, underpaid.value, False),
            *(
                (predeploy, request.calldata, request.value, True)
                for request in pre_fork
            ),
        ],
    )
    post_fork_getter, post_fork_getter_storage = deploy_fee_getter(
        pre, predeploy, min_fee
    )
    post_fork_relay, post_fork_data, post_fork_relay_storage = (
        call_results_relay(
            pre, [(predeploy, post_fork.calldata, post_fork.value, True)]
        )
    )
    pre_fork_records = [
        request.with_source_address(pre_fork_relay) for request in pre_fork
    ]
    post_fork_record = post_fork.with_source_address(post_fork_relay)
    sender = pre.fund_eoa()

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[
                    Transaction(sender=sender, to=pre_fork_getter),
                    Transaction(
                        sender=sender, to=pre_fork_relay, data=pre_fork_data
                    ),
                ],
                header_verify=Header(
                    requests_hash=Requests(*pre_fork_records)
                ),
            ),
            Block(
                txs=[
                    Transaction(sender=sender, to=post_fork_getter),
                    Transaction(
                        sender=sender,
                        to=post_fork_relay,
                        data=post_fork_data,
                    ),
                ],
                header_verify=Header(requests_hash=Requests(post_fork_record)),
            ),
        ],
        post={
            pre_fork_getter: Account(storage=pre_fork_getter_storage),
            pre_fork_relay: Account(storage=pre_fork_relay_storage),
            post_fork_getter: Account(storage=post_fork_getter_storage),
            post_fork_relay: Account(storage=post_fork_relay_storage),
            # The queue emptied after the first block, so the post-fork
            # record took the first item's slots again.
            predeploy: Account(
                balance=2 * Spec.PRE_FORK_FEE + min_fee,
                storage=record_storage(pre_fork_records[1], 1)
                | record_storage(post_fork_record, 0),
            ),
        },
    )
