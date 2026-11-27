"""Benchmark blocks rejected for a bad header or transaction."""

from dataclasses import dataclass, field
from math import ceil
from typing import Any, Callable, List

import pytest
from execution_testing import (
    Alloc,
    AuthorizationTuple,
    BenchmarkTestFiller,
    Block,
    BlockException,
    Fork,
    Hash,
    Header,
    JumpLoopGenerator,
    Op,
    RecipientType,
    Transaction,
    TransactionException,
)
from execution_testing.base_types import Bloom

from tests.benchmark.helper.account_sender_receiver import (
    yield_distinct_nonexistent_receiver,
)
from tests.benchmark.helper.constants import TRANSFER_VALUE
from tests.frontier.precompiles.spec import EcrecoverInput
from tests.frontier.precompiles.spec import Spec as EcrecoverSpec

pytestmark = [
    pytest.mark.valid_from("Amsterdam"),
    pytest.mark.exception_test,
]

BadTransaction = Callable[[Alloc, Fork, int], Transaction]

# Upper limits clients enforce on header fields.
MAXIMUM_EXTRA_DATA_SIZE = 32
MAXIMUM_GAS_LIMIT = 2**63 - 1


@dataclass(frozen=True, kw_only=True)
class ShapedBlock:
    """
    The transactions of a block and the gas they use.

    ``gas_used`` is ``None`` when the exact gas is unknown, and the
    benchmark then skips checking it.
    """

    txs: List[Transaction] = field(default_factory=list)
    gas_used: int | None = None


BlockBuilder = Callable[[Alloc, Fork, int], ShapedBlock]
InvalidHeader = Callable[[Fork, ShapedBlock], Header]

# Every block below sends all its transactions from one sender, so each
# extra transaction adds a signature to recover but no sender account.


def heavy_block(
    pre: Alloc, fork: Fork, gas_benchmark_value: int
) -> ShapedBlock:
    """
    Fill the gas target with as few transactions as the cap allows.

    Each calls ECRECOVER in a loop until it runs out of gas, so the block
    is full but has few signatures to recover.
    """
    sender = pre.fund_eoa()
    contract = JumpLoopGenerator(
        setup=Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE),
        attack_block=Op.MSTORE(
            0,
            Op.ADD(
                Op.MLOAD(0),
                Op.STATICCALL(
                    gas=Op.GAS,
                    address=EcrecoverSpec.ECRECOVER,
                    args_size=Op.CALLDATASIZE,
                    ret_offset=0x80,
                    ret_size=0x20,
                ),
            ),
        ),
    ).deploy_contracts(pre=pre, fork=fork)

    # The loop never ends, so each transaction spends its whole gas
    # limit. The target is shared evenly between as few transactions as
    # the cap allows.
    cap = fork.transaction_gas_limit_cap() or gas_benchmark_value
    gas_per_tx = gas_benchmark_value // ceil(gas_benchmark_value / cap)
    tx_count = gas_benchmark_value // gas_per_tx

    # A valid signature, so every call runs the whole recovery.
    signature = EcrecoverInput(
        msg_hash=0x38D18ACB67D25C8BB9942764B62F18E17054F66A817BD4295423ADF9ED98873E,
        v=0x1B,
        r=0x38D18ACB67D25C8BB9942764B62F18E17054F66A817BD4295423ADF9ED98873E,
        s=0x789D1DD423D25F0772D2748D60F7E4B81BB14D086EBA8E8E8EFB6DCFF8A4AE02,
    )
    txs = [
        Transaction(
            to=contract,
            data=bytes(signature),
            gas_limit=gas_per_tx,
            sender=sender,
        )
        for _ in range(tx_count)
    ]
    return ShapedBlock(txs=txs, gas_used=tx_count * gas_per_tx)


def transfer_block(
    pre: Alloc, fork: Fork, gas_benchmark_value: int
) -> ShapedBlock:
    """
    Fill the gas target with transfers to existing accounts.

    A transfer is the cheapest transaction, so this block has the most
    transactions and the most signatures to recover.
    """
    sender = pre.fund_eoa()
    gas_per_tx = fork.transaction_intrinsic_cost_calculator()(
        sends_value=True,
        recipient_type=RecipientType.EOA,
    )
    tx_count = gas_benchmark_value // gas_per_tx

    txs = [
        Transaction(
            to=pre.fund_eoa(TRANSFER_VALUE),
            value=TRANSFER_VALUE,
            gas_limit=gas_per_tx,
            sender=sender,
        )
        for _ in range(tx_count)
    ]
    return ShapedBlock(txs=txs, gas_used=tx_count * gas_per_tx)


