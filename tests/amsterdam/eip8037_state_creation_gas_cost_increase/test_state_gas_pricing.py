"""
Test the core EIP-8037 state gas pricing function and charge mechanism.

The `state_gas_per_byte()` function computes a dynamic cost per state
byte based on the block gas limit, targeting 100 GiB/year of state
growth. The cost is quantized to 5 significant bits and has a minimum
return of 1.

The `charge_state_gas()` function draws from the state gas reservoir
first, then spills into gas_left. If both pools are insufficient, the
transaction runs out of gas.

Tests for [EIP-8037: State Creation Gas Cost Increase]
(https://eips.ethereum.org/EIPS/eip-8037).
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    AuthorizationTuple,
    Block,
    BlockchainTestFiller,
    Environment,
    Fork,
    Op,
    StateTestFiller,
    Storage,
    Transaction,
    TransactionException,
)
from execution_testing.checklists import EIPChecklist

from .spec import Spec, ref_spec_8037

REFERENCE_SPEC_GIT_PATH = ref_spec_8037.git_path
REFERENCE_SPEC_VERSION = ref_spec_8037.version

BLOCK_GAS_LIMITS = [
    pytest.param(1_000_000, id="1M"),
    pytest.param(30_000_000, id="30M"),
    pytest.param(36_000_000, id="36M"),
    pytest.param(60_000_000, id="60M"),
    pytest.param(100_000_000, id="100M"),
    pytest.param(120_000_000, id="120M"),
    pytest.param(200_000_000, id="200M"),
    pytest.param(300_000_000, id="300M"),
    pytest.param(500_000_000, id="500M"),
    pytest.param(1_000_000_000, id="1G"),
]


@EIPChecklist.GasCostChanges.Test.GasUpdatesMeasurement()
@pytest.mark.parametrize("block_gas_limit", BLOCK_GAS_LIMITS)
@pytest.mark.valid_from("EIP8037")
def test_pricing_at_various_gas_limits(
    state_test: StateTestFiller,
    pre: Alloc,
    block_gas_limit: int,
    fork: Fork,
) -> None:
    """
    Test SSTORE succeeds at various block gas limits.

    The state gas cost per byte varies with the block gas limit.
    At each gas limit, an SSTORE zero-to-nonzero should succeed
    when given sufficient total gas, confirming the pricing function
    produces a valid (nonzero) cost.
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    env = Environment(gas_limit=block_gas_limit)
    fork._env_gas_limit = block_gas_limit
    sstore_state_gas = fork.sstore_state_gas()
    tx_gas = min(gas_limit_cap + sstore_state_gas, block_gas_limit)

    storage = Storage()
    contract = pre.deploy_contract(
        code=Op.SSTORE(storage.store_next(1), 1),
    )

    tx = Transaction(
        to=contract,
        gas_limit=tx_gas,
        sender=pre.fund_eoa(),
    )

    post = {contract: Account(storage=storage)}
    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("EIP8037")
