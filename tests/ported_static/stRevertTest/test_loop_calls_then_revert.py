"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stRevertTest/LoopCallsThenRevertFiller.json
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
    ["tests/static/state_tests/stRevertTest/LoopCallsThenRevertFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_loop_calls_then_revert(
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

    # Source: raw bytecode
    contract = pre.deploy_contract(
        code=(
            Op.JUMPDEST
            + Op.SSTORE(key=0x0, value=Op.SUB(Op.SLOAD(key=0x0), 0x1))
            + Op.POP(
                Op.CALL(
                    gas=0xC350,
                    address=0xC47BCBF49DD735566CFDE927821E938D5B33014C,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.JUMPI(pc=0x0, condition=Op.SLOAD(key=0x0))
        ),
        storage={0x0: 0x352},
        nonce=0,
        address=Address("0x0347aff20d9d3c574e18f3b17dc267ddcd2d75ca"),  # noqa: E501
    )
    callee = pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=Op.ADD(0x1, Op.SLOAD(key=0x0))) + Op.STOP
        ),
        nonce=0,
        address=Address("0xc47bcbf49dd735566cfde927821e938d5b33014c"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xE8D4A51000)

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": 0, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    code=bytes.fromhex(
                        "5b6001600054036000556000600060006000600073c47bcbf49dd735566cfde927821e938d5b33014c61c350f150600054600057"  # noqa: E501
                    )
                ),
                callee: Account(
                    storage={0: 850},
                    code=bytes.fromhex("60005460010160005500"),
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
