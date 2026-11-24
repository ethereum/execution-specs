"""
Benchmark [EIP-8141](https://eips.ethereum.org/EIPS/eip-8141) frame
transactions.

A transaction occupies the larger of its two EIP-8037 gas dimensions,
`block_gas_used`, while its payer is charged their sum,
`payer_gas_used`. Senders are contracts approving from their own code,
so no transaction carries a signature entry of its own.
"""

import math
from itertools import count
from typing import Any, List

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    BenchmarkTestFiller,
    Block,
    Bytecode,
    Bytes,
    Environment,
    Fork,
    FrameSignature,
    Op,
)

from tests.amsterdam.eip7708_eth_transfer_logs.spec import transfer_log
from tests.bogota.eip8141_frame_transactions.helpers import (
    APPROVE_ALL,
    FrameCase,
    FrameTransaction,
    default_frame,
    expiry_frame,
    expiry_verifier_gas,
    sender_frame,
    verify_frame,
)
from tests.bogota.eip8141_frame_transactions.signature_helpers import (
    DIGEST,
    P256_SIGNATURE,
    canonical_entry,
    valid_p256_entry,
)
from tests.bogota.eip8141_frame_transactions.spec import Spec, ref_spec_8141

REFERENCE_SPEC_GIT_PATH = ref_spec_8141.git_path
REFERENCE_SPEC_VERSION = ref_spec_8141.version

pytestmark = pytest.mark.valid_from("Bogota")


@pytest.mark.parametrize("distinct_senders", [True, False])
@pytest.mark.parametrize("distinct_targets", [True, False])
@pytest.mark.parametrize(
    "frame_count",
    [2, 8, 32, pytest.param(Spec.MAX_FRAMES, id="frame_count_max")],
)
def test_frame_count(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_benchmark_value: int,
    frame_count: int,
    distinct_targets: bool,
    distinct_senders: bool,
) -> None:
    """Fill a block with transactions carrying `frame_count` frames."""
    shared_sender = pre.deploy_contract(code=APPROVE_ALL, balance=10**24)
    shared_nonces = count(1)
    shared_target = pre.deploy_contract(code=Op.STOP)

    def transaction() -> FrameTransaction:
        frames: List[FrameCase] = [
            verify_frame(
                code=APPROVE_ALL,
                gas_limit_delta=0,
                state_gas_limit_delta=0,
            )
        ]
        while len(frames) < frame_count:
            frames.append(
                sender_frame(
                    target=(
                        pre.deploy_contract(code=Op.STOP)
                        if distinct_targets
                        else shared_target
                    ),
                    code=Op.STOP,
                    warm=not distinct_targets and len(frames) > 1,
                    gas_limit_delta=0,
                    state_gas_limit_delta=0,
                )
            )
        sender = (
            pre.deploy_contract(code=APPROVE_ALL, balance=10**24)
            if distinct_senders
            else shared_sender
        )
        return FrameTransaction.build(
            fork=fork,
            sender=sender,
            nonce=1 if distinct_senders else next(shared_nonces),
            settle=False,
            frames=frames,
        )

    first = transaction()
    iteration_count = gas_benchmark_value // first.block_gas_used()
    txs = [first] + [transaction() for _ in range(iteration_count - 1)]

    benchmark_test(
        pre=pre,
        blocks=[Block(txs=txs)],
        expected_benchmark_gas_used=sum(tx.payer_gas_used() for tx in txs),
    )


