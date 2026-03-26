"""
Ori Pomerantz qbzzt1@gmail.com

Ported from:
state_tests/VMTests/vmIOandFlowOperations/returnFiller.yml
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
]
TX_GAS = [16777216]
TX_VALUE = [1]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d])


@pytest.mark.ported_from(
    ["state_tests/VMTests/vmIOandFlowOperations/returnFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0, 0, 0,
            id="return",
        ),
        pytest.param(
            1, 0, 0,
            id="returnInfBuff",
        ),
        pytest.param(
            2, 0, 0,
            id="returnBigBuff",
        ),
        pytest.param(
            3, 0, 0,
            id="returnOffset",
        ),
        pytest.param(
            4, 0, 0,
            id="returnOld",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_return(
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
    contract_5 = Address("0xcccccccccccccccccccccccccccccccccccccccc")
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
    #    [0] 0x0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef
    #    [[0xFF]] 0x600D
    #    (return 0x00 0x40)
    # }
    contract_0 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x0, value=0x123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef)
        + Op.SSTORE(key=0xff, value=0x600d) + Op.RETURN(offset=0x0, size=0x40)
        + Op.STOP,
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001000"),  # noqa: E501
    )
    # Source: lll
    # {
    #    [0] 0x0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef
    #    [[0xFF]] 0x600D
    #    (return 0x00 (- 0 1))
    # }
    contract_1 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x0, value=0x123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef)
        + Op.SSTORE(key=0xff, value=0x600d)
        + Op.RETURN(offset=0x0, size=Op.SUB(0x0, 0x1)) + Op.STOP,
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001001"),  # noqa: E501
    )
    # Source: lll
    # {
    #    [0] 0x0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef
    #    [[0xFF]] 0x600D
    #    (return 0x00 0x1000)
    # }
    contract_2 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x0, value=0x123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef)
        + Op.SSTORE(key=0xff, value=0x600d) + Op.RETURN(offset=0x0, size=0x1000)  # noqa: E501
        + Op.STOP,
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001002"),  # noqa: E501
    )
    # Source: lll
    # {
    #    [0] 0x0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef
    #    [[0xFF]] 0x600D
    #    (return 0x05 0x20)
    # }
    contract_3 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x0, value=0x123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef)
        + Op.SSTORE(key=0xff, value=0x600d) + Op.RETURN(offset=0x5, size=0x20)
        + Op.STOP,
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001003"),  # noqa: E501
    )
    # Source: raw
    # 0x6001608052600060805111601b57600160005260206000f3602b565b602760005260206000f360026080525b00
    contract_4 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x80, value=0x1)
        + Op.JUMPI(pc=0x1b, condition=Op.GT(Op.MLOAD(offset=0x80), 0x0))
        + Op.MSTORE(offset=0x0, value=0x1) + Op.RETURN(offset=0x0, size=0x20)
        + Op.JUMP(pc=0x2b) + Op.JUMPDEST + Op.MSTORE(offset=0x0, value=0x27)
        + Op.RETURN(offset=0x0, size=0x20) + Op.MSTORE(offset=0x80, value=0x2)
        + Op.JUMPDEST + Op.STOP,
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001004"),  # noqa: E501
    )
    # Source: lll
    # {
    #     ; read 0x40 bytes of return data
    #     (delegatecall 0xffffff (+ 0x1000 $4) 0 0 0x00 0x40)
    # 
    #     [[0]] @0x00
    #     [[1]] @0x20
    # }
    contract_5 = pre.deploy_contract(
        code=Op.POP(Op.DELEGATECALL(gas=0xffffff, address=Op.ADD(0x1000, Op.CALLDATALOAD(offset=0x4)), args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x40))
        + Op.SSTORE(key=0x0, value=Op.MLOAD(offset=0x0))
        + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x20)) + Op.STOP,
        storage={255: 2989},
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        address=Address("0xcccccccccccccccccccccccccccccccccccccccc"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xba1a9ce0ba1a9ce)

    expect_entries_: list[dict] = [
        {
            "indexes": {'data': [0, 2], 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        contract_5: Account(
                storage={
            0: 0x123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef,
            1: 0,
            255: 24589,
        },
            ),
    },
        },
        {
            "indexes": {'data': [1], 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {contract_5: Account(storage={255: 2989})},
        },
        {
            "indexes": {'data': [3], 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        contract_5: Account(
                storage={
            0: 0xabcdef0123456789abcdef0123456789abcdef0123456789abcdef0000000000,
            1: 0,
            255: 24589,
        },
            ),
    },
        },
        {
            "indexes": {'data': [4], 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {contract_5: Account(storage={0: 39, 255: 2989})},
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx = Transaction(
        sender=sender,
        to=contract_5,
        data=_tx_data(d),
        gas_limit=TX_GAS[g],
        value=TX_VALUE[v],
        nonce=0,
        gas_price=10,
        error=_exc,
    )


    state_test(env=env, pre=pre, post=post, tx=tx)
