"""
CALL a contract that SELFDESTRUCTs without balance, in a transaction that runs
out of gas.

Ported from:
state_tests/stZeroCallsRevert/ZeroValue_SUICIDE_OOGRevertFiller.json
state_tests/stZeroCallsRevert/ZeroValue_SUICIDE_ToEmpty_OOGRevert_ParisFiller.json
state_tests/stZeroCallsRevert/ZeroValue_SUICIDE_ToNonZeroBalance_OOGRevertFiller.json
state_tests/stZeroCallsRevert/ZeroValue_SUICIDE_ToOneStorageKey_OOGRevert_ParisFiller.json

@manually-enhanced: Do not overwrite. Four fillers in one file; the three with
an EOA beneficiary are parametrized by recipient.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    StateTestFiller,
    Storage,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stZeroCallsRevert/ZeroValue_SUICIDE_OOGRevertFiller.json"],
)
@pytest.mark.valid_from("Cancun")
def test_zero_value_suicide_oog_revert(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """CALL a contract that SELFDESTRUCTs to itself, then run out of gas."""
    sender = pre.fund_eoa()

    # Source: lll
    # { (SELFDESTRUCT <contract:0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b>)  }
    addr = pre.deploy_contract(
        code=Op.SELFDESTRUCT(address=Op.ADDRESS) + Op.STOP,
    )
    # Source: lll
    # { (CALL 40000 <contract:0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b> 0 0 0 0 0) [[2]]12 [[3]]12 [[4]]12 [[100]](GAS) }  # noqa: E501
    target = pre.deploy_contract(
        code=Op.POP(Op.CALL(gas=0x9C40, address=addr))
        + Op.SSTORE(key=0x2, value=0xC)
        + Op.SSTORE(key=0x3, value=0xC)
        + Op.SSTORE(key=0x4, value=0xC)
        + Op.SSTORE(key=0x64, value=Op.GAS)
        + Op.STOP,
    )

    tx = Transaction(
        sender=sender,
        to=target,
        gas_limit=100000,
    )

    post = {
        sender: Account(nonce=1),
        target: Account(storage={}),
        addr: Account(storage={}),
    }

    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    [
        "state_tests/stZeroCallsRevert/ZeroValue_SUICIDE_ToEmpty_OOGRevert_ParisFiller.json",  # noqa: E501
        "state_tests/stZeroCallsRevert/ZeroValue_SUICIDE_ToNonZeroBalance_OOGRevertFiller.json",  # noqa: E501
        "state_tests/stZeroCallsRevert/ZeroValue_SUICIDE_ToOneStorageKey_OOGRevert_ParisFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "recipient",
    [
        "funded_eoa",
        pytest.param("eoa_with_storage", marks=pytest.mark.pre_alloc_mutable),
    ],
)
def test_zero_value_suicide_to_eoa_oog_revert(
    state_test: StateTestFiller,
    pre: Alloc,
    recipient: str,
) -> None:
    """CALL a contract that SELFDESTRUCTs to `recipient`, then go OOG."""
    sender = pre.fund_eoa()
    storage = Storage()
    if recipient == "eoa_with_storage":
        storage[0] = 1
        beneficiary = pre.fund_eoa(storage=storage, nonce=0)
    else:
        beneficiary = pre.fund_eoa()

    # Source: lll
    # { (SELFDESTRUCT <eoa:0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b>) }
    addr = pre.deploy_contract(
        code=Op.SELFDESTRUCT(address=beneficiary) + Op.STOP,
        storage=storage,
    )
    # Source: lll
    # { (CALL 50000 <contract:0xd94f5374fce5edbc8e2a8697c15331677e6ebf0b> 0 0 0 0 0) [[2]]12 [[3]]12 [[4]]12 }  # noqa: E501
    target = pre.deploy_contract(
        code=Op.POP(Op.CALL(gas=0xC350, address=addr))
        + Op.SSTORE(key=0x2, value=0xC)
        + Op.SSTORE(key=0x3, value=0xC)
        + Op.SSTORE(key=0x4, value=0xC)
        + Op.STOP,
        storage=storage,
    )

    tx = Transaction(
        sender=sender,
        to=target,
        gas_limit=75000,
    )

    post = {
        sender: Account(nonce=1),
        target: Account(storage=storage),
        beneficiary: Account(storage=storage, balance_change=0),
    }

    state_test(pre=pre, post=post, tx=tx)
