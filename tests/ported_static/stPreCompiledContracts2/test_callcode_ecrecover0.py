"""
Test_callcode_ecrecover0.

Ported from:
state_tests/stPreCompiledContracts2/CALLCODEEcrecover0Filler.json
"""

import pytest
from execution_testing import (
    EOA,
    Account,
    Address,
    Alloc,
    Bytes,
    Environment,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stPreCompiledContracts2/CALLCODEEcrecover0Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_callcode_ecrecover0(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_callcode_ecrecover0."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    contract_0 = Address(0x095E7BAEA6A6C7C4C2DFEB977EFAC326AF552D87)
    sender = EOA(
        key=0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    pre[sender] = Account(balance=0xDE0B6B3A7640000)
    # Source: lll
    # { (MSTORE 0 0x18c547e4f7b0f325ad1e56f57e26c745b09a3e503d86e00e5255ff7f715d3d1c) (MSTORE 32 28) (MSTORE 64 0x73b1693892219d736caba55bdb67216e485557ea6b6af75f37096c9aa6a5a75f) (MSTORE 96 0xeeb940b1d03b21e36b0e47e79769f095fe2ab855bd91e3a38756b7d75a9c4549) [[ 2 ]] (CALLCODE 300000 1 0 0 128 128 32) [[ 0 ]] (MOD (MLOAD 128) (EXP 2 160)) [[ 1 ]] (EQ (ORIGIN) (SLOAD 0))  }  # noqa: E501
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(
            offset=0x0,
            value=0x18C547E4F7B0F325AD1E56F57E26C745B09A3E503D86E00E5255FF7F715D3D1C,  # noqa: E501
        )
        + Op.MSTORE(offset=0x20, value=0x1C)
        + Op.MSTORE(
            offset=0x40,
            value=0x73B1693892219D736CABA55BDB67216E485557EA6B6AF75F37096C9AA6A5A75F,  # noqa: E501
        )
        + Op.MSTORE(
            offset=0x60,
            value=0xEEB940B1D03B21E36B0E47E79769F095FE2AB855BD91E3A38756B7D75A9C4549,  # noqa: E501
        )
        + Op.SSTORE(
            key=0x2,
            value=Op.CALLCODE(
                gas=0x493E0,
                address=0x1,
                value=0x0,
                args_offset=0x0,
                args_size=0x80,
                ret_offset=0x80,
                ret_size=0x20,
            ),
        )
        + Op.SSTORE(
            key=0x0, value=Op.MOD(Op.MLOAD(offset=0x80), Op.EXP(0x2, 0xA0))
        )
        + Op.SSTORE(key=0x1, value=Op.EQ(Op.ORIGIN, Op.SLOAD(key=0x0)))
        + Op.STOP,
        balance=0x1312D00,
        nonce=0,
        address=Address(0x095E7BAEA6A6C7C4C2DFEB977EFAC326AF552D87),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=Bytes(""),
        gas_limit=3652240,
        value=0x186A0,
    )

    post = {contract_0: Account(storage={0: sender, 1: 1, 2: 1})}

    state_test(env=env, pre=pre, post=post, tx=tx)
