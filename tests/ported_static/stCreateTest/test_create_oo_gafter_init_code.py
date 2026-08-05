"""
Test_create_oo_gafter_init_code.

Ported from:
state_tests/stCreateTest/CreateOOGafterInitCodeFiller.json
@manually-enhanced: Do not overwrite. The init code RETURNs a 5-byte
deployed contract; g0 must run out before the deposit (account stays
NONEXISTENT) and g1 must just clear it (account created). On Cancun
the deploy gap is the 1000-gas regular code deposit and the test's
two budgets straddle it. EIP-8037/8038 move account creation into a
spilling state-gas charge AND drop OPCODE_CREATE_BASE, so the budget
that reaches the same RETURN point changes by a fork-derived amount.
The lift restores the straddle: it is exactly 0 pre-EIP-8037 and
tracks the parameters. See `_oog_lift` below for the derivation.
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
from execution_testing.vm import Op

from tests.ported_static.post_state_resolution import (
    resolve_expect_post,
)

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
    # The init code RETURNs a 5-byte deployed contract, so the CREATE
    # frame is charged a code deposit after the init RETURN. On Cancun
    # that deposit is 1000 (CODE_DEPOSIT_PER_BYTE * 5 regular) and the
    # two budgets below straddle it: g0 reaches RETURN just under the
    # threshold (deploy fails, account NONEXISTENT) and g1 just over
    # (deploy succeeds). The 1000-gas gap between the budgets is exactly
    # this Cancun deploy threshold.
    #
    # EIP-8037/8038 change the CREATE dispatch in two ways that the
    # budget must absorb before the init code RETURNs: the new
    # `create_state_gas()` spills into regular gas (empty reservoir),
    # and `OPCODE_CREATE_BASE` drops from its Cancun value of 32000.
    # Their sum is the net extra the dispatch consumes from the budget.
    # The deposit step then changes too: its regular `CODE_DEPOSIT_PER_BYTE
    # * 5` portion is now covered by the state-gas reservoir credited at
    # dispatch, while `code_deposit_state_gas(code_size=5)` spills and
    # must come from the forwarded gas instead. The lift restores the
    # Cancun straddle by funding the net dispatch consumption plus the
    # deposit's state spill, minus the regular deposit the budgets
    # already carried in their 1000-gas gap. Every term is 0
    # pre-EIP-8037, so the original Cancun behavior is preserved.
    gas_costs = fork.gas_costs()
    _cancun_create_base = 32000
    _deploy_size = 5
    _oog_lift = 0
    if fork.is_eip_enabled(8037):
        _oog_lift = (
            fork.oog_budget_lift(
                creates_before_oog=1, deploy_code_size=_deploy_size
            )
            + (gas_costs.OPCODE_CREATE_BASE - _cancun_create_base)
            - gas_costs.CODE_DEPOSIT_PER_BYTE * _deploy_size
        )
    # EIP-2780 reshapes the tx intrinsic for non-self non-value txs:
    # ``TX_BASE`` drops to 12_000 and an explicit
    # ``COLD_ACCOUNT_ACCESS`` (3_000) recipient charge is added. The
    # original test was built against Cancun's flat ``TX_BASE`` of
    # 21_000, so shift the budget by the intrinsic delta to keep the
    # straddle landing at the same RETURN point.
    intrinsic = fork.transaction_intrinsic_cost_calculator()()
    _oog_lift += intrinsic - 21_000
    tx_gas = [54000 + _oog_lift, 55000 + _oog_lift]

    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
