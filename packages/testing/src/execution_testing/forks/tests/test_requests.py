"""Test the request classes each fork defines."""

import pytest

from execution_testing.base_types import Address

from ..forks.eips.bogota.eip_8483 import (
    OTHER_CHAIN_PROOFS_OF_POSSESSION,
    PROOF_OF_POSSESSION_VERIFIER_ADDRESS,
    PROOFS_OF_POSSESSION,
    PQBuilderRegistrationRequest,
    PQRegistrationRequest,
)
from ..forks.forks import Bogota
from ..helpers import ALL_FORKS, get_forks
from ..requests import FeeSystemContractRequest, SystemContractRequest

REQUEST_CLASSES: list[type[SystemContractRequest]] = sorted(
    {
        cls
        for fork in ALL_FORKS
        for cls in fork.system_contract_request_types()
    },
    key=lambda cls: cls.type,
)
QUEUED_REQUEST_CLASSES: list[type[FeeSystemContractRequest]] = [
    cls for cls in REQUEST_CLASSES if issubclass(cls, FeeSystemContractRequest)
]


def test_request_types_are_unique() -> None:
    """Each request class owns one request type byte."""
    types = [cls.type for cls in REQUEST_CLASSES]
    assert types == sorted(types) and len(set(types)) == len(types)


def test_latest_fork_lists_every_request_class() -> None:
    """The newest fork lists every request class any fork defines."""
    assert set(get_forks()[-1].system_contract_request_types()) == set(
        REQUEST_CLASSES
    )


@pytest.mark.parametrize("request_class", QUEUED_REQUEST_CLASSES)
def test_from_index_request_serializes(
    request_class: type[FeeSystemContractRequest],
) -> None:
    """A request built from an index has calldata and request bytes."""
    request = request_class.from_index(1)
    assert len(bytes(request)) > 0
    assert len(request.calldata) > 0
    assert request.value >= request.fee


@pytest.mark.parametrize("request_class", QUEUED_REQUEST_CLASSES)
def test_record_slots_follow_the_queue_layout(
    request_class: type[FeeSystemContractRequest],
) -> None:
    """Records occupy consecutive slot runs from the queue offset."""
    width = request_class.slots_per_request
    assert request_class.record_slots(0, 1) == list(range(4, 4 + width))
    assert request_class.record_slots(2, 2) == list(
        range(4 + 2 * width, 4 + 4 * width)
    )
    assert request_class.empty_block_bal_item_count() == 5


@pytest.mark.parametrize("request_class", QUEUED_REQUEST_CLASSES)
def test_enqueue_fees_by_processing_mode(
    request_class: type[FeeSystemContractRequest],
) -> None:
    """Fees rise within a block only for call-processed queues."""
    target = request_class.target_per_block
    fees = request_class.get_enqueue_fees(target + 3)
    if request_class.excess_fee_processing == "block":
        assert fees == [request_class.get_fee(0)] * (target + 3)
    elif request_class.excess_fee_processing == "call":
        assert fees[: target + 1] == [request_class.get_fee(0)] * (target + 1)
        assert fees[target + 1 :] == [
            request_class.get_fee(1),
            request_class.get_fee(2),
        ]
    else:
        raise ValueError(request_class.excess_fee_processing)


@pytest.mark.parametrize(
    "request_class,calldata_size,record_size",
    [
        pytest.param(PQRegistrationRequest, 2516, 132, id="validator"),
        pytest.param(PQBuilderRegistrationRequest, 2484, 100, id="builder"),
    ],
)
def test_pq_registration_sizes(
    request_class: type[FeeSystemContractRequest],
    calldata_size: int,
    record_size: int,
) -> None:
    """A registration has the calldata and record sizes of its contract."""
    request = request_class.from_index(0)
    assert len(request.calldata) == calldata_size
    assert len(bytes(request)) == record_size


def test_pq_registrations_from_index_differ() -> None:
    """
    Validator registrations from different indices differ, since the index
    is the unsigned part of `pq_data`. Builder registrations differ until the
    proofs repeat.
    """
    proof_count = len(PROOFS_OF_POSSESSION.proofs)
    validators = {
        bytes(PQRegistrationRequest.from_index(i))
        for i in range(2 * proof_count)
    }
    assert len(validators) == 2 * proof_count
    builders = {
        bytes(PQBuilderRegistrationRequest.from_index(i))
        for i in range(proof_count)
    }
    assert len(builders) == proof_count


def test_proofs_of_possession() -> None:
    """
    The proofs are for chain 1, where the tests run, and there are enough to
    fill a block with builder registrations and queue one more.
    """
    assert PROOFS_OF_POSSESSION.chain_id == 1
    assert (
        len(PROOFS_OF_POSSESSION.proofs)
        > PQBuilderRegistrationRequest.max_per_block
    )
    assert OTHER_CHAIN_PROOFS_OF_POSSESSION.chain_id != 1


def test_proof_verifier_is_not_a_system_contract() -> None:
    """
    Bogota pre-allocates the verifier, but only the registration predeploys
    call it.
    """
    assert PROOF_OF_POSSESSION_VERIFIER_ADDRESS in (
        Bogota.pre_allocation_blockchain()
    )
    verifier = Address(PROOF_OF_POSSESSION_VERIFIER_ADDRESS)
    assert verifier not in Bogota.system_contracts()
    assert verifier not in Bogota.system_contract_call_phases()
