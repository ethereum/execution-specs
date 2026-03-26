"""
test_static_call_ask_more_gas_on_depth2_then_transaction_has

Ported from:
state_tests/stStaticCall/static_CallAskMoreGasOnDepth2ThenTransactionHasFiller.json
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
    "000000000000000000000000ef69a9b2c20255fb7bd2b0ac7d45601a03d570b0",
    "0000000000000000000000008169dc735802bb5c18a777052cf4ce326b5fd725",
]
TX_GAS = [600000]
TX_VALUE = [0]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d])


@pytest.mark.ported_from(
    ["state_tests/stStaticCall/static_CallAskMoreGasOnDepth2ThenTransactionHasFiller.json"],
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
def test_static_call_ask_more_gas_on_depth2_then_transaction_has(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """test_static_call_ask_more_gas_on_depth2_then_transaction_has"""
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
    # { (SSTORE 8 1) (SSTORE 9 (STATICCALL 200000 <contract:0x1000000000000000000000000000000000000107> 0 0 0 0)) }
    addr_0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b = pre.deploy_contract(
        code=Op.SSTORE(key=0x8, value=0x1)
        + Op.SSTORE(key=0x9, value=Op.STATICCALL(gas=0x30d40, address=0xd9539c5a3dc4713d47a547bfc9a075bd97287080, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))  # noqa: E501
        + Op.STOP,
        nonce=0,
        address=Address("0xef69a9b2c20255fb7bd2b0ac7d45601a03d570b0"),  # noqa: E501
    )
    # Source: lll
    # { (MSTORE 8 (GAS)) (MSTORE 9 (STATICCALL 600000 <contract:0x1000000000000000000000000000000000000108> 0 0 0 0)) }
    addr_0x1000000000000000000000000000000000000107 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x8, value=Op.GAS)
        + Op.MSTORE(offset=0x9, value=Op.STATICCALL(gas=0x927c0, address=0x5044bfb29664a79de12215897c630dc8a11b0b97, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))
        + Op.STOP,
        nonce=0,
        address=Address("0xd9539c5a3dc4713d47a547bfc9a075bd97287080"),  # noqa: E501
    )
    # Source: lll
    # { (SSTORE 8 1)}
    addr_0x1000000000000000000000000000000000000108 = pre.deploy_contract(
        code=Op.SSTORE(key=0x8, value=0x1) + Op.STOP,
        nonce=0,
        address=Address("0x5044bfb29664a79de12215897c630dc8a11b0b97"),  # noqa: E501
    )
    # Source: lll
    # { (SSTORE 8 1) (SSTORE 9 (STATICCALL 200000 <contract:0x2000000000000000000000000000000000000107> 0 0 0 0)) }
    addr_0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b = pre.deploy_contract(
        code=Op.SSTORE(key=0x8, value=0x1)
        + Op.SSTORE(key=0x9, value=Op.STATICCALL(gas=0x30d40, address=0xe5a4d8074950ec8067d602848b666ca151b09c9f, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))  # noqa: E501
        + Op.STOP,
        nonce=0,
        address=Address("0x8169dc735802bb5c18a777052cf4ce326b5fd725"),  # noqa: E501
    )
    # Source: lll
    # { (MSTORE 8 (GAS)) (MSTORE 9 (STATICCALL 600000 <contract:0x2000000000000000000000000000000000000108> 0 0 0 0)) }
    addr_0x2000000000000000000000000000000000000107 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x8, value=Op.GAS)
        + Op.MSTORE(offset=0x9, value=Op.STATICCALL(gas=0x927c0, address=0x91b291a3336bc1357388354df18ca061b39e3745, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))
        + Op.STOP,
        nonce=0,
        address=Address("0xe5a4d8074950ec8067d602848b666ca151b09c9f"),  # noqa: E501
    )
    # Source: lll
    # { (MSTORE 8 (GAS))}
    addr_0x2000000000000000000000000000000000000108 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x8, value=Op.GAS) + Op.STOP,
        nonce=0,
        address=Address("0x91b291a3336bc1357388354df18ca061b39e3745"),  # noqa: E501
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {'data': 0, 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        addr_0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b: Account(storage={8: 1, 9: 1}),
        addr_0x1000000000000000000000000000000000000107: Account(storage={8: 0, 9: 0}),
        addr_0x1000000000000000000000000000000000000108: Account(storage={8: 0}),
        target: Account(storage={0: 1, 1: 1}),
    },
        },
        {
            "indexes": {'data': 1, 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        addr_0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b: Account(storage={8: 1, 9: 1}),
        addr_0x2000000000000000000000000000000000000107: Account(storage={8: 0, 9: 0}),
        addr_0x2000000000000000000000000000000000000108: Account(storage={8: 0}),
        target: Account(storage={0: 1, 1: 1}),
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
