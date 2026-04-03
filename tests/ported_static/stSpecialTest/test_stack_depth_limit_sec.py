"""
Test_stack_depth_limit_sec.

Ported from:
state_tests/stSpecialTest/StackDepthLimitSECFiller.json
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
    compute_create_address,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stSpecialTest/StackDepthLimitSECFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_stack_depth_limit_sec(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_stack_depth_limit_sec."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = EOA(
        key=0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000,
    )

    pre[sender] = Account(balance=0x2540BE400)

    tx = Transaction(
        sender=sender,
        to=None,
        data=Op.POP(Op.ADDRESS)
        + Op.POP(Op.ORIGIN)
        + Op.POP(Op.CALLER)
        + Op.CODECOPY(dest_offset=0x0, offset=0x0, size=0x4)
        + Op.POP(Op.MLOAD(offset=0x0))
        + Op.CALLDATACOPY(dest_offset=0x0, offset=0x0, size=0x4)
        + Op.POP(Op.MLOAD(offset=0x0))
        + Op.MSTORE(offset=0x0, value=0x600060006000600060003060405A03F1)
        + Op.RETURN(offset=0x10, size=0x10),
        gas_limit=1000000,
        value=10,
    )

    post = {
        compute_create_address(address=sender, nonce=0): Account(
            code=bytes.fromhex("600060006000600060003060405a03f1"),
            balance=10,
        ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
