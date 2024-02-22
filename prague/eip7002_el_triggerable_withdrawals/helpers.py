"""
Helpers for the EIP-7002 deposit tests.
"""
from dataclasses import dataclass, field
from functools import cached_property
from itertools import count
from typing import Callable, ClassVar, Dict, List

from ethereum_test_tools import Account, Address
from ethereum_test_tools import Opcodes as Op
from ethereum_test_tools import (
    TestAddress,
    TestAddress2,
    TestPrivateKey,
    TestPrivateKey2,
    Transaction,
)
from ethereum_test_tools import WithdrawalRequest as WithdrawalRequestBase

from .spec import Spec


@dataclass
class SenderAccount:
    """Test sender account descriptor."""

    address: Address
    key: str


TestAccount1 = SenderAccount(TestAddress, TestPrivateKey)
TestAccount2 = SenderAccount(TestAddress2, TestPrivateKey2)


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
    sender_account: SenderAccount = field(
        default_factory=lambda: SenderAccount(TestAddress, TestPrivateKey)
    )
    """
    Account that will send the transaction.
    """

    def transaction(self, nonce: int) -> Transaction:
        """Return a transaction for the withdrawal request."""
        raise NotImplementedError

    def update_pre(self, base_pre: Dict[Address, Account]):
        """Return the pre-state of the account."""
        raise NotImplementedError

    def valid_requests(self, current_minimum_fee: int) -> List[WithdrawalRequest]:
        """Return the list of withdrawal requests that should be valid in the block."""
        raise NotImplementedError


@dataclass(kw_only=True)
class WithdrawalRequestTransaction(WithdrawalRequestInteractionBase):
    """Class used to describe a withdrawal request originated from an externally owned account."""

    request: WithdrawalRequest
    """
    Withdrawal request to be requested by the transaction.
    """

    def transaction(self, nonce: int) -> Transaction:
        """Return a transaction for the withdrawal request."""
        return Transaction(
            nonce=nonce,
            gas_limit=self.request.gas_limit,
            gas_price=0x07,
            to=self.request.interaction_contract_address,
            value=self.request.value,
            data=self.request.calldata,
            secret_key=self.sender_account.key,
        )

    def update_pre(self, base_pre: Dict[Address, Account]):
        """Return the pre-state of the account."""
        base_pre.update(
            {
                self.sender_account.address: Account(balance=self.sender_balance),
            }
        )

    def valid_requests(self, current_minimum_fee: int) -> List[WithdrawalRequest]:
        """Return the list of withdrawal requests that are valid."""
        if self.request.valid and self.request.fee >= current_minimum_fee:
            return [self.request.with_source_address(self.sender_account.address)]
        return []


@dataclass(kw_only=True)
class WithdrawalRequestContract(WithdrawalRequestInteractionBase):
    """Class used to describe a deposit originated from a contract."""

    request: List[WithdrawalRequest] | WithdrawalRequest
    """
    Withdrawal request or list of withdrawal requests to be requested by the contract.
    """

    tx_gas_limit: int = 1_000_000
    """
    Gas limit for the transaction.
    """

    contract_balance: int = 32_000_000_000_000_000_000 * 100
    """
    Balance of the contract that will make the call to the pre-deploy contract.
    """
    contract_address: int = 0x200
    """
    Address of the contract that will make the call to the pre-deploy contract.
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
    def requests(self) -> List[WithdrawalRequest]:
        """Return the list of withdrawal requests."""
        if not isinstance(self.request, List):
            return [self.request]
        return self.request

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

    def transaction(self, nonce: int) -> Transaction:
        """Return a transaction for the deposit request."""
        return Transaction(
            nonce=nonce,
            gas_limit=self.tx_gas_limit,
            gas_price=0x07,
            to=self.entry_address(),
            value=0,
            data=b"".join(r.calldata for r in self.requests),
            secret_key=self.sender_account.key,
        )

    def entry_address(self) -> Address:
        """Return the address of the contract entry point."""
        if self.call_depth == 2:
            return Address(self.contract_address)
        elif self.call_depth > 2:
            return Address(self.contract_address + self.call_depth - 2)
        raise ValueError("Invalid call depth")

    def extra_contracts(self) -> Dict[Address, Account]:
        """Extra contracts used to simulate call depth."""
        if self.call_depth <= 2:
            return {}
        return {
            Address(self.contract_address + i): Account(
                balance=self.contract_balance,
                code=Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE)
                + Op.POP(
                    Op.CALL(
                        Op.GAS,
                        self.contract_address + i - 1,
                        0,
                        0,
                        Op.CALLDATASIZE,
                        0,
                        0,
                    )
                ),
                nonce=1,
            )
            for i in range(1, self.call_depth - 1)
        }

    def update_pre(self, base_pre: Dict[Address, Account]):
        """Return the pre-state of the account."""
        while Address(self.contract_address) in base_pre:
            self.contract_address += 0x100
        base_pre.update(
            {
                self.sender_account.address: Account(balance=self.sender_balance),
                Address(self.contract_address): Account(
                    balance=self.contract_balance, code=self.contract_code, nonce=1
                ),
            }
        )
        base_pre.update(self.extra_contracts())

    def valid_requests(self, current_minimum_fee: int) -> List[WithdrawalRequest]:
        """Return the list of withdrawal requests that are valid."""
        valid_requests: List[WithdrawalRequest] = []
        for r in self.requests:
            if r.valid and r.value >= current_minimum_fee:
                valid_requests.append(r.with_source_address(Address(self.contract_address)))
        return valid_requests


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
    nonce = count(0)
    withdrawal_index = 0
    previous_fee = 0
    for required_excess_withdrawals in get_n_fee_increments(n):
        withdrawals_required = (
            required_excess_withdrawals
            + Spec.TARGET_WITHDRAWAL_REQUESTS_PER_BLOCK
            - previous_excess
        )
        contract_address = next(nonce)
        fee = Spec.get_fee(previous_excess)
        assert fee > previous_fee
        blocks.append(
            [
                WithdrawalRequestContract(
                    request=[
                        WithdrawalRequest(
                            validator_public_key=i,
                            amount=0,
                            fee=fee,
                        )
                        for i in range(withdrawal_index, withdrawal_index + withdrawals_required)
                    ],
                    # Increment the contract address to avoid overwriting the previous one
                    contract_address=0x200 + (contract_address * 0x100),
                )
            ],
        )
        previous_fee = fee
        withdrawal_index += withdrawals_required
        previous_excess = required_excess_withdrawals

    return blocks
