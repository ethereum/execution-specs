"""
Tests the end-of-block request system calls when the request contract holds
a delegation designator or no code.

The system call follows a designator as any message call does, per
[EIP-7702: Set EOA account code](https://eips.ethereum.org/EIPS/eip-7702).
A request contract without code makes the block invalid, per
[EIP-7002](https://eips.ethereum.org/EIPS/eip-7002) and
[EIP-7251](https://eips.ethereum.org/EIPS/eip-7251).
"""

from typing import Dict, List, Type

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Block,
    BlockAccessListExpectation,
    BlockchainTestFiller,
    BlockException,
    BuilderDepositRequest,
    BuilderExitRequest,
    ConsolidationRequest,
    FeeSystemContractRequest,
    Fork,
    Header,
    Requests,
    WithdrawalRequest,
)

from ..eip7702_set_code_tx.spec import Spec as Spec7702
from .spec import ref_spec_7685

REFERENCE_SPEC_GIT_PATH: str = ref_spec_7685.git_path
REFERENCE_SPEC_VERSION: str = ref_spec_7685.version

# The request contracts are genesis accounts from Prague on. A designator or
# missing code at one of them is a state that no live chain can reach, so the
# tests change the genesis allocation.
pytestmark: List[pytest.MarkDecorator] = [
    pytest.mark.valid_from("Prague"),
    pytest.mark.pre_alloc_mutable,
]


def counting_bytes(length: int, first: int) -> bytes:
    """Return `length` bytes that count up from `first` and skip zero."""
    return bytes((first + i) % 255 + 1 for i in range(length))


def full_width_request(
    request_class: Type[FeeSystemContractRequest], source: Address
) -> FeeSystemContractRequest:
    """
    Return a request of `request_class` whose fields fill their full width
    with non-zero bytes, so that no word of its queue record is zero.
    """
    amount = int.from_bytes(counting_bytes(8, 200))
    if request_class is WithdrawalRequest:
        return WithdrawalRequest(
            source_address=source,
            validator_pubkey=counting_bytes(48, 0),
            amount=amount,
        )
    elif request_class is ConsolidationRequest:
        return ConsolidationRequest(
            source_address=source,
            source_pubkey=counting_bytes(48, 0),
            target_pubkey=counting_bytes(48, 100),
        )
    elif request_class is BuilderExitRequest:
        return BuilderExitRequest(
            source_address=source, pubkey=counting_bytes(48, 0)
        )
    elif request_class is BuilderDepositRequest:
        return BuilderDepositRequest(
            pubkey=counting_bytes(48, 0),
            withdrawal_credentials=counting_bytes(32, 50),
            amount=amount,
            signature=counting_bytes(96, 100),
        )
    raise ValueError(f"unhandled request class: {request_class.__name__}")


def queued_record_storage(
    request: FeeSystemContractRequest,
) -> Dict[int, int | bytes]:
    """
    Return the storage of `request` as the first record in the queue: the
    source address when the request carries one, then the calldata in
    32-byte words.
    """
    calldata = request.calldata
    values: List[int | bytes] = []
    source_address = getattr(request, "source_address", None)
    if source_address is not None:
        values.append(int.from_bytes(source_address))
    values.extend(
        calldata[i : i + 32].ljust(32, b"\x00")
        for i in range(0, len(calldata), 32)
    )
    return dict(zip(request.record_slots(0, 1), values, strict=True))


@pytest.mark.with_all_system_contract_request_types(
    selector=lambda cls: issubclass(cls, FeeSystemContractRequest)
)
@pytest.mark.parametrize(
    "delegate_code",
    [
        pytest.param("canonical", id="delegate_to_canonical_code"),
        pytest.param("empty", id="delegate_to_empty_account"),
    ],
)
def test_system_contract_with_delegation(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    request_class: Type[FeeSystemContractRequest],
    delegate_code: str,
) -> None:
    """
    Test a request contract whose code is a delegation designator, with one
    request in its queue.

    The system call runs the delegate's code in the storage of the request
    contract.
    """
    system_contract = request_class.system_contract_address
    queued_request = full_width_request(request_class, pre.fund_eoa(amount=0))
    record_storage = queued_record_storage(queued_request)
    queued_storage = {request_class.queue_tail_slot: 1, **record_storage}

    if delegate_code == "canonical":
        canonical_code = fork.pre_allocation_blockchain()[
            int.from_bytes(system_contract)
        ]["code"]
        delegate = pre.deploy_contract(canonical_code)
        # The dequeue empties the queue, which resets the head and tail, and
        # leaves the record slots in place.
        expected_requests = Requests(queued_request)
        post_storage = record_storage
        delegate_post: Account | None = Account(
            code=canonical_code, storage={}
        )
    elif delegate_code == "empty":
        # Alone, this case passes on a client that runs the designator bytes
        # as code and ignores the failed call; the canonical case catches it.
        delegate = pre.fund_eoa(amount=0)
        expected_requests = Requests()
        post_storage = queued_storage
        delegate_post = Account.NONEXISTENT
    else:
        raise ValueError(f"unhandled delegate code: {delegate_code}")

    designator = Spec7702.delegation_designation(delegate)
    pre.update_account(
        system_contract, code=designator, storage=queued_storage
    )

    blockchain_test(
        pre=pre,
        blocks=[Block(header_verify=Header(requests_hash=expected_requests))],
        post={
            system_contract: Account(code=designator, storage=post_storage),
            delegate: delegate_post,
        },
    )


@pytest.mark.with_all_system_contract_request_types(
    selector=lambda cls: issubclass(cls, FeeSystemContractRequest)
)
@pytest.mark.exception_test
def test_system_contract_without_code(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    request_class: Type[FeeSystemContractRequest],
) -> None:
    """
    Test the first block of a chain that starts at the fork without the
    request contract.

    The block is invalid, as in the deployment test where the contract is
    deployed after the fork, but here the chain has no block before the fork.
    """
    system_contract: Address = request_class.system_contract_address
    del pre[system_contract]

    # The transition tool reads an empty system contract's code outside the
    # tracked state, so it leaves the contract out of the block access list.
    # List it; otherwise the list would be a second defect of the block.
    empty_contract_bal: BlockAccessListExpectation | None = None
    if fork.header_bal_hash_required():
        empty_contract_bal = BlockAccessListExpectation().modify(
            lambda bal: bal.with_accounts([system_contract])
        )

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                exception=BlockException.SYSTEM_CONTRACT_EMPTY,
                expected_block_access_list=empty_contract_bal,
            )
        ],
        post={},
        # The chain cannot leave a block without the contract, so the sync
        # block the filler would append cannot execute either.
        sync_block=False,
    )