def new_account_block(
    pre: Alloc, fork: Fork, gas_benchmark_value: int
) -> ShapedBlock:
    """
    Fill the gas target with transfers that each create an account.

    The block holds as many new accounts as its state gas allows.
    """
    sender = pre.fund_eoa()
    intrinsic = fork.transaction_intrinsic_cost_calculator()(
        sends_value=True,
        recipient_type=RecipientType.EMPTY_ACCOUNT,
    )
    state = fork.transaction_top_frame_state_gas(
        sends_value=True,
        recipient_type=RecipientType.EMPTY_ACCOUNT,
    )
    # The block counts the larger of its regular and state gas, which
    # here is the state gas of the new account.
    gas_per_tx = max(intrinsic, state)
    tx_count = gas_benchmark_value // gas_per_tx

    receivers = yield_distinct_nonexistent_receiver()
    txs = [
        Transaction(
            to=next(receivers),
            value=TRANSFER_VALUE,
            # Without gas for the new account the transfer fails.
            gas_limit=intrinsic + state,
            sender=sender,
        )
        for _ in range(tx_count)
    ]
    return ShapedBlock(txs=txs, gas_used=tx_count * gas_per_tx)


def authorization_block(
    pre: Alloc, fork: Fork, gas_benchmark_value: int
) -> ShapedBlock:
    """
    Fill the gas target with long EIP-7702 authorization lists.

    This is the most signatures per unit of gas. The exact gas a failed
    authorization spends is not known here, so ``gas_used`` is left out.
    """
    sender = pre.fund_eoa()
    gas_costs = fork.gas_costs()
    intrinsic = fork.transaction_intrinsic_cost_calculator()(
        recipient_type=RecipientType.EOA,
    )

    # As many authorizations per transaction as both limits allow: the
    # gas limit reserves AUTH_BASE for each and must stay under the cap,
    # and the gas they finally spend must fit in the gas target.
    cap = fork.transaction_gas_limit_cap() or gas_benchmark_value
    by_cap = (cap - intrinsic) // gas_costs.AUTH_BASE
    by_target = (
        gas_benchmark_value - intrinsic
    ) // gas_costs.EXECUTION_PER_AUTH_BASE_COST
    auths_per_tx = max(1, min(by_cap, by_target))

    # An estimate of what each transaction finally spends.
    gas_per_tx = (
        intrinsic + auths_per_tx * gas_costs.EXECUTION_PER_AUTH_BASE_COST
    )
    tx_count = gas_benchmark_value // gas_per_tx

    authority = pre.fund_eoa()
    delegate = pre.deploy_contract(code=Op.STOP)

    txs = []
    for _ in range(tx_count):
        # The authority's nonce is 0, so nonces from 1 make every
        # authorization fail, which leaves the block valid.
        authorization_list = [
            AuthorizationTuple(address=delegate, nonce=nonce, signer=authority)
            for nonce in range(1, auths_per_tx + 1)
        ]
        txs.append(
            Transaction(
                to=sender,
                gas_limit=intrinsic + auths_per_tx * gas_costs.AUTH_BASE,
                sender=sender,
                authorization_list=authorization_list,
            )
        )
    return ShapedBlock(txs=txs)


def benchmark_modified_header(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    block: ShapedBlock,
    header: Header,
    exception: BlockException | List[BlockException],
) -> None:
    """Benchmark ``block`` with the fields set in ``header`` overwritten."""
    header_verify: Header | None = None
    if block.gas_used is not None:
        # Confirm the block used this much before the header is changed.
        header_verify = Header(gas_used=block.gas_used)

    benchmark_test(
        pre=pre,
        post={},
        blocks=[
            Block(
                txs=block.txs,
                header_verify=header_verify,
                rlp_modifier=header,
                exception=exception,
            )
        ],
        expected_benchmark_gas_used=block.gas_used,
        skip_gas_used_validation=block.gas_used is None,
    )


