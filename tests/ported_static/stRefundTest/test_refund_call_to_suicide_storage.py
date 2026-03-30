"""
Test_refund_call_to_suicide_storage.

Ported from:
state_tests/stRefundTest/refund_CallToSuicideStorageFiller.json
"""

import pytest
from execution_testing import (
    EOA,
    Account,
    Address,
    Alloc,
    Environment,
    Hash,
    StateTestFiller,
    Transaction,
)
from execution_testing.forks import Fork
from execution_testing.specs.static_state.expect_section import (
    resolve_expect_post,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stRefundTest/refund_CallToSuicideStorageFiller.json"],
)
@pytest.mark.valid_from("Cancun")
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
def test_refund_call_to_suicide_storage(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test_refund_call_to_suicide_storage."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = EOA(
        key=0x6F0117D3E9C684C7D6E1E6B79DC3880DA2BEBE77C765B171C062FDFFD38A673F
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    # Source: lll
    # { [[ 0 ]] (CALL (CALLDATALOAD 0) <contract:0xaaae7baea6a6c7c4c2dfeb977efac326af552aaa> 0 0 0 0 0 )}  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x0,
            value=Op.CALL(
                gas=Op.CALLDATALOAD(offset=0x0),
                address=0x9DEA1AD5123F3D8B91CFC830B1C602597883E97C,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.STOP,
        storage={1: 1},
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address(0x5BE4B33890F720EFF72BE0019B122E0FF75CB937),  # noqa: E501
    )
    pre[sender] = Account(balance=0x2540BE400)
    # Source: lll
    # { (SELFDESTRUCT <contract:target:0x095e7baea6a6c7c4c2dfeb977efac326af552d87>) }  # noqa: E501
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.SELFDESTRUCT(
            address=0x5BE4B33890F720EFF72BE0019B122E0FF75CB937
        )
        + Op.STOP,
        storage={1: 1},
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address(0x9DEA1AD5123F3D8B91CFC830B1C602597883E97C),  # noqa: E501
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": 0, "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(
                    storage={0: 0, 1: 1}, balance=0xDE0B6B3A764000A
                ),
                sender: Account(nonce=1),
                addr: Account(storage={0: 0, 1: 1}),
            },
        },
        {
            "indexes": {"data": 1, "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(
                    storage={0: 1, 1: 1}, balance=0x1BC16D674EC8000A
                ),
                sender: Account(nonce=1),
                addr: Account(storage={1: 1}, balance=0, nonce=0),
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

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
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
