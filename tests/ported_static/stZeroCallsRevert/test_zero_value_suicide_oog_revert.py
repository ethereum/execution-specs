"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stZeroCallsRevert
ZeroValue_SUICIDE_OOGRevertFiller.json
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
        "tests/static/state_tests/stZeroCallsRevert/ZeroValue_SUICIDE_OOGRevertFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_zero_value_suicide_oog_revert(
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

    # Source: LLL
    # { (CALL 40000 <contract:0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b> 0 0 0 0 0) [[2]]12 [[3]]12 [[4]]12 [[100]](GAS) }  # noqa: E501
    contract = pre.deploy_contract(
        code=(
            Op.POP(
                Op.CALL(
                    gas=0x9C40,
                    address=0xDA2EB5512889130C4AF686A291B08665B889CB22,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.SSTORE(key=0x2, value=0xC)
            + Op.SSTORE(key=0x3, value=0xC)
            + Op.SSTORE(key=0x4, value=0xC)
            + Op.SSTORE(key=0x64, value=Op.GAS)
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x3f9709b08071257d9b49276abf1787b5bdccf0c4"),  # noqa: E501
    )
    callee = pre.deploy_contract(
        code=(
            Op.SELFDESTRUCT(address=0xDA2EB5512889130C4AF686A291B08665B889CB22)
            + Op.STOP
        ),
        nonce=0,
        address=Address("0xda2eb5512889130c4af686a291b08665b889cb22"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xE8D4A51000)

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": 0, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    code=bytes.fromhex(
                        "6000600060006000600073da2eb5512889130c4af686a291b08665b889cb22619c40f150600c600255600c600355600c6004555a60645500"  # noqa: E501
                    )
                ),
                callee: Account(
                    code=bytes.fromhex(
                        "73da2eb5512889130c4af686a291b08665b889cb22ff00"
                    )
                ),
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, 0, 0, 0, fork)

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=100000,
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
