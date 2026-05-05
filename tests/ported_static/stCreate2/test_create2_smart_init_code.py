"""
Create2SmartInitCode. create2 works different each time you call it.

Ported from:
state_tests/stCreate2/create2SmartInitCodeFiller.json
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
    ["state_tests/stCreate2/create2SmartInitCodeFiller.json"],
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
def test_create2_smart_init_code(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Create2SmartInitCode."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    contract_0 = Address(0x0F572E5295C57F15886F9B263E2F6D2D6C7B5EC6)
    contract_1 = Address(0x1F572E5295C57F15886F9B263E2F6D2D6C7B5EC6)
    contract_2 = Address(0xB94F5374FCE5EDBC8E2A8697C15331677E6EBF0B)
    sender = EOA(
        key=0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=47244640256,
    )

    pre[sender] = Account(balance=0x6400000000)
    # Source: lll
    # { (MSTORE 0 0x600060015414601157600a6000f3601a565b60016001556001ff5b) [[1]](CREATE2 1 5 27 0) [[2]](CREATE2 1 5 27 0) }  # noqa: E501
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(
            offset=0x0,
            value=0x600060015414601157600A6000F3601A565B60016001556001FF5B,
        )
        + Op.SSTORE(
            key=0x1,
            value=Op.CREATE2(value=0x1, offset=0x5, size=0x1B, salt=0x0),
        )
        + Op.SSTORE(
            key=0x2,
            value=Op.CREATE2(value=0x1, offset=0x5, size=0x1B, salt=0x0),
        )
        + Op.STOP,
        balance=100,
        nonce=0,
        address=Address(0x0F572E5295C57F15886F9B263E2F6D2D6C7B5EC6),  # noqa: E501
    )
    # Source: lll
    # { (MSTORE 0 0x600060015414601157600a6000f3601c565b6001600155600a6000f35b) [[1]](CREATE2 1 3 29 0) [[2]](CREATE2 1 5 27 0) }  # noqa: E501
    contract_1 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(
            offset=0x0,
            value=0x600060015414601157600A6000F3601C565B6001600155600A6000F35B,
        )
        + Op.SSTORE(
            key=0x1,
            value=Op.CREATE2(value=0x1, offset=0x3, size=0x1D, salt=0x0),
        )
        + Op.SSTORE(
            key=0x2,
            value=Op.CREATE2(value=0x1, offset=0x5, size=0x1B, salt=0x0),
        )
        + Op.STOP,
        balance=100,
        nonce=0,
        address=Address(0x1F572E5295C57F15886F9B263E2F6D2D6C7B5EC6),  # noqa: E501
    )
    # Source: lll
    # { (CALL (GAS) (CALLDATALOAD 0) 0 0 0 0 0) }
    contract_2 = pre.deploy_contract(  # noqa: F841
        code=Op.CALL(
            gas=Op.GAS,
            address=Op.CALLDATALOAD(offset=0x0),
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        balance=0x6400000000,
        nonce=0,
        address=Address(0xB94F5374FCE5EDBC8E2A8697C15331677E6EBF0B),  # noqa: E501
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": 0, "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                Address(0x0000000000000000000000000000000000000001): Account(
                    balance=1
                ),
                contract_0: Account(nonce=2),
            },
        },
        {
            "indexes": {"data": 1, "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                contract_1: Account(
                    storage={
                        1: 0xD27E800C69122409AC5609FE4DF903745F3988A0,
                        2: 0,
                    },
                ),
                Address(0xD27E800C69122409AC5609FE4DF903745F3988A0): Account(
                    storage={1: 1},
                    code=bytes.fromhex("00000000000000000000"),
                    nonce=1,
                ),
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx_data = [
        Hash(contract_0, left_padding=True),
        Hash(contract_1, left_padding=True),
    ]
    tx_gas = [400000]

    tx = Transaction(
        sender=sender,
        to=contract_2,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