@pytest.mark.repricing
@pytest.mark.parametrize(
    "scheme",
    [
        pytest.param(Spec.SCHEME_SECP256K1, id="secp256k1"),
        pytest.param(Spec.SCHEME_P256, id="p256"),
        pytest.param(Spec.SCHEME_ARBITRARY, id="arbitrary"),
    ],
)
def test_signature_entries(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_benchmark_value: int,
    tx_gas_limit: int,
    scheme: int,
) -> None:
    """Fill a block with `scheme` signature entries over a fixed digest."""
    sender = pre.deploy_contract(code=APPROVE_ALL, balance=10**24)
    nonces = count(1)
    target = pre.deploy_contract(code=Op.STOP)

    def entry() -> FrameSignature:
        if scheme == Spec.SCHEME_SECP256K1:
            return canonical_entry(pre.fund_eoa(amount=0), msg=Bytes(DIGEST))
        if scheme == Spec.SCHEME_P256:
            # P256 signing is randomized, so reuse the suite's signature.
            return valid_p256_entry()
        if scheme == Spec.SCHEME_ARBITRARY:
            # The unverified control, sized like a P256 signature.
            return FrameSignature(
                scheme=Spec.SCHEME_ARBITRARY,
                msg=Bytes(DIGEST),
                signature=Bytes(b"\xff" * len(P256_SIGNATURE)),
            )
        raise ValueError(f"unknown signature scheme: {scheme}")

    def transaction(entry_count: int, **overrides: Any) -> FrameTransaction:
        return FrameTransaction.build(
            fork=fork,
            sender=sender,
            settle=False,
            frames=[
                verify_frame(
                    code=APPROVE_ALL,
                    gas_limit_delta=0,
                    state_gas_limit_delta=0,
                ),
                sender_frame(
                    target=target,
                    code=Op.STOP,
                    gas_limit_delta=0,
                    state_gas_limit_delta=0,
                ),
            ],
            signatures=[entry() for _ in range(entry_count)],
            **overrides,
        )

    payload_gas = gas_benchmark_value // math.ceil(
        gas_benchmark_value / min(tx_gas_limit, gas_benchmark_value)
    )
    # The floor makes gas piecewise affine in the count, so iterate
    # until the estimate lands on the piece holding the target.
    entry_count = 0
    for _ in range(4):
        base = transaction(entry_count, nonce=0).block_gas_used()
        entry_gas = (
            transaction(entry_count + 1, nonce=0).block_gas_used() - base
        )
        entry_count += (payload_gas - base) // entry_gas
    assert transaction(entry_count, nonce=0).block_gas_used() <= payload_gas, (
        "the entry count did not settle on the gas the entries are "
        "meant to occupy"
    )

    first = transaction(entry_count, nonce=next(nonces))
    iteration_count = gas_benchmark_value // first.block_gas_used()
    txs = [first] + [
        transaction(entry_count, nonce=next(nonces))
        for _ in range(iteration_count - 1)
    ]

    benchmark_test(
        pre=pre,
        blocks=[Block(txs=txs)],
        expected_benchmark_gas_used=sum(tx.payer_gas_used() for tx in txs),
    )


@pytest.mark.repricing
@pytest.mark.parametrize("zero_byte", [True, False])
def test_block_full_frame_data(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_benchmark_value: int,
    tx_gas_limit: int,
    zero_byte: bool,
) -> None:
    """
    Fill a block with frame data that no frame reads.

    The floor prices every byte alike, so the cases differ only in how
    well the block body compresses.
    """
    sender = pre.deploy_contract(code=APPROVE_ALL, balance=10**24)
    nonces = count(1)
    target = pre.deploy_contract(code=Op.STOP)
    byte = b"\x00" if zero_byte else b"\xff"

    def transaction(data_length: int, **overrides: Any) -> FrameTransaction:
        return FrameTransaction.build(
            fork=fork,
            sender=sender,
            settle=False,
            frames=[
                verify_frame(
                    code=APPROVE_ALL,
                    gas_limit_delta=0,
                    state_gas_limit_delta=0,
                ),
                default_frame(
                    target=target,
                    code=Op.STOP,
                    data=byte * data_length,
                    gas_limit_delta=0,
                    state_gas_limit_delta=0,
                ),
            ],
            **overrides,
        )

    payload_gas = gas_benchmark_value // math.ceil(
        gas_benchmark_value / min(tx_gas_limit, gas_benchmark_value)
    )
    # The floor makes gas piecewise affine in the length, so iterate
    # until the estimate lands on the piece holding the target.
    data_length = 0
    for _ in range(4):
        base = transaction(data_length, nonce=0).block_gas_used()
        byte_gas = (
            transaction(data_length + 1, nonce=0).block_gas_used() - base
        )
        data_length += (payload_gas - base) // byte_gas
    assert transaction(data_length, nonce=0).block_gas_used() <= payload_gas, (
        "the data length did not settle on the gas the payload is meant "
        "to occupy"
    )

    first = transaction(data_length, nonce=next(nonces))
    iteration_count = gas_benchmark_value // first.block_gas_used()
    txs = [first] + [
        transaction(data_length, nonce=next(nonces))
        for _ in range(iteration_count - 1)
    ]

    block_rlp_limit = fork.block_rlp_size_limit()
    if block_rlp_limit is not None:
        assert iteration_count * data_length < block_rlp_limit, (
            "the block's frame data outgrew the EIP-7934 block RLP size "
            "limit: the floor no longer prices data above the limit's "
            "share of the benchmark gas"
        )

    benchmark_test(
        pre=pre,
        blocks=[Block(txs=txs)],
        expected_benchmark_gas_used=sum(tx.payer_gas_used() for tx in txs),
    )


