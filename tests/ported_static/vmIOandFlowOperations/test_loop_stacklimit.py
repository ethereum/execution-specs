"""
Ori Pomerantz qbzzt1@gmail.com.

Ported from:
state_tests/VMTests/vmIOandFlowOperations/loop_stacklimitFiller.yml
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
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


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
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = pre.fund_eoa(amount=0x100000000000)

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    # Source: lll
    # {
    #    (asm 0 CALLVALUE JUMPDEST 1 SWAP1 SUB SWAP1 1 ADD DUP2 DUP1 3 JUMPI 0 MSTORE 1 MSTORE 0 MSIZE RETURN)  # noqa: E501
    # }
    addr = pre.deploy_contract(  # noqa: F841
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
        address=Address(0x15F0298E83391F673B708790F259F3F34DFBD788),  # noqa: E501
    )
    # Source: raw
    # 0x6000345b60019003906001018180600357600052600152600059f300
    addr_2 = pre.deploy_contract(  # noqa: F841
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
        address=Address(0x3B20573C5048E5BA16083407E59FC0BBC044B6C0),  # noqa: E501
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
        address=Address(0xF9B46C1D708104B4E6007D17AE485B0A00D8E952),  # noqa: E501
    )

    tx_data = [
        Bytes("693c6139") + Hash(0x0),
        Bytes("693c6139") + Hash(0x1),
    ]
    tx_gas = [16777216]
    tx_value = [1]

    tx = Transaction(
        sender=sender,
        to=target,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        value=tx_value[v],
    )

    post = {target: Account(storage={0: 0})}

    state_test(env=env, pre=pre, post=post, tx=tx)
