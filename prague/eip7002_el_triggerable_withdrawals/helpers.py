"""
Helpers for the EIP-7002 deposit tests.
"""
from dataclasses import dataclass, field
from functools import cached_property
from itertools import count
from typing import Callable, ClassVar, List

from ethereum_test_tools import EOA, Address, Alloc
from ethereum_test_tools import Opcodes as Op
from ethereum_test_tools import Transaction
from ethereum_test_tools import WithdrawalRequest as WithdrawalRequestBase

from .spec import Spec


class WithdrawalRequest(WithdrawalRequestBase):
    """
    Class used to describe a withdrawal request in a test.
    """

    fee: int = 0
    """
    Fee to be paid for the withdrawal request.
    """
    valid: bool = True
    """
    Whether the withdrawal request is valid or not.
    """
    gas_limit: int = 1_000_000
    """
    Gas limit for the call.
    """
    calldata_modifier: Callable[[bytes], bytes] = lambda x: x
    """
    Calldata modifier function.
    """

    interaction_contract_address: ClassVar[Address] = Address(
        Spec.WITHDRAWAL_REQUEST_PREDEPLOY_ADDRESS
    )

    @property
    def value(self) -> int:
        """
        Returns the value of the withdrawal request.
        """
        return self.fee

    @cached_property
    def calldata(self) -> bytes:
        """
        Returns the calldata needed to call the withdrawal request contract and make the
        withdrawal.
        """
        return self.calldata_modifier(
            self.validator_public_key + self.amount.to_bytes(8, byteorder="big")
        )

    def with_source_address(self, source_address: Address) -> "WithdrawalRequest":
        """
        Return a new instance of the withdrawal request with the source address set.
        """
        return self.copy(source_address=source_address)


@dataclass(kw_only=True)
class WithdrawalRequestInteractionBase:
    """
    Base class for all types of withdrawal transactions we want to test.
    """

    sender_balance: int = 32_000_000_000_000_000_000 * 100
    """
    Balance of the account that sends the transaction.
    """
    sender_account: EOA | None = None
    """
    Account that will send the transaction.
    """
    requests: List[WithdrawalRequest]
    """
    Withdrawal request to be included in the block.
    """

    def transactions(self) -> List[Transaction]:
        """Return a transaction for the withdrawal request."""
        raise NotImplementedError

    def update_pre(self, pre: Alloc):
        """Return the pre-state of the account."""
        raise NotImplementedError

    def valid_requests(self, current_minimum_fee: int) -> List[WithdrawalRequest]:
        """Return the list of withdrawal requests that should be valid in the block."""
        raise NotImplementedError


@dataclass(kw_only=True)
class WithdrawalRequestTransaction(WithdrawalRequestInteractionBase):
    """Class used to describe a withdrawal request originated from an externally owned account."""

    def transactions(self) -> List[Transaction]:
        """Return a transaction for the withdrawal request."""
        assert self.sender_account is not None, "Sender account not initialized"
        return [
            Transaction(
                gas_limit=request.gas_limit,
                gas_price=0x07,
                to=request.interaction_contract_address,
                value=request.value,
                data=request.calldata,
                sender=self.sender_account,
            )
            for request in self.requests
        ]

    def update_pre(self, pre: Alloc):
        """Return the pre-state of the account."""
        self.sender_account = pre.fund_eoa(self.sender_balance)

    def valid_requests(self, current_minimum_fee: int) -> List[WithdrawalRequest]:
        """Return the list of withdrawal requests that are valid."""
        assert self.sender_account is not None, "Sender account not initialized"
        return [
            request.with_source_address(self.sender_account)
            for request in self.requests
            if request.valid and request.fee >= current_minimum_fee
        ]


