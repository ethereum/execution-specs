"""
Test good and bad EOFCREATE cases
"""

import pytest

from ethereum_test_tools import Alloc, Environment, StateTestFiller, compute_eofcreate_address
from ethereum_test_tools.eof.v1 import Container, Section
from ethereum_test_tools.vm.opcode import Opcodes as Op
from ethereum_test_types.helpers import cost_memory_bytes

from .. import EOF_FORK_NAME
from ..gas_test import gas_test
from .helpers import (
    aborting_container,
    big_runtime_subcontainer,
    bigger_initcode_subcontainer,
    bigger_initcode_subcontainer_gas,
    data_appending_initcode_subcontainer,
    data_appending_initcode_subcontainer_gas,
    data_initcode_subcontainer,
    data_runtime_container,
    expensively_reverting_container,
    expensively_reverting_container_gas,
    reverting_container,
    slot_counter,
    smallest_initcode_subcontainer,
    smallest_initcode_subcontainer_gas,
    smallest_runtime_subcontainer,
)

REFERENCE_SPEC_GIT_PATH = "EIPS/eip-7620.md"
REFERENCE_SPEC_VERSION = "52ddbcdddcf72dd72427c319f2beddeb468e1737"

pytestmark = pytest.mark.valid_from(EOF_FORK_NAME)

EOFCREATE_GAS = 32000


def make_factory(initcode: Container):
    """
    Wraps an initcontainer into a minimal runtime container
    """
    return Container(
        name="Factory Subcontainer",
        sections=[
            Section.Code(Op.EOFCREATE[0](0, 0, 0, 0) + Op.STOP),
            Section.Container(initcode),
        ],
    )


@pytest.mark.parametrize("value", [0, 1])
@pytest.mark.parametrize("new_account", [True, False])
@pytest.mark.parametrize(
    "mem_expansion_bytes",
    [0, 1, 32, 33],
)
@pytest.mark.parametrize(
    ["initcode", "initcode_execution_cost", "runtime"],
    [
        pytest.param(
            smallest_initcode_subcontainer,
            smallest_initcode_subcontainer_gas,
            smallest_runtime_subcontainer,
            id="smallest_code",
        ),
        pytest.param(
            Container.Init(aborting_container),
            smallest_initcode_subcontainer_gas,
            aborting_container,
            id="aborting_runtime",
        ),
        pytest.param(
            reverting_container, smallest_initcode_subcontainer_gas, None, id="reverting_initcode"
        ),
        pytest.param(
            expensively_reverting_container,
            expensively_reverting_container_gas,
            None,
            id="expensively_reverting_initcode",
        ),
        pytest.param(
            Container.Init(big_runtime_subcontainer),
            smallest_initcode_subcontainer_gas,
            big_runtime_subcontainer,
            id="big_runtime",
        ),
        pytest.param(
            Container.Init(make_factory(smallest_initcode_subcontainer)),
            smallest_initcode_subcontainer_gas,
            make_factory(smallest_initcode_subcontainer),
            id="nested_initcode",
        ),
        pytest.param(
            bigger_initcode_subcontainer,
            bigger_initcode_subcontainer_gas,
            smallest_runtime_subcontainer,
            id="bigger_initcode",
        ),
        pytest.param(
            data_initcode_subcontainer,
            smallest_initcode_subcontainer_gas,
            data_runtime_container,
            id="data_initcode",
        ),
        pytest.param(
            data_appending_initcode_subcontainer,
            data_appending_initcode_subcontainer_gas,
            data_runtime_container,
            id="data_appending_initcode",
        ),
    ],
)
def test_eofcreate_gas(
    state_test: StateTestFiller,
    pre: Alloc,
    value: int,
    new_account: bool,
    mem_expansion_bytes: int,
    initcode: Container,
    initcode_execution_cost: int,
    runtime: Container,
):
    """Tests variations of EOFCREATE gas"""
    initcode_hashing_cost = 6 * ((len(initcode) + 31) // 32)
    deployed_code_cost = 200 * len(runtime) if runtime else 0

    subject_address = pre.fund_eoa(0)

    salt_addresses = [compute_eofcreate_address(subject_address, i, initcode) for i in range(4)]

    if not new_account:
        for a in salt_addresses:
            pre.fund_address(a, 1)

    # Using `TLOAD` / `TSTORE` to work around warm/cold gas differences. We need a counter to pick
    # a distinct salt on each `EOFCREATE` and avoid running into address conflicts.
    code_increment_counter = (
        Op.TLOAD(slot_counter) + Op.DUP1 + Op.TSTORE(slot_counter, Op.PUSH1(1) + Op.ADD)
    )

    gas_test(
        state_test,
        Environment(),
        pre,
        setup_code=Op.PUSH1(mem_expansion_bytes)
        + Op.PUSH0
        + code_increment_counter
        + Op.PUSH32(value),
        subject_code=Op.EOFCREATE[0],
        tear_down_code=Op.STOP,
        cold_gas=EOFCREATE_GAS
        + cost_memory_bytes(mem_expansion_bytes, 0)
        + initcode_hashing_cost
        + initcode_execution_cost
        + deployed_code_cost,
        subject_subcontainer=initcode,
        subject_balance=value * 4,
        subject_address=subject_address,
        oog_difference=initcode_execution_cost + deployed_code_cost + 1,
    )
