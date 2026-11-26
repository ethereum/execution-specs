"""
Fork-transition tests for
[EIP-8483: Post-Quantum Material Registration](https://eips.ethereum.org/EIPS/eip-8483).
"""

from typing import Dict, List

import pytest
from execution_testing import (
    EOA,
    Account,
    Address,
    Alloc,
    Block,
    BlockchainTestFiller,
    EIPChecklist,
    FeeSystemContractRequest,
    Header,
    PQBuilderRegistrationRequest,
    PQRegistrationRequest,
    Requests,
    SystemContractInteractionTransaction,
    Transaction,
    TransitionFork,
)

from .helpers import deploy_fee_getter, record_storage
from .spec import Spec, ref_spec_8483

REFERENCE_SPEC_GIT_PATH = ref_spec_8483.git_path
REFERENCE_SPEC_VERSION = ref_spec_8483.version

REQUEST_CLASSES: List[type[FeeSystemContractRequest]] = [
    PQRegistrationRequest,
    PQBuilderRegistrationRequest,
]


@pytest.mark.valid_at_transition_to("Bogota")
@pytest.mark.pre_alloc_mutable
@EIPChecklist.SystemContract.Test.ForkTransition.CallBeforeFork()
def test_registrations_during_fork(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: TransitionFork,
) -> None:
    """
    Registrations sent before the fork pay the constructor's fixed fee and
    stay queued, since no system call runs before it. The fork block's system
    call returns them in order with the fork block's own, and from the next
    block on a registration pays the dynamic fee.

    Until the addresses are final the predeploys can't be deployed through
    the EIP-7997 factory, so the test stores the constructor's excess in the
    genesis accounts.
    """
    senders: Dict[type[FeeSystemContractRequest], EOA] = {}
    # One registration per block for each class: three at the fixed fee,
    # the last at the minimum dynamic fee.
    registrations: Dict[
        type[FeeSystemContractRequest], List[FeeSystemContractRequest]
    ] = {}
    for request_class in REQUEST_CLASSES:
        predeploy = request_class.system_contract_address
        assert pre[predeploy] is not None, "the genesis allocates Bogota's"
        pre.update_account(
            predeploy,
            storage={request_class.excess_slot: Spec.EXCESS_PRE_FORK},
        )
        senders[request_class] = pre.fund_eoa()
        registrations[request_class] = [
            request_class.from_index(i)
            .copy(fee=Spec.PRE_FORK_FEE)
            .with_source_address(senders[request_class])
            for i in range(3)
        ] + [
            request_class.from_index(3)
            .copy(fee=request_class.get_fee(0))
            .with_source_address(senders[request_class])
        ]

    def registration_transactions(index: int) -> List[Transaction]:
        return [
            tx
            for request_class in REQUEST_CLASSES
            for tx in SystemContractInteractionTransaction(
                sender_account=senders[request_class],
                requests=[registrations[request_class][index]],
            ).transactions()
        ]

    getters = {}
    getter_storage = {}
    for request_class in REQUEST_CLASSES:
        for when, fee in (
            ("pre_fork", Spec.PRE_FORK_FEE),
            ("post_fork", request_class.get_fee(0)),
        ):
            getter, storage = deploy_fee_getter(
                pre, request_class.system_contract_address, fee
            )
            getters[request_class, when] = getter
            getter_storage[getter] = storage
    getter_sender = pre.fund_eoa()

    def getter_transactions(when: str) -> List[Transaction]:
        return [
            Transaction(sender=getter_sender, to=getters[request_class, when])
            for request_class in REQUEST_CLASSES
        ]

    blocks = [
        Block(
            timestamp=fork.at_timestamp - 2,
            txs=getter_transactions("pre_fork") + registration_transactions(0),
            header_verify=Header(requests_hash=Requests()),
        ),
        Block(
            timestamp=fork.at_timestamp - 1,
            txs=registration_transactions(1),
            header_verify=Header(requests_hash=Requests()),
        ),
        Block(
            timestamp=fork.at_timestamp,
            txs=registration_transactions(2),
            header_verify=Header(
                requests_hash=Requests(
                    *(
                        record
                        for request_class in REQUEST_CLASSES
                        for record in registrations[request_class][:3]
                    )
                )
            ),
        ),
        Block(
            timestamp=fork.at_timestamp + 1,
            txs=getter_transactions("post_fork")
            + registration_transactions(3),
            header_verify=Header(
                requests_hash=Requests(
                    *(
                        registrations[request_class][3]
                        for request_class in REQUEST_CLASSES
                    )
                )
            ),
        ),
        Block(
            timestamp=fork.at_timestamp + 2,
            header_verify=Header(requests_hash=Requests()),
        ),
    ]

    post: Dict[Address, Account] = {
        getter: Account(storage=storage)
        for getter, storage in getter_storage.items()
    }
    for request_class in REQUEST_CLASSES:
        records = registrations[request_class]
        # The fork block emptied the queue, so the last registration took the
        # first item's slots again, and the excess and count are zero.
        post[request_class.system_contract_address] = Account(
            balance=sum(record.value for record in records),
            storage=record_storage(records[1], 1)
            | record_storage(records[2], 2)
            | record_storage(records[3], 0),
        )

    blockchain_test(pre=pre, blocks=blocks, post=post)