@pytest.mark.parametrize(
    "invalid_header,exception",
    [
        # Early: a client can check these from the header and its parent
        # alone, without running a transaction. Fields a client rebuilds
        # from the payload itself, such as the transactions root, cannot
        # be made wrong here. A timestamp is left out: one before the
        # parent's can fall in an earlier fork.
        pytest.param(
            lambda *_: Header(
                extra_data=b"\x00" * (MAXIMUM_EXTRA_DATA_SIZE + 1)
            ),
            BlockException.EXTRA_DATA_TOO_BIG,
            id="extra_data_too_big",
        ),
        pytest.param(
            lambda *_: Header(gas_limit=MAXIMUM_GAS_LIMIT + 1),
            BlockException.GASLIMIT_TOO_BIG,
            id="gas_limit_too_big",
        ),
        pytest.param(
            lambda *_: Header(gas_used=MAXIMUM_GAS_LIMIT),
            [
                BlockException.INVALID_GAS_USED_ABOVE_LIMIT,
                BlockException.INVALID_GAS_USED,
            ],
            id="gas_used_above_limit",
        ),
        pytest.param(
            # Far from the parent's number plus one.
            lambda *_: Header(number=2**32),
            [
                BlockException.INVALID_BLOCK_NUMBER,
                BlockException.UNKNOWN_PARENT,
            ],
            id="block_number_wrong",
        ),
        pytest.param(
            # One ether per gas, far from the base fee the parent implies.
            lambda *_: Header(base_fee_per_gas=10**18),
            BlockException.INVALID_BASEFEE_PER_GAS,
            id="base_fee_wrong",
        ),
        # Neither the block nor its parent has blobs, so any nonzero
        # blob gas is wrong.
        pytest.param(
            lambda fork, _: Header(blob_gas_used=fork.blob_gas_per_blob()),
            BlockException.INCORRECT_BLOB_GAS_USED,
            id="blob_gas_used_wrong",
        ),
        pytest.param(
            lambda fork, _: Header(excess_blob_gas=fork.blob_gas_per_blob()),
            BlockException.INCORRECT_EXCESS_BLOB_GAS,
            id="excess_blob_gas_wrong",
        ),
        # Late: a client knows these only after running every
        # transaction.
        pytest.param(
            lambda *_: Header(state_root=Hash(0)),
            BlockException.INVALID_STATE_ROOT,
            id="state_root",
        ),
        pytest.param(
            lambda *_: Header(receipts_root=Hash(0)),
            BlockException.INVALID_RECEIPTS_ROOT,
            id="receipts_root",
        ),
        # Amsterdam logs every ether transfer under EIP-7708, so the
        # real bloom is not empty.
        pytest.param(
            lambda *_: Header(logs_bloom=Bloom(0)),
            BlockException.INVALID_LOG_BLOOM,
            id="logs_bloom",
        ),
        pytest.param(
            # Off by one, so only running the block reveals it.
            lambda _, block: Header(gas_used=block.gas_used - 1),
            BlockException.INVALID_GAS_USED,
            id="gas_used",
        ),
    ],
)
def test_invalid_header_field(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_benchmark_value: int,
    invalid_header: InvalidHeader,
    exception: BlockException | List[BlockException],
) -> None:
    """
    Benchmark a full block rejected for one wrong header field.

    Early fields can be checked without running the block, so a client
    that checks them first rejects it almost at once. Late fields need
    the whole block run. The gap between the two shows how much a client
    saves by checking cheap fields first.
    """
    block = transfer_block(pre, fork, gas_benchmark_value)
    benchmark_modified_header(
        benchmark_test,
        pre,
        block,
        invalid_header(fork, block),
        exception,
    )


@pytest.mark.parametrize(
    "invalid_header,exception",
    [
        pytest.param(
            lambda *_: Header(
                extra_data=b"\x00" * (MAXIMUM_EXTRA_DATA_SIZE + 1)
            ),
            BlockException.EXTRA_DATA_TOO_BIG,
            id="extra_data_too_big",
        ),
        pytest.param(
            lambda *_: Header(state_root=Hash(0)),
            BlockException.INVALID_STATE_ROOT,
            id="state_root",
        ),
    ],
)
@pytest.mark.parametrize(
    "build_block",
    [
        pytest.param(heavy_block, id="heavy"),
        pytest.param(transfer_block, id="transfers"),
        pytest.param(new_account_block, id="new_accounts"),
        pytest.param(authorization_block, id="authorizations"),
    ],
)
def test_invalid_header_by_block_shape(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_benchmark_value: int,
    build_block: BlockBuilder,
    invalid_header: InvalidHeader,
    exception: BlockException | List[BlockException],
) -> None:
    """
    Benchmark one early and one late defect on blocks of different shape.

    Some clients recover every transaction's sender before checking the
    header: geth does it in ``payloadToBlock``, and besu and nethermind
    do the same elsewhere. Such a client's time on the early defect
    grows with the number of signatures, not with the gas.

    On the late defect, ``new_accounts`` leaves the client as many new
    accounts to add to the state as a block can hold, where
    ``transfers`` at the same gas leaves none.
    """
    block = build_block(pre, fork, gas_benchmark_value)
    benchmark_modified_header(
        benchmark_test,
        pre,
        block,
        invalid_header(fork, block),
        exception,
    )


