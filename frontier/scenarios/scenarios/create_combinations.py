"""Define Scenario that will put a given program in create contexts."""

from dataclasses import dataclass
from typing import List

from ethereum_test_tools import Alloc, Bytecode
from ethereum_test_tools.vm.opcode import Macros as Om
from ethereum_test_tools.vm.opcode import Opcode
from ethereum_test_tools.vm.opcode import Opcodes as Op
from ethereum_test_types import compute_create_address
from ethereum_test_vm import EVMCodeType

from ..common import Scenario, ScenarioEnvironment, ScenarioGeneratorInput


@dataclass
class AddressBalance:
    """Definition of values we use to put in contract balances and call."""

    root_call_value = 1
    create_value = 3
    call_value = 5
    root_contract_balance = 100
    scenario_contract_balance = 200


def scenarios_create_combinations(scenario_input: ScenarioGeneratorInput) -> List[Scenario]:
    """Generate Scenarios for create combinations."""

    def _compute_selfbalance() -> int:
        """Compute selfbalance opcode for root -> call -> scenario -> create | [call*] -> program."""  # noqa: E501
        if call in [Op.DELEGATECALL, Op.CALLCODE]:
            return (
                balance.scenario_contract_balance + balance.root_call_value - balance.create_value
            )
        if call == Op.CALL:
            return balance.create_value + balance.call_value
        return balance.create_value

    scenarios_list: List[Scenario] = []
    keep_gas = 100000
    create_types: List[Opcode] = [
        create_code
        for create_code, evm_type in scenario_input.fork.create_opcodes()
        if evm_type == EVMCodeType.LEGACY
    ]
    env: ScenarioEnvironment
    balance: AddressBalance = AddressBalance()

    # run code in create constructor
    for create in create_types:
        salt = [0] if create == Op.CREATE2 else []
        operation_contract = scenario_input.pre.deploy_contract(code=scenario_input.operation_code)

        # the code result in init code will be actually code of a deployed contract
        scenario_contract = scenario_input.pre.deploy_contract(
            balance=3,
            code=Op.EXTCODECOPY(operation_contract, 0, 0, Op.EXTCODESIZE(operation_contract))
            + Op.MSTORE(0, create(3, 0, Op.EXTCODESIZE(operation_contract), *salt))
            + Op.EXTCODECOPY(Op.MLOAD(0), 0, 0, 32)
            + Op.RETURN(0, 32),
        )

        created_address = compute_create_address(
            address=scenario_contract,
            nonce=1,
            initcode=scenario_input.operation_code,
            opcode=Op.CREATE if create == Op.CREATE else Op.CREATE2,
        )

        env = ScenarioEnvironment(
            # Define address on which behalf program is executed
            code_address=created_address,
            code_caller=scenario_contract,
            selfbalance=3,
            call_value=3,
            call_dataload_0=0,
            call_datasize=0,
        )
        scenarios_list.append(
            Scenario(
                category="create_constructor_combinations",
                name=f"scenario_{create}_constructor",
                code=scenario_contract,
                env=env,
            )
        )

    # create a contract with test code and call it
    deploy_code = Bytecode(
        Op.EXTCODECOPY(operation_contract, 0, 0, Op.EXTCODESIZE(operation_contract))
        + Op.RETURN(0, Op.EXTCODESIZE(operation_contract))
    )
    deploy_code_size: int = int(len(deploy_code.hex()) / 2)
    call_types: List[Opcode] = [
        callcode
        for callcode, evm_type in scenario_input.fork.call_opcodes()
        if evm_type == EVMCodeType.LEGACY
    ]

    pre: Alloc = scenario_input.pre
    for create in create_types:
        for call in call_types:
            salt = [0] if create == Op.CREATE2 else []

            scenario_contract = pre.deploy_contract(
                balance=balance.scenario_contract_balance,
                code=Om.MSTORE(deploy_code, 0)
                + Op.MSTORE(32, create(balance.create_value, 0, deploy_code_size, *salt))
                + Op.MSTORE(0, 0)
                + Op.MSTORE(64, 1122334455)
                + call(
                    gas=Op.SUB(Op.GAS, keep_gas),
                    address=Op.MLOAD(32),
                    args_offset=64,
                    args_size=40,
                    ret_offset=0,
                    ret_size=32,
                    value=balance.call_value,
                )
                + Op.RETURN(0, 32),
            )

            root_contract = pre.deploy_contract(
                balance=balance.root_contract_balance,
                code=Op.CALL(
                    gas=Op.SUB(Op.GAS, keep_gas),
                    address=scenario_contract,
                    ret_size=32,
                    value=balance.root_call_value,
                )
                + Op.RETURN(0, 32),
            )

            created_address = compute_create_address(
                address=scenario_contract,
                nonce=1,
                initcode=deploy_code,
                opcode=Op.CREATE if create == Op.CREATE else Op.CREATE2,
            )

            env = ScenarioEnvironment(
                # Define address on which behalf program is executed
                code_address=(
                    scenario_contract
                    if call in [Op.CALLCODE, Op.DELEGATECALL]
                    else created_address
                ),
                code_caller=root_contract if call == Op.DELEGATECALL else scenario_contract,
                selfbalance=_compute_selfbalance(),
                call_value=(
                    0
                    if call in [Op.STATICCALL]
                    else (
                        balance.root_call_value
                        if call in [Op.DELEGATECALL]
                        else balance.call_value
                    )
                ),
                call_dataload_0=1122334455,
                call_datasize=40,
                has_static=True if call == Op.STATICCALL else False,
            )
            scenarios_list.append(
                Scenario(
                    category="create_call_combinations",
                    name=f"scenario_{create}_then_{call}",
                    code=root_contract,
                    env=env,
                )
            )

    return scenarios_list
