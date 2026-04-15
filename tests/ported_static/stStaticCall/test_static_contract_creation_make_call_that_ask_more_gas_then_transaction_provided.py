"""
Test_static_contract_creation_make_call_that_ask_more_gas_then_transacti...

Ported from:
state_tests/stStaticCall/static_contractCreationMakeCallThatAskMoreGasThenTransactionProvidedFiller.json
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Environment,
    StateTestFiller,
    Transaction,
    compute_create_address,
)
from execution_testing.forks import Fork
from execution_testing.specs.static_state.expect_section import (
    resolve_expect_post,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    [
        "state_tests/stStaticCall/static_contractCreationMakeCallThatAskMoreGasThenTransactionProvidedFiller.json"  # noqa: E501
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
        pytest.param(
            2,
            0,
            0,
            id="d2",
        ),
        pytest.param(
            3,
            0,
            0,
            id="d3",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_static_contract_creation_make_call_that_ask_more_gas_then_transaction_provided(  # noqa: E501
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test_static_contract_creation_make_call_that_ask_more_gas_then_tran..."""  # noqa: E501
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    contract_0 = Address(0xB94F5374FCE5EDBC8E2A8697C15331677E6EBF0B)
    contract_1 = Address(0x1000000000000000000000000000000000000001)
    contract_2 = Address(0x2000000000000000000000000000000000000001)
    contract_3 = Address(0x3000000000000000000000000000000000000001)
    contract_4 = Address(0x4000000000000000000000000000000000000001)
    contract_5 = Address(0x5000000000000000000000000000000000000001)
    contract_6 = Address(0x4000000000000000000000000000000000000004)
    sender = pre.fund_eoa(amount=0x10C8E0)

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    # Source: lll
    # {(SSTORE 1 1)}
    contract_1 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1) + Op.STOP,
        balance=0x186A0,
        nonce=0,
    )
    # Source: lll
    # {(MSTORE 1 1)}
    contract_2 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x1, value=0x1) + Op.STOP,
        balance=0x186A0,
        nonce=0,
    )
    # Source: lll
    # { (def 'i 0x80) (for {} (< @i 50000) [i](+ @i 1) (EXTCODESIZE 1)) }
    contract_3 = pre.deploy_contract(  # noqa: F841
        code=Op.JUMPDEST
        + Op.JUMPI(
            pc=0x1C, condition=Op.ISZERO(Op.LT(Op.MLOAD(offset=0x80), 0xC350))
        )
        + Op.POP(Op.EXTCODESIZE(address=0x1))
        + Op.MSTORE(offset=0x80, value=Op.ADD(Op.MLOAD(offset=0x80), 0x1))
        + Op.JUMP(pc=0x0)
        + Op.JUMPDEST
        + Op.STOP,
        balance=0x186A0,
        nonce=0,
    )
    # Source: lll
    # { (MSTORE 1 1) }
    contract_6 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x1, value=0x1) + Op.STOP,
        balance=0x186A0,
        nonce=0,
    )
    # Source: lll
    # {(STATICCALL 50000 0x1000000000000000000000000000000000000001 0 64 0 64)}
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=Op.STATICCALL(
            gas=0xC350,
            address=contract_1,
            args_offset=0x0,
            args_size=0x40,
            ret_offset=0x0,
            ret_size=0x40,
        )
        + Op.STOP,
        balance=0x186A0,
        nonce=0,
    )
    # Source: lll
    # { (CALLCODE 1000000 0x4000000000000000000000000000000000000004 0 0 0 0 0) }  # noqa: E501
    contract_5 = pre.deploy_contract(  # noqa: F841
        code=Op.CALLCODE(
            gas=0xF4240,
            address=contract_6,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        balance=0x186A0,
        nonce=0,
    )
    # Source: lll
    # { (CALLCODE 1000 0x4000000000000000000000000000000000000004 0 0 0 0 0) }
    contract_4 = pre.deploy_contract(  # noqa: F841
        code=Op.CALLCODE(
            gas=0x3E8,
            address=contract_6,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        balance=0x186A0,
        nonce=0,
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": 0, "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                compute_create_address(address=sender, nonce=0): Account(
                    nonce=1
                )
            },
        },
        {
            "indexes": {"data": 1, "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                compute_create_address(address=sender, nonce=0): Account(
                    nonce=1
                )
            },
        },
        {
            "indexes": {"data": 2, "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                compute_create_address(address=sender, nonce=0): Account(
                    nonce=1
                )
            },
        },
        {
            "indexes": {"data": 3, "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                compute_create_address(address=sender, nonce=0): Account(
                    nonce=1
                )
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx_data = [
        Op.STATICCALL(
            gas=0xC350,
            address=contract_1,
            args_offset=0x0,
            args_size=0x40,
            ret_offset=0x0,
            ret_size=0x40,
        ),
        Op.STATICCALL(
            gas=0xC350,
            address=contract_2,
            args_offset=0x0,
            args_size=0x40,
            ret_offset=0x0,
            ret_size=0x40,
        ),
        Op.STATICCALL(
            gas=0xC350,
            address=contract_3,
            args_offset=0x0,
            args_size=0x40,
            ret_offset=0x0,
            ret_size=0x40,
        ),
        Op.STATICCALL(
            gas=0xC350,
            address=contract_4,
            args_offset=0x0,
            args_size=0x40,
            ret_offset=0x0,
            ret_size=0x40,
        ),
    ]
    tx_gas = [96000]

    tx = Transaction(
        sender=sender,
        to=None,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
