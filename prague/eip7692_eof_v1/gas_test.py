"""
Utility to generate gas usage related state tests automatically.
"""

import itertools

from ethereum_test_base_types.base_types import Address
from ethereum_test_tools import Account, Alloc, Environment, StateTestFiller, Transaction
from ethereum_test_tools.eof.v1 import Container
from ethereum_test_tools.vm.opcode import Opcodes as Op
from ethereum_test_types.eof.v1 import Section
from ethereum_test_vm import Bytecode, EVMCodeType
from tests.prague.eip7692_eof_v1.eip7069_extcall.spec import (
    LEGACY_CALL_FAILURE,
    LEGACY_CALL_SUCCESS,
)

WARM_ACCOUNT_ACCESS_GAS = 100

"""Storage addresses for common testing fields"""
_slot = itertools.count()
slot_cold_gas = next(_slot)
slot_warm_gas = next(_slot)
slot_oog_call_result = next(_slot)
slot_sanity_call_result = next(_slot)


def gas_test(
    state_test: StateTestFiller,
    env: Environment,
    pre: Alloc,
    setup_code: Bytecode,
    subject_code: Bytecode,
    tear_down_code: Bytecode,
    cold_gas: int,
    warm_gas: int | None = None,
    subject_subcontainer: Container | None = None,
    subject_address: Address | None = None,
    subject_balance: int = 0,
    oog_difference: int = 1,
):
    """
    Creates a State Test to check the gas cost of a sequence of EOF code.

    `setup_code` and `tear_down_code` are called multiple times during the test, and MUST NOT have
    any side-effects which persist across message calls, and in particular, any effects on the gas
    usage of `subject_code`.
    """
    if cold_gas <= 0:
        raise ValueError(f"Target gas allocations (cold_gas) must be > 0, got {cold_gas}")
    if warm_gas is None:
        warm_gas = cold_gas

    sender = pre.fund_eoa()

    address_baseline = pre.deploy_contract(Container.Code(setup_code + tear_down_code))
    code_subject = setup_code + subject_code + tear_down_code
    address_subject = pre.deploy_contract(
        Container.Code(code_subject)
        if not subject_subcontainer
        else Container(
            sections=[
                Section.Code(code_subject),
                Section.Container(subject_subcontainer),
            ]
        ),
        balance=subject_balance,
        address=subject_address,
    )
    # 2 times GAS, POP, CALL, 6 times PUSH1 - instructions charged for at every gas run
    gas_single_gas_run = 2 * 2 + 2 + WARM_ACCOUNT_ACCESS_GAS + 6 * 3
    address_legacy_harness = pre.deploy_contract(
        code=(
            # warm subject and baseline without executing
            (Op.BALANCE(address_subject) + Op.POP + Op.BALANCE(address_baseline) + Op.POP)
            # Baseline gas run
            + (
                Op.GAS
                + Op.CALL(address=address_baseline, gas=Op.GAS)
                + Op.POP
                + Op.GAS
                + Op.SWAP1
                + Op.SUB
            )
            # cold gas run
            + (
                Op.GAS
                + Op.CALL(address=address_subject, gas=Op.GAS)
                + Op.POP
                + Op.GAS
                + Op.SWAP1
                + Op.SUB
            )
            # warm gas run
            + (
                Op.GAS
                + Op.CALL(address=address_subject, gas=Op.GAS)
                + Op.POP
                + Op.GAS
                + Op.SWAP1
                + Op.SUB
            )
            # Store warm gas: DUP3 is the gas of the baseline gas run
            + (Op.DUP3 + Op.SWAP1 + Op.SUB + Op.PUSH2(slot_warm_gas) + Op.SSTORE)
            # store cold gas: DUP2 is the gas of the baseline gas run
            + (Op.DUP2 + Op.SWAP1 + Op.SUB + Op.PUSH2(slot_cold_gas) + Op.SSTORE)
            # oog gas run:
            # - DUP7 is the gas of the baseline gas run, after other CALL args were pushed
            # - subtract the gas charged by the harness
            # - add warm gas charged by the subject
            # - subtract `oog_difference` to cause OOG exception (1 by default)
            + Op.SSTORE(
                slot_oog_call_result,
                Op.CALL(
                    gas=Op.ADD(warm_gas - gas_single_gas_run - oog_difference, Op.DUP7),
                    address=address_subject,
                ),
            )
            # sanity gas run: not subtracting 1 to see if enough gas makes the call succeed
            + Op.SSTORE(
                slot_sanity_call_result,
                Op.CALL(
                    gas=Op.ADD(warm_gas - gas_single_gas_run, Op.DUP7),
                    address=address_subject,
                ),
            )
            + Op.STOP
        ),
        evm_code_type=EVMCodeType.LEGACY,  # Needs to be legacy to use GAS opcode
    )

    post = {
        address_legacy_harness: Account(
            storage={
                slot_warm_gas: warm_gas,
                slot_cold_gas: cold_gas,
                slot_oog_call_result: LEGACY_CALL_FAILURE,
                slot_sanity_call_result: LEGACY_CALL_SUCCESS,
            },
        ),
    }

    tx = Transaction(to=address_legacy_harness, gas_limit=env.gas_limit, sender=sender)

    state_test(env=env, pre=pre, tx=tx, post=post)
