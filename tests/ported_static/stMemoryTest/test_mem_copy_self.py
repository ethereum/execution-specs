"""
Ori Pomerantz qbzzt1@gmail.com.

Ported from:
state_tests/stMemoryTest/memCopySelfFiller.yml
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
    ["state_tests/stMemoryTest/memCopySelfFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_mem_copy_self(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Ori Pomerantz qbzzt1@gmail."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = EOA(
        key=0x48DC5A9F099CAAAA557742CA3A990A94BE45B9969126A1BC74E5E8BE5A2B5B47
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[sender] = Account(balance=0xBA1A9CE0BA1A9CE, nonce=1)
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
    target = pre.deploy_contract(  # noqa: F841
        code=Op.PUSH1[0x4]
        + Op.PUSH1[0x0]
        + Op.JUMPDEST
        + Op.JUMPI(pc=0x30, condition=Op.LT(Op.DUP2, 0xF))
        + Op.PUSH1[0xA]
        + Op.PUSH1[0x2]
        + Op.DUP2
        + Op.PUSH1[0x0]
        + Op.DUP1
        + Op.DUP7
        + Op.SSTORE(key=Op.DUP3, value=Op.MLOAD(offset=Op.DUP2))
        + Op.GAS
        + Op.POP(Op.CALL)
        + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x0))
        + Op.RETURNDATACOPY(dest_offset=0x20, offset=0x0, size=0xA)
        + Op.SSTORE(key=0x2, value=Op.MLOAD(offset=0x20))
        + Op.STOP
        + Op.JUMPDEST
        + Op.DUP1
        + Op.PUSH1[0x11]
        + Op.PUSH1[0x1]
        + Op.DUP1
        + Op.SWAP4
        + Op.ADD
        + Op.MSTORE8(offset=Op.DUP2, value=Op.MUL)
        + Op.ADD
        + Op.JUMP(pc=0x4),
        storage={0: 24743},
        balance=0xBA1A9CE0BA1A9CE,
        nonce=1,
        address=Address(0xB595300AC049B84C5277C7CA68A96D74AE377B85),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=16777216,
        nonce=1,
    )

    post = {
        target: Account(
            storage={
                0: 0x112233445566778899AABBCCDDEEFF0000000000000000000000000000000000,  # noqa: E501
                1: 0x1122112233445566778899AADDEEFF0000000000000000000000000000000000,  # noqa: E501
                2: 0x112233445566778899AA00000000000000000000000000000000000000000000,  # noqa: E501
            },
        ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
