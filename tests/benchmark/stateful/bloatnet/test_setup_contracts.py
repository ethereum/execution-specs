"""Deploy the CREATE2 contracts for benchmarks."""

from execution_testing import (
    DETERMINISTIC_FACTORY_ADDRESS,
    Alloc,
    BenchmarkTestFiller,
    Fork,
    Hash,
    Op,
    Transaction,
)

from tests.benchmark.helper.account_creator import (
    AccountCreator,
    AccountMode,
)
from tests.benchmark.stateful.helpers import (
    pack_transactions_into_blocks,
)

RECEIVER_CONTRACT_COUNT = 120_000

CONTRACT_MODES = [
    AccountMode.EXISTING_CONTRACT_MINIMAL,
    AccountMode.EXISTING_CONTRACT_SAME,
    AccountMode.EXISTING_CONTRACT_DIFF,
]


def deployment_gas_limit(
    fork: Fork, initcode: bytes, runtime_size: int
) -> int:
    """
    Return the gas limit for one CREATE2 deployment, derived from the
    intrinsic, CREATE2, and code-deposit costs with a small margin.
    """
    intrinsic = fork.transaction_intrinsic_cost_calculator()(
        calldata=Hash(0) + initcode
    )
    create_cost = Op.CREATE2(
        value=0,
        offset=0,
        size=len(initcode),
        salt=0,
        init_code_size=len(initcode),
    ).gas_cost(fork)
    deposit_cost = Op.RETURN(
        0,
        runtime_size,
        code_deposit_size=runtime_size,
    ).gas_cost(fork)
    base = intrinsic + create_cost + deposit_cost
    return base + base // 16


def test_deploy_existing_contracts(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_benchmark_value: int,
) -> None:
    """
    Deploy the contracts behind the `AccountMode.EXISTING_CONTRACT_*`
    receivers via the deterministic CREATE2 factory.
    """
    txs = []
    for account_mode in CONTRACT_MODES:
        creator = AccountCreator(account_mode)
        initcode = creator.initcode
        gas_limit = deployment_gas_limit(fork, initcode, creator.runtime_size)
        sender = pre.fund_eoa()
        for salt in range(RECEIVER_CONTRACT_COUNT):
            txs.append(
                Transaction(
                    to=DETERMINISTIC_FACTORY_ADDRESS,
                    data=Hash(salt) + initcode,
                    gas_limit=gas_limit,
                    sender=sender,
                )
            )

    blocks = pack_transactions_into_blocks(txs, gas_benchmark_value)

    benchmark_test(
        blocks=blocks,
        skip_gas_used_validation=True,
        expected_receipt_status=1,
    )
