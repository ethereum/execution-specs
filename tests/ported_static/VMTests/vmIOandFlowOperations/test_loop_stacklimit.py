"""
Ori Pomerantz qbzzt1@gmail.com.

Ported from:
tests/static/state_tests/VMTests/vmIOandFlowOperations
loop_stacklimitFiller.yml
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

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    [
        "tests/static/state_tests/VMTests/vmIOandFlowOperations/loop_stacklimitFiller.yml",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex, expected_post",
    [
        (
            "693c61390000000000000000000000000000000000000000000000000000000000000001",  # noqa: E501
            {},
        ),
        (
            "693c61390000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
            {},
        ),
    ],
    ids=["case0", "case1"],
)
@pytest.mark.pre_alloc_mutable
def test_loop_stacklimit(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
    expected_post: dict,
) -> None:
    """Ori Pomerantz qbzzt1@gmail.com."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0xA62D63F95900B04CCD3FEE13360DE78966F24695945E8B2C09E646352BC5AF94
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.PUSH1[0x0]
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
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x15f0298e83391f673b708790f259f3f34dfbd788"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.PUSH1[0x0]
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
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x3b20573c5048e5ba16083407e59fc0bbc044b6c0"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x100000000000)
    # Source: LLL
    # {
    #     (delegatecall (gas) (+ 0x1000 $4) 0 0 0 0)
    # }
    contract = pre.deploy_contract(
        code=(
            Op.DELEGATECALL(
                gas=Op.GAS,
                address=Op.ADD(0x1000, Op.CALLDATALOAD(offset=0x4)),
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
            + Op.STOP
        ),
        storage={0x0: 0x0},
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0xf9b46c1d708104b4e6007d17ae485b0a00d8e952"),  # noqa: E501
    )

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        sender=sender,
        to=contract,
        data=tx_data,
        gas_limit=16777216,
        value=1,
    )

    post = expected_post

    state_test(env=env, pre=pre, post=post, tx=tx)
