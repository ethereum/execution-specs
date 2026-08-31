"""
EIP-161 emptiness must be judged by an account's fields alone.

A zero-value CALL to an absent precompile runs its code without creating
the account, so the address stays dead. A client that records the account
on that first touch and later reads its own bookkeeping as proof of
existence skips new-account charges and diverges. Regression tests for
https://github.com/erigontech/erigon/issues/23670.
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Bytecode,
    CodeGasMeasure,
    Fork,
    Op,
    StateTestFiller,
    Storage,
    Transaction,
)

from ethereum.crypto.hash import keccak256

from .spec import ref_spec_161

REFERENCE_SPEC_GIT_PATH = ref_spec_161.git_path
REFERENCE_SPEC_VERSION = ref_spec_161.version


def touch_code(precompile: Address, touch: str) -> Bytecode:
    """Return the same-transaction touch that precedes the probe."""
    if touch == "none":
        return Bytecode()
    if touch == "zero_value_call":
        return Op.POP(Op.CALL(gas=100_000, address=precompile))
    # The value exceeds the caller's balance, so the transfer fails
    # after the target access is charged.
    return Op.POP(Op.CALL(gas=100_000, address=precompile, value=2**100))


@pytest.mark.valid_from("ConstantinopleFix")
@pytest.mark.with_all_precompiles
@pytest.mark.parametrize(
    "touch", ["zero_value_call", "insufficient_value_call"]
)
@pytest.mark.parametrize("funded", [False, True])
def test_extcodehash_after_precompile_touch(
    state_test: StateTestFiller,
    pre: Alloc,
    precompile: Address,
    touch: str,
    funded: bool,
) -> None:
    """
    Probe a precompile's fields after touching it in the same transaction.

    The touch must not make an absent precompile look existent, and must
    not make a funded one look absent.
    """
    storage = Storage()
    if funded:
        pre.fund_address(precompile, 1)
    expected_hash = keccak256(b"") if funded else 0
    expected_balance = 1 if funded else 0

    code = (
        Op.SSTORE(
            storage.store_next(expected_hash, "hash_before"),
            Op.EXTCODEHASH(precompile),
        )
        + touch_code(precompile, touch)
        + Op.SSTORE(
            storage.store_next(expected_hash, "hash_after"),
            Op.EXTCODEHASH(precompile),
        )
        + Op.SSTORE(
            storage.store_next(0, "size_after"),
            Op.EXTCODESIZE(precompile),
        )
        + Op.SSTORE(
            storage.store_next(expected_balance, "balance_after"),
            Op.BALANCE(precompile),
        )
    )
    caller = pre.deploy_contract(code, storage=storage.canary())

    tx = Transaction(sender=pre.fund_eoa(), to=caller)

    post = {
        caller: Account(storage=storage),
        precompile: (Account(balance=1) if funded else Account.NONEXISTENT),
    }
    state_test(pre=pre, post=post, tx=tx)


# Before Berlin the opcode metadata gas model prices account access
# with warm and cold costs that do not exist yet, so the exact-gas tests
# start at Berlin. The probe test above still pins the charge on older
# forks through the sender balance in the state root.
@pytest.mark.valid_from("Berlin")
@pytest.mark.parametrize(
    "precompile,args_size",
    [
        pytest.param(Address(0x01), 0, id="ecrecover"),
        # 15 input words lift the RIPEMD-160 cost above the value
        # stipend, so the callee always runs out of gas.
        pytest.param(Address(0x03), 480, id="ripemd160"),
    ],
)
@pytest.mark.parametrize(
    "touch", ["none", "zero_value_call", "insufficient_value_call"]
)
def test_call_new_account_charge_after_precompile_touch(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    precompile: Address,
    args_size: int,
    touch: str,
) -> None:
    """
    Charge the full value-call cost to a dead precompile that was touched
    earlier in the transaction.

    The measured cost includes the new-account charge while it is
    execution gas. Once it moves to state gas the GAS delta no longer
    sees it, but the fixture still pins it through the sender balance in
    the state root. The zero gas argument makes the callee run on the
    value stipend alone, which is below its precompile cost, so the
    callee always halts and no gas flows back into the measurement.
    """
    storage = Storage()
    measured_call = Op.CALL(
        gas=0,
        address=precompile,
        value=1,
        args_size=args_size,
        value_transfer=True,
        account_new=True,
        address_warm=True,
        new_memory_size=args_size,
    )
    code = touch_code(precompile, touch) + CodeGasMeasure(
        code=measured_call,
        extra_stack_items=1,
        sstore_key=storage.store_next(
            measured_call.execution_cost(fork), "measured_call_cost"
        ),
    )
    caller = pre.deploy_contract(code, balance=1, storage=storage.canary())

    tx = Transaction(sender=pre.fund_eoa(), to=caller)

    post = {
        caller: Account(storage=storage, balance=1),
        precompile: Account.NONEXISTENT,
    }
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("Berlin")
@pytest.mark.parametrize(
    "precompile",
    [
        pytest.param(Address(0x01), id="ecrecover"),
        pytest.param(Address(0x03), id="ripemd160"),
    ],
)
@pytest.mark.parametrize(
    "touch", ["none", "zero_value_call", "insufficient_value_call"]
)
def test_selfdestruct_beneficiary_charge_after_precompile_touch(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    precompile: Address,
    touch: str,
) -> None:
    """
    Charge the beneficiary creation cost when a funded contract
    self-destructs to a dead precompile touched earlier in the
    transaction.

    The measured cost covers the outer call plus the destroyer frame.
    Once the beneficiary creation cost moves to state gas the GAS delta
    no longer sees it, but the fixture still pins it through the sender
    balance in the state root.
    """
    storage = Storage()
    destroyer_code = Op.SELFDESTRUCT(
        precompile, account_new=True, address_warm=True
    )
    destroyer = pre.deploy_contract(destroyer_code, balance=1)

    outer_call = Op.CALL(gas=100_000, address=destroyer)
    code = touch_code(precompile, touch) + CodeGasMeasure(
        code=outer_call,
        extra_stack_items=1,
        sstore_key=storage.store_next(
            outer_call.execution_cost(fork)
            + destroyer_code.execution_cost(fork),
            "destroyer_call_cost",
        ),
    )
    caller = pre.deploy_contract(code, storage=storage.canary())

    tx = Transaction(sender=pre.fund_eoa(), to=caller)

    post = {
        caller: Account(storage=storage),
        precompile: Account(balance=1),
    }
    state_test(pre=pre, post=post, tx=tx)
