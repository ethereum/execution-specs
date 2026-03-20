"""
CALLCODE -> CALLCODE1 -> DELEGATECALL2 -> CALLCODE1 -> ...

Ported from:
tests/static/state_tests/stCallDelegateCodesCallCodeHomestead
callcallcallcode_ABCB_RECURSIVEFiller.json
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
        "tests/static/state_tests/stCallDelegateCodesCallCodeHomestead/callcallcallcode_ABCB_RECURSIVEFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_callcallcallcode_abcb_recursive(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """CALLCODE -> CALLCODE1 -> DELEGATECALL2 -> CALLCODE1 -> ..."""
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
        gas_limit=3000000000,
    )

    # Source: LLL
    # {  [[ 0 ]] (CALLCODE 25000000 <contract:0x1000000000000000000000000000000000000001> 0 0 64 0 64 ) }  # noqa: E501
    contract = pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x0,
                value=Op.CALLCODE(
                    gas=0x17D7840,
                    address=0xE2AB9779F4FB1D9D39211CC2082083ADD172E69C,
                    value=0x0,
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
        address=Address("0x6d477a21d3906d4c0cd1edbfa7d272e6e21f1ca1"),  # noqa: E501
    )
    callee = pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x2,
                value=Op.DELEGATECALL(
                    gas=0x7A120,
                    address=0xE2AB9779F4FB1D9D39211CC2082083ADD172E69C,
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
        address=Address("0xa72f0e2f2fc5fd0878af9b8e4aaed09983670929"),  # noqa: E501
    )
    callee_1 = pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x1,
                value=Op.CALLCODE(
                    gas=0xF4240,
                    address=0xA72F0E2F2FC5FD0878AF9B8E4AAED09983670929,
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
        address=Address("0xe2ab9779f4fb1d9d39211cc2082083add172e69c"),  # noqa: E501
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
                        "6040600060406000600073e2ab9779f4fb1d9d39211cc2082083add172e69c63017d7840f260005500"  # noqa: E501
                    ),
                ),
                callee: Account(
                    code=bytes.fromhex(
                        "604060006040600073e2ab9779f4fb1d9d39211cc2082083add172e69c6207a120f460025500"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "6040600060406000600073a72f0e2f2fc5fd0878af9b8e4aaed09983670929620f4240f260015500"  # noqa: E501
                    )
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
