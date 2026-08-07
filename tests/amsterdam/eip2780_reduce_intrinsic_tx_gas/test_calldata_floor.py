"""EIP-2780 interaction with the EIP-7623/7976 calldata floor."""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Bytes,
    Fork,
    Op,
    RecipientType,
    StateTestFiller,
    Transaction,
    TransactionException,
    TransactionReceipt,
    compute_create_address,
)

from ...prague.eip7623_increase_calldata_cost.helpers import (
    find_floor_cost_threshold,
)
from .helpers import (
    EOA_INITIAL_BALANCE,
    AuthorizationAction,
    build_authorization,
)
from .spec import ref_spec_2780

REFERENCE_SPEC_GIT_PATH = ref_spec_2780.git_path
REFERENCE_SPEC_VERSION = ref_spec_2780.version

pytestmark = pytest.mark.valid_from("Amsterdam")


def _floor_dominating_calldata(fork: Fork) -> Bytes:
    """
    Return zero-byte calldata sized so its calldata floor strictly
    exceeds the decomposed intrinsic of every non-create shape
    ``test_calldata_floor`` runs.

    Reuses the shared EIP-7623 ``find_floor_cost_threshold`` binary
    search against the costliest such shape (a value-bearing transfer
    to a distinct EOA), then steps one byte past the threshold (the
    last size where the floor does not yet dominate) so the floor
    strictly binds -- for that shape, and a fortiori for the cheaper
    self-transfer shape.
    """
    intrinsic_calc = fork.transaction_intrinsic_cost_calculator()
    floor_calc = fork.transaction_data_floor_cost_calculator()

    def intrinsic(byte_count: int) -> int:
        return intrinsic_calc(
            calldata=b"\x00" * byte_count,
            sends_value=True,
            recipient_type=RecipientType.EOA,
            return_cost_deducted_prior_execution=True,
        )

    def floor(byte_count: int) -> int:
        return floor_calc(data=b"\x00" * byte_count)

    threshold = find_floor_cost_threshold(
        floor_data_gas_cost_calculator=floor,
        intrinsic_gas_cost_calculator=intrinsic,
    )
    byte_count = threshold + 1

    assert floor(byte_count) > intrinsic(byte_count)
    return Bytes(b"\x00" * byte_count)


@pytest.mark.inclusion_test
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
    "value",
    [
        pytest.param(0, id="zero_value"),
        pytest.param(1, id="non-zero_value"),
    ],
)
@pytest.mark.parametrize(
    "recipient_type",
    [
        pytest.param(RecipientType.EOA, id="other_eoa"),
        pytest.param(RecipientType.SELF, id="self_transfer"),
    ],
)
def test_calldata_floor(
    fork: Fork,
    pre: Alloc,
    state_test: StateTestFiller,
    outcome: str,
    value: int,
    recipient_type: RecipientType,
) -> None:
    """
    A data-heavy transaction to an existing EOA -- a distinct account
    or the sender itself -- whose calldata floor exceeds the decomposed
    value-transfer intrinsic.

    - ``floor_binds``: with a gas limit above the floor, ``gas_used``
      pins to the floor.
    - ``below_floor``: a gas limit one short of the floor still covers
      the (smaller) decomposed intrinsic, so the floor is the only
      thing that can reject it, with
      ``INTRINSIC_GAS_BELOW_FLOOR_GAS_COST``.
    """
    sender = pre.fund_eoa()
    is_self_transfer = recipient_type == RecipientType.SELF
    target = (
        sender
        if is_self_transfer
        else pre.fund_eoa(amount=EOA_INITIAL_BALANCE)
    )

    calldata = _floor_dominating_calldata(fork)
    calldata_floor = fork.transaction_data_floor_cost_calculator()(
        data=calldata,
        sends_value=bool(value),
        recipient_type=recipient_type,
    )

    intrinsic_gas = fork.transaction_intrinsic_cost_calculator()(
        calldata=calldata,
        sends_value=bool(value),
        recipient_type=recipient_type,
        return_cost_deducted_prior_execution=True,
    )
    # The calldata was sized against the costliest shape (value moving
    # to a distinct EOA), so the floor dominates the carved-out
    # self-transfer intrinsic a fortiori.
    assert intrinsic_gas < calldata_floor, (
        "the calldata floor must dominate the decomposed intrinsic"
    )

    post: dict[Address, Account] = {}
    if outcome == "below_floor":
        # ``gas_limit`` one short of the floor still covers the
        # decomposed intrinsic, so the floor is the only thing that can
        # reject it; the post state is empty (transaction rejected).
        # The transaction is rejected, never included in a block, so
        # there is no receipt to assert against; the ``error`` is the
        # whole expectation.
        gas_limit = calldata_floor - 1
        tx = Transaction(
            sender=sender,
            to=target,
            value=value,
            data=calldata,
            gas_limit=gas_limit,
            error=TransactionException.INTRINSIC_GAS_BELOW_FLOOR_GAS_COST,
        )
    else:
        # ``floor_binds``: no explicit gas limit (auto-fills above the
        # floor). Each shape pays exactly its own floor -- the
        # decomposed base survives into it -- and the transferred wei
        # nets to zero on a self-transfer.
        tx = Transaction(
            sender=sender,
            to=target,
            value=value,
            data=calldata,
            expected_receipt=TransactionReceipt(
                cumulative_gas_used=calldata_floor,
            ),
        )
        post = {
            sender: Account(nonce=1),
        }
        if not is_self_transfer:
            post[target] = Account(balance=EOA_INITIAL_BALANCE + value)

    state_test(pre=pre, tx=tx, post=post)


