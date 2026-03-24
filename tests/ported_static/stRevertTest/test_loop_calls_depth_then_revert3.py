"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stRevertTest/LoopCallsDepthThenRevert3Filler.json
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
    [
        "tests/static/state_tests/stRevertTest/LoopCallsDepthThenRevert3Filler.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Prague")
@pytest.mark.pre_alloc_mutable
def test_loop_calls_depth_then_revert3(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=9223372036854775807,
    )

    # Source: raw bytecode
    contract = pre.deploy_contract(
        code=(
            Op.JUMPI(pc=0x3F, condition=Op.EQ(Op.SLOAD(key=0x0), 0x3FE))
            + Op.SSTORE(key=0x0, value=Op.ADD(Op.SLOAD(key=0x0), 0x1))
            + Op.POP(
                Op.CALL(
                    gas=Op.GAS,
                    address=0xA000000000000000000000000000000000000000,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.JUMPI(pc=0x53, condition=Op.LT(Op.SLOAD(key=0x0), 0x41A))
            + Op.JUMPDEST
            + Op.MSTORE(offset=0x0, value=0x600060006002F0)
            + Op.POP(Op.CREATE(value=0x3, offset=0x19, size=0x7))
            + Op.JUMPDEST
        ),
        balance=10,
        nonce=0,
        address=Address("0xa000000000000000000000000000000000000000"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x13426172C74D822B878FE800000000)

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=9214364837600034817,
    )

    post = {
        contract: Account(storage={0: 1022}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
