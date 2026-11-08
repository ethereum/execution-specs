"""Test the addresses that rejected transactions add to the BAL."""

from execution_testing.base_types import (
    Address,
    TestAddress,
    TestAddress2,
    TestPrivateKey,
    TestPrivateKey2,
)
from execution_testing.test_types import AuthorizationTuple, Transaction

from ..blockchain import rejected_transactions_accessed_addresses


def test_only_rejected_transactions_are_listed() -> None:
    """Test that only the rejected transactions' addresses are returned."""
    accepted = Transaction(
        to=Address(0x100), gas_limit=21_000, secret_key=TestPrivateKey
    ).with_signature_and_sender()
    rejected = Transaction(
        to=Address(0x200), gas_limit=21_000, secret_key=TestPrivateKey2
    ).with_signature_and_sender()

    assert rejected_transactions_accessed_addresses(
        [accepted, rejected], [1]
    ) == [TestAddress2, Address(0x200)]


def test_contract_creation_has_no_recipient() -> None:
    """Test that a contract creation lists only its sender."""
    tx = Transaction(
        to=None, gas_limit=100_000, secret_key=TestPrivateKey
    ).with_signature_and_sender()

    assert rejected_transactions_accessed_addresses([tx], [0]) == [TestAddress]


def test_authorization_authorities_are_listed() -> None:
    """Test that recoverable authorization signers are returned."""
    recovered = AuthorizationTuple(
        address=Address(0x300), secret_key=TestPrivateKey2
    )
    unrecoverable = AuthorizationTuple(address=Address(0x400), v=0, r=0, s=0)
    assert unrecoverable.signer is None
    tx = Transaction(
        to=Address(0x200),
        gas_limit=100_000,
        authorization_list=[recovered, unrecoverable],
        secret_key=TestPrivateKey,
    ).with_signature_and_sender()

    assert rejected_transactions_accessed_addresses([tx], [0]) == [
        TestAddress,
        Address(0x200),
        TestAddress2,
    ]
