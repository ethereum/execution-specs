"""
test_push0_gas2

Ported from:
state_tests/Shanghai/stEIP3855_push0/push0Gas2Filler.yml
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
    "0000000000000000000000000000000000001000",
    "0000000000000000000000000000000000000200",
]
TX_GAS = [300000]
TX_VALUE = [0]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d])


@pytest.mark.ported_from(
    ["state_tests/Shanghai/stEIP3855_push0/push0Gas2Filler.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0, 0, 0,
            id="use_push0",
        ),
        pytest.param(
            1, 0, 0,
            id="use_push1_00",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_push0_gas2(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """test_push0_gas2"""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    contract_0 = Address("0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    contract_1 = Address("0x0000000000000000000000000000000000001000")
    contract_2 = Address("0x0000000000000000000000000000000000000200")
    sender = EOA(
        key=0x45a915e4d060149eb4365960e6a7a45f334393093061116b197e3240065ff2d8
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=89128960,
    )

    pre[sender] = Account(balance=0x989680)
    # Source: yul
    # berlin
    # {
    #    sstore(0, call(100000, shr(96, calldataload(0)), 0, 0, 0, 0, 0))
    #    sstore(1, 1)
    # }
    contract_0 = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.CALL(gas=0x186a0, address=Op.SHR(0x60, Op.CALLDATALOAD(offset=Op.DUP1)), value=Op.DUP1, args_offset=Op.DUP1, args_size=Op.DUP1, ret_offset=Op.DUP1, ret_size=0x0))  # noqa: E501
        + Op.SSTORE(key=Op.DUP1, value=0x1) + Op.STOP,
        nonce=0,
        address=Address("0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b"),  # noqa: E501
    )
    # Source: raw
    # 0x5a5f5a9091039055
    contract_1 = pre.deploy_contract(
        code=Op.GAS + Op.PUSH0 + Op.GAS + Op.SWAP1 + Op.SWAP2 + Op.SUB + Op.SWAP1
        + Op.SSTORE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001000"),  # noqa: E501
    )
    # Source: raw
    # 0x5a60005a9091039055
    contract_2 = pre.deploy_contract(
        code=Op.GAS + Op.PUSH1[0x0] + Op.GAS + Op.SWAP1 + Op.SWAP2 + Op.SUB
        + Op.SWAP1 + Op.SSTORE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000000200"),  # noqa: E501
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {'data': [0], 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        contract_1: Account(storage={0: 4}, balance=0),
        contract_0: Account(storage={0: 1, 1: 1}),
    },
        },
        {
            "indexes": {'data': [1], 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        contract_2: Account(storage={0: 5}, balance=0),
        contract_0: Account(storage={0: 1, 1: 1}),
    },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=_tx_data(d),
        gas_limit=TX_GAS[g],
        nonce=0,
        gas_price=10,
        error=_exc,
    )


    state_test(env=env, pre=pre, post=post, tx=tx)
