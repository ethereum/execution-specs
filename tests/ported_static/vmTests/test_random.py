"""
Ori Pomerantz qbzzt1@gmail.com.

Ported from:
state_tests/VMTests/vmTests/randomFiller.yml
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Bytes,
    Environment,
    Hash,
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
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = pre.fund_eoa(amount=0x10000000000000)

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    # Source: hex
    # 0x434342444244454597
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.NUMBER * 2
        + Op.TIMESTAMP
        + Op.PREVRANDAO
        + Op.TIMESTAMP
        + Op.PREVRANDAO
        + Op.GASLIMIT * 2
        + Op.SWAP8,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x66B8DBA513DC25F967EF7E84306616C0071CCCAE),  # noqa: E501
    )
    # Source: hex
    # 0x4045404145454441343987ff3735043055
    addr_2 = pre.deploy_contract(  # noqa: F841
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
        address=Address(0x3412D3EBAC3FCACFB451708AEF7CC8E5BF1E5261),  # noqa: E501
    )
    # Source: hex
    # 0x4040459143404144809759886d608f
    addr_3 = pre.deploy_contract(  # noqa: F841
        code=bytes.fromhex("4040459143404144809759886d608f"),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x15ADFB805BE4F3EE3E5C535ABC860890A3A2A6C9),  # noqa: E501
    )
    # Source: hex
    # 0x7745414245403745f31387900a8d55
    addr_4 = pre.deploy_contract(  # noqa: F841
        code=bytes.fromhex("7745414245403745f31387900a8d55"),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0xDFE69E96FB3AAFDE261565670B1FEA29869C6950),  # noqa: E501
    )
    # Source: hex
    # 0x65424555
    addr_5 = pre.deploy_contract(  # noqa: F841
        code=bytes.fromhex("65424555"),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0xACD000F275B1A28D0C3B7DEE7F114C4D28FB1636),  # noqa: E501
    )
    # Source: hex
    # 0x4041
    addr_6 = pre.deploy_contract(  # noqa: F841
        code=Op.BLOCKHASH + Op.COINBASE,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x2E3B99613A2E74EBB0CD62D7B9EB38BAD240CEC6),  # noqa: E501
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
        address=Address(0xA83DB56C7CE68C06129B80C7BE0D0F5E0869D536),  # noqa: E501
    )

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

    tx_data = [
        Bytes("693c6139") + Hash(0x0),
        Bytes("693c6139") + Hash(0x1),
        Bytes("693c6139") + Hash(0x2),
        Bytes("693c6139") + Hash(0x3),
        Bytes("693c6139") + Hash(0x4),
        Bytes("693c6139") + Hash(0x5),
    ]
    tx_gas = [16777216]
    tx_value = [1]

    tx = Transaction(
        sender=sender,
        to=target,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        value=tx_value[v],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
