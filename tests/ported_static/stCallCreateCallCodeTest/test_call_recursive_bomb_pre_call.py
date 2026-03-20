"""
recursive call.

Ported from:
tests/static/state_tests/stCallCreateCallCodeTest
CallRecursiveBombPreCallFiller.json
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
        "tests/static/state_tests/stCallCreateCallCodeTest/CallRecursiveBombPreCallFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Prague")
@pytest.mark.pre_alloc_mutable
def test_call_recursive_bomb_pre_call(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Recursive call."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x77F65B71F1F16A75476F469F7106D1B60BFEC266AE25B8DA16A9091D223AA24A
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=9223372036854775807,
    )

    callee = pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=Op.ADD(Op.SLOAD(key=0x0), 0x1))
            + Op.SSTORE(
                key=0x1,
                value=Op.CALL(
                    gas=Op.SUB(Op.GAS, 0x36B00),
                    address=Op.ADDRESS,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.STOP
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0x1b3f200856856edc2e98efcd637775c6e341e3c0"),  # noqa: E501
    )
    # Source: LLL
    # { (CALL 100000 0xbad304eb96065b2a98b57a48a06ae28d285a71b5 23 0 0 0 0)  (CALL 0x7ffffffffffffff <contract:0x945304eb96065b2a98b57a48a06ae28d285a71b5> 23 0 0 0 0)  }  # noqa: E501
    contract = pre.deploy_contract(
        code=(
            Op.POP(
                Op.CALL(
                    gas=0x186A0,
                    address=0xBAD304EB96065B2A98B57A48A06AE28D285A71B5,
                    value=0x17,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.CALL(
                gas=0x7FFFFFFFFFFFFFF,
                address=0x1B3F200856856EDC2E98EFCD637775C6E341E3C0,
                value=0x17,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
            + Op.STOP
        ),
        balance=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,
        nonce=0,
        address=Address("0x55bd941930d381e552d261d75ed997be59e36350"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": 0, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    storage={0: 1024, 1: 1},
                    code=bytes.fromhex(
                        "600160005401600055600060006000600060003062036b005a03f160015500"  # noqa: E501
                    ),
                ),
                contract: Account(
                    code=bytes.fromhex(
                        "6000600060006000601773bad304eb96065b2a98b57a48a06ae28d285a71b5620186a0f15060006000600060006017731b3f200856856edc2e98efcd637775c6e341e3c06707fffffffffffffff100"  # noqa: E501
                    )
                ),
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, 0, 0, 0, fork)

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=9214364837600034817,
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
