"""
Test_returndatasize_after_failing_callcode.

Ported from:
state_tests/stReturnDataTest/returndatasize_after_failing_callcodeFiller.json
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
    [
        "state_tests/stReturnDataTest/returndatasize_after_failing_callcodeFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_returndatasize_after_failing_callcode(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_returndatasize_after_failing_callcode."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    addr = Address(0x285D0814904BEBB3B4ADD3B531A07647C2D08F59)
    sender = EOA(
        key=0x834185262E53584684BF2B72C64E510013C235D0F45E462DB65900455DF45A35
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=111669149696,
    )

    pre[addr] = Account(balance=0x10000000)
    # Source: lll
    # { (seq (CALLCODE 100000 <contract:0x1000000000000000000000000000000000000002> 0 0 0 0 0) (SSTORE 0 (RETURNDATASIZE)))}  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.POP(
            Op.CALLCODE(
                gas=0x186A0,
                address=0x665521FD750490FD880EE369C267FCA44ED8A078,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.SSTORE(key=0x0, value=Op.RETURNDATASIZE)
        + Op.STOP,
        storage={0: 0xFFFFFFFF},
        nonce=0,
        address=Address(0x716E4812F69C442687F8917638E10BBE6EB00592),  # noqa: E501
    )
    # Source: raw
    # 0xfd
    addr_2 = pre.deploy_contract(  # noqa: F841
        code=Op.REVERT,
        balance=0x6400000000,
        nonce=0,
        address=Address(0x665521FD750490FD880EE369C267FCA44ED8A078),  # noqa: E501
    )
    pre[sender] = Account(balance=0x6400000000)

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=200000,
    )

    post = {target: Account(storage={0: 0})}

    state_test(env=env, pre=pre, post=post, tx=tx)