def test_charge_draws_entirely_from_reservoir(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test state gas is drawn entirely from the reservoir.

    When the reservoir has enough gas for the SSTORE state cost,
    gas_left should not be reduced by the state charge. Verify by
    performing a regular-gas-heavy computation after the SSTORE.
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    env = Environment()
    sstore_state_gas = fork.sstore_state_gas()

    storage = Storage()
    contract = pre.deploy_contract(
        code=(
            # SSTORE draws state gas from reservoir
            Op.SSTORE(storage.store_next(1), 1)
            # Remaining gas_left is available for regular ops
            + Op.SSTORE(
                storage.store_next(1),
                Op.ADD(1, 0),  # Cheap regular-gas op
            )
        ),
    )

    # Provide exact state gas in the reservoir
    tx = Transaction(
        to=contract,
        gas_limit=gas_limit_cap + sstore_state_gas * 2,
        sender=pre.fund_eoa(),
    )

    post = {contract: Account(storage=storage)}
    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("EIP8037")
def test_charge_spills_to_gas_left(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test state gas spills from reservoir to gas_left.

    When the reservoir has some gas but not enough to cover the full
    state charge, the remainder is taken from gas_left. The SSTORE
    should still succeed.
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    env = Environment()
    sstore_state_gas = fork.sstore_state_gas()

    storage = Storage()
    contract = pre.deploy_contract(
        code=Op.SSTORE(storage.store_next(1), 1),
    )

    # Provide half the state gas in the reservoir, rest from gas_left
    half_state_gas = sstore_state_gas // 2
    tx = Transaction(
        to=contract,
        gas_limit=gas_limit_cap + half_state_gas,
        sender=pre.fund_eoa(),
    )

    post = {contract: Account(storage=storage)}
    state_test(env=env, pre=pre, post=post, tx=tx)


@EIPChecklist.GasCostChanges.Test.OutOfGas()
@pytest.mark.valid_from("EIP8037")
def test_charge_oog_both_pools_insufficient(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test OOG when both reservoir and gas_left are insufficient.

    Provide just enough gas for intrinsic + SSTORE regular gas but
    not enough for the state gas charge. Neither the reservoir (empty
    at TX_MAX_GAS_LIMIT) nor gas_left can cover the cost.
    """
    gas_costs = fork.gas_costs()
    contract = pre.deploy_contract(
        code=Op.SSTORE(0, 1),
    )

    # Tight gas: intrinsic + SSTORE regular gas only
    intrinsic_cost = fork.transaction_intrinsic_cost_calculator()
    gas_limit = intrinsic_cost() + gas_costs.COLD_STORAGE_WRITE

    tx = Transaction(
        to=contract,
        gas_limit=gas_limit,
        sender=pre.fund_eoa(),
    )

    # OOG — storage unchanged
    post = {contract: Account(storage={0: 0})}
    state_test(pre=pre, post=post, tx=tx)


@EIPChecklist.GasRefundsChanges.Test.RefundCalculation()
@pytest.mark.valid_from("EIP8037")
def test_refund_cap_includes_state_gas(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test the 1/5 refund cap includes state gas used from gas_left.

    When state gas is drawn from gas_left (no reservoir), it counts
    toward tx_gas_used_before_refund. The 1/5 refund cap applies to
    the combined total of regular + state gas consumed. This test
    performs an SSTORE zero-to-nonzero-to-zero sequence to generate
    a refund and verifies the transaction succeeds.
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    contract = pre.deploy_contract(
        code=(Op.SSTORE(0, 1) + Op.SSTORE(0, 0)),
    )

    # No reservoir — all gas from gas_left, refund cap applies
    tx = Transaction(
        to=contract,
        gas_limit=gas_limit_cap,
        sender=pre.fund_eoa(),
    )

    # Slot 0 restored to zero
    post = {contract: Account(storage={0: 0})}
    state_test(pre=pre, post=post, tx=tx)


@EIPChecklist.GasRefundsChanges.Test.RefundCalculation()
@pytest.mark.valid_from("EIP8037")
def test_refund_with_reservoir_state_gas(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test refund when state gas is drawn from reservoir.

    When state gas comes from the reservoir, the refund still applies.
    The refund_counter accumulates state + regular gas refunds, and
    the 1/5 cap uses tx_gas_used_before_refund which accounts for
    both dimensions. An SSTORE zero-to-nonzero-to-zero sequence
    should refund correctly.
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    env = Environment()
    sstore_state_gas = fork.sstore_state_gas()

    contract = pre.deploy_contract(
        code=(Op.SSTORE(0, 1) + Op.SSTORE(0, 0)),
    )

    tx = Transaction(
        to=contract,
        gas_limit=gas_limit_cap + sstore_state_gas,
        sender=pre.fund_eoa(),
    )

    # Slot 0 restored to zero
    post = {contract: Account(storage={0: 0})}
    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.parametrize(
    "gas_limit_block_1,gas_limit_block_2",
    [
        pytest.param(30_000_000, 30_029_295, id="increase"),
        pytest.param(30_000_000, 29_970_705, id="decrease"),
    ],
)
@pytest.mark.valid_from("EIP8037")
def test_pricing_changes_with_block_gas_limit(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    gas_limit_block_1: int,
    gas_limit_block_2: int,
    fork: Fork,
) -> None:
    """
    Test state gas cost changes when block gas limit changes.

    The cost_per_state_byte is a function of the block gas limit.
    When the gas limit increases, state gas becomes more expensive
    (targeting constant state growth). Each block's SSTORE should
    succeed with the appropriate state gas for that block's gas limit.
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    sstore_state_gas = fork.sstore_state_gas()

    storage_1 = Storage()
    contract_1 = pre.deploy_contract(
        code=Op.SSTORE(storage_1.store_next(1), 1),
    )

    storage_2 = Storage()
    contract_2 = pre.deploy_contract(
        code=Op.SSTORE(storage_2.store_next(1), 1),
    )

    env = Environment(gas_limit=gas_limit_block_1)

    block_1 = Block(
        gas_limit=gas_limit_block_1,
        txs=[
            Transaction(
                to=contract_1,
                gas_limit=gas_limit_cap + sstore_state_gas,
                sender=pre.fund_eoa(),
            ),
        ],
    )

    block_2 = Block(
        gas_limit=gas_limit_block_2,
        txs=[
            Transaction(
                to=contract_2,
                gas_limit=gas_limit_cap + sstore_state_gas,
                sender=pre.fund_eoa(),
            ),
        ],
    )

    blockchain_test(
        genesis_environment=env,
        pre=pre,
        blocks=[block_1, block_2],
        post={
            contract_1: Account(storage=storage_1),
            contract_2: Account(storage=storage_2),
        },
    )


@pytest.mark.valid_from("EIP8037")
def test_pricing_minimum_cpsb_floor(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Test cost_per_state_byte returns 1 when block gas limit is low.

    The cost_per_state_byte formula has a minimum floor of 1. When the
    block gas limit is low enough that the quantized result falls below
    the offset, the function returns 1. Use a block gas limit of
    10_000_000 (below TX_MAX_GAS_LIMIT) so the state gas per SSTORE
    is just 32 * 1 = 32.
    """
    block_gas_limit = 10_000_000
    assert Spec.cost_per_state_byte(block_gas_limit) == 1
    env = Environment(gas_limit=block_gas_limit)

    contract = pre.deploy_contract(
        code=Op.SSTORE(0, 1),
    )

    # State gas = 32 * 1 = 32, very cheap
    tx = Transaction(
        to=contract,
        gas_limit=block_gas_limit,
        sender=pre.fund_eoa(),
    )

    post = {contract: Account(storage={0: 1})}
    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.exception_test
@pytest.mark.valid_from("EIP8037")
def test_intrinsic_regular_gas_exceeds_cap(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test that tx is rejected when intrinsic regular gas exceeds cap.

    validate_transaction checks that the intrinsic regular gas (or
    calldata floor) does not exceed the transaction gas limit cap.
    A transaction with enough calldata to push intrinsic cost above
    the cap is invalid even with a high gas_limit.
    """
    gas_costs = fork.gas_costs()
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    # One more non-zero byte than needed to exceed the cap
    calldata_len = gas_limit_cap // gas_costs.TX_DATA_PER_NON_ZERO + 1
    calldata = b"\x01" * calldata_len

    contract = pre.deploy_contract(code=Op.STOP)

    tx = Transaction(
        to=contract,
        gas_limit=gas_limit_cap * 2,
        data=calldata,
        sender=pre.fund_eoa(),
        error=TransactionException.INTRINSIC_GAS_TOO_LOW,
    )

    state_test(pre=pre, post={}, tx=tx)


@pytest.mark.parametrize(
    "above_floor",
    [
        pytest.param(
            False,
            id="below_floor",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(True, id="at_floor"),
    ],
)
@pytest.mark.valid_from("EIP8037")
def test_calldata_floor_enforced_with_state_gas(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    above_floor: bool,
) -> None:
    """
    Test EIP-7623 calldata floor is enforced when EIP-8037 is active.

    Send 100 non-zero calldata bytes to a call transaction so the
    regular intrinsic cost is below the calldata floor. A gas_limit
    at the floor succeeds; one below the floor is rejected.
    """
    calldata = b"\x01" * 100
    intrinsic_cost = fork.transaction_intrinsic_cost_calculator()
    floor_cost = fork.transaction_data_floor_cost_calculator()

    regular_gas = intrinsic_cost(
        calldata=calldata,
        return_cost_deducted_prior_execution=True,
    )
    floor_gas = floor_cost(data=calldata)
    assert floor_gas > regular_gas, "floor must exceed regular for test"

    if above_floor:
        gas_limit = floor_gas
        error = None
    else:
        # Between regular and floor: satisfies regular but not floor
        gas_limit = (regular_gas + floor_gas) // 2
        error = TransactionException.INTRINSIC_GAS_BELOW_FLOOR_GAS_COST

    tx = Transaction(
        to=pre.fund_eoa(0),
        data=calldata,
        gas_limit=gas_limit,
        sender=pre.fund_eoa(),
        error=error,
    )

    state_test(pre=pre, post={}, tx=tx)


@pytest.mark.parametrize("block_gas_limit", BLOCK_GAS_LIMITS)
@pytest.mark.valid_from("EIP8037")
def test_create_state_gas_scales_with_cpsb(
    state_test: StateTestFiller,
    pre: Alloc,
    block_gas_limit: int,
    fork: Fork,
) -> None:
    """
    Test CREATE new-account state gas scales with block gas limit.

    State gas for a CREATE is 112 * cpsb (new account) plus
    code_size * cpsb (code deposit).
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    env = Environment(gas_limit=block_gas_limit)
    fork._env_gas_limit = block_gas_limit
    create_state_gas = fork.create_state_gas(code_size=1)

    storage = Storage()
    contract = pre.deploy_contract(
        code=(
            Op.SSTORE(
                storage.store_next(1, "create_success"),
                Op.GT(Op.CREATE(0, 0, 1), 0),
            )
        ),
    )

    tx_gas = min(gas_limit_cap + create_state_gas, block_gas_limit)
    tx = Transaction(
        to=contract,
        gas_limit=tx_gas,
        sender=pre.fund_eoa(),
    )

    post = {contract: Account(storage=storage)}
    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.parametrize("block_gas_limit", BLOCK_GAS_LIMITS)
@pytest.mark.valid_from("EIP8037")
def test_call_new_account_state_gas_scales_with_cpsb(
    state_test: StateTestFiller,
    pre: Alloc,
    block_gas_limit: int,
    fork: Fork,
) -> None:
    """
    Test CALL value transfer to empty account scales with block gas limit.

    Sending value to a non-existent account charges 112 * cpsb
    of state gas for account creation.
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    env = Environment(gas_limit=block_gas_limit)
    fork._env_gas_limit = block_gas_limit
    gas_costs = fork.gas_costs()
    new_account_state_gas = gas_costs.NEW_ACCOUNT

    empty = pre.fund_eoa(0)
    storage = Storage()
    contract = pre.deploy_contract(
        code=(
            Op.SSTORE(
                storage.store_next(1, "call_success"),
                Op.CALL(gas=100_000, address=empty, value=1),
            )
        ),
        balance=1,
    )

    tx_gas = min(gas_limit_cap + new_account_state_gas, block_gas_limit)
    tx = Transaction(
        to=contract,
        gas_limit=tx_gas,
        sender=pre.fund_eoa(),
    )

    post = {contract: Account(storage=storage)}
    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.parametrize("block_gas_limit", BLOCK_GAS_LIMITS)
@pytest.mark.valid_from("EIP8037")
def test_selfdestruct_new_beneficiary_scales_with_cpsb(
    state_test: StateTestFiller,
    pre: Alloc,
    block_gas_limit: int,
    fork: Fork,
) -> None:
    """
    Test SELFDESTRUCT to new beneficiary scales with block gas limit.

    Destructing to a non-existent address with balance charges
    112 * cpsb of state gas for the new beneficiary account.
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    env = Environment(gas_limit=block_gas_limit)
    fork._env_gas_limit = block_gas_limit
    gas_costs = fork.gas_costs()
    new_account_state_gas = gas_costs.NEW_ACCOUNT

    beneficiary = pre.fund_eoa(0)
    storage = Storage()
    caller = pre.deploy_contract(
        code=(
            Op.SSTORE(
                storage.store_next(1, "selfdestruct_ran"),
                1,
            )
            + Op.SELFDESTRUCT(beneficiary)
        ),
        balance=1,
    )

    tx_gas = min(gas_limit_cap + new_account_state_gas, block_gas_limit)
    tx = Transaction(
        to=caller,
        gas_limit=tx_gas,
        sender=pre.fund_eoa(),
    )

    post = {caller: Account(storage=storage)}
    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.parametrize("block_gas_limit", BLOCK_GAS_LIMITS)
@pytest.mark.valid_from("EIP8037")
def test_sstore_refund_scales_with_cpsb(
    state_test: StateTestFiller,
    pre: Alloc,
    block_gas_limit: int,
    fork: Fork,
) -> None:
    """
    Test SSTORE restoration refund scales with block gas limit.

    Zero-to-nonzero-to-zero in the same tx refunds the state gas
    (32 * cpsb) via refund_counter.
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    env = Environment(gas_limit=block_gas_limit)
    fork._env_gas_limit = block_gas_limit
    sstore_state_gas = fork.sstore_state_gas()

    contract = pre.deploy_contract(
        code=(Op.SSTORE(0, 1) + Op.SSTORE(0, 0)),
    )

    tx_gas = min(gas_limit_cap + sstore_state_gas, block_gas_limit)
    tx = Transaction(
        to=contract,
        gas_limit=tx_gas,
        sender=pre.fund_eoa(),
    )

    post = {contract: Account(storage={0: 0})}
    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.parametrize("block_gas_limit", BLOCK_GAS_LIMITS)
@pytest.mark.valid_from("EIP8037")
def test_auth_state_gas_scales_with_cpsb(
    state_test: StateTestFiller,
    pre: Alloc,
    block_gas_limit: int,
    fork: Fork,
) -> None:
    """
    Test SetCode authorization state gas scales with block gas limit.

    A type-4 tx with one authorization charges (112 + 23) * cpsb
    of intrinsic state gas for the new account delegation.
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    env = Environment(gas_limit=block_gas_limit)
    fork._env_gas_limit = block_gas_limit
    auth_state_gas = fork.transaction_intrinsic_state_gas(
        authorization_count=1,
    )

    delegate = pre.deploy_contract(code=Op.SSTORE(0, 1))
    signer = pre.fund_eoa()

    storage = Storage()
    target = pre.deploy_contract(
        code=Op.SSTORE(
            storage.store_next(1, "delegated_call_success"),
            Op.CALL(gas=100_000, address=signer),
        ),
    )

    tx_gas = min(gas_limit_cap + auth_state_gas, block_gas_limit)
    tx = Transaction(
        ty=4,
        to=target,
        gas_limit=tx_gas,
        sender=pre.fund_eoa(),
        authorization_list=[
            AuthorizationTuple(
                address=delegate,
                nonce=0,
                signer=signer,
            ),
        ],
    )

    post = {target: Account(storage=storage)}
    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.parametrize(
    "block_gas_limit",
    [
        pytest.param(1_000_000, id="1M"),
        pytest.param(5_000_000, id="5M"),
        pytest.param(10_000_000, id="10M"),
    ],
)
@pytest.mark.valid_from("EIP8037")
def test_cpsb_underflow_boundary(
    state_test: StateTestFiller,
    pre: Alloc,
    block_gas_limit: int,
) -> None:
    """
    Test cpsb floors at 1 when quantized value < OFFSET.

    At very low gas limits the quantized value can be less than
    CPSB_OFFSET (9578). Clients must return max(quantized - OFFSET, 1)
    rather than underflowing.
    """
    assert Spec.cost_per_state_byte(block_gas_limit) == 1
    env = Environment(gas_limit=block_gas_limit)

    contract = pre.deploy_contract(
        code=Op.SSTORE(0, 1),
    )

    tx = Transaction(
        to=contract,
        gas_limit=block_gas_limit,
        sender=pre.fund_eoa(),
    )

    post = {contract: Account(storage={0: 1})}
    state_test(env=env, pre=pre, post=post, tx=tx)
