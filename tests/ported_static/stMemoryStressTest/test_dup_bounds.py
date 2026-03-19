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
from execution_testing.forks import Fork
from execution_testing.specs.static_state.expect_section import (
    resolve_expect_post,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

TX_DATA = [
    "",
    "",
    "",
]

TX_GAS = [150000, 1000000, 16777216]

TX_VALUE = [1]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d]) if TX_DATA[d] else b""


@pytest.mark.ported_from(
    ["tests/static/state_tests/stMemoryStressTest/DUP_BoundsFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(0, 0, 0, id="case0"),
        pytest.param(1, 1, 0, id="case1"),
        pytest.param(2, 2, 0, id="case2"),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_dup_bounds(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
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

    EXPECT_ENTRIES: list[dict] = [
        {
            "indexes": {"data": 0, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    code=bytes.fromhex(
                        "600080505063ffffffff80505067ffffffffffffffff8050506fffffffffffffffffffffffffffffffff8050507fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff805050600060008150505063ffffffff63ffffffff8150505067ffffffffffffffff67ffffffffffffffff815050506fffffffffffffffffffffffffffffffff6fffffffffffffffffffffffffffffffff815050507fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff81505050600060006000825050505063ffffffff63ffffffff63ffffffff825050505067ffffffffffffffff67ffffffffffffffff67ffffffffffffffff82505050506fffffffffffffffffffffffffffffffff6fffffffffffffffffffffffffffffffff6fffffffffffffffffffffffffffffffff82505050507fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff8250505050600060006000600083505050505063ffffffff63ffffffff63ffffffff63ffffffff83505050505067ffffffffffffffff67ffffffffffffffff67ffffffffffffffff67ffffffffffffffff8350505050506fffffffffffffffffffffffffffffffff6fffffffffffffffffffffffffffffffff6fffffffffffffffffffffffffffffffff6fffffffffffffffffffffffffffffffff8350505050507fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff835050505050600060006000600060008450505050505063ffffffff63ffffffff63ffffffff63ffffffff63ffffffff8450505050505067ffffffffffffffff67ffffffffffffffff67ffffffffffffffff67ffffffffffffffff67ffffffffffffffff845050505050506fffffffffffffffffffffffffffffffff6fffffffffffffffffffffffffffffffff6fffffffffffffffffffffffffffffffff6fffffffffffffffffffffffffffffffff6fffffffffffffffffffffffffffffffff845050505050507fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff84505050505050600060006000600060006000855050505050505063ffffffff63ffffffff63ffffffff63ffffffff63ffffffff63ffffffff855050505050505067ffffffffffffffff67ffffffffffffffff67ffffffffffffffff67ffffffffffffffff67ffffffffffffffff67ffffffffffffffff85505050505050506fffffffffffffffffffffffffffffffff6fffffffffffffffffffffffffffffffff6fffffffffffffffffffffffffffffffff6fffffffffffffffffffffffffffffffff6fffffffffffffffffffffffffffffffff6fffffffffffffffffffffffffffffffff85505050505050507fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff8550505050505050600060006000600060006000600086505050505050505063ffffffff63ffffffff63ffffffff63ffffffff63ffffffff63ffffffff63ffffffff86505050505050505067ffffffffffffffff67ffffffffffffffff67ffffffffffffffff67ffffffffffffffff67ffffffffffffffff67ffffffffffffffff67ffffffffffffffff8650505050505050506fffffffffffffffffffffffffffffffff6fffffffffffffffffffffffffffffffff6fffffffffffffffffffffffffffffffff6fffffffffffffffffffffffffffffffff6fffffffffffffffffffffffffffffffff6fffffffffffffffffffffffffffffffff6fffffffffffffffffffffffffffffffff8650505050505050507fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff865050505050505050600060006000600060006000600060008750505050505050505063ffffffff63ffffffff63ffffffff63ffffffff63ffffffff63ffffffff63ffffffff63ffffffff8750505050505050505067ffffffffffffffff67ffffffffffffffff67ffffffffffffffff67ffffffffffffffff67ffffffffffffffff67ffffffffffffffff67ffffffffffffffff67ffffffffffffffff875050505050505050506fffffffffffffffffffffffffffffffff6fffffffffffffffffffffffffffffffff6fffffffffffffffffffffffffffffffff6fffffffffffffffffffffffffffffffff6fffffffffffffffffffffffffffffffff6fffffffffffffffffffffffffffffffff6fffffffffffffffffffffffffffffffff6fffffffffffffffffffffffffffffffff875050505050505050507fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff87"  # noqa: E501
                    )
                )
            },
        },
        {
            "indexes": {"data": 1, "gas": 1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    code=bytes.fromhex(
                        "600080505063ffffffff80505067ffffffffffffffff8050506fffffffffffffffffffffffffffffffff8050507fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff805050600060008150505063ffffffff63ffffffff8150505067ffffffffffffffff67ffffffffffffffff815050506fffffffffffffffffffffffffffffffff6fffffffffffffffffffffffffffffffff815050507fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff81505050600060006000825050505063ffffffff63ffffffff63ffffffff825050505067ffffffffffffffff67ffffffffffffffff67ffffffffffffffff82505050506fffffffffffffffffffffffffffffffff6fffffffffffffffffffffffffffffffff6fffffffffffffffffffffffffffffffff82505050507fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff8250505050600060006000600083505050505063ffffffff63ffffffff63ffffffff63ffffffff83505050505067ffffffffffffffff67ffffffffffffffff67ffffffffffffffff67ffffffffffffffff8350505050506fffffffffffffffffffffffffffffffff6fffffffffffffffffffffffffffffffff6fffffffffffffffffffffffffffffffff6fffffffffffffffffffffffffffffffff8350505050507fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff835050505050600060006000600060008450505050505063ffffffff63ffffffff63ffffffff63ffffffff63ffffffff8450505050505067ffffffffffffffff67ffffffffffffffff67ffffffffffffffff67ffffffffffffffff67ffffffffffffffff845050505050506fffffffffffffffffffffffffffffffff6fffffffffffffffffffffffffffffffff6fffffffffffffffffffffffffffffffff6fffffffffffffffffffffffffffffffff6fffffffffffffffffffffffffffffffff845050505050507fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff84505050505050600060006000600060006000855050505050505063ffffffff63ffffffff63ffffffff63ffffffff63ffffffff63ffffffff855050505050505067ffffffffffffffff67ffffffffffffffff67ffffffffffffffff67ffffffffffffffff67ffffffffffffffff67ffffffffffffffff85505050505050506fffffffffffffffffffffffffffffffff6fffffffffffffffffffffffffffffffff6fffffffffffffffffffffffffffffffff6fffffffffffffffffffffffffffffffff6fffffffffffffffffffffffffffffffff6fffffffffffffffffffffffffffffffff85505050505050507fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff8550505050505050600060006000600060006000600086505050505050505063ffffffff63ffffffff63ffffffff63ffffffff63ffffffff63ffffffff63ffffffff86505050505050505067ffffffffffffffff67ffffffffffffffff67ffffffffffffffff67ffffffffffffffff67ffffffffffffffff67ffffffffffffffff67ffffffffffffffff8650505050505050506fffffffffffffffffffffffffffffffff6fffffffffffffffffffffffffffffffff6fffffffffffffffffffffffffffffffff6fffffffffffffffffffffffffffffffff6fffffffffffffffffffffffffffffffff6fffffffffffffffffffffffffffffffff6fffffffffffffffffffffffffffffffff8650505050505050507fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff865050505050505050600060006000600060006000600060008750505050505050505063ffffffff63ffffffff63ffffffff63ffffffff63ffffffff63ffffffff63ffffffff63ffffffff8750505050505050505067ffffffffffffffff67ffffffffffffffff67ffffffffffffffff67ffffffffffffffff67ffffffffffffffff67ffffffffffffffff67ffffffffffffffff67ffffffffffffffff875050505050505050506fffffffffffffffffffffffffffffffff6fffffffffffffffffffffffffffffffff6fffffffffffffffffffffffffffffffff6fffffffffffffffffffffffffffffffff6fffffffffffffffffffffffffffffffff6fffffffffffffffffffffffffffffffff6fffffffffffffffffffffffffffffffff6fffffffffffffffffffffffffffffffff875050505050505050507fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff87"  # noqa: E501
                    )
                )
            },
        },
        {
            "indexes": {"data": 2, "gas": 2, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    code=bytes.fromhex(
                        "600080505063ffffffff80505067ffffffffffffffff8050506fffffffffffffffffffffffffffffffff8050507fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff805050600060008150505063ffffffff63ffffffff8150505067ffffffffffffffff67ffffffffffffffff815050506fffffffffffffffffffffffffffffffff6fffffffffffffffffffffffffffffffff815050507fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff81505050600060006000825050505063ffffffff63ffffffff63ffffffff825050505067ffffffffffffffff67ffffffffffffffff67ffffffffffffffff82505050506fffffffffffffffffffffffffffffffff6fffffffffffffffffffffffffffffffff6fffffffffffffffffffffffffffffffff82505050507fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff8250505050600060006000600083505050505063ffffffff63ffffffff63ffffffff63ffffffff83505050505067ffffffffffffffff67ffffffffffffffff67ffffffffffffffff67ffffffffffffffff8350505050506fffffffffffffffffffffffffffffffff6fffffffffffffffffffffffffffffffff6fffffffffffffffffffffffffffffffff6fffffffffffffffffffffffffffffffff8350505050507fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff835050505050600060006000600060008450505050505063ffffffff63ffffffff63ffffffff63ffffffff63ffffffff8450505050505067ffffffffffffffff67ffffffffffffffff67ffffffffffffffff67ffffffffffffffff67ffffffffffffffff845050505050506fffffffffffffffffffffffffffffffff6fffffffffffffffffffffffffffffffff6fffffffffffffffffffffffffffffffff6fffffffffffffffffffffffffffffffff6fffffffffffffffffffffffffffffffff845050505050507fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff84505050505050600060006000600060006000855050505050505063ffffffff63ffffffff63ffffffff63ffffffff63ffffffff63ffffffff855050505050505067ffffffffffffffff67ffffffffffffffff67ffffffffffffffff67ffffffffffffffff67ffffffffffffffff67ffffffffffffffff85505050505050506fffffffffffffffffffffffffffffffff6fffffffffffffffffffffffffffffffff6fffffffffffffffffffffffffffffffff6fffffffffffffffffffffffffffffffff6fffffffffffffffffffffffffffffffff6fffffffffffffffffffffffffffffffff85505050505050507fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff8550505050505050600060006000600060006000600086505050505050505063ffffffff63ffffffff63ffffffff63ffffffff63ffffffff63ffffffff63ffffffff86505050505050505067ffffffffffffffff67ffffffffffffffff67ffffffffffffffff67ffffffffffffffff67ffffffffffffffff67ffffffffffffffff67ffffffffffffffff8650505050505050506fffffffffffffffffffffffffffffffff6fffffffffffffffffffffffffffffffff6fffffffffffffffffffffffffffffffff6fffffffffffffffffffffffffffffffff6fffffffffffffffffffffffffffffffff6fffffffffffffffffffffffffffffffff6fffffffffffffffffffffffffffffffff8650505050505050507fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff865050505050505050600060006000600060006000600060008750505050505050505063ffffffff63ffffffff63ffffffff63ffffffff63ffffffff63ffffffff63ffffffff63ffffffff8750505050505050505067ffffffffffffffff67ffffffffffffffff67ffffffffffffffff67ffffffffffffffff67ffffffffffffffff67ffffffffffffffff67ffffffffffffffff67ffffffffffffffff875050505050505050506fffffffffffffffffffffffffffffffff6fffffffffffffffffffffffffffffffff6fffffffffffffffffffffffffffffffff6fffffffffffffffffffffffffffffffff6fffffffffffffffffffffffffffffffff6fffffffffffffffffffffffffffffffff6fffffffffffffffffffffffffffffffff6fffffffffffffffffffffffffffffffff875050505050505050507fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff87"  # noqa: E501
                    )
                )
            },
        },
    ]

    post, _exc = resolve_expect_post(EXPECT_ENTRIES, d, g, v, fork)

    tx = Transaction(
        sender=sender,
        to=contract,
        data=_tx_data(d),
        gas_limit=TX_GAS[g],
        value=TX_VALUE[v],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
