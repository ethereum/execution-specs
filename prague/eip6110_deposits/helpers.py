"""
Helpers for the EIP-6110 deposit tests.
"""
from dataclasses import dataclass, field
from functools import cached_property
from hashlib import sha256 as sha256_hashlib
from typing import Callable, ClassVar, Dict, List

from ethereum_test_tools import Account, Address
from ethereum_test_tools import DepositRequest as DepositRequestBase
from ethereum_test_tools import Hash
from ethereum_test_tools import Opcodes as Op
from ethereum_test_tools import (
    TestAddress,
    TestAddress2,
    TestPrivateKey,
    TestPrivateKey2,
    Transaction,
)

from .spec import Spec


def sha256(*args: bytes) -> bytes:
    """
    Returns the sha256 hash of the input.
    """
    return sha256_hashlib(b"".join(args)).digest()


@dataclass
class SenderAccount:
    """Test sender account descriptor."""

    address: Address
    key: str


TestAccount1 = SenderAccount(TestAddress, TestPrivateKey)
TestAccount2 = SenderAccount(TestAddress2, TestPrivateKey2)


class DepositRequest(DepositRequestBase):
    """Deposit request descriptor."""

    valid: bool = True
    """
    Whether the deposit request is valid or not.
    """
    gas_limit: int = 1_000_000
    """
    Gas limit for the call.
    """
    calldata_modifier: Callable[[bytes], bytes] = lambda x: x
    """
    Calldata modifier function.
    """

    interaction_contract_address: ClassVar[Address] = Address(Spec.DEPOSIT_CONTRACT_ADDRESS)

    @cached_property
    def value(self) -> int:
        """
        Returns the value of the deposit transaction.
        """
        return self.amount * 10**9

    @cached_property
    def deposit_data_root(self) -> Hash:
        """
        Returns the deposit data root of the deposit.
        """
        pubkey_root = sha256(self.pubkey, b"\x00" * 16)
        signature_root = sha256(
            sha256(self.signature[:64]), sha256(self.signature[64:], b"\x00" * 32)
        )
        pubkey_withdrawal_root = sha256(pubkey_root, self.withdrawal_credentials)
        amount_bytes = (self.amount).to_bytes(32, byteorder="little")
        amount_signature_root = sha256(amount_bytes, signature_root)
        return Hash(sha256(pubkey_withdrawal_root, amount_signature_root))

    @cached_property
    def calldata(self) -> bytes:
        """
        Returns the calldata needed to call the beacon chain deposit contract and make the deposit.

        deposit(
            bytes calldata pubkey,
            bytes calldata withdrawal_credentials,
            bytes calldata signature,
            bytes32 deposit_data_root
        )
        """
        offset_length = 32
        pubkey_offset = offset_length * 3 + len(self.deposit_data_root)
        withdrawal_offset = pubkey_offset + offset_length + len(self.pubkey)
        signature_offset = withdrawal_offset + offset_length + len(self.withdrawal_credentials)
        return self.calldata_modifier(
            b"\x22\x89\x51\x18"
            + pubkey_offset.to_bytes(offset_length, byteorder="big")
            + withdrawal_offset.to_bytes(offset_length, byteorder="big")
            + signature_offset.to_bytes(offset_length, byteorder="big")
            + self.deposit_data_root
            + len(self.pubkey).to_bytes(offset_length, byteorder="big")
            + self.pubkey
            + len(self.withdrawal_credentials).to_bytes(offset_length, byteorder="big")
            + self.withdrawal_credentials
            + len(self.signature).to_bytes(offset_length, byteorder="big")
            + self.signature
        )


@dataclass(kw_only=True)
class DepositInteractionBase:
    """
    Base class for all types of deposit transactions we want to test.
    """

    sender_balance: int = 32_000_000_000_000_000_000 * 100
    """
    Balance of the account that sends the transaction.
    """
    sender_account: SenderAccount = field(
        default_factory=lambda: SenderAccount(TestAddress, TestPrivateKey)
    )
    """
    Account that sends the transaction.
    """

    def transaction(self, nonce: int) -> Transaction:
        """Return a transaction for the deposit request."""
        raise NotImplementedError

    def update_pre(self, base_pre: Dict[Address, Account]):
        """Return the pre-state of the account."""
        raise NotImplementedError

    def valid_requests(self, current_minimum_fee: int) -> List[DepositRequest]:
        """Return the list of deposit requests that should be included in the block."""
        raise NotImplementedError


@dataclass(kw_only=True)
class DepositTransaction(DepositInteractionBase):
    """Class used to describe a deposit originated from an externally owned account."""

    request: DepositRequest
    """
    Deposit request to be included in the block.
    """

    def transaction(self, nonce: int) -> Transaction:
        """Return a transaction for the deposit request."""
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

    def valid_requests(self, current_minimum_fee: int) -> List[DepositRequest]:
        """Return the list of deposit requests that should be included in the block."""
        return (
            [self.request]
            if self.request.valid and self.request.value >= current_minimum_fee
            else []
        )


@dataclass(kw_only=True)
class DepositContract(DepositInteractionBase):
    """Class used to describe a deposit originated from a contract."""

    request: List[DepositRequest] | DepositRequest
    """
    Deposit request or list of deposit requests to send from the contract.
    """

    tx_gas_limit: int = 1_000_000
    """
    Gas limit for the transaction.
    """

    contract_balance: int = 32_000_000_000_000_000_000 * 100
    """
    Balance of the contract that sends the deposit requests.
    """
    contract_address: int = 0x200
    """
    Address of the contract that sends the deposit requests.
    """

    call_type: Op = field(default_factory=lambda: Op.CALL)
    """
    Type of call to be made to the deposit contract.
    """
    call_depth: int = 2
    """
    Frame depth of the beacon chain deposit contract when it executes the deposit requests.
    """
    extra_code: bytes = b""
    """
    Extra code to be included in the contract that sends the deposit requests.
    """

    @property
    def requests(self) -> List[DepositRequest]:
        """Return the list of deposit requests."""
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

    def valid_requests(self, current_minimum_fee: int) -> List[DepositRequest]:
        """Return the list of deposit requests that should be included in the block."""
        return [d for d in self.requests if d.valid and d.value >= current_minimum_fee]
