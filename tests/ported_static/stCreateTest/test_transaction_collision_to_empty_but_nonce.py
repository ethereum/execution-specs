"""
Test_transaction_collision_to_empty_but_nonce.

Ported from:
state_tests/stCreateTest/TransactionCollisionToEmptyButNonceFiller.json
"""

import pytest
from execution_testing import (
    EOA,
    Account,
    Address,
    Alloc,
    Environment,
    Header,
    StateTestFiller,
    Transaction,
)
from execution_testing.forks import Fork
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.gas_check
@pytest.mark.ported_from(
    [
        "state_tests/stCreateTest/TransactionCollisionToEmptyButNonceFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0,
            0,
            0,
            id="-g0-v0",
        ),
        pytest.param(
            0,
            0,
            1,
            id="-g0-v1",
        ),
        pytest.param(
            0,
            1,
            0,
            id="-g1-v0",
        ),
        pytest.param(
            0,
            1,
            1,
            id="-g1-v1",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_transaction_collision_to_empty_but_nonce(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test_transaction_collision_to_empty_but_nonce."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    contract_0 = Address(0x6295EE1B4F6DD65047762F924ECD367C17EABF8F)
    sender = EOA(
        key=0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    pre[sender] = Account(balance=0xE8D4A51000)
    pre[contract_0] = Account(balance=0, nonce=1)

    tx_data = [
        Op.SSTORE(key=0x1, value=0x1),
    ]
    tx_gas = [600000, 54000]
    tx_value = [0, 1]

    tx = Transaction(
        sender=sender,
        to=None,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        value=tx_value[v],
    )

    post = {
        sender: Account(nonce=1),
        contract_0: Account(storage={1: 0}, nonce=1),
    }

    # On collision, all execution gas is reclassified to regular and the
    # tx-time state reservoir is restored. Under EIP-8037 2D gas this
    # gives header.gas_used = max(intrinsic_regular + execution_gas,
    # intrinsic_state); pre-EIP-8037 the state component is zero, so the
    # same expression collapses to tx.gas.
    intrinsic_total = fork.transaction_intrinsic_cost_calculator()(
        calldata=bytes(tx_data[d]),
        contract_creation=True,
    )
    intrinsic_state = fork.create_state_gas()
    intrinsic_regular = intrinsic_total - intrinsic_state
    execution_gas = tx_gas[g] - intrinsic_total
    expected_header_gas_used = max(
        intrinsic_regular + execution_gas, intrinsic_state
    )

    state_test(
        env=env,
        pre=pre,
        post=post,
        tx=tx,
        blockchain_test_header_verify=Header(
            gas_used=expected_header_gas_used,
        ),
    )
