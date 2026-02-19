"""
Tests [EIP-3651: Warm COINBASE](https://eips.ethereum.org/EIPS/eip-3651).

Tests ported from:
[ethereum/tests/pull/1082](https://github.com/ethereum/tests/pull/1082).
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Bytecode,
    CodeGasMeasure,
    Environment,
    Fork,
    Op,
    StateTestFiller,
    Transaction,
)
from execution_testing.forks import Shanghai

from .spec import ref_spec_3651

REFERENCE_SPEC_GIT_PATH = ref_spec_3651.git_path
REFERENCE_SPEC_VERSION = ref_spec_3651.version


@pytest.mark.valid_from("Shanghai")
@pytest.mark.parametrize(
    "use_sufficient_gas",
    [True, False],
    ids=["sufficient_gas", "insufficient_gas"],
)
@pytest.mark.parametrize(
    "opcode,call_opcode",
    [
        ("call", Op.CALL),
        ("callcode", Op.CALLCODE),
        ("delegatecall", Op.DELEGATECALL),
        ("staticcall", Op.STATICCALL),
    ],
    ids=["CALL", "CALLCODE", "DELEGATECALL", "STATICCALL"],
)
def test_warm_coinbase_call_out_of_gas(
    state_test: StateTestFiller,
    env: Environment,
    pre: Alloc,
    post: Alloc,
    sender: Address,
    fork: Fork,
    opcode: str,
    call_opcode: Op,
    use_sufficient_gas: bool,
) -> None:
    """
    Test that the coinbase is warm by accessing the COINBASE with each
    of the following opcodes.

    - CALL
    - CALLCODE
    - DELEGATECALL
    - STATICCALL
    """
    # Build contract code: POP(xCALL(0, COINBASE, 0, ...))
    if call_opcode in (Op.CALL, Op.CALLCODE):
        contract_under_test_code = Op.POP(
            call_opcode(0, Op.COINBASE, 0, 0, 0, 0, 0)
        )
    else:
        contract_under_test_code = Op.POP(
            call_opcode(0, Op.COINBASE, 0, 0, 0, 0)
        )

    contract_under_test_address = pre.deploy_contract(contract_under_test_code)

    # Compute exact gas: warm call cost + overhead
    # (COINBASE, PUSHes, DUPs, POP)
    warm_call_cost = call_opcode(address_warm=True).gas_cost(fork)
    # Overhead = total cost (with cold default) minus the cold call cost
    cold_call_cost = call_opcode(address_warm=False).gas_cost(fork)
    total_with_cold = contract_under_test_code.gas_cost(fork)
    call_gas_exact = warm_call_cost + (total_with_cold - cold_call_cost)

    if not use_sufficient_gas:
        call_gas_exact -= 1

    caller_code = Op.SSTORE(
        0,
        Op.CALL(call_gas_exact, contract_under_test_address, 0, 0, 0, 0, 0),
    )
    caller_address = pre.deploy_contract(caller_code)

    tx = Transaction(
        to=caller_address,
        gas_limit=100_000,
        sender=sender,
    )

    if use_sufficient_gas and fork >= Shanghai:
        post[caller_address] = Account(
            storage={
                # On shanghai and beyond, calls with only 100 gas to
                # coinbase will succeed.
                0: 1,
            }
        )
    else:
        post[caller_address] = Account(
            storage={
                # Before shanghai, calls with only 100 gas to
                # coinbase will fail.
                0: 0,
            }
        )

    state_test(
        env=env,
        pre=pre,
        post=post,
        tx=tx,
        tag="opcode_" + opcode,
    )


# List of opcodes that are affected by EIP-3651, with their code and
# extra_stack_items. Overhead cost is computed at test time via gas_cost(fork).
gas_measured_opcodes = [
    ("EXTCODESIZE", Op.EXTCODESIZE(Op.COINBASE), 1),
    ("EXTCODECOPY", Op.EXTCODECOPY(Op.COINBASE, 0, 0, 0), 0),
    ("EXTCODEHASH", Op.EXTCODEHASH(Op.COINBASE), 1),
    ("BALANCE", Op.BALANCE(Op.COINBASE), 1),
    ("CALL", Op.CALL(0xFF, Op.COINBASE, 0, 0, 0, 0, 0), 1),
    ("CALLCODE", Op.CALLCODE(0xFF, Op.COINBASE, 0, 0, 0, 0, 0), 1),
    ("DELEGATECALL", Op.DELEGATECALL(0xFF, Op.COINBASE, 0, 0, 0, 0), 1),
    ("STATICCALL", Op.STATICCALL(0xFF, Op.COINBASE, 0, 0, 0, 0), 1),
]


@pytest.mark.valid_from("Berlin")  # these tests fill for fork >= Berlin
@pytest.mark.parametrize(
    "opcode,measured_code,extra_stack_items",
    gas_measured_opcodes,
    ids=[i[0] for i in gas_measured_opcodes],
)
def test_warm_coinbase_gas_usage(
    state_test: StateTestFiller,
    env: Environment,
    pre: Alloc,
    sender: Address,
    fork: Fork,
    opcode: str,
    measured_code: Bytecode,
    extra_stack_items: int,
) -> None:
    """
    Test the gas usage of opcodes affected by assuming a warm coinbase.

    - EXTCODESIZE
    - EXTCODECOPY
    - EXTCODEHASH
    - BALANCE
    - CALL
    - CALLCODE
    - DELEGATECALL
    - STATICCALL
    """
    # Compute overhead cost: total bytecode cost minus the
    # opcode-under-test cost
    # The opcode-under-test cost (warm or cold) is what we're measuring
    total_code_cost = measured_code.gas_cost(fork)
    # The opcode cost with default (cold) metadata
    opcode_cold_cost = Op.BALANCE(address_warm=False).gas_cost(fork)
    overhead_cost = total_code_cost - opcode_cold_cost

    code_gas_measure = CodeGasMeasure(
        code=measured_code,
        overhead_cost=overhead_cost,
        extra_stack_items=extra_stack_items,
    )

    measure_address = pre.deploy_contract(
        code=code_gas_measure,
    )

    # Coinbase is warm after EIP-3651 (Shanghai+), cold before
    expected_gas = Op.BALANCE(address_warm=(fork >= Shanghai)).gas_cost(fork)

    tx = Transaction(
        to=measure_address,
        gas_limit=100_000,
        sender=sender,
    )

    post = {
        measure_address: Account(
            storage={
                0x00: expected_gas,
            }
        )
    }

    state_test(
        env=env,
        pre=pre,
        post=post,
        tx=tx,
        tag="opcode_" + opcode.lower(),
    )
