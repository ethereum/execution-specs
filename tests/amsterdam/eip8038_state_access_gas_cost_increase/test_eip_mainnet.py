"""
Mainnet-marked happy-path smoke tests for
[EIP-8038: State Access Gas Cost Increase](https://eips.ethereum.org/EIPS/eip-8038).

One minimal success per repriced dimension (no boundaries, no exact
magnitudes): a state slot is written, a value-bearing cold ``CALL``
lands, an ``EXTCODESIZE`` runs, a ``CREATE`` deploys a contract, a
``SELFDESTRUCT`` funds a fresh account, a single ``7702`` authorization
installs a delegation, and a re-authorization of an already-delegated
authority applies the existing-authority refund. Gas limits are
deliberately generous so these prove the operation runs under the
EIP-8038 schedule without re-deriving any per-opcode cost (other files
own those matrices).
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
)
from execution_testing.checklists import EIPChecklist

from ...prague.eip7702_set_code_tx.spec import Spec as Spec7702
from .spec import ref_spec_8038

REFERENCE_SPEC_GIT_PATH = ref_spec_8038.git_path
REFERENCE_SPEC_VERSION = ref_spec_8038.version

pytestmark = [pytest.mark.valid_at("Amsterdam"), pytest.mark.mainnet]


@EIPChecklist.GasCostChanges.Test.GasUpdatesMeasurement()
def test_sstore_zero_to_nonzero(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    A zero-to-nonzero ``SSTORE`` pays the EIP-8038 storage write and
    succeeds, leaving the slot set.
    """
    storage = Storage()
    contract = pre.deploy_contract(code=Op.SSTORE(storage.store_next(1), 1))

    tx = Transaction(
        to=contract,
        gas_limit=1_000_000,
        sender=pre.fund_eoa(),
    )

    post = {contract: Account(storage=storage)}
    state_test(pre=pre, post=post, tx=tx)


@EIPChecklist.GasCostChanges.Test.GasUpdatesMeasurement()
def test_cold_call_with_value(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    A value-bearing cold ``CALL`` pays ``COLD_ACCOUNT_ACCESS`` plus
    ``CALL_VALUE`` and succeeds; the caller records the ``CALL`` success
    flag and the callee receives the forwarded value.
    """
    callee = pre.deploy_contract(code=Op.STOP, balance=0)

    caller_storage = Storage()
    caller = pre.deploy_contract(
        code=(
            Op.SSTORE(
                caller_storage.store_next(1),
                Op.CALL(gas=100_000, address=callee, value=1),
            )
        ),
    )

    tx = Transaction(
        to=caller,
        gas_limit=1_000_000,
        value=1,
        sender=pre.fund_eoa(),
    )

    post = {
        caller: Account(storage=caller_storage),
        callee: Account(balance=1),
    }
    state_test(pre=pre, post=post, tx=tx)


@EIPChecklist.GasCostChanges.Test.GasUpdatesMeasurement()
def test_extcodesize(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    ``EXTCODESIZE`` pays the EIP-8038 account access plus the code-read
    surcharge and succeeds, returning the target's non-zero code size.
    """
    target = pre.deploy_contract(code=Op.STOP * 3)

    storage = Storage()
    contract = pre.deploy_contract(
        code=Op.SSTORE(storage.store_next(3), Op.EXTCODESIZE(target)),
    )

    tx = Transaction(
        to=contract,
        gas_limit=1_000_000,
        sender=pre.fund_eoa(),
    )

    post = {contract: Account(storage=storage)}
    state_test(pre=pre, post=post, tx=tx)


@EIPChecklist.GasCostChanges.Test.GasUpdatesMeasurement()
def test_create_deploys_contract(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    A factory ``CREATE``s a one-byte (``STOP``) contract under the
    EIP-8038 schedule and succeeds; the factory records the ``CREATE``
    success flag in a slot. The transaction supplies the CREATE state
    gas via the reservoir.
    """
    init_code = Op.STOP
    init_word = int.from_bytes(bytes(init_code), "big") << (
        256 - 8 * len(init_code)
    )

    storage = Storage()
    factory = pre.deploy_contract(
        code=(
            Op.MSTORE(0, init_word)
            + Op.SSTORE(
                storage.store_next(True),
                Op.GT(Op.CREATE(0, 0, len(init_code)), 0),
            )
        ),
    )

    tx = Transaction(
        to=factory,
        gas_limit=1_000_000,
        state_gas_reservoir=fork.create_state_gas(code_size=0),
        sender=pre.fund_eoa(),
    )

    post = {factory: Account(storage=storage)}
    state_test(pre=pre, post=post, tx=tx)


@EIPChecklist.GasCostChanges.Test.GasUpdatesMeasurement()
def test_selfdestruct_funds_new_account(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    A balance-bearing contract ``SELFDESTRUCT``s to a fresh beneficiary
    under the EIP-8038 schedule, forwarding its balance. The new-account
    state gas is supplied via the reservoir; the beneficiary ends up
    holding the transferred balance.
    """
    beneficiary = pre.fund_eoa(amount=0)

    suicidal = pre.deploy_contract(
        code=Op.SELFDESTRUCT(beneficiary),
        balance=1,
    )

    tx = Transaction(
        to=suicidal,
        gas_limit=1_000_000,
        state_gas_reservoir=Op.SELFDESTRUCT(account_new=True).state_cost(fork),
        sender=pre.fund_eoa(),
    )

    post = {beneficiary: Account(balance=1)}
    state_test(pre=pre, post=post, tx=tx)


@EIPChecklist.GasCostChanges.Test.GasUpdatesMeasurement()
def test_auth_installs_delegation(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    A single valid ``7702`` authorization pays the EIP-8038 auth
    intrinsic and installs a delegation designation on the authority.
    """
    auth_signer = pre.fund_eoa()
    set_code_to = pre.deploy_contract(code=Op.STOP)

    authorization_list = [
        AuthorizationTuple(
            address=set_code_to,
            nonce=0,
            signer=auth_signer,
        ),
    ]

    tx = Transaction(
        to=auth_signer,
        gas_limit=1_000_000,
        authorization_list=authorization_list,
        sender=pre.fund_eoa(),
    )

    post = {
        auth_signer: Account(
            nonce=1,
            code=Spec7702.delegation_designation(set_code_to),
        ),
    }
    state_test(pre=pre, post=post, tx=tx)


@EIPChecklist.GasCostChanges.Test.GasUpdatesMeasurement()
def test_existing_authority_refund(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Re-authorizing an already-delegated authority applies the
    existing-authority refund and re-points the delegation; the tx
    succeeds with the new designation installed.
    """
    old_target = pre.deploy_contract(code=Op.STOP)
    new_target = pre.deploy_contract(code=Op.STOP)

    # Authority already carries a delegation, so the new authorization
    # triggers REFUND_AUTH_PER_EXISTING_ACCOUNT.
    auth_signer = pre.fund_eoa(delegation=old_target)

    authorization_list = [
        AuthorizationTuple(
            address=new_target,
            nonce=1,
            signer=auth_signer,
        ),
    ]

    tx = Transaction(
        to=auth_signer,
        gas_limit=1_000_000,
        authorization_list=authorization_list,
        sender=pre.fund_eoa(),
    )

    post = {
        auth_signer: Account(
            nonce=2,
            code=Spec7702.delegation_designation(new_target),
        ),
    }
    state_test(pre=pre, post=post, tx=tx)
