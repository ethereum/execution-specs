"""
abstract: Tests [EIP-7069: Revamped CALL instructions](https://eips.ethereum.org/EIPS/eip-7069)
    Tests gas comsumption
"""  # noqa: E501

import pytest

from ethereum_test_tools import Account, Alloc, Environment, StateTestFiller, Transaction
from ethereum_test_tools.eof.v1 import Container, Section
from ethereum_test_tools.vm.opcode import Opcodes as Op
from ethereum_test_vm import Bytecode, EVMCodeType

from .. import EOF_FORK_NAME
from . import REFERENCE_SPEC_GIT_PATH, REFERENCE_SPEC_VERSION
from .helpers import slot_cold_gas, slot_warm_gas

REFERENCE_SPEC_GIT_PATH = REFERENCE_SPEC_GIT_PATH
REFERENCE_SPEC_VERSION = REFERENCE_SPEC_VERSION

pytestmark = pytest.mark.valid_from(EOF_FORK_NAME)


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
    """Creates a State Test to check the gas cost of a sequence of EOF code."""
    if cold_gas <= 0:
        raise ValueError(f"Target gas allocations (warm_gas) must be > 0, got {cold_gas}")
    if warm_gas is None:
        warm_gas = cold_gas

    sender = pre.fund_eoa(10**18)

    address_baseline = pre.deploy_contract(setup_code + tear_down_code)
    address_subject = pre.deploy_contract(setup_code + subject_code + tear_down_code)
    address_legacy_harness = pre.deploy_contract(
        code=(
            # warm subject and baseline without executing
            (Op.BALANCE(address_subject) + Op.POP + Op.BALANCE(address_baseline) + Op.POP)
            # cold gas run
            + (
                Op.GAS
                + Op.CALL(address=address_subject, gas=500_000)
                + Op.POP
                + Op.GAS
                + Op.SWAP1
                + Op.SUB
            )
            # Baseline gas run
            + (
                Op.GAS
                + Op.CALL(address=address_baseline, gas=500_000)
                + Op.POP
                + Op.GAS
                + Op.SWAP1
                + Op.SUB
            )
            # warm gas run
            + (
                Op.GAS
                + Op.CALL(address=address_subject, gas=500_000)
                + Op.POP
                + Op.GAS
                + Op.SWAP1
                + Op.SUB
            )
            # Store warm gas
            + (Op.DUP2 + Op.SWAP1 + Op.SUB + Op.PUSH2(slot_warm_gas) + Op.SSTORE)
            # store cold gas
            + (Op.SWAP1 + Op.SUB + Op.PUSH2(slot_cold_gas) + Op.SSTORE)
            + Op.STOP
        ),
        evm_code_type=EVMCodeType.LEGACY,  # Needs to be legacy to use GAS opcode
    )

    post = {
        address_legacy_harness: Account(
            storage={
                slot_warm_gas: warm_gas,
                slot_cold_gas: cold_gas,
            },
        ),
    }

    tx = Transaction(to=address_legacy_harness, gas_limit=2_000_000, sender=sender)

    state_test(env=env, pre=pre, tx=tx, post=post)


@pytest.mark.parametrize(
    ["opcode", "pre_setup", "cold_gas", "warm_gas"],
    [
        pytest.param(Op.EXTCALL, Op.PUSH0, 2600, 100, id="EXTCALL"),
        pytest.param(Op.EXTCALL, Op.PUSH1(1), 2600 + 9000, 100 + 9000, id="EXTCALL_with_value"),
        pytest.param(Op.EXTDELEGATECALL, Op.NOOP, 2600, 100, id="EXTSTATICCALL"),
        pytest.param(Op.EXTSTATICCALL, Op.NOOP, 2600, 100, id="EXTDELEGATECALL"),
    ],
)
def test_ext_calls_gas(
    state_test: StateTestFiller,
    pre: Alloc,
    state_env: Environment,
    opcode: Op,
    pre_setup: Op,
    cold_gas: int,
    warm_gas: int | None,
):
    """Tests 4 variations of EXT*CALL gas, both warm and cold"""
    address_target = pre.deploy_contract(Container(sections=[Section.Code(code=Op.STOP)]))

    gas_test(
        state_test,
        state_env,
        pre,
        setup_code=pre_setup + Op.PUSH0 + Op.PUSH0 + Op.PUSH20(address_target),
        subject_code=opcode,
        tear_down_code=Op.STOP,
        cold_gas=cold_gas,
        warm_gas=warm_gas,
    )
