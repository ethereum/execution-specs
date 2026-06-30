"""
Test-side descriptors for execution-layer requests triggered via system
contracts.

A `SystemContractRequest` is a `RequestBase` (it serializes to the on-chain
request bytes) that also carries the calldata, value and validity needed to
drive and verify a request from a test. The interaction classes
(`SystemContractInteractionTransaction` / `SystemContractInteractionContract`)
operate on any `SystemContractRequest`, so a single interaction can even mix
request types in one transaction.
"""

from abc import abstractmethod
from dataclasses import dataclass, field, replace
from typing import Any, Callable, ClassVar, List, Self, Sequence

from execution_testing.base_types import Address, CamelModel
from execution_testing.forks.forks.helpers import fake_exponential
from execution_testing.vm import Bytecode, Op

from .account_types import EOA, Alloc
from .request_types import RequestBase
from .transaction_types import Transaction


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

    interaction_contract_address: ClassVar[Address]
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

    @classmethod
    @abstractmethod
    def from_index(cls, index: int, fee: int | None = None) -> Self:
        """Build a request from a sequential index, paying `fee`."""
        ...


class FeeSystemContractRequest(SystemContractRequest):
    """
    A `SystemContractRequest` whose triggering call must pay a fee that grows
    with the per-block excess request count, following the `fake_exponential`
    dynamic shared by EIP-7002, EIP-7251 (and future system contracts).

    Subclasses set `min_fee`, `update_fraction` and `target_per_block`, and
    implement `from_index` to build a request from a sequential index.
    """

    fee: int = 0
    """Fee (in wei) paid to the system contract to enqueue the request."""

    min_fee: ClassVar[int]
    """Minimum fee, charged when there is no excess."""
    update_fraction: ClassVar[int]
    """Controls how quickly the fee grows with the excess request count."""
    target_per_block: ClassVar[int]
    """Target requests per block; excess above this raises the fee."""
    max_per_block: ClassVar[int]
    """Maximum number of requests dequeued into a single block."""

    def model_post_init(self, __context: Any) -> None:
        """Default an unset fee to the base fee (the fee at zero excess)."""
        super().model_post_init(__context)
        if "fee" not in self.model_fields_set:
            self.fee = type(self).get_fee(0)

    @property
    def value(self) -> int:
        """The value of the triggering call is the fee."""
        return self.fee

    @classmethod
    def get_fee(cls, excess: int) -> int:
        """Return the fee charged for the given excess request count."""
        return fake_exponential(cls.min_fee, excess, cls.update_fraction)

    @classmethod
    def get_excess(cls, previous_excess: int, count: int) -> int:
        """Return the new excess after a block processing `count` requests."""
        return max(0, previous_excess + count - cls.target_per_block)

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
    def get_n_fee_increment_blocks(
        cls, n: int
    ) -> List[List["SystemContractInteractionContract"]]:
        """
        Return N blocks such that each subsequent block has an increasing fee
        for the requests.

        Each block contains the number of requests required to reach the next
        fee increment (plus the per-block target), built from sequential
        indices via `from_index` and wrapped in a relay-contract interaction.
        """
        blocks = []
        previous_excess = 0
        request_index = 0
        previous_fee = 0
        for required_excess_requests in cls.get_n_fee_increments(n):
            requests_required = (
                required_excess_requests
                + cls.target_per_block
                - previous_excess
            )
            fee = cls.get_fee(previous_excess)
            assert fee > previous_fee
            blocks.append(
                [
                    SystemContractInteractionContract(
                        requests=[
                            cls.from_index(i, fee)
                            for i in range(
                                request_index,
                                request_index + requests_required,
                            )
                        ],
                    )
                ],
            )
            previous_fee = fee
            request_index += requests_required
            previous_excess = required_excess_requests

        return blocks


def relay_contract_code(
    requests: Sequence[SystemContractRequest],
    *,
    call_type: Op,
    extra_code: Bytecode,
    gas_limits: List[int | None] | None = None,
) -> Bytecode:
    """
    Build the code of a relay contract that issues each request by calling its
    system contract with the request's calldata.

    The contract reads the concatenated request calldata from its own calldata,
    copies each request payload into memory and issues `call_type` to the
    corresponding system contract.

    `gas_limits` is an optional list, aligned with `requests`, that overrides
    the gas forwarded to each inner call. It is only used by the out-of-gas
    test functions; a `None` entry (or omitting the list) forwards all
    available gas via `Op.GAS`.
    """
    if gas_limits is not None:
        assert len(gas_limits) == len(requests), (
            "gas_limits must be aligned with requests"
        )
    code = Bytecode()
    current_offset = 0
    for i, r in enumerate(requests):
        gas_limit = gas_limits[i] if gas_limits is not None else None
        value_arg = [r.value] if call_type in (Op.CALL, Op.CALLCODE) else []
        code += Op.CALLDATACOPY(0, current_offset, len(r.calldata)) + Op.POP(
            call_type(
                Op.GAS if gas_limit is None else gas_limit,
                r.interaction_contract_address,
                *value_arg,
                0,
                len(r.calldata),
                0,
                0,
            )
        )
        current_offset += len(r.calldata)
    return code + extra_code


