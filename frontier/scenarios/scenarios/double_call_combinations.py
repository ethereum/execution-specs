"""Define Scenario that will run a given program and then revert."""

from typing import List

from ethereum_test_tools import Conditional
from ethereum_test_tools.vm.opcode import Macro, Opcode
from ethereum_test_tools.vm.opcode import Macros as Om
from ethereum_test_tools.vm.opcode import Opcodes as Op

from ..common import Scenario, ScenarioEnvironment, ScenarioGeneratorInput


def scenarios_double_call_combinations(scenario_input: ScenarioGeneratorInput) -> List[Scenario]:
    """
    Generate Scenarios for double call combinations.
    First call the operation normally.
    Then do a subcall that will [OOG,REVERT,RETURN].
    Second call the operation normally.
    Compare the results of first call with the second operation call.
    """
    scenarios_list: List[Scenario] = []
    keep_gas = 300000
    revert_types: List[Opcode | Macro] = [Op.STOP, Om.OOG, Op.RETURN]
    if Op.REVERT in scenario_input.fork.valid_opcodes():
        revert_types.append(Op.REVERT)
    for revert in revert_types:
        operation_contract = scenario_input.pre.deploy_contract(code=scenario_input.operation_code)
        subcall_contract = scenario_input.pre.deploy_contract(
            code=Op.MSTORE(0, 0x1122334455667788991011121314151617181920212223242526272829303132)
            + revert(offset=0, size=32)
        )
        scenario_contract = scenario_input.pre.deploy_contract(
            code=Op.CALL(gas=Op.SUB(Op.GAS, keep_gas), address=operation_contract, ret_size=32)
            + Op.MSTORE(100, Op.MLOAD(0))
            + Op.MSTORE(0, 0)
            + Op.CALL(gas=50_000, address=subcall_contract)
            + Op.CALL(gas=Op.SUB(Op.GAS, keep_gas), address=operation_contract, ret_size=32)
            + Op.MSTORE(200, Op.MLOAD(0))
            + Conditional(
                condition=Op.EQ(Op.MLOAD(100), Op.MLOAD(200)),
                if_true=Op.RETURN(100, 32),
                if_false=Op.MSTORE(0, 0) + Op.RETURN(0, 32),
            )
        )
        env: ScenarioEnvironment = ScenarioEnvironment(
            code_address=operation_contract,
            code_caller=scenario_contract,
            selfbalance=0,
            call_value=0,
            call_dataload_0=0,
            call_datasize=0,
        )
        scenarios_list.append(
            Scenario(
                category="double_call_combinations",
                name=f"scenario_call_then_{revert}_in_subcall_then_call",
                code=scenario_contract,
                env=env,
                halts=False,
            )
        )

    return scenarios_list
