"""
Returndatacopy after failing create case due to 0xfd code.

Ported from:
state_tests/stReturnDataTest/returndatacopy_afterFailing_createFiller.json
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
        "state_tests/stReturnDataTest/returndatacopy_afterFailing_createFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_returndatacopy_after_failing_create(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Returndatacopy after failing create case due to 0xfd code."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
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

    # Source: lll
    # { (MSTORE 0 0x600260005260206000fd) (create 0 22 10) (SSTORE 0 (RETURNDATASIZE)) (RETURNDATACOPY 0 0 32) (SSTORE 1 (MLOAD 0)) }  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x0, value=0x600260005260206000FD)
        + Op.POP(Op.CREATE(value=0x0, offset=0x16, size=0xA))
        + Op.SSTORE(key=0x0, value=Op.RETURNDATASIZE)
        + Op.RETURNDATACOPY(dest_offset=0x0, offset=0x0, size=0x20)
        + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x0))
        + Op.STOP,
        storage={0: 1},
        nonce=0,
        address=Address(0x1F2642DD423C1BAC7E318EE8DF07608C3216D725),  # noqa: E501
    )
    pre[sender] = Account(balance=0x6400000000)

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=100000,
    )

    post = {target: Account(storage={0: 32, 1: 2})}

    state_test(env=env, pre=pre, post=post, tx=tx)
