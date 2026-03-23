"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stCallDelegateCodesCallCodeHomestead
callcodecallcallcode_101_SuicideMiddleFiller.json
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
        "tests/static/state_tests/stCallDelegateCodesCallCodeHomestead/callcodecallcallcode_101_SuicideMiddleFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_callcodecallcallcode_101_suicide_middle(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
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
    # {  [[ 0 ]] (DELEGATECALL 150000 0x1000000000000000000000000000000000000001 0 64 0 64 ) }  # noqa: E501
    contract = pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x0,
                value=Op.DELEGATECALL(
                    gas=0x249F0,
                    address=0x1000000000000000000000000000000000000001,
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
        address=Address("0x1000000000000000000000000000000000000000"),  # noqa: E501
    )
    # Source: LLL
    # {  [[ 1 ]] (CALLCODE 100000 0x1000000000000000000000000000000000000002 0 0 64 0 64 ) }  # noqa: E501
    callee = pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x1,
                value=Op.CALLCODE(
                    gas=0x186A0,
                    address=0x1000000000000000000000000000000000000002,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x40,
                    ret_offset=0x0,
                    ret_size=0x40,
                ),
            )
            + Op.STOP
        ),
        balance=0x2540BE400,
        nonce=0,
        address=Address("0x1000000000000000000000000000000000000001"),  # noqa: E501
    )
    # Source: LLL
    # { (SELFDESTRUCT 0x1000000000000000000000000000000000000000) [[ 2 ]] (DELEGATECALL 50000 0x1000000000000000000000000000000000000003 0 64 0 64 ) }  # noqa: E501
    callee_1 = pre.deploy_contract(
        code=(
            Op.SELFDESTRUCT(address=0x1000000000000000000000000000000000000000)
            + Op.SSTORE(
                key=0x2,
                value=Op.DELEGATECALL(
                    gas=0xC350,
                    address=0x1000000000000000000000000000000000000003,
                    args_offset=0x0,
                    args_size=0x40,
                    ret_offset=0x0,
                    ret_size=0x40,
                ),
            )
            + Op.STOP
        ),
        balance=0x2540BE400,
        nonce=0,
        address=Address("0x1000000000000000000000000000000000000002"),  # noqa: E501
    )
    # Source: LLL
    # {  (SSTORE 3 1) }
    callee_2 = pre.deploy_contract(
        code=Op.SSTORE(key=0x3, value=0x1) + Op.STOP,
        balance=0x2540BE400,
        nonce=0,
        address=Address("0x1000000000000000000000000000000000000003"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": 0, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={0: 1, 1: 1},
                    code=bytes.fromhex(
                        "6040600060406000731000000000000000000000000000000000000001620249f0f460005500"  # noqa: E501
                    ),
                ),
                callee: Account(
                    code=bytes.fromhex(
                        "60406000604060006000731000000000000000000000000000000000000002620186a0f260015500"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "731000000000000000000000000000000000000000ff604060006040600073100000000000000000000000000000000000000361c350f460025500"  # noqa: E501
                    )
                ),
                callee_2: Account(code=bytes.fromhex("600160035500")),
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
