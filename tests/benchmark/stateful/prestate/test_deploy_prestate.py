"""
Prestate deployers: create the on-chain accounts the stateful repricing
benchmarks expect, on a live mainnet fork (jochemnet).

The stateful benchmarks under `tests/benchmark/stateful/bloatnet` do NOT
deploy their own targets -- their setup phase only deploys the caller
harness. Targets are looked up at fixed, deterministic addresses and are
assumed to already exist on the network. On jochemnet three CREATE2
target families and the EIP-7702 delegate authorities are absent, which
blocks every `EXISTING_CONTRACT_{MINIMAL,SAME_MAX,DIFF_MAX}` and
`diff_to_delegated_contract_diff` parametrisation.

These deployers close that gap. Fill them once, replay the payloads onto
the snapshot, and freeze the result as the new prestate.

# Address derivation must match the benchmarks exactly

Targets are CREATE2 deployments from `DETERMINISTIC_FACTORY_ADDRESS` with
`salt = index` and mode-specific initcode, mirroring
`AccountCreator.target_address_of` / `yield_distinct_create2_receiver`.
The initcode is taken from `AccountCreator` itself rather than
re-derived, so the addresses cannot drift from what the benchmarks probe.

`AccountCreator` pins `code_size` to `DEFAULT_CODE_SIZE`
(= Osaka's 24576) even on Amsterdam, which raises `max_code_size` to
65536. Do not "fix" this to Amsterdam's max: it would change every
target address.

# EIP-8037 state gas (Amsterdam)

Creating accounts and depositing code charge *state gas*, priced at
`cost_per_state_byte()` (1530 on Amsterdam) per state byte:

    24 KiB contract  ->  create_state_gas() = 37,784,880
                         (24576 bytes of code + 120 bytes of account)
    1-byte contract  ->  create_state_gas() =    185,130

State gas is paid from a per-transaction *reservoir*, and
`allocate_evm_gas` funds that reservoir with exactly the portion of
`tx.gas` that exceeds `transaction_gas_limit_cap()` (16,777,216):

    evm_gas             = tx.gas - intrinsic
    execution_gas       = min(cap - intrinsic, evm_gas)
    state_gas_reservoir = evm_gas - execution_gas

So a deployer transaction MUST request a gas limit far above the cap.
A 24 KiB deploy needs ~5M execution gas but ~37.8M state gas; requesting
only the cap would leave an empty reservoir, spill the state gas into the
capped execution grant, and run out of gas. This is the one thing that
makes these deployers Amsterdam-specific -- `state_gas_budget()` below
returns 0 on pre-8037 forks, so the same tests still fill on Osaka.

Because the block header's `gasUsed` is
`max(block_gas_used, block_state_gas_used)`, state gas -- not execution
gas -- is what bounds a block here: ~26 deploys per 1 GGas of block
budget for the 24 KiB families.
"""

import itertools
from typing import Generator

import pytest
from execution_testing import (
    DETERMINISTIC_FACTORY_ADDRESS,
    Address,
    Alloc,
    AuthorizationTuple,
    BenchmarkTestFiller,
    Block,
    Fork,
    Transaction,
    Withdrawal,
)

from tests.benchmark.helper.account_creator import (
    AccountCreator,
    AccountMode,
)
from tests.benchmark.helper.account_sender_receiver import (
    yield_distinct_delegate_receiver,
    yield_distinct_sender,
)

# Target count per family. The benchmarks consume targets sequentially
# from salt 0, one per iteration, so this must cover the largest
# iteration count any benchmark reaches (~115k at 300M gas).
TARGET_COUNT = 150_000

# Families missing from jochemnet. EXISTING_CONTRACT_JUMPDEST is already
# deployed there (its initcode class is literally named
# JochemnetPredeployContractInitcode), so it is deliberately excluded.
MISSING_CONTRACT_MODES = [
    AccountMode.EXISTING_CONTRACT_MINIMAL,
    AccountMode.EXISTING_CONTRACT_SAME_MAX,
    AccountMode.EXISTING_CONTRACT_DIFF_MAX,
]

# Senders the benchmarks draw from. A transfer costs ~20k gas, so a 300M
# gas block can only send from ~15k distinct senders -- unlike targets,
# which cost ~2k and so reach 150k. Matches the original funding payload
# (15,001 withdrawals of 2**64-1 gwei, zero transactions).
FUNDED_SENDER_COUNT = 15_000
WITHDRAWAL_AMOUNT_GWEI = 2**64 - 1

