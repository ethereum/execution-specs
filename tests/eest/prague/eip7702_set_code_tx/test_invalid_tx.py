"""
abstract: Tests invalid set-code transactions from [EIP-7702: Set EOA account code for one transaction](https://eips.ethereum.org/EIPS/eip-7702)
    Tests invalid set-code transactions from [EIP-7702: Set EOA account code for one transaction](https://eips.ethereum.org/EIPS/eip-7702).
"""  # noqa: E501

from enum import Enum, auto
from typing import List, Type

import pytest

from ethereum_test_base_types import Bytes, FixedSizeBytes, HexNumber
from ethereum_test_tools import (
    Address,
    Alloc,
    AuthorizationTuple,
    Transaction,
    TransactionException,
    TransactionTestFiller,
)

from .spec import Spec, ref_spec_7702

REFERENCE_SPEC_GIT_PATH = ref_spec_7702.git_path
REFERENCE_SPEC_VERSION = ref_spec_7702.version

pytestmark = [pytest.mark.valid_from("Prague"), pytest.mark.exception_test]

auth_account_start_balance = 0


class OversizedInt(FixedSizeBytes[2]):  # type: ignore
    """
    Oversized 2-byte int.

    Will only fail if the int value is less than 2**8.
    """

    pass


class OversizedAddress(FixedSizeBytes[21]):  # type: ignore
    """Oversized Address Type."""

    pass


class UndersizedAddress(FixedSizeBytes[19]):  # type: ignore
    """Undersized Address Type."""

    pass


class InvalidRLPMode(Enum):
    """Enum for invalid RLP modes."""

    TRUNCATED_RLP = auto()
    EXTRA_BYTES = auto()


def test_empty_authorization_list(
    transaction_test: TransactionTestFiller,
    pre: Alloc,
):
    """Test sending a transaction with an empty authorization list."""
    tx = Transaction(
        gas_limit=100_000,
        to=0,
        value=0,
        authorization_list=[],
        error=TransactionException.TYPE_4_EMPTY_AUTHORIZATION_LIST,
        sender=pre.fund_eoa(),
    )
    transaction_test(
        pre=pre,
        tx=tx,
    )


@pytest.mark.parametrize(
    "v,r,s",
    [
        pytest.param(2**8, 1, 1, id="v=2**8"),
        pytest.param(1, 2**256, 1, id="r=2**256"),
        pytest.param(1, 1, 2**256, id="s=2**256"),
        pytest.param(2**8, 2**256, 2**256, id="v=2**8,r=s=2**256"),
    ],
)
@pytest.mark.parametrize(
    "delegate_address",
    [
        pytest.param(Spec.RESET_DELEGATION_ADDRESS, id="reset_delegation_address"),
        pytest.param(Address(1), id="non_zero_address"),
    ],
)
def test_invalid_auth_signature(
    transaction_test: TransactionTestFiller,
    pre: Alloc,
    v: int,
    r: int,
    s: int,
    delegate_address: Address,
):
    """Test sending a transaction where one of the signature elements is out of range."""
    tx = Transaction(
        gas_limit=100_000,
        to=0,
        value=0,
        authorization_list=[
            AuthorizationTuple(
                address=delegate_address,
                nonce=0,
                chain_id=1,
                v=v,
                r=r,
                s=s,
            ),
        ],
        error=[
            TransactionException.TYPE_4_INVALID_AUTHORITY_SIGNATURE,
            TransactionException.TYPE_4_INVALID_AUTHORITY_SIGNATURE_S_TOO_HIGH,
        ],
        sender=pre.fund_eoa(),
    )

    transaction_test(
        pre=pre,
        tx=tx,
    )


@pytest.mark.parametrize(
    "auth_chain_id",
    [
        pytest.param(Spec.MAX_AUTH_CHAIN_ID + 1, id="auth_chain_id=2**256"),
    ],
)
@pytest.mark.parametrize(
    "delegate_address",
    [
        pytest.param(Spec.RESET_DELEGATION_ADDRESS, id="reset_delegation_address"),
        pytest.param(Address(1), id="non_zero_address"),
    ],
)
def test_invalid_tx_invalid_auth_chain_id(
    transaction_test: TransactionTestFiller,
    pre: Alloc,
    auth_chain_id: int,
    delegate_address: Address,
):
    """
    Test sending a transaction where the chain id field of an authorization overflows the
    maximum value.
    """
    authorization = AuthorizationTuple(
        address=delegate_address,
        nonce=0,
        chain_id=auth_chain_id,
        signer=pre.fund_eoa(auth_account_start_balance),
    )

    tx = Transaction(
        gas_limit=100_000,
        to=0,
        value=0,
        authorization_list=[authorization],
        error=TransactionException.TYPE_4_INVALID_AUTHORIZATION_FORMAT,
        sender=pre.fund_eoa(),
    )

    transaction_test(
        pre=pre,
        tx=tx,
    )


