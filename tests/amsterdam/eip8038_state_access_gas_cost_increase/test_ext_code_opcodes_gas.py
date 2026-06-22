"""
Tests for [EIP-8038: State Access Gas Cost Increase](https://eips.ethereum.org/EIPS/eip-8038).

Covers the EIP-8038 ``EXT*`` "double-read" surcharge: ``EXTCODESIZE`` and
``EXTCODECOPY`` perform two database reads (the account leaf and then the
code) and are therefore charged an extra ``WARM_ACCESS`` on top of the
account-access cost, whereas ``BALANCE`` and ``EXTCODEHASH`` read only the
account leaf and are charged the account-access cost alone.
"""

from typing import Callable

import pytest
from execution_testing import (
    AccessList,
    Account,
    Alloc,
    Bytecode,
    CodeGasMeasure,
    Environment,
    Fork,
    Op,
    StateTestFiller,
    Transaction,
)
from execution_testing.checklists import EIPChecklist

from .spec import ref_spec_8038

REFERENCE_SPEC_GIT_PATH = ref_spec_8038.git_path
REFERENCE_SPEC_VERSION = ref_spec_8038.version

pytestmark = pytest.mark.valid_from("Amsterdam")


# Each parameter carries:
#   - executable: builds the runnable opcode targeting ``target``
#   - cost_metadata: builds the metadata-only opcode for gas computation
#   - extra_stack_items: stack items left by the opcode (for CodeGasMeasure)
#   - code_read_surcharge: whether EIP-8038 adds the extra WARM_ACCESS read
EXT_OPCODES = [
    pytest.param(
        lambda target: Op.EXTCODESIZE(target),
        lambda warm: Op.EXTCODESIZE(address_warm=warm),
        1,
        True,
        id="EXTCODESIZE",
    ),
    pytest.param(
        lambda target: Op.EXTCODECOPY(target, 0, 0, 0),
        lambda warm: Op.EXTCODECOPY(address_warm=warm),
        0,
        True,
        id="EXTCODECOPY",
    ),
    pytest.param(
        lambda target: Op.EXTCODEHASH(target),
        lambda warm: Op.EXTCODEHASH(address_warm=warm),
        1,
        False,
        id="EXTCODEHASH",
    ),
    pytest.param(
        lambda target: Op.BALANCE(target),
        lambda warm: Op.BALANCE(address_warm=warm),
        1,
        False,
        id="BALANCE",
    ),
]


@EIPChecklist.GasCostChanges.Test.GasUpdatesMeasurement()
@pytest.mark.parametrize("warm", [False, True], ids=["cold", "warm"])
@pytest.mark.parametrize(
    "executable,cost_metadata,extra_stack_items,code_read_surcharge",
    EXT_OPCODES,
)
def test_ext_code_opcode_gas(
    state_test: StateTestFiller,
    env: Environment,
    pre: Alloc,
    fork: Fork,
    warm: bool,
    executable: Callable[[object], Bytecode],
    cost_metadata: Callable[[bool], Bytecode],
    extra_stack_items: int,
    code_read_surcharge: bool,
) -> None:
    """
    Measure the exact gas of an external-code/account-access opcode and
    assert it matches the EIP-8038 schedule.

    ``EXTCODESIZE``/``EXTCODECOPY`` must cost exactly one ``WARM_ACCESS``
    more than ``BALANCE``/``EXTCODEHASH`` at equal warmth (the second,
    code-reading database access).
    """
    gas_costs = fork.gas_costs()

    target = pre.deploy_contract(Op.STOP)

    measured_code = executable(target)
    # Subtract the opcode's OWN cold cost (not BALANCE's) so the
    # CodeGasMeasure overhead excludes only the PUSH wrapper; under
    # EIP-8038 EXTCODESIZE/EXTCODECOPY have a higher cold cost than
    # BALANCE because of the code-read surcharge.
    cold_opcode_cost = cost_metadata(False).gas_cost(fork)
    overhead_cost = measured_code.gas_cost(fork) - cold_opcode_cost

    code_gas_measure = CodeGasMeasure(
        code=measured_code,
        overhead_cost=overhead_cost,
        extra_stack_items=extra_stack_items,
    )
    measure_address = pre.deploy_contract(code=code_gas_measure)

    access_cost = (
        gas_costs.WARM_ACCESS if warm else gas_costs.COLD_ACCOUNT_ACCESS
    )
    surcharge = gas_costs.WARM_ACCESS if code_read_surcharge else 0
    expected_gas = access_cost + surcharge
    # Cross-check the framework opcode model agrees with the formula.
    assert expected_gas == cost_metadata(warm).gas_cost(fork)

    # Warm the target via the access list when required; the cold case
    # leaves it absent so its first runtime access is cold.
    access_list = (
        [AccessList(address=target, storage_keys=[])] if warm else None
    )
    tx = Transaction(
        to=measure_address,
        sender=pre.fund_eoa(),
        gas_limit=1_000_000,
        access_list=access_list,
    )

    post = {measure_address: Account(storage={0: expected_gas})}

    state_test(env=env, pre=pre, post=post, tx=tx)
