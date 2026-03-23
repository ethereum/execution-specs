"""
Ori Pomerantz qbzzt1@gmail.com.

Ported from:
tests/static/state_tests/VMTests/vmIOandFlowOperations/returnFiller.yml
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
    return bytes.fromhex(TX_DATA[d]) if TX_DATA[d] else b""


@pytest.mark.ported_from(
    [
        "tests/static/state_tests/VMTests/vmIOandFlowOperations/returnFiller.yml",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(2, 0, 0, id="case0"),
        pytest.param(1, 0, 0, id="case1"),
        pytest.param(3, 0, 0, id="case2"),
        pytest.param(4, 0, 0, id="case3"),
        pytest.param(0, 0, 0, id="case4"),
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
    """Ori Pomerantz qbzzt1@gmail.com."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    callee = pre.deploy_contract(
        code=(
            Op.MSTORE(
                offset=0x0,
                value=0x123456789ABCDEF0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF,  # noqa: E501
            )
            + Op.SSTORE(key=0xFF, value=0x600D)
            + Op.RETURN(offset=0x0, size=0x40)
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001000"),  # noqa: E501
    )
    callee_1 = pre.deploy_contract(
        code=(
            Op.MSTORE(
                offset=0x0,
                value=0x123456789ABCDEF0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF,  # noqa: E501
            )
            + Op.SSTORE(key=0xFF, value=0x600D)
            + Op.RETURN(offset=0x0, size=Op.SUB(0x0, 0x1))
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001001"),  # noqa: E501
    )
    callee_2 = pre.deploy_contract(
        code=(
            Op.MSTORE(
                offset=0x0,
                value=0x123456789ABCDEF0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF,  # noqa: E501
            )
            + Op.SSTORE(key=0xFF, value=0x600D)
            + Op.RETURN(offset=0x0, size=0x1000)
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001002"),  # noqa: E501
    )
    callee_3 = pre.deploy_contract(
        code=(
            Op.MSTORE(
                offset=0x0,
                value=0x123456789ABCDEF0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF,  # noqa: E501
            )
            + Op.SSTORE(key=0xFF, value=0x600D)
            + Op.RETURN(offset=0x5, size=0x20)
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001003"),  # noqa: E501
    )
    # Source: raw bytecode
    callee_4 = pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x80, value=0x1)
            + Op.JUMPI(pc=0x1B, condition=Op.GT(Op.MLOAD(offset=0x80), 0x0))
            + Op.MSTORE(offset=0x0, value=0x1)
            + Op.RETURN(offset=0x0, size=0x20)
            + Op.JUMP(pc=0x2B)
            + Op.JUMPDEST
            + Op.MSTORE(offset=0x0, value=0x27)
            + Op.RETURN(offset=0x0, size=0x20)
            + Op.MSTORE(offset=0x80, value=0x2)
            + Op.JUMPDEST
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001004"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xBA1A9CE0BA1A9CE)
    # Source: LLL
    # {
    #     ; read 0x40 bytes of return data
    #     (delegatecall 0xffffff (+ 0x1000 $4) 0 0 0x00 0x40)
    #
    #     [[0]] @0x00
    #     [[1]] @0x20
    # }
    contract = pre.deploy_contract(
        code=(
            Op.POP(
                Op.DELEGATECALL(
                    gas=0xFFFFFF,
                    address=Op.ADD(0x1000, Op.CALLDATALOAD(offset=0x4)),
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x40,
                ),
            )
            + Op.SSTORE(key=0x0, value=Op.MLOAD(offset=0x0))
            + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x20))
            + Op.STOP
        ),
        storage={0xFF: 0xBAD},
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0xcccccccccccccccccccccccccccccccccccccccc"),  # noqa: E501
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": 2, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "7f0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef60005261600d60ff5560406000f300"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "7f0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef60005261600d60ff5560016000036000f300"  # noqa: E501
                    )
                ),
                callee_2: Account(
                    code=bytes.fromhex(
                        "7f0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef60005261600d60ff556110006000f300"  # noqa: E501
                    )
                ),
                callee_3: Account(
                    code=bytes.fromhex(
                        "7f0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef60005261600d60ff5560206005f300"  # noqa: E501
                    )
                ),
                callee_4: Account(
                    code=bytes.fromhex(
                        "6001608052600060805111601b57600160005260206000f3602b565b602760005260206000f360026080525b00"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={
                        0: 0x123456789ABCDEF0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF,  # noqa: E501
                        255: 24589,
                    },
                    code=bytes.fromhex(
                        "60406000600060006004356110000162fffffff45060005160005560205160015500"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 1, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "7f0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef60005261600d60ff5560406000f300"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "7f0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef60005261600d60ff5560016000036000f300"  # noqa: E501
                    )
                ),
                callee_2: Account(
                    code=bytes.fromhex(
                        "7f0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef60005261600d60ff556110006000f300"  # noqa: E501
                    )
                ),
                callee_3: Account(
                    code=bytes.fromhex(
                        "7f0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef60005261600d60ff5560206005f300"  # noqa: E501
                    )
                ),
                callee_4: Account(
                    code=bytes.fromhex(
                        "6001608052600060805111601b57600160005260206000f3602b565b602760005260206000f360026080525b00"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={255: 2989},
                    code=bytes.fromhex(
                        "60406000600060006004356110000162fffffff45060005160005560205160015500"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 3, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "7f0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef60005261600d60ff5560406000f300"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "7f0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef60005261600d60ff5560016000036000f300"  # noqa: E501
                    )
                ),
                callee_2: Account(
                    code=bytes.fromhex(
                        "7f0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef60005261600d60ff556110006000f300"  # noqa: E501
                    )
                ),
                callee_3: Account(
                    code=bytes.fromhex(
                        "7f0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef60005261600d60ff5560206005f300"  # noqa: E501
                    )
                ),
                callee_4: Account(
                    code=bytes.fromhex(
                        "6001608052600060805111601b57600160005260206000f3602b565b602760005260206000f360026080525b00"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={
                        0: 0xABCDEF0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF0000000000,  # noqa: E501
                        255: 24589,
                    },
                    code=bytes.fromhex(
                        "60406000600060006004356110000162fffffff45060005160005560205160015500"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 4, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "7f0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef60005261600d60ff5560406000f300"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "7f0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef60005261600d60ff5560016000036000f300"  # noqa: E501
                    )
                ),
                callee_2: Account(
                    code=bytes.fromhex(
                        "7f0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef60005261600d60ff556110006000f300"  # noqa: E501
                    )
                ),
                callee_3: Account(
                    code=bytes.fromhex(
                        "7f0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef60005261600d60ff5560206005f300"  # noqa: E501
                    )
                ),
                callee_4: Account(
                    code=bytes.fromhex(
                        "6001608052600060805111601b57600160005260206000f3602b565b602760005260206000f360026080525b00"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={0: 39, 255: 2989},
                    code=bytes.fromhex(
                        "60406000600060006004356110000162fffffff45060005160005560205160015500"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 0, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "7f0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef60005261600d60ff5560406000f300"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "7f0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef60005261600d60ff5560016000036000f300"  # noqa: E501
                    )
                ),
                callee_2: Account(
                    code=bytes.fromhex(
                        "7f0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef60005261600d60ff556110006000f300"  # noqa: E501
                    )
                ),
                callee_3: Account(
                    code=bytes.fromhex(
                        "7f0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef60005261600d60ff5560206005f300"  # noqa: E501
                    )
                ),
                callee_4: Account(
                    code=bytes.fromhex(
                        "6001608052600060805111601b57600160005260206000f3602b565b602760005260206000f360026080525b00"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={
                        0: 0x123456789ABCDEF0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF,  # noqa: E501
                        255: 24589,
                    },
                    code=bytes.fromhex(
                        "60406000600060006004356110000162fffffff45060005160005560205160015500"  # noqa: E501
                    ),
                ),
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx = Transaction(
        sender=sender,
        to=contract,
        data=_tx_data(d),
        gas_limit=TX_GAS[g],
        value=TX_VALUE[v],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
