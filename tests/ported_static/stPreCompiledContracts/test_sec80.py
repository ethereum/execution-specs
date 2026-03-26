"""
test_sec80

Ported from:
state_tests/stPreCompiledContracts/sec80Filler.json
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
    ["state_tests/stPreCompiledContracts/sec80Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_sec80(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """test_sec80"""
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
        gas_limit=100000000,
    )

    # Source: raw
    # 0x601b565b6000555b005b630badf00d6003565b63c001f00d6003565b7319e7e376e7c213b7e7e7e46cc70a5dd086daff2a7f22ae6da6b482f9b1b19b0b897c3fd43884180a1c5ee361e1107a1bc635649dda600052601b603f537f16433dce375ce6dc8151d3f0a22728bc4a1d9fd6ed39dfd18b4609331937367f6040527f306964c0cf5d74f04129fdc60b54d35b596dde1bf89ad92cb4123318f4c0e40060605260206080607f60006000600161fffff21560075760805114601257600956
    target = pre.deploy_contract(
        code=Op.JUMP(pc=0x1b) + Op.JUMPDEST + Op.PUSH1[0x0] + Op.SSTORE
        + Op.JUMPDEST + Op.STOP + Op.JUMPDEST + Op.PUSH4[0xbadf00d]
        + Op.JUMP(pc=0x3) + Op.JUMPDEST + Op.PUSH4[0xc001f00d] + Op.JUMP(pc=0x3)
        + Op.JUMPDEST + Op.PUSH20[0x19e7e376e7c213b7e7e7e46cc70a5dd086daff2a]
        + Op.MSTORE(offset=0x0, value=0x22ae6da6b482f9b1b19b0b897c3fd43884180a1c5ee361e1107a1bc635649dda)
        + Op.MSTORE8(offset=0x3f, value=0x1b)
        + Op.MSTORE(offset=0x40, value=0x16433dce375ce6dc8151d3f0a22728bc4a1d9fd6ed39dfd18b4609331937367f)
        + Op.MSTORE(offset=0x60, value=0x306964c0cf5d74f04129fdc60b54d35b596dde1bf89ad92cb4123318f4c0e400)
        + Op.JUMPI(pc=0x7, condition=Op.ISZERO(Op.CALLCODE(gas=0xffff, address=0x1, value=0x0, args_offset=0x0, args_size=0x7f, ret_offset=0x80, ret_size=0x20)))
        + Op.MLOAD(offset=0x80) + Op.JUMPI(pc=0x12, condition=Op.EQ)
        + Op.JUMP(pc=0x9),
        balance=0x1312d00,
        nonce=0,
        address=Address("0x39c2fbd2d4e46fa75775649472ddb79e836160b0"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000)


    tx = Transaction(
        sender=sender,
        to=target,
        data=b'',
        gas_limit=10000000,
        value=0x186a0,
        nonce=0,
        gas_price=10,
    )

    post = {target: Account(storage={0: 0xc001f00d})}

    state_test(env=env, pre=pre, post=post, tx=tx)
