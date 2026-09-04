"""Benchmark different transaction types."""

import math
import random
from dataclasses import dataclass
from typing import Generator, List, Tuple

import pytest
from execution_testing import (
    AccessList,
    Account,
    Address,
    Alloc,
    AuthorizationTuple,
    BenchmarkTestFiller,
    Block,
    Fork,
    Hash,
    Op,
    RecipientType,
    Transaction,
    compute_create_address,
)


def test_empty_block(
    benchmark_test: BenchmarkTestFiller,
) -> None:
    """Test running an empty block as a baseline for fixed proving costs."""
    benchmark_test(
        blocks=[Block(txs=[])],
        expected_benchmark_gas_used=0,
    )


@pytest.fixture
def intrinsic_cost(fork: Fork) -> int:
    """Transaction intrinsic cost."""
    intrinsic_cost = fork.transaction_intrinsic_cost_calculator()
    return intrinsic_cost()


def get_distinct_sender_list(pre: Alloc) -> Generator[Address, None, None]:
    """Get a list of distinct sender accounts."""
    while True:
        yield pre.fund_eoa()


def get_distinct_receiver_list(
    pre: Alloc,
    balance: int,
    delegation: Address | None = None,
) -> Generator[Address, None, None]:
    """Get a list of distinct receiver accounts."""
    while True:
        yield pre.fund_eoa(balance, delegation=delegation)


def get_single_sender_list(pre: Alloc) -> Generator[Address, None, None]:
    """Get a list of single sender accounts."""
    sender = pre.fund_eoa()
    while True:
        yield sender


def get_single_receiver_list(
    pre: Alloc,
    balance: int,
    delegation: Address | None = None,
) -> Generator[Address, None, None]:
    """Get a list of single receiver accounts."""
    receiver = pre.fund_eoa(balance, delegation=delegation)
    while True:
        yield receiver


@dataclass(frozen=True)
class ReceiverAccountType:
    """Receiver account type for ether transfer benchmarks."""

    balance: int
    delegated: bool


@pytest.fixture
def ether_transfer_case(
    case_id: str,
    pre: Alloc,
    receiver_account_type: ReceiverAccountType,
) -> Tuple[Generator[Address, None, None], Generator[Address, None, None]]:
    """Generate sender and receiver generators based on the test case."""
    balance = receiver_account_type.balance
    delegation = (
        pre.deploy_contract(code=Op.STOP)
        if receiver_account_type.delegated
        else None
    )

    if case_id == "a_to_a":
        """Sending to self."""
        senders = get_single_sender_list(pre)
        receivers = senders

    elif case_id == "a_to_b":
        """One sender → one receiver."""
        senders = get_single_sender_list(pre)
        receivers = get_single_receiver_list(pre, balance, delegation)

    elif case_id == "diff_acc_to_b":
        """Multiple senders → one receiver."""
        senders = get_distinct_sender_list(pre)
        receivers = get_single_receiver_list(pre, balance, delegation)

    elif case_id == "a_to_diff_acc":
        """One sender → multiple receivers."""
        senders = get_single_sender_list(pre)
        receivers = get_distinct_receiver_list(pre, balance, delegation)

    elif case_id == "diff_acc_to_diff_acc":
        """Multiple senders → multiple receivers."""
        senders = get_distinct_sender_list(pre)
        receivers = get_distinct_receiver_list(pre, balance, delegation)

    else:
        raise ValueError(f"Unknown case: {case_id}")

    return senders, receivers


