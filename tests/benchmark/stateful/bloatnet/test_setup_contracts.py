"""Deploy the CREATE2 contracts for benchmarks."""

import os

import pytest
from execution_testing import (
    DETERMINISTIC_FACTORY_ADDRESS,
    DETERMINISTIC_FACTORY_BYTECODE,
    EOA,
    Account,
    Alloc,
    AuthorizationTuple,
    BenchmarkTestFiller,
    Fork,
    Hash,
    Op,
    TransactionWithCost,
    compute_create2_address,
)
from execution_testing.forks import Amsterdam, Osaka

from tests.benchmark.helper.account_creator import (
    AccountCreator,
    AccountMode,
)
from tests.benchmark.helper.account_sender_receiver import (
    delegate_base_key,
)
from tests.benchmark.helper.transactions import (
    pack_transactions_with_cost_into_blocks,
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
    AccountMode.EXISTING_CONTRACT_SAME_MAX,
    AccountMode.EXISTING_CONTRACT_DIFF_MAX,
]

# Factory-frame and initcode execution costs (CALLDATACOPY, the MCOPY
# doubling loop, memory expansion) plus CREATE2's 63/64 retention.
EXECUTION_GAS_BUFFER = 50_000


def deployment_gas(
    fork: Fork, initcode: bytes, runtime_size: int
) -> tuple[int, int]:
    """
    Return the (regular, state) gas for one CREATE2 deployment, derived
    from the intrinsic, CREATE2, and code-deposit costs with a margin
    for the factory and initcode execution.

    The opcode costs are two-dimensional totals, so the state gas the
    account creation and the code deposit charge is split back out; the
    margin lands on the regular side, which is what it pays for.
    """
    initcode_size = len(initcode)
    intrinsic = fork.transaction_intrinsic_cost_calculator()(
        calldata=b"\xff" * 32 + initcode
    )
    create_cost = Op.CREATE2(
        value=0,
        offset=0,
        size=initcode_size,
        salt=0,
        # Gas accounting
        init_code_size=initcode_size,
    ).gas_cost(fork)
    # The factory frame wrapped around that CREATE2: its own bytecode,
    # less the CREATE2 already counted above, plus the copy of the
    # initcode out of the calldata that the bytecode alone cannot size.
    factory_cost = (
        DETERMINISTIC_FACTORY_BYTECODE.gas_cost(fork)
        - Op.CREATE2(value=0, offset=0, size=0, salt=0).gas_cost(fork)
        + Op.CALLDATACOPY(
            dest_offset=0,
            offset=32,
            size=initcode_size,
            # Gas accounting
            data_size=initcode_size,
            old_memory_size=0,
            new_memory_size=initcode_size,
        ).gas_cost(fork)
    )
    deposit_cost = Op.RETURN(
        0,
        runtime_size,
        code_deposit_size=runtime_size,
    ).gas_cost(fork)
    base = intrinsic + factory_cost + create_cost + deposit_cost
    state = fork.create_state_gas(code_size=runtime_size)
    regular = base - state + base // 16 + EXECUTION_GAS_BUFFER
    return regular, state


@pytest.mark.valid_from("Amsterdam")
@pytest.mark.parametrize(
    "code_size", [Osaka.max_code_size(), Amsterdam.max_code_size()]
)
def test_deploy_existing_contracts(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_benchmark_value: int,
    tx_gas_limit: int,
    code_size: int,
) -> None:
    """
    Deploy the contracts behind the `AccountMode.EXISTING_CONTRACT_*`
    receivers via the deterministic CREATE2 factory.

    Delegate deterministic EOAs to EXISTING_CONTRACT_DIFF_MAX receivers.
    """
    contract_modes = list(CONTRACT_MODES)
    # One STOP byte: same initcode and CREATE2 address at every code size,
    # so a second deployment would collide and revert the factory.
    if code_size == Osaka.max_code_size():
        contract_modes.append(AccountMode.EXISTING_CONTRACT_MINIMAL)
    if code_size == Amsterdam.max_code_size():
        contract_modes.append(AccountMode.EXISTING_CONTRACT_JUMPDEST)

    txs = []
    post: dict = {}
    for account_mode in contract_modes:
        creator = AccountCreator(account_mode, code_size=code_size)
        initcode = creator.initcode
        regular_gas, state_gas = deployment_gas(
            fork, initcode, creator.runtime_size
        )
        sender = pre.fund_eoa()
        for salt in range(RECEIVER_CONTRACT_COUNT):
            txs.append(
                TransactionWithCost(
                    to=DETERMINISTIC_FACTORY_ADDRESS,
                    data=Hash(salt) + initcode,
                    gas_limit=regular_gas + state_gas,
                    sender=sender,
                    execution_cost=regular_gas,
                    state_cost=state_gas,
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
    top_frame = fork.transaction_top_frame_gas_calculator()
    # DIFF receivers share one initcode; build it once for CREATE2 derivation.
    diff_initcode = AccountCreator(
        AccountMode.EXISTING_CONTRACT_DIFF_MAX, code_size=code_size
    ).initcode

    base_key = delegate_base_key(code_size)
    authorizations = []
    for i in range(RECEIVER_CONTRACT_COUNT):
        authority = EOA(key=base_key + i)
        target = compute_create2_address(
            address=DETERMINISTIC_FACTORY_ADDRESS,
            salt=i,
            initcode=diff_initcode,
        )
        authorizations.append(
            AuthorizationTuple(
                address=target,
                nonce=0,
                signer=authority,
                # The authorities are deterministic and never funded, so
                # applying the delegation is what brings them into being.
                creates_account=True,
            )
        )
        if i == 0 or i == RECEIVER_CONTRACT_COUNT - 1:
            post[authority] = Account(
                nonce=1,
                code=Spec7702.delegation_designation(target),
            )

    def authorization_gas(
        authorization_list: list[AuthorizationTuple],
    ) -> tuple[int, int]:
        """Return the (regular, state) gas an authorization list costs."""
        regular = intrinsic(
            authorization_list_or_count=len(authorization_list)
        ) + top_frame(authorizations=authorization_list)
        state = fork.transaction_top_frame_state_gas(
            authorizations=authorization_list
        )
        return regular, state

    gas_buffer = 100_000
    base_regular, base_state = authorization_gas([])
    one_regular, one_state = authorization_gas(authorizations[:1])
    per_auth_gas = (one_regular + one_state) - (base_regular + base_state)
    auths_per_tx = max(
        1,
        (tx_gas_limit - gas_buffer - base_regular - base_state)
        // per_auth_gas,
    )

    for start in range(0, RECEIVER_CONTRACT_COUNT, auths_per_tx):
        authorization_list = authorizations[start : start + auths_per_tx]
        regular_gas, state_gas = authorization_gas(authorization_list)
        txs.append(
            TransactionWithCost(
                to=delegation_sender,
                gas_limit=regular_gas + state_gas + gas_buffer,
                sender=delegation_sender,
                authorization_list=authorization_list,
                execution_cost=regular_gas + gas_buffer,
                state_cost=state_gas,
            )
        )

    benchmark_test(
        post=post,
        blocks=pack_transactions_with_cost_into_blocks(
            txs, gas_benchmark_value
        ),
        skip_gas_used_validation=True,
        expected_receipt_status=1,
    )
