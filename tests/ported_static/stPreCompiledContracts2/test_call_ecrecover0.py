"""
test_call_ecrecover0

Ported from:
state_tests/stPreCompiledContracts2/CallEcrecover0Filler.json
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
    ["state_tests/stPreCompiledContracts2/CallEcrecover0Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_call_ecrecover0(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """test_call_ecrecover0"""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    contract_0 = Address("0x095e7baea6a6c7c4c2dfeb977efac326af552d87")
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
        gas_limit=10000000,
    )

    # Source: lll
    # { (MSTORE 0 0x18c547e4f7b0f325ad1e56f57e26c745b09a3e503d86e00e5255ff7f715d3d1c) (MSTORE 32 28) (MSTORE 64 0x73b1693892219d736caba55bdb67216e485557ea6b6af75f37096c9aa6a5a75f) (MSTORE 96 0xeeb940b1d03b21e36b0e47e79769f095fe2ab855bd91e3a38756b7d75a9c4549) [[ 2 ]] (CALL 300000 1 0 0 128 128 32) [[ 0 ]] (MOD (MLOAD 128) (EXP 2 160)) [[ 1 ]] (EQ (ORIGIN) (SLOAD 0))  }
    contract_0 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x0, value=0x18c547e4f7b0f325ad1e56f57e26c745b09a3e503d86e00e5255ff7f715d3d1c)
        + Op.MSTORE(offset=0x20, value=0x1c)
        + Op.MSTORE(offset=0x40, value=0x73b1693892219d736caba55bdb67216e485557ea6b6af75f37096c9aa6a5a75f)
        + Op.MSTORE(offset=0x60, value=0xeeb940b1d03b21e36b0e47e79769f095fe2ab855bd91e3a38756b7d75a9c4549)
        + Op.SSTORE(key=0x2, value=Op.CALL(gas=0x493e0, address=0x1, value=0x0, args_offset=0x0, args_size=0x80, ret_offset=0x80, ret_size=0x20))  # noqa: E501
        + Op.SSTORE(key=0x0, value=Op.MOD(Op.MLOAD(offset=0x80), Op.EXP(0x2, 0xa0)))  # noqa: E501
        + Op.SSTORE(key=0x1, value=Op.EQ(Op.ORIGIN, Op.SLOAD(key=0x0))) + Op.STOP,  # noqa: E501
        balance=0x1312d00,
        nonce=0,
        address=Address("0x095e7baea6a6c7c4c2dfeb977efac326af552d87"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000)


    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=b'',
        gas_limit=3652240,
        value=0x186a0,
        nonce=0,
        gas_price=10,
    )

    post = {
        contract_0: Account(
                storage={
            0: 0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b,
            1: 1,
            2: 1,
        },
            ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
