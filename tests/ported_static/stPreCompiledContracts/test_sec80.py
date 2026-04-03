"""
Test_sec80.

Ported from:
state_tests/stPreCompiledContracts/sec80Filler.json
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
    ["state_tests/stPreCompiledContracts/sec80Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_sec80(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_sec80."""
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
        gas_limit=100000000,
    )

    # Source: raw
    # 0x601b565b6000555b005b630badf00d6003565b63c001f00d6003565b7319e7e376e7c213b7e7e7e46cc70a5dd086daff2a7f22ae6da6b482f9b1b19b0b897c3fd43884180a1c5ee361e1107a1bc635649dda600052601b603f537f16433dce375ce6dc8151d3f0a22728bc4a1d9fd6ed39dfd18b4609331937367f6040527f306964c0cf5d74f04129fdc60b54d35b596dde1bf89ad92cb4123318f4c0e40060605260206080607f60006000600161fffff21560075760805114601257600956  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.JUMP(pc=0x1B)
        + Op.JUMPDEST
        + Op.PUSH1[0x0]
        + Op.SSTORE
        + Op.JUMPDEST
        + Op.STOP
        + Op.JUMPDEST
        + Op.PUSH4[0xBADF00D]
        + Op.JUMP(pc=0x3)
        + Op.JUMPDEST
        + Op.PUSH4[0xC001F00D]
        + Op.JUMP(pc=0x3)
        + Op.JUMPDEST
        + Op.PUSH20[0x19E7E376E7C213B7E7E7E46CC70A5DD086DAFF2A]
        + Op.MSTORE(
            offset=0x0,
            value=0x22AE6DA6B482F9B1B19B0B897C3FD43884180A1C5EE361E1107A1BC635649DDA,  # noqa: E501
        )
        + Op.MSTORE8(offset=0x3F, value=0x1B)
        + Op.MSTORE(
            offset=0x40,
            value=0x16433DCE375CE6DC8151D3F0A22728BC4A1D9FD6ED39DFD18B4609331937367F,  # noqa: E501
        )
        + Op.MSTORE(
            offset=0x60,
            value=0x306964C0CF5D74F04129FDC60B54D35B596DDE1BF89AD92CB4123318F4C0E400,  # noqa: E501
        )
        + Op.JUMPI(
            pc=0x7,
            condition=Op.ISZERO(
                Op.CALLCODE(
                    gas=0xFFFF,
                    address=0x1,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x7F,
                    ret_offset=0x80,
                    ret_size=0x20,
                )
            ),
        )
        + Op.MLOAD(offset=0x80)
        + Op.JUMPI(pc=0x12, condition=Op.EQ)
        + Op.JUMP(pc=0x9),
        balance=0x1312D00,
        nonce=0,
        address=Address(0x39C2FBD2D4E46FA75775649472DDB79E836160B0),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=10000000,
        value=0x186A0,
    )

    post = {target: Account(storage={0: 0xC001F00D})}

    state_test(env=env, pre=pre, post=post, tx=tx)
