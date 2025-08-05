"""test `CALL` opcode."""

import pytest  # type: ignore

from ethereum_test_forks import Fork
from ethereum_test_tools import (
    Account,
    Alloc,
    Environment,
    StateTestFiller,
    Transaction,
)
from ethereum_test_tools.code.generators import CodeGasMeasure
from ethereum_test_tools.vm.opcode import Opcodes as Op


# TODO: There's an issue with gas definitions on forks previous to Berlin, remove this when fixed.
# https://github.com/ethereum/execution-spec-tests/pull/1952#discussion_r2237634275
@pytest.mark.valid_from("Berlin")
def test_call_large_offset_mstore(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
):
    """
    CALL with ret_offset larger than memory size and ret_size zero
    Then do an MSTORE in that offset to see if memory was expanded in CALL.

    This is for bug in a faulty EVM implementation where memory is expanded when it shouldn't.
    """
    sender = pre.fund_eoa()

    gsc = fork.gas_costs()
    mem_offset = 128  # arbitrary number

    call_measure = CodeGasMeasure(
        code=Op.CALL(gas=0, ret_offset=mem_offset, ret_size=0),
        overhead_cost=gsc.G_VERY_LOW * len(Op.CALL.kwargs),  # Cost of pushing CALL args
        extra_stack_items=1,  # Because CALL pushes 1 item to the stack
        sstore_key=0,
        stop=False,  # Because it's the first CodeGasMeasure
    )
    mstore_measure = CodeGasMeasure(
        code=Op.MSTORE(offset=mem_offset, value=1),
        overhead_cost=gsc.G_VERY_LOW * len(Op.MSTORE.kwargs),  # Cost of pushing MSTORE args
        extra_stack_items=0,
        sstore_key=1,
    )

    contract = pre.deploy_contract(call_measure + mstore_measure)

    tx = Transaction(
        gas_limit=500_000,
        to=contract,
        value=0,
        sender=sender,
    )

    # this call cost is just the address_access_cost
    call_cost = gsc.G_COLD_ACCOUNT_ACCESS

    memory_expansion_gas_calc = fork.memory_expansion_gas_calculator()
    # mstore cost: base cost + expansion cost
    mstore_cost = gsc.G_MEMORY + memory_expansion_gas_calc(new_bytes=mem_offset + 1)
    state_test(
        env=Environment(),
        pre=pre,
        tx=tx,
        post={
            contract: Account(
                storage={
                    0: call_cost,
                    1: mstore_cost,
                },
            )
        },
    )


# TODO: There's an issue with gas definitions on forks previous to Berlin, remove this when fixed.
# https://github.com/ethereum/execution-spec-tests/pull/1952#discussion_r2237634275
@pytest.mark.valid_from("Berlin")
def test_call_memory_expands_on_early_revert(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
):
    """
    When CALL reverts early (e.g. because of not enough balance by the sender),
    memory should be expanded anyway.
    We check this with an MSTORE.

    This is for a bug in an EVM implementation where memory is expanded after executing a CALL, but
    not when an early revert happens.
    """
    sender = pre.fund_eoa()

    gsc = fork.gas_costs()
    ret_size = 128  # arbitrary number, greater than memory size to trigger an expansion

    call_measure = CodeGasMeasure(
        code=Op.CALL(gas=0, value=100, ret_size=ret_size),  # CALL with value
        overhead_cost=gsc.G_VERY_LOW * len(Op.CALL.kwargs),  # Cost of pushing CALL args
        extra_stack_items=1,  # Because CALL pushes 1 item to the stack
        sstore_key=0,
        stop=False,  # Because it's the first CodeGasMeasure
    )
    mstore_measure = CodeGasMeasure(
        code=Op.MSTORE(offset=ret_size // 2, value=1),  # Low offset for not expanding memory
        overhead_cost=gsc.G_VERY_LOW * len(Op.MSTORE.kwargs),  # Cost of pushing MSTORE args
        extra_stack_items=0,
        sstore_key=1,
    )

    # Contract without enough balance to send value transfer
    contract = pre.deploy_contract(code=call_measure + mstore_measure, balance=0)

    tx = Transaction(
        gas_limit=500_000,
        to=contract,
        value=0,
        sender=sender,
    )

    memory_expansion_gas_calc = fork.memory_expansion_gas_calculator()
    # call cost: address_access_cost + new_acc_cost + memory_expansion_cost + value - stipend
    call_cost = (
        gsc.G_COLD_ACCOUNT_ACCESS
        + gsc.G_NEW_ACCOUNT
        + memory_expansion_gas_calc(new_bytes=ret_size)
        + gsc.G_CALL_VALUE
        - gsc.G_CALL_STIPEND
    )

    # mstore cost: base cost. No memory expansion cost needed, it was expanded on CALL.
    mstore_cost = gsc.G_MEMORY
    state_test(
        env=Environment(),
        pre=pre,
        tx=tx,
        post={
            contract: Account(
                storage={
                    0: call_cost,
                    1: mstore_cost,
                },
            )
        },
    )
