"""
test_static_callcodecall_10_suicide_end

Ported from:
state_tests/stStaticCall/static_callcodecall_10_SuicideEndFiller.json
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
    "000000000000000000000000cfb5784a5e49924becc2d5c5d2ee0a9b141e6216",
    "000000000000000000000000703b936fd4d674f0ff5d6957f61097152f8781b8",
]
TX_GAS = [3000000]
TX_VALUE = [0]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d])


@pytest.mark.ported_from(
    ["state_tests/stStaticCall/static_callcodecall_10_SuicideEndFiller.json"],
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
def test_static_callcodecall_10_suicide_end(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """test_static_callcodecall_10_suicide_end"""
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
    # { (MSTORE 0 (CALLDATALOAD 0)) [[ 0 ]] (DELEGATECALL 150000 <contract:0x1000000000000000000000000000000000000001> 0 64 0 64 ) [[ 1 ]] (GAS) }
    target = pre.deploy_contract(
        code=Op.MSTORE(offset=0x0, value=Op.CALLDATALOAD(offset=0x0))
        + Op.SSTORE(key=0x0, value=Op.DELEGATECALL(gas=0x249f0, address=0xdc07fff80d888eba04eab962d37897f6c923462b, args_offset=0x0, args_size=0x40, ret_offset=0x0, ret_size=0x40))  # noqa: E501
        + Op.SSTORE(key=0x1, value=Op.GAS) + Op.STOP,
        balance=0xde0b6b3a7640000,
        nonce=0,
        address=Address("0x99b0d2d9eea3205f4de64fdc26910432824ab1a7"),  # noqa: E501
    )
    # Source: lll
    # {  (STATICCALL 50000 (CALLDATALOAD 0) 0 64 0 64 ) (SELFDESTRUCT <contract:target:0x1000000000000000000000000000000000000000>) }
    addr_0x1000000000000000000000000000000000000001 = pre.deploy_contract(
        code=Op.POP(Op.STATICCALL(gas=0xc350, address=Op.CALLDATALOAD(offset=0x0), args_offset=0x0, args_size=0x40, ret_offset=0x0, ret_size=0x40))
        + Op.SELFDESTRUCT(address=0x99b0d2d9eea3205f4de64fdc26910432824ab1a7)
        + Op.STOP,
        balance=0x2540be400,
        nonce=0,
        address=Address("0xdc07fff80d888eba04eab962d37897f6c923462b"),  # noqa: E501
    )
    # Source: lll
    # {  (MSTORE 2 1) }
    addr_0x1000000000000000000000000000000000000002 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x2, value=0x1) + Op.STOP,
        balance=0x2540be400,
        nonce=0,
        address=Address("0xcfb5784a5e49924becc2d5c5d2ee0a9b141e6216"),  # noqa: E501
    )
    # Source: lll
    # {  (SSTORE 2 1) }
    addr_0x2000000000000000000000000000000000000002 = pre.deploy_contract(
        code=Op.SSTORE(key=0x2, value=0x1) + Op.STOP,
        balance=0x2540be400,
        nonce=0,
        address=Address("0x703b936fd4d674f0ff5d6957f61097152f8781b8"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000)

    expect_entries_: list[dict] = [
        {
            "indexes": {'data': -1, 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {target: Account(balance=0xde0b6b3a7640000, nonce=0)},
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
