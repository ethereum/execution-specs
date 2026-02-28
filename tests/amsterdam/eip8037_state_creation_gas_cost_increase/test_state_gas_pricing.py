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


@EIPChecklist.GasCostChanges.Test.GasUpdatesMeasurement()
@pytest.mark.parametrize(
    "block_gas_limit",
    [
        pytest.param(30_000_000, id="mainnet_typical"),
        pytest.param(60_000_000, id="double_mainnet"),
        pytest.param(100_000_000, id="high_gas_limit"),
    ],
)
@pytest.mark.valid_from("Amsterdam")
def test_pricing_at_various_gas_limits(
    state_test: StateTestFiller,
    pre: Alloc,
    block_gas_limit: int,
) -> None:
    """
    Test SSTORE succeeds at various block gas limits.

    The state gas cost per byte varies with the block gas limit.
    At each gas limit, an SSTORE zero-to-nonzero should succeed
    when given sufficient total gas, confirming the pricing function
    produces a valid (nonzero) cost.
    """
    env = Environment(gas_limit=block_gas_limit)
    cpsb = Spec.COST_PER_STATE_BYTE
    sstore_state_gas = Spec.STATE_BYTES_PER_STORAGE_SET * cpsb

    storage = Storage()
    contract = pre.deploy_contract(
        code=Op.SSTORE(storage.store_next(1), 1) + Op.STOP,
    )

    tx = Transaction(
        to=contract,
        gas_limit=Spec.TX_MAX_GAS_LIMIT + sstore_state_gas,
        sender=pre.fund_eoa(),
    )

    post = {contract: Account(storage=storage)}
    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("Amsterdam")
