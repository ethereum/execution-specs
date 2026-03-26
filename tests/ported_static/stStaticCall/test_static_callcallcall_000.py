"""
test_static_callcallcall_000

Ported from:
state_tests/stStaticCall/static_callcallcall_000Filler.json
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
    "000000000000000000000000fb157bfd4470ab46dffec6f8390b747c67f62b38",
    "000000000000000000000000bf23f3306533431b2ee5e4ca95e0a0834c090105",
]
TX_GAS = [3000000]
TX_VALUE = [0]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d])


@pytest.mark.ported_from(
    ["state_tests/stStaticCall/static_callcallcall_000Filler.json"],
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
def test_static_callcallcall_000(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """test_static_callcallcall_000"""
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
    # {  [[ 0 ]] (STATICCALL 650000 <contract:0x1000000000000000000000000000000000000001> 0 64 0 64 ) }
    addr_0x1000000000000000000000000000000000000000 = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.STATICCALL(gas=0x9eb10, address=0x36ace903a154317b8fa379aad88a425b7ef025dc, args_offset=0x0, args_size=0x40, ret_offset=0x0, ret_size=0x40))  # noqa: E501
        + Op.STOP,
        balance=0xde0b6b3a7640000,
        nonce=0,
        address=Address("0xfb157bfd4470ab46dffec6f8390b747c67f62b38"),  # noqa: E501
    )
    # Source: lll
    # {  (MSTORE 3 1) (STATICCALL 400000 <contract:0x1000000000000000000000000000000000000002> 0 64 0 64 ) (MSTORE 32 1) }
    addr_0x1000000000000000000000000000000000000001 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x3, value=0x1)
        + Op.POP(Op.STATICCALL(gas=0x61a80, address=0x3f6d147a714319ef90c47921715dc5f0ccfe3b09, args_offset=0x0, args_size=0x40, ret_offset=0x0, ret_size=0x40))
        + Op.MSTORE(offset=0x20, value=0x1) + Op.STOP,
        balance=0xde0b6b3a7640000,
        nonce=0,
        address=Address("0x36ace903a154317b8fa379aad88a425b7ef025dc"),  # noqa: E501
    )
    # Source: lll
    # {  (MSTORE 3 1) (STATICCALL 250000 <contract:0x1000000000000000000000000000000000000003> 0 64 0 64 ) (MSTORE 32 1) }
    addr_0x1000000000000000000000000000000000000002 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x3, value=0x1)
        + Op.POP(Op.STATICCALL(gas=0x3d090, address=0x181b4ed322e192361633cc3c0a418f259ab0cf4b, args_offset=0x0, args_size=0x40, ret_offset=0x0, ret_size=0x40))
        + Op.MSTORE(offset=0x20, value=0x1) + Op.STOP,
        balance=0xde0b6b3a7640000,
        nonce=0,
        address=Address("0x3f6d147a714319ef90c47921715dc5f0ccfe3b09"),  # noqa: E501
    )
    # Source: lll
    # {  (SSTORE 3 1) (SSTORE 4 (CALLER)) (SSTORE 7 (CALLVALUE)) (SSTORE 330 (ADDRESS)) (SSTORE 332 (ORIGIN)) (SSTORE 336 (CALLDATASIZE)) (SSTORE 338 (CODESIZE)) (SSTORE 340 (GASPRICE))}
    addr_0x1000000000000000000000000000000000000003 = pre.deploy_contract(
        code=Op.SSTORE(key=0x3, value=0x1) + Op.SSTORE(key=0x4, value=Op.CALLER)  # noqa: E501
        + Op.SSTORE(key=0x7, value=Op.CALLVALUE)
        + Op.SSTORE(key=0x14a, value=Op.ADDRESS)
        + Op.SSTORE(key=0x14c, value=Op.ORIGIN)
        + Op.SSTORE(key=0x150, value=Op.CALLDATASIZE)
        + Op.SSTORE(key=0x152, value=Op.CODESIZE)
        + Op.SSTORE(key=0x154, value=Op.GASPRICE) + Op.STOP,
        nonce=0,
        address=Address("0x181b4ed322e192361633cc3c0a418f259ab0cf4b"),  # noqa: E501
    )
    # Source: lll
    # {  [[ 0 ]] (STATICCALL 350000 <contract:0x2000000000000000000000000000000000000001> 0 64 0 64 ) }
    addr_0x2000000000000000000000000000000000000000 = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.STATICCALL(gas=0x55730, address=0xd518ebb39fb88beb34ad1598fe3ccd3f8e4c4708, args_offset=0x0, args_size=0x40, ret_offset=0x0, ret_size=0x40))  # noqa: E501
        + Op.STOP,
        balance=0xde0b6b3a7640000,
        nonce=0,
        address=Address("0xbf23f3306533431b2ee5e4ca95e0a0834c090105"),  # noqa: E501
    )
    # Source: lll
    # {  (MSTORE 3 1) (STATICCALL 300000 <contract:0x2000000000000000000000000000000000000002> 0 64 0 64 ) (MSTORE 32 1) }
    addr_0x2000000000000000000000000000000000000001 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x3, value=0x1)
        + Op.POP(Op.STATICCALL(gas=0x493e0, address=0x85ee033b8ff327153f5c82d191b4942102debffc, args_offset=0x0, args_size=0x40, ret_offset=0x0, ret_size=0x40))
        + Op.MSTORE(offset=0x20, value=0x1) + Op.STOP,
        balance=0xde0b6b3a7640000,
        nonce=0,
        address=Address("0xd518ebb39fb88beb34ad1598fe3ccd3f8e4c4708"),  # noqa: E501
    )
    # Source: lll
    # {  (MSTORE 3 1) (STATICCALL 250000 <contract:0x2000000000000000000000000000000000000003> 0 64 0 64 ) (MSTORE 32 1) }
    addr_0x2000000000000000000000000000000000000002 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x3, value=0x1)
        + Op.POP(Op.STATICCALL(gas=0x3d090, address=0x335c5531b84765a7626e6e76688f18b81be5259c, args_offset=0x0, args_size=0x40, ret_offset=0x0, ret_size=0x40))
        + Op.MSTORE(offset=0x20, value=0x1) + Op.STOP,
        balance=0xde0b6b3a7640000,
        nonce=0,
        address=Address("0x85ee033b8ff327153f5c82d191b4942102debffc"),  # noqa: E501
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
        addr_0x1000000000000000000000000000000000000000: Account(storage={0: 1}),
        addr_0x1000000000000000000000000000000000000001: Account(storage={}),
        addr_0x1000000000000000000000000000000000000002: Account(storage={}),
        addr_0x1000000000000000000000000000000000000003: Account(
                storage={
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
        target: Account(storage={0: 1, 1: 1}),
    },
        },
        {
            "indexes": {'data': 1, 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        addr_0x2000000000000000000000000000000000000000: Account(storage={0: 1}),
        addr_0x2000000000000000000000000000000000000001: Account(storage={}),
        addr_0x2000000000000000000000000000000000000002: Account(storage={}),
        addr_0x2000000000000000000000000000000000000003: Account(
                storage={
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
