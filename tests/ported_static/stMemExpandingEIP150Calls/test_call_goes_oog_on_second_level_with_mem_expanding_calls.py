"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stMemExpandingEIP150Calls
CallGoesOOGOnSecondLevelWithMemExpandingCallsFiller.json
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


@pytest.mark.ported_from(
    [
        "tests/static/state_tests/stMemExpandingEIP150Calls/CallGoesOOGOnSecondLevelWithMemExpandingCallsFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_call_goes_oog_on_second_level_with_mem_expanding_calls(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x8D19F2B0D2F5689C1771FBCA70476CA6E877A81EE15C3733DE87FAE38E5ABCEF
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    # Source: raw bytecode
    callee = pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x8, value=Op.GAS)
            + Op.POP(Op.CREATE(value=0x0, offset=0x0, size=0x0))
            + Op.POP(Op.CREATE(value=0x0, offset=0x0, size=0x0))
            + Op.SSTORE(key=0x9, value=Op.GAS)
            + Op.SSTORE(key=0xA, value=Op.GAS)
        ),
        nonce=0,
        address=Address("0x2ef686162bebf2542147767d5be471976860cceb"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xE8D4A51000)
    callee_1 = pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x8, value=Op.GAS)
            + Op.SSTORE(
                key=0x9,
                value=Op.CALL(
                    gas=0x927C0,
                    address=0x2EF686162BEBF2542147767D5BE471976860CCEB,
                    value=0x0,
                    args_offset=0xFF,
                    args_size=0xFF,
                    ret_offset=0xFF,
                    ret_size=0xFF,
                ),
            )
        ),
        nonce=0,
        address=Address("0xa27e20572430916b3d6772b27329cc460224904d"),  # noqa: E501
    )
    # Source: raw bytecode
    contract = pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x8, value=Op.GAS)
            + Op.SSTORE(
                key=0x9,
                value=Op.CALL(
                    gas=0x927C0,
                    address=0xA27E20572430916B3D6772B27329CC460224904D,
                    value=0x0,
                    args_offset=0xFF,
                    args_size=0xFF,
                    ret_offset=0xFF,
                    ret_size=0xFF,
                ),
            )
        ),
        nonce=0,
        address=Address("0xaf229807016a538dfcdab92a53337de38178d40f"),  # noqa: E501
    )

    EXPECT_ENTRIES: list[dict] = [
        {
            "indexes": {"data": 0, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "5a600855600060006000f050600060006000f0505a6009555a600a55"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "5a60085560ff60ff60ff60ff6000732ef686162bebf2542147767d5be471976860cceb620927c0f1600955"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={8: 0x30956},
                    code=bytes.fromhex(
                        "5a60085560ff60ff60ff60ff600073a27e20572430916b3d6772b27329cc460224904d620927c0f1600955"  # noqa: E501
                    ),
                ),
            },
        },
    ]

    post, _exc = resolve_expect_post(EXPECT_ENTRIES, 0, 0, 0, fork)

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=220000,
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
