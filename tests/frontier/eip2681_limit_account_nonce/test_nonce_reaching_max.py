"""
Tests that reaching the maximum account nonce (`2**64 - 1`) during execution
is valid.

Per [EIP-2681](https://eips.ethereum.org/EIPS/eip-2681) only a transaction
whose nonce is `2**64 - 1` is invalid; merely incrementing an account to that
value while executing a transaction is permitted.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    AuthorizationTuple,
    Fork,
    Op,
    StateTestFiller,
    Storage,
    Transaction,
    compute_create_address,
)
from execution_testing.forks import SpuriousDragon

from ...prague.eip7702_set_code_tx.spec import Spec as Spec7702
from .spec import Spec, ref_spec_2681

REFERENCE_SPEC_GIT_PATH = ref_spec_2681.git_path
REFERENCE_SPEC_VERSION = ref_spec_2681.version


@pytest.mark.valid_from("Frontier")
@pytest.mark.pre_alloc_mutable
def test_tx_at_nonce_max_minus_one_call(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Test that a top-level CALL transaction from a sender at the highest usable
    nonce (`2**64 - 2`) executes normally, bumping the sender to the maximum
    nonce (`2**64 - 1`).
    """
    sender = pre.fund_eoa(nonce=Spec.max_nonce - 1)
    to = pre.fund_eoa(amount=0)

    tx = Transaction(
        to=to,
        nonce=Spec.max_nonce - 1,
        sender=sender,
        protected=False,
    )

    state_test(pre=pre, post={sender: Account(nonce=Spec.max_nonce)}, tx=tx)


@pytest.mark.valid_from("Frontier")
@pytest.mark.pre_alloc_mutable
def test_tx_at_nonce_max_minus_one_create(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test that a top-level CREATE transaction from a sender at the highest
    usable nonce (`2**64 - 2`) executes normally, creating a contract and
    bumping the sender to the maximum nonce (`2**64 - 1`).
    """
    sender = pre.fund_eoa(nonce=Spec.max_nonce - 1)

    tx = Transaction(
        to=None,
        nonce=Spec.max_nonce - 1,
        sender=sender,
        protected=False,
    )

    # EIP-161 (Spurious Dragon) initializes a new contract's nonce to 1.
    created_nonce = 1 if fork >= SpuriousDragon else 0
    created = compute_create_address(address=sender, nonce=Spec.max_nonce - 1)

    state_test(
        pre=pre,
        post={
            sender: Account(nonce=Spec.max_nonce),
            created: Account(nonce=created_nonce, code=b""),
        },
        tx=tx,
    )


@pytest.mark.valid_from("Prague")
@pytest.mark.pre_alloc_mutable
def test_set_code_self_authorization_reaching_nonce_max(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Test a self-sponsored set-code transaction whose authorization bumps the
    sender's nonce to the maximum value (`2**64 - 1`).

    The sender starts at nonce `2**64 - 3`. The transaction increments it to
    `2**64 - 2`, then the self-signed authorization (nonce `2**64 - 2`)
    applies and increments it to `2**64 - 1`.
    """
    storage = Storage()
    sender = pre.fund_eoa(nonce=Spec.max_nonce - 2)
    delegate = pre.fund_eoa(amount=0)

    # The transaction targets this contract (not the sender), so its SSTORE
    # proves the top-level call executed.
    set_code_to_address = pre.deploy_contract(
        code=Op.SSTORE(storage.store_next(sender), Op.ORIGIN),
    )

    tx = Transaction(
        to=set_code_to_address,
        authorization_list=[
            AuthorizationTuple(
                address=delegate,
                nonce=Spec.max_nonce - 1,
                signer=sender,
            ),
        ],
        sender=sender,
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            set_code_to_address: Account(storage=storage),
            sender: Account(
                nonce=Spec.max_nonce,
                code=Spec7702.delegation_designation(delegate),
            ),
        },
    )
