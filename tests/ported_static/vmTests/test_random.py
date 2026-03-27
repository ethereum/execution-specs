"""
Ori Pomerantz qbzzt1@gmail.com.

Ported from:
state_tests/VMTests/vmTests/randomFiller.yml
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
    "693c61390000000000000000000000000000000000000000000000000000000000000005",
]
TX_GAS = [16777216]
TX_VALUE = [1]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d])


@pytest.mark.ported_from(
    ["state_tests/VMTests/vmTests/randomFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0,
            0,
            0,
            id="random0",
        ),
        pytest.param(
            1,
            0,
            0,
            id="random1",
        ),
        pytest.param(
            2,
            0,
            0,
            id="random2",
        ),
        pytest.param(
            3,
            0,
            0,
            id="random3",
        ),
        pytest.param(
            4,
            0,
            0,
            id="random4",
        ),
        pytest.param(
            5,
            0,
            0,
            id="random5",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_random(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Ori Pomerantz qbzzt1@gmail."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0xF3630C36A29EC9AF814AE38E4D48056A3368BB1435C5C2B3289763E4C77A3DF0
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

    # Source: hex
    # 0x434342444244454597
    addr_0x0000000000000000000000000000000000001000 = pre.deploy_contract(  # noqa: F841
        code=Op.NUMBER * 2
        + Op.TIMESTAMP
        + Op.PREVRANDAO
        + Op.TIMESTAMP
        + Op.PREVRANDAO
        + Op.GASLIMIT * 2
        + Op.SWAP8,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x66b8dba513dc25f967ef7e84306616c0071cccae"),  # noqa: E501
    )
    # Source: hex
    # 0x4045404145454441343987ff3735043055
    addr_0x0000000000000000000000000000000000001001 = pre.deploy_contract(  # noqa: F841
        code=Op.BLOCKHASH
        + Op.BLOCKHASH(block_number=Op.GASLIMIT)
        + Op.COINBASE
        + Op.GASLIMIT * 2
        + Op.CODECOPY(
            dest_offset=Op.CALLVALUE, offset=Op.COINBASE, size=Op.PREVRANDAO
        )
        + Op.SELFDESTRUCT(address=Op.DUP8)
        + Op.CALLDATACOPY
        + Op.CALLDATALOAD
        + Op.SSTORE(key=Op.ADDRESS, value=Op.DIV),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x3412d3ebac3fcacfb451708aef7cc8e5bf1e5261"),  # noqa: E501
    )
    # Source: hex
    # 0x4040459143404144809759886d608f
    addr_0x0000000000000000000000000000000000001002 = pre.deploy_contract(  # noqa: F841
        code=bytes.fromhex("4040459143404144809759886d608f"),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x15adfb805be4f3ee3e5c535abc860890a3a2a6c9"),  # noqa: E501
    )
    # Source: hex
    # 0x7745414245403745f31387900a8d55
    addr_0x0000000000000000000000000000000000001003 = pre.deploy_contract(  # noqa: F841
        code=bytes.fromhex("7745414245403745f31387900a8d55"),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0xdfe69e96fb3aafde261565670b1fea29869c6950"),  # noqa: E501
    )
    # Source: hex
    # 0x65424555
    addr_0x0000000000000000000000000000000000001004 = pre.deploy_contract(  # noqa: F841
        code=bytes.fromhex("65424555"),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0xacd000f275b1a28d0c3b7dee7f114c4d28fb1636"),  # noqa: E501
    )
    # Source: hex
    # 0x4041
    addr_0x0000000000000000000000000000000000001005 = pre.deploy_contract(  # noqa: F841
        code=Op.BLOCKHASH + Op.COINBASE,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x2e3b99613a2e74ebb0cd62d7b9eb38bad240cec6"),  # noqa: E501
    )
    # Source: lll
    # {
    #     (call (gas) (+ 0x1000 $4) 0 0 0 0 0)
    # }
    target = pre.deploy_contract(  # noqa: F841
        code=Op.CALL(
            gas=Op.GAS,
            address=Op.ADD(0x1000, Op.CALLDATALOAD(offset=0x4)),
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0xa83db56c7ce68c06129b80c7be0d0f5e0869d536"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x10000000000000)

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": [0], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {sender: Account(nonce=1)},
        },
        {
            "indexes": {"data": [1], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {sender: Account(nonce=1)},
        },
        {
            "indexes": {"data": [2], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {sender: Account(nonce=1)},
        },
        {
            "indexes": {"data": [3], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {sender: Account(nonce=1)},
        },
        {
            "indexes": {"data": [4], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {sender: Account(nonce=1)},
        },
        {
            "indexes": {"data": [5], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {sender: Account(nonce=1)},
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx = Transaction(
        sender=sender,
        to=target,
        data=_tx_data(d),
        gas_limit=TX_GAS[g],
        value=TX_VALUE[v],
        gas_price=10,
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