@dataclass(kw_only=True)
class WithdrawalRequestContract(WithdrawalRequestInteractionBase):
    """Class used to describe a deposit originated from a contract."""

    tx_gas_limit: int = 1_000_000
    """
    Gas limit for the transaction.
    """

    contract_balance: int = 32_000_000_000_000_000_000 * 100
    """
    Balance of the contract that will make the call to the pre-deploy contract.
    """
    contract_address: Address | None = None
    """
    Address of the contract that will make the call to the pre-deploy contract.
    """
    entry_address: Address | None = None
    """
    Address to send the transaction to.
    """

    call_type: Op = field(default_factory=lambda: Op.CALL)
    """
    Type of call to be used to make the withdrawal request.
    """
    call_depth: int = 2
    """
    Frame depth of the pre-deploy contract when it executes the call.
    """
    extra_code: bytes = b""
    """
    Extra code to be added to the contract code.
    """

    @property
    def contract_code(self) -> bytes:
        """Contract code used by the relay contract."""
        code = b""
        current_offset = 0
        for r in self.requests:
            value_arg = [r.value] if self.call_type in (Op.CALL, Op.CALLCODE) else []
            code += Op.CALLDATACOPY(0, current_offset, len(r.calldata)) + Op.POP(
                self.call_type(
                    Op.GAS if r.gas_limit == -1 else r.gas_limit,
                    r.interaction_contract_address,
                    *value_arg,
                    0,
                    len(r.calldata),
                    0,
                    0,
                )
            )
            current_offset += len(r.calldata)
        return code + self.extra_code

    def transactions(self) -> List[Transaction]:
        """Return a transaction for the deposit request."""
        assert self.entry_address is not None, "Entry address not initialized"
        return [
            Transaction(
                gas_limit=self.tx_gas_limit,
                gas_price=0x07,
                to=self.entry_address,
                value=0,
                data=b"".join(r.calldata for r in self.requests),
                sender=self.sender_account,
            )
        ]

    def update_pre(self, pre: Alloc):
        """Return the pre-state of the account."""
        self.sender_account = pre.fund_eoa(self.sender_balance)
        self.contract_address = pre.deploy_contract(
            code=self.contract_code, balance=self.contract_balance
        )
        self.entry_address = self.contract_address
        if self.call_depth > 2:
            for _ in range(1, self.call_depth - 1):
                self.entry_address = pre.deploy_contract(
                    code=Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE)
                    + Op.POP(
                        Op.CALL(
                            Op.GAS,
                            self.entry_address,
                            0,
                            0,
                            Op.CALLDATASIZE,
                            0,
                            0,
                        )
                    )
                )

    def valid_requests(self, current_minimum_fee: int) -> List[WithdrawalRequest]:
        """Return the list of withdrawal requests that are valid."""
        assert self.contract_address is not None, "Contract address not initialized"
        return [
            r.with_source_address(self.contract_address)
            for r in self.requests
            if r.valid and r.value >= current_minimum_fee
        ]


def get_n_fee_increments(n: int) -> List[int]:
    """
    Get the first N excess withdrawal requests that increase the fee.
    """
    excess_withdrawal_requests_counts = []
    last_fee = 1
    for i in count(0):
        if Spec.get_fee(i) > last_fee:
            excess_withdrawal_requests_counts.append(i)
            last_fee = Spec.get_fee(i)
        if len(excess_withdrawal_requests_counts) == n:
            break
    return excess_withdrawal_requests_counts


def get_n_fee_increment_blocks(n: int) -> List[List[WithdrawalRequestContract]]:
    """
    Return N blocks that should be included in the test such that each subsequent block has an
    increasing fee for the withdrawal requests.

    This is done by calculating the number of withdrawals required to reach the next fee increment
    and creating a block with that number of withdrawal requests plus the number of withdrawals
    required to reach the target.
    """
    blocks = []
    previous_excess = 0
    withdrawal_index = 0
    previous_fee = 0
    for required_excess_withdrawals in get_n_fee_increments(n):
        withdrawals_required = (
            required_excess_withdrawals
            + Spec.TARGET_WITHDRAWAL_REQUESTS_PER_BLOCK
            - previous_excess
        )
        fee = Spec.get_fee(previous_excess)
        assert fee > previous_fee
        blocks.append(
            [
                WithdrawalRequestContract(
                    requests=[
                        WithdrawalRequest(
                            validator_public_key=i,
                            amount=0,
                            fee=fee,
                        )
                        for i in range(withdrawal_index, withdrawal_index + withdrawals_required)
                    ],
                )
            ],
        )
        previous_fee = fee
        withdrawal_index += withdrawals_required
        previous_excess = required_excess_withdrawals

    return blocks
