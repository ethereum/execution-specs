"""
Disable-switch tests for
[EIP-8282: Builder Execution Requests](https://eips.ethereum.org/EIPS/eip-8282).

The builder exit predeploy carries the same reversible kill switch as the
deposit predeploy: while `EXCESS_INHIBITOR` sits in the excess slot, exits
revert, and the next end-of-block system call clears the slot and re-enables
the queue. The disabled state is seeded directly here rather than triggered,
as the protocol's system call never carries the input that sets it.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Block,
    BlockchainTestFiller,
    BuilderExitRequest,
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
    """Seed the builder exit predeploy with the disable inhibitor set."""
    predeploy = Alloc.model_validate(fork.pre_allocation_blockchain())[
        BuilderExitRequest.system_contract_address
    ]
    assert predeploy is not None
    pre[BuilderExitRequest.system_contract_address] = Account(
        nonce=predeploy.nonce,
        code=predeploy.code,
        storage={BuilderExitRequest.excess_slot: Spec.EXCESS_INHIBITOR},
    )
    return pre


def exit_request() -> BuilderExitRequest:
    """Build an exit request paying the zero-excess fee."""
    return BuilderExitRequest(
        pubkey=0x01,
        fee=BuilderExitRequest.get_fee(0),
    )


def test_builder_exit_inhibited(
    blockchain_test: BlockchainTestFiller,
    inhibited_pre: Alloc,
) -> None:
    """
    An exit to an inhibited predeploy reverts and produces no request, the
    end-of-block system call clears the inhibitor back to zero, and an
    identical exit in the next block is queued and dequeued normally.
    """
    rejected = SystemContractInteractionTransaction(
        requests=[exit_request()]
    ).update_pre(inhibited_pre)
    accepted = SystemContractInteractionTransaction(
        requests=[exit_request()]
    ).update_pre(inhibited_pre)

    source_address = accepted.request_source_address
    assert source_address is not None

    # The dequeue advances past the record but does not zero its slots. The
    # exit record is stored as caller ++ pubkey[0:32] ++ pubkey[32:48].
    calldata = exit_request().calldata
    residual_record_slots = {
        BuilderExitRequest.queue_offset: source_address,
        BuilderExitRequest.queue_offset + 1: calldata[0:32],
        BuilderExitRequest.queue_offset + 2: calldata[32:48].ljust(
            32, b"\x00"
        ),
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
                    requests_hash=Requests(
                        *(
                            request.with_source_address(source_address)
                            for request in accepted.requests
                        )
                    )
                ),
            ),
        ],
        post={
            BuilderExitRequest.system_contract_address: Account(
                storage={
                    BuilderExitRequest.excess_slot: 0,
                    **residual_record_slots,
                },
            ),
        },
    )
