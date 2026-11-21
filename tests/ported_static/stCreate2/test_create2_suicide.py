"""
CREATE2 suicide with/without value, CREATE2 suicide to itself.

Self-destruct either in the init code or in deployed code that is then
called (or static-called, where SELFDESTRUCT fails).

Ported from:
state_tests/stCreate2/CREATE2_SuicideFiller.json
@manually-enhanced: Do not overwrite. Rewritten by hand; tx `gas_limit`
removed.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytecode,
    Fork,
    StateTestFiller,
    Transaction,
    compute_create_address,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stCreate2/CREATE2_SuicideFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize("create_value", [0, 1])
@pytest.mark.parametrize("mode", ["init", "call", "staticcall"])
@pytest.mark.parametrize("beneficiary_kind", ["other", "self"])
def test_create2_suicide(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    beneficiary_kind: str,
    mode: str,
    create_value: int,
) -> None:
    """CREATE2 a contract that self-destructs to itself or another."""
    sender = pre.fund_eoa()
    beneficiary = pre.nonexistent_account()
    tx_value = 10

    suicide: Bytecode
    if beneficiary_kind == "self":
        suicide = Op.SELFDESTRUCT(address=Op.ADDRESS)
    else:
        suicide = Op.SELFDESTRUCT(address=beneficiary)

    initcode: Bytecode
    if mode == "init":
        initcode = suicide
    else:
        initcode = Op.MSTORE(
            offset=0, value=int.from_bytes(bytes(suicide), "big")
        ) + Op.RETURN(offset=32 - len(suicide), size=len(suicide))
    assert len(initcode) <= 32

    creator = compute_create_address(address=sender, nonce=0)
    created = compute_create_address(
        address=creator, salt=0, initcode=initcode, opcode=Op.CREATE2
    )
    create = Op.MSTORE(
        offset=0, value=int.from_bytes(bytes(initcode), "big")
    ) + Op.CREATE2(
        value=create_value,
        offset=32 - len(initcode),
        size=len(initcode),
        salt=0,
    )
    tx_data: Bytecode
    if mode == "init":
        tx_data = create + Op.STOP
    elif mode == "call":
        tx_data = Op.CALL(address=create) + Op.STOP
    elif mode == "staticcall":
        tx_data = Op.STATICCALL(address=create) + Op.STOP
    else:
        raise ValueError(f"Unknown mode: {mode}")

    post: dict = {
        sender: Account(nonce=1),
        creator: Account(nonce=2, balance=tx_value - create_value),
    }
    if beneficiary_kind == "other":
        post[beneficiary] = (
            Account(balance=create_value)
            if create_value and mode != "staticcall"
            else Account.NONEXISTENT
        )
    if mode == "staticcall":
        post[created] = Account(code=suicide, balance=create_value, nonce=1)
    elif (
        beneficiary_kind == "self"
        and create_value
        and fork.is_eip_enabled(8246)
    ):
        post[created] = Account(
            balance=create_value, nonce=0, code=b"", storage={}
        )
    else:
        post[created] = Account.NONEXISTENT

    tx = Transaction(sender=sender, to=None, data=tx_data, value=tx_value)

    state_test(pre=pre, post=post, tx=tx)
