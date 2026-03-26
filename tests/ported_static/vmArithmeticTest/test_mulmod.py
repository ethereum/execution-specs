"""
Ori Pomerantz qbzzt1@gmail.com

Ported from:
state_tests/VMTests/vmArithmeticTest/mulmodFiller.yml
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
    "693c61390000000000000000000000000000000000000000000000000000000000000008",
    "693c61390000000000000000000000000000000000000000000000000000000000000009",
    "693c6139000000000000000000000000000000000000000000000000000000000000000a",
    "693c6139000000000000000000000000000000000000000000000000000000000000000b",
    "693c6139000000000000000000000000000000000000000000000000000000000000000c",
    "693c6139000000000000000000000000000000000000000000000000000000000000000d",
    "693c6139000000000000000000000000000000000000000000000000000000000000000e",
    "693c6139000000000000000000000000000000000000000000000000000000000000000d",
]
TX_GAS = [16777216]
TX_VALUE = [1]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d])


@pytest.mark.ported_from(
    ["state_tests/VMTests/vmArithmeticTest/mulmodFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0, 0, 0,
            id="mm_1_2_2",
        ),
        pytest.param(
            1, 0, 0,
            id="mm_neg1_neg2_3",
        ),
        pytest.param(
            2, 0, 0,
            id="mm_neg5_1_3",
        ),
        pytest.param(
            3, 0, 0,
            id="mm_5_1_neg3",
        ),
        pytest.param(
            4, 0, 0,
            id="mm_27_37_100",
        ),
        pytest.param(
            5, 0, 0,
            id="mm_2pow255_2_5",
        ),
        pytest.param(
            6, 0, 0,
            id="mm_neg1_2_5",
        ),
        pytest.param(
            7, 0, 0,
            id="mm_2pow255min1_2_5",
        ),
        pytest.param(
            8, 0, 0,
            id="mm_2pow255plus1_2_5",
        ),
        pytest.param(
            9, 0, 0,
            id="mulmod_vs_smod",
        ),
        pytest.param(
            10, 0, 0,
            id="mulmod_vs_mod",
        ),
        pytest.param(
            11, 0, 0,
            id="mulmod_pos_pos_neg",
        ),
        pytest.param(
            12, 0, 0,
            id="mm_0_1_0",
        ),
        pytest.param(
            13, 0, 0,
            id="mm_1_0_0",
        ),
        pytest.param(
            14, 0, 0,
            id="one_minus_mm_0_0_0",
        ),
        pytest.param(
            15, 0, 0,
            id="mm_5_1_0",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_mulmod(
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
    contract_8 = Address("0x0000000000000000000000000000000000001008")
    contract_9 = Address("0x0000000000000000000000000000000000001009")
    contract_10 = Address("0x000000000000000000000000000000000000100a")
    contract_11 = Address("0x000000000000000000000000000000000000100b")
    contract_12 = Address("0x000000000000000000000000000000000000100c")
    contract_13 = Address("0x000000000000000000000000000000000000100d")
    contract_14 = Address("0x000000000000000000000000000000000000100e")
    contract_15 = Address("0x000000000000000000000000000000000000100f")
    contract_16 = Address("0xcccccccccccccccccccccccccccccccccccccccc")
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
    #    ; (1*2) % 2 is zero
    #    [[0]] (mulmod 1 2 2)
    # }
    contract_0 = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.MULMOD(0x1, 0x2, 0x2)) + Op.STOP,
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001000"),  # noqa: E501
    )
    # Source: lll
    # {
    #    ; -a is actually 2^256-a
    #    ;
    #    ; 2^256 % 3 = 1
    #    ; (2^256-1) % 3 = (1-1)%3 = 0
    #    [[0]] (mulmod (- 0 1) (- 0 2) 3)
    # }
    contract_1 = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.MULMOD(Op.SUB(0x0, 0x1), Op.SUB(0x0, 0x2), 0x3))  # noqa: E501
        + Op.STOP,
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001001"),  # noqa: E501
    )
    # Source: lll
    # {
    #    ; -5 % 3 = (2^256 - 5) % 3 = (1-2)%3 = (-1) % 3 = 2
    #    [[0]] (mulmod (- 0 5) 1 3)
    # }
    contract_2 = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.MULMOD(Op.SUB(0x0, 0x5), 0x1, 0x3))
        + Op.STOP,
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001002"),  # noqa: E501
    )
    # Source: lll
    # {
    #    ; -3 is actually 2^256-3, which is much more than five
    #    [[0]] (mulmod 5 1 (- 0 3))
    # }
    contract_3 = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.MULMOD(0x5, 0x1, Op.SUB(0x0, 0x3)))
        + Op.STOP,
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001003"),  # noqa: E501
    )
    # Source: lll
    # {
    #    [[0]] (mulmod 27 37 100)
    # }
    contract_4 = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.MULMOD(0x1b, 0x25, 0x64)) + Op.STOP,
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001004"),  # noqa: E501
    )
    # Source: lll
    # {
    #    (def 'pow2_255 0x8000000000000000000000000000000000000000000000000000000000000000)
    # 
    #    ; 2^255%5 = 3
    #    ;     2%5 = 2
    #    ;           6%5 = 1
    #    [[0]] (mulmod pow2_255 2 5)
    # }
    contract_5 = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.MULMOD(0x8000000000000000000000000000000000000000000000000000000000000000, 0x2, 0x5))  # noqa: E501
        + Op.STOP,
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001005"),  # noqa: E501
    )
    # Source: lll
    # {
    #    ; (256^2-1) % 5 = 0
    #    [[0]] (mulmod (- 0 1) 2 5)
    # }
    contract_6 = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.MULMOD(Op.SUB(0x0, 0x1), 0x2, 0x5))
        + Op.STOP,
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001006"),  # noqa: E501
    )
    # Source: lll
    # {
    #    (def 'pow2_255 0x8000000000000000000000000000000000000000000000000000000000000000)
    # 
    #    ; 2^255%5 = 3
    #    ;     2%5 = 2
    #    ; (3-1) * 2 = 4
    #    [[0]] (mulmod (- pow2_255 1) 2 5)
    # }
    contract_7 = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.MULMOD(Op.SUB(0x8000000000000000000000000000000000000000000000000000000000000000, 0x1), 0x2, 0x5))  # noqa: E501
        + Op.STOP,
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001007"),  # noqa: E501
    )
    # Source: lll
    # {
    #    (def 'pow2_255 0x8000000000000000000000000000000000000000000000000000000000000000)
    # 
    #    ; 2^255%5 = 3
    #    ;     2%5 = 2
    #    ; ((3+1) * 2) % 5 = 3
    #    [[0]] (mulmod (+ pow2_255 1) 2 5)
    # }
    contract_8 = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.MULMOD(Op.ADD(0x8000000000000000000000000000000000000000000000000000000000000000, 0x1), 0x2, 0x5))  # noqa: E501
        + Op.STOP,
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001008"),  # noqa: E501
    )
    # Source: lll
    # {
    #    ; smod   is signed mod, -5%3 = -1
    #    ; mulmod is unsigned mod, -5%3 = 2
    #    ; -1 != 2
    #    [[0]] (= (smod (- 0 5) 3) (mulmod (- 0 5) 1 3))
    # }
    contract_9 = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.EQ(Op.SMOD(Op.SUB(0x0, 0x5), 0x3), Op.MULMOD(Op.SUB(0x0, 0x5), 0x1, 0x3)))  # noqa: E501
        + Op.STOP,
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001009"),  # noqa: E501
    )
    # Source: lll
    # {
    #    ; mod and mulmod are both unsigned mod
    #    ; equal
    #    [[0]] (= (mod (- 0 5) 3) (mulmod (- 0 5) 1 3))
    # }
    contract_10 = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.EQ(Op.MOD(Op.SUB(0x0, 0x5), 0x3), Op.MULMOD(Op.SUB(0x0, 0x5), 0x1, 0x3)))  # noqa: E501
        + Op.STOP,
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        address=Address("0x000000000000000000000000000000000000100a"),  # noqa: E501
    )
    # Source: lll
    # {
    #    ; (mulmod a b -c) is usually a*b, because -c is
    #    ; actually 2^256-c, which is huge
    #    ; not equal
    #    [[0]] (= (mulmod 5 1 (- 0 3)) 2)
    # }
    contract_11 = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.EQ(Op.MULMOD(0x5, 0x1, Op.SUB(0x0, 0x3)), 0x2))  # noqa: E501
        + Op.STOP,
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        address=Address("0x000000000000000000000000000000000000100b"),  # noqa: E501
    )
    # Source: lll
    # {
    #    ; (mulmod x y 0) is zero
    #    [[0]] (mulmod 0 1 0)
    # }
    contract_12 = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.MULMOD(0x0, 0x1, 0x0)) + Op.STOP,
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        address=Address("0x000000000000000000000000000000000000100c"),  # noqa: E501
    )
    # Source: lll
    # {
    #    ; (mulmod x y 0) is zero
    #    [[0]] (mulmod 1 0 0)
    # }
    contract_13 = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.MULMOD(0x1, 0x0, 0x0)) + Op.STOP,
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        address=Address("0x000000000000000000000000000000000000100d"),  # noqa: E501
    )
    # Source: lll
    # {
    #    ; (mulmod x y 0) is zero
    #    [[0]] (- 1 (mulmod 0 0 0))
    # }
    contract_14 = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.SUB(0x1, Op.MULMOD(0x0, 0x0, 0x0)))
        + Op.STOP,
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        address=Address("0x000000000000000000000000000000000000100e"),  # noqa: E501
    )
    # Source: lll
    # {
    #    ; (mulmod x y 0) is zero
    #    [[0]] (mulmod 5 1 0)
    # }
    contract_15 = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.MULMOD(0x5, 0x1, 0x0)) + Op.STOP,
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        address=Address("0x000000000000000000000000000000000000100f"),  # noqa: E501
    )
    # Source: lll
    # {
    #     (call 0xffffff (+ 0x1000 $4) 0 0 0 0 0)
    # }
    contract_16 = pre.deploy_contract(
        code=Op.CALL(gas=0xffffff, address=Op.ADD(0x1000, Op.CALLDATALOAD(offset=0x4)), value=0x0, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0)
        + Op.STOP,
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        address=Address("0xcccccccccccccccccccccccccccccccccccccccc"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xba1a9ce0ba1a9ce)

    expect_entries_: list[dict] = [
        {
            "indexes": {'data': [0, 1, 6, 9, 11, 12, 13, 15], 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        contract_0: Account(storage={0: 0}),
        contract_1: Account(storage={0: 0}),
        contract_6: Account(storage={0: 0}),
        contract_9: Account(storage={0: 0}),
        contract_11: Account(storage={0: 0}),
        contract_12: Account(storage={0: 0}),
        contract_13: Account(storage={0: 0}),
        contract_15: Account(storage={0: 0}),
    },
        },
        {
            "indexes": {'data': [2], 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {contract_2: Account(storage={0: 2})},
        },
        {
            "indexes": {'data': [3], 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {contract_3: Account(storage={0: 5})},
        },
        {
            "indexes": {'data': [4], 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {contract_4: Account(storage={0: 99})},
        },
        {
            "indexes": {'data': [5], 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {contract_5: Account(storage={0: 1})},
        },
        {
            "indexes": {'data': [7], 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {contract_7: Account(storage={0: 4})},
        },
        {
            "indexes": {'data': [8], 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {contract_8: Account(storage={0: 3})},
        },
        {
            "indexes": {'data': [10], 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {contract_10: Account(storage={0: 1})},
        },
        {
            "indexes": {'data': [14], 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {contract_14: Account(storage={0: 1})},
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx = Transaction(
        sender=sender,
        to=contract_16,
        data=_tx_data(d),
        gas_limit=TX_GAS[g],
        value=TX_VALUE[v],
        nonce=0,
        gas_price=10,
        error=_exc,
    )


    state_test(env=env, pre=pre, post=post, tx=tx)
