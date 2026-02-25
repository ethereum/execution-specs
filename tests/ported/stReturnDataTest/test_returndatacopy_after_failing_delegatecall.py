"""
Ported from:
tests/static/state_tests/stReturnDataTest/returndatacopy_after_failing_delegatecallFiller.json

callee code:
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0x665521fd750490fd880ee369c267fca44ed8a078
    push2 0x2710
    delegatecall
    pop
    push1 0x20
    push1 0x00
    push1 0x00
    returndatacopy
    push1 0x00
    mload
    push1 0x00
    sstore
    stop

callee_1 code:
    revert
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Environment,
    Hash,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["tests/static/state_tests/stReturnDataTest/returndatacopy_after_failing_delegatecallFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_returndatacopy_after_failing_delegatecall(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xc102734f6a1e4747310179c0a0fc16e674aa901d")
    contract = Address("0x905c744acaf4d8f5436c9c5e91e0626d44add821")
    callee = Address("0x5242f2ad00427020024f504ae629e0576ca6a01a")
    callee_1 = Address("0x665521fd750490fd880ee369c267fca44ed8a078")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=111669149696,
    )

    pre[callee] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0x665521fd750490fd880ee369c267fca44ed8a078] + Op.PUSH2[0x2710]
        + Op.DELEGATECALL + Op.POP + Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.RETURNDATACOPY + Op.PUSH1[0x0] + Op.MLOAD + Op.PUSH1[0x0] + Op.SSTORE
        + Op.STOP
    ),
        storage={0x0: 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff},
    )
    pre[callee_1] = Account(balance=0x6400000000, nonce=0, code=Op.REVERT)
    pre[contract] = Account(balance=0x100000, nonce=0)
    pre[sender] = Account(balance=0x6400000000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x834185262e53584684bf2b72c64e510013c235d0f45e462db65900455df45a35"
        ),
        to=contract,
        data=b"",
        gas_limit=100000,
        gas_price=10,
        nonce=0,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
