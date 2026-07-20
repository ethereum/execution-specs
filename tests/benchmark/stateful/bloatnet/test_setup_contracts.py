"""Deploy the CREATE2 contracts for benchmarks."""

import os

from execution_testing import (
    DETERMINISTIC_FACTORY_ADDRESS,
    EOA,
    Account,
    Alloc,
    AuthorizationTuple,
    BenchmarkTestFiller,
    Fork,
    Hash,
    Op,
    Transaction,
    compute_create2_address,
)

from tests.benchmark.helper.account_creator import (
    AccountCreator,
    AccountMode,
)
from tests.benchmark.helper.account_sender_receiver import (
    DELEGATE_BASE_KEY,
)
from tests.benchmark.helper.transactions import (
    pack_transactions_into_blocks,
)
from tests.prague.eip7702_set_code_tx.spec import Spec as Spec7702

# Number of CREATE2 receiver contracts deployed per mode. Overridable via
# BLOATNET_RECEIVER_CONTRACT_COUNT so a smoke/plumbing run (e.g. benchmarkoor
# pre_runs) can deploy a small set for fast iteration; defaults to the full
# 100k benchmark set.
RECEIVER_CONTRACT_COUNT = int(
    os.environ.get("BLOATNET_RECEIVER_CONTRACT_COUNT", "100000")
)

CONTRACT_MODES = [
    AccountMode.EXISTING_CONTRACT_MINIMAL,
    AccountMode.EXISTING_CONTRACT_SAME_MAX,
    AccountMode.EXISTING_CONTRACT_DIFF_MAX,
]

# Factory-frame and initcode execution costs (CALLDATACOPY, the MCOPY
# doubling loop, memory expansion) plus CREATE2's 63/64 retention.
EXECUTION_GAS_BUFFER = 50_000


def deployment_gas_limit(
    fork: Fork, initcode: bytes, runtime_size: int
) -> int:
    """
    Return the gas limit for one CREATE2 deployment, derived from the
    intrinsic, CREATE2, and code-deposit costs with a margin for the
    factory and initcode execution.
    """
    intrinsic = fork.transaction_intrinsic_cost_calculator()(
        calldata=b"\xff" * 32 + initcode
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
    return base + base // 16 + EXECUTION_GAS_BUFFER


def test_deploy_existing_contracts(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_benchmark_value: int,
    tx_gas_limit: int,
) -> None:
    """
    Deploy the contracts behind the `AccountMode.EXISTING_CONTRACT_*`
    receivers via the deterministic CREATE2 factory.

    Delegate deterministic EOAs to EXISTING_CONTRACT_DIFF_MAX receivers.
    """
    txs = []
    post: dict = {}
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
        # Nonce 1 at the CREATE2-derived address proves deployment.
        for salt in (0, RECEIVER_CONTRACT_COUNT - 1):
            contract = compute_create2_address(
                address=DETERMINISTIC_FACTORY_ADDRESS,
                salt=salt,
                initcode=initcode,
            )
            post[contract] = Account(nonce=1)

    # Delegate authority i to the i-th DIFF receiver (EIP-7702).
    delegation_sender = pre.fund_eoa()
    intrinsic = fork.transaction_intrinsic_cost_calculator()
    # DIFF receivers share one initcode; build it once for CREATE2 derivation.
    diff_initcode = AccountCreator(
        AccountMode.EXISTING_CONTRACT_DIFF_MAX
    ).initcode

    base_gas = intrinsic(authorization_list_or_count=0)
    per_auth_gas = intrinsic(authorization_list_or_count=1) - base_gas
    gas_buffer = 100_000
    auths_per_tx = max(
        1, (tx_gas_limit - gas_buffer - base_gas) // per_auth_gas
    )

    for start in range(0, RECEIVER_CONTRACT_COUNT, auths_per_tx):
        count = min(auths_per_tx, RECEIVER_CONTRACT_COUNT - start)
        authorization_list = []
        for i in range(start, start + count):
            authority = EOA(key=DELEGATE_BASE_KEY + i)
            target = compute_create2_address(
                address=DETERMINISTIC_FACTORY_ADDRESS,
                salt=i,
                initcode=diff_initcode,
            )
            authorization_list.append(
                AuthorizationTuple(address=target, nonce=0, signer=authority)
            )
            if i == 0 or i == RECEIVER_CONTRACT_COUNT - 1:
                post[authority] = Account(
                    nonce=1,
                    code=Spec7702.delegation_designation(target),
                )

        txs.append(
            Transaction(
                to=delegation_sender,
                gas_limit=(
                    intrinsic(authorization_list_or_count=count) + gas_buffer
                ),
                sender=delegation_sender,
                authorization_list=authorization_list,
            )
        )

    benchmark_test(
        post=post,
        blocks=pack_transactions_into_blocks(txs, gas_benchmark_value),
        skip_gas_used_validation=True,
        expected_receipt_status=1,
    )
