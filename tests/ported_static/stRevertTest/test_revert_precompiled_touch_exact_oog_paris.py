"""
Test_revert_precompiled_touch_exact_oog_paris.

Ported from:
state_tests/stRevertTest/RevertPrecompiledTouchExactOOG_ParisFiller.json
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Hash,
    StateTestFiller,
    Transaction,
)
from execution_testing.forks import Fork, Prague
from execution_testing.vm import Op

from tests.ported_static.post_state_resolution import (
    resolve_expect_post,
)

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    [
        "state_tests/stRevertTest/RevertPrecompiledTouchExactOOG_ParisFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0,
            0,
            0,
            id="d0-g0",
        ),
        pytest.param(
            0,
            1,
            0,
            id="d0-g1",
        ),
        pytest.param(
            0,
            2,
            0,
            id="d0-g2",
        ),
        pytest.param(
            1,
            0,
            0,
            id="d1-g0",
        ),
        pytest.param(
            1,
            1,
            0,
            id="d1-g1",
        ),
        pytest.param(
            1,
            2,
            0,
            id="d1-g2",
        ),
        pytest.param(
            2,
            0,
            0,
            id="d2-g0",
        ),
        pytest.param(
            2,
            1,
            0,
            id="d2-g1",
        ),
        pytest.param(
            2,
            2,
            0,
            id="d2-g2",
        ),
        pytest.param(
            3,
            0,
            0,
            id="d3-g0",
        ),
        pytest.param(
            3,
            1,
            0,
            id="d3-g1",
        ),
        pytest.param(
            3,
            2,
            0,
            id="d3-g2",
        ),
        pytest.param(
            4,
            0,
            0,
            id="d4-g0",
        ),
        pytest.param(
            4,
            1,
            0,
            id="d4-g1",
        ),
        pytest.param(
            4,
            2,
            0,
            id="d4-g2",
        ),
        pytest.param(
            5,
            0,
            0,
            id="d5-g0",
        ),
        pytest.param(
            5,
            1,
            0,
            id="d5-g1",
        ),
        pytest.param(
            5,
            2,
            0,
            id="d5-g2",
        ),
        pytest.param(
            6,
            0,
            0,
            id="d6-g0",
        ),
        pytest.param(
            6,
            1,
            0,
            id="d6-g1",
        ),
        pytest.param(
            6,
            2,
            0,
            id="d6-g2",
        ),
        pytest.param(
            7,
            0,
            0,
            id="d7-g0",
        ),
        pytest.param(
            7,
            1,
            0,
            id="d7-g1",
        ),
        pytest.param(
            7,
            2,
            0,
            id="d7-g2",
        ),
        pytest.param(
            8,
            0,
            0,
            id="d8-g0",
        ),
        pytest.param(
            8,
            1,
            0,
            id="d8-g1",
        ),
        pytest.param(
            8,
            2,
            0,
            id="d8-g2",
        ),
        pytest.param(
            9,
            0,
            0,
            id="d9-g0",
        ),
        pytest.param(
            9,
            1,
            0,
            id="d9-g1",
        ),
        pytest.param(
            9,
            2,
            0,
            id="d9-g2",
        ),
        pytest.param(
            10,
            0,
            0,
            id="d10-g0",
        ),
        pytest.param(
            10,
            1,
            0,
            id="d10-g1",
        ),
        pytest.param(
            10,
            2,
            0,
            id="d10-g2",
        ),
        pytest.param(
            11,
            0,
            0,
            id="d11-g0",
        ),
        pytest.param(
            11,
            1,
            0,
            id="d11-g1",
        ),
        pytest.param(
            11,
            2,
            0,
            id="d11-g2",
        ),
        pytest.param(
            12,
            0,
            0,
            id="d12-g0",
        ),
        pytest.param(
            12,
            1,
            0,
            id="d12-g1",
        ),
        pytest.param(
            12,
            2,
            0,
            id="d12-g2",
        ),
        pytest.param(
            13,
            0,
            0,
            id="d13-g0",
        ),
        pytest.param(
            13,
            1,
            0,
            id="d13-g1",
        ),
        pytest.param(
            13,
            2,
            0,
            id="d13-g2",
        ),
        pytest.param(
            14,
            0,
            0,
            id="d14-g0",
        ),
        pytest.param(
            14,
            1,
            0,
            id="d14-g1",
        ),
        pytest.param(
            14,
            2,
            0,
            id="d14-g2",
        ),
        pytest.param(
            15,
            0,
            0,
            id="d15-g0",
        ),
        pytest.param(
            15,
            1,
            0,
            id="d15-g1",
        ),
        pytest.param(
            15,
            2,
            0,
            id="d15-g2",
        ),
        pytest.param(
            16,
            0,
            0,
            id="d16-g0",
        ),
        pytest.param(
            16,
            1,
            0,
            id="d16-g1",
        ),
        pytest.param(
            16,
            2,
            0,
            id="d16-g2",
        ),
        pytest.param(
            17,
            0,
            0,
            id="d17-g0",
        ),
        pytest.param(
            17,
            1,
            0,
            id="d17-g1",
        ),
        pytest.param(
            17,
            2,
            0,
            id="d17-g2",
        ),
        pytest.param(
            18,
            0,
            0,
            id="d18-g0",
        ),
        pytest.param(
            18,
            1,
            0,
            id="d18-g1",
        ),
        pytest.param(
            18,
            2,
            0,
            id="d18-g2",
        ),
        pytest.param(
            19,
            0,
            0,
            id="d19-g0",
        ),
        pytest.param(
            19,
            1,
            0,
            id="d19-g1",
        ),
        pytest.param(
            19,
            2,
            0,
            id="d19-g2",
        ),
        pytest.param(
            20,
            0,
            0,
            id="d20-g0",
        ),
        pytest.param(
            20,
            1,
            0,
            id="d20-g1",
        ),
        pytest.param(
            20,
            2,
            0,
            id="d20-g2",
        ),
        pytest.param(
            21,
            0,
            0,
            id="d21-g0",
        ),
        pytest.param(
            21,
            1,
            0,
            id="d21-g1",
        ),
        pytest.param(
            21,
            2,
            0,
            id="d21-g2",
        ),
        pytest.param(
            22,
            0,
            0,
            id="d22-g0",
        ),
        pytest.param(
            22,
            1,
            0,
            id="d22-g1",
        ),
        pytest.param(
            22,
            2,
            0,
            id="d22-g2",
        ),
        pytest.param(
            23,
            0,
            0,
            id="d23-g0",
        ),
        pytest.param(
            23,
            1,
            0,
            id="d23-g1",
        ),
        pytest.param(
            23,
            2,
            0,
            id="d23-g2",
        ),
        pytest.param(
            24,
            0,
            0,
            id="d24-g0",
        ),
        pytest.param(
            24,
            1,
            0,
            id="d24-g1",
        ),
        pytest.param(
            24,
            2,
            0,
            id="d24-g2",
        ),
        pytest.param(
            25,
            0,
            0,
            id="d25-g0",
        ),
        pytest.param(
            25,
            1,
            0,
            id="d25-g1",
        ),
        pytest.param(
            25,
            2,
            0,
            id="d25-g2",
        ),
        pytest.param(
            26,
            0,
            0,
            id="d26-g0",
        ),
        pytest.param(
            26,
            1,
            0,
            id="d26-g1",
        ),
        pytest.param(
            26,
            2,
            0,
            id="d26-g2",
        ),
        pytest.param(
            27,
            0,
            0,
            id="d27-g0",
        ),
        pytest.param(
            27,
            1,
            0,
            id="d27-g1",
        ),
        pytest.param(
            27,
            2,
            0,
            id="d27-g2",
        ),
        pytest.param(
            28,
            0,
            0,
            id="d28-g0",
        ),
        pytest.param(
            28,
            1,
            0,
            id="d28-g1",
        ),
        pytest.param(
            28,
            2,
            0,
            id="d28-g2",
        ),
        pytest.param(
            29,
            0,
            0,
            id="d29-g0",
        ),
        pytest.param(
            29,
            1,
            0,
            id="d29-g1",
        ),
        pytest.param(
            29,
            2,
            0,
            id="d29-g2",
        ),
        pytest.param(
            30,
            0,
            0,
            id="d30-g0",
        ),
        pytest.param(
            30,
            1,
            0,
            id="d30-g1",
        ),
        pytest.param(
            30,
            2,
            0,
            id="d30-g2",
        ),
        pytest.param(
            31,
            0,
            0,
            id="d31-g0",
        ),
        pytest.param(
            31,
            1,
            0,
            id="d31-g1",
        ),
        pytest.param(
            31,
            2,
            0,
            id="d31-g2",
        ),
    ],
)
def test_revert_precompiled_touch_exact_oog_paris(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test_revert_precompiled_touch_exact_oog_paris."""
    precompile_1 = Address(0x0000000000000000000000000000000000000001)
    precompile_2 = Address(0x0000000000000000000000000000000000000002)
    precompile_3 = Address(0x0000000000000000000000000000000000000003)
    precompile_4 = Address(0x0000000000000000000000000000000000000004)
    precompile_5 = Address(0x0000000000000000000000000000000000000005)
    precompile_6 = Address(0x0000000000000000000000000000000000000006)
    precompile_7 = Address(0x0000000000000000000000000000000000000007)
    precompile_8 = Address(0x0000000000000000000000000000000000000008)
    sender = pre.fund_eoa()

    pre.fund_address(precompile_1, amount=1)
    pre.fund_address(precompile_2, amount=1)
    pre.fund_address(precompile_3, amount=1)
    pre.fund_address(precompile_4, amount=1)
    pre.fund_address(precompile_5, amount=1)
    pre.fund_address(precompile_6, amount=1)
    pre.fund_address(precompile_7, amount=1)
    pre.fund_address(precompile_8, amount=1)

    # Source: lll
    # {  (CALLCODE (GAS) (CALLDATALOAD 0) 0 0 (CALLDATALOAD 32) 0 0) }
    target = pre.deploy_contract(
        code=Op.CALLCODE(
            gas=Op.GAS,
            address=Op.CALLDATALOAD(offset=0x0),
            value=0x0,
            args_offset=0x0,
            args_size=Op.CALLDATALOAD(offset=0x20),
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
    )
    # Source: lll
    # { (CALL (GAS) (CALLDATASIZE) 0 0 0 0 0) }
    addr = pre.deploy_contract(
        code=Op.CALL(
            gas=Op.GAS,
            address=Op.CALLDATASIZE,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
    )
    # Source: lll
    # { (DELEGATECALL (GAS) (CALLDATASIZE) 0 0 0 0) }
    addr_2 = pre.deploy_contract(
        code=Op.DELEGATECALL(
            gas=Op.GAS,
            address=Op.CALLDATASIZE,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
    )
    # Source: lll
    # { (CALLCODE (GAS) (CALLDATASIZE) 0 0 0 0 0) }
    addr_3 = pre.deploy_contract(
        code=Op.CALLCODE(
            gas=Op.GAS,
            address=Op.CALLDATASIZE,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
    )
    # Source: lll
    # { (STATICCALL (GAS) (CALLDATASIZE) 0 0 0 0)  }
    addr_4 = pre.deploy_contract(
        code=Op.STATICCALL(
            gas=Op.GAS,
            address=Op.CALLDATASIZE,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": [0, 8, 16, 24], "gas": 0, "value": -1},
            "network": [">=Cancun"],
            "result": {precompile_1: Account(nonce=0)},
        },
        {
            "indexes": {"data": [1, 25, 9, 17], "gas": 0, "value": -1},
            "network": [">=Cancun"],
            "result": {precompile_2: Account(nonce=0)},
        },
        {
            "indexes": {"data": [18, 26, 2, 10], "gas": 0, "value": -1},
            "network": [">=Cancun"],
            "result": {precompile_3: Account(nonce=0)},
        },
        {
            "indexes": {"data": [11, 19, 3, 27], "gas": 0, "value": -1},
            "network": [">=Cancun"],
            "result": {precompile_4: Account(nonce=0)},
        },
        {
            "indexes": {"data": [20, 28, 4, 12], "gas": 0, "value": -1},
            "network": [">=Cancun"],
            "result": {precompile_5: Account(nonce=0)},
        },
        {
            "indexes": {"data": [29, 13, 21, 5], "gas": 0, "value": -1},
            "network": [">=Cancun"],
            "result": {precompile_6: Account(nonce=0)},
        },
        {
            "indexes": {"data": [22, 30, 6, 14], "gas": 0, "value": -1},
            "network": [">=Cancun"],
            "result": {precompile_7: Account(nonce=0)},
        },
        {
            "indexes": {"data": [31, 15, 23, 7], "gas": 0, "value": -1},
            "network": [">=Cancun"],
            "result": {precompile_8: Account(nonce=0)},
        },
        {
            "indexes": {"data": [8, 16], "gas": [1, 2], "value": -1},
            "network": [">=Cancun"],
            "result": {precompile_1: Account(nonce=0)},
        },
        {
            "indexes": {"data": [0, 24], "gas": [1, 2], "value": -1},
            "network": [">=Cancun"],
            "result": {precompile_1: Account(nonce=0)},
        },
        {
            "indexes": {"data": [9, 17], "gas": [1, 2], "value": -1},
            "network": [">=Cancun"],
            "result": {precompile_2: Account(nonce=0)},
        },
        {
            "indexes": {"data": [1, 25], "gas": [1, 2], "value": -1},
            "network": [">=Cancun"],
            "result": {precompile_2: Account(nonce=0)},
        },
        {
            "indexes": {"data": [10, 18], "gas": [1, 2], "value": -1},
            "network": [">=Cancun"],
            "result": {precompile_3: Account(nonce=0)},
        },
        {
            "indexes": {"data": [2, 26], "gas": [1, 2], "value": -1},
            "network": [">=Cancun"],
            "result": {precompile_3: Account(nonce=0)},
        },
        {
            "indexes": {"data": [19, 11], "gas": [1, 2], "value": -1},
            "network": [">=Cancun"],
            "result": {precompile_4: Account(nonce=0)},
        },
        {
            "indexes": {"data": [27, 3], "gas": [1, 2], "value": -1},
            "network": [">=Cancun"],
            "result": {precompile_4: Account(nonce=0)},
        },
        {
            "indexes": {"data": [12, 20], "gas": [1, 2], "value": -1},
            "network": [">=Cancun"],
            "result": {precompile_5: Account(nonce=0)},
        },
        {
            "indexes": {"data": [4, 28], "gas": [1, 2], "value": -1},
            "network": [">=Cancun"],
            "result": {precompile_5: Account(nonce=0)},
        },
        {
            "indexes": {"data": [21, 13], "gas": [1, 2], "value": -1},
            "network": [">=Cancun"],
            "result": {precompile_6: Account(nonce=0)},
        },
        {
            "indexes": {"data": [29, 5], "gas": [1, 2], "value": -1},
            "network": [">=Cancun"],
            "result": {precompile_6: Account(nonce=0)},
        },
        {
            "indexes": {"data": [14, 22], "gas": [1, 2], "value": -1},
            "network": [">=Cancun"],
            "result": {precompile_7: Account(nonce=0)},
        },
        {
            "indexes": {"data": [6, 30], "gas": [1, 2], "value": -1},
            "network": [">=Cancun"],
            "result": {precompile_7: Account(nonce=0)},
        },
        {
            "indexes": {"data": [23, 15], "gas": [1, 2], "value": -1},
            "network": [">=Cancun"],
            "result": {precompile_8: Account(nonce=0)},
        },
        {
            "indexes": {"data": [31, 7], "gas": 2, "value": -1},
            "network": [">=Cancun"],
            "result": {precompile_8: Account(nonce=0)},
        },
        {
            "indexes": {"data": [31, 7], "gas": 1, "value": -1},
            "network": [">=Cancun"],
            "result": {precompile_8: Account(nonce=0)},
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx_data = [
        Hash(addr, left_padding=True) + Hash(precompile_1, left_padding=True),
        Hash(addr, left_padding=True) + Hash(precompile_2, left_padding=True),
        Hash(addr, left_padding=True) + Hash(precompile_3, left_padding=True),
        Hash(addr, left_padding=True) + Hash(precompile_4, left_padding=True),
        Hash(addr, left_padding=True) + Hash(precompile_5, left_padding=True),
        Hash(addr, left_padding=True) + Hash(precompile_6, left_padding=True),
        Hash(addr, left_padding=True) + Hash(precompile_7, left_padding=True),
        Hash(addr, left_padding=True) + Hash(precompile_8, left_padding=True),
        Hash(addr_2, left_padding=True)
        + Hash(precompile_1, left_padding=True),
        Hash(addr_2, left_padding=True)
        + Hash(precompile_2, left_padding=True),
        Hash(addr_2, left_padding=True)
        + Hash(precompile_3, left_padding=True),
        Hash(addr_2, left_padding=True)
        + Hash(precompile_4, left_padding=True),
        Hash(addr_2, left_padding=True)
        + Hash(precompile_5, left_padding=True),
        Hash(addr_2, left_padding=True)
        + Hash(precompile_6, left_padding=True),
        Hash(addr_2, left_padding=True)
        + Hash(precompile_7, left_padding=True),
        Hash(addr_2, left_padding=True)
        + Hash(precompile_8, left_padding=True),
        Hash(addr_3, left_padding=True)
        + Hash(precompile_1, left_padding=True),
        Hash(addr_3, left_padding=True)
        + Hash(precompile_2, left_padding=True),
        Hash(addr_3, left_padding=True)
        + Hash(precompile_3, left_padding=True),
        Hash(addr_3, left_padding=True)
        + Hash(precompile_4, left_padding=True),
        Hash(addr_3, left_padding=True)
        + Hash(precompile_5, left_padding=True),
        Hash(addr_3, left_padding=True)
        + Hash(precompile_6, left_padding=True),
        Hash(addr_3, left_padding=True)
        + Hash(precompile_7, left_padding=True),
        Hash(addr_3, left_padding=True)
        + Hash(precompile_8, left_padding=True),
        Hash(addr_4, left_padding=True)
        + Hash(precompile_1, left_padding=True),
        Hash(addr_4, left_padding=True)
        + Hash(precompile_2, left_padding=True),
        Hash(addr_4, left_padding=True)
        + Hash(precompile_3, left_padding=True),
        Hash(addr_4, left_padding=True)
        + Hash(precompile_4, left_padding=True),
        Hash(addr_4, left_padding=True)
        + Hash(precompile_5, left_padding=True),
        Hash(addr_4, left_padding=True)
        + Hash(precompile_6, left_padding=True),
        Hash(addr_4, left_padding=True)
        + Hash(precompile_7, left_padding=True),
        Hash(addr_4, left_padding=True)
        + Hash(precompile_8, left_padding=True),
    ]
    # The original ported test uses gas_limit tuned for an exact-OOG
    # boundary on the CALLCODE-to-precompile path. EIP-7976 bumps the
    # calldata floor cost per token from 10 to 16 (Amsterdam, with
    # 8037), which would push the floor above the tightest budget.
    # Shift gas_limit by the intrinsic delta so the same execution
    # budget is preserved on every fork. The baseline is the filler's
    # calldata, whose dispatcher address `0x1000...` has one nonzero byte.
    current_intrinsic = fork.transaction_intrinsic_cost_calculator()(
        calldata=tx_data[d]
    )
    baseline_intrinsic = Prague.transaction_intrinsic_cost_calculator()(
        calldata=Hash(0x1000000000000000000000000000000000000000) + Hash(0x1)
    )
    intrinsic_delta = current_intrinsic - baseline_intrinsic
    tx_gas = [
        22500 + intrinsic_delta,
        120000 + intrinsic_delta,
        69000 + intrinsic_delta,
    ]

    floor_cost = fork.transaction_data_floor_cost_calculator()(data=tx_data[d])
    tx = Transaction(
        sender=sender,
        to=target,
        data=tx_data[d],
        gas_limit=max(tx_gas[g], floor_cost),
        error=_exc,
    )

    state_test(pre=pre, post=post, tx=tx)