# The historical funding payload credited 15,001 addresses: the 15,000
# senders plus this one, first, at withdrawal index 2. It is neither a
# sender nor a delegate authority nor the Anvil dev key -- it is that
# run's `--rpc-seed-key` account, funded so the filler itself can
# operate. Credited here too so this block is a superset of the original.
LEGACY_FILL_SEED = Address(0x86CF016FB873D50A7B8F31EB154C9234DD31B058)

# Per-block ceiling on state gas. The header's gasUsed is
# max(execution, state), so this bounds block count for the 24 KiB
# families (~23.8k deploys/block). Kept below jochemnet's 1e12 limit
# with headroom for the execution side.
STATE_GAS_PER_BLOCK = 900_000_000_000

# Balance for the dedicated deployer, funded from the seed via
# `pre.fund_eoa`. Generous: 150k deploys at ~42.8M gas each is a few
# thousand ETH at any sane fee, and the seed holds billions.
DEPLOYER_BALANCE = 10**24

# Hard cap on transactions per block, independent of gas. State gas does
# not bind for cheap deploys -- a 1-byte contract costs only 185,130, so
# the budget above would allow ~4.9M of them in one block -- but every
# block is submitted as a single `testing_buildBlockV1` request, and
# geth's HTTP body limit is 5 MiB. At roughly 315 bytes per encoded
# transaction, 5,000 keeps a request near 1.6 MiB.
MAX_TXS_PER_BLOCK = 5_000

# Execution-gas allowance per CREATE2 deploy: CREATE2 (32000), the
# 200/byte code deposit, initcode execution (an MCOPY doubling loop) and
# the factory's own dispatch. Rounded up -- unused gas is refunded, and
# the cap check below keeps it honest.
CREATE2_EXECUTION_OVERHEAD = 120_000
CODE_DEPOSIT_GAS_PER_BYTE = 200


def state_gas_budget(fork: Fork, *, code_size: int) -> int:
    """
    State gas a single CREATE2 deploy must have in its reservoir.

    Zero on forks without EIP-8037, which makes these deployers
    fork-agnostic.
    """
    if not fork.state_gas_reservoir_enabled():
        return 0
    return fork.create_state_gas(code_size=code_size)


def deploy_gas_limit(fork: Fork, *, code_size: int, initcode: bytes) -> int:
    """
    Gas limit for one CREATE2 deploy transaction.

    Sized as intrinsic + execution + state gas, so that
    `allocate_evm_gas` leaves the state gas above the cap in the
    reservoir instead of spilling it into the execution grant.

    The intrinsic cost is computed against an all-0xff salt: calldata is
    16 gas per non-zero byte versus 4 per zero byte, so this bounds every
    salt in the range with one calculation. Over-requesting is safe --
    unused gas is refunded -- while under-requesting would abort the
    deploy.
    """
    intrinsic = fork.transaction_intrinsic_cost_calculator()(
        calldata=b"\xff" * 32 + initcode
    )
    execution = (
        CREATE2_EXECUTION_OVERHEAD + CODE_DEPOSIT_GAS_PER_BYTE * code_size
    )
    cap = fork.transaction_gas_limit_cap()
    if cap is not None and intrinsic + execution > cap:
        pytest.fail(
            f"execution gas {intrinsic + execution} exceeds the transaction "
            f"gas limit cap {cap}; a {code_size}-byte deploy cannot fit in "
            "one transaction on this fork"
        )
    return intrinsic + execution + state_gas_budget(fork, code_size=code_size)