def _floor_dominating_initcode(fork: Fork) -> Bytes:
    """
    Return zero-byte init code sized so its calldata floor strictly
    exceeds a creation transaction's full cost, for
    ``test_calldata_floor_contract_creation`` (the only creation-
    transaction test in this module; ``test_calldata_floor`` uses
    ``_floor_dominating_calldata`` instead).

    All-zero init code executes a single free ``STOP`` and deploys
    empty code, so the transaction's cost is the creation intrinsic
    plus the created account's top-frame ``NEW_ACCOUNT`` state charge,
    with no execution or deposit gas. The threshold search runs against
    that total, then steps one byte past it so the floor strictly
    binds.
    """
    intrinsic_calc = fork.transaction_intrinsic_cost_calculator()
    floor_calc = fork.transaction_data_floor_cost_calculator()
    new_account_state_gas = fork.transaction_top_frame_state_gas(
        contract_creation=True,
    )

    def total(byte_count: int) -> int:
        return (
            intrinsic_calc(
                calldata=b"\x00" * byte_count,
                contract_creation=True,
                sends_value=True,
                return_cost_deducted_prior_execution=True,
            )
            + new_account_state_gas
        )

    def floor(byte_count: int) -> int:
        return floor_calc(
            data=b"\x00" * byte_count,
            contract_creation=True,
        )

    threshold = find_floor_cost_threshold(
        floor_data_gas_cost_calculator=floor,
        intrinsic_gas_cost_calculator=total,
    )
    byte_count = threshold + 1

    assert floor(byte_count) > total(byte_count)
    assert byte_count <= fork.max_initcode_size()
    return Bytes(b"\x00" * byte_count)


