"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stStaticCall
static_ZeroValue_SUICIDE_OOGRevertFiller.json
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
        "tests/static/state_tests/stStaticCall/static_ZeroValue_SUICIDE_OOGRevertFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
@pytest.mark.slow
def test_static_zero_value_suicide_oog_revert(
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
    # { (STATICCALL 100000 <contract:0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b> 0 0 0 0) (KECCAK256 0x00 0x2fffff) }  # noqa: E501
    contract = pre.deploy_contract(
        code=(
            Op.POP(
                Op.STATICCALL(
                    gas=0x186A0,
                    address=0xDA2EB5512889130C4AF686A291B08665B889CB22,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.SHA3(offset=0x0, size=0x2FFFFF)
            + Op.STOP
        ),
        nonce=0,
        address=Address("0xcbecd26bebbaeddef56fce1849f78096332b11ab"),  # noqa: E501
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

    EXPECT_ENTRIES: list[dict] = [
        {
            "indexes": {"data": 0, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    code=bytes.fromhex(
                        "600060006000600073da2eb5512889130c4af686a291b08665b889cb22620186a0fa50622fffff60002000"  # noqa: E501
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

    post, _exc = resolve_expect_post(EXPECT_ENTRIES, 0, 0, 0, fork)

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=1000000,
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
