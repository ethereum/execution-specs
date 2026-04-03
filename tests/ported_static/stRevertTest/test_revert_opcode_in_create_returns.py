"""
Test_revert_opcode_in_create_returns.

Ported from:
state_tests/stRevertTest/RevertOpcodeInCreateReturnsFiller.json
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
    ["state_tests/stRevertTest/RevertOpcodeInCreateReturnsFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_revert_opcode_in_create_returns(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_revert_opcode_in_create_returns."""
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
        gas_limit=42949672960,
    )

    # Source: lll
    # { (seq (CREATE 0 0 (lll (seq (mstore 0 0x112233) (revert 0 32)) 0)) (SSTORE 0 (RETURNDATASIZE)) (STOP) )}  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.PUSH1[0xD]
        + Op.CODECOPY(dest_offset=0x0, offset=0x15, size=Op.DUP1)
        + Op.PUSH1[0x0] * 2
        + Op.POP(Op.CREATE)
        + Op.SSTORE(key=0x0, value=Op.RETURNDATASIZE)
        + Op.STOP * 2
        + Op.INVALID
        + Op.MSTORE(offset=0x0, value=0x112233)
        + Op.REVERT(offset=0x0, size=0x20)
        + Op.STOP,
        storage={0: 1},
        nonce=0,
        address=Address(0x910073CEED5C2372DC67FFD941B0F148DC4EBAF5),  # noqa: E501
    )
    pre[sender] = Account(balance=0x6400000000)

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=100000,
    )

    post = {target: Account(storage={0: 32})}

    state_test(env=env, pre=pre, post=post, tx=tx)
