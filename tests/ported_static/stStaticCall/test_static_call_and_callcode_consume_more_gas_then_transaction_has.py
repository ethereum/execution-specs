"""
Test_static_call_and_callcode_consume_more_gas_then_transaction_has.

Ported from:
state_tests/stStaticCall/static_CallAndCallcodeConsumeMoreGasThenTransactionHasFiller.json
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
    [
        "state_tests/stStaticCall/static_CallAndCallcodeConsumeMoreGasThenTransactionHasFiller.json"  # noqa: E501
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
def test_static_call_and_callcode_consume_more_gas_then_transaction_has(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test_static_call_and_callcode_consume_more_gas_then_transaction_has."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = EOA(
        key=0x4F31B3206FBF0E0E598B9B1A7D8AC86302A0FF1D8930738F1BEBAE9B67173E52
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
    # Source: lll
    # {  [[ 0 ]] (CALL (GAS) (CALLDATALOAD 0) (CALLVALUE) 0 0 0 0) [[ 1 ]] 1 }
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x0,
            value=Op.CALL(
                gas=Op.GAS,
                address=Op.CALLDATALOAD(offset=0x0),
                value=Op.CALLVALUE,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.SSTORE(key=0x1, value=0x1)
        + Op.STOP,
        nonce=0,
        address=Address(0xC0E4183389EB57F779A986D8C878F89B9401DC8E),  # noqa: E501
    )
    # Source: lll
    # {  (SSTORE 9 (STATICCALL 600000 <contract:0x1000000000000000000000000000000000000103> 0 0 0 0)) (SSTORE 10 (CALLCODE 600000 <contract:0x1000000000000000000000000000000000000103> 0 0 0 0 0)) }  # noqa: E501
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x9,
            value=Op.STATICCALL(
                gas=0x927C0,
                address=0xFD59ABAE521384B5731AC657616680219FBC423D,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.SSTORE(
            key=0xA,
            value=Op.CALLCODE(
                gas=0x927C0,
                address=0xFD59ABAE521384B5731AC657616680219FBC423D,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.STOP,
        nonce=0,
        address=Address(0x438F316BA8E30F69666A3477A7F5CD26235D3CBB),  # noqa: E501
    )
    # Source: lll
    # { (SSTORE 0 0x12) }
    addr_2 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x12) + Op.STOP,
        nonce=0,
        address=Address(0xFD59ABAE521384B5731AC657616680219FBC423D),  # noqa: E501
    )
    # Source: lll
    # {  (SSTORE 9 (STATICCALL 600000 <contract:0x2000000000000000000000000000000000000103> 0 0 0 0)) (SSTORE 10 (CALLCODE 600000 <contract:0x1000000000000000000000000000000000000103> 0 0 0 0 0)) }  # noqa: E501
    addr_3 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x9,
            value=Op.STATICCALL(
                gas=0x927C0,
                address=0x9620801959B49D6D1BD08F0CDAFDA5D87E900403,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.SSTORE(
            key=0xA,
            value=Op.CALLCODE(
                gas=0x927C0,
                address=0xFD59ABAE521384B5731AC657616680219FBC423D,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.STOP,
        nonce=0,
        address=Address(0x7D77EAF6DC93E2B7B83A8E06314AF1CE47CD2596),  # noqa: E501
    )
    # Source: lll
    # { (MSTORE 0 0x12) }
    addr_4 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x0, value=0x12) + Op.STOP,
        nonce=0,
        address=Address(0x9620801959B49D6D1BD08F0CDAFDA5D87E900403),  # noqa: E501
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": 0, "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                addr: Account(storage={0: 0, 8: 0, 9: 0, 10: 0}),
                addr_2: Account(
                    storage={},
                    code=bytes.fromhex("601260005500"),
                    nonce=0,
                ),
            },
        },
        {
            "indexes": {"data": 1, "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                addr_3: Account(storage={0: 18, 9: 1, 10: 1}),
                addr_4: Account(
                    storage={},
                    code=bytes.fromhex("601260005200"),
                    nonce=0,
                ),
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx_data = [
        Hash(addr, left_padding=True),
        Hash(addr_3, left_padding=True),
    ]
    tx_gas = [600000]

    tx = Transaction(
        sender=sender,
        to=target,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
