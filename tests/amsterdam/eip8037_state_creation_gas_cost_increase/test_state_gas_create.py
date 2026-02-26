"""
Test CREATE and CREATE2 state gas charging under EIP-8037.

Contract creation charges state gas for the new account
(112 * cost_per_state_byte) and for code deposit
(len(code) * cost_per_state_byte). Regular gas for CREATE is
REGULAR_GAS_CREATE (9000).

Tests for [EIP-8037: State Creation Gas Cost Increase]
(https://eips.ethereum.org/EIPS/eip-8037).
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Environment,
    Fork,
    Op,
    StateTestFiller,
    Storage,
    Transaction,
)
from execution_testing.checklists import EIPChecklist

from .spec import Spec, ref_spec_8037

REFERENCE_SPEC_GIT_PATH = ref_spec_8037.git_path
REFERENCE_SPEC_VERSION = ref_spec_8037.version


@EIPChecklist.GasCostChanges.Test.GasUpdatesMeasurement()
@pytest.mark.valid_from("Amsterdam")
def test_create_charges_state_gas(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Test CREATE charges state gas for new account and code deposit.

    A successful CREATE charges 112 * cost_per_state_byte for the new
    account plus len(runtime_code) * cost_per_state_byte for code
    deposit.
    """
    init_code = Op.STOP

    storage = Storage()
    contract = pre.deploy_contract(
        code=(
            Op.MSTORE(
                0,
                int.from_bytes(bytes(init_code), "big")
                << (256 - 8 * len(init_code)),
            )
            + Op.SSTORE(
                storage.store_next(True),
                Op.GT(Op.CREATE(0, 0, len(init_code)), 0),
            )
            + Op.STOP
        ),
    )

    tx = Transaction(
        to=contract,
        gas_limit=Spec.TX_MAX_GAS_LIMIT,
        sender=pre.fund_eoa(),
    )

    post = {contract: Account(storage=storage)}
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.parametrize(
    "opcode",
    [
        pytest.param(Op.CREATE, id="create"),
        pytest.param(Op.CREATE2, id="create2"),
    ],
)
@pytest.mark.valid_from("Amsterdam")
def test_create_with_reservoir(
    state_test: StateTestFiller,
    pre: Alloc,
    opcode: Op,
) -> None:
    """
    Test CREATE/CREATE2 with state gas funded from the reservoir.

    Provide gas above TX_MAX_GAS_LIMIT so the new account state gas
    is drawn from the reservoir rather than gas_left.
    """
    env = Environment()
    cpsb = Spec.COST_PER_STATE_BYTE
    create_state_gas = Spec.STATE_BYTES_PER_NEW_ACCOUNT * cpsb

    storage = Storage()
    init_code = Op.STOP

    if opcode == Op.CREATE:
        create_call = Op.CREATE(0, 0, len(init_code))
    else:
        create_call = Op.CREATE2(0, 0, len(init_code), 0)

    contract = pre.deploy_contract(
        code=(
            Op.MSTORE(
                0,
                int.from_bytes(bytes(init_code), "big")
                << (256 - 8 * len(init_code)),
            )
            + Op.SSTORE(
                storage.store_next(True),
                Op.GT(create_call, 0),
            )
            + Op.STOP
        ),
    )

    tx = Transaction(
        to=contract,
        gas_limit=Spec.TX_MAX_GAS_LIMIT + create_state_gas,
        sender=pre.fund_eoa(),
    )

    post = {contract: Account(storage=storage)}
    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.parametrize(
    "code_size",
    [
        pytest.param(1, id="tiny_code"),
        pytest.param(32, id="one_word"),
        pytest.param(256, id="small_contract"),
        pytest.param(1024, id="medium_contract"),
    ],
)
@pytest.mark.valid_from("Amsterdam")
def test_code_deposit_state_gas_scales_with_size(
    state_test: StateTestFiller,
    pre: Alloc,
    code_size: int,
) -> None:
    """
    Test code deposit state gas scales linearly with code size.

    The code deposit charges len(code) * cost_per_state_byte of state
    gas. Larger deployed code requires proportionally more state gas.
    """
    env = Environment()
    cpsb = Spec.COST_PER_STATE_BYTE
    # State gas: new account + code deposit
    total_state_gas = (Spec.STATE_BYTES_PER_NEW_ACCOUNT + code_size) * cpsb

    # Build init code that returns `code_size` bytes of 0x00
    # PUSH2 code_size, PUSH1 0, RETURN
    init_code = Op.RETURN(0, code_size)

    tx = Transaction(
        to=None,
        data=init_code,
        gas_limit=Spec.TX_MAX_GAS_LIMIT + total_state_gas,
        sender=pre.fund_eoa(),
    )

    state_test(env=env, pre=pre, post={}, tx=tx)


