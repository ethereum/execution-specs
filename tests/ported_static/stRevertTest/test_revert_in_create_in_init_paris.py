"""
Test_revert_in_create_in_init_paris.

Ported from:
state_tests/stRevertTest/RevertInCreateInInit_ParisFiller.json
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
    ["state_tests/stRevertTest/RevertInCreateInInit_ParisFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_revert_in_create_in_init_paris(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_revert_in_create_in_init_paris."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    addr = Address(0x4757608F18B70777AE788DD4056EEED52F7AA68F)
    sender = EOA(
        key=0x834185262E53584684BF2B72C64E510013C235D0F45E462DB65900455DF45A35
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
    )

    pre[addr] = Account(balance=10, storage={0: 1})
    pre[sender] = Account(balance=0x6400000000)

    tx = Transaction(
        sender=sender,
        to=None,
        data=Op.POP(Op.ADDRESS)
        + Op.PUSH1[0xD]
        + Op.CODECOPY(dest_offset=0x0, offset=0x24, size=Op.DUP1)
        + Op.PUSH1[0x0] * 2
        + Op.POP(Op.CREATE)
        + Op.SSTORE(key=0x0, value=Op.RETURNDATASIZE)
        + Op.RETURNDATACOPY(dest_offset=0x0, offset=0x0, size=0x20)
        + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x0))
        + Op.STOP * 2
        + Op.INVALID
        + Op.MSTORE(offset=0x0, value=0x112233)
        + Op.REVERT(offset=0x0, size=0x20)
        + Op.STOP,
        gas_limit=200000,
    )

    post = {addr: Account(storage={0: 1}, balance=10)}

    state_test(env=env, pre=pre, post=post, tx=tx)
