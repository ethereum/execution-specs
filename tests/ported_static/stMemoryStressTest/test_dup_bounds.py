"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stMemoryStressTest/DUP_BoundsFiller.json
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
    ["tests/static/state_tests/stMemoryStressTest/DUP_BoundsFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        150000,
        1000000,
        16777216,
    ],
    ids=["case0", "case1", "case2"],
)
@pytest.mark.pre_alloc_mutable
def test_dup_bounds(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x31B5AF02B012484AE954B3A43943242EDE546A2E76FC0A6ACC17435107C385EB
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
            Op.PUSH1[0x0]
            + Op.POP(Op.DUP1)
            + Op.POP
            + Op.PUSH4[0xFFFFFFFF]
            + Op.POP(Op.DUP1)
            + Op.POP
            + Op.PUSH8[0xFFFFFFFFFFFFFFFF]
            + Op.POP(Op.DUP1)
            + Op.POP
            + Op.PUSH16[0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF]
            + Op.POP(Op.DUP1)
            + Op.POP
            + Op.PUSH32[
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF  # noqa: E501
            ]
            + Op.POP(Op.DUP1)
            + Op.POP
            + Op.PUSH1[0x0]
            + Op.PUSH1[0x0]
            + Op.POP(Op.DUP2)
            + Op.POP
            + Op.POP
            + Op.PUSH4[0xFFFFFFFF]
            + Op.PUSH4[0xFFFFFFFF]
            + Op.POP(Op.DUP2)
            + Op.POP
            + Op.POP
            + Op.PUSH8[0xFFFFFFFFFFFFFFFF]
            + Op.PUSH8[0xFFFFFFFFFFFFFFFF]
            + Op.POP(Op.DUP2)
            + Op.POP
            + Op.POP
            + Op.PUSH16[0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF]
            + Op.PUSH16[0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF]
            + Op.POP(Op.DUP2)
            + Op.POP
            + Op.POP
            + Op.PUSH32[
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF  # noqa: E501
            ]
            + Op.PUSH32[
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF  # noqa: E501
            ]
            + Op.POP(Op.DUP2)
            + Op.POP
            + Op.POP
            + Op.PUSH1[0x0]
            + Op.PUSH1[0x0]
            + Op.PUSH1[0x0]
            + Op.POP(Op.DUP3)
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.PUSH4[0xFFFFFFFF]
            + Op.PUSH4[0xFFFFFFFF]
            + Op.PUSH4[0xFFFFFFFF]
            + Op.POP(Op.DUP3)
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.PUSH8[0xFFFFFFFFFFFFFFFF]
            + Op.PUSH8[0xFFFFFFFFFFFFFFFF]
            + Op.PUSH8[0xFFFFFFFFFFFFFFFF]
            + Op.POP(Op.DUP3)
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.PUSH16[0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF]
            + Op.PUSH16[0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF]
            + Op.PUSH16[0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF]
            + Op.POP(Op.DUP3)
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.PUSH32[
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF  # noqa: E501
            ]
            + Op.PUSH32[
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF  # noqa: E501
            ]
            + Op.PUSH32[
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF  # noqa: E501
            ]
            + Op.POP(Op.DUP3)
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.PUSH1[0x0]
            + Op.PUSH1[0x0]
            + Op.PUSH1[0x0]
            + Op.PUSH1[0x0]
            + Op.POP(Op.DUP4)
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.PUSH4[0xFFFFFFFF]
            + Op.PUSH4[0xFFFFFFFF]
            + Op.PUSH4[0xFFFFFFFF]
            + Op.PUSH4[0xFFFFFFFF]
            + Op.POP(Op.DUP4)
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.PUSH8[0xFFFFFFFFFFFFFFFF]
            + Op.PUSH8[0xFFFFFFFFFFFFFFFF]
            + Op.PUSH8[0xFFFFFFFFFFFFFFFF]
            + Op.PUSH8[0xFFFFFFFFFFFFFFFF]
            + Op.POP(Op.DUP4)
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.PUSH16[0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF]
            + Op.PUSH16[0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF]
            + Op.PUSH16[0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF]
            + Op.PUSH16[0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF]
            + Op.POP(Op.DUP4)
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.PUSH32[
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF  # noqa: E501
            ]
            + Op.PUSH32[
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF  # noqa: E501
            ]
            + Op.PUSH32[
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF  # noqa: E501
            ]
            + Op.PUSH32[
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF  # noqa: E501
            ]
            + Op.POP(Op.DUP4)
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.PUSH1[0x0]
            + Op.PUSH1[0x0]
            + Op.PUSH1[0x0]
            + Op.PUSH1[0x0]
            + Op.PUSH1[0x0]
            + Op.POP(Op.DUP5)
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.PUSH4[0xFFFFFFFF]
            + Op.PUSH4[0xFFFFFFFF]
            + Op.PUSH4[0xFFFFFFFF]
            + Op.PUSH4[0xFFFFFFFF]
            + Op.PUSH4[0xFFFFFFFF]
            + Op.POP(Op.DUP5)
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.PUSH8[0xFFFFFFFFFFFFFFFF]
            + Op.PUSH8[0xFFFFFFFFFFFFFFFF]
            + Op.PUSH8[0xFFFFFFFFFFFFFFFF]
            + Op.PUSH8[0xFFFFFFFFFFFFFFFF]
            + Op.PUSH8[0xFFFFFFFFFFFFFFFF]
            + Op.POP(Op.DUP5)
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.PUSH16[0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF]
            + Op.PUSH16[0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF]
            + Op.PUSH16[0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF]
            + Op.PUSH16[0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF]
            + Op.PUSH16[0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF]
            + Op.POP(Op.DUP5)
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.PUSH32[
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF  # noqa: E501
            ]
            + Op.PUSH32[
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF  # noqa: E501
            ]
            + Op.PUSH32[
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF  # noqa: E501
            ]
            + Op.PUSH32[
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF  # noqa: E501
            ]
            + Op.PUSH32[
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF  # noqa: E501
            ]
            + Op.POP(Op.DUP5)
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.PUSH1[0x0]
            + Op.PUSH1[0x0]
            + Op.PUSH1[0x0]
            + Op.PUSH1[0x0]
            + Op.PUSH1[0x0]
            + Op.PUSH1[0x0]
            + Op.POP(Op.DUP6)
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.PUSH4[0xFFFFFFFF]
            + Op.PUSH4[0xFFFFFFFF]
            + Op.PUSH4[0xFFFFFFFF]
            + Op.PUSH4[0xFFFFFFFF]
            + Op.PUSH4[0xFFFFFFFF]
            + Op.PUSH4[0xFFFFFFFF]
            + Op.POP(Op.DUP6)
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.PUSH8[0xFFFFFFFFFFFFFFFF]
            + Op.PUSH8[0xFFFFFFFFFFFFFFFF]
            + Op.PUSH8[0xFFFFFFFFFFFFFFFF]
            + Op.PUSH8[0xFFFFFFFFFFFFFFFF]
            + Op.PUSH8[0xFFFFFFFFFFFFFFFF]
            + Op.PUSH8[0xFFFFFFFFFFFFFFFF]
            + Op.POP(Op.DUP6)
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.PUSH16[0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF]
            + Op.PUSH16[0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF]
            + Op.PUSH16[0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF]
            + Op.PUSH16[0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF]
            + Op.PUSH16[0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF]
            + Op.PUSH16[0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF]
            + Op.POP(Op.DUP6)
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.PUSH32[
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF  # noqa: E501
            ]
            + Op.PUSH32[
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF  # noqa: E501
            ]
            + Op.PUSH32[
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF  # noqa: E501
            ]
            + Op.PUSH32[
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF  # noqa: E501
            ]
            + Op.PUSH32[
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF  # noqa: E501
            ]
            + Op.PUSH32[
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF  # noqa: E501
            ]
            + Op.POP(Op.DUP6)
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.PUSH1[0x0]
            + Op.PUSH1[0x0]
            + Op.PUSH1[0x0]
            + Op.PUSH1[0x0]
            + Op.PUSH1[0x0]
            + Op.PUSH1[0x0]
            + Op.PUSH1[0x0]
            + Op.POP(Op.DUP7)
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.PUSH4[0xFFFFFFFF]
            + Op.PUSH4[0xFFFFFFFF]
            + Op.PUSH4[0xFFFFFFFF]
            + Op.PUSH4[0xFFFFFFFF]
            + Op.PUSH4[0xFFFFFFFF]
            + Op.PUSH4[0xFFFFFFFF]
            + Op.PUSH4[0xFFFFFFFF]
            + Op.POP(Op.DUP7)
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.PUSH8[0xFFFFFFFFFFFFFFFF]
            + Op.PUSH8[0xFFFFFFFFFFFFFFFF]
            + Op.PUSH8[0xFFFFFFFFFFFFFFFF]
            + Op.PUSH8[0xFFFFFFFFFFFFFFFF]
            + Op.PUSH8[0xFFFFFFFFFFFFFFFF]
            + Op.PUSH8[0xFFFFFFFFFFFFFFFF]
            + Op.PUSH8[0xFFFFFFFFFFFFFFFF]
            + Op.POP(Op.DUP7)
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.PUSH16[0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF]
            + Op.PUSH16[0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF]
            + Op.PUSH16[0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF]
            + Op.PUSH16[0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF]
            + Op.PUSH16[0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF]
            + Op.PUSH16[0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF]
            + Op.PUSH16[0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF]
            + Op.POP(Op.DUP7)
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.PUSH32[
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF  # noqa: E501
            ]
            + Op.PUSH32[
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF  # noqa: E501
            ]
            + Op.PUSH32[
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF  # noqa: E501
            ]
            + Op.PUSH32[
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF  # noqa: E501
            ]
            + Op.PUSH32[
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF  # noqa: E501
            ]
            + Op.PUSH32[
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF  # noqa: E501
            ]
            + Op.PUSH32[
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF  # noqa: E501
            ]
            + Op.POP(Op.DUP7)
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.PUSH1[0x0]
            + Op.PUSH1[0x0]
            + Op.PUSH1[0x0]
            + Op.PUSH1[0x0]
            + Op.PUSH1[0x0]
            + Op.PUSH1[0x0]
            + Op.PUSH1[0x0]
            + Op.PUSH1[0x0]
            + Op.POP(Op.DUP8)
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.PUSH4[0xFFFFFFFF]
            + Op.PUSH4[0xFFFFFFFF]
            + Op.PUSH4[0xFFFFFFFF]
            + Op.PUSH4[0xFFFFFFFF]
            + Op.PUSH4[0xFFFFFFFF]
            + Op.PUSH4[0xFFFFFFFF]
            + Op.PUSH4[0xFFFFFFFF]
            + Op.PUSH4[0xFFFFFFFF]
            + Op.POP(Op.DUP8)
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.PUSH8[0xFFFFFFFFFFFFFFFF]
            + Op.PUSH8[0xFFFFFFFFFFFFFFFF]
            + Op.PUSH8[0xFFFFFFFFFFFFFFFF]
            + Op.PUSH8[0xFFFFFFFFFFFFFFFF]
            + Op.PUSH8[0xFFFFFFFFFFFFFFFF]
            + Op.PUSH8[0xFFFFFFFFFFFFFFFF]
            + Op.PUSH8[0xFFFFFFFFFFFFFFFF]
            + Op.PUSH8[0xFFFFFFFFFFFFFFFF]
            + Op.POP(Op.DUP8)
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.PUSH16[0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF]
            + Op.PUSH16[0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF]
            + Op.PUSH16[0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF]
            + Op.PUSH16[0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF]
            + Op.PUSH16[0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF]
            + Op.PUSH16[0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF]
            + Op.PUSH16[0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF]
            + Op.PUSH16[0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF]
            + Op.POP(Op.DUP8)
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.POP
            + Op.PUSH32[
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF  # noqa: E501
            ]
            + Op.PUSH32[
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF  # noqa: E501
            ]
            + Op.PUSH32[
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF  # noqa: E501
            ]
            + Op.PUSH32[
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF  # noqa: E501
            ]
            + Op.PUSH32[
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF  # noqa: E501
            ]
            + Op.PUSH32[
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF  # noqa: E501
            ]
            + Op.PUSH32[
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF  # noqa: E501
            ]
            + Op.PUSH32[
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF  # noqa: E501
            ]
            + Op.DUP8
        ),
        nonce=0,
        address=Address("0xe860bd7bf0474923e526cbe86fa5b5f76aee36ed"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x7FFFFFFFFFFFFFFF)

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=tx_gas_limit,
        value=1,
    )

    post: dict = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
