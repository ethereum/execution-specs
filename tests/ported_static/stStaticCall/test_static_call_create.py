"""
test_static_call_create

Ported from:
state_tests/stStaticCall/static_callCreateFiller.json
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
    "000000000000000000000000f5c27325e6c5769b6569971cd81e01570fd30ef1",
    "00000000000000000000000029d4d72a31d1b141b2067d1d4193bdf12fcddc41",
    "000000000000000000000000b4aa7cc91d100eddc01f22ca32f643bb0f1c91cc",
    "000000000000000000000000f9ecfe0635fefb5ad44418f97d7fcaf210ebd5aa",
]
TX_GAS = [1000000]
TX_VALUE = [100000]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d])


@pytest.mark.ported_from(
    ["state_tests/stStaticCall/static_callCreateFiller.json"],
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
        pytest.param(
            2, 0, 0,
            id="d2",
        ),
        pytest.param(
            3, 0, 0,
            id="d3",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_static_call_create(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """test_static_call_create"""
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
        gas_limit=10000000,
    )

    # Source: lll
    # {  [[ 0 ]] (STATICCALL 300000 (CALLDATALOAD 0) 0 0 0 0) }
    target = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.STATICCALL(gas=0x493e0, address=Op.CALLDATALOAD(offset=0x0), args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))  # noqa: E501
        + Op.STOP,
        balance=0xde0b6b3a7640000,
        nonce=0,
        address=Address("0xe49f04b30026f23e9e04493c44ece7cfec9224ca"),  # noqa: E501
    )
    # Source: lll
    # {  (CALL 150000 <contract:0x1000000000000000000000000000000000000002> 0 0 0 0 0) }
    addr_0x1000000000000000000000000000000000000001 = pre.deploy_contract(
        code=Op.CALL(gas=0x249f0, address=0x29d4d72a31d1b141b2067d1d4193bdf12fcddc41, value=0x0, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0)
        + Op.STOP,
        balance=0xde0b6b3a7640000,
        nonce=0,
        address=Address("0xf5c27325e6c5769b6569971cd81e01570fd30ef1"),  # noqa: E501
    )
    # Source: lll
    # {  (DELEGATECALL 150000 <contract:0x1000000000000000000000000000000000000002> 0 0 0 0) }
    addr_0x1000000000000000000000000000000000000003 = pre.deploy_contract(
        code=Op.DELEGATECALL(gas=0x249f0, address=0x29d4d72a31d1b141b2067d1d4193bdf12fcddc41, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0)
        + Op.STOP,
        balance=0xde0b6b3a7640000,
        nonce=0,
        address=Address("0xb4aa7cc91d100eddc01f22ca32f643bb0f1c91cc"),  # noqa: E501
    )
    # Source: lll
    # {  (STATICCALL 150000 <contract:0x1000000000000000000000000000000000000002> 0 0 0 0) }
    addr_0x1000000000000000000000000000000000000004 = pre.deploy_contract(
        code=Op.STATICCALL(gas=0x249f0, address=0x29d4d72a31d1b141b2067d1d4193bdf12fcddc41, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0)
        + Op.STOP,
        balance=0xde0b6b3a7640000,
        nonce=0,
        address=Address("0xf9ecfe0635fefb5ad44418f97d7fcaf210ebd5aa"),  # noqa: E501
    )
    # Source: lll
    # {  (CREATE 0 1 1) }
    addr_0x1000000000000000000000000000000000000002 = pre.deploy_contract(
        code=Op.CREATE(value=0x0, offset=0x1, size=0x1) + Op.STOP,
        balance=0xde0b6b3a7640000,
        nonce=0,
        address=Address("0x29d4d72a31d1b141b2067d1d4193bdf12fcddc41"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000)

    expect_entries_: list[dict] = [
        {
            "indexes": {'data': [0, 2, 3], 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {target: Account(storage={0: 1})},
        },
        {
            "indexes": {'data': [1], 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {target: Account(storage={0: 0})},
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
