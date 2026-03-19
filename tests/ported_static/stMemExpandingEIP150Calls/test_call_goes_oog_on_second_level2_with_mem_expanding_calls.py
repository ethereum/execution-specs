"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stMemExpandingEIP150Calls
CallGoesOOGOnSecondLevel2WithMemExpandingCallsFiller.json
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
        "tests/static/state_tests/stMemExpandingEIP150Calls/CallGoesOOGOnSecondLevel2WithMemExpandingCallsFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_call_goes_oog_on_second_level2_with_mem_expanding_calls(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x0B51075BB33D347A23B516E327E1B71C54F63FAA192D1D94B62C76E0C26CF98A
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    # Source: raw bytecode
    contract = pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x8, value=Op.GAS)
            + Op.SSTORE(
                key=0x9,
                value=Op.CALL(
                    gas=0x927C0,
                    address=0xC10A98222464B07008CEB5A0EC44ED49920ADDDA,
                    value=0x0,
                    args_offset=0xFF,
                    args_size=0xFF,
                    ret_offset=0xFF,
                    ret_size=0xFF,
                ),
            )
        ),
        nonce=0,
        address=Address("0x0700bb425d7d4c412ac658014015bd6c98652dc4"),  # noqa: E501
    )
    # Source: raw bytecode
    callee = pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x8, value=Op.GAS)
            + Op.SSTORE(key=0x9, value=Op.GAS)
            + Op.SSTORE(key=0xA, value=Op.GAS)
        ),
        nonce=0,
        address=Address("0x96983de02bfbcb5d0f4e0ee98fdde6d6f0c75fe0"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xE8D4A510000)
    callee_1 = pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x8, value=Op.GAS)
            + Op.SSTORE(
                key=0x9,
                value=Op.CALL(
                    gas=0x927C0,
                    address=0x96983DE02BFBCB5D0F4E0EE98FDDE6D6F0C75FE0,
                    value=0x0,
                    args_offset=0xFF,
                    args_size=0xFF,
                    ret_offset=0xFF,
                    ret_size=0xFF,
                ),
            )
        ),
        nonce=0,
        address=Address("0xc10a98222464b07008ceb5a0ec44ed49920addda"),  # noqa: E501
    )

    EXPECT_ENTRIES: list[dict] = [
        {
            "indexes": {"data": 0, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    code=bytes.fromhex(
                        "5a60085560ff60ff60ff60ff600073c10a98222464b07008ceb5a0ec44ed49920addda620927c0f1600955"  # noqa: E501
                    )
                ),
                callee: Account(
                    code=bytes.fromhex("5a6008555a6009555a600a55")
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "5a60085560ff60ff60ff60ff60007396983de02bfbcb5d0f4e0ee98fdde6d6f0c75fe0620927c0f1600955"  # noqa: E501
                    )
                ),
            },
        },
    ]

    post, _exc = resolve_expect_post(EXPECT_ENTRIES, 0, 0, 0, fork)

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=160000,
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
