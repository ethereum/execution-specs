"""
Call RETURNDATASIZE and RETURNDATACOPY after CREATE deploy a contract....

Ported from:
state_tests/stCreateTest/CreateOOGafterInitCodeReturndata2Filler.json
@manually-enhanced: Do not overwrite. tx_gas[1] is tuned to barely
finish CREATE + two post-deploy SSTOREs on Cancun; on Amsterdam the
NEW_ACCOUNT and SSTORE-set state-gas spills, so lift the budget by
Fork.oog_budget_lift.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytes,
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
    ["state_tests/stCreateTest/CreateOOGafterInitCodeReturndata2Filler.json"],
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
def test_create_oo_gafter_init_code_returndata2(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Call RETURNDATASIZE and RETURNDATACOPY after CREATE deploy a contract."""  # noqa: E501
    sender = pre.fund_eoa(amount=0xE8D4A51000)

    # Source: lll
    # { (MSTORE 0 0x6460016001556000526005601bf3) (CREATE 0 18 14) [[ 1 ]] (RETURNDATASIZE) (RETURNDATACOPY 0 0 0) [[ 2 ]] (MLOAD 0) }  # noqa: E501
    contract_0 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x0, value=0x6460016001556000526005601BF3)
        + Op.POP(Op.CREATE(value=0x0, offset=0x12, size=0xE))
        + Op.SSTORE(key=0x1, value=Op.RETURNDATASIZE)
        + Op.RETURNDATACOPY(dest_offset=0x0, offset=0x0, size=0x0)
        + Op.SSTORE(key=0x2, value=Op.MLOAD(offset=0x0))
        + Op.STOP,
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": -1, "gas": 0, "value": -1},
            "network": [">=Cancun"],
            "result": {
                contract_0: Account(storage={1: 0}),
                compute_create_address(
                    address=contract_0, nonce=1
                ): Account.NONEXISTENT,
            },
        },
        {
            "indexes": {"data": -1, "gas": 1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                contract_0: Account(
                    storage={1: 0, 2: 0x6460016001556000526005601BF3}
                ),
                compute_create_address(address=contract_0, nonce=1): Account(
                    code=bytes.fromhex("6001600155")
                ),
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx_data = [
        Bytes(""),
    ]
    tx_gas = [
        54000,
        95000
        + fork.oog_budget_lift(creates_before_oog=1, sstores_before_oog=2),
    ]

    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        error=_exc,
    )

    state_test(pre=pre, post=post, tx=tx)
