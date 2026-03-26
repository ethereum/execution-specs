"""
test_static_callcall_00

Ported from:
state_tests/stStaticCall/static_callcall_00Filler.json
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
    ["state_tests/stStaticCall/static_callcall_00Filler.json"],
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
def test_static_callcall_00(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """test_static_callcall_00"""
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
    # {  [[ 0 ]] (CALL (GAS) (CALLDATALOAD 0) (CALLVALUE) 0 0 0 0) [[ 1 ]] 1 }
    target = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.CALL(gas=Op.GAS, address=Op.CALLDATALOAD(offset=0x0), value=Op.CALLVALUE, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))  # noqa: E501
        + Op.SSTORE(key=0x1, value=0x1) + Op.STOP,
        nonce=0,
        address=Address("0xc0e4183389eb57f779a986d8c878f89b9401dc8e"),  # noqa: E501
    )
    # Source: lll
    # {  [[ 0 ]] (STATICCALL 350000 <contract:0x1000000000000000000000000000000000000001> 0 64 0 64 ) }
    addr_0x1000000000000000000000000000000000000000 = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.STATICCALL(gas=0x55730, address=0x620b442c84d5068e6b57d390a1ac99130205406e, args_offset=0x0, args_size=0x40, ret_offset=0x0, ret_size=0x40))  # noqa: E501
        + Op.STOP,
        balance=0xde0b6b3a7640000,
        nonce=0,
        address=Address("0x2f9ec0afcb4edcd7d38c6a48f5e36038263ca3cd"),  # noqa: E501
    )
    # Source: lll
    # {  (STATICCALL 250000 <contract:0x1000000000000000000000000000000000000002> 0 64 0 64 ) }
    addr_0x1000000000000000000000000000000000000001 = pre.deploy_contract(
        code=Op.STATICCALL(gas=0x3d090, address=0x33f368f0b54063613cf5944941e8e0e4eeb64697, args_offset=0x0, args_size=0x40, ret_offset=0x0, ret_size=0x40)
        + Op.STOP,
        balance=0xde0b6b3a7640000,
        nonce=0,
        address=Address("0x620b442c84d5068e6b57d390a1ac99130205406e"),  # noqa: E501
    )
    # Source: lll
    # {  (SSTORE 2 1) (SSTORE 4 (CALLER)) (SSTORE 7 (CALLVALUE)) (SSTORE 230 (ADDRESS)) (SSTORE 232 (ORIGIN)) (SSTORE 236 (CALLDATASIZE)) (SSTORE 238 (CODESIZE)) (SSTORE 240 (GASPRICE))}
    addr_0x1000000000000000000000000000000000000002 = pre.deploy_contract(
        code=Op.SSTORE(key=0x2, value=0x1) + Op.SSTORE(key=0x4, value=Op.CALLER)  # noqa: E501
        + Op.SSTORE(key=0x7, value=Op.CALLVALUE)
        + Op.SSTORE(key=0xe6, value=Op.ADDRESS)
        + Op.SSTORE(key=0xe8, value=Op.ORIGIN)
        + Op.SSTORE(key=0xec, value=Op.CALLDATASIZE)
        + Op.SSTORE(key=0xee, value=Op.CODESIZE)
        + Op.SSTORE(key=0xf0, value=Op.GASPRICE) + Op.STOP,
        nonce=0,
        address=Address("0x33f368f0b54063613cf5944941e8e0e4eeb64697"),  # noqa: E501
    )
    # Source: lll
    # {  [[ 0 ]] (STATICCALL 350000 <contract:0x2000000000000000000000000000000000000001> 0 64 0 64 ) }
    addr_0x2000000000000000000000000000000000000000 = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.STATICCALL(gas=0x55730, address=0xdcc76191e9f918ecfe9fba5414884d5ee621ae00, args_offset=0x0, args_size=0x40, ret_offset=0x0, ret_size=0x40))  # noqa: E501
        + Op.STOP,
        balance=0xde0b6b3a7640000,
        nonce=0,
        address=Address("0xbf23f3306533431b2ee5e4ca95e0a0834c090105"),  # noqa: E501
    )
    # Source: lll
    # {  (STATICCALL 250000 <contract:0x2000000000000000000000000000000000000002> 0 64 0 64 ) }
    addr_0x2000000000000000000000000000000000000001 = pre.deploy_contract(
        code=Op.STATICCALL(gas=0x3d090, address=0x29736372c0fab51db4556614ef27d74a89acfe21, args_offset=0x0, args_size=0x40, ret_offset=0x0, ret_size=0x40)
        + Op.STOP,
        balance=0xde0b6b3a7640000,
        nonce=0,
        address=Address("0xdcc76191e9f918ecfe9fba5414884d5ee621ae00"),  # noqa: E501
    )
    # Source: lll
    # {  (MSTORE 0 1) (MSTORE 32 (CALLER)) (MSTORE 64 (CALLVALUE)) (MSTORE 96 (ADDRESS)) (MSTORE 128 (ORIGIN)) (MSTORE 160 (CALLDATASIZE)) (MSTORE 192 (CODESIZE)) (MSTORE 224 (GASPRICE))}
    addr_0x2000000000000000000000000000000000000002 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x0, value=0x1)
        + Op.MSTORE(offset=0x20, value=Op.CALLER)
        + Op.MSTORE(offset=0x40, value=Op.CALLVALUE)
        + Op.MSTORE(offset=0x60, value=Op.ADDRESS)
        + Op.MSTORE(offset=0x80, value=Op.ORIGIN)
        + Op.MSTORE(offset=0xa0, value=Op.CALLDATASIZE)
        + Op.MSTORE(offset=0xc0, value=Op.CODESIZE)
        + Op.MSTORE(offset=0xe0, value=Op.GASPRICE) + Op.STOP,
        nonce=0,
        address=Address("0x29736372c0fab51db4556614ef27d74a89acfe21"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000)

    expect_entries_: list[dict] = [
        {
            "indexes": {'data': 0, 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        target: Account(storage={0: 1, 1: 1}),
        addr_0x1000000000000000000000000000000000000000: Account(storage={0: 1}),
        addr_0x1000000000000000000000000000000000000002: Account(
                storage={
            2: 0,
            4: 0,
            7: 0,
            230: 0,
            232: 0,
            236: 0,
            238: 0,
            240: 0,
        },
            ),
    },
        },
        {
            "indexes": {'data': 1, 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        target: Account(storage={0: 1, 1: 1}),
        addr_0x2000000000000000000000000000000000000000: Account(storage={0: 1}),
        addr_0x2000000000000000000000000000000000000002: Account(
                storage={
            2: 0,
            4: 0,
            7: 0,
            230: 0,
            232: 0,
            236: 0,
            238: 0,
            240: 0,
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
