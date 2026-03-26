"""
Ori Pomerantz qbzzt1@gmail.com

Ported from:
state_tests/VMTests/vmLogTest/log0Filler.yml
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
    "693c61390000000000000000000000000000000000000000000000000000000000000000",
    "693c61390000000000000000000000000000000000000000000000000000000000000001",
    "693c61390000000000000000000000000000000000000000000000000000000000000002",
    "693c61390000000000000000000000000000000000000000000000000000000000000003",
    "693c61390000000000000000000000000000000000000000000000000000000000000004",
    "693c61390000000000000000000000000000000000000000000000000000000000000005",
    "693c61390000000000000000000000000000000000000000000000000000000000000006",
    "693c6139000000000000000000000000000000000000000000000000000000000000000a",
]
TX_GAS = [16777216]
TX_VALUE = [1]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d])


@pytest.mark.ported_from(
    ["state_tests/VMTests/vmLogTest/log0Filler.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0, 0, 0,
            id="emptyMem",
        ),
        pytest.param(
            1, 0, 0,
            id="memStartTooHigh",
        ),
        pytest.param(
            2, 0, 0,
            id="memSizeTooHigh",
        ),
        pytest.param(
            3, 0, 0,
            id="memSizeZero",
        ),
        pytest.param(
            4, 0, 0,
            id="nonEmptyMem",
        ),
        pytest.param(
            5, 0, 0,
            id="log_0_1",
        ),
        pytest.param(
            6, 0, 0,
            id="log_31_1",
        ),
        pytest.param(
            7, 0, 0,
            id="logTwice",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_log0(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Ori Pomerantz qbzzt1@gmail."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    contract_0 = Address("0x0000000000000000000000000000000000001000")
    contract_1 = Address("0x0000000000000000000000000000000000001001")
    contract_2 = Address("0x0000000000000000000000000000000000001002")
    contract_3 = Address("0x0000000000000000000000000000000000001003")
    contract_4 = Address("0x0000000000000000000000000000000000001004")
    contract_5 = Address("0x0000000000000000000000000000000000001005")
    contract_6 = Address("0x0000000000000000000000000000000000001006")
    contract_7 = Address("0x000000000000000000000000000000000000100a")
    contract_8 = Address("0xcccccccccccccccccccccccccccccccccccccccc")
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
        gas_limit=100000000,
    )

    # Source: lll
    # {   ; emptyMem
    #     (log0 0 0)
    # 
    #     [[0]] 0x600D
    # }
    contract_0 = pre.deploy_contract(
        code=Op.LOG0(offset=0x0, size=0x0) + Op.SSTORE(key=0x0, value=0x600d)
        + Op.STOP,
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001000"),  # noqa: E501
    )
    # Source: lll
    # {      ; memStartTooHigh
    #    [0]   0xaabbffffffffffffffffffffffffffffffffffffffffffffffffffffffffccdd
    #    (log0 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff 1)
    #    [[0]] 0x600D
    # }
    contract_1 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x0, value=0xaabbffffffffffffffffffffffffffffffffffffffffffffffffffffffffccdd)
        + Op.LOG0(offset=0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff, size=0x1)
        + Op.SSTORE(key=0x0, value=0x600d) + Op.STOP,
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001001"),  # noqa: E501
    )
    # Source: lll
    # {        ; memSizeTooHigh
    #    [0] 0xaabbffffffffffffffffffffffffffffffffffffffffffffffffffffffffccdd
    #    (log0 1 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff)
    #    [[0]] 0x600D
    # }
    contract_2 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x0, value=0xaabbffffffffffffffffffffffffffffffffffffffffffffffffffffffffccdd)
        + Op.LOG0(offset=0x1, size=0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff)
        + Op.SSTORE(key=0x0, value=0x600d) + Op.STOP,
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001002"),  # noqa: E501
    )
    # Source: lll
    # {        ; memSizeZero
    #    [0] 0xaabbffffffffffffffffffffffffffffffffffffffffffffffffffffffffccdd
    #    (log0 1 0)
    #    [[0]] 0x600D
    # }
    contract_3 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x0, value=0xaabbffffffffffffffffffffffffffffffffffffffffffffffffffffffffccdd)
        + Op.LOG0(offset=0x1, size=0x0) + Op.SSTORE(key=0x0, value=0x600d)
        + Op.STOP,
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001003"),  # noqa: E501
    )
    # Source: lll
    # {        ; nonEmptyMem
    #    [0] 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff
    #    (log0 0 32)
    #    [[0]] 0x600D
    # }
    contract_4 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x0, value=0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff)
        + Op.LOG0(offset=0x0, size=0x20) + Op.SSTORE(key=0x0, value=0x600d)
        + Op.STOP,
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001004"),  # noqa: E501
    )
    # Source: lll
    # {        ; log_0_1
    #    [0] 0xaabbffffffffffffffffffffffffffffffffffffffffffffffffffffffffccdd
    #    (log0 0 1)
    #    [[0]] 0x600D
    # }
    contract_5 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x0, value=0xaabbffffffffffffffffffffffffffffffffffffffffffffffffffffffffccdd)
        + Op.LOG0(offset=0x0, size=0x1) + Op.SSTORE(key=0x0, value=0x600d)
        + Op.STOP,
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001005"),  # noqa: E501
    )
    # Source: lll
    # {        ; log_31_1
    #    [0] 0xaabbffffffffffffffffffffffffffffffffffffffffffffffffffffffffccdd
    #    (log0 31 1)
    #    [[0]] 0x600D
    # }
    contract_6 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x0, value=0xaabbffffffffffffffffffffffffffffffffffffffffffffffffffffffffccdd)
        + Op.LOG0(offset=0x1f, size=0x1) + Op.SSTORE(key=0x0, value=0x600d)
        + Op.STOP,
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001006"),  # noqa: E501
    )
    # Source: lll
    # {        ; logTwice
    #    [0] 0xaabbffffffffffffffffffffffffffffffffffffffffffffffffffffffffccdd
    #    (log0 0 32)
    #    (log0 2 16)
    #    [[0]] 0x600D
    # }
    contract_7 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x0, value=0xaabbffffffffffffffffffffffffffffffffffffffffffffffffffffffffccdd)
        + Op.LOG0(offset=0x0, size=0x20) + Op.LOG0(offset=0x2, size=0x10)
        + Op.SSTORE(key=0x0, value=0x600d) + Op.STOP,
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        address=Address("0x000000000000000000000000000000000000100a"),  # noqa: E501
    )
    # Source: lll
    # {
    #     (delegatecall (gas) (+ 0x1000 $4) 0 0 0 0)
    # }
    contract_8 = pre.deploy_contract(
        code=Op.DELEGATECALL(gas=Op.GAS, address=Op.ADD(0x1000, Op.CALLDATALOAD(offset=0x4)), args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0)
        + Op.STOP,
        storage={0: 2989},
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        address=Address("0xcccccccccccccccccccccccccccccccccccccccc"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x100000000000)

    expect_entries_: list[dict] = [
        {
            "indexes": {'data': [0, 3, 4, 5, 6, 7], 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {contract_8: Account(storage={0: 24589})},
        },
        {
            "indexes": {'data': [1, 2], 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {contract_8: Account(storage={0: 2989})},
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx = Transaction(
        sender=sender,
        to=contract_8,
        data=_tx_data(d),
        gas_limit=TX_GAS[g],
        value=TX_VALUE[v],
        nonce=0,
        gas_price=10,
        error=_exc,
    )


    state_test(env=env, pre=pre, post=post, tx=tx)