@pytest.mark.inclusion_test
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
    "value",
    [
        pytest.param(0, id="zero_value"),
        pytest.param(1, id="non-zero_value"),
    ],
)
def test_calldata_floor_contract_creation(
    fork: Fork,
    pre: Alloc,
    state_test: StateTestFiller,
    outcome: str,
    value: int,
) -> None:
    """
    A contract creation whose calldata floor exceeds the creation
    intrinsic plus the created account's ``NEW_ACCOUNT`` state charge.

    The init code is all zeros: it executes a free ``STOP``, deploys
    empty code, and prices every byte as one floor token.

    - ``floor_binds``: ``gas_used`` pins to the floor, which anchors
      on the creation execution base (``TX_BASE + CREATE_ACCESS``)
      but excludes the created account's ``NEW_ACCOUNT`` *state* charge
      and the init-code word cost -- both masked by the binding floor --
      while the deploy (and any moved wei) still lands.
      The receipt pins the floor exactly.
    - ``below_floor``: a gas limit one short of the floor still covers
      the creation intrinsic, so the rejection is pinned to the floor,
      with ``INTRINSIC_GAS_BELOW_FLOOR_GAS_COST``.
    """
    sender = pre.fund_eoa()
    created = compute_create_address(address=sender, nonce=sender.nonce)

    init_code = _floor_dominating_initcode(fork)
    calldata_floor = fork.transaction_data_floor_cost_calculator()(
        data=init_code,
        contract_creation=True,
        sends_value=bool(value),
    )

    intrinsic_gas = fork.transaction_intrinsic_cost_calculator()(
        calldata=init_code,
        contract_creation=True,
        sends_value=bool(value),
        return_cost_deducted_prior_execution=True,
    )
    assert intrinsic_gas < calldata_floor, (
        "the calldata floor must dominate the creation intrinsic"
    )

    post: dict[Address, Account | None] = {}
    if outcome == "below_floor":
        # One gas short of the floor still covers the creation
        # intrinsic, so the floor is the only thing that can reject it;
        # the post state is empty and there is no receipt to assert
        # against (transaction rejected, never included).
        gas_limit = calldata_floor - 1
        tx = Transaction(
            sender=sender,
            to=None,
            value=value,
            data=init_code,
            gas_limit=gas_limit,
            error=TransactionException.INTRINSIC_GAS_BELOW_FLOOR_GAS_COST,
        )
    else:
        # ``floor_binds``: headroom above the floor; the receipt pins
        # ``gas_used`` to exactly the floor, so the ``NEW_ACCOUNT``
        # state charge is masked while the deploy still happens.
        tx = Transaction(
            sender=sender,
            to=None,
            value=value,
            data=init_code,
            gas_limit=calldata_floor,
            expected_receipt=TransactionReceipt(
                cumulative_gas_used=calldata_floor,
            ),
        )
        post = {
            sender: Account(nonce=1),
            created: Account(nonce=1, balance=value, code=b""),
        }

    state_test(pre=pre, tx=tx, post=post)


@pytest.mark.inclusion_test
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
def test_calldata_floor_with_authorizations(
    fork: Fork,
    pre: Alloc,
    state_test: StateTestFiller,
    outcome: str,
) -> None:
    """
    A data-heavy type-4 transaction whose calldata floor exceeds the
    full authorization total: the intrinsic plus the authorization's
    top-frame execution and state charges.
    """
    sender = pre.fund_eoa()
    recipient = pre.deploy_contract(code=Op.STOP)
    scenario = build_authorization(
        pre, AuthorizationAction.SETS_NEW_DELEGATION
    )
    authorization_list = [scenario.authorization]

    intrinsic_calc = fork.transaction_intrinsic_cost_calculator()
    floor_calc = fork.transaction_data_floor_cost_calculator()
    top_frame_gas = fork.transaction_top_frame_gas_calculator()(
        recipient_type=RecipientType.CONTRACT,
        authorizations=authorization_list,
    )
    top_frame_state_gas = fork.transaction_top_frame_state_gas(
        recipient_type=RecipientType.CONTRACT,
        authorizations=authorization_list,
    )

    def total(byte_count: int) -> int:
        return (
            intrinsic_calc(
                calldata=b"\x00" * byte_count,
                recipient_type=RecipientType.CONTRACT,
                authorization_list_or_count=authorization_list,
                return_cost_deducted_prior_execution=True,
            )
            + top_frame_gas
            + top_frame_state_gas
        )

    def floor(byte_count: int) -> int:
        return floor_calc(
            data=b"\x00" * byte_count,
            recipient_type=RecipientType.CONTRACT,
        )

    threshold = find_floor_cost_threshold(
        floor_data_gas_cost_calculator=floor,
        intrinsic_gas_cost_calculator=total,
    )
    byte_count = threshold + 1
    calldata = Bytes(b"\x00" * byte_count)
    calldata_floor = floor(byte_count)
    assert calldata_floor > total(byte_count), (
        "the calldata floor must dominate the full authorization total"
    )

    post: dict[Address, Account | None]
    if outcome == "below_floor":
        tx = Transaction(
            sender=sender,
            to=recipient,
            data=calldata,
            authorization_list=authorization_list,
            gas_limit=calldata_floor - 1,
            error=TransactionException.INTRINSIC_GAS_BELOW_FLOOR_GAS_COST,
        )
        post = {scenario.authority: scenario.original_account}
    else:
        tx = Transaction(
            sender=sender,
            to=recipient,
            data=calldata,
            authorization_list=authorization_list,
            gas_limit=calldata_floor,
            expected_receipt=TransactionReceipt(
                cumulative_gas_used=calldata_floor,
            ),
        )
        post = {
            sender: Account(nonce=1),
            scenario.authority: scenario.applied_account,
        }

    state_test(pre=pre, tx=tx, post=post)