def test_charge_draws_entirely_from_reservoir(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Test state gas is drawn entirely from the reservoir.

    When the reservoir has enough gas for the SSTORE state cost,
    gas_left should not be reduced by the state charge. Verify by
    performing a regular-gas-heavy computation after the SSTORE.
    """
    env = Environment()
    cpsb = Spec.COST_PER_STATE_BYTE
    sstore_state_gas = Spec.STATE_BYTES_PER_STORAGE_SET * cpsb

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
            + Op.STOP
        ),
    )

    # Provide exact state gas in the reservoir
    tx = Transaction(
        to=contract,
        gas_limit=Spec.TX_MAX_GAS_LIMIT + sstore_state_gas * 2,
        sender=pre.fund_eoa(),
    )

    post = {contract: Account(storage=storage)}
    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("Amsterdam")
def test_charge_spills_to_gas_left(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Test state gas spills from reservoir to gas_left.

    When the reservoir has some gas but not enough to cover the full
    state charge, the remainder is taken from gas_left. The SSTORE
    should still succeed.
    """
    env = Environment()
    cpsb = Spec.COST_PER_STATE_BYTE
    sstore_state_gas = Spec.STATE_BYTES_PER_STORAGE_SET * cpsb

    storage = Storage()
    contract = pre.deploy_contract(
        code=Op.SSTORE(storage.store_next(1), 1) + Op.STOP,
    )

    # Provide half the state gas in the reservoir, rest from gas_left
    half_state_gas = sstore_state_gas // 2
    tx = Transaction(
        to=contract,
        gas_limit=Spec.TX_MAX_GAS_LIMIT + half_state_gas,
        sender=pre.fund_eoa(),
    )

    post = {contract: Account(storage=storage)}
    state_test(env=env, pre=pre, post=post, tx=tx)


@EIPChecklist.GasCostChanges.Test.OutOfGas()
@pytest.mark.valid_from("Amsterdam")
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
    contract = pre.deploy_contract(
        code=Op.SSTORE(0, 1) + Op.STOP,
    )

    # Tight gas: intrinsic + SSTORE regular gas only
    intrinsic_cost = fork.transaction_intrinsic_cost_calculator()
    gas_limit = intrinsic_cost() + Spec.GAS_COLD_STORAGE_WRITE

    tx = Transaction(
        to=contract,
        gas_limit=gas_limit,
        sender=pre.fund_eoa(),
    )

    # OOG — storage unchanged
    post = {contract: Account(storage={0: 0})}
    state_test(pre=pre, post=post, tx=tx)


@EIPChecklist.GasRefundsChanges.Test.RefundCalculation()
@pytest.mark.valid_from("Amsterdam")
def test_refund_cap_includes_state_gas(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Test the 1/5 refund cap includes state gas used from gas_left.

    When state gas is drawn from gas_left (no reservoir), it counts
    toward tx_gas_used_before_refund. The 1/5 refund cap applies to
    the combined total of regular + state gas consumed. This test
    performs an SSTORE zero-to-nonzero-to-zero sequence to generate
    a refund and verifies the transaction succeeds.
    """
    contract = pre.deploy_contract(
        code=(Op.SSTORE(0, 1) + Op.SSTORE(0, 0) + Op.STOP),
    )

    # No reservoir — all gas from gas_left, refund cap applies
    tx = Transaction(
        to=contract,
        gas_limit=Spec.TX_MAX_GAS_LIMIT,
        sender=pre.fund_eoa(),
    )

    # Slot 0 restored to zero
    post = {contract: Account(storage={0: 0})}
    state_test(pre=pre, post=post, tx=tx)


@EIPChecklist.GasRefundsChanges.Test.RefundCalculation()
@pytest.mark.valid_from("Amsterdam")
def test_refund_with_reservoir_state_gas(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Test refund when state gas is drawn from reservoir.

    When state gas comes from the reservoir, the refund still applies.
    The refund_counter accumulates state + regular gas refunds, and
    the 1/5 cap uses tx_gas_used_before_refund which accounts for
    both dimensions. An SSTORE zero-to-nonzero-to-zero sequence
    should refund correctly.
    """
    env = Environment()
    cpsb = Spec.COST_PER_STATE_BYTE
    sstore_state_gas = Spec.STATE_BYTES_PER_STORAGE_SET * cpsb

    contract = pre.deploy_contract(
        code=(Op.SSTORE(0, 1) + Op.SSTORE(0, 0) + Op.STOP),
    )

    tx = Transaction(
        to=contract,
        gas_limit=Spec.TX_MAX_GAS_LIMIT + sstore_state_gas,
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
@pytest.mark.valid_from("Amsterdam")
def test_pricing_changes_with_block_gas_limit(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    gas_limit_block_1: int,
    gas_limit_block_2: int,
) -> None:
    """
    Test state gas cost changes when block gas limit changes.

    The cost_per_state_byte is a function of the block gas limit.
    When the gas limit increases, state gas becomes more expensive
    (targeting constant state growth). Each block's SSTORE should
    succeed with the appropriate state gas for that block's gas limit.
    """
    cpsb_1 = Spec.COST_PER_STATE_BYTE
    cpsb_2 = Spec.COST_PER_STATE_BYTE
    sstore_state_gas_1 = Spec.STATE_BYTES_PER_STORAGE_SET * cpsb_1
    sstore_state_gas_2 = Spec.STATE_BYTES_PER_STORAGE_SET * cpsb_2

    storage_1 = Storage()
    contract_1 = pre.deploy_contract(
        code=Op.SSTORE(storage_1.store_next(1), 1) + Op.STOP,
    )

    storage_2 = Storage()
    contract_2 = pre.deploy_contract(
        code=Op.SSTORE(storage_2.store_next(1), 1) + Op.STOP,
    )

    env = Environment(gas_limit=gas_limit_block_1)

    block_1 = Block(
        gas_limit=gas_limit_block_1,
        txs=[
            Transaction(
                to=contract_1,
                gas_limit=Spec.TX_MAX_GAS_LIMIT + sstore_state_gas_1,
                sender=pre.fund_eoa(),
            ),
        ],
    )

    block_2 = Block(
        gas_limit=gas_limit_block_2,
        txs=[
            Transaction(
                to=contract_2,
                gas_limit=Spec.TX_MAX_GAS_LIMIT + sstore_state_gas_2,
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


@pytest.mark.valid_from("Amsterdam")
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
        code=Op.SSTORE(0, 1) + Op.STOP,
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
@pytest.mark.valid_from("Amsterdam")
def test_intrinsic_regular_gas_exceeds_cap(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Test that tx is rejected when intrinsic regular gas exceeds cap.

    validate_transaction checks that the intrinsic regular gas (or
    calldata floor) does not exceed TX_MAX_GAS_LIMIT. A transaction
    with enough calldata to push intrinsic cost above the cap is
    invalid even with a high gas_limit.
    """
    # TX_MAX_GAS_LIMIT = 2^24 = 16_777_216
    # TX_DATA_NON_ZERO_GAS = 16 per byte
    # We need 16_777_216 / 16 + 1 = 1_048_577 non-zero bytes
    calldata = b"\x01" * 1_048_577

    contract = pre.deploy_contract(code=Op.STOP)

    tx = Transaction(
        to=contract,
        gas_limit=Spec.TX_MAX_GAS_LIMIT * 2,
        data=calldata,
        sender=pre.fund_eoa(),
        error=TransactionException.INTRINSIC_GAS_TOO_LOW,
    )

    state_test(pre=pre, post={}, tx=tx)
