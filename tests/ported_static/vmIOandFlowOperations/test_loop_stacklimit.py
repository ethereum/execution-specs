"""
Ori Pomerantz qbzzt1@gmail.com.

Ported from:
state_tests/VMTests/vmIOandFlowOperations/loop_stacklimitFiller.yml
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
]
TX_GAS = [16777216]
TX_VALUE = [1]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d])


@pytest.mark.ported_from(
    ["state_tests/VMTests/vmIOandFlowOperations/loop_stacklimitFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0,
            0,
            0,
            id="loop_1021",
        ),
        pytest.param(
            1,
            0,
            0,
            id="loop_1020",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_loop_stacklimit(
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
        key=0xA62D63F95900B04CCD3FEE13360DE78966F24695945E8B2C09E646352BC5AF94
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
    #    (asm 0 CALLVALUE JUMPDEST 1 SWAP1 SUB SWAP1 1 ADD DUP2 DUP1 3 JUMPI 0 MSTORE 1 MSTORE 0 MSIZE RETURN)  # noqa: E501
    # }
    addr_0x0000000000000000000000000000000000001000 = pre.deploy_contract(  # noqa: F841
        code=Op.PUSH1[0x0]
        + Op.CALLVALUE
        + Op.JUMPDEST
        + Op.PUSH1[0x1]
        + Op.SWAP1
        + Op.SUB
        + Op.SWAP1
        + Op.PUSH1[0x1]
        + Op.ADD
        + Op.DUP2
        + Op.JUMPI(pc=0x3, condition=Op.DUP1)
        + Op.PUSH1[0x0]
        + Op.MSTORE
        + Op.PUSH1[0x1]
        + Op.MSTORE
        + Op.RETURN(offset=Op.MSIZE, size=0x0)
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x15f0298e83391f673b708790f259f3f34dfbd788"),  # noqa: E501
    )
    # Source: raw
    # 0x6000345b60019003906001018180600357600052600152600059f300
    addr_0x0000000000000000000000000000000000001001 = pre.deploy_contract(  # noqa: F841
        code=Op.PUSH1[0x0]
        + Op.CALLVALUE
        + Op.JUMPDEST
        + Op.PUSH1[0x1]
        + Op.SWAP1
        + Op.SUB
        + Op.SWAP1
        + Op.PUSH1[0x1]
        + Op.ADD
        + Op.DUP2
        + Op.JUMPI(pc=0x3, condition=Op.DUP1)
        + Op.PUSH1[0x0]
        + Op.MSTORE
        + Op.PUSH1[0x1]
        + Op.MSTORE
        + Op.RETURN(offset=Op.MSIZE, size=0x0)
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x3b20573c5048e5ba16083407e59fc0bbc044b6c0"),  # noqa: E501
    )
    # Source: lll
    # {
    #     (delegatecall (gas) (+ 0x1000 $4) 0 0 0 0)
    # }
    target = pre.deploy_contract(  # noqa: F841
        code=Op.DELEGATECALL(
            gas=Op.GAS,
            address=Op.ADD(0x1000, Op.CALLDATALOAD(offset=0x4)),
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        storage={0: 0},
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0xf9b46c1d708104b4e6007d17ae485b0a00d8e952"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x100000000000)

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": [0, 1], "gas": -1, "value": -1},
            "network": [">=Cancun"],
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
        gas_price=10,
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
