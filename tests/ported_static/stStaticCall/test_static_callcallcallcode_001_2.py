"""
test_static_callcallcallcode_001_2

Ported from:
state_tests/stStaticCall/static_callcallcallcode_001_2Filler.json
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
    "0000000000000000000000002f9ec0afcb4edcd7d38c6a48f5e36038263ca3cd",
    "000000000000000000000000bf23f3306533431b2ee5e4ca95e0a0834c090105",
]
TX_GAS = [3000000]
TX_VALUE = [0]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d])


@pytest.mark.ported_from(
    ["state_tests/stStaticCall/static_callcallcallcode_001_2Filler.json"],
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
def test_static_callcallcallcode_001_2(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """test_static_callcallcallcode_001_2"""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0xe04d1ac7ddda0c98397d56a0b501e960d4cd325a39286919ac23c1a07009a869
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=30000000,
    )

    # Source: lll
    # {  [[ 0 ]] (CALL (GAS) (CALLDATALOAD 0) (CALLVALUE) 0 0 0 0) [[ 1 ]] 1}
    target = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.CALL(gas=Op.GAS, address=Op.CALLDATALOAD(offset=0x0), value=Op.CALLVALUE, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))  # noqa: E501
        + Op.SSTORE(key=0x1, value=0x1) + Op.STOP,
        nonce=0,
        address=Address("0xe4552fdc3736d39144e64ad1a1e8253017b0c974"),  # noqa: E501
    )
    # Source: lll
    # {  [[ 0 ]] (STATICCALL 350000 <contract:0x1000000000000000000000000000000000000001> 0 64 0 64 ) }
    addr_0x1000000000000000000000000000000000000000 = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.STATICCALL(gas=0x55730, address=0x52bc8086d7f6ac48937cf1b98dfc6f4be0f75112, args_offset=0x0, args_size=0x40, ret_offset=0x0, ret_size=0x40))  # noqa: E501
        + Op.STOP,
        balance=0xde0b6b3a7640000,
        nonce=0,
        address=Address("0x2f9ec0afcb4edcd7d38c6a48f5e36038263ca3cd"),  # noqa: E501
    )
    # Source: lll
    # {  (STATICCALL 300000 <contract:0x1000000000000000000000000000000000000002> 0 64 0 64 ) (MSTORE 3 1) }
    addr_0x1000000000000000000000000000000000000001 = pre.deploy_contract(
        code=Op.POP(Op.STATICCALL(gas=0x493e0, address=0xffffaeb931552e5f094ca96a70be612da56b887, args_offset=0x0, args_size=0x40, ret_offset=0x0, ret_size=0x40))
        + Op.MSTORE(offset=0x3, value=0x1) + Op.STOP,
        balance=0xde0b6b3a7640000,
        nonce=0,
        address=Address("0x52bc8086d7f6ac48937cf1b98dfc6f4be0f75112"),  # noqa: E501
    )
    # Source: lll
    # {  [[ 2 ]] (CALLCODE 250000 <contract:0x1000000000000000000000000000000000000003> 3 0 64 0 64 ) }
    addr_0x1000000000000000000000000000000000000002 = pre.deploy_contract(
        code=Op.SSTORE(key=0x2, value=Op.CALLCODE(gas=0x3d090, address=0x2881a083ea775f78057a93f73110241fdb7398a9, value=0x3, args_offset=0x0, args_size=0x40, ret_offset=0x0, ret_size=0x40))  # noqa: E501
        + Op.STOP,
        balance=0xde0b6b3a7640000,
        nonce=0,
        address=Address("0x0ffffaeb931552e5f094ca96a70be612da56b887"),  # noqa: E501
    )
    # Source: lll
    # {  (MSTORE 1 0x11223344) }
    addr_0x1000000000000000000000000000000000000003 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x1, value=0x11223344) + Op.STOP,
        nonce=0,
        address=Address("0x2881a083ea775f78057a93f73110241fdb7398a9"),  # noqa: E501
    )
    # Source: lll
    # {  [[ 0 ]] (STATICCALL 350000 <contract:0x2000000000000000000000000000000000000001> 0 64 0 64 ) }
    addr_0x2000000000000000000000000000000000000000 = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.STATICCALL(gas=0x55730, address=0xb4631a307a08abc5d5a582549b23cb98a7c5beb2, args_offset=0x0, args_size=0x40, ret_offset=0x0, ret_size=0x40))  # noqa: E501
        + Op.STOP,
        balance=0xde0b6b3a7640000,
        nonce=0,
        address=Address("0xbf23f3306533431b2ee5e4ca95e0a0834c090105"),  # noqa: E501
    )
    # Source: lll
    # {  (STATICCALL 300000 <contract:0x2000000000000000000000000000000000000002> 0 64 0 64 ) (MSTORE 3 1) }
    addr_0x2000000000000000000000000000000000000001 = pre.deploy_contract(
        code=Op.POP(Op.STATICCALL(gas=0x493e0, address=0x5517c40699ceb16c4eb71f2b0d841078c198560e, args_offset=0x0, args_size=0x40, ret_offset=0x0, ret_size=0x40))
        + Op.MSTORE(offset=0x3, value=0x1) + Op.STOP,
        balance=0xde0b6b3a7640000,
        nonce=0,
        address=Address("0xb4631a307a08abc5d5a582549b23cb98a7c5beb2"),  # noqa: E501
    )
    # Source: lll
    # {  (MSTORE 4 1) (CALLCODE 250000 <contract:0x2000000000000000000000000000000000000003> 0 0 64 0 64 ) (MSTORE 6 1) }
    addr_0x2000000000000000000000000000000000000002 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x4, value=0x1)
        + Op.POP(Op.CALLCODE(gas=0x3d090, address=0x335c5531b84765a7626e6e76688f18b81be5259c, value=0x0, args_offset=0x0, args_size=0x40, ret_offset=0x0, ret_size=0x40))
        + Op.MSTORE(offset=0x6, value=0x1) + Op.STOP,
        balance=0xde0b6b3a7640000,
        nonce=0,
        address=Address("0x5517c40699ceb16c4eb71f2b0d841078c198560e"),  # noqa: E501
    )
    # Source: lll
    # {  (MSTORE 3 1) }
    addr_0x2000000000000000000000000000000000000003 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x3, value=0x1) + Op.STOP,
        nonce=0,
        address=Address("0x335c5531b84765a7626e6e76688f18b81be5259c"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000)

    expect_entries_: list[dict] = [
        {
            "indexes": {'data': 0, 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        target: Account(storage={0: 1, 1: 1}),
        addr_0x1000000000000000000000000000000000000002: Account(
                storage={
            2: 0,
            3: 0,
            4: 0,
            7: 0,
            330: 0,
            332: 0,
            336: 0,
            338: 0,
            340: 0,
        },
            ),
    },
        },
        {
            "indexes": {'data': 1, 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        target: Account(storage={0: 1, 1: 1}),
        addr_0x1000000000000000000000000000000000000002: Account(
                storage={
            2: 0,
            3: 0,
            4: 0,
            7: 0,
            330: 0,
            332: 0,
            336: 0,
            338: 0,
            340: 0,
        },
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
