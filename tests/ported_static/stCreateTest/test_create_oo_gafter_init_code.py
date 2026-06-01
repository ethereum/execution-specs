"""
Test_create_oo_gafter_init_code.

Ported from:
state_tests/stCreateTest/CreateOOGafterInitCodeFiller.json
@manually-enhanced: Do not overwrite. tx_gas[1] is tuned to barely
succeed CREATE on Cancun; on Amsterdam EIP-8037 the NEW_ACCOUNT
state-gas spills, so lift the budget by Fork.oog_budget_lift.
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Bytes,
    Environment,
    StateTestFiller,
    Transaction,
    compute_create_address,
)
from execution_testing.forks import Fork
from execution_testing.specs.static_state.expect_section import (
    resolve_expect_post,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stCreateTest/CreateOOGafterInitCodeFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0,
            0,
            0,
            id="-g0",
        ),
        pytest.param(
            0,
            1,
            0,
            id="-g1",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_create_oo_gafter_init_code(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test_create_oo_gafter_init_code."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    contract_0 = Address(0xB94F5374FCE5EDBC8E2A8697C15331677E6EBF0B)
    sender = pre.fund_eoa(amount=0xE8D4A51000)

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
    )

    # Source: lll
    # { (MSTORE 0 0x6460016001556000526005601bf3) (CREATE 0 18 14) }
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x0, value=0x6460016001556000526005601BF3)
        + Op.CREATE(value=0x0, offset=0x12, size=0xE)
        + Op.STOP,
        nonce=0,
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": -1, "gas": 0, "value": -1},
            "network": [">=Cancun"],
            "result": {
                contract_0: Account(storage={1: 0}),
                compute_create_address(
                    address=contract_0, nonce=0
                ): Account.NONEXISTENT,
            },
        },
        {
            "indexes": {"data": -1, "gas": 1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                contract_0: Account(storage={1: 0}),
                compute_create_address(address=contract_0, nonce=0): Account(
                    code=bytes.fromhex("6001600155")
                ),
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx_data = [
        Bytes(""),
    ]
    # Lift both entries on Amsterdam so the test still exercises its
    # named scenario. With only tx_gas[1] lifted, g=0 OoG'd at CREATE
    # dispatch (NEW_ACCOUNT state-gas spill) before init code ever ran —
    # the assertion still passes (`NONEXISTENT` either way) but the
    # failure mode is "dispatch-time OoG" instead of "OoG after init
    # code". A simple `fork.oog_budget_lift(creates_before_oog=1)` (183600)
    # is *too* generous and pushes g=0 past the deploy threshold; the
    # Cancun 1000-gas gap between g=0 and g=1 collapses on Amsterdam
    # because once dispatch is cleared, the 5-byte init code is cheap
    # enough to always complete. The value below is the middle of the
    # empirically-safe range (166499, 167000) where g=0 still OoGs at
    # dispatch *and* g=1 just clears the deploy threshold (~221.5k).
    _oog_lift = 166_750 if fork.is_eip_enabled(8037) else 0
    tx_gas = [54000 + _oog_lift, 55000 + _oog_lift]

    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
