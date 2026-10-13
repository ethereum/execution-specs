"""
Transaction-type coverage for
[EIP-7778 Block Gas Accounting without Refunds](https://eips.ethereum.org/EIPS/eip-7778).

Block gas accounting is transaction-type agnostic: whatever envelope
carries the refunding call, the block counts its pre-refund gas while the
sender is charged the post-refund amount.
"""

from enum import Enum

import pytest
from execution_testing import (
    Alloc,
    AuthorizationTuple,
    Block,
    BlockchainTestFiller,
    BlockException,
    EIPChecklist,
    Environment,
    Fork,
    RefundTypes,
    Transaction,
    TransactionException,
    add_kzg_version,
)
from execution_testing.vm import Op

from .helpers import RefundTransaction, TransactionFailure
from .spec import ref_spec_7778

REFERENCE_SPEC_GIT_PATH = ref_spec_7778.git_path
REFERENCE_SPEC_VERSION = ref_spec_7778.version

INITIAL_FUND = 10**18
REFUNDS_COUNT = 10

pytestmark = [
    pytest.mark.valid_from("EIP7778"),
    pytest.mark.execute(
        pytest.mark.skip(reason="Requires specific gas price")
    ),
]


class TypedTxPosition(Enum):
    """Which transaction of the block carries the parametrized type."""

    HEAD = "head"
    TRAILING = "trailing"


@pytest.fixture
def authorization_list(
    pre: Alloc, tx_type: int
) -> list[AuthorizationTuple] | None:
    """Authorization list required by a type-4 envelope, else None."""
    if tx_type != 4:
        return None
    return [
        AuthorizationTuple(
            address=pre.deploy_contract(code=Op.STOP),
            signer=pre.fund_eoa(),
        )
    ]


@EIPChecklist.BlockLevelConstraint.Test.Content.TransactionTypes()
@TransactionFailure.with_all_tx_failures()
@pytest.mark.with_all_tx_types(selector=lambda tx_type: tx_type != 6)
@pytest.mark.with_all_refund_types()
def test_block_gas_accounting_all_transaction_types(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    tx_type: int,
    refund_type: RefundTypes,
    refund_tx_failure: TransactionFailure | None,
    authorization_list: list[AuthorizationTuple] | None,
) -> None:
    """Pin block gas accounting for a refund carried by each tx type."""
    refund_tx = RefundTransaction.build(
        fork=fork,
        sender=pre.fund_eoa(INITIAL_FUND),
        refund_types={refund_type},
        refunds_count=REFUNDS_COUNT,
        tx_failure=refund_tx_failure,
        ty=tx_type,
        authorization_list=authorization_list,
    )
    refund_tx.set_pre(pre)

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[refund_tx],
                expected_gas_used=refund_tx.block_gas_used(),
            )
        ],
        post=refund_tx.post(pre),
    )


