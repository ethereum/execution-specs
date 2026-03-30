"""
Test_call_ecrecover3.

Ported from:
state_tests/stPreCompiledContracts2/CallEcrecover3Filler.json
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
    ["state_tests/stPreCompiledContracts2/CallEcrecover3Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_call_ecrecover3(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_call_ecrecover3."""
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
    # { (MSTORE 0 0x2f380a2dea7e778d81affc2443403b8fe4644db442ae4862ff5bb3732829cdb9) (MSTORE 32 27) (MSTORE 64 0x6b65ccb0558806e9b097f27a396d08f964e37b8b7af6ceeb516ff86739fbea0a) (MSTORE 96 0x37cbc8d883e129a4b1ef9d5f1df53c4f21a3ef147cf2a50a4ede0eb06ce092d4) [[ 2 ]] (CALL 100000 1 0 0 128 128 32) [[ 0 ]] (MOD (MLOAD 128) (EXP 2 160)) [[ 1 ]] (EQ (ORIGIN) (SLOAD 0))  }  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(
            offset=0x0,
            value=0x2F380A2DEA7E778D81AFFC2443403B8FE4644DB442AE4862FF5BB3732829CDB9,  # noqa: E501
        )
        + Op.MSTORE(offset=0x20, value=0x1B)
        + Op.MSTORE(
            offset=0x40,
            value=0x6B65CCB0558806E9B097F27A396D08F964E37B8B7AF6CEEB516FF86739FBEA0A,  # noqa: E501
        )
        + Op.MSTORE(
            offset=0x60,
            value=0x37CBC8D883E129A4B1EF9D5F1DF53C4F21A3EF147CF2A50A4EDE0EB06CE092D4,  # noqa: E501
        )
        + Op.SSTORE(
            key=0x2,
            value=Op.CALL(
                gas=0x186A0,
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
        address=Address(0x28D98D7CC227972A80FA4A16964272BF8738D792),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=365224,
        value=0x186A0,
    )

    post = {
        target: Account(
            storage={
                0: 0xE4319F4B631C6D0FCFC84045DBCB676865FE5E13,
                2: 1,
            },
        ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
