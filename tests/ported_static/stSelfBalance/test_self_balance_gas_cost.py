"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stSelfBalance/selfBalanceGasCostFiller.json
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
    ["tests/static/state_tests/stSelfBalance/selfBalanceGasCostFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_self_balance_gas_cost(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x897B12D02D588D8A4FE16FF831CBD4459C6F62F8C845B0CCDD31CAF068C84A26
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000000,
    )

    # Source: asm
    # (asm GAS SELFBALANCE GAS SWAP1 POP SWAP1 SUB 2 SWAP1 SUB 0x01 SSTORE)
    contract = pre.deploy_contract(
        code=(
            Op.GAS
            + Op.SELFBALANCE
            + Op.GAS
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.SUB
            + Op.PUSH1[0x2]
            + Op.SWAP1
            + Op.SSTORE(key=0x1, value=Op.SUB)
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x20005b9a765d12c8f6ac08c2673b00fa6be00486"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x3635C9ADC5DEA00000)

    EXPECT_ENTRIES: list[dict] = [
        {
            "indexes": {"data": 0, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={1: 5},
                    code=bytes.fromhex("5a475a905090036002900360015500"),
                )
            },
        },
    ]

    post, _exc = resolve_expect_post(EXPECT_ENTRIES, 0, 0, 0, fork)

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=100000,
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
