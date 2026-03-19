"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stEIP158Specific/CALL_OneVCallSuicide2Filler.json
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
        "tests/static/state_tests/stEIP158Specific/CALL_OneVCallSuicide2Filler.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_call_one_v_call_suicide2(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x4F31B3206FBF0E0E598B9B1A7D8AC86302A0FF1D8930738F1BEBAE9B67173E52
    )
    callee_1 = Address("0xeb201d2887816e041f6e807e804f64f3a7a226fe")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    callee = pre.deploy_contract(
        code=(
            Op.SELFDESTRUCT(address=0xEB201D2887816E041F6E807E804F64F3A7A226FE)
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x99378e0db04e57ae174ad69770e1b7a0aa805930"),  # noqa: E501
    )
    # Source: LLL
    # { [0](GAS) (CALL 60000 <contract:0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b> 1 0 0 0 0) [[100]] (SUB @0 (GAS)) }  # noqa: E501
    contract = pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x0, value=Op.GAS)
            + Op.POP(
                Op.CALL(
                    gas=0xEA60,
                    address=0x99378E0DB04E57AE174AD69770E1B7A0AA805930,
                    value=0x1,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.SSTORE(key=0x64, value=Op.SUB(Op.MLOAD(offset=0x0), Op.GAS))
            + Op.STOP
        ),
        balance=100,
        nonce=0,
        address=Address("0xea04224539257fbe043981aa6058fbc1d5e21b1a"),  # noqa: E501
    )
    pre[callee_1] = Account(balance=0, nonce=1)
    pre[sender] = Account(balance=0xE8D4A51000)

    EXPECT_ENTRIES: list[dict] = [
        {
            "indexes": {"data": 0, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "73eb201d2887816e041f6e807e804f64f3a7a226feff00"
                    )
                ),
                contract: Account(
                    storage={100: 16937},
                    code=bytes.fromhex(
                        "5a600052600060006000600060017399378e0db04e57ae174ad69770e1b7a0aa80593061ea60f1505a6000510360645500"  # noqa: E501
                    ),
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
