"""
test_static_call_and_callcode_consume_more_gas_then_transaction_has

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
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op
from execution_testing.forks import Fork
from execution_testing.specs.static_state.expect_section import (
    resolve_expect_post,
)

REFERENCE_SPEC_GIT_PATH = "N/A"

REFERENCE_SPEC_VERSION = "N/A"

TX_DATA = [
    "000000000000000000000000438f316ba8e30f69666a3477a7f5cd26235d3cbb",
    "0000000000000000000000007d77eaf6dc93e2b7b83a8e06314af1ce47cd2596",
]
TX_GAS = [600000]
TX_VALUE = [0]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d])


@pytest.mark.ported_from(
    ["state_tests/stStaticCall/static_CallAndCallcodeConsumeMoreGasThenTransactionHasFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0, 0, 0,
            id="d0",
        ),
        pytest.param(
            1, 0, 0,
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
    """test_static_call_and_callcode_consume_more_gas_then_transaction_has"""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x4f31b3206fbf0e0e598b9b1a7d8ac86302a0ff1d8930738f1bebae9b67173e52
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    pre[sender] = Account(balance=0xe8d4a51000)
    # Source: lll
    # {  [[ 0 ]] (CALL (GAS) (CALLDATALOAD 0) (CALLVALUE) 0 0 0 0) [[ 1 ]] 1 }
    target = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.CALL(gas=Op.GAS, address=Op.CALLDATALOAD(offset=0x0), value=Op.CALLVALUE, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))  # noqa: E501
        + Op.SSTORE(key=0x1, value=0x1) + Op.STOP,
        nonce=0,
        address=Address("0xc0e4183389eb57f779a986d8c878f89b9401dc8e"),  # noqa: E501
    )
    # Source: lll
    # {  (SSTORE 9 (STATICCALL 600000 <contract:0x1000000000000000000000000000000000000103> 0 0 0 0)) (SSTORE 10 (CALLCODE 600000 <contract:0x1000000000000000000000000000000000000103> 0 0 0 0 0)) }
    addr_0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b = pre.deploy_contract(
        code=Op.SSTORE(key=0x9, value=Op.STATICCALL(gas=0x927c0, address=0xfd59abae521384b5731ac657616680219fbc423d, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))  # noqa: E501
        + Op.SSTORE(key=0xa, value=Op.CALLCODE(gas=0x927c0, address=0xfd59abae521384b5731ac657616680219fbc423d, value=0x0, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))  # noqa: E501
        + Op.STOP,
        nonce=0,
        address=Address("0x438f316ba8e30f69666a3477a7f5cd26235d3cbb"),  # noqa: E501
    )
    # Source: lll
    # { (SSTORE 0 0x12) }
    addr_0x1000000000000000000000000000000000000103 = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=0x12) + Op.STOP,
        nonce=0,
        address=Address("0xfd59abae521384b5731ac657616680219fbc423d"),  # noqa: E501
    )
    # Source: lll
    # {  (SSTORE 9 (STATICCALL 600000 <contract:0x2000000000000000000000000000000000000103> 0 0 0 0)) (SSTORE 10 (CALLCODE 600000 <contract:0x1000000000000000000000000000000000000103> 0 0 0 0 0)) }
    addr_0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b = pre.deploy_contract(
        code=Op.SSTORE(key=0x9, value=Op.STATICCALL(gas=0x927c0, address=0x9620801959b49d6d1bd08f0cdafda5d87e900403, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))  # noqa: E501
        + Op.SSTORE(key=0xa, value=Op.CALLCODE(gas=0x927c0, address=0xfd59abae521384b5731ac657616680219fbc423d, value=0x0, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))  # noqa: E501
        + Op.STOP,
        nonce=0,
        address=Address("0x7d77eaf6dc93e2b7b83a8e06314af1ce47cd2596"),  # noqa: E501
    )
    # Source: lll
    # { (MSTORE 0 0x12) }
    addr_0x2000000000000000000000000000000000000103 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x0, value=0x12) + Op.STOP,
        nonce=0,
        address=Address("0x9620801959b49d6d1bd08f0cdafda5d87e900403"),  # noqa: E501
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {'data': 0, 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        addr_0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b: Account(storage={0: 0, 8: 0, 9: 0, 10: 0}),
        addr_0x1000000000000000000000000000000000000103: Account(
                storage={},
                code=bytes.fromhex("601260005500"),
                nonce=0,
            ),
    },
        },
        {
            "indexes": {'data': 1, 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        addr_0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b: Account(storage={0: 18, 9: 1, 10: 1}),
        addr_0x2000000000000000000000000000000000000103: Account(
                storage={},
                code=bytes.fromhex("601260005200"),
                nonce=0,
            ),
    },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx = Transaction(
        sender=sender,
        to=target,
        data=_tx_data(d),
        gas_limit=TX_GAS[g],
        nonce=0,
        gas_price=10,
        error=_exc,
    )


    state_test(env=env, pre=pre, post=post, tx=tx)