def transfer(pre: Alloc, gas_limit: int, **overrides: Any) -> Transaction:
    """
    Return a one-wei transfer from a new sender, with ``overrides`` set.

    Each bad transaction has its own sender, so it leaves the other
    transactions of the block unchanged.
    """
    if "sender" not in overrides:
        overrides["sender"] = pre.fund_eoa()
    overrides.setdefault("value", TRANSFER_VALUE)
    return Transaction(
        to=pre.fund_eoa(TRANSFER_VALUE),
        gas_limit=gas_limit,
        **overrides,
    )


@pytest.mark.parametrize(
    "bad_transaction,error",
    # Ordered from checks that need the sender's account to checks on
    # the transaction alone.
    [
        pytest.param(
            # The sender's balance covers neither the gas nor the value,
            # which is more ether than exists.
            lambda pre, _, gas: transfer(
                pre, gas, sender=pre.fund_eoa(amount=gas), value=2**127
            ),
            TransactionException.INSUFFICIENT_ACCOUNT_FUNDS,
            id="insufficient_funds",
        ),
        pytest.param(
            lambda pre, _, gas: transfer(pre, gas, nonce=1),
            TransactionException.NONCE_MISMATCH_TOO_HIGH,
            id="nonce_too_high",
        ),
        pytest.param(
            lambda pre, _, gas: transfer(pre, gas - 1),
            TransactionException.INTRINSIC_GAS_TOO_LOW,
            id="intrinsic_gas_too_low",
        ),
        pytest.param(
            # Exceeds the cap on the declared gas limit. The EIP-7825
            # cap now bounds only execution gas, so the gas limit alone
            # cannot break it.
            lambda pre, fork, _: transfer(
                pre, fork.transaction_total_gas_limit_cap() + 1
            ),
            TransactionException.GAS_LIMIT_EXCEEDS_MAXIMUM,
            id="gas_limit_over_total_cap",
        ),
        pytest.param(
            lambda pre, _, gas: transfer(pre, gas, max_fee_per_gas=0),
            TransactionException.INSUFFICIENT_MAX_FEE_PER_GAS,
            id="max_fee_below_base_fee",
        ),
        pytest.param(
            lambda pre, _, gas: transfer(pre, gas, chain_id=2),
            TransactionException.INVALID_CHAINID,
            id="wrong_chain_id",
        ),
        pytest.param(
            # r = s = 0 is never a valid signature.
            lambda pre, _, gas: transfer(pre, gas, v=0, r=0, s=0),
            TransactionException.INVALID_SIGNATURE_VRS,
            id="invalid_signature",
        ),
    ],
)
@pytest.mark.parametrize(
    "position",
    # "last" appends the bad transaction, so the others keep their
    # places. "first" and "middle" leave valid transactions after it,
    # which the framework requires marking.
    [
        pytest.param("first", marks=pytest.mark.invalid_tx_not_last),
        pytest.param("middle", marks=pytest.mark.invalid_tx_not_last),
        pytest.param("last"),
    ],
)
def test_invalid_transaction_at(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_benchmark_value: int,
    bad_transaction: BadTransaction,
    error: TransactionException,
    position: str,
) -> None:
    """
    Benchmark a full block with one invalid transaction in it.

    A client that checks every transaction before running any takes the
    same time wherever the bad one is. A client that finds it while
    running pays for every transaction before it.
    """
    txs = transfer_block(pre, fork, gas_benchmark_value).txs

    if position == "first":
        index = 0
    elif position == "middle":
        index = len(txs) // 2
    else:
        index = len(txs)

    transfer_gas = fork.transaction_intrinsic_cost_calculator()(
        sends_value=True,
        recipient_type=RecipientType.EOA,
    )
    bad_tx = bad_transaction(pre, fork, transfer_gas).with_error(error)
    txs.insert(index, bad_tx)

    benchmark_test(
        pre=pre,
        post={},
        blocks=[Block(txs=txs, exception=error)],
        # The block is rejected, so there is no gas used to check.
        skip_gas_used_validation=True,
    )