@pytest.mark.parametrize(
    "case_id",
    [
        "a_to_a",
        "a_to_b",
        "diff_acc_to_b",
        "a_to_diff_acc",
        "diff_acc_to_diff_acc",
    ],
)
@pytest.mark.parametrize("transfer_amount", [0, 1])
@pytest.mark.parametrize(
    "receiver_account_type",
    [
        pytest.param(
            ReceiverAccountType(balance=0, delegated=False),
            id="empty_account",
        ),
        pytest.param(
            ReceiverAccountType(balance=1, delegated=False),
            id="non_empty_account",
        ),
        pytest.param(
            ReceiverAccountType(balance=0, delegated=True),
            id="delegated_account",
        ),
    ],
)
@pytest.mark.parametrize("warm_access", [False, True])
def test_ether_transfers(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    case_id: str,
    receiver_account_type: ReceiverAccountType,
    transfer_amount: int,
    fork: Fork,
    gas_benchmark_value: int,
    warm_access: bool,
    ether_transfer_case: Tuple[
        Generator[Address, None, None], Generator[Address, None, None]
    ],
) -> None:
    """
    Single test for ether transfer scenarios.

    Scenarios:
    - a_to_a: one sender → one sender
    - a_to_b: one sender → one receiver
    - diff_acc_to_b: multiple senders → one receiver
    - a_to_diff_acc: one sender → multiple receivers
    - diff_acc_to_diff_acc: multiple senders → multiple receivers

    When warm_access is True, each transaction includes an access list
    entry for the receiver to warm the account before the transfer.
    """
    senders, receivers = ether_transfer_case

    balance = receiver_account_type.balance
    sends_value = transfer_amount > 0
    distinct_receivers = case_id in ("a_to_diff_acc", "diff_acc_to_diff_acc")

    if case_id == "a_to_a":
        recipient_type = RecipientType.SELF
    elif receiver_account_type.delegated:
        recipient_type = RecipientType.DELEGATION_7702
    else:
        recipient_type = RecipientType.CONTRACT

    warm_list = (
        [AccessList(address=Address(0x100), storage_keys=[])]
        if warm_access
        else None
    )

    transfer_cost = fork.transaction_intrinsic_cost_calculator()(
        access_list=warm_list,
        sends_value=sends_value,
        recipient_type=recipient_type,
    ) + fork.transaction_top_frame_execution_gas(
        sends_value=sends_value,
        recipient_type=recipient_type,
    )

    creates_account = (
        sends_value
        and balance == 0
        and not receiver_account_type.delegated
        and recipient_type != RecipientType.SELF
    )

    new_account_cost = (
        fork.transaction_top_frame_state_gas(
            sends_value=True,
            recipient_type=RecipientType.EMPTY_ACCOUNT,
        )
        if creates_account
        else 0
    )

    txs = []
    token_transfers: dict[Address, int] = {}

    gas_used = 0
    tx_index = 0
    while True:
        creating = creates_account and (distinct_receivers or tx_index == 0)
        tx_cost = transfer_cost + (new_account_cost if creating else 0)
        if gas_used + tx_cost > gas_benchmark_value:
            break

        gas_used += tx_cost

        receiver = next(receivers)
        token_transfers[receiver] = (
            token_transfers.get(receiver, 0) + transfer_amount
        )

        txs.append(
            Transaction(
                to=receiver,
                value=transfer_amount,
                gas_limit=tx_cost,
                sender=next(senders),
                access_list=(
                    [AccessList(address=receiver, storage_keys=[])]
                    if warm_access
                    else None
                ),
            )
        )
        tx_index += 1

    post_state = (
        {}
        if recipient_type == RecipientType.SELF
        else {
            receiver: Account(balance=balance + transferred_amount)
            for receiver, transferred_amount in token_transfers.items()
            if balance + transferred_amount > 0
        }
    )

    benchmark_test(
        pre=pre,
        post=post_state,
        blocks=[Block(txs=txs)],
        expected_benchmark_gas_used=gas_used,
    )


@pytest.mark.with_all_precompiles
@pytest.mark.parametrize("transfer_amount", [0, 1])
def test_ether_transfers_to_precompile(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    precompile: int,
    fork: Fork,
    gas_benchmark_value: int,
    transfer_amount: int,
) -> None:
    """Test a block full of ether transfers to a precompile address."""
    # A precompile already exists, so a value transfer pays the EIP-2780
    # value-transfer charge but never the new-account state gas.
    iteration_cost = fork.transaction_intrinsic_cost_calculator()(
        sends_value=transfer_amount > 0,
        recipient_type=RecipientType.PRECOMPILE,
    )
    iteration_count = gas_benchmark_value // iteration_cost
    txs = []
    for _ in range(iteration_count):
        txs.append(
            Transaction(
                to=Address(precompile),
                value=transfer_amount,
                gas_limit=iteration_cost,
                sender=pre.fund_eoa(),
            )
        )

    benchmark_test(
        pre=pre,
        blocks=[Block(txs=txs)],
        expected_benchmark_gas_used=iteration_count * iteration_cost,
    )


@pytest.fixture
def total_cost_floor_per_token(fork: Fork) -> int:
    """Total cost floor per token (EIP-7623)."""
    return fork.gas_costs().TX_DATA_TOKEN_FLOOR


@pytest.fixture
def total_cost_standard_per_token(fork: Fork) -> int:
    """Standard cost per token (EIP-7623)."""
    return fork.gas_costs().TX_DATA_TOKEN_STANDARD


