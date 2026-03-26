"""
Ori Pomerantz qbzzt1@gmail.com

Ported from:
state_tests/stEIP150singleCodeGasPrices/eip2929OOGFiller.yml
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
    "1a8451e6000000000000000000000000000000000000000000000000000000000000105400000000000000000000000000000000000000000000000000000000000007d0",
    "1a8451e6000000000000000000000000000000000000000000000000000000000000105500000000000000000000000000000000000000000000000000000000000055f0",
    "1a8451e6000000000000000000000000000000000000000000000000000000000000103100000000000000000000000000000000000000000000000000000000000007d0",
    "1a8451e6000000000000000000000000000000000000000000000000000000000000103b00000000000000000000000000000000000000000000000000000000000009c4",
    "1a8451e6000000000000000000000000000000000000000000000000000000000000103c00000000000000000000000000000000000000000000000000000000000009c4",
    "1a8451e6000000000000000000000000000000000000000000000000000000000000103f00000000000000000000000000000000000000000000000000000000000009c4",
    "1a8451e600000000000000000000000000000000000000000000000000000000000010f100000000000000000000000000000000000000000000000000000000000006d6",
    "1a8451e600000000000000000000000000000000000000000000000000000000000010f200000000000000000000000000000000000000000000000000000000000006d6",
    "1a8451e600000000000000000000000000000000000000000000000000000000000010f400000000000000000000000000000000000000000000000000000000000006d6",
    "1a8451e600000000000000000000000000000000000000000000000000000000000010fa00000000000000000000000000000000000000000000000000000000000006d6",
]
TX_GAS = [16777216]
TX_VALUE = [1]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d])


@pytest.mark.ported_from(
    ["state_tests/stEIP150singleCodeGasPrices/eip2929OOGFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0, 0, 0,
            id="failEIP2929",
        ),
        pytest.param(
            1, 0, 0,
            id="failEIP2929",
        ),
        pytest.param(
            2, 0, 0,
            id="failEIP2929",
        ),
        pytest.param(
            3, 0, 0,
            id="failEIP2929",
        ),
        pytest.param(
            4, 0, 0,
            id="failEIP2929",
        ),
        pytest.param(
            5, 0, 0,
            id="failEIP2929",
        ),
        pytest.param(
            6, 0, 0,
            id="failEIP2929",
        ),
        pytest.param(
            7, 0, 0,
            id="failEIP2929",
        ),
        pytest.param(
            8, 0, 0,
            id="failEIP2929",
        ),
        pytest.param(
            9, 0, 0,
            id="failEIP2929",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_eip2929_oog(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Ori Pomerantz qbzzt1@gmail."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    contract_0 = Address("0x0000000000000000000000000000000000001054")
    contract_1 = Address("0x0000000000000000000000000000000000001055")
    contract_2 = Address("0x0000000000000000000000000000000000001031")
    contract_3 = Address("0x000000000000000000000000000000000000103b")
    contract_4 = Address("0x000000000000000000000000000000000000103c")
    contract_5 = Address("0x000000000000000000000000000000000000103f")
    contract_6 = Address("0x00000000000000000000000000000000000010f1")
    contract_7 = Address("0x00000000000000000000000000000000000010f2")
    contract_8 = Address("0x00000000000000000000000000000000000010f4")
    contract_9 = Address("0x00000000000000000000000000000000000010fa")
    contract_10 = Address("0x000000000000000000000000000000000000acc7")
    contract_11 = Address("0xcccccccccccccccccccccccccccccccccccccccc")
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
    #    @@0
    # }
    contract_0 = pre.deploy_contract(
        code=Op.SLOAD(key=0x0) + Op.STOP,
        balance=0xba1a9ce0ba1a9ce,
        nonce=1,
        address=Address("0x0000000000000000000000000000000000001054"),  # noqa: E501
    )
    # Source: lll
    # {
    #    [[0]] 0x60A7
    # }
    contract_1 = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=0x60a7) + Op.STOP,
        balance=0xba1a9ce0ba1a9ce,
        nonce=1,
        address=Address("0x0000000000000000000000000000000000001055"),  # noqa: E501
    )
    # Source: lll
    # {
    #    (balance 0xACC7)
    # }
    contract_2 = pre.deploy_contract(
        code=Op.BALANCE(address=0xacc7) + Op.STOP,
        balance=0xba1a9ce0ba1a9ce,
        nonce=1,
        address=Address("0x0000000000000000000000000000000000001031"),  # noqa: E501
    )
    # Source: lll
    # {
    #    (extcodesize 0x1031)
    # }
    contract_3 = pre.deploy_contract(
        code=Op.EXTCODESIZE(address=0x1031) + Op.STOP,
        balance=0xba1a9ce0ba1a9ce,
        nonce=1,
        address=Address("0x000000000000000000000000000000000000103b"),  # noqa: E501
    )
    # Source: lll
    # {
    #    (extcodecopy 0x1031 0 0 0x20)
    # }
    contract_4 = pre.deploy_contract(
        code=Op.EXTCODECOPY(address=0x1031, dest_offset=0x0, offset=0x0, size=0x20)
        + Op.STOP,
        balance=0xba1a9ce0ba1a9ce,
        nonce=1,
        address=Address("0x000000000000000000000000000000000000103c"),  # noqa: E501
    )
    # Source: lll
    # {
    #    (extcodehash 0x1031)
    # }
    contract_5 = pre.deploy_contract(
        code=Op.EXTCODEHASH(address=0x1031) + Op.STOP,
        balance=0xba1a9ce0ba1a9ce,
        nonce=1,
        address=Address("0x000000000000000000000000000000000000103f"),  # noqa: E501
    )
    # Source: lll
    # {
    #    (call 0x06A5 0xACC7 0 0 0 0 0)
    # }
    contract_6 = pre.deploy_contract(
        code=Op.CALL(gas=0x6a5, address=0xacc7, value=0x0, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0)
        + Op.STOP,
        balance=0xba1a9ce0ba1a9ce,
        nonce=1,
        address=Address("0x00000000000000000000000000000000000010f1"),  # noqa: E501
    )
    # Source: lll
    # {
    #    (callcode 0x06A5 0xACC7 0 0 0 0 0)
    # }
    contract_7 = pre.deploy_contract(
        code=Op.CALLCODE(gas=0x6a5, address=0xacc7, value=0x0, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0)
        + Op.STOP,
        balance=0xba1a9ce0ba1a9ce,
        nonce=1,
        address=Address("0x00000000000000000000000000000000000010f2"),  # noqa: E501
    )
    # Source: lll
    # {
    #    (delegatecall 0x06A5 0xACC7 0 0 0 0)
    # }
    contract_8 = pre.deploy_contract(
        code=Op.DELEGATECALL(gas=0x6a5, address=0xacc7, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0)
        + Op.STOP,
        balance=0xba1a9ce0ba1a9ce,
        nonce=1,
        address=Address("0x00000000000000000000000000000000000010f4"),  # noqa: E501
    )
    # Source: lll
    # {
    #    (staticcall 0x06A5 0xACC7 0 0 0 0)
    # }
    contract_9 = pre.deploy_contract(
        code=Op.STATICCALL(gas=0x6a5, address=0xacc7, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0)
        + Op.STOP,
        balance=0xba1a9ce0ba1a9ce,
        nonce=1,
        address=Address("0x00000000000000000000000000000000000010fa"),  # noqa: E501
    )
    # Source: lll
    # {
    #    (return 0 0)
    # }
    contract_10 = pre.deploy_contract(
        code=Op.RETURN(offset=0x0, size=0x0) + Op.STOP,
        balance=0xba1a9ce0ba1a9ce,
        nonce=1,
        address=Address("0x000000000000000000000000000000000000acc7"),  # noqa: E501
    )
    # Source: lll
    # {
    #    (def 'addr     $4)     ; the address to call
    #    (def 'callGas $36)     ; the amount of gas to give it
    # 
    #    [[0]] (call callGas addr 0 0 0 0 0)
    # }
    contract_11 = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.CALL(gas=Op.CALLDATALOAD(offset=0x24), address=Op.CALLDATALOAD(offset=0x4), value=0x0, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))  # noqa: E501
        + Op.STOP,
        storage={0: 24743},
        balance=0xba1a9ce0ba1a9ce,
        nonce=1,
        address=Address("0xcccccccccccccccccccccccccccccccccccccccc"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xba1a9ce0ba1a9ce, nonce=1)

    expect_entries_: list[dict] = [
        {
            "indexes": {'data': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9], 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {contract_11: Account(storage={0: 0})},
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx = Transaction(
        sender=sender,
        to=contract_11,
        data=_tx_data(d),
        gas_limit=TX_GAS[g],
        value=TX_VALUE[v],
        nonce=1,
        gas_price=10,
        error=_exc,
    )


    state_test(env=env, pre=pre, post=post, tx=tx)
