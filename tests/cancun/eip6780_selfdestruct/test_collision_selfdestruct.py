"""
Test CREATE2 collision interaction with SELFDESTRUCT (EIP-6780).

Verify that a failed CREATE2 (due to collision) does not cause a
subsequent SELFDESTRUCT to destroy the pre-existing contract.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Environment,
    Fork,
    Initcode,
    Op,
    StateTestFiller,
    Storage,
    Transaction,
    compute_create2_address,
)

REFERENCE_SPEC_GIT_PATH = "EIPS/eip-6780.md"
REFERENCE_SPEC_VERSION = "1b6a0e94cc47e859b9866e570391cf37dc55059a"


@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_selfdestruct_after_create2_collision(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test that a failed CREATE2 collision does not count as creation.

    A CREATE2 that collides with an existing contract fails. A
    subsequent SELFDESTRUCT on the same address must not destroy the
    contract because EIP-6780 only allows destruction if the contract
    was created in the same transaction.
    """
    env = Environment()
    storage = Storage()

    salt = 0
    initcode = Initcode(deploy_code=Op.STOP)

    deployer_storage = Storage()
    deployer_code = Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE) + Op.SSTORE(
        deployer_storage.store_next(0, "create2_result"),
        Op.CREATE2(value=0, offset=0, size=Op.CALLDATASIZE, salt=salt),
    )
    deployer = pre.deploy_contract(
        deployer_code, storage=deployer_storage.canary()
    )

    target_address = compute_create2_address(deployer, salt, initcode)

    beneficiary = pre.fund_eoa(amount=0)

    # Target already exists with balance and code (causes collision).
    target_code = Op.SELFDESTRUCT(beneficiary)
    pre[target_address] = Account(
        balance=1,
        nonce=1,
        code=target_code,
    )

    # Controller: attempt CREATE2 (will collide), then call target
    # (SELFDESTRUCT should NOT destroy since target was not created
    # in this tx).
    controller = pre.deploy_contract(
        Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE)
        # CREATE2 via deployer — will fail (collision)
        + Op.SSTORE(
            storage.store_next(1, "create2_call_success"),
            Op.CALL(
                # The colliding CREATE2 consumes 63/64 of the deployer's
                # gas (the account-creation state gas is charged then
                # refunded on collision under EIP-8037); size the budget
                # so the surviving 1/64 still covers the deployer's cold
                # SSTORE of the CREATE2 result.
                gas=500_000 + 64 * fork.gas_costs().COLD_STORAGE_WRITE,
                address=deployer,
                args_size=Op.CALLDATASIZE,
            ),
        )
        # Call target to trigger SELFDESTRUCT
        + Op.SSTORE(
            storage.store_next(1, "selfdestruct_call_success"),
            Op.CALL(gas=500_000, address=target_address),
        )
        + Op.STOP
    )

    sender = pre.fund_eoa()

    post = {
        controller: Account(storage=storage),
        # CREATE2 failed due to collision — returned 0.
        deployer: Account(storage=deployer_storage),
        # Target must still exist (SELFDESTRUCT did not destroy because
        # it was NOT created in this tx). Balance was transferred to
        # beneficiary.
        target_address: Account(
            balance=0,
            nonce=1,
            code=target_code,
        ),
        beneficiary: Account(balance=1),
    }

    state_test(
        env=env,
        pre=pre,
        post=post,
        tx=Transaction(
            sender=sender,
            to=controller,
            data=initcode,
        ),
    )
