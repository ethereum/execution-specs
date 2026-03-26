"""
Requires a separate pre-alloc group due to time required to fill when grouped with other tests.

Ported from:
state_tests/stStaticCall/static_LoopCallsThenRevertFiller.json
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
    "",
]
TX_GAS = [10000000, 9000000]
TX_VALUE = [0]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d])


@pytest.mark.ported_from(
    ["state_tests/stStaticCall/static_LoopCallsThenRevertFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0, 0, 0,
            id="-g0",
        ),
        pytest.param(
            0, 1, 0,
            id="-g1",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_static_loop_calls_then_revert(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Requires a separate pre-alloc group due to time required to fill wh..."""
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
        gas_limit=100000000,
    )

    pre[sender] = Account(balance=0xe8d4a51000)
    # Source: lll
    # { (MSTORE 0 850) [[ 0 ]] (CALL (- (GAS) 10000) <contract:0xa000000000000000000000000000000000000000> 0 0 32 0 0) [[ 1 ]] 1 }
    target = pre.deploy_contract(
        code=Op.MSTORE(offset=0x0, value=0x352)
        + Op.SSTORE(key=0x0, value=Op.CALL(gas=Op.SUB(Op.GAS, 0x2710), address=0x7a2af5cc0310371cce006e472ed3b5d68e62f839, value=0x0, args_offset=0x0, args_size=0x20, ret_offset=0x0, ret_size=0x0))  # noqa: E501
        + Op.SSTORE(key=0x1, value=0x1) + Op.STOP,
        nonce=0,
        address=Address("0xd64495cbba16d27a88b96f2a72417b957ed4cae6"),  # noqa: E501
    )
    # Source: raw
    # 0x5b600160003503600052600060006000600073<contract:0xb000000000000000000000000000000000000000>61c350fa50600051600057
    addr_0xa000000000000000000000000000000000000000 = pre.deploy_contract(
        code=Op.JUMPDEST
        + Op.MSTORE(offset=0x0, value=Op.SUB(Op.CALLDATALOAD(offset=0x0), 0x1))
        + Op.POP(Op.STATICCALL(gas=0xc350, address=0x59c89b27361fd637262b13489f28923c835e17b2, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))
        + Op.JUMPI(pc=0x0, condition=Op.MLOAD(offset=0x0)),
        storage={0: 850},
        nonce=0,
        address=Address("0x7a2af5cc0310371cce006e472ed3b5d68e62f839"),  # noqa: E501
    )
    # Source: lll
    # { (MSTORE 0 (ADD 1 (MLOAD 0))) }
    addr_0xb000000000000000000000000000000000000000 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x0, value=Op.ADD(0x1, Op.MLOAD(offset=0x0)))
        + Op.STOP,
        nonce=0,
        address=Address("0x59c89b27361fd637262b13489f28923c835e17b2"),  # noqa: E501
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {'data': -1, 'gas': 0, 'value': -1},
            "network": ['>=Cancun'],
            "result": {target: Account(storage={1: 1})},
        },
        {
            "indexes": {'data': -1, 'gas': 1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {target: Account(storage={1: 1})},
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
