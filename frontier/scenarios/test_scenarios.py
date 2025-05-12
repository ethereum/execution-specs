"""
Call every possible opcode and test that the subcall is successful
if the opcode is supported by the fork and fails otherwise.
"""

from typing import List

import pytest

from ethereum_test_forks import Fork
from ethereum_test_tools import (
    Account,
    Address,
    Alloc,
    Block,
    BlockchainTestFiller,
    Environment,
    Storage,
    Transaction,
)
from ethereum_test_tools.vm.opcode import Opcodes as Op

from .common import (
    ExecutionEnvironment,
    Scenario,
    ScenarioDebug,
    ScenarioGeneratorInput,
    ScenarioTestProgram,
)
from .programs.all_frontier_opcodes import ProgramAllFrontierOpcodes
from .programs.context_calls import (
    ProgramAddress,
    ProgramBalance,
    ProgramBasefee,
    ProgramBlobBaseFee,
    ProgramBlobhash,
    ProgramBlockhash,
    ProgramCallDataCopy,
    ProgramCallDataLoad,
    ProgramCallDataSize,
    ProgramCaller,
    ProgramCallValue,
    ProgramChainid,
    ProgramCodeCopyCodeSize,
    ProgramCoinbase,
    ProgramDifficultyRandao,
    ProgramExtCodeCopyExtCodeSize,
    ProgramExtCodehash,
    ProgramGasLimit,
    ProgramGasPrice,
    ProgramMcopy,
    ProgramNumber,
    ProgramOrigin,
    ProgramPush0,
    ProgramReturnDataCopy,
    ProgramReturnDataSize,
    ProgramSelfbalance,
    ProgramTimestamp,
    ProgramTload,
)
from .programs.invalid_opcodes import ProgramInvalidOpcode
from .programs.static_violation import (
    ProgramLogs,
    ProgramSstoreSload,
    ProgramSuicide,
    ProgramTstoreTload,
)
from .scenarios.call_combinations import ScenariosCallCombinations
from .scenarios.create_combinations import scenarios_create_combinations
from .scenarios.revert_combinations import scenarios_revert_combinations

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.fixture
def scenarios(fork: Fork, pre: Alloc, test_program: ScenarioTestProgram) -> List[Scenario]:
    """Define fixture vectors of all possible scenarios, given the current pre state input."""
    scenarios_list: List[Scenario] = []

    scenario_input = ScenarioGeneratorInput(
        fork=fork,
        pre=pre,
        operation_code=test_program.make_test_code(pre, fork),
    )

    call_combinations = ScenariosCallCombinations(scenario_input).generate()
    for combination in call_combinations:
        scenarios_list.append(combination)

    call_combinations = scenarios_create_combinations(scenario_input)
    for combination in call_combinations:
        scenarios_list.append(combination)

    revert_combinations = scenarios_revert_combinations(scenario_input)
    for combination in revert_combinations:
        scenarios_list.append(combination)

    return scenarios_list


program_classes = [
    ProgramSstoreSload(),
    ProgramTstoreTload(),
    ProgramLogs(),
    ProgramSuicide(),
    ProgramInvalidOpcode(),
    ProgramAddress(),
    ProgramBalance(),
    ProgramOrigin(),
    ProgramCaller(),
    ProgramCallValue(),
    ProgramCallDataLoad(),
    ProgramCallDataSize(),
    ProgramCallDataCopy(),
    ProgramCodeCopyCodeSize(),
    ProgramGasPrice(),
    ProgramExtCodeCopyExtCodeSize(),
    ProgramReturnDataSize(),
    ProgramReturnDataCopy(),
    ProgramExtCodehash(),
    ProgramBlockhash(),
    ProgramCoinbase(),
    ProgramTimestamp(),
    ProgramNumber(),
    ProgramDifficultyRandao(),
    ProgramGasLimit(),
    ProgramChainid(),
    ProgramSelfbalance(),
    ProgramBasefee(),
    ProgramBlobhash(),
    ProgramBlobBaseFee(),
    ProgramTload(),
    ProgramMcopy(),
    ProgramPush0(),
    ProgramAllFrontierOpcodes(),
]


@pytest.mark.valid_from("Frontier")
@pytest.mark.parametrize(
    # select program to debug ("program_id", "scenario_name")
    # program="" select all programs
    # scenario_name="" select all scenarios
    # Example: [ScenarioDebug(program_id=ProgramSstoreSload().id, scenario_name="scenario_CALL_CALL")],  # noqa: E501
    "debug",
    [ScenarioDebug(program_id="", scenario_name="")],
    ids=["debug"],
)
@pytest.mark.parametrize(
    "test_program",
    program_classes,
    ids=[cls.id for cls in program_classes],
)
@pytest.mark.execute(pytest.mark.skip("Requires gasprice"))
def test_scenarios(
    blockchain_test: BlockchainTestFiller,
    fork: Fork,
    pre: Alloc,
    debug: ScenarioDebug,
    test_program: ScenarioTestProgram,
    scenarios,
):
    """
    Test given operation in different scenarios
    Verify that it's return value equal to expected result on every scenario,
    that is valid for the given fork.

    Note: Don't use pytest parametrize for scenario production, because scenarios will be complex
    Generate one test file for [each operation] * [each scenario] to save space
    As well as operations will be complex too
    """
    tx_env = Environment()
    tx_origin: Address = pre.fund_eoa()

    tests: int = 0
    blocks: List[Block] = []
    post: dict = {}
    for scenario in scenarios:
        if debug.scenario_name and scenario.name != debug.scenario_name:
            continue

        if debug.program_id:
            if test_program.id != debug.program_id:
                continue
        tests = tests + 1

        post_storage = Storage()
        result_slot = post_storage.store_next(1, hint=f"runner result {scenario.name}")

        tx_max_gas = 7_000_000 if test_program.id == ProgramInvalidOpcode().id else 1_000_000
        tx_gasprice: int = 10
        exec_env = ExecutionEnvironment(
            fork=fork,
            origin=tx_origin,
            gasprice=tx_gasprice,
            timestamp=tx_env.timestamp,  # we can't know timestamp before head, use gas hash
            number=len(blocks) + 1,
            gaslimit=tx_env.gas_limit,
            coinbase=tx_env.fee_recipient,
        )

        def make_result(scenario: Scenario, exec_env: ExecutionEnvironment, post: Storage) -> int:
            """Make Scenario post result."""
            if scenario.halts:
                return post.store_next(0, hint=scenario.name)
            else:
                return post.store_next(
                    test_program.result().translate_result(scenario.env, exec_env),
                    hint=scenario.name,
                )

        runner_contract = pre.deploy_contract(
            code=Op.MSTORE(0, 0)
            + Op.CALL(tx_max_gas, scenario.code, 0, 0, 0, 0, 32)
            + Op.SSTORE(make_result(scenario, exec_env, post_storage), Op.MLOAD(0))
            + Op.SSTORE(result_slot, 1),
            storage={
                result_slot: 0xFFFF,
            },
        )

        tx = Transaction(
            sender=tx_origin,
            gas_limit=tx_max_gas + 100_000,
            gas_price=tx_gasprice,
            to=runner_contract,
            data=bytes.fromhex("11223344"),
            value=0,
            protected=False,
        )

        post[runner_contract] = Account(storage=post_storage)
        blocks.append(Block(txs=[tx], post=post))

    if tests > 0:
        blockchain_test(
            pre=pre,
            blocks=blocks,
            post=post,
        )
