"""
abstract: Tests [EIP-7069: Revamped CALL instructions](https://eips.ethereum.org/EIPS/eip-7069)
    Tests gas comsumption
"""  # noqa: E501

import pytest

from ethereum_test_tools import Alloc, Environment, StateTestFiller
from ethereum_test_tools.eof.v1 import Container
from ethereum_test_tools.vm.opcode import Opcodes as Op
from ethereum_test_types.helpers import cost_memory_bytes

from .. import EOF_FORK_NAME
from ..gas_test import gas_test
from . import REFERENCE_SPEC_GIT_PATH, REFERENCE_SPEC_VERSION

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
    "mem_expansion_bytes",
    [0, 1, 32, 33],
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
    mem_expansion_bytes: int,
):
    """Tests variations of EXT*CALL gas, both warm and cold, without and with mem expansions"""
    address_target = (
        pre.fund_eoa(0) if new_account else pre.deploy_contract(Container.Code(Op.STOP))
    )

    gas_test(
        state_test,
        state_env,
        pre,
        setup_code=pre_setup
        + Op.PUSH1(mem_expansion_bytes)
        + Op.PUSH0
        + Op.PUSH20(address_target),
        subject_code=opcode,
        tear_down_code=Op.STOP,
        cold_gas=cold_gas + cost_memory_bytes(mem_expansion_bytes, 0),
        warm_gas=warm_gas + cost_memory_bytes(mem_expansion_bytes, 0),
    )