@pytest.mark.parametrize("new_recipients", [True, False])
@pytest.mark.parametrize(
    "transfers_per_transaction",
    [1, 8, pytest.param(Spec.MAX_FRAMES - 1, id="transfers_max")],
)
def test_value_transfer_frames(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_benchmark_value: int,
    new_recipients: bool,
    transfers_per_transaction: int,
) -> None:
    """Fill a block with `SENDER` frames transferring value."""
    sender = pre.deploy_contract(code=APPROVE_ALL, balance=10**24)
    nonces = count(1)
    transfer_value = 10**9
    account_creation = fork.gas_costs().NEW_ACCOUNT if new_recipients else 0

    def transaction(transfers: int, **overrides: Any) -> FrameTransaction:
        frames: List[FrameCase] = [
            verify_frame(
                code=APPROVE_ALL,
                logs=[],
                gas_limit_delta=0,
                state_gas_limit_delta=0,
            )
        ]
        for _ in range(transfers):
            recipient = pre.fund_eoa(amount=0 if new_recipients else 1)
            frames.append(
                sender_frame(
                    target=recipient,
                    value=transfer_value,
                    logs=[transfer_log(sender, recipient, transfer_value)],
                    gas_limit_delta=0,
                    state_gas_limit=account_creation,
                    state_gas_used=account_creation,
                )
            )
        return FrameTransaction.build(
            fork=fork,
            sender=sender,
            settle=False,
            frames=frames,
            **overrides,
        )

    first = transaction(transfers_per_transaction, nonce=next(nonces))
    iteration_count = gas_benchmark_value // first.block_gas_used()
    if iteration_count < 1:
        pytest.skip("a frame transaction exceeds the benchmark gas value")
    txs = [first] + [
        transaction(transfers_per_transaction, nonce=next(nonces))
        for _ in range(iteration_count - 1)
    ]
    # Fill the leftover gas with one shorter transaction of this shape.
    leftover = gas_benchmark_value - sum(tx.block_gas_used() for tx in txs)
    tail_transfers = 1
    for _ in range(4):
        base = transaction(tail_transfers, nonce=0).block_gas_used()
        transfer_gas = (
            transaction(tail_transfers + 1, nonce=0).block_gas_used() - base
        )
        if transfer_gas == 0:
            # The state dimension binds, so extra frames cost no block gas.
            tail_transfers = transfers_per_transaction
            break
        tail_transfers = max(
            1,
            min(
                transfers_per_transaction,
                tail_transfers + (leftover - base) // transfer_gas,
            ),
        )
    if transaction(tail_transfers, nonce=0).block_gas_used() <= leftover:
        txs.append(transaction(tail_transfers, nonce=next(nonces)))

    post = {
        Address(frame.target): Account(
            balance=transfer_value + (0 if new_recipients else 1)
        )
        for tx in txs
        for frame in (tx.frames or [])
        if frame.target is not None and frame.value > 0
    }

    benchmark_test(
        pre=pre,
        post=post,
        blocks=[Block(txs=txs)],
        expected_benchmark_gas_used=sum(tx.payer_gas_used() for tx in txs),
    )


