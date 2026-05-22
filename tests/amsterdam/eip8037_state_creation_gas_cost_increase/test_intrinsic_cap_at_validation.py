"""
Test EIP-8037 intrinsic-or-floor cap at tx validation.

Tests for [EIP-8037: State Creation Gas Cost Increase]
(https://eips.ethereum.org/EIPS/eip-8037).
"""

import pytest
from execution_testing import (
    AccessList,
    Account,
    Address,
    Alloc,
    Fork,
    Op,
    StateTestFiller,
    Transaction,
    TransactionException,
)

from .spec import ref_spec_8037

REFERENCE_SPEC_GIT_PATH = ref_spec_8037.git_path
REFERENCE_SPEC_VERSION = ref_spec_8037.version


@pytest.mark.parametrize(
    "scenario, expected_exception",
    [
        pytest.param(
            "floor_binds",
            TransactionException.INTRINSIC_GAS_TOO_LOW,
            id="floor_binds",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            "intrinsic_binds",
            TransactionException.INTRINSIC_GAS_TOO_LOW,
            id="intrinsic_binds",
            marks=pytest.mark.exception_test,
        ),
        pytest.param("neither_binds", None, id="neither_binds"),
    ],
)
@pytest.mark.parametrize(
    "tx_type",
    [pytest.param(1, id="type_1"), pytest.param(2, id="type_2")],
)
@pytest.mark.valid_from("EIP8037")
def test_intrinsic_or_floor_cap_at_validation(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    tx_type: int,
    scenario: str,
    expected_exception: TransactionException | None,
) -> None:
    """
    Reject when ``max(intrinsic_regular, calldata_floor) > TX_MAX_GAS_LIMIT``.

    Type 0 lacks an access list to vary intrinsic independently of floor;
    type 4 would need thousands of signed authorizations.
    """
    cap = fork.transaction_gas_limit_cap()
    assert cap is not None
    gas_costs = fork.gas_costs()
    floor_per_byte = (
        gas_costs.TX_DATA_TOKEN_FLOOR * gas_costs.TX_DATA_TOKEN_STANDARD
    )

    if scenario == "floor_binds":
        data = b"\x01" * ((cap - gas_costs.TX_BASE) // floor_per_byte + 1)
        access_list = []
    elif scenario == "intrinsic_binds":
        data = b""
        n = (cap - gas_costs.TX_BASE) // gas_costs.TX_ACCESS_LIST_ADDRESS + 1
        access_list = [
            AccessList(address=Address(i + 1), storage_keys=[])
            for i in range(n)
        ]
    else:
        data = b""
        access_list = []

    contract = pre.deploy_contract(Op.STOP)
    sender = pre.fund_eoa()
    tx = Transaction(
        ty=tx_type,
        sender=sender,
        to=contract,
        data=data,
        access_list=access_list,
        gas_limit=cap + 1,
        error=expected_exception,
    )
    post = (
        {sender: Account(nonce=0)}
        if expected_exception
        else {sender: Account(nonce=1)}
    )
    state_test(pre=pre, post=post, tx=tx)
