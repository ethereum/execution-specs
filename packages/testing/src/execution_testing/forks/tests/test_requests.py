"""Test the request classes each fork defines."""

import pytest

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
