"""Exercise state-gas transactions with execute --estimate-gas."""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    AuthorizationTuple,
    Initcode,
    Op,
    StateTestFiller,
    Transaction,
    TransactionReceipt,
    compute_create_address,
)

from tests.prague.eip7702_set_code_tx.spec import Spec as SetCodeSpec

from .spec import ref_spec_8037

REFERENCE_SPEC_GIT_PATH = ref_spec_8037.git_path
REFERENCE_SPEC_VERSION = ref_spec_8037.version

pytestmark = pytest.mark.valid_from("Amsterdam")


@pytest.mark.parametrize("tx_type", [0, 1, 2])
@pytest.mark.parametrize(
    "scenario", ["new_account", "storage", "calldata_floor", "cross_frame"]
)
def test_state_gas_estimation(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_type: int,
    scenario: str,
) -> None:
    """Require implicit-gas transactions to complete their state changes."""
    sender = pre.fund_eoa()
    target: Address
    post: dict[Address, Account]
    data = b""
    value = 0
    if scenario == "new_account":
        target = pre.fund_eoa(amount=0)
        value = 1
        post = {target: Account(balance=1)}
    elif scenario == "cross_frame":
        holder = pre.deploy_contract(code=Op.SSTORE(0, Op.CALLDATASIZE))
        target = pre.deploy_contract(
            code=Op.SSTORE(0, Op.CALL(gas=Op.GAS, address=holder, args_size=1))
            + Op.SSTORE(1, Op.CALL(gas=Op.GAS, address=holder))
        )
        post = {
            target: Account(storage={0: 1, 1: 1}),
            holder: Account(storage={0: 0}),
        }
    else:
        target = pre.deploy_contract(code=Op.SSTORE(0, 1))
        post = {target: Account(storage={0: 1})}
        if scenario == "calldata_floor":
            data = b"\xff" * 4096
    state_test(
        pre=pre,
        post=post,
        tx=Transaction(
            ty=tx_type,
            sender=sender,
            to=target,
            value=value,
            data=data,
            expected_receipt=TransactionReceipt(status=1),
        ),
    )


@pytest.mark.parametrize("tx_type", [0, 1, 2])
@pytest.mark.parametrize("code_size", [31, 32, 33])
def test_code_deposit_estimation(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_type: int,
    code_size: int,
) -> None:
    """Require enough gas for account creation and code deposit."""
    sender = pre.fund_eoa()
    code = Op.STOP * code_size
    tx = Transaction(
        ty=tx_type,
        sender=sender,
        to=None,
        data=Initcode(deploy_code=code),
        expected_receipt=TransactionReceipt(status=1),
    )
    state_test(
        pre=pre,
        tx=tx,
        post={
            compute_create_address(address=sender, nonce=tx.nonce): Account(
                nonce=1, code=code
            )
        },
    )


@pytest.mark.parametrize("existing_authority", [False, True])
def test_authorization_estimation(
    state_test: StateTestFiller,
    pre: Alloc,
    existing_authority: bool,
) -> None:
    """Require authorization processing and delegated writes to succeed."""
    sender = pre.fund_eoa()
    authority = pre.fund_eoa(amount=1 if existing_authority else 0)
    target = pre.deploy_contract(code=Op.SSTORE(0, 1))
    tx = Transaction(
        sender=sender,
        to=authority,
        authorization_list=[
            AuthorizationTuple(
                signer=authority,
                address=target,
                creates_account=not existing_authority,
            )
        ],
        expected_receipt=TransactionReceipt(status=1),
    )
    state_test(
        pre=pre,
        tx=tx,
        post={
            authority: Account(
                nonce=1,
                code=SetCodeSpec.delegation_designation(target),
                storage={0: 1},
            )
        },
    )