def test_sponsored_frame_transactions(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_benchmark_value: int,
) -> None:
    """Fill a block with sponsored frame transactions."""
    sender = pre.deploy_contract(
        code=Op.APPROVE(0, 0, Spec.APPROVE_EXECUTION), balance=10**24
    )
    payer = pre.deploy_contract(
        code=Op.APPROVE(0, 0, Spec.APPROVE_PAYMENT), balance=10**24
    )
    nonces = count(1)
    target = pre.deploy_contract(code=Op.STOP)

    def transaction() -> FrameTransaction:
        return FrameTransaction.build(
            fork=fork,
            sender=sender,
            payer=payer,
            nonce=next(nonces),
            settle=False,
            frames=[
                verify_frame(
                    flags=Spec.APPROVE_EXECUTION,
                    code=Op.APPROVE(0, 0, Spec.APPROVE_EXECUTION),
                    gas_limit_delta=0,
                    state_gas_limit_delta=0,
                ),
                verify_frame(
                    flags=Spec.APPROVE_PAYMENT,
                    target=payer,
                    code=Op.APPROVE(0, 0, Spec.APPROVE_PAYMENT),
                    gas_limit_delta=0,
                    state_gas_limit_delta=0,
                ),
                sender_frame(
                    target=target,
                    code=Op.STOP,
                    gas_limit_delta=0,
                    state_gas_limit_delta=0,
                ),
            ],
        )

    first = transaction()
    iteration_count = gas_benchmark_value // first.block_gas_used()
    txs = [first] + [transaction() for _ in range(iteration_count - 1)]

    benchmark_test(
        pre=pre,
        blocks=[Block(txs=txs)],
        expected_benchmark_gas_used=sum(tx.payer_gas_used() for tx in txs),
    )


def test_expiry_verifier_frames(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_benchmark_value: int,
) -> None:
    """Fill a block with expiry verifier frames, one per transaction."""
    sender = pre.deploy_contract(code=APPROVE_ALL, balance=10**24)
    nonces = count(1)
    target = pre.deploy_contract(code=Op.STOP)

    def transaction() -> FrameTransaction:
        return FrameTransaction.build(
            fork=fork,
            sender=sender,
            nonce=next(nonces),
            settle=False,
            frames=[
                verify_frame(
                    code=APPROVE_ALL,
                    gas_limit_delta=0,
                    state_gas_limit_delta=0,
                ),
                # The verifier's state budget must stay zero.
                expiry_frame(
                    execution_gas=expiry_verifier_gas(fork),
                    gas_limit_delta=0,
                ),
                sender_frame(
                    target=target,
                    code=Op.STOP,
                    gas_limit_delta=0,
                    state_gas_limit_delta=0,
                ),
            ],
        )

    first = transaction()
    iteration_count = gas_benchmark_value // first.block_gas_used()
    txs = [first] + [transaction() for _ in range(iteration_count - 1)]

    benchmark_test(
        pre=pre,
        blocks=[Block(txs=txs)],
        expected_benchmark_gas_used=sum(tx.payer_gas_used() for tx in txs),
    )


@pytest.mark.repricing
def test_gas_cost_transaction_intrinsic(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_benchmark_value: int,
) -> None:
    """Fill a block with the cheapest frame transaction there is."""
    sender = pre.deploy_contract(code=APPROVE_ALL, balance=10**24)

    def transaction(nonce: int) -> FrameTransaction:
        return FrameTransaction.build(
            fork=fork,
            sender=sender,
            nonce=nonce,
            settle=False,
            frames=[
                verify_frame(
                    code=APPROVE_ALL,
                    gas_limit_delta=0,
                    state_gas_limit_delta=0,
                )
            ],
        )

    first = transaction(1)
    iteration_count = gas_benchmark_value // first.block_gas_used()
    txs = [transaction(1 + index) for index in range(iteration_count)]

    benchmark_test(
        pre=pre,
        blocks=[Block(txs=txs)],
        expected_benchmark_gas_used=sum(tx.payer_gas_used() for tx in txs),
    )


