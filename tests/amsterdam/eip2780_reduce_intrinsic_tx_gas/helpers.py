"""Shared helpers for EIP-2780 tests."""

from dataclasses import dataclass
from enum import Enum, auto

from execution_testing import (
    EOA,
    AccessList,
    Account,
    Address,
    Alloc,
    AuthorizationTuple,
    Fork,
    Op,
    RecipientType,
)

from ...prague.eip7702_set_code_tx.spec import Spec as Spec7702

EOA_INITIAL_BALANCE = 1
NULL_ADDRESS = Address(0)

RECIPIENT_TYPES_NON_CREATE = [
    RecipientType.EOA,
    RecipientType.CONTRACT,
    RecipientType.EMPTY_ACCOUNT,
    RecipientType.SELF,
    RecipientType.DELEGATION_7702,
]


class AuthorizationAction(Enum):
    """The action an EIP-7702 authorization performs on its authority."""

    CREATES_ACCOUNT = auto()
    SETS_NEW_DELEGATION = auto()
    SETS_DIFFERENT_DELEGATION = auto()
    SETS_SAME_DELEGATION = auto()
    CLEARS_DELEGATION = auto()
    INVALID = auto()


@dataclass
class AuthorizationScenario:
    """
    An EIP-7702 authorization together with the authority it acts on and
    that authority's account before and after the authorization applies.

    ``applied_account`` is the authority's post-state once
    ``set_delegation`` runs the authorization; ``original_account`` is
    its pre-transaction state (``None`` when the leaf does not yet
    exist), used to assert the authority is untouched when the
    authorization is rolled back or skipped.
    """

    authority: EOA
    authorization: AuthorizationTuple
    applied_account: Account
    original_account: Account | None


def build_authorization(
    pre: Alloc,
    action: AuthorizationAction,
    *,
    balance: int = EOA_INITIAL_BALANCE,
) -> AuthorizationScenario:
    """
    Fund an authority in the pre-state and build an authorization acting
    on it for the given ``action``, annotated with the
    ``creates_account`` / ``writes_delegation`` / ``first_write`` flags
    the top-frame calculators consume.

    The authority is always a third party (never ``tx.to`` or the
    sender), so every valid action is the transaction's first write to
    it and ``first_write`` keeps its ``True`` default; only ``INVALID``
    (never applied) clears it. Delegation targets are freshly deployed
    and referenced by the returned accounts, so callers need only
    assert against ``applied_account`` / ``original_account``.
    """
    designation = Spec7702.delegation_designation

    match action:
        case AuthorizationAction.CREATES_ACCOUNT:
            target = pre.deploy_contract(code=Op.STOP)
            authority = pre.fund_eoa(amount=0)
            authorization = AuthorizationTuple(
                address=target,
                nonce=0,
                signer=authority,
                creates_account=True,
            )
            applied = Account(nonce=1, balance=0, code=designation(target))
            original = None
        case AuthorizationAction.SETS_NEW_DELEGATION:
            target = pre.deploy_contract(code=Op.STOP)
            assert balance > 0, (
                "An existing account must have non-zero balance"
            )
            authority = pre.fund_eoa(amount=balance)
            authorization = AuthorizationTuple(
                address=target,
                nonce=0,
                signer=authority,
                creates_account=False,
            )
            applied = Account(
                nonce=1, balance=balance, code=designation(target)
            )
            original = Account(nonce=0, balance=balance, code=b"")
        case AuthorizationAction.SETS_DIFFERENT_DELEGATION:
            old_target = pre.deploy_contract(code=Op.STOP)
            new_target = pre.deploy_contract(code=Op.STOP)
            authority = pre.fund_eoa(amount=balance, delegation=old_target)
            authorization = AuthorizationTuple(
                address=new_target,
                nonce=1,
                signer=authority,
                creates_account=False,
                writes_delegation=False,
            )
            applied = Account(
                nonce=2, balance=balance, code=designation(new_target)
            )
            original = Account(
                nonce=1, balance=balance, code=designation(old_target)
            )
        case AuthorizationAction.SETS_SAME_DELEGATION:
            target = pre.deploy_contract(code=Op.STOP)
            authority = pre.fund_eoa(amount=balance, delegation=target)
            authorization = AuthorizationTuple(
                address=target,
                nonce=1,
                signer=authority,
                creates_account=False,
                writes_delegation=False,
            )
            applied = Account(
                nonce=2, balance=balance, code=designation(target)
            )
            original = Account(
                nonce=1, balance=balance, code=designation(target)
            )
        case AuthorizationAction.CLEARS_DELEGATION:
            target = pre.deploy_contract(code=Op.STOP)
            authority = pre.fund_eoa(amount=balance, delegation=target)
            authorization = AuthorizationTuple(
                address=NULL_ADDRESS,
                nonce=1,
                signer=authority,
                creates_account=False,
                writes_delegation=False,
            )
            applied = Account(nonce=2, balance=balance, code=b"")
            original = Account(
                nonce=1, balance=balance, code=designation(target)
            )
        case AuthorizationAction.INVALID:
            target = pre.deploy_contract(code=Op.STOP)
            assert balance > 0, (
                "An existing account must have non-zero balance"
            )
            authority = pre.fund_eoa(amount=balance)
            # The nonce does not match the authority's account nonce, so
            # validate_authorization skips the authorization; only the
            # intrinsic base cost is paid and the authority is untouched
            # -- never applied, so never written.
            authorization = AuthorizationTuple(
                address=target,
                nonce=99,
                signer=authority,
                creates_account=False,
                writes_delegation=False,
                first_write=False,
            )
            applied = Account(nonce=0, balance=balance, code=b"")
            original = Account(nonce=0, balance=balance, code=b"")
        case _:
            raise ValueError(f"unknown authorization action {action}")

    return AuthorizationScenario(
        authority=authority,
        authorization=authorization,
        applied_account=applied,
        original_account=original,
    )


