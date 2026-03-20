"""
CALLCODE -> (CALLCODE -> DELEGATE -> CODE) OOG.

Ported from:
tests/static/state_tests/stCallDelegateCodesCallCodeHomestead
callcallcallcode_001_OOGMAfterFiller.json
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
        "tests/static/state_tests/stCallDelegateCodesCallCodeHomestead/callcallcallcode_001_OOGMAfterFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_callcallcallcode_001_oogm_after(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """CALLCODE -> (CALLCODE -> DELEGATE -> CODE) OOG."""
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

    callee = pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x1,
                value=Op.CALLCODE(
                    gas=0x927C0,
                    address=0x7B1ED5FA290739659102E7C47B650EFD2EBA625B,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x40,
                    ret_offset=0x0,
                    ret_size=0x40,
                ),
            )
            + Op.SHA3(offset=0x0, size=0x2FFFFF)
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x37e72dd6ff3c2ac8c1ddab092a26164a2ad5988c"),  # noqa: E501
    )
    callee_1 = pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x2,
                value=Op.DELEGATECALL(
                    gas=0x61A80,
                    address=0xB126C622075B1189FB6C45E851641CFADDF65B36,
                    args_offset=0x0,
                    args_size=0x40,
                    ret_offset=0x0,
                    ret_size=0x40,
                ),
            )
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x7b1ed5fa290739659102e7c47b650efd2eba625b"),  # noqa: E501
    )
    # Source: LLL
    # {  [[ 0 ]] (CALLCODE 800000 <contract:0x1000000000000000000000000000000000000001> 0 0 64 0 64 ) [[11]] 1  }  # noqa: E501
    contract = pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x0,
                value=Op.CALLCODE(
                    gas=0xC3500,
                    address=0x37E72DD6FF3C2AC8C1DDAB092A26164A2AD5988C,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x40,
                    ret_offset=0x0,
                    ret_size=0x40,
                ),
            )
            + Op.SSTORE(key=0xB, value=0x1)
            + Op.STOP
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0x7dabf2bb39aaf74720cfa113ae52f673bf477e2b"),  # noqa: E501
    )
    callee_2 = pre.deploy_contract(
        code=Op.SSTORE(key=0x3, value=0x1) + Op.STOP,
        nonce=0,
        address=Address("0xb126c622075b1189fb6c45e851641cfaddf65b36"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": 0, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "60406000604060006000737b1ed5fa290739659102e7c47b650efd2eba625b620927c0f2600155622fffff60002000"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "604060006040600073b126c622075b1189fb6c45e851641cfaddf65b3662061a80f460025500"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={11: 1},
                    code=bytes.fromhex(
                        "604060006040600060007337e72dd6ff3c2ac8c1ddab092a26164a2ad5988c620c3500f26000556001600b5500"  # noqa: E501
                    ),
                ),
                callee_2: Account(code=bytes.fromhex("600160035500")),
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, 0, 0, 0, fork)

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=1000000,
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