@pytest.mark.parametrize(
    "auth_chain_id",
    [pytest.param(0), pytest.param(1)],
)
@pytest.mark.parametrize(
    "delegate_address",
    [
        pytest.param(Spec.RESET_DELEGATION_ADDRESS, id="reset_delegation_address"),
        pytest.param(Address(1), id="non_zero_address"),
    ],
)
def test_invalid_tx_invalid_auth_chain_id_encoding(
    transaction_test: TransactionTestFiller,
    pre: Alloc,
    delegate_address: Address,
    auth_chain_id: int,
):
    """
    Test sending a transaction where the chain id field of an authorization has an incorrect
    encoding.
    """

    class ModifiedAuthorizationTuple(AuthorizationTuple):
        chain_id: OversizedInt  # type: ignore

    authorization = ModifiedAuthorizationTuple(
        address=delegate_address,
        nonce=0,
        chain_id=auth_chain_id,
        signer=pre.fund_eoa(auth_account_start_balance),
    )

    tx = Transaction(
        gas_limit=100_000,
        to=0,
        value=0,
        authorization_list=[authorization],
        error=TransactionException.TYPE_4_INVALID_AUTHORIZATION_FORMAT,
        sender=pre.fund_eoa(),
    )

    transaction_test(
        pre=pre,
        tx=tx,
    )


@pytest.mark.parametrize(
    "nonce",
    [
        pytest.param(Spec.MAX_NONCE + 1, id="nonce=2**64"),
        pytest.param(2**256, id="nonce=2**256"),
    ],
)
@pytest.mark.parametrize(
    "delegate_address",
    [
        pytest.param(Spec.RESET_DELEGATION_ADDRESS, id="reset_delegation_address"),
        pytest.param(Address(1), id="non_zero_address"),
    ],
)
def test_invalid_tx_invalid_nonce(
    transaction_test: TransactionTestFiller,
    pre: Alloc,
    nonce: int,
    delegate_address: Address,
):
    """
    Test sending a transaction where the nonce field of an authorization overflows the maximum
    value.
    """
    auth_signer = pre.fund_eoa()

    tx = Transaction(
        gas_limit=100_000,
        to=0,
        value=0,
        authorization_list=[
            AuthorizationTuple(
                address=delegate_address,
                nonce=nonce,
                signer=auth_signer,
            ),
        ],
        error=TransactionException.TYPE_4_INVALID_AUTHORIZATION_FORMAT,
        sender=pre.fund_eoa(),
    )

    transaction_test(
        pre=pre,
        tx=tx,
    )


@pytest.mark.parametrize(
    "nonce",
    [
        pytest.param([], id="nonce=empty-list"),
        pytest.param([0], id="nonce=non-empty-list"),
        pytest.param([0, 0], id="nonce=multi-element-list"),
    ],
)
@pytest.mark.parametrize(
    "delegate_address",
    [
        pytest.param(Spec.RESET_DELEGATION_ADDRESS, id="reset_delegation_address"),
        pytest.param(Address(1), id="non_zero_address"),
    ],
)
def test_invalid_tx_invalid_nonce_as_list(
    transaction_test: TransactionTestFiller,
    pre: Alloc,
    nonce: List[int],
    delegate_address: Address,
):
    """
    Test sending a transaction where the nonce field of an authorization overflows the maximum
    value.
    """
    auth_signer = pre.fund_eoa()

    class AuthorizationTupleWithNonceAsList(AuthorizationTuple):
        nonce: List[HexNumber]  # type: ignore

    tx = Transaction(
        gas_limit=100_000,
        to=0,
        value=0,
        authorization_list=[
            AuthorizationTupleWithNonceAsList(
                address=delegate_address,
                nonce=nonce,
                signer=auth_signer,
            ),
        ],
        error=TransactionException.TYPE_4_INVALID_AUTHORIZATION_FORMAT,
        sender=pre.fund_eoa(),
    )

    transaction_test(
        pre=pre,
        tx=tx,
    )