def calldata_generator(
    gas_amount: int,
    zero_byte: int,
    fork: Fork,
) -> bytes:
    """Calculate the calldata based on the gas amount and zero byte."""
    # Gas cost calculation based on EIP-7683: (https://eips.ethereum.org/EIPS/eip-7683)
    #
    #   tx.gasUsed = 21000 + max(
    #       TX_DATA_TOKEN_STANDARD * tokens_in_calldata
    #       + execution_gas_used
    #       + isContractCreation * (32000 +
    #                                 INITCODE_WORD_COST * words(calldata)),
    #       TX_DATA_TOKEN_FLOOR * tokens_in_calldata)
    #
    # Simplified in this test case:
    # - No execution gas used (no opcodes are executed)
    # - Not a contract creation (no initcode)
    #
    # Therefore:
    #   max_token_cost =
    #       max(TX_DATA_TOKEN_STANDARD, TX_DATA_TOKEN_FLOOR)
    #   tx.gasUsed = 21000 + tokens_in_calldata * max_token_cost
    #
    byte_data = b"\x00" if zero_byte else b"\xff"
    gas_per_byte = fork.calldata_gas_calculator()(data=byte_data, floor=True)
    return byte_data * (gas_amount // gas_per_byte)


@pytest.mark.parametrize("zero_byte", [True, False])
def test_block_full_data(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    zero_byte: bool,
    intrinsic_cost: int,
    gas_benchmark_value: int,
    tx_gas_limit: int,
    fork: Fork,
) -> None:
    """Test a block full of calldata, respecting RLP size limits."""
    iteration_count = math.ceil(gas_benchmark_value / tx_gas_limit)

    # check for EIP-7934 block RLP size limit and cap gas to stay under it
    block_rlp_limit = fork.block_rlp_size_limit()
    effective_gas = gas_benchmark_value

    if block_rlp_limit:
        # Max calldata bytes at 99% of limit (Osaka: 8,388,608 * 0.99 ≈ 8.3 MB)
        safe_calldata_bytes = int(block_rlp_limit * 0.99)

        gas_per_byte = fork.calldata_gas_calculator()(
            data=b"\x00" if zero_byte else b"\xff", floor=True
        )
        # For zero bytes: 8.3MB * 10 = 83M gas just for calldata
        max_calldata_gas = safe_calldata_bytes * gas_per_byte
        # Add intrinsic cost per tx (Osaka): 83M + 6 txs * 21k ≈ 83.1M total
        rlp_limited_gas = max_calldata_gas + iteration_count * intrinsic_cost

        # use the min between benchmark target and the RLP limit
        effective_gas = min(gas_benchmark_value, rlp_limited_gas)

    gas_remaining = effective_gas
    total_gas_used = 0
    txs = []
    for _ in range(iteration_count):
        if gas_remaining <= intrinsic_cost:
            break
        gas_available = min(tx_gas_limit, gas_remaining) - intrinsic_cost
        data = calldata_generator(
            gas_available,
            zero_byte,
            fork,
        )

        total_gas_used += fork.transaction_intrinsic_cost_calculator()(
            calldata=data
        )
        gas_remaining -= gas_available + intrinsic_cost

        txs.append(
            Transaction(
                to=pre.fund_eoa(),
                data=data,
                gas_limit=gas_available + intrinsic_cost,
                sender=pre.fund_eoa(),
            )
        )

    benchmark_test(
        blocks=[Block(txs=txs)],
        expected_benchmark_gas_used=total_gas_used,
    )


def test_block_full_access_list_and_data(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    intrinsic_cost: int,
    total_cost_standard_per_token: int,
    fork: Fork,
    gas_benchmark_value: int,
    tx_gas_limit: int,
) -> None:
    """
    Test a block with access lists (60% gas) and calldata (40% gas) using
    random mixed bytes.
    """
    # Skip if EIP-7934 block RLP size limit would be exceeded
    block_rlp_limit = fork.block_rlp_size_limit()
    if block_rlp_limit:
        pytest.skip(
            "Test skipped: EIP-7934 block RLP size limit might be exceeded"
        )

    iteration_count = math.ceil(gas_benchmark_value / tx_gas_limit)

    gas_remaining = gas_benchmark_value
    total_gas_used = 0

    txs = []
    for _ in range(iteration_count):
        gas_available = min(tx_gas_limit, gas_remaining) - intrinsic_cost

        # Split available gas: 60% for access lists, 40% for calldata
        gas_for_access_list = int(gas_available * 0.6)
        gas_for_calldata = int(gas_available * 0.4)

        # Access list gas costs from fork's gas_costs
        gas_costs = fork.gas_costs()
        gas_per_address = gas_costs.TX_ACCESS_LIST_ADDRESS
        gas_per_storage_key = gas_costs.TX_ACCESS_LIST_STORAGE_KEY

        # Calculate number of storage keys we can fit
        gas_after_address = gas_for_access_list - gas_per_address
        num_storage_keys = gas_after_address // gas_per_storage_key

        # Create access list with 1 address and many storage keys
        access_address = Address("0x1234567890123456789012345678901234567890")
        storage_keys = []
        for i in range(num_storage_keys):
            # Generate random-looking storage keys
            storage_keys.append(Hash(i))

        access_list = [
            AccessList(
                address=access_address,
                storage_keys=storage_keys,
            )
        ]

        # Calculate calldata with 29% of gas for zero bytes and 71% for
        # non-zero bytes
        # Token accounting: tokens_in_calldata = zero_bytes + 4 *
        # non_zero_bytes
        # We want to split the gas budget:
        # - 29% of gas_for_calldata for zero bytes
        # - 71% of gas_for_calldata for non-zero bytes

        max_tokens_in_calldata = (
            gas_for_calldata // total_cost_standard_per_token
        )

        # Calculate how many tokens to allocate to each type
        tokens_for_zero_bytes = int(max_tokens_in_calldata * 0.29)
        tokens_for_non_zero_bytes = (
            max_tokens_in_calldata - tokens_for_zero_bytes
        )

        # Convert tokens to actual byte counts
        # Zero bytes: 1 token per byte
        # Non-zero bytes: 4 tokens per byte
        num_zero_bytes = tokens_for_zero_bytes  # 1 token = 1 zero byte
        num_non_zero_bytes = (
            tokens_for_non_zero_bytes // 4
        )  # 4 tokens = 1 non-zero byte

        # Create calldata with mixed bytes
        calldata = bytearray()

        # Add zero bytes
        calldata.extend(b"\x00" * num_zero_bytes)

        # Add non-zero bytes (random values from 0x01 to 0xff)
        rng = random.Random(42)  # For reproducibility
        for _ in range(num_non_zero_bytes):
            calldata.append(rng.randint(1, 255))

        # Shuffle the bytes to mix zero and non-zero bytes
        calldata_list = list(calldata)
        rng.shuffle(calldata_list)
        shuffled_calldata = bytes(calldata_list)

        txs.append(
            Transaction(
                to=pre.fund_eoa(amount=0),
                data=shuffled_calldata,
                gas_limit=gas_available + intrinsic_cost,
                sender=pre.fund_eoa(),
                access_list=access_list,
            )
        )

        gas_remaining -= gas_for_access_list + intrinsic_cost
        total_gas_used += fork.transaction_intrinsic_cost_calculator()(
            calldata=shuffled_calldata,
            access_list=access_list,
        )

    benchmark_test(
        blocks=[Block(txs=txs)],
        expected_benchmark_gas_used=total_gas_used,
    )


@pytest.mark.parametrize("empty_authority", [True, False])
@pytest.mark.parametrize("zero_delegation", [True, False])
@pytest.mark.parametrize("empty_account", [True, False])
@pytest.mark.parametrize("transfer_amount", [True, False])
def test_auth_transaction(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    gas_benchmark_value: int,
    fork: Fork,
    empty_authority: bool,
    empty_account: bool,
    transfer_amount: int,
    zero_delegation: bool,
    tx_gas_limit: int,
) -> None:
    """Test an auth block."""
    intrinsic_cost_calc = fork.transaction_intrinsic_cost_calculator()
    top_frame_calc = fork.transaction_top_frame_execution_gas

    code = Op.INVALID * fork.max_code_size()
    auth_target = (
        Address(0) if zero_delegation else pre.deploy_contract(code=code)
    )

    sends_value = bool(transfer_amount)

    receiver_type = (
        RecipientType.EMPTY_ACCOUNT
        if empty_account
        else RecipientType.CONTRACT
    )

    auth_effects = AuthorizationTuple(
        address=auth_target,
        v=0,
        r=0,
        s=0,
        creates_account=empty_authority,
        writes_delegation=empty_authority and not zero_delegation,
        first_write=True,
    )

    def auth_tx_gas(count: int) -> int:
        """
        Return the full gas consumed by a transaction carrying `count`
        authorizations: intrinsic gas plus the state-conditional
        top-frame charges, which have no refunds per EIP-2780.
        """
        auths = [auth_effects] * count
        return (
            intrinsic_cost_calc(
                authorization_list_or_count=count,
                sends_value=sends_value,
                recipient_type=receiver_type,
            )
            + top_frame_calc(
                sends_value=sends_value,
                recipient_type=receiver_type,
                authorizations=auths,
            )
            + fork.transaction_top_frame_state_gas(
                sends_value=sends_value,
                recipient_type=receiver_type,
                authorizations=auths,
            )
        )

    remaining_gas = gas_benchmark_value
    authorizations_per_tx: List[int] = []

    min_authorization_tx_gas = auth_tx_gas(1)

    while remaining_gas >= min_authorization_tx_gas:
        tx_max_gas = min(remaining_gas, tx_gas_limit)

        low = 1
        high = 2

        # Exponential search to find upper bound
        while auth_tx_gas(high) < tx_max_gas:
            low = high
            high *= 2

        # Binary search for exact fit
        while low < high:
            mid = (low + high) // 2

            if auth_tx_gas(mid) > tx_max_gas:
                high = mid
            else:
                low = mid + 1

        best_iterations = low - 1
        authorizations_per_tx.append(best_iterations)
        remaining_gas -= auth_tx_gas(best_iterations)

    delegation_code = (
        b"" if zero_delegation else b"\xef\x01\x00" + bytes(auth_target)
    )

    expected_gas_usage = 0
    txs = []
    post = {}

    for auths_in_this_tx in authorizations_per_tx:
        auth_tuples = []
        for _ in range(auths_in_this_tx):
            signer = (
                pre.fund_eoa(amount=0, delegation=None)
                if empty_authority
                else pre.fund_eoa(amount=0, delegation=auth_target)
            )
            auth_tuple = AuthorizationTuple(
                address=auth_target,
                nonce=signer.nonce,
                signer=signer,
                creates_account=auth_effects.creates_account,
                writes_delegation=auth_effects.writes_delegation,
            )
            auth_tuples.append(auth_tuple)
            post[signer] = Account(
                nonce=signer.nonce + 1, code=delegation_code
            )

        # The gas limit is exact, so an under-estimate halts the top
        # frame (rolling back every delegation) and fails the post
        # check.
        tx_gas = auth_tx_gas(auths_in_this_tx)
        expected_gas_usage += tx_gas

        receiver = pre.fund_eoa(0 if empty_account else 1)

        txs.append(
            Transaction(
                to=receiver,
                value=transfer_amount,
                gas_limit=tx_gas,
                sender=pre.fund_eoa(),
                authorization_list=auth_tuples,
            )
        )

    benchmark_test(
        pre=pre,
        post=post,
        blocks=[Block(txs=txs)],
        expected_benchmark_gas_used=expected_gas_usage,
    )


@pytest.mark.parametrize("transfer_amount", [0, 1])
@pytest.mark.parametrize(
    "contract_size", [0, 1, pytest.param(None, id="contract_size_max")]
)
def test_contract_creation(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    transfer_amount: int,
    gas_benchmark_value: int,
    contract_size: int | None,
) -> None:
    """Benchmark contract creations via transactions."""
    if contract_size is None:
        contract_size = fork.max_code_size()

    initcode = Op.RETURN(
        Op.PUSH0,
        contract_size,
        # gas accounting
        old_memory_size=0,
        new_memory_size=contract_size,
        code_deposit_size=contract_size,
    )
    intrinsic_gas_calc = fork.transaction_intrinsic_cost_calculator()
    sends_value = transfer_amount > 0

    # EIP-7623: actual gas used = max(standard + execution, floor)
    standard_intrinsic = intrinsic_gas_calc(
        calldata=bytes(initcode),
        contract_creation=True,
        sends_value=sends_value,
        return_cost_deducted_prior_execution=True,
    )
    floor_intrinsic = intrinsic_gas_calc(
        calldata=bytes(initcode),
        contract_creation=True,
        sends_value=sends_value,
    )
    execution_gas = initcode.gas_cost(fork)
    top_frame_state_gas = fork.transaction_top_frame_state_gas(
        contract_creation=True
    )
    tx_cost = max(
        standard_intrinsic + execution_gas + top_frame_state_gas,
        floor_intrinsic,
    )

    iteration_count = gas_benchmark_value // tx_cost

    sender = pre.fund_eoa()
    txs = []
    post = {}
    for nonce in range(iteration_count):
        txs.append(
            Transaction(
                to=None,
                data=initcode,
                value=transfer_amount,
                gas_limit=tx_cost,
                sender=sender,
            )
        )
        created_address = compute_create_address(address=sender, nonce=nonce)
        post[created_address] = Account(nonce=1)

    benchmark_test(
        pre=pre,
        post=post,
        blocks=[Block(txs=txs)],
        expected_benchmark_gas_used=iteration_count * tx_cost,
    )