def chunk_into_blocks(
    txs: list[Transaction], state_gas_each: int
) -> Generator[list[Transaction], None, None]:
    """Split transactions into blocks bounded by state gas and request size."""
    per_block = max(1, STATE_GAS_PER_BLOCK // max(1, state_gas_each))
    per_block = min(per_block, MAX_TXS_PER_BLOCK)
    for start in range(0, len(txs), per_block):
        yield txs[start : start + per_block]


@pytest.mark.repricing
@pytest.mark.parametrize(
    "mode", MISSING_CONTRACT_MODES, ids=lambda m: m.name
)
def test_deploy_create2_targets(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    mode: AccountMode,
) -> None:
    """
    Deploy TARGET_COUNT CREATE2 targets for one account mode.

    Salt i deploys the target the benchmarks look up at index i, so the
    resulting addresses are exactly those probed by
    `yield_distinct_create2_receiver(creator.initcode)`.
    """
    creator = AccountCreator(mode)
    initcode = creator.initcode
    code_size = creator.runtime_size

    # Arachnid deterministic factory calldata: 32-byte salt ++ initcode.
    gas_limit = deploy_gas_limit(
        fork, code_size=code_size, initcode=initcode
    )
    state_each = state_gas_budget(fork, code_size=code_size)

    # One dedicated deployer, funded from the seed. Every address in `pre`
    # is re-read over RPC each block by `get_alloc` (getBalance + getCode +
    # getTransactionCount), so a distinct sender per deploy costs ~3 round
    # trips per deploy and dominates the fill. One sender keeps that at
    # three calls per block. It also leaves the benchmark sender pool
    # untouched -- EEST keeps those accounts out of the pre-alloc so they
    # stay uncached, and deploying from them would warm all 15,000.
    deployer = pre.fund_eoa(DEPLOYER_BALANCE)
    txs = [
        Transaction(
            to=DETERMINISTIC_FACTORY_ADDRESS,
            data=salt.to_bytes(32, "big") + initcode,
            gas_limit=gas_limit,
            sender=deployer,
        )
        for salt in range(TARGET_COUNT)
    ]

    blocks = [Block(txs=chunk) for chunk in chunk_into_blocks(txs, state_each)]

    benchmark_test(
        pre=pre,
        post={},
        blocks=blocks,
        expected_benchmark_gas_used=len(txs) * gas_limit,
        expected_receipt_status=1,
    )


@pytest.mark.repricing
def test_delegate_7702_authorities(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Point TARGET_COUNT EIP-7702 authorities at EXISTING_CONTRACT_DIFF_MAX.

    Authority i delegates to DIFF_MAX target i, matching
    `yield_distinct_delegate_receiver` and
    `register_delegate_targets`. Requires
    test_deploy_create2_targets[EXISTING_CONTRACT_DIFF_MAX] to have run
    first -- a delegation designator pointing at an empty account would
    satisfy the benchmarks' code-prefix check but execute nothing.
    """
    diff_max = AccountCreator(AccountMode.EXISTING_CONTRACT_DIFF_MAX)
    delegate_target = diff_max.target_address_of()

    authorities = yield_distinct_delegate_receiver()
    deployer = pre.fund_eoa(DEPLOYER_BALANCE)

    # An authority whose account is empty pays NEW_ACCOUNT on top of
    # AUTH_BASE; both are state gas and must be funded above the cap.
    per_auth_state_gas = (
        fork.create_state_gas(code_size=0)
        if fork.state_gas_reservoir_enabled()
        else 0
    )
    intrinsic = fork.transaction_intrinsic_cost_calculator()(
        authorization_list_or_count=1
    )
    gas_limit = intrinsic + 200_000 + per_auth_state_gas

    txs = [
        Transaction(
            to=Address(0),
            gas_limit=gas_limit,
            sender=deployer,
            authorization_list=[
                AuthorizationTuple(
                    address=delegate_target(index),
                    signer=next(authorities),
                )
            ],
        )
        for index in range(TARGET_COUNT)
    ]

    blocks = [
        Block(txs=chunk) for chunk in chunk_into_blocks(txs, per_auth_state_gas)
    ]

    benchmark_test(
        pre=pre,
        post={},
        blocks=blocks,
        expected_benchmark_gas_used=len(txs) * gas_limit,
        expected_receipt_status=1,
    )


@pytest.mark.repricing
def test_fund_sender_pool(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Credit the deterministic sender pool via consensus-layer withdrawals.

    Replaces the historical `funding.txt`, whose payload is chained onto
    the tail of a 5,000-block gas-bump run and therefore cannot be
    replayed directly onto the snapshot head. jochemnet already carries a
    1 TGas block limit, so no gas ramp is needed -- only this block.

    Withdrawals credit balance without executing anything, which is why
    the senders stay uncached: they are never touched by a transaction
    until the benchmark that uses them.
    """
    recipients = [LEGACY_FILL_SEED, *itertools.islice(
        yield_distinct_sender(), FUNDED_SENDER_COUNT
    )]
    withdrawals = [
        Withdrawal(
            index=index,
            validator_index=index,
            address=recipient,
            amount=WITHDRAWAL_AMOUNT_GWEI,
        )
        for index, recipient in enumerate(recipients)
    ]

    benchmark_test(
        pre=pre,
        post={},
        blocks=[Block(txs=[], withdrawals=withdrawals)],
        expected_benchmark_gas_used=0,
    )
