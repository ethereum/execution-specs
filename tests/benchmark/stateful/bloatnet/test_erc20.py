"""
abstract: BloatNet ERC20 targets (can be used on any deployed ERC20 contract)
Tests storage operations.
"""

import json
import math
from pathlib import Path
from execution_testing.specs.benchmark import BenchmarkTestFiller
from execution_testing.test_types import Environment
import pytest
from execution_testing import (
    Account,
    Alloc,
    Block,
    BlockchainTestFiller,
    Bytecode,
    Fork,
    Op,
    Transaction,
    While,
    TestPhaseManager
)


# ERC20 function selectors
APPROVE_SELECTOR = 0x095EA7B3  # approve(address,uint256)
ALLOWANCE_SELECTOR = 0xDD62ED3E  # allowance(address,address)

# Load token names from stubs.json for test parametrization
_STUBS_FILE = Path(__file__).parent / "stubs.json"
with open(_STUBS_FILE) as f:
    _STUBS = json.load(f)

# Extract unique token names for each test type
TARGET_TOKENS = [
    k.replace("test_erc20_", "")
    for k in _STUBS.keys()
    if k.startswith("test_erc20_")
]

MAX_UINT256 = (1 << 256) - 1

# TODO: add SLOAD variant, this is the below contract except changed
# where it calls allowance instead of writing to approve()
# TODO: add warm gas costs, in the form of access list
# For each contract stub we need to know the position offset of the approval map
# To calculate the accessed storage slot allowance[x][y], this is:
# map[x] = keccak256(bytes32(p) + bytes32(x))
# map[x][y] = keccak256(map[x] + bytes32(y))
# NOTE: `p` is supposed to be in the stub and should be extracted
# The naming is `test_erc20_TOKENNAME_allowance_X`
# Note, seems that standard contracts seem to have this at pos 1.

@pytest.mark.valid_from("Osaka")
@pytest.mark.parametrize("token_name", TARGET_TOKENS)
@pytest.mark.parametrize("initial", [0, MAX_UINT256])
@pytest.mark.parametrize("target", [0, MAX_UINT256, 2])
@pytest.mark.parametrize("warm", [False, True])
@pytest.mark.repricing
def test_sstore_erc20(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_benchmark_value: int,
    tx_gas_limit: int,
    token_name: str,
    initial: int,
    target: int,
    warm: bool,
    env: Environment
) -> None:
    stub_name = next((item for item in _STUBS 
                      if item.startswith(f"test_erc20_{token_name}")), None)
    
    cheapest_write_cost = 1900
    setup_write_costs = 30000 # This value should be higher than the actual cost 
                              #to setup 1 storage slot in the ERC20 contract
    target_slots = gas_benchmark_value // cheapest_write_cost

    after_loop_costs_minimum = 30000 # gas necessary for the final steps after the loop

    erc20_address = pre.deploy_contract(
        code=Bytecode(),
        stub=stub_name,
    )

    # attack contract has two modes
    # if called with callvalue then attack, otherwise fill
    # fill: delegatecall to fill contract
    # saves the jump stuff

    initial_setup = Op.MSTORE(128, Op.ISZERO(Op.CALLVALUE))
    
    code_init_memory = (Op.MSTORE(0, APPROVE_SELECTOR)
                        + Op.MSTORE(32, Op.SLOAD(Op.MLOAD(128)))
                        + Op.MSTORE(64, target))
    
    code_loop = Op.POP(Op.STATICCALL(address=erc20_address, args_offset=28, args_size=68))
                 
    if not warm:
        code_loop = code_loop + Op.MSTORE(32, Op.ADD(Op.MLOAD(32), 1))
    
    set_min_gas = (Op.GAS + code_loop + Op.GAS + Op.SWAP1 + Op.SUB +
                    Op.PUSH32(after_loop_costs_minimum) + Op.ADD + Op.PUSH1(96) + Op.MSTORE)

    loop = While(body=code_loop, condition=Op.GT(Op.GAS, Op.MLOAD(96)))

    final_steps = Op.SSTORE(Op.MLOAD(128), Op.MLOAD(32))

    code = initial_setup + code_init_memory + code_loop + set_min_gas + loop + final_steps

    contract = pre.deploy_contract(code=code)

    sender = pre.fund_eoa()

    blocks = []

    tx_cost = fork.transaction_intrinsic_cost_calculator()

    if initial != 0:
        with TestPhaseManager.setup():
            current_slots = 0
            while current_slots < target_slots:
                remaining_gas = env.gas_limit
                txs = []
                while remaining_gas > 0 and current_slots < target_slots:
                    gas_limit=tx_gas_limit if remaining_gas > tx_gas_limit else remaining_gas
                    if gas_limit < tx_cost():
                        break
                    txs.append(Transaction(
                        to=contract,
                        gas_limit=gas_limit,
                        sender=sender
                    ))
                    remaining_gas = remaining_gas - gas_limit
                    current_slots = current_slots + gas_limit // setup_write_costs
                blocks.append(Block(txs=txs))

    with TestPhaseManager.execution():
        remaining_gas = gas_benchmark_value
        txs = []
        while remaining_gas > 0:
            gas_limit=tx_gas_limit if remaining_gas > tx_gas_limit else remaining_gas
            if gas_limit < tx_cost():
                break
            txs.append(Transaction(
                to=contract,
                gas_limit=gas_limit,
                value=1,
                sender=sender
            ))
            remaining_gas = remaining_gas - gas_limit
        blocks.append(Block(txs=txs))
    benchmark_test(blocks=blocks,post={}, skip_gas_used_validation=True)
