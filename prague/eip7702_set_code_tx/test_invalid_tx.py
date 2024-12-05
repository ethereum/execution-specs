"""
abstract: Tests invalid set-code transactions from [EIP-7702: Set EOA account code for one transaction](https://eips.ethereum.org/EIPS/eip-7702)
    Tests invalid set-code transactions from [EIP-7702: Set EOA account code for one transaction](https://eips.ethereum.org/EIPS/eip-7702).
"""  # noqa: E501

from typing import List

import pytest

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

pytestmark = pytest.mark.valid_from("Prague")

auth_account_start_balance = 0


def test_empty_authorization_list(
    transaction_test: TransactionTestFiller,
    pre: Alloc,
):
    """
    Test sending a transaction with an empty authorization list.
    """
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
    """
    Test sending a transaction where one of the signature elements is out of range.
    """
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
    "chain_id",
    [
        pytest.param(Spec.MAX_CHAIN_ID + 1, id="chain_id=2**64"),
        pytest.param(2**256, id="chain_id=2**256"),
    ],
)
@pytest.mark.parametrize(
    "delegate_address",
    [
        pytest.param(Spec.RESET_DELEGATION_ADDRESS, id="reset_delegation_address"),
        pytest.param(Address(1), id="non_zero_address"),
    ],
)
def test_invalid_tx_invalid_chain_id(
    transaction_test: TransactionTestFiller,
    pre: Alloc,
    chain_id: int,
    delegate_address: Address,
):
    """
    Test sending a transaction where the chain id field of an authorization overflows the
    maximum value.
    """
    authorization = AuthorizationTuple(
        address=delegate_address,
        nonce=0,
        chain_id=chain_id,
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
        pytest.param([], id="nonce=empty-list"),
        pytest.param([0], id="nonce=non-empty-list"),
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
    nonce: int | List[int],
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
