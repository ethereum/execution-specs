"""
Tests for the static per-authorization floor term of
[EIP-8279: Block Access List Byte Floor](https://eips.ethereum.org/EIPS/eip-8279).
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    AuthorizationTuple,
    EIPChecklist,
    Fork,
    Op,
    StateTestFiller,
    Transaction,
    TransactionException,
    TransactionReceipt,
)

from ...prague.eip7702_set_code_tx.spec import Spec as Spec7702
from .helpers import floor_dominating_calldata
from .spec import ref_spec_8279

REFERENCE_SPEC_GIT_PATH = ref_spec_8279.git_path
REFERENCE_SPEC_VERSION = ref_spec_8279.version

pytestmark = pytest.mark.valid_from("Bogota")

AUTHORITY_BALANCE = 1


@EIPChecklist.GasCostChanges.Test.GasUpdatesMeasurement()
@pytest.mark.parametrize(
    "outcome",
    [
        pytest.param("floor_binds", id="floor_binds"),
        pytest.param(
            "below_floor",
            id="below_floor_rejected",
            marks=pytest.mark.exception_test,
        ),
    ],
)
@pytest.mark.parametrize(
    "valid",
    [
        pytest.param(True, id="valid_authorizations"),
        pytest.param(False, id="invalid_authorizations"),
    ],
)
@pytest.mark.parametrize("authorization_count", [1, 3])
def test_authorization_floor(
    fork: Fork,
    pre: Alloc,
    state_test: StateTestFiller,
    outcome: str,
    valid: bool,
    authorization_count: int,
) -> None:
    """
    Each authorization adds its block access list bytes to the static
    floor, whether or not it is applied: the floor binds with the term
    included, and a gas limit one short of it is rejected for the floor
    alone.
    """
    sender = pre.fund_eoa()
    recipient = pre.deploy_contract(code=Op.STOP)
    target = pre.deploy_contract(code=Op.STOP)

    authorities = [
        pre.fund_eoa(amount=AUTHORITY_BALANCE)
        for _ in range(authorization_count)
    ]
    authorizations = []
    for authority in authorities:
        authorizations.append(
            AuthorizationTuple(
                address=target,
                # A mismatched nonce makes `validate_authorization` skip
                # the tuple; the floor term is charged all the same.
                nonce=0 if valid else 99,
                signer=authority,
                creates_account=False,
                writes_delegation=valid,
                first_write=valid,
            )
        )
    top_frame_gas = fork.transaction_top_frame_gas_calculator()(
        authorizations=authorizations
    )
    intrinsic_calc = fork.transaction_intrinsic_cost_calculator()
    floor_calc = fork.transaction_data_floor_cost_calculator()

    def total_cost(byte_count: int) -> int:
        return (
            intrinsic_calc(
                calldata=b"\x00" * byte_count,
                authorization_list_or_count=authorizations,
                return_cost_deducted_prior_execution=True,
            )
            + top_frame_gas
        )

    def floor_cost(byte_count: int) -> int:
        return floor_calc(
            data=b"\x00" * byte_count,
            authorization_list_or_count=authorizations,
        )

    calldata = floor_dominating_calldata(total_cost, floor_cost)
    static_floor = floor_cost(len(calldata))

    post: dict[Address, Account] = {}
    if outcome == "below_floor":
        # One short of the floor still covers the intrinsic cost, so the
        # floor is the only rule that can reject the transaction.
        assert total_cost(len(calldata)) < static_floor
        tx = Transaction(
            sender=sender,
            to=recipient,
            data=calldata,
            authorization_list=authorizations,
            gas_limit=static_floor - 1,
            error=TransactionException.INTRINSIC_GAS_BELOW_FLOOR_GAS_COST,
        )
    elif outcome == "floor_binds":
        tx = Transaction(
            sender=sender,
            to=recipient,
            data=calldata,
            authorization_list=authorizations,
            expected_receipt=TransactionReceipt(
                cumulative_gas_used=static_floor
            ),
        )
        for authority in authorities:
            post[authority] = (
                Account(
                    nonce=1,
                    balance=AUTHORITY_BALANCE,
                    code=Spec7702.delegation_designation(target),
                )
                if valid
                else Account(nonce=0, balance=AUTHORITY_BALANCE, code=b"")
            )
    else:
        raise ValueError(f"unknown outcome {outcome}")

    state_test(pre=pre, tx=tx, post=post)
