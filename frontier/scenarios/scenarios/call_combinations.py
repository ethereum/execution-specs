"""Define Scenario that will put a given program in all call contexts."""

from dataclasses import dataclass
from typing import List

from ethereum_test_tools import Address, Alloc
from ethereum_test_tools.vm.opcode import Opcode
from ethereum_test_tools.vm.opcode import Opcodes as Op
from ethereum_test_vm import EVMCodeType

from ..common import Scenario, ScenarioEnvironment, ScenarioGeneratorInput


class ScenariosCallCombinations:
    """Class that would generate scenarios for all call combinations."""

    @dataclass
    class AddressBalance:
        """Definition of values we use to put in contract balances and call."""

        root_call_value = 1
        first_call_value = 3
        second_call_value = 5

        root_contract_balance = 105
        scenario_contract_balance = 107
        sub_contract_balance = 111
        program_selfbalance = 113

    """The gas we keep before calling an address"""
    keep_gas = 100000

    """Possible calls list to make as a first call"""
    first_call_opcodes: List[Opcode] = []

    """Possible calls list to make as a second call"""
    second_call_opcodes: List[Opcode] = []

    """Balance map that we put in different accounts"""
    balance: AddressBalance
    scenario_input: ScenarioGeneratorInput

    env: ScenarioEnvironment

    def __init__(self, scenario_input: ScenarioGeneratorInput):
        """Define possible call combinations given the fork."""
        self.first_call_opcodes = [
            callcode
            for callcode, evm_type in scenario_input.fork.call_opcodes()
            if evm_type == EVMCodeType.LEGACY
        ]
        self.second_call_opcodes = self.first_call_opcodes[:]
        self.second_call_opcodes.append(Op.NOOP)
        self.scenario_input = scenario_input
        self.balance = self.AddressBalance()

    def generate(self) -> List[Scenario]:
        """
        Generate Scenarios for call combinations
        We take code that we want to test at scenario_input.operation_contract
        and put it in the context of call combinations.

        Example:
        root_contract -> call -> scenario_contract -> first_call -> sub_contract
        sub_contact -> second_call -> code
        We assume that code always returns it's result
        That we pass as return value in scenario_contract for the post state verification

        """
        scenarios_list: List[Scenario] = []

        for first_call in self.first_call_opcodes:
            for second_call in self.second_call_opcodes:
                if second_call == Op.NOOP:
                    scenarios_list.append(self._generate_one_call_scenario(first_call))
                else:
                    scenarios_list.append(
                        self._generate_two_call_scenario(first_call, second_call)
                    )
        return scenarios_list

    def _generate_one_call_scenario(self, first_call: Opcode) -> Scenario:
        """
        Generate scenario for only one call
        root_contract -(CALL)-> scenario_contract -(first_call)-> operation_contract.
        """
        scenario_input: ScenarioGeneratorInput = self.scenario_input
        pre: Alloc = scenario_input.pre
        balance = self.balance
        operation_contract = pre.deploy_contract(
            code=scenario_input.operation_code, balance=balance.program_selfbalance
        )

        scenario_contract = pre.deploy_contract(
            code=Op.MSTORE(32, 1122334455)
            + first_call(
                gas=Op.SUB(Op.GAS, self.keep_gas),
                address=operation_contract,
                args_offset=32,
                args_size=40,
                ret_size=32,
                value=balance.first_call_value,
            )
            + Op.RETURN(0, 32),
            balance=balance.scenario_contract_balance,
        )

        root_contract = pre.deploy_contract(
            code=Op.CALL(
                gas=Op.SUB(Op.GAS, self.keep_gas),
                address=scenario_contract,
                ret_size=32,
            )
            + Op.RETURN(0, 32),
            balance=balance.root_contract_balance,
        )

        return Scenario(
            name=f"scenario_{first_call}",
            code=root_contract,
            env=ScenarioEnvironment(
                # Define address on which behalf program is executed
                code_address=(
                    scenario_contract
                    if first_call == Op.CALLCODE or first_call == Op.DELEGATECALL
                    else operation_contract
                ),
                # Define code_caller for Op.CALLER
                code_caller=(
                    root_contract if first_call == Op.DELEGATECALL else scenario_contract
                ),
                # Define balance for Op.BALANCE
                selfbalance=(
                    balance.scenario_contract_balance
                    if first_call in [Op.DELEGATECALL, Op.CALLCODE]
                    else (
                        balance.program_selfbalance
                        if first_call == Op.STATICCALL
                        else balance.first_call_value + balance.program_selfbalance
                    )
                ),
                call_value=(
                    0
                    if first_call in [Op.STATICCALL, Op.DELEGATECALL]
                    else balance.first_call_value
                ),
                call_dataload_0=1122334455,
                call_datasize=40,
                has_static=True if first_call == Op.STATICCALL else False,
            ),
        )

    def _generate_two_call_scenario(self, first_call: Opcode, second_call: Opcode) -> Scenario:
        """
        Generate scenario for two types of calls combination
        root_contract -(CALL)-> scenario_contract -(first_call)-> sub_contract
        sub_contract -(second_call) -> operation_contract.
        """

        def _compute_code_caller() -> Address:
            """
            Calculate who is the code caller in program_contract's code in given sequence
            root -CALL-> scenario_contract -(first_call)-> sub_contract -(second_call)-> program.
            """
            code_caller: Address = root_contract
            if first_call == Op.DELEGATECALL:
                code_caller = scenario_contract
                if second_call == Op.DELEGATECALL:
                    code_caller = root_contract
            else:
                if second_call == Op.DELEGATECALL:
                    code_caller = scenario_contract
                else:
                    code_caller = sub_contract
            if first_call == Op.CALLCODE:
                code_caller = scenario_contract
            return code_caller

        def _compute_selfbalance() -> int:
            """
            Calculate the result of Op.SELFBALANCE in program scope in given sequence
            root -CALL-> scenario_contract -(first_call)-> sub_contract -(second_call)-> program.
            """
            selfbalance: int = 0
            if second_call in [Op.CALL]:
                selfbalance = second_call_value + balance.program_selfbalance
                return selfbalance
            if second_call in [Op.STATICCALL]:
                selfbalance = balance.program_selfbalance
                return selfbalance
            if first_call == Op.STATICCALL and second_call in [Op.DELEGATECALL, Op.CALLCODE]:
                selfbalance = balance.sub_contract_balance
            if first_call in [Op.CALLCODE, Op.DELEGATECALL] and second_call in [
                Op.DELEGATECALL,
                Op.CALLCODE,
            ]:
                selfbalance = balance.scenario_contract_balance + balance.root_call_value
            if first_call == Op.CALL and second_call in [Op.DELEGATECALL, Op.CALLCODE]:
                selfbalance = balance.sub_contract_balance + balance.first_call_value
            if first_call == Op.STATICCALL and second_call == Op.STATICCALL:
                selfbalance = balance.program_selfbalance
            return selfbalance

        def _compute_callvalue() -> int:
            """
            Calculate the expected callvalue in program scope given sequence:
            root -CALL-> scenario_contract -(first_call)-> sub_contract -(second_call)-> program.
            """
            if second_call == Op.STATICCALL:
                return 0
            if second_call == Op.DELEGATECALL:
                if first_call == Op.STATICCALL:
                    return 0
                else:
                    if first_call == Op.DELEGATECALL:
                        return balance.root_call_value
                    else:
                        return balance.first_call_value
            else:
                return second_call_value

        scenario_input = self.scenario_input
        pre: Alloc = scenario_input.pre
        balance = self.balance
        second_call_value = balance.second_call_value if first_call != Op.STATICCALL else 0

        operation_contract = pre.deploy_contract(
            code=scenario_input.operation_code, balance=balance.program_selfbalance
        )
        sub_contract = pre.deploy_contract(
            code=Op.MSTORE(32, 1122334455)
            + second_call(
                gas=Op.SUB(Op.GAS, self.keep_gas),
                address=operation_contract,
                args_size=40,
                args_offset=32,
                ret_size=32,
                value=second_call_value,
            )
            + Op.RETURN(0, 32),
            balance=balance.sub_contract_balance,
        )
        scenario_contract = pre.deploy_contract(
            code=first_call(
                gas=Op.SUB(Op.GAS, self.keep_gas),
                address=sub_contract,
                ret_size=32,
                value=balance.first_call_value,
            )
            + Op.RETURN(0, 32),
            balance=balance.scenario_contract_balance,
        )

        root_contract = pre.deploy_contract(
            balance=balance.root_contract_balance,
            code=Op.CALL(
                gas=Op.SUB(Op.GAS, self.keep_gas),
                address=scenario_contract,
                ret_size=32,
                value=balance.root_call_value,
            )
            + Op.RETURN(0, 32),
        )

        return Scenario(
            name=f"scenario_{first_call}_{second_call}",
            code=root_contract,
            env=ScenarioEnvironment(
                # Define address on which behalf program is executed
                code_address=(
                    operation_contract
                    if second_call not in [Op.CALLCODE, Op.DELEGATECALL]
                    else (
                        sub_contract
                        if first_call not in [Op.CALLCODE, Op.DELEGATECALL]
                        else scenario_contract
                    )
                ),
                # Define code_caller for Op.CALLER
                code_caller=_compute_code_caller(),
                selfbalance=_compute_selfbalance(),
                call_value=_compute_callvalue(),
                call_dataload_0=1122334455,
                call_datasize=40,
                has_static=(
                    True if first_call == Op.STATICCALL or second_call == Op.STATICCALL else False
                ),
            ),
        )
