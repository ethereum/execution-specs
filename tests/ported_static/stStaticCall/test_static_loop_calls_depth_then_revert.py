"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stStaticCall
static_LoopCallsDepthThenRevertFiller.json
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
        "tests/static/state_tests/stStaticCall/static_LoopCallsDepthThenRevertFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
@pytest.mark.slow
def test_static_loop_calls_depth_then_revert(
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
        gas_limit=100000000,
    )

    # Source: LLL
    # { [[ 0 ]] (CALL ( - (GAS) 100000) <contract:target:0x1000000000000000000000000000000000000000> 0 0 0 0 0) [[ 1 ]] 1 }  # noqa: E501
    contract = pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x0,
                value=Op.CALL(
                    gas=Op.SUB(Op.GAS, 0x186A0),
                    address=0x15DC6AD6AA4B45C8C5F8658596F0BE95F4FB77FD,
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
        nonce=0,
        address=Address("0x15dc6ad6aa4b45c8c5f8658596f0be95f4fb77fd"),  # noqa: E501
    )
    callee = pre.deploy_contract(
        code=(
            Op.STATICCALL(
                gas=Op.GAS,
                address=0x8AC26AD64561031BE35E49C24EE18C6E43C21795,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x77c35f69d9f67cc9c06c803eb2c0aca9c2a746e6"),  # noqa: E501
    )
    callee_1 = pre.deploy_contract(
        code=(
            Op.STATICCALL(
                gas=Op.GAS,
                address=0x77C35F69D9F67CC9C06C803EB2C0ACA9C2A746E6,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x8ac26ad64561031be35e49c24ee18c6e43c21795"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xE8D4A51000)

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": 0, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={0: 1, 1: 1},
                    code=bytes.fromhex(
                        "600060006000600060007315dc6ad6aa4b45c8c5f8658596f0be95f4fb77fd620186a05a03f1600055600160015500"  # noqa: E501
                    ),
                ),
                callee: Account(
                    code=bytes.fromhex(
                        "6000600060006000738ac26ad64561031be35e49c24ee18c6e43c217955afa00"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "60006000600060007377c35f69d9f67cc9c06c803eb2c0aca9c2a746e65afa00"  # noqa: E501
                    )
                ),
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, 0, 0, 0, fork)

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=10000000,
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
