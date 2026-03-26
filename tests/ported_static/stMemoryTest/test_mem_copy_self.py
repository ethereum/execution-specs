"""
Ori Pomerantz qbzzt1@gmail.com

Ported from:
state_tests/stMemoryTest/memCopySelfFiller.yml
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
    ["state_tests/stMemoryTest/memCopySelfFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_mem_copy_self(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Ori Pomerantz qbzzt1@gmail."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x48dc5a9f099caaaa557742ca3a990a94be45b9969126a1bc74e5e8be5a2b5b47
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

    # Source: yul
    # berlin
    # {
    #    let idPrecomp := 0x04
    # 
    #    for { let i := 0} lt(i, 0x0F) { i := add(i, 1) } 
    #    {
    #        mstore8(i, mul(add(i, 1), 0x11)) 
    #    }
    #     
    #    // The initial memory value
    #    sstore(0, mload(0))
    #    
    #    // Call idPrecomp
    #    pop(call(gas(), idPrecomp, 0, 
    #      0, 10,     // input buffer
    #      2, 10      // output buffer (overlapping the input)
    #    ))
    # 
    #    // Memory value immediately after the call
    #    sstore(1, mload(0))
    # 
    #    // Copy the return data (to check if it is corrupt)
    #    returndatacopy(0x20, 0, 10)
    #    sstore(2, mload(0x20))
    # }
    target = pre.deploy_contract(
        code=Op.PUSH1[0x4] + Op.PUSH1[0x0] + Op.JUMPDEST
        + Op.JUMPI(pc=0x30, condition=Op.LT(Op.DUP2, 0xf)) + Op.PUSH1[0xa]
        + Op.PUSH1[0x2] + Op.DUP2 + Op.PUSH1[0x0] + Op.DUP1 + Op.DUP7
        + Op.SSTORE(key=Op.DUP3, value=Op.MLOAD(offset=Op.DUP2)) + Op.GAS
        + Op.POP(Op.CALL) + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x0))
        + Op.RETURNDATACOPY(dest_offset=0x20, offset=0x0, size=0xa)
        + Op.SSTORE(key=0x2, value=Op.MLOAD(offset=0x20)) + Op.STOP + Op.JUMPDEST  # noqa: E501
        + Op.DUP1 + Op.PUSH1[0x11] + Op.PUSH1[0x1] + Op.DUP1 + Op.SWAP4 + Op.ADD
        + Op.MSTORE8(offset=Op.DUP2, value=Op.MUL) + Op.ADD + Op.JUMP(pc=0x4),
        storage={0: 24743},
        balance=0xba1a9ce0ba1a9ce,
        nonce=1,
        address=Address("0xb595300ac049b84c5277c7ca68a96d74ae377b85"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xba1a9ce0ba1a9ce, nonce=1)


    tx = Transaction(
        sender=sender,
        to=target,
        data=b'',
        gas_limit=16777216,
        nonce=1,
        gas_price=10,
    )

    post = {
        target: Account(
                storage={
            0: 0x112233445566778899aabbccddeeff0000000000000000000000000000000000,
            1: 0x1122112233445566778899aaddeeff0000000000000000000000000000000000,
            2: 0x112233445566778899aa00000000000000000000000000000000000000000000,
        },
            ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
