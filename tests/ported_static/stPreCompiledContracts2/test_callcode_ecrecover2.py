"""
Test_callcode_ecrecover2.

Ported from:
state_tests/stPreCompiledContracts2/CALLCODEEcrecover2Filler.json
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
    ["state_tests/stPreCompiledContracts2/CALLCODEEcrecover2Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_callcode_ecrecover2(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_callcode_ecrecover2."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = EOA(
        key=0xE04D1AC7DDDA0C98397D56A0B501E960D4CD325A39286919AC23C1A07009A869
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    # Source: lll
    # { (MSTORE 0 0x18c547e4f7b0f325ad1e56f57e26c745b09a3e503d86e00e5255ff7f715d3d1c) (MSTORE 32 28) (MSTORE 33 0x73b1693892219d736caba55bdb67216e485557ea6b6af75f37096c9aa6a5a75f) (MSTORE 65 0xeeb940b1d03b21e36b0e47e79769f095fe2ab855bd91e3a38756b7d75a9c4549) [[ 2 ]] (CALLCODE 100000 1 0 0 97 97 32) [[ 0 ]] (MOD (MLOAD 97) (EXP 2 160)) [[ 1 ]] (EQ (ORIGIN) (SLOAD 0))  }  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(
            offset=0x0,
            value=0x18C547E4F7B0F325AD1E56F57E26C745B09A3E503D86E00E5255FF7F715D3D1C,  # noqa: E501
        )
        + Op.MSTORE(offset=0x20, value=0x1C)
        + Op.MSTORE(
            offset=0x21,
            value=0x73B1693892219D736CABA55BDB67216E485557EA6B6AF75F37096C9AA6A5A75F,  # noqa: E501
        )
        + Op.MSTORE(
            offset=0x41,
            value=0xEEB940B1D03B21E36B0E47E79769F095FE2AB855BD91E3A38756B7D75A9C4549,  # noqa: E501
        )
        + Op.SSTORE(
            key=0x2,
            value=Op.CALLCODE(
                gas=0x186A0,
                address=0x1,
                value=0x0,
                args_offset=0x0,
                args_size=0x61,
                ret_offset=0x61,
                ret_size=0x20,
            ),
        )
        + Op.SSTORE(
            key=0x0, value=Op.MOD(Op.MLOAD(offset=0x61), Op.EXP(0x2, 0xA0))
        )
        + Op.SSTORE(key=0x1, value=Op.EQ(Op.ORIGIN, Op.SLOAD(key=0x0)))
        + Op.STOP,
        balance=0x1312D00,
        nonce=0,
        address=Address(0x82FED9E1D9833BFED4D0DFAB03D1E35DBFFA4243),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=365224,
        value=0x186A0,
    )

    post = {target: Account(storage={2: 1})}

    state_test(env=env, pre=pre, post=post, tx=tx)
