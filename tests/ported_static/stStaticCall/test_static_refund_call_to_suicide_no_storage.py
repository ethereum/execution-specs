"""
Test_static_refund_call_to_suicide_no_storage.

Ported from:
state_tests/stStaticCall/static_refund_CallToSuicideNoStorageFiller.json
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Environment,
    Hash,
    StateTestFiller,
    Transaction,
)
from execution_testing.forks import Fork
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    [
        "state_tests/stStaticCall/static_refund_CallToSuicideNoStorageFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.slow
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0,
            0,
            0,
            id="d0",
        ),
        pytest.param(
            1,
            0,
            0,
            id="d1",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_static_refund_call_to_suicide_no_storage(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test_static_refund_call_to_suicide_no_storage."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = pre.fund_eoa(amount=0x2540BE400)

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000000,
    )

    # Source: lll
    # { [[ 0 ]] (STATICCALL (CALLDATALOAD 0) <contract:0xaaae7baea6a6c7c4c2dfeb977efac326af552aaa> 0 0 0 0 ) [[ 2 ]] 1 }  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x0,
            value=Op.STATICCALL(
                gas=Op.CALLDATALOAD(offset=0x0),
                address=0x4FF65047CE9C85F968689E4369C10003026A41A9,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.SSTORE(key=0x2, value=0x1)
        + Op.STOP,
        storage={1: 1},
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address(0xA2A10D67C0F0864B703D90D9C36296AD8A547AE6),  # noqa: E501
    )
    # Source: lll
    # { (SELFDESTRUCT <contract:target:0x095e7baea6a6c7c4c2dfeb977efac326af552d87>) }  # noqa: E501
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.SELFDESTRUCT(
            address=0xA2A10D67C0F0864B703D90D9C36296AD8A547AE6
        )
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address(0x4FF65047CE9C85F968689E4369C10003026A41A9),  # noqa: E501
    )

    tx_data = [
        Hash(0x1F4),
        Hash(0x10000),
    ]
    tx_gas = [10000000]
    tx_value = [10]

    tx = Transaction(
        sender=sender,
        to=target,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        value=tx_value[v],
    )

    post = {
        target: Account(
            storage={0: 0, 1: 1, 2: 1},
            balance=0xDE0B6B3A764000A,
        ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
