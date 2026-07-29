"""
Verify the EIP-150 repriced code/account operations in one frame:
EXTCODESIZE, EXTCODECOPY, SLOAD, failing value CALL/CALLCODE (insufficient
balance), DELEGATECALL that writes the caller's storage, a call to a
nonexistent account, BALANCE, and the whole window's measured gas.

Ported from:
state_tests/stEIP150Specific/NewGasPriceForCodesFiller.json

@manually-enhanced: Do not overwrite. The ported bytecode shape is kept,
but the window delta, the mid-execution sender balance, and the copied
code word are derived (opcode metadata, fee formula, the deployed bytes);
the delegate's budget is derived so its store — state-priced under
EIP-8037 — fits inside the grant (a reservoir-less sub-call pays state
gas from its regular grant); each failed value call returns its stipend.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Fork,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

EXTCODE_BYTES = bytes.fromhex(
    "1122334455667788991011121314151617181920212223242526272829303132"
)
COPY_SIZE = 0x14
DELEGATE_VALUE = 0x11
# Budget for the calls whose outcome does not depend on it (the value
# calls fail on insufficient balance; the absent target runs nothing).
FORWARDED_GAS = 0x7530
GAS_PRICE = 10
INITIAL_BALANCE = 10**15


@pytest.mark.ported_from(
    ["state_tests/stEIP150Specific/NewGasPriceForCodesFiller.json"],
)
@pytest.mark.valid_from("Berlin")
def test_new_gas_price_for_codes(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Measure a frame exercising every repriced code/account operation."""
    sender = pre.fund_eoa(amount=INITIAL_BALANCE)
    code_target = pre.deploy_contract(code=EXTCODE_BYTES, balance=111)
    delegate_store = Op.SSTORE(
        key=0x64,
        value=DELEGATE_VALUE,
        key_warm=False,
        original_value=0,
        new_value=DELEGATE_VALUE,
    )
    storage_writer = pre.deploy_contract(code=delegate_store + Op.STOP)
    absent = pre.nonexistent_account()

    # The delegate must succeed: with a zero reservoir its state-priced
    # store is paid from the regular grant, so the budget is derived.
    delegate_budget = delegate_store.gas_cost(fork) + 2_000

    # The measured window: entry GAS snapshot through the closing GAS.
    # The value-bearing CALL and CALLCODE fail on insufficient balance
    # (this contract holds nothing), costing their access and transfer
    # charges minus the returned stipend; the DELEGATECALL runs the
    # writer against this contract's storage.
    window = (
        Op.MSTORE(offset=0x3E7, value=Op.GAS, new_memory_size=0x407)
        + Op.SSTORE(
            key=0x1,
            value=Op.EXTCODESIZE(address=code_target, address_warm=False),
            key_warm=False,
            original_value=0,
            new_value=1,
        )
        + Op.EXTCODECOPY(
            address=code_target,
            dest_offset=0x0,
            offset=0x0,
            size=COPY_SIZE,
            address_warm=True,
            data_size=COPY_SIZE,
            new_memory_size=0x407,
            old_memory_size=0x407,
        )
        + Op.SSTORE(
            key=0x2,
            value=Op.MLOAD(offset=0x0),
            key_warm=False,
            original_value=0,
            new_value=1,
        )
        + Op.SSTORE(
            key=0x4,
            value=Op.SLOAD(key=0x0, key_warm=False),
            key_warm=False,
            original_value=0,
            new_value=1,
        )
        + Op.SSTORE(
            key=0x5,
            value=Op.CALL(
                gas=FORWARDED_GAS,
                address=storage_writer,
                value=0x1,
                address_warm=False,
                value_transfer=True,
                account_new=False,
            ),
            key_warm=False,
            original_value=0,
            new_value=0,
        )
        + Op.SSTORE(
            key=0x6,
            value=Op.CALLCODE(
                gas=FORWARDED_GAS,
                address=storage_writer,
                value=0x1,
                address_warm=True,
                value_transfer=True,
                account_new=False,
            ),
            key_warm=False,
            original_value=0,
            new_value=0,
        )
        + Op.SSTORE(
            key=0x7,
            value=Op.DELEGATECALL(
                gas=delegate_budget,
                address=storage_writer,
                address_warm=True,
            ),
            key_warm=False,
            original_value=0,
            new_value=1,
        )
        + Op.SSTORE(
            key=0x8,
            value=Op.CALL(
                gas=FORWARDED_GAS,
                address=absent,
                value=0x0,
                address_warm=False,
                value_transfer=False,
                account_new=False,
            ),
            key_warm=False,
            original_value=0,
            new_value=1,
        )
        + Op.SSTORE(
            key=0x3,
            value=Op.BALANCE(address=sender, address_warm=True),
            key_warm=False,
            original_value=0,
            new_value=1,
        )
    )
    delta_store = Op.SSTORE(
        key=0xA,
        value=Op.SUB(Op.MLOAD(offset=0x3E7), Op.GAS),
        key_warm=False,
        original_value=0,
        new_value=1,
    )
    target = pre.deploy_contract(
        code=window + delta_store + Op.STOP,
        storage={0: 18},
    )

    # Window delta: everything from the entry GAS read to the closing
    # one; the lead GAS and the closing GAS cancel out of the composite,
    # the delegate's work is added on top, and each failed value call
    # hands back its stipend along with the unused grant.
    measured = (
        window.gas_cost(fork)
        + delegate_store.gas_cost(fork)
        - 2 * fork.gas_costs().CALL_STIPEND
    )

    # Fork-derived budget with an EIP-2200 stipend margin for the
    # trailing delta store.
    intrinsic = fork.transaction_intrinsic_cost_calculator()()
    gas_limit = intrinsic + measured + delta_store.gas_cost(fork) + 5_000

    tx = Transaction(
        sender=sender,
        to=target,
        gas_limit=gas_limit,
        gas_price=GAS_PRICE,
    )

    copied_word = int.from_bytes(
        EXTCODE_BYTES[:COPY_SIZE].ljust(0x20, b"\x00"), "big"
    )
    post = {
        target: Account(
            storage={
                0x0: 18,
                0x1: len(EXTCODE_BYTES),
                0x2: copied_word,
                # Mid-execution balance: the full fee is charged upfront.
                0x3: INITIAL_BALANCE - gas_limit * GAS_PRICE,
                0x4: 18,
                # Slots 5 and 6 stay zero: the value calls failed.
                0x7: 1,
                0x8: 1,
                0xA: measured,
                0x64: DELEGATE_VALUE,
            },
        ),
    }

    state_test(pre=pre, post=post, tx=tx)