@pytest.mark.parametrize(
    "delegate_address",
    [
        pytest.param(Spec.RESET_DELEGATION_ADDRESS, id="reset_delegation_address"),
        pytest.param(Address(1), id="non_zero_address"),
    ],
)
def test_invalid_tx_invalid_nonce_encoding(
    transaction_test: TransactionTestFiller,
    pre: Alloc,
    delegate_address: Address,
):
    """
    Test sending a transaction where the chain id field of an authorization has an incorrect
    encoding.
    """

    class ModifiedAuthorizationTuple(AuthorizationTuple):
        nonce: OversizedInt  # type: ignore

    authorization = ModifiedAuthorizationTuple(
        address=delegate_address,
        nonce=0,
        signer=pre.fund_eoa(auth_account_start_balance),
    )

    tx = Transaction(
        gas_limit=100_000,
        to=0,
        value=0,
        authorization_list=[authorization],
        error=TransactionException.TYPE_4_INVALID_AUTHORIZATION_FORMAT,
        sender=pre.fund_eoa(),
    )

    transaction_test(
        pre=pre,
        tx=tx,
    )


@pytest.mark.parametrize(
    "address_type",
    [
        pytest.param(
            OversizedAddress,
            id="oversized",
        ),
        pytest.param(
            UndersizedAddress,
            id="undersized",
        ),
    ],
)
@pytest.mark.parametrize(
    "delegate_address",
    [
        pytest.param(
            int.from_bytes(Spec.RESET_DELEGATION_ADDRESS, byteorder="big"),
            id="reset_delegation_address",
        ),
        pytest.param(1, id="non_zero_address"),
    ],
)
def test_invalid_tx_invalid_address(
    transaction_test: TransactionTestFiller,
    pre: Alloc,
    delegate_address: int,
    address_type: Type[FixedSizeBytes],
):
    """
    Test sending a transaction where the address field of an authorization is incorrectly
    serialized.
    """
    auth_signer = pre.fund_eoa()

    class ModifiedAuthorizationTuple(AuthorizationTuple):
        address: address_type  # type: ignore

    tx = Transaction(
        gas_limit=100_000,
        to=0,
        value=0,
        authorization_list=[
            ModifiedAuthorizationTuple(
                address=delegate_address,
                nonce=0,
                signer=auth_signer,
            ),
        ],
        error=TransactionException.TYPE_4_INVALID_AUTHORIZATION_FORMAT,
        sender=pre.fund_eoa(),
    )

    transaction_test(
        pre=pre,
        tx=tx,
    )


@pytest.mark.parametrize("extra_element_value", [0, 1])
@pytest.mark.parametrize(
    "delegate_address",
    [
        pytest.param(Spec.RESET_DELEGATION_ADDRESS, id="reset_delegation_address"),
        pytest.param(Address(1), id="non_zero_address"),
    ],
)
def test_invalid_tx_invalid_authorization_tuple_extra_element(
    transaction_test: TransactionTestFiller,
    pre: Alloc,
    delegate_address: Address,
    extra_element_value: int,
):
    """
    Test sending a transaction where the authorization tuple field of the type-4 transaction
    is serialized to contain an extra element.
    """
    auth_signer = pre.fund_eoa()

    class ExtraElementAuthorizationTuple(AuthorizationTuple):
        extra_element: HexNumber  # type: ignore

        def get_rlp_fields(self) -> List[str]:
            """Append the extra field to the list of fields to be encoded in RLP."""
            rlp_fields = super().get_rlp_fields()[:]
            rlp_fields.append("extra_element")
            return rlp_fields

    tx = Transaction(
        gas_limit=100_000,
        to=0,
        value=0,
        authorization_list=[
            ExtraElementAuthorizationTuple(
                address=delegate_address,
                nonce=0,
                signer=auth_signer,
                extra_element=extra_element_value,
            ),
        ],
        error=TransactionException.TYPE_4_INVALID_AUTHORIZATION_FORMAT,
        sender=pre.fund_eoa(),
    )

    transaction_test(
        pre=pre,
        tx=tx,
    )


