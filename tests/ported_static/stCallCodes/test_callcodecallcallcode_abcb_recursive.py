"""
CALLCODE -> CALL <-> CALLCODE.

Ported from:
tests/static/state_tests/stCallCodes
callcodecallcallcode_ABCB_RECURSIVEFiller.json
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
        "tests/static/state_tests/stCallCodes/callcodecallcallcode_ABCB_RECURSIVEFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_callcodecallcallcode_abcb_recursive(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """CALLCODE -> CALL <-> CALLCODE."""
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

    callee = pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x1,
                value=Op.CALL(
                    gas=0xF4240,
                    address=0xA71333D8C0291CFD6DA54BEC5A3957563AB16C1C,
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
        address=Address("0x66c0d9f841a86866465e6385c3827be02b580020"),  # noqa: E501
    )
    # Source: LLL
    # {  [[ 0 ]] (CALLCODE 25000000 <contract:0x1000000000000000000000000000000000000001> 0 0 64 0 64 ) }  # noqa: E501
    contract = pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x0,
                value=Op.CALLCODE(
                    gas=0x17D7840,
                    address=0x66C0D9F841A86866465E6385C3827BE02B580020,
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
    callee_1 = pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x2,
                value=Op.CALLCODE(
                    gas=0x7A120,
                    address=0x66C0D9F841A86866465E6385C3827BE02B580020,
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
        address=Address("0xa71333d8c0291cfd6da54bec5a3957563ab16c1c"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    EXPECT_ENTRIES: list[dict] = [
        {
            "indexes": {"data": 0, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "6040600060406000600073a71333d8c0291cfd6da54bec5a3957563ab16c1c620f4240f160015500"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={0: 1, 1: 1},
                    code=bytes.fromhex(
                        "604060006040600060007366c0d9f841a86866465e6385c3827be02b58002063017d7840f260005500"  # noqa: E501
                    ),
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "604060006040600060007366c0d9f841a86866465e6385c3827be02b5800206207a120f260025500"  # noqa: E501
                    )
                ),
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
