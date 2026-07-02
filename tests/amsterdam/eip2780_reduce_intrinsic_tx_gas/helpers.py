"""Shared helpers for EIP-2780 tests."""

from execution_testing import Address, Alloc, Op, RecipientType

from ...prague.eip7702_set_code_tx.spec import Spec as Spec7702

EOA_INITIAL_BALANCE = 100

RECIPIENT_TYPES_NON_CREATE = [
    RecipientType.EOA,
    RecipientType.CONTRACT,
    RecipientType.EMPTY_ACCOUNT,
    RecipientType.SELF,
    RecipientType.DELEGATION_7702,
]


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
            return pre.deploy_contract(
                code=Spec7702.delegation_designation(delegated_to)
            )
        case _:
            raise ValueError(f"Unsupported recipient type {recipient_type}")
