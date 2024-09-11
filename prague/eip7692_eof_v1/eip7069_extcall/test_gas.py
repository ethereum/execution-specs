"""
abstract: Tests [EIP-7069: Revamped CALL instructions](https://eips.ethereum.org/EIPS/eip-7069)
    Tests gas comsumption
"""  # noqa: E501

import pytest

from ethereum_test_tools import Account, Alloc, Environment, StateTestFiller, Transaction
from ethereum_test_tools.eof.v1 import Container
from ethereum_test_tools.vm.opcode import Opcodes as Op
from ethereum_test_vm import Bytecode, EVMCodeType

from .. import EOF_FORK_NAME
from . import REFERENCE_SPEC_GIT_PATH, REFERENCE_SPEC_VERSION
from .helpers import (
    slot_cold_gas,
    slot_oog_call_result,
    slot_sanity_call_result,
    slot_warm_gas,
    value_call_legacy_abort,
    value_call_legacy_success,
)

REFERENCE_SPEC_GIT_PATH = REFERENCE_SPEC_GIT_PATH
REFERENCE_SPEC_VERSION = REFERENCE_SPEC_VERSION

pytestmark = pytest.mark.valid_from(EOF_FORK_NAME)


COLD_ACCOUNT_ACCESS_GAS = 2600
WARM_ACCOUNT_ACCESS_GAS = 100
CALL_WITH_VALUE_GAS = 9000
ACCOUNT_CREATION_GAS = 25000


@pytest.fixture
def state_env() -> Environment:
    """
    Prepare the environment for all state test cases.

    Main difference is that the excess blob gas is not increased by the target, as
    there is no genesis block -> block 1 transition, and therefore the excess blob gas
    is not decreased by the target.
    """
    return Environment()


def gas_test(
    state_test: StateTestFiller,
    env: Environment,
    pre: Alloc,
    setup_code: Bytecode,
    subject_code: Bytecode,
    tear_down_code: Bytecode,
    cold_gas: int,
    warm_gas: int | None = None,
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
    address_subject = pre.deploy_contract(
        Container.Code(setup_code + subject_code + tear_down_code)
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
            # - subtract 1 to cause OOG exception
            + Op.SSTORE(
                slot_oog_call_result,
                Op.CALL(
                    gas=Op.ADD(warm_gas - gas_single_gas_run - 1, Op.DUP7),
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
                slot_oog_call_result: value_call_legacy_abort,
                slot_sanity_call_result: value_call_legacy_success,
            },
        ),
    }

    tx = Transaction(to=address_legacy_harness, gas_limit=env.gas_limit, sender=sender)

    state_test(env=env, pre=pre, tx=tx, post=post)


@pytest.mark.parametrize(
    ["opcode", "pre_setup", "cold_gas", "warm_gas", "new_account"],
    [
        pytest.param(
            Op.EXTCALL,
            Op.PUSH0,
            COLD_ACCOUNT_ACCESS_GAS,
            WARM_ACCOUNT_ACCESS_GAS,
            False,
            id="EXTCALL",
        ),
        pytest.param(
            Op.EXTCALL,
            Op.PUSH1(1),
            COLD_ACCOUNT_ACCESS_GAS + CALL_WITH_VALUE_GAS,
            WARM_ACCOUNT_ACCESS_GAS + CALL_WITH_VALUE_GAS,
            False,
            id="EXTCALL_with_value",
        ),
        pytest.param(
            Op.EXTDELEGATECALL,
            Op.NOOP,
            COLD_ACCOUNT_ACCESS_GAS,
            WARM_ACCOUNT_ACCESS_GAS,
            False,
            id="EXTDELEGATECALL",
        ),
        pytest.param(
            Op.EXTSTATICCALL,
            Op.NOOP,
            COLD_ACCOUNT_ACCESS_GAS,
            WARM_ACCOUNT_ACCESS_GAS,
            False,
            id="EXTSTATICCALL",
        ),
        pytest.param(
            Op.EXTCALL,
            Op.PUSH0,
            COLD_ACCOUNT_ACCESS_GAS,
            WARM_ACCOUNT_ACCESS_GAS,
            True,
            id="EXTCALL_new_acc",
        ),
        pytest.param(
            Op.EXTCALL,
            Op.PUSH1(1),
            COLD_ACCOUNT_ACCESS_GAS + ACCOUNT_CREATION_GAS + CALL_WITH_VALUE_GAS,
            WARM_ACCOUNT_ACCESS_GAS + ACCOUNT_CREATION_GAS + CALL_WITH_VALUE_GAS,
            True,
            id="EXTCALL_with_value_new_acc",
        ),
        pytest.param(
            Op.EXTDELEGATECALL,
            Op.NOOP,
            COLD_ACCOUNT_ACCESS_GAS,
            WARM_ACCOUNT_ACCESS_GAS,
            True,
            id="EXTDELEGATECALL_new_acc",
        ),
        pytest.param(
            Op.EXTSTATICCALL,
            Op.NOOP,
            COLD_ACCOUNT_ACCESS_GAS,
            WARM_ACCOUNT_ACCESS_GAS,
            True,
            id="EXTSTATICCALL_new_acc",
        ),
    ],
)
@pytest.mark.parametrize(
    ["mem_expansion_size", "mem_expansion_extra_gas"],
    [
        pytest.param(0, 0, id="no_mem_expansion"),
        pytest.param(1, 3, id="1byte_mem_expansion"),
        pytest.param(32, 3, id="1word_mem_expansion"),
        pytest.param(33, 6, id="33bytes_mem_expansion"),
    ],
)
def test_ext_calls_gas(
    state_test: StateTestFiller,
    pre: Alloc,
    state_env: Environment,
    opcode: Op,
    pre_setup: Op,
    cold_gas: int,
    warm_gas: int,
    new_account: bool,
    mem_expansion_size: int,
    mem_expansion_extra_gas: int,
):
    """Tests variations of EXT*CALL gas, both warm and cold, without and with mem expansions"""
    address_target = (
        pre.fund_eoa(0) if new_account else pre.deploy_contract(Container.Code(Op.STOP))
    )

    gas_test(
        state_test,
        state_env,
        pre,
        setup_code=pre_setup + Op.PUSH1(mem_expansion_size) + Op.PUSH0 + Op.PUSH20(address_target),
        subject_code=opcode,
        tear_down_code=Op.STOP,
        cold_gas=cold_gas + mem_expansion_extra_gas,
        warm_gas=warm_gas + mem_expansion_extra_gas,
    )
