"""
Verify the EIP-150 repriced code/account operations in one frame whose
calls also expand memory: EXTCODESIZE, EXTCODECOPY, failing value
CALL/CALLCODE (insufficient balance), DELEGATECALL that writes the
caller's storage, a call to a nonexistent account, BALANCE, and a final
raw gas reading that pins the whole execution.

Ported from:
state_tests/stMemExpandingEIP150Calls/NewGasPriceForCodesWithMemExpandingCallsFiller.json

@manually-enhanced: Do not overwrite. The ported bytecode shape is kept,
but the final gas reading, the mid-execution sender balance, and the
copied code word are derived (opcode metadata, fee formula, the deployed
bytes); the delegate's budget is derived so its store — state-priced
under EIP-8037 — fits inside the grant; each failed value call returns
its stipend.
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
# Budget for the calls whose outcome does not depend on it.
FORWARDED_GAS = 0x7530
# The ported calls' argument window, driving the memory expansion.
MEM_OFFSET = 0xFF
MEM_SIZE = 0xFF
GAS_PRICE = 10
INITIAL_BALANCE = 10**15


@pytest.mark.ported_from(
    [
        "state_tests/stMemExpandingEIP150Calls/NewGasPriceForCodesWithMemExpandingCallsFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Berlin")
def test_new_gas_price_for_codes_with_mem_expanding_calls(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Measure repriced operations with memory-expanding call windows."""
    sender = pre.fund_eoa(amount=INITIAL_BALANCE)
    code_target = pre.deploy_contract(code=EXTCODE_BYTES, balance=111)
    delegate_store = Op.SSTORE(
        key=0x64,
        value=DELEGATE_VALUE,
        key_warm=False,
        original_value=0,
        new_value=DELEGATE_VALUE,
    )
    storage_writer = pre.deploy_contract(code=delegate_store)
    absent = pre.nonexistent_account()

    # The delegate must succeed: with a zero reservoir its state-priced
    # store is paid from the regular grant, so the budget is derived.
    delegate_budget = delegate_store.gas_cost(fork) + 2_000

    call_window = MEM_OFFSET + MEM_SIZE
    body = (
        Op.SSTORE(
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
            new_memory_size=0x20,
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
                args_offset=MEM_OFFSET,
                args_size=MEM_SIZE,
                ret_offset=MEM_OFFSET,
                ret_size=MEM_SIZE,
                address_warm=False,
                value_transfer=True,
                account_new=False,
                new_memory_size=call_window,
                old_memory_size=0x20,
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
                args_offset=MEM_OFFSET,
                args_size=MEM_SIZE,
                ret_offset=MEM_OFFSET,
                ret_size=MEM_SIZE,
                address_warm=True,
                value_transfer=True,
                account_new=False,
                new_memory_size=call_window,
                old_memory_size=call_window,
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
                args_offset=MEM_OFFSET,
                args_size=MEM_SIZE,
                ret_offset=MEM_OFFSET,
                ret_size=MEM_SIZE,
                address_warm=True,
                new_memory_size=call_window,
                old_memory_size=call_window,
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
                args_offset=MEM_OFFSET,
                args_size=MEM_SIZE,
                ret_offset=MEM_OFFSET,
                ret_size=MEM_SIZE,
                address_warm=False,
                value_transfer=False,
                account_new=False,
                new_memory_size=call_window,
                old_memory_size=call_window,
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
    final_store = Op.SSTORE(
        key=0xA,
        value=Op.GAS,
        key_warm=False,
        original_value=0,
        new_value=1,
    )
    target = pre.deploy_contract(
        code=body + final_store + Op.STOP,
        storage={0: 18},
    )

    # Consumption before the final GAS read: the body's composite plus
    # the delegate's work, minus the two returned stipends.
    consumed = (
        body.gas_cost(fork)
        + delegate_store.gas_cost(fork)
        - 2 * fork.gas_costs().CALL_STIPEND
    )

    intrinsic = fork.transaction_intrinsic_cost_calculator()()
    gas_limit = intrinsic + consumed + final_store.gas_cost(fork) + 5_000

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
                # Raw reading: everything left after the body's work and
                # the GAS opcode itself.
                0xA: gas_limit - intrinsic - consumed - Op.GAS.gas_cost(fork),
                0x64: DELEGATE_VALUE,
            },
        ),
    }

    state_test(pre=pre, post=post, tx=tx)
