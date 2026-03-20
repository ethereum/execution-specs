"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stStaticCall
static_CallRecursiveBomb0_OOG_atMaxCallDepthFiller.json
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
        "tests/static/state_tests/stStaticCall/static_CallRecursiveBomb0_OOG_atMaxCallDepthFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Prague")
@pytest.mark.pre_alloc_mutable
@pytest.mark.slow
def test_static_call_recursive_bomb0_oog_at_max_call_depth(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0xE04D1AC7DDDA0C98397D56A0B501E960D4CD325A39286919AC23C1A07009A869
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=110000000000,
    )

    # Source: LLL
    # { (CALLCODE (GAS) <contract:0x095e7baea6a6c7c4c2dfeb977efac326af552d87> 0 0 0 0 0) [[ 1 ]] 1 }  # noqa: E501
    contract = pre.deploy_contract(
        code=(
            Op.POP(
                Op.CALLCODE(
                    gas=Op.GAS,
                    address=0xBB09BB747BB11897420C59CACB65853142C67BB7,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.SSTORE(key=0x1, value=0x1)
            + Op.STOP
        ),
        balance=0x1312D00,
        nonce=0,
        address=Address("0x4a20a569d7008020c8cd630cff560f3e627522d3"),  # noqa: E501
    )
    callee = pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x0, value=Op.ADD(Op.SLOAD(key=0x0), 0x1))
            + Op.MSTORE(
                offset=0x2,
                value=Op.MUL(
                    Op.DIV(Op.MLOAD(offset=0x0), 0x402),
                    0xFFFFFFFFFFFFFFFFFFF,
                ),
            )
            + Op.STATICCALL(
                gas=Op.SUB(Op.GAS, 0x400),
                address=Op.ADDRESS,
                args_offset=0x0,
                args_size=Op.MUL(
                    Op.DIV(Op.MLOAD(offset=0x0), 0x402),
                    0xFFFFFFFFFFFFFFFFFFF,
                ),
                ret_offset=0x0,
                ret_size=0x0,
            )
            + Op.STOP
        ),
        balance=0x1312D00,
        nonce=0,
        address=Address("0xbb09bb747bb11897420c59cacb65853142c67bb7"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": 0, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={1: 1},
                    code=bytes.fromhex(
                        "6000600060006000600073bb09bb747bb11897420c59cacb65853142c67bb75af250600160015500"  # noqa: E501
                    ),
                ),
                callee: Account(
                    code=bytes.fromhex(
                        "600160005401600052690fffffffffffffffffff610402600051040260025260006000690fffffffffffffffffff61040260005104026000306104005a03fa00"  # noqa: E501
                    )
                ),
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, 0, 0, 0, fork)

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=100000000000,
        value=100000,
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