@pytest.mark.repricing
def test_gas_cost_per_frame(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_benchmark_value: int,
) -> None:
    """Fill a block with the cheapest frames a transaction can carry."""
    sender = pre.deploy_contract(code=APPROVE_ALL, balance=10**24)
    nonces = count(1)

    def transaction() -> FrameTransaction:
        return FrameTransaction.build(
            fork=fork,
            sender=sender,
            nonce=next(nonces),
            settle=False,
            frames=[
                verify_frame(
                    code=APPROVE_ALL,
                    gas_limit_delta=0,
                    state_gas_limit_delta=0,
                )
            ]
            + [
                # The coinbase is warm and codeless; an empty target would
                # resolve to the sender and rerun its approval.
                sender_frame(
                    target=Environment().fee_recipient,
                    code=Bytecode(),
                    warm=True,
                    gas_limit_delta=0,
                    state_gas_limit_delta=0,
                )
                for _ in range(Spec.MAX_FRAMES - 1)
            ],
        )

    first = transaction()
    iteration_count = gas_benchmark_value // first.block_gas_used()
    txs = [first] + [transaction() for _ in range(iteration_count - 1)]

    benchmark_test(
        pre=pre,
        blocks=[Block(txs=txs)],
        expected_benchmark_gas_used=sum(tx.payer_gas_used() for tx in txs),
    )


@pytest.mark.repricing
@pytest.mark.parametrize("delegated", [True, False])
def test_gas_cost_frame_entry(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_benchmark_value: int,
    delegated: bool,
) -> None:
    """Fill a block with frames entering accounts cold to each transaction."""
    sender = pre.deploy_contract(code=APPROVE_ALL, balance=10**24)
    nonces = count(1)
    delegate = pre.deploy_contract(code=Op.STOP)
    targets = [
        pre.fund_eoa(amount=0, delegation=delegate)
        if delegated
        else pre.deploy_contract(code=Op.STOP)
        for _ in range(Spec.MAX_FRAMES - 1)
    ]

    def transaction() -> FrameTransaction:
        return FrameTransaction.build(
            fork=fork,
            sender=sender,
            nonce=next(nonces),
            settle=False,
            frames=[
                verify_frame(
                    code=APPROVE_ALL,
                    gas_limit_delta=0,
                    state_gas_limit_delta=0,
                )
            ]
            + [
                sender_frame(
                    target=target,
                    code=Op.STOP,
                    delegated=delegated,
                    delegation_warm=delegated and index > 0,
                    gas_limit_delta=0,
                    state_gas_limit_delta=0,
                )
                for index, target in enumerate(targets)
            ],
        )

    first = transaction()
    iteration_count = gas_benchmark_value // first.block_gas_used()
    txs = [first] + [transaction() for _ in range(iteration_count - 1)]

    benchmark_test(
        pre=pre,
        blocks=[Block(txs=txs)],
        expected_benchmark_gas_used=sum(tx.payer_gas_used() for tx in txs),
    )


@pytest.mark.repricing
def test_gas_cost_value_transfer(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_benchmark_value: int,
) -> None:
    """Fill a block with frames paying accounts that already exist."""
    sender = pre.deploy_contract(code=APPROVE_ALL, balance=10**24)
    nonces = count(1)
    recipients = [pre.fund_eoa(amount=1) for _ in range(Spec.MAX_FRAMES - 1)]

    def transaction() -> FrameTransaction:
        return FrameTransaction.build(
            fork=fork,
            sender=sender,
            nonce=next(nonces),
            settle=False,
            frames=[
                verify_frame(
                    code=APPROVE_ALL,
                    logs=[],
                    gas_limit_delta=0,
                    state_gas_limit_delta=0,
                )
            ]
            + [
                sender_frame(
                    target=recipient,
                    value=1,
                    logs=[transfer_log(sender, recipient, 1)],
                    gas_limit_delta=0,
                    state_gas_limit_delta=0,
                )
                for recipient in recipients
            ],
        )

    first = transaction()
    iteration_count = gas_benchmark_value // first.block_gas_used()
    txs = [first] + [transaction() for _ in range(iteration_count - 1)]

    benchmark_test(
        pre=pre,
        blocks=[Block(txs=txs)],
        expected_benchmark_gas_used=sum(tx.payer_gas_used() for tx in txs),
    )
