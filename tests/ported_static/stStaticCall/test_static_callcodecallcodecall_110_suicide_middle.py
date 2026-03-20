"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stStaticCall
static_callcodecallcodecall_110_SuicideMiddleFiller.json
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
        "tests/static/state_tests/stStaticCall/static_callcodecallcodecall_110_SuicideMiddleFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
@pytest.mark.slow
def test_static_callcodecallcodecall_110_suicide_middle(
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
        gas_limit=30000000,
    )

    # Source: LLL
    # {  [[ 0 ]] (DELEGATECALL 150000 <contract:0x1000000000000000000000000000000000000001> 0 64 0 64 ) }  # noqa: E501
    contract = pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x0,
                value=Op.DELEGATECALL(
                    gas=0x249F0,
                    address=0x92D7028788CAA240253B7B2A92386464690CDC72,
                    args_offset=0x0,
                    args_size=0x40,
                    ret_offset=0x0,
                    ret_size=0x40,
                ),
            )
            + Op.STOP
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0x2b30b637f37e3f5b8ca4ab846331d0779a3f4671"),  # noqa: E501
    )
    callee = pre.deploy_contract(
        code=(
            Op.SELFDESTRUCT(address=0x2B30B637F37E3F5B8CA4AB846331D0779A3F4671)
            + Op.STATICCALL(
                gas=0xC350,
                address=0x48E2D4C0B593BFEBE5DDB4F13AA355B8BD83DDD3,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x40,
            )
            + Op.STOP
        ),
        balance=0x2540BE400,
        nonce=0,
        address=Address("0x408f1aceffec7bdaa35d77006cdcaead563bb694"),  # noqa: E501
    )
    callee_1 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x3, value=0x1) + Op.STOP,
        balance=0x2540BE400,
        nonce=0,
        address=Address("0x48e2d4c0b593bfebe5ddb4f13aa355b8bd83ddd3"),  # noqa: E501
    )
    callee_2 = pre.deploy_contract(
        code=(
            Op.DELEGATECALL(
                gas=0x186A0,
                address=0x408F1ACEFFEC7BDAA35D77006CDCAEAD563BB694,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x40,
            )
            + Op.STOP
        ),
        balance=0x2540BE400,
        nonce=0,
        address=Address("0x92d7028788caa240253b7b2a92386464690cdc72"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": 0, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={0: 1},
                    code=bytes.fromhex(
                        "60406000604060007392d7028788caa240253b7b2a92386464690cdc72620249f0f460005500"  # noqa: E501
                    ),
                ),
                callee: Account(
                    code=bytes.fromhex(
                        "732b30b637f37e3f5b8ca4ab846331d0779a3f4671ff60406000604060007348e2d4c0b593bfebe5ddb4f13aa355b8bd83ddd361c350fa00"  # noqa: E501
                    )
                ),
                callee_1: Account(code=bytes.fromhex("600160035200")),
                callee_2: Account(
                    code=bytes.fromhex(
                        "604060006040600073408f1aceffec7bdaa35d77006cdcaead563bb694620186a0f400"  # noqa: E501
                    )
                ),
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, 0, 0, 0, fork)

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=3000000,
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
