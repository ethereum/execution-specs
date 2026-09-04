"""Test the independent gas budgets of EIP-8037 protocol system calls."""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Block,
    BlockchainTestFiller,
    BlockException,
    Bytecode,
    EIPChecklist,
    Environment,
    Fork,
    Header,
    Op,
)

from ...cancun.eip4788_beacon_root.spec import Spec as BeaconSpec
from ...prague.eip2935_historical_block_hashes_from_state.spec import (
    Spec as HistorySpec,
)
from ...prague.eip7002_el_triggerable_withdrawals.spec import (
    Spec as WithdrawalSpec,
)
from ...prague.eip7251_consolidations.spec import Spec as ConsolidationSpec
from .spec import Spec, ref_spec_8037

REFERENCE_SPEC_GIT_PATH = ref_spec_8037.git_path
REFERENCE_SPEC_VERSION = ref_spec_8037.version

pytestmark = [
    pytest.mark.valid_from("EIP8037"),
    pytest.mark.pre_alloc_mutable,
]

SYSTEM_CONTRACTS = [
    (BeaconSpec.BEACON_ROOTS_ADDRESS, False, "beacon"),
    (HistorySpec.HISTORY_STORAGE_ADDRESS, False, "history"),
    (WithdrawalSpec.WITHDRAWAL_REQUEST_PREDEPLOY_ADDRESS, True, "withdrawals"),
    (
        ConsolidationSpec.CONSOLIDATION_REQUEST_PREDEPLOY_ADDRESS,
        True,
        "consolidations",
    ),
]
system_contract_cases = pytest.mark.parametrize(
    "system_contract",
    [pytest.param(address, id=name) for address, _, name in SYSTEM_CONTRACTS],
)


@system_contract_cases
@EIPChecklist.GasCostChanges.Test.GasUpdatesMeasurement()
def test_system_call_execution_grant(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    system_contract: int,
) -> None:
    """Keep the execution grant independent of the reservoir and tx cap."""
    address = Address(system_contract)
    # GAS executes first, before the key is pushed for SSTORE.
    code = Op.SSTORE(0, Op.GAS)
    pre[address] = Account(code=code)
    expected = WithdrawalSpec.SYSTEM_CALL_GAS_LIMIT - Op.GAS.gas_cost(fork)
    blockchain_test(
        pre=pre,
        genesis_environment=Environment(gas_limit=1_000_000),
        blocks=[Block(txs=[], header_verify=Header(gas_used=0))],
        post={address: Account(storage={0: expected})},
    )


@system_contract_cases
@EIPChecklist.GasCostChanges.Test.OutOfGas()
@pytest.mark.parametrize("allow_spill", [False, True])
def test_system_call_reservoir_boundary(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    system_contract: int,
    allow_spill: bool,
) -> None:
    """Fund the reservoir-sized prefix, then require spill for one more set."""
    count = Spec.SYSTEM_MAX_SSTORES_PER_CALL
    probe_code = Op.SSTORE(0, 1)
    code = Bytecode()
    post = {}
    for i in range(count + 1):
        succeeds = i < count or allow_spill
        probe = pre.deploy_contract(code=probe_code)
        grant = probe_code.execution_cost(fork)
        if i == count and allow_spill:
            grant += probe_code.state_cost(fork)
        code += Op.SSTORE(i, Op.CALL(gas=grant, address=probe))
        post[probe] = Account(storage={0: int(succeeds)})
    address = Address(system_contract)
    # Pre-existing result slots keep instrumentation out of the state budget.
    pre[address] = Account(
        code=code, storage=dict.fromkeys(range(count + 1), 2)
    )
    post[address] = Account(
        storage={i: int(i < count or allow_spill) for i in range(count + 1)}
    )
    blockchain_test(
        pre=pre,
        genesis_environment=Environment(gas_limit=1_000_000),
        blocks=[Block(txs=[], header_verify=Header(gas_used=0))],
        post=post,
    )


@pytest.fixture
def execution_boundary_code(fork: Fork) -> Bytecode:
    """Spend the full execution grant while leaving state gas available."""
    budget = WithdrawalSpec.SYSTEM_CALL_GAS_LIMIT
    marker = Op.SSTORE(0, 1)

    # Memory expansion spends most of the grant with a single instruction.
    def prefix_for(words: int) -> Bytecode:
        return marker + Op.MSTORE8(
            words * 32 - 1, 0, new_memory_size=words * 32
        )

    low, high = 1, 2
    while prefix_for(high).execution_cost(fork) <= budget:
        low, high = high, high * 2
    while low + 1 < high:
        middle = (low + high) // 2
        if prefix_for(middle).execution_cost(fork) <= budget:
            low = middle
        else:
            high = middle
    prefix = prefix_for(low)
    padding = budget - prefix.execution_cost(fork)
    assert padding >= 0
    return prefix + Op.JUMPDEST * padding


@pytest.mark.parametrize(
    "system_contract,checked,extra_execution",
    [
        pytest.param(
            address,
            checked,
            extra,
            id=f"{name}-{'one_over' if extra else 'exact'}",
            marks=pytest.mark.exception_test if checked and extra else (),
        )
        for address, checked, name in SYSTEM_CONTRACTS
        for extra in (0, 1)
    ],
)
@EIPChecklist.GasCostChanges.Test.OutOfGas()
def test_system_call_execution_boundary(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    system_contract: int,
    checked: bool,
    extra_execution: int,
    execution_boundary_code: Bytecode,
) -> None:
    """Exhaust execution gas without borrowing the unspent reservoir."""
    code = execution_boundary_code + Op.JUMPDEST * extra_execution
    address = Address(system_contract)
    pre[address] = Account(code=code)
    fails_block = checked and extra_execution > 0
    blockchain_test(
        pre=pre,
        genesis_environment=Environment(gas_limit=1_000_000),
        blocks=[
            Block(
                txs=[],
                exception=BlockException.SYSTEM_CONTRACT_CALL_FAILED
                if fails_block
                else None,
                header_verify=None if fails_block else Header(gas_used=0),
            )
        ],
        post={address: Account(storage={0: int(extra_execution == 0)})},
    )
