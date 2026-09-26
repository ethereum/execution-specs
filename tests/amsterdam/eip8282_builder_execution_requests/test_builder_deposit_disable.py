"""
Disable-switch tests for
[EIP-8282: Builder Execution Requests](https://eips.ethereum.org/EIPS/eip-8282).

The builder deposit predeploy carries a reversible kill switch: while
`EXCESS_INHIBITOR` sits in the excess slot, deposits revert, and the next
end-of-block system call clears the slot and re-enables the queue (the system
call sets the inhibitor only when it carries input, which the protocol never
sends, so absent a fork that appends calldata the disabled state always lasts
exactly until the end of the block). The disabled state is therefore seeded
directly here rather than triggered.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Block,
    BlockchainTestFiller,
    BuilderDepositRequest,
    Fork,
    Header,
    Requests,
    SystemContractInteractionTransaction,
)

from .spec import Spec, ref_spec_8282

REFERENCE_SPEC_GIT_PATH = ref_spec_8282.git_path
REFERENCE_SPEC_VERSION = ref_spec_8282.version

pytestmark = [
    pytest.mark.valid_from("Amsterdam"),
    pytest.mark.pre_alloc_mutable(),
]


@pytest.fixture
def inhibited_pre(pre: Alloc, fork: Fork) -> Alloc:
    """Seed the builder deposit predeploy with the disable inhibitor set."""
    predeploy = Alloc.model_validate(fork.pre_allocation_blockchain())[
        BuilderDepositRequest.system_contract_address
    ]
    assert predeploy is not None
    pre[BuilderDepositRequest.system_contract_address] = Account(
        nonce=predeploy.nonce,
        code=predeploy.code,
        storage={BuilderDepositRequest.excess_slot: Spec.EXCESS_INHIBITOR},
    )
    return pre


def deposit_request() -> BuilderDepositRequest:
    """Build a minimum-stake deposit request paying the zero-excess fee."""
    return BuilderDepositRequest(
        pubkey=0x01,
        withdrawal_credentials=0x02,
        amount=BuilderDepositRequest.min_deposit_wei // 10**9,
        signature=0x03,
        fee=BuilderDepositRequest.get_fee(0),
    )


def test_builder_deposit_inhibited(
    blockchain_test: BlockchainTestFiller,
    inhibited_pre: Alloc,
) -> None:
    """
    A deposit to an inhibited predeploy reverts and produces no request, the
    end-of-block system call clears the inhibitor back to zero, and an
    identical deposit in the next block is queued and dequeued normally.
    """
    rejected = SystemContractInteractionTransaction(
        requests=[deposit_request()]
    ).update_pre(inhibited_pre)
    accepted = SystemContractInteractionTransaction(
        requests=[deposit_request()]
    ).update_pre(inhibited_pre)

    # The dequeue advances past the record but does not zero its slots, so
    # the accepted request's calldata words remain in the queue's storage.
    calldata = deposit_request().calldata
    residual_record_slots = {
        BuilderDepositRequest.queue_offset + i: calldata[
            i * 32 : (i + 1) * 32
        ].ljust(32, b"\x00")
        for i in range((len(calldata) + 31) // 32)
    }

    blockchain_test(
        pre=inhibited_pre,
        blocks=[
            Block(
                txs=rejected.transactions(),
                header_verify=Header(requests_hash=Requests()),
            ),
            Block(
                txs=accepted.transactions(),
                header_verify=Header(
                    requests_hash=Requests(*accepted.requests)
                ),
            ),
        ],
        post={
            BuilderDepositRequest.system_contract_address: Account(
                storage={
                    BuilderDepositRequest.excess_slot: 0,
                    **residual_record_slots,
                },
            ),
        },
    )
