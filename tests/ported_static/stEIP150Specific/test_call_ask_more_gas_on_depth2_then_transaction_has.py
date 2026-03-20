"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stEIP150Specific
CallAskMoreGasOnDepth2ThenTransactionHasFiller.json
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
        "tests/static/state_tests/stEIP150Specific/CallAskMoreGasOnDepth2ThenTransactionHasFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_call_ask_more_gas_on_depth2_then_transaction_has(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x4F31B3206FBF0E0E598B9B1A7D8AC86302A0FF1D8930738F1BEBAE9B67173E52
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    callee = pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x8, value=Op.GAS)
            + Op.SSTORE(
                key=0x9,
                value=Op.CALL(
                    gas=0x927C0,
                    address=0xF39D40EACB6D2C685AC10664E759D1CF8F775DFF,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x25c370b55ec8467127bc4e13404915901d689098"),  # noqa: E501
    )
    # Source: LLL
    # { (SSTORE 8 (GAS)) (SSTORE 9 (CALL 200000 <contract:0x1000000000000000000000000000000000000107> 0 0 0 0 0)) }  # noqa: E501
    contract = pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x8, value=Op.GAS)
            + Op.SSTORE(
                key=0x9,
                value=Op.CALL(
                    gas=0x30D40,
                    address=0x25C370B55EC8467127BC4E13404915901D689098,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x8553d06001d46f3b0b18a938acf8c552d87c5837"),  # noqa: E501
    )
    callee_1 = pre.deploy_contract(
        code=Op.SSTORE(key=0x8, value=Op.GAS) + Op.STOP,
        nonce=0,
        address=Address("0xf39d40eacb6d2c685ac10664e759d1cf8f775dff"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xE8D4A51000)

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": 0, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    storage={8: 0x30D3E, 9: 1},
                    code=bytes.fromhex(
                        "5a6008556000600060006000600073f39d40eacb6d2c685ac10664e759d1cf8f775dff620927c0f160095500"  # noqa: E501
                    ),
                ),
                contract: Account(
                    storage={8: 0x8D5B6, 9: 1},
                    code=bytes.fromhex(
                        "5a600855600060006000600060007325c370b55ec8467127bc4e13404915901d68909862030d40f160095500"  # noqa: E501
                    ),
                ),
                callee_1: Account(
                    storage={8: 0x2A1F6}, code=bytes.fromhex("5a60085500")
                ),
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, 0, 0, 0, fork)

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=600000,
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