def authorization_transaction_cost(
    fork: Fork,
    authorization_list: list[AuthorizationTuple],
    *,
    access_list: list[AccessList] | None = None,
) -> int:
    """
    Return the exact gas a value-free type-4 transaction to a plain
    contract recipient consumes for the given authorizations.

    The recipient is a ``CONTRACT`` that runs no code, so no recipient
    top-frame charge applies and the cost reduces to the intrinsic plus
    the authorizations' own top-frame execution and state charges. Each
    authorization's charge is driven by its ``creates_account`` /
    ``writes_delegation`` / ``first_write`` annotations.
    """
    intrinsic_gas = fork.transaction_intrinsic_cost_calculator()(
        access_list=access_list,
        recipient_type=RecipientType.CONTRACT,
        authorization_list_or_count=authorization_list,
        return_cost_deducted_prior_execution=True,
    )
    return intrinsic_gas + fork.transaction_top_frame_gas_calculator()(
        recipient_type=RecipientType.CONTRACT,
        authorizations=authorization_list,
    )


def setup_target(
    pre: Alloc, recipient_type: RecipientType, sender: Address
) -> Address:
    """
    Allocate a target account matching the given recipient type.

    ``EOA`` targets are pre-funded to ``EOA_INITIAL_BALANCE`` so that
    post-state balance assertions distinguish a successful value
    transfer from a no-op.
    """
    match recipient_type:
        case RecipientType.EOA:
            return pre.fund_eoa(amount=EOA_INITIAL_BALANCE)
        case RecipientType.CONTRACT:
            return pre.deploy_contract(code=Op.STOP)
        case RecipientType.EMPTY_ACCOUNT:
            return pre.nonexistent_account()
        case RecipientType.SELF:
            return sender
        case RecipientType.DELEGATION_7702:
            delegated_to = pre.deploy_contract(code=Op.STOP)
            return pre.fund_eoa(amount=0, delegation=delegated_to)
        case _:
            raise ValueError(f"Unsupported recipient type {recipient_type}")
