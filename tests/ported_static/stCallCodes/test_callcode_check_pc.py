"""
Check the PC after doing call to a contract.

Ported from:
state_tests/stCallCodes/callcode_checkPCFiller.json
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
    ["state_tests/stCallCodes/callcode_checkPCFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_callcode_check_pc(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Check the PC after doing call to a contract."""
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
        gas_limit=3000000000,
    )

    # Source: lll
    # { (CALL 1000000 <contract:0x1000000000000000000000000000000000000001> 0 0 64 0 64 ) [[3]] (PC) }  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.POP(
            Op.CALL(
                gas=0xF4240,
                address=0xFA7FC61138EE12431F8693335FB2BF5AF4051632,
                value=0x0,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x40,
            )
        )
        + Op.SSTORE(key=0x3, value=Op.PC)
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address(0x6861B8D2BA9A24E77F63623E4A5E83E2BC6A30DF),  # noqa: E501
    )
    # Source: lll
    # { [[0]] 1 }
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x1) + Op.STOP,
        balance=0x2540BE400,
        nonce=0,
        address=Address(0xFA7FC61138EE12431F8693335FB2BF5AF4051632),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=1100000,
    )

    post = {target: Account(storage={3: 37})}

    state_test(env=env, pre=pre, post=post, tx=tx)