@pytest.mark.parametrize(
    "missing_index",
    [
        pytest.param(0, id="missing_chain_id"),
        pytest.param(1, id="missing_address"),
        pytest.param(2, id="missing_nonce"),
        pytest.param(3, id="missing_signature_y_parity"),
        pytest.param(4, id="missing_signature_r"),
        pytest.param(5, id="missing_signature_s"),
    ],
)
@pytest.mark.parametrize(
    "delegate_address",
    [
        pytest.param(Spec.RESET_DELEGATION_ADDRESS, id="reset_delegation_address"),
        pytest.param(Address(1), id="non_zero_address"),
    ],
)
def test_invalid_tx_invalid_authorization_tuple_missing_element(
    transaction_test: TransactionTestFiller,
    pre: Alloc,
    delegate_address: Address,
    missing_index: int,
):
    """
    Test sending a transaction where the authorization tuple field of the type-4 transaction
    is serialized to miss one element.
    """
    auth_signer = pre.fund_eoa()

    class MissingElementAuthorizationTuple(AuthorizationTuple):
        missing_element_index: int

        def get_rlp_fields(self) -> List[str]:
            """Remove the field that is specified by the missing element index."""
            rlp_fields = super().get_rlp_fields()[:]
            rlp_fields.pop(self.missing_element_index)
            return rlp_fields

    tx = Transaction(
        gas_limit=100_000,
        to=0,
        value=0,
        authorization_list=[
            MissingElementAuthorizationTuple(
                address=delegate_address,
                nonce=0,
                signer=auth_signer,
                missing_element_index=missing_index,
            ),
        ],
        error=TransactionException.TYPE_4_INVALID_AUTHORIZATION_FORMAT,
        sender=pre.fund_eoa(),
    )

    transaction_test(
        pre=pre,
        tx=tx,
    )


@pytest.mark.parametrize(
    "delegate_address",
    [
        pytest.param(Spec.RESET_DELEGATION_ADDRESS, id="reset_delegation_address"),
        pytest.param(Address(1), id="non_zero_address"),
    ],
)
def test_invalid_tx_invalid_authorization_tuple_encoded_as_bytes(
    transaction_test: TransactionTestFiller,
    pre: Alloc,
    delegate_address: Address,
):
    """
    Test sending a transaction where the authorization tuple field of the type-4 transaction
    is encoded in the outer element as bytes instead of a list of elements.
    """

    class ModifiedTransaction(Transaction):
        authorization_list: List[Bytes] | None  # type: ignore

    auth_signer = pre.fund_eoa()

    authorization_list = AuthorizationTuple(
        address=delegate_address,
        nonce=0,
        signer=auth_signer,
    )
    tx = ModifiedTransaction(
        gas_limit=100_000,
        to=0,
        value=0,
        authorization_list=[authorization_list.rlp()],
        error=TransactionException.TYPE_4_INVALID_AUTHORIZATION_FORMAT,
        sender=pre.fund_eoa(),
    )

    transaction_test(
        pre=pre,
        tx=tx,
    )


@pytest.mark.parametrize(
    "invalid_rlp_mode",
    [
        pytest.param(InvalidRLPMode.TRUNCATED_RLP, id="truncated_rlp"),
        pytest.param(InvalidRLPMode.EXTRA_BYTES, id="extra_bytes"),
    ],
)
@pytest.mark.parametrize(
    "delegate_address",
    [
        pytest.param(Spec.RESET_DELEGATION_ADDRESS, id="reset_delegation_address"),
        pytest.param(Address(1), id="non_zero_address"),
    ],
)
def test_invalid_tx_invalid_rlp_encoding(
    transaction_test: TransactionTestFiller,
    pre: Alloc,
    delegate_address: Address,
    invalid_rlp_mode: InvalidRLPMode,
):
    """
    Test sending a transaction type-4 where the RLP encoding of the transaction is
    invalid.
    """
    auth_signer = pre.fund_eoa()

    tx = Transaction(
        gas_limit=100_000,
        to=0,
        value=0,
        authorization_list=[
            AuthorizationTuple(
                address=delegate_address,
                nonce=0,
                signer=auth_signer,
            )
        ],
        error=TransactionException.TYPE_4_INVALID_AUTHORIZATION_FORMAT,
        sender=pre.fund_eoa(),
    )

    if invalid_rlp_mode == InvalidRLPMode.TRUNCATED_RLP:
        # Truncate the last byte of the RLP encoding
        tx.rlp_override = Bytes(tx.rlp()[:-1])
    elif invalid_rlp_mode == InvalidRLPMode.EXTRA_BYTES:
        # Add an extra byte to the end of the RLP encoding
        tx.rlp_override = Bytes(tx.rlp() + b"\x00")

    transaction_test(
        pre=pre,
        tx=tx,
    )
