"""
Test that a frame one gas short of a cold state access runs out of gas.

The original tests were written by Ori Pomerantz.

Ported from:
state_tests/stEIP150singleCodeGasPrices/eip2929OOGFiller.yml

@manually-enhanced: Do not overwrite. `caller` calls `accessor` with
exactly the gas `accessor` needs, or one gas less, and stores the call's
success flag. `accessor` performs one cold access: SLOAD or SSTORE of
its own storage slot, or an account access opcode on `accessed_account`
(the call opcodes forward it no gas, which its STOP needs none of). The
gas comes from the framework gas calculation with cold-access metadata,
so the one-short arm runs out of gas in the access on every fork. The
filler gave budgets that only EIP-2929's cold costs exceed; the exact
and one-short pair pins the cold cost from both sides instead. On
EIP-7928 forks the block access list shows that a starved access records
nothing but SSTORE's read of its slot.
"""

from typing import Generator

import pytest
from _pytest.mark.structures import ParameterSet
from execution_testing import (
    Account,
    Address,
    Alloc,
    BalAccountExpectation,
    BalStorageChange,
    BalStorageSlot,
    BlockAccessListExpectation,
    Bytecode,
    StateTestFiller,
    Transaction,
)
from execution_testing.forks import Fork
from execution_testing.vm import Op, Opcode

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

SENTINEL = 0x0BAD
RESULT_SLOT = 0
ACCESSED_SLOT = 0
STORED_VALUE = 0x60A7
COPY_SIZE = 0x20

ACCESS_OPCODES: list[Opcode] = [
    Op.SLOAD,
    Op.SSTORE,
    Op.BALANCE,
    Op.EXTCODESIZE,
    Op.EXTCODECOPY,
    Op.EXTCODEHASH,
    Op.CALL,
    Op.CALLCODE,
    Op.DELEGATECALL,
    Op.STATICCALL,
]
CALL_OPCODES = (Op.CALL, Op.CALLCODE, Op.DELEGATECALL, Op.STATICCALL)


def access_opcodes_by_fork(
    fork: Fork,
) -> Generator[ParameterSet, None, None]:
    """Yield every cold access opcode that exists on `fork`."""
    valid_opcodes = set(fork.valid_opcodes())
    for opcode in ACCESS_OPCODES:
        if opcode in valid_opcodes:
            yield pytest.param(opcode, id=opcode._name_.lower())


pytestmark = [
    pytest.mark.ported_from(
        ["state_tests/stEIP150singleCodeGasPrices/eip2929OOGFiller.yml"],
    ),
    pytest.mark.valid_from("Frontier"),
    pytest.mark.parametrize_by_fork("opcode", access_opcodes_by_fork),
]


@pytest.mark.parametrize("starved", [False, True], ids=["exact", "one_short"])
def test_eip2929_oog(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    opcode: Opcode,
    starved: bool,
) -> None:
    """Call a cold-access with exactly enough gas, or one gas less."""
    sender = pre.fund_eoa()
    accessed_account = pre.deploy_contract(code=Op.STOP)

    access: Bytecode
    if opcode == Op.SLOAD:
        access = Op.SLOAD(key=ACCESSED_SLOT, key_warm=False)
    elif opcode == Op.SSTORE:
        access = Op.SSTORE(
            key=ACCESSED_SLOT,
            value=STORED_VALUE,
            key_warm=False,
            original_value=0,
            new_value=STORED_VALUE,
        )
    elif opcode == Op.EXTCODECOPY:
        access = Op.EXTCODECOPY(
            address=accessed_account,
            dest_offset=0,
            offset=0,
            size=COPY_SIZE,
            address_warm=False,
            data_size=COPY_SIZE,
            new_memory_size=COPY_SIZE,
        )
    elif opcode in CALL_OPCODES:
        access = opcode(gas=0, address=accessed_account, address_warm=False)
    elif opcode in (Op.BALANCE, Op.EXTCODESIZE, Op.EXTCODEHASH):
        access = opcode(address=accessed_account, address_warm=False)
    else:
        raise ValueError(f"Unknown access opcode: {opcode}")
    accessor_code = access + Op.STOP
    accessor = pre.deploy_contract(code=accessor_code)

    accessor_gas = accessor_code.gas_cost(fork)
    if starved:
        accessor_gas -= 1

    caller = pre.deploy_contract(
        code=Op.SSTORE(
            RESULT_SLOT, Op.CALL(gas=accessor_gas, address=accessor)
        )
        + Op.STOP,
        storage={RESULT_SLOT: SENTINEL},
    )

    # The SSTORE's state gas must come out of the accessor's budget, not
    # out of a reservoir (EIP-8037). The other accesses have no state gas,
    # so they leave the reservoir unset and keep their frame variants.
    reservoir = {"state_gas_reservoir": 0} if opcode == Op.SSTORE else {}
    tx = Transaction(
        sender=sender,
        to=caller,
        protected=fork.supports_protected_txs(),
        **reservoir,
    )

    post = {caller: Account(storage={RESULT_SLOT: 0 if starved else 1})}
    if opcode == Op.SSTORE:
        post[accessor] = Account(
            storage={} if starved else {ACCESSED_SLOT: STORED_VALUE}
        )

    expected_block_access_list = None
    if fork.is_eip_enabled(7928):
        # A starved access halts before it touches anything, so neither
        # the accessed slot nor the accessed account is recorded. SSTORE
        # is the exception: it reads the slot once its access cost is
        # affordable, and only then runs short on the rest of its charge.
        expectations: dict[Address, BalAccountExpectation | None]
        if opcode == Op.SLOAD:
            expectations = {
                accessor: BalAccountExpectation.empty()
                if starved
                else BalAccountExpectation(storage_reads=[ACCESSED_SLOT]),
            }
        elif opcode == Op.SSTORE:
            expectations = {
                accessor: BalAccountExpectation(
                    storage_reads=[ACCESSED_SLOT], storage_changes=[]
                )
                if starved
                else BalAccountExpectation(
                    storage_reads=[],
                    storage_changes=[
                        BalStorageSlot(
                            slot=ACCESSED_SLOT,
                            slot_changes=[
                                BalStorageChange(
                                    block_access_index=1,
                                    post_value=STORED_VALUE,
                                )
                            ],
                        )
                    ],
                ),
            }
        else:
            expectations = {
                accessed_account: None
                if starved
                else BalAccountExpectation.empty(),
            }
        expected_block_access_list = BlockAccessListExpectation(
            account_expectations=expectations
        )

    state_test(
        pre=pre,
        post=post,
        tx=tx,
        expected_block_access_list=expected_block_access_list,
    )
