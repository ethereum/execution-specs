"""
Ori Pomerantz qbzzt1@gmail.com

Ported from:
state_tests/VMTests/vmArithmeticTest/divFiller.yml
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
    "693c61390000000000000000000000000000000000000000000000000000000000000007",
]
TX_GAS = [16777216]
TX_VALUE = [1]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d])


@pytest.mark.ported_from(
    ["state_tests/VMTests/vmArithmeticTest/divFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0, 0, 0,
            id="div_2_big",
        ),
        pytest.param(
            1, 0, 0,
            id="div_boost_bug",
        ),
        pytest.param(
            2, 0, 0,
            id="div_5_2",
        ),
        pytest.param(
            3, 0, 0,
            id="div_23_24",
        ),
        pytest.param(
            4, 0, 0,
            id="div_0_24",
        ),
        pytest.param(
            5, 0, 0,
            id="div_1_0",
        ),
        pytest.param(
            6, 0, 0,
            id="div_2_0",
        ),
        pytest.param(
            7, 0, 0,
            id="div_0_add",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_div(
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
    contract_7 = Address("0x0000000000000000000000000000000000001007")
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
    # {
    #    [[0]]  (/ 0x02
    #        0xfedcba9876543210fedcba9876543210fedcba9876543210fedcba9876543210)
    # }
    contract_0 = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.DIV(0x2, 0xfedcba9876543210fedcba9876543210fedcba9876543210fedcba9876543210))  # noqa: E501
        + Op.STOP,
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001000"),  # noqa: E501
    )
    # Source: lll
    # {
    #    ; Verify the fix to the divBoostBug
    #    [[0]] (/ 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFBA
    #              0x1DAE6076B981DAE6076B981DAE6076B981DAE6076B981DAE6076B981DAE6077)
    # 
    # 
    # }
    contract_1 = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.DIV(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffba, 0x1dae6076b981dae6076b981dae6076b981dae6076b981dae6076b981dae6077))  # noqa: E501
        + Op.STOP,
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001001"),  # noqa: E501
    )
    # Source: lll
    # {
    #    [[0]]  (/ 5 2)
    # }
    contract_2 = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.DIV(0x5, 0x2)) + Op.STOP,
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001002"),  # noqa: E501
    )
    # Source: lll
    # {
    #    [[0]]  (/ 23 24)
    # }
    contract_3 = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.DIV(0x17, 0x18)) + Op.STOP,
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001003"),  # noqa: E501
    )
    # Source: lll
    # {
    #    [[0]]  (/ 0 24)
    # }
    contract_4 = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.DIV(0x0, 0x18)) + Op.STOP,
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001004"),  # noqa: E501
    )
    # Source: lll
    # {
    #    [[0]]  (/ 1 1)
    # }
    contract_5 = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.DIV(0x1, 0x1)) + Op.STOP,
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001005"),  # noqa: E501
    )
    # Source: lll
    # {
    #    ; Divide by zero
    #    [[0]]  (/ 2 0)
    # }
    contract_6 = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.DIV(0x2, 0x0)) + Op.STOP,
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001006"),  # noqa: E501
    )
    # Source: lll
    # {
    #    [[0]]  (+ (/ 13 0) 7)
    # }
    contract_7 = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.ADD(Op.DIV(0xd, 0x0), 0x7)) + Op.STOP,
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001007"),  # noqa: E501
    )
    # Source: lll
    # {
    #     (call 0xffffff (+ 0x1000 $4) 0 0 0 0 0)
    # }
    contract_8 = pre.deploy_contract(
        code=Op.CALL(gas=0xffffff, address=Op.ADD(0x1000, Op.CALLDATALOAD(offset=0x4)), value=0x0, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0)
        + Op.STOP,
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        address=Address("0xcccccccccccccccccccccccccccccccccccccccc"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xba1a9ce0ba1a9ce)

    expect_entries_: list[dict] = [
        {
            "indexes": {'data': [0, 3, 4, 6], 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        contract_0: Account(storage={0: 0}),
        contract_3: Account(storage={0: 0}),
        contract_4: Account(storage={0: 0}),
        contract_6: Account(storage={0: 0}),
    },
        },
        {
            "indexes": {'data': [1], 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {contract_1: Account(storage={0: 137})},
        },
        {
            "indexes": {'data': [2], 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {contract_2: Account(storage={0: 2})},
        },
        {
            "indexes": {'data': [5], 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {contract_5: Account(storage={0: 1})},
        },
        {
            "indexes": {'data': [7], 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {contract_7: Account(storage={0: 7})},
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
