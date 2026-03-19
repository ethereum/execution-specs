"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stMemExpandingEIP150Calls
DelegateCallOnEIPWithMemExpandingCallsFiller.json
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
        "tests/static/state_tests/stMemExpandingEIP150Calls/DelegateCallOnEIPWithMemExpandingCallsFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_delegate_call_on_eip_with_mem_expanding_calls(
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
    contract = pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x8, value=Op.GAS)
            + Op.SSTORE(
                key=0x9,
                value=Op.DELEGATECALL(
                    gas=0x927C0,
                    address=0xA1F6E75A455896613053D45331763A07F4718969,
                    args_offset=0xFF,
                    args_size=0xFF,
                    ret_offset=0xFF,
                    ret_size=0xFF,
                ),
            )
        ),
        nonce=0,
        address=Address("0x3fc906a124d4054023be5dd8666ce29aa3712ccb"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xE8D4A51000)
    # Source: raw bytecode
    callee = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=0x12),
        nonce=0,
        address=Address("0xa1f6e75a455896613053d45331763a07f4718969"),  # noqa: E501
    )

    EXPECT_ENTRIES: list[dict] = [
        {
            "indexes": {"data": 0, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={0: 18, 8: 0x8D5B6, 9: 1},
                    code=bytes.fromhex(
                        "5a60085560ff60ff60ff60ff73a1f6e75a455896613053d45331763a07f4718969620927c0f4600955"  # noqa: E501
                    ),
                ),
                callee: Account(code=bytes.fromhex("6012600055")),
            },
        },
    ]

    post, _exc = resolve_expect_post(EXPECT_ENTRIES, 0, 0, 0, fork)

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=600000,
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
