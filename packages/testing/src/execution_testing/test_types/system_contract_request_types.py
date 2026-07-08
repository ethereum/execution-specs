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
from typing import Callable, ClassVar, List, Literal, Self, Sequence

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
    excess_fee_processing: ClassVar[Literal["block", "call"]] = "block"
    """When the excess fee is recalculated."""

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
                            cls.from_index(i)
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


# Scratch memory offsets for the out-of-gas measurement, placed above the
# largest supported request calldata so they never overlap the copied calldata.
_MEASURE_TOTAL_SLOT = 0x400
_MEASURE_OVERHEAD_SLOT = 0x420


@dataclass(kw_only=True, frozen=True)
class SystemContractInteractionMeasuredOutOfGasContract(
    SystemContractInteractionContract
):
    """
    Relay-contract interaction that self-measures each request's gas cost and
    forces the requests marked invalid (`valid=False`) out of gas by forwarding
    one gas less than required, independent of the fork's gas schedule.

    Reuses `SystemContractInteractionContract` for the driving transaction and
    pre-state allocation.
    """

    @property
    def contract_code(self) -> Bytecode:
        """
        Build a relay contract that measures, at runtime, the gas each system
        contract request needs, then forces the requests marked invalid out of
        gas by forwarding one gas less than required.

        Like `relay_contract_code`, the contract reads the concatenated request
        calldata from its own calldata. It then issues, in order:

        1. A warm-up call for the first valid request, warming the predeploy
           account and its storage slots so the measurement reflects the warm
           cost.
        2. A measured call for the second valid request, capturing `GAS` around
           the call to record its total cost (CALL base cost + value transfer
           + the gas value stipend + the callee's own consumption).
        3. Full-gas calls for any remaining valid requests.
        4. An overhead probe: a call identical to (2) that forwards only
           minimal gas so the callee runs out, isolating everything except the
           callee's own consumption. Subtracting it from (2) yields the gas
           that must be forwarded for the callee to succeed.
        5. A call for each invalid request forwarding `(total - overhead) - 1`
           gas, one short of the requirement, so it runs out of gas and is not
           enqueued.

        Because steps (2) and (4) use byte-identical op sequences (including a
        same-width gas `PUSH`), every base-opcode cost cancels in the
        subtraction, making the forced out-of-gas independent of the fork's
        gas schedule.

        All requests must share the same calldata length and a non-zero call
        value so the measured overhead applies uniformly to each call.
        """
        valid_indices = [i for i, r in enumerate(self.requests) if r.valid]
        invalid_indices = [
            i for i, r in enumerate(self.requests) if not r.valid
        ]
        assert len(valid_indices) >= 2, (
            "measured_out_of_gas_relay_code needs at least two valid requests"
        )
        assert invalid_indices, (
            "measured_out_of_gas_relay_code needs at least one invalid request"
        )
        assert len({len(r.calldata) for r in self.requests}) == 1, (
            "all requests must share the same calldata length"
        )
        assert all(r.value > 0 for r in self.requests), (
            "all requests must have a non-zero call value"
        )

        offsets: List[int] = []
        current = 0
        for r in self.requests:
            offsets.append(current)
            current += len(r.calldata)

        def issue(
            *,
            index: int,
            gas_argument: Bytecode | Op,
            measure_into: int | None = None,
        ) -> Bytecode:
            r = self.requests[index]
            copy = Op.CALLDATACOPY(0, offsets[index], len(r.calldata))
            call = Op.CALL(
                gas_argument,
                r.interaction_contract_address,
                r.value,
                0,
                len(r.calldata),
                0,
                0,
            )
            if measure_into is None:
                return copy + Op.POP(call)
            return (
                copy
                + Op.GAS
                + call
                + Op.POP
                + Op.GAS
                + Op.SWAP1
                + Op.SUB
                + Op.PUSH2(measure_into)
                + Op.MSTORE
            )

        warmup_index = valid_indices[0]
        probe_index = valid_indices[1]

        code = issue(index=warmup_index, gas_argument=Op.GAS)
        code += issue(
            index=probe_index,
            # Forward all gas using the same PUSH opcode in both calls:
            # Op.GAS and Op.PUSH0 could diverge in gas cost in the future.
            gas_argument=Op.PUSH4[0xFFFFFFFF],
            measure_into=_MEASURE_TOTAL_SLOT,
        )
        for i in valid_indices[2:]:
            code += issue(index=i, gas_argument=Op.GAS)
        # The overhead probe reuses the second valid request so its call value
        # and calldata size (hence CALL base cost) match the total measurement
        # exactly.
        code += issue(
            index=probe_index,
            gas_argument=Op.PUSH4[0],
            measure_into=_MEASURE_OVERHEAD_SLOT,
        )
        forwarded_gas = Op.SUB(
            Op.SUB(
                Op.MLOAD(_MEASURE_TOTAL_SLOT), Op.MLOAD(_MEASURE_OVERHEAD_SLOT)
            ),
            1,
        )
        for i in invalid_indices:
            code += issue(index=i, gas_argument=forwarded_gas)
        return code + self.extra_code
