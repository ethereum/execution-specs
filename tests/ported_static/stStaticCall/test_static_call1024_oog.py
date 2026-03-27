"""
Test_static_call1024_oog.

Ported from:
state_tests/stStaticCall/static_Call1024OOGFiller.json
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
from execution_testing.forks import Fork
from execution_testing.specs.static_state.expect_section import (
    resolve_expect_post,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"

REFERENCE_SPEC_VERSION = "N/A"

TX_DATA = [
    "0000000000000000000000005eb006f1716196a0d072b390030a665386c48b9b",
    "00000000000000000000000042223ec7d9570a769becbe4beed7d885e01e6e37",
]
TX_GAS = [15720826]
TX_VALUE = [10]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d])


@pytest.mark.ported_from(
    ["state_tests/stStaticCall/static_Call1024OOGFiller.json"],
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
def test_static_call1024_oog(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test_static_call1024_oog."""
    coinbase = Address("0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    addr_0xaaaf5374fce5edbc8e2a8697c15331677e6ebf0b = Address(
        "0xd9b97c712ebce43f3c19179bbef44b550f9e8bc0"
    )
    sender = EOA(
        key=0xE7C72B378297589ACEE4E0BA3272841BCFC5E220F86DE253F890274CFEE9E474
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=9223372036854775807,
    )

    pre[sender] = Account(balance=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)
    pre[addr_0xaaaf5374fce5edbc8e2a8697c15331677e6ebf0b] = Account(
        balance=7000
    )
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
        address=Address("0xc0e4183389eb57f779a986d8c878f89b9401dc8e"),  # noqa: E501
    )
    # Source: lll
    # { [[ 0 ]] (ADD @@0 1) [[ 1 ]] (STATICCALL (MUL (SUB (GAS) 10000) (SUB 1 (DIV @@0 1025))) <contract:0xbbbf5374fce5edbc8e2a8697c15331677e6ebf0b> 0 0 0 0) [[ 2 ]] (ADD 1(MUL @@0 1000)) }  # noqa: E501
    addr_0xbbbf5374fce5edbc8e2a8697c15331677e6ebf0b = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=Op.ADD(Op.SLOAD(key=0x0), 0x1))
        + Op.SSTORE(
            key=0x1,
            value=Op.STATICCALL(
                gas=Op.MUL(
                    Op.SUB(Op.GAS, 0x2710),
                    Op.SUB(0x1, Op.DIV(Op.SLOAD(key=0x0), 0x401)),
                ),
                address=0x5EB006F1716196A0D072B390030A665386C48B9B,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.SSTORE(
            key=0x2, value=Op.ADD(0x1, Op.MUL(Op.SLOAD(key=0x0), 0x3E8))
        )
        + Op.STOP,
        balance=1024,
        nonce=0,
        address=Address("0x5eb006f1716196a0d072b390030a665386c48b9b"),  # noqa: E501
    )
    # Source: lll
    # { (MSTORE 0 (ADD (MLOAD 0) 1))  (STATICCALL (MUL (SUB (GAS) 10000) (SUB 1 (DIV (MLOAD 0) 1025))) <contract:0xcbbf5374fce5edbc8e2a8697c15331677e6ebf0b> 0 0 0 0) (MSTORE 32 (ADD 1(MUL (MLOAD 0) 1000))) }  # noqa: E501
    addr_0xcbbf5374fce5edbc8e2a8697c15331677e6ebf0b = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x0, value=Op.ADD(Op.MLOAD(offset=0x0), 0x1))
        + Op.POP(
            Op.STATICCALL(
                gas=Op.MUL(
                    Op.SUB(Op.GAS, 0x2710),
                    Op.SUB(0x1, Op.DIV(Op.MLOAD(offset=0x0), 0x401)),
                ),
                address=0x42223EC7D9570A769BECBE4BEED7D885E01E6E37,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.MSTORE(
            offset=0x20, value=Op.ADD(0x1, Op.MUL(Op.MLOAD(offset=0x0), 0x3E8))
        )
        + Op.STOP,
        balance=1024,
        nonce=0,
        address=Address("0x42223ec7d9570a769becbe4beed7d885e01e6e37"),  # noqa: E501
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": 0, "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                addr_0xbbbf5374fce5edbc8e2a8697c15331677e6ebf0b: Account(
                    storage={0: 1, 1: 0, 2: 1001}
                ),
                target: Account(storage={0: 1, 1: 1}),
            },
        },
        {
            "indexes": {"data": 1, "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                addr_0xbbbf5374fce5edbc8e2a8697c15331677e6ebf0b: Account(
                    storage={0: 0, 1: 0, 2: 0}
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
        value=TX_VALUE[v],
        nonce=0,
        gas_price=10,
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