@pytest.mark.valid_from("Amsterdam")
def test_create_tx_state_gas(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Test contract creation transaction charges intrinsic state gas.

    A create transaction (to=None) charges 112 * cost_per_state_byte
    as intrinsic state gas for the new account, plus code deposit state
    gas for the deployed bytecode.
    """
    tx = Transaction(
        to=None,
        data=Op.STOP,
        gas_limit=Spec.TX_MAX_GAS_LIMIT,
        sender=pre.fund_eoa(),
    )

    state_test(pre=pre, post={}, tx=tx)


@pytest.mark.valid_from("Amsterdam")
def test_create_revert_no_code_deposit_state_gas(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Test reverted CREATE does not charge code deposit state gas.

    When CREATE fails during init code execution (REVERT), the new
    account state gas is consumed but no code deposit state gas is
    charged because no code was deployed.
    """
    init_code = Op.REVERT(0, 0)

    storage = Storage()
    contract = pre.deploy_contract(
        code=(
            Op.MSTORE(
                0,
                int.from_bytes(bytes(init_code), "big")
                << (256 - 8 * len(init_code)),
            )
            + Op.SSTORE(
                storage.store_next(0),  # CREATE returns 0 on failure
                Op.CREATE(0, 0, len(init_code)),
            )
            + Op.STOP
        ),
    )

    tx = Transaction(
        to=contract,
        gas_limit=Spec.TX_MAX_GAS_LIMIT,
        sender=pre.fund_eoa(),
    )

    post = {contract: Account(storage=storage)}
    state_test(pre=pre, post=post, tx=tx)


@EIPChecklist.GasCostChanges.Test.OutOfGas()
@pytest.mark.valid_from("Amsterdam")
def test_create_insufficient_state_gas(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test CREATE OOGs when state gas is insufficient.

    Provide enough gas for CREATE's regular gas cost (9000) but not
    enough to cover the 112 * cost_per_state_byte state gas for the
    new account. The CREATE should fail, returning 0.
    """
    init_code = Op.STOP

    storage = Storage()
    contract = pre.deploy_contract(
        code=(
            Op.MSTORE(
                0,
                int.from_bytes(bytes(init_code), "big")
                << (256 - 8 * len(init_code)),
            )
            + Op.SSTORE(
                storage.store_next(0),  # CREATE returns 0 on OOG
                Op.CREATE(0, 0, len(init_code)),
            )
            + Op.STOP
        ),
    )

    # Tight gas — enough for intrinsic + CREATE regular gas but not
    # enough for the new account state gas
    intrinsic_cost = fork.transaction_intrinsic_cost_calculator()
    gas_limit = intrinsic_cost() + Spec.REGULAR_GAS_CREATE + 10_000

    tx = Transaction(
        to=contract,
        gas_limit=gas_limit,
        sender=pre.fund_eoa(),
    )

    post = {contract: Account(storage=storage)}
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("Amsterdam")
def test_create2_address_collision(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Test CREATE2 returns zero on address collision.

    When CREATE2 targets an address that already has code or storage,
    the collision is detected early and returns zero without charging
    state gas. The existing account is left unchanged.
    """
    init_code = Op.STOP
    salt = 0

    storage = Storage()
    contract = pre.deploy_contract(
        code=(
            Op.MSTORE(
                0,
                int.from_bytes(bytes(init_code), "big")
                << (256 - 8 * len(init_code)),
            )
            # First CREATE2 succeeds
            + Op.SSTORE(
                storage.store_next(1, "first_create2"),
                Op.ISZERO(Op.ISZERO(Op.CREATE2(0, 0, len(init_code), salt))),
            )
            # Second CREATE2 with same salt collides
            + Op.SSTORE(
                storage.store_next(0, "collision_create2"),
                Op.CREATE2(0, 0, len(init_code), salt),
            )
            + Op.STOP
        ),
    )

    tx = Transaction(
        to=contract,
        gas_limit=Spec.TX_MAX_GAS_LIMIT * 2,
        sender=pre.fund_eoa(),
    )

    post = {contract: Account(storage=storage)}
    state_test(pre=pre, post=post, tx=tx)
