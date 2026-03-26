"""
test_callcode_ecrecover3

Ported from:
state_tests/stPreCompiledContracts2/CALLCODEEcrecover3Filler.json
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
    ["state_tests/stPreCompiledContracts2/CALLCODEEcrecover3Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_callcode_ecrecover3(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """test_callcode_ecrecover3"""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0xe04d1ac7ddda0c98397d56a0b501e960d4cd325a39286919ac23c1a07009a869
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    # Source: lll
    # { (MSTORE 0 0x2f380a2dea7e778d81affc2443403b8fe4644db442ae4862ff5bb3732829cdb9) (MSTORE 32 27) (MSTORE 64 0x6b65ccb0558806e9b097f27a396d08f964e37b8b7af6ceeb516ff86739fbea0a) (MSTORE 96 0x37cbc8d883e129a4b1ef9d5f1df53c4f21a3ef147cf2a50a4ede0eb06ce092d4) [[ 2 ]] (CALLCODE 100000 1 0 0 128 128 32) [[ 0 ]] (MOD (MLOAD 128) (EXP 2 160)) [[ 1 ]] (EQ (ORIGIN) (SLOAD 0))  }
    target = pre.deploy_contract(
        code=Op.MSTORE(offset=0x0, value=0x2f380a2dea7e778d81affc2443403b8fe4644db442ae4862ff5bb3732829cdb9)
        + Op.MSTORE(offset=0x20, value=0x1b)
        + Op.MSTORE(offset=0x40, value=0x6b65ccb0558806e9b097f27a396d08f964e37b8b7af6ceeb516ff86739fbea0a)
        + Op.MSTORE(offset=0x60, value=0x37cbc8d883e129a4b1ef9d5f1df53c4f21a3ef147cf2a50a4ede0eb06ce092d4)
        + Op.SSTORE(key=0x2, value=Op.CALLCODE(gas=0x186a0, address=0x1, value=0x0, args_offset=0x0, args_size=0x80, ret_offset=0x80, ret_size=0x20))  # noqa: E501
        + Op.SSTORE(key=0x0, value=Op.MOD(Op.MLOAD(offset=0x80), Op.EXP(0x2, 0xa0)))  # noqa: E501
        + Op.SSTORE(key=0x1, value=Op.EQ(Op.ORIGIN, Op.SLOAD(key=0x0))) + Op.STOP,  # noqa: E501
        balance=0x1312d00,
        nonce=0,
        address=Address("0xfbedf77edb387c8e6d9b016f522d38201f4de408"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000)


    tx = Transaction(
        sender=sender,
        to=target,
        data=b'',
        gas_limit=365224,
        value=0x186a0,
        nonce=0,
        gas_price=10,
    )

    post = {
        target: Account(
                storage={
            0: 0xe4319f4b631c6d0fcfc84045dbcb676865fe5e13,
            2: 1,
        },
            ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
