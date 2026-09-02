"""
Execution-layer request types.

`RequestBase` serializes a request to its on-chain bytes and `Requests`
aggregates them into the EIP-7685 requests hash. A `SystemContractRequest`
also knows how to trigger the request through its system contract, and a
`FeeSystemContractRequest` is one whose system contract queues requests and
charges a fee that grows with the per-block excess. Each fork defines its
request classes next to the EIP that introduces them.
"""

from abc import abstractmethod
from collections import defaultdict
from typing import Callable, ClassVar, Dict, List, Literal, Self, SupportsBytes

from execution_testing.base_types import Address, Bytes, CamelModel

from .forks.helpers import fake_exponential


class RequestBase:
    """Base class for requests."""

    type: ClassVar[int]

    @abstractmethod
    def __bytes__(self) -> bytes:
        """Return request's attributes as bytes."""
        ...


class SystemContractRequest(RequestBase, CamelModel):
    """
    Test descriptor for a request triggered by calling a system contract.

    Holds the fields and interface shared by all request types; the concrete
    serialized fields (and the `RequestBase.__bytes__` / `type`) are provided
    by each subclass.
    """

    valid: bool = True
    """Whether the request is expected to be valid and therefore included."""
    calldata_modifier: Callable[[bytes], bytes] = lambda x: x
    """Calldata modifier function applied when building the calldata."""

    system_contract_address: ClassVar[Address]
    """Address of the system contract that processes the request."""

    @property
    @abstractmethod
    def value(self) -> int:
        """Value (in wei) of the call that triggers the request."""
        ...

    @property
    @abstractmethod
    def calldata(self) -> bytes:
        """Calldata of the call that triggers the request."""
        ...

    @abstractmethod
    def with_source_address(self, source_address: Address) -> Self:
        """Return a copy of the request with its source address set."""
        ...

    def set_source_address(self, source_address: Address) -> None:
        """
        Record `source_address` on the request in place, for request types
        that carry one (e.g. withdrawals, consolidations). A no-op for request
        types whose serialized form omits the source (e.g. deposits).
        """
        if "source_address" in type(self).model_fields:
            self.source_address = source_address

    @classmethod
    @abstractmethod
    def from_index(cls, index: int) -> Self:
        """Build a request from a sequential index."""
        ...


class FeeSystemContractRequest(SystemContractRequest):
    """
    A `SystemContractRequest` whose system contract queues the requests for
    the post-execution system call to dequeue, charging a fee that grows
    with the per-block excess request count via `fake_exponential`.

    Subclasses set the contract address, the per-block caps, the fee
    parameters and the record width, and implement `from_index` to build a
    request from a sequential index. The queue storage layout follows the
    EIP-7002 predeploy: excess, count, queue head and queue tail each take a
    slot, and queued records occupy `slots_per_request` consecutive slots
    from `queue_offset` onward.
    """

    fee: int = 0
    """Fee (in wei) paid to the system contract to enqueue the request."""

    max_per_block: ClassVar[int]
    """Maximum number of requests dequeued into a single block."""
    target_per_block: ClassVar[int]
    """Target requests per block; excess above this raises the fee."""
    min_fee: ClassVar[int]
    """Minimum fee, charged when there is no excess."""
    fee_update_fraction: ClassVar[int]
    """Controls how quickly the fee grows with the excess request count."""
    excess_fee_processing: ClassVar[Literal["block", "call"]]
    """When the excess fee is recalculated."""
    slots_per_request: ClassVar[int]
    """Storage slots each queued record occupies."""

    excess_slot: ClassVar[int] = 0
    count_slot: ClassVar[int] = 1
    queue_head_slot: ClassVar[int] = 2
    queue_tail_slot: ClassVar[int] = 3
    queue_offset: ClassVar[int] = 4

    @property
    def value(self) -> int:
        """The value of the triggering call is the fee."""
        return self.fee

    @classmethod
    def get_fee(cls, excess: int) -> int:
        """Return the fee charged for the given excess request count."""
        return fake_exponential(cls.min_fee, excess, cls.fee_update_fraction)

    @classmethod
    def get_excess(cls, previous_excess: int, count: int) -> int:
        """Return the new excess after a block processing `count` requests."""
        return max(0, previous_excess + count - cls.target_per_block)

    @classmethod
    def get_enqueue_fees(cls, count: int) -> List[int]:
        """
        Return the fee each of `count` requests enqueued in one block must pay
        when no excess is stored.

        With "call" processing, requests already queued this block beyond the
        target raise the fee for the next one; with "block" processing the fee
        changes only at the block's system call.
        """
        if cls.excess_fee_processing == "call":
            return [
                cls.get_fee(max(i - cls.target_per_block, 0))
                for i in range(count)
            ]
        elif cls.excess_fee_processing == "block":
            return [cls.get_fee(0)] * count
        raise ValueError(
            f"unhandled fee processing {cls.excess_fee_processing}"
        )

    @classmethod
    def get_n_fee_increments(cls, n: int) -> List[int]:
        """Get the first N excess request counts that increase the fee."""
        excess_request_counts: List[int] = []
        last_fee = 1
        i = 0
        while len(excess_request_counts) < n:
            fee = cls.get_fee(i)
            if fee > last_fee:
                excess_request_counts.append(i)
                last_fee = fee
            i += 1
        return excess_request_counts

    @classmethod
    def empty_block_bal_item_count(cls) -> int:
        """
        Return the block access list items an idle queue adds to a block:
        the contract address plus the excess, count, head and tail slots its
        system call reads.
        """
        return 1 + len(
            {
                cls.excess_slot,
                cls.count_slot,
                cls.queue_head_slot,
                cls.queue_tail_slot,
            }
        )

    @classmethod
    def record_slots(cls, start_index: int, count: int) -> List[int]:
        """Return the slots of `count` queued records from `start_index` on."""
        first = cls.queue_offset + start_index * cls.slots_per_request
        return list(range(first, first + count * cls.slots_per_request))


def requests_list_to_bytes(
    requests_list: List[RequestBase] | Bytes | SupportsBytes,
) -> Bytes:
    """Convert list of requests to bytes."""
    if not isinstance(requests_list, list):
        return Bytes(requests_list)
    return Bytes(b"".join([bytes(r) for r in requests_list]))


class Requests:
    """Requests for the transition tool."""

    requests_list: List[Bytes]

    def __init__(
        self,
        *requests: RequestBase,
        requests_lists: List[List[RequestBase] | Bytes] | None = None,
    ) -> None:
        """Initialize requests object."""
        if requests_lists is not None:
            assert len(requests) == 0, (
                "requests must be empty if list is provided"
            )
            self.requests_list = []
            for requests_list in requests_lists:
                self.requests_list.append(
                    requests_list_to_bytes(requests_list)
                )
            return
        else:
            lists: Dict[int, List[RequestBase]] = defaultdict(list)
            for r in requests:
                lists[r.type].append(r)

            self.requests_list = [
                Bytes(
                    bytes([request_type])
                    + requests_list_to_bytes(lists[request_type])
                )
                for request_type in sorted(lists.keys())
            ]

    def __bytes__(self) -> bytes:
        """Return requests hash."""
        s: bytes = b"".join(r.sha256() for r in self.requests_list)
        return Bytes(s).sha256()