@dataclass(kw_only=True, frozen=True)
class SystemContractInteractionBase:
    """Base class for all types of request transactions we want to test."""

    sender_account: EOA | None = None
    """Account that sends the transaction."""
    requests: Sequence[SystemContractRequest]
    """Requests to be included in the block."""
    gas_limits: List[int | None] | None = None
    """
    Optional per-request gas overrides, aligned with `requests`. Only set by
    the out-of-gas test functions; left `None` for normal tests so the
    automatic transaction gas-limit (and full inner-call gas) applies.
    """

    @property
    def request_source_address(self) -> Address | None:
        """Address recorded as the source of the requests."""
        raise NotImplementedError

    def transactions(self) -> List[Transaction]:
        """Return the transactions that trigger the requests."""
        raise NotImplementedError

    def update_pre(self, pre: Alloc) -> Self:
        """
        Allocate accounts/contracts in `pre` and return a new instance with
        the allocated state populated. Does not mutate `self`, so the
        parametrize value remains pristine across fixture format runs.
        """
        raise NotImplementedError

    def valid_requests(
        self, current_minimum_fee: int | None = None
    ) -> List[SystemContractRequest]:
        """
        Return the list of requests that should be included in the block.

        `current_minimum_fee` filters out requests whose value is below it
        (e.g. the per-block fee). When `None`, no fee filter is applied and
        every request marked `valid` is returned, trusting the caller to
        ensure each request's value is sufficient.
        """
        source = self.request_source_address
        assert source is not None, "Source address not initialized"
        return [
            r.with_source_address(source)
            for r in self.requests
            if r.valid
            and (current_minimum_fee is None or r.value >= current_minimum_fee)
        ]


@dataclass(kw_only=True, frozen=True)
class SystemContractInteractionTransaction(SystemContractInteractionBase):
    """
    Describe requests originated from an externally owned account, one
    transaction per request.
    """

    @property
    def request_source_address(self) -> Address | None:
        """The sender account is the source of the requests."""
        return self.sender_account

    def transactions(self) -> List[Transaction]:
        """Return one transaction per request."""
        assert self.sender_account is not None, (
            "Sender account not initialized"
        )
        txs: List[Transaction] = []
        for i, request in enumerate(self.requests):
            gas_limit = (
                self.gas_limits[i] if self.gas_limits is not None else None
            )
            txs.append(
                Transaction(
                    gas_limit=gas_limit,
                    to=request.interaction_contract_address,
                    value=request.value,
                    data=request.calldata,
                    sender=self.sender_account,
                )
            )
        return txs

    def update_pre(self, pre: Alloc) -> Self:
        """Return a copy of self with `sender_account` populated."""
        return replace(self, sender_account=pre.fund_eoa())


@dataclass(kw_only=True, frozen=True)
class SystemContractInteractionContract(SystemContractInteractionBase):
    """Describe requests originated from a relay contract."""

    tx_value: int = 0
    """Value to send with the transaction."""

    contract_balance: int | None = None
    """
    Balance of the relay contract that sends the requests. `None` (the
    default) funds the contract with the sum of the request values, which is
    always enough to forward each request's value.
    """
    contract_address: Address | None = None
    """Address of the relay contract that sends the requests."""
    entry_address: Address | None = None
    """Address to send the transaction to."""

    call_type: Op = field(default_factory=lambda: Op.CALL)
    """Type of call to be made to the system contract."""
    call_depth: int = 2
    """Frame depth of the system contract when it processes the requests."""
    extra_code: Bytecode = field(default_factory=Bytecode)
    """Extra code to be included in the relay contract."""

    @property
    def request_source_address(self) -> Address | None:
        """The relay contract is the source of the requests."""
        return self.contract_address

    @property
    def contract_code(self) -> Bytecode:
        """Code used by the relay contract."""
        return relay_contract_code(
            self.requests,
            call_type=self.call_type,
            extra_code=self.extra_code,
            gas_limits=self.gas_limits,
        )

    def transactions(self) -> List[Transaction]:
        """Return the single transaction that drives the relay contract."""
        assert self.entry_address is not None, "Entry address not initialized"
        return [
            Transaction(
                to=self.entry_address,
                value=self.tx_value,
                data=b"".join(r.calldata for r in self.requests),
                sender=self.sender_account,
            )
        ]

    def update_pre(self, pre: Alloc) -> Self:
        """
        Return a copy of self with the allocated sender/contract/entry
        addresses populated.
        """
        sender_account = pre.fund_eoa()
        contract_balance = (
            self.contract_balance
            if self.contract_balance is not None
            else sum(r.value for r in self.requests)
        )
        contract_address = pre.deploy_contract(
            code=self.contract_code, balance=contract_balance
        )
        entry_address = contract_address
        if self.call_depth > 2:
            for _ in range(1, self.call_depth - 1):
                entry_address = pre.deploy_contract(
                    code=Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE)
                    + Op.POP(
                        Op.CALL(
                            Op.GAS,
                            entry_address,
                            0,
                            0,
                            Op.CALLDATASIZE,
                            0,
                            0,
                        )
                    ),
                )
        return replace(
            self,
            sender_account=sender_account,
            contract_address=contract_address,
            entry_address=entry_address,
        )