@EIPChecklist.BlockLevelConstraint.Test.Content.TransactionTypes()
@pytest.mark.inclusion_test
@pytest.mark.parametrize(
    "typed_tx_position",
    [
        pytest.param(TypedTxPosition.HEAD, id="typed_head_tx"),
        pytest.param(TypedTxPosition.TRAILING, id="typed_trailing_tx"),
    ],
)
@pytest.mark.with_all_tx_types(selector=lambda tx_type: tx_type != 6)
@pytest.mark.with_all_refund_types()
@pytest.mark.filter_combinations(
    lambda tx_type, typed_tx_position, **_: not (
        tx_type == 0 and typed_tx_position is TypedTxPosition.TRAILING
    ),
    reason=(
        "a type-0 envelope on either side of the gate builds the same "
        "block, already covered by the head parametrization"
    ),
)
@pytest.mark.parametrize(
    "trailing_tx_block_gas_limit_delta",
    [
        pytest.param(
            1,
            id="extra_block_gas_limit",
        ),
        pytest.param(
            0,
            id="exact_block_gas_limit",
        ),
        pytest.param(
            -1,
            marks=[pytest.mark.exception_test],
            id="exceeds_block_gas_limit",
        ),
    ],
)
def test_trailing_tx_admission_all_transaction_types(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    tx_type: int,
    refund_type: RefundTypes,
    typed_tx_position: TypedTxPosition,
    authorization_list: list[AuthorizationTuple] | None,
    trailing_tx_block_gas_limit_delta: int,
) -> None:
    """
    Pin the admission gate with each tx type on either side of the gate.

    The block gas limit leaves room for the trailing transaction only
    under post-refund accounting, so it must be rejected whichever
    envelope carries the refund and whichever one is turned away.
    """
    typed_head = typed_tx_position is TypedTxPosition.HEAD
    trailing_tx_succeeds = trailing_tx_block_gas_limit_delta >= 0

    refund_tx = RefundTransaction.build(
        fork=fork,
        sender=pre.fund_eoa(INITIAL_FUND),
        refund_types={refund_type},
        refunds_count=REFUNDS_COUNT,
        ty=tx_type if typed_head else 0,
        authorization_list=authorization_list if typed_head else None,
    )
    refund_tx.set_pre(pre)

    receipt_gas_used = refund_tx.expected_receipt.gas_used
    assert receipt_gas_used is not None
    assert refund_tx.block_execution() > receipt_gas_used, (
        "Parametrization must produce a refund; without one pre- and "
        "post-refund accounting agree"
    )

    stop_address = pre.deterministic_deploy_contract(deploy_code=Op.STOP)
    trailing_auth = None if typed_head else authorization_list
    trailing_ty = 0 if typed_head else tx_type
    intrinsic_cost_calc = fork.transaction_intrinsic_cost_calculator()
    # Slack so a post-refund gate admits the trailing tx and still keeps
    # the block within its gas limit. The grant must also outgrow the
    # refund tx's state gas: the admission gate weighs a full gas limit
    # against the execution budget, so a block sized off the execution
    # dimension alone would turn the refund tx itself away.
    trailing_tx_gas_limit = (
        2
        * intrinsic_cost_calc(
            calldata=b"",
            authorization_list_or_count=trailing_auth,
        )
        + refund_tx.state_gas
    )
    trailing_tx = Transaction(
        ty=trailing_ty,
        to=stop_address,
        gas_limit=trailing_tx_gas_limit,
        sender=pre.fund_eoa(),
        authorization_list=trailing_auth,
        blob_versioned_hashes=(
            add_kzg_version([0x01], 0x01) if trailing_ty == 3 else None
        ),
        error=None
        if trailing_tx_succeeds
        else TransactionException.GAS_ALLOWANCE_EXCEEDED,
    )

    block_gas_limit = (
        refund_tx.block_execution()
        + trailing_tx_gas_limit
        + trailing_tx_block_gas_limit_delta
    )
    assert block_gas_limit >= refund_tx.gas_limit, (
        "block must admit the refund transaction itself"
    )

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[refund_tx, trailing_tx],
                gas_limit=block_gas_limit,
                exception=None
                if trailing_tx_succeeds
                else [
                    BlockException.GAS_USED_OVERFLOW,
                    TransactionException.GAS_ALLOWANCE_EXCEEDED,
                ],
            )
        ],
        post=refund_tx.post(pre, block_is_invalid=not trailing_tx_succeeds),
        genesis_environment=Environment(gas_limit=block_gas_limit),
    )


@EIPChecklist.BlockLevelConstraint.Test.Content.Logs()
@pytest.mark.with_all_refund_types()
def test_block_gas_accounting_with_logs(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    refund_type: RefundTypes,
) -> None:
    """
    Verify transaction containing refunds that also emits a log.
    """
    refund_tx = RefundTransaction.build(
        fork=fork,
        sender=pre.fund_eoa(INITIAL_FUND),
        refund_types={refund_type},
        refunds_count=REFUNDS_COUNT,
        emit_log=True,
    )
    refund_tx.set_pre(pre)

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[refund_tx],
                expected_gas_used=refund_tx.block_gas_used(),
            )
        ],
        post=refund_tx.post(pre),
    )
