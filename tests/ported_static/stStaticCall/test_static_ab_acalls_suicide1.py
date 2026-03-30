"""
Test_static_ab_acalls_suicide1.

Ported from:
state_tests/stStaticCall/static_ABAcallsSuicide1Filler.json
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
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stStaticCall/static_ABAcallsSuicide1Filler.json"],
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
def test_static_ab_acalls_suicide1(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test_static_ab_acalls_suicide1."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    contract_0 = Address(0x095E7BAEA6A6C7C4C2DFEB977EFAC326AF552D87)
    contract_1 = Address(0x945304EB96065B2A98B57A48A06AE28D285A71B5)
    sender = EOA(
        key=0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
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
    # {  (MSTORE 0 (CALLDATALOAD 0)) (STATICCALL (CALLDATALOAD 0) 0x945304eb96065b2a98b57a48a06ae28d285a71b5 0 32 0 0)   }  # noqa: E501
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x0, value=Op.CALLDATALOAD(offset=0x0))
        + Op.STATICCALL(
            gas=Op.CALLDATALOAD(offset=0x0),
            address=0x945304EB96065B2A98B57A48A06AE28D285A71B5,
            args_offset=0x0,
            args_size=0x20,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address(0x095E7BAEA6A6C7C4C2DFEB977EFAC326AF552D87),  # noqa: E501
    )
    # Source: lll
    # {  (MSTORE 0 (CALLDATALOAD 0))  (STATICCALL (SUB (CALLDATALOAD 0) 50000) 0x095e7baea6a6c7c4c2dfeb977efac326af552d87 0 32 0 0) (SELFDESTRUCT 0x0f572e5295c57f15886f9b263e2f6d2d6c7b5ec6) }  # noqa: E501
    contract_1 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x0, value=Op.CALLDATALOAD(offset=0x0))
        + Op.POP(
            Op.STATICCALL(
                gas=Op.SUB(Op.CALLDATALOAD(offset=0x0), 0xC350),
                address=0x95E7BAEA6A6C7C4C2DFEB977EFAC326AF552D87,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.SELFDESTRUCT(address=0xF572E5295C57F15886F9B263E2F6D2D6C7B5EC6)
        + Op.STOP,
        balance=23,
        nonce=0,
        address=Address(0x945304EB96065B2A98B57A48A06AE28D285A71B5),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    tx_data = [
        Hash(0x186A0),
        Hash(0x486A0),
    ]
    tx_gas = [10000000]
    tx_value = [100000]

    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        value=tx_value[v],
    )

    post = {
        contract_0: Account(storage={}),
        Address(
            0x0F572E5295C57F15886F9B263E2F6D2D6C7B5EC6
        ): Account.NONEXISTENT,
        contract_1: Account(storage={}, balance=23),
        sender: Account(nonce=1),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
