"""
Execution of dependency verification frames (EIP-8288): their receipts,
the intrinsic recursive STARK share of their claims, their visibility
to later frames, and an account that approves on a declared claim.
"""

from typing import List

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytecode,
    Conditional,
    Fork,
    Frame,
    FrameReceipt,
    Header,
    Op,
    StateTestFiller,
    Storage,
    Transaction,
    TransactionException,
    TransactionReceipt,
)

from tests.bogota.eip7906_transaction_assertions.helpers import (
    body_frame,
    post_tx_frame,
)
from tests.bogota.eip8141_frame_transactions.helpers import (
    default_code_frame_gas,
    default_frame,
    floor_binding_padding,
    sender_frame,
    verify_frame,
)
from tests.bogota.eip8141_frame_transactions.spec import Spec as Spec8141

from .helpers import (
    Dependency,
    claim,
    dependency_frame,
    dependency_receipt,
    expected_recursive_stark,
    verification_gas,
)
from .spec import Spec, ref_spec_8288

REFERENCE_SPEC_GIT_PATH = ref_spec_8288.git_path
REFERENCE_SPEC_VERSION = ref_spec_8288.version

pytestmark = pytest.mark.valid_from("EIP8288")

PROBE_FRAME_GAS = 500_000
"""Execution gas budget of the probe frame, ample for its reads."""


def intrinsic_without_recursive_stark_share(
    fork: Fork, tx: Transaction
) -> int:
    """
    Return the intrinsic cost of `tx` with its dependency frames priced
    as ordinary frames carrying the same data.
    """
    assert tx.frames is not None and tx.signatures is not None
    return fork.frame_transaction_intrinsic_cost_calculator()(
        frames=[
            frame.copy(mode=Spec8141.MODE_DEFAULT)
            if frame.mode == Spec.MODE_DEP_VERIFY
            else frame
            for frame in tx.frames
        ],
        signatures=tx.signatures,
        return_cost_deducted_prior_execution=True,
    )


@pytest.mark.parametrize(
    "frame_claims",
    [
        pytest.param([[claim(1)]], id="one_claim"),
        pytest.param([[claim(1), claim(1)]], id="duplicate_in_frame"),
        pytest.param([[claim(1)], [claim(1)]], id="duplicate_across_frames"),
        pytest.param(
            [
                [
                    claim(index)
                    for index in range(Spec.MAX_DEPENDENCIES_PER_FRAME)
                ]
            ],
            id="max_claims",
        ),
    ],
)
def test_dependency_frame_gas(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    frame_claims: List[List[Dependency]],
) -> None:
    """
    Charge each dependency frame its whole verification budget, and the
    transaction `LEANSTARK_VERIFICATION_GAS` of intrinsic gas for every
    claim declared, duplicates included.
    """
    sender = pre.fund_eoa()
    tx = Transaction(
        sender=sender,
        frames=[
            *[dependency_frame(fork, claims) for claims in frame_claims],
            verify_frame(),
        ],
    )
    tx.sign()
    assert tx.frames is not None and tx.signatures is not None

    declared = sum(len(claims) for claims in frame_claims)
    receipts = [
        *[dependency_receipt(fork, len(claims)) for claims in frame_claims],
        FrameReceipt(
            status=Spec8141.STATUS_SUCCESS,
            gas_used=default_code_frame_gas(fork, target_warm=True),
            state_gas_used=0,
        ),
    ]
    gas_used = (
        intrinsic_without_recursive_stark_share(fork, tx)
        + declared * fork.gas_costs().LEANSTARK_VERIFICATION
        + sum(int(receipt.gas_used or 0) for receipt in receipts)
    )
    # The premise: the calldata floor does not bind.
    assert gas_used > fork.frame_transaction_data_floor_cost_calculator()(
        frames=tx.frames, signatures=tx.signatures
    )

    tx.expected_receipt = TransactionReceipt(
        payer=sender, cumulative_gas_used=gas_used, frame_receipts=receipts
    )
    state_test(pre=pre, tx=tx, post={sender: Account(nonce=1)})


@pytest.mark.parametrize(
    "floor_binds", [True, False], ids=["floor", "below_floor"]
)
def test_recursive_stark_share_outside_calldata_floor(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    floor_binds: bool,
) -> None:
    """
    Leave the recursive STARK share out of the calldata floor, so a
    floor-bound transaction pays the floor alone.
    """
    sender = pre.fund_eoa()
    noop = pre.deploy_contract(code=Op.STOP)
    padding_gas = fork.frame_entry_gas_calculator()(target_warm=False)
    receipts = [
        dependency_receipt(fork, 1),
        FrameReceipt(
            status=Spec8141.STATUS_SUCCESS,
            gas_used=default_code_frame_gas(fork, target_warm=True),
        ),
        FrameReceipt(status=Spec8141.STATUS_SUCCESS, gas_used=padding_gas),
    ]

    def build(data_length: int) -> Transaction:
        tx = Transaction(
            sender=sender,
            nonce=0,
            frames=[
                dependency_frame(fork, [claim(1)]),
                verify_frame(),
                default_frame(
                    target=noop,
                    gas_limit=padding_gas,
                    state_gas_limit=0,
                    data=bytes(data_length),
                ),
            ],
        )
        tx.sign()
        return tx

    def spent_and_floor(tx: Transaction) -> tuple[int, int]:
        assert tx.frames is not None and tx.signatures is not None
        spent = (
            intrinsic_without_recursive_stark_share(fork, tx)
            + fork.gas_costs().LEANSTARK_VERIFICATION
            + sum(int(receipt.gas_used or 0) for receipt in receipts)
        )
        floor = fork.frame_transaction_data_floor_cost_calculator()(
            frames=tx.frames, signatures=tx.signatures
        )
        return spent, floor

    def binds(data_length: int) -> bool:
        spent, floor = spent_and_floor(build(data_length))
        return floor > spent

    data_length = floor_binding_padding(binds)
    if not floor_binds:
        data_length -= 1
    tx = build(data_length)
    spent, floor = spent_and_floor(tx)

    tx.expected_receipt = TransactionReceipt(
        payer=sender,
        cumulative_gas_used=max(spent, floor),
        frame_receipts=receipts,
    )
    state_test(pre=pre, tx=tx, post={sender: Account(nonce=1)})


def test_dependency_frame_introspection(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Expose a dependency frame to later frames through `FRAMEPARAM` and
    `FRAMEDATALOAD`: its mode, its claims, the sender as its resolved
    target, and a receipt of success with its whole budget used.
    """
    sender = pre.fund_eoa()
    claims = [claim(1, key=7), claim(2, key=8)]
    storage = Storage()
    probe_code = Bytecode()
    expected_params = [
        (Spec8141.FRAMEPARAM_RESOLVED_TARGET, int.from_bytes(sender, "big")),
        (Spec8141.FRAMEPARAM_EXECUTION_GAS_LIMIT, verification_gas(fork, 2)),
        (Spec8141.FRAMEPARAM_MODE, Spec.MODE_DEP_VERIFY),
        (Spec8141.FRAMEPARAM_FLAGS, 0),
        (Spec8141.FRAMEPARAM_DATA_LENGTH, 2 * Spec.DEPENDENCY_LENGTH),
        (Spec8141.FRAMEPARAM_STATUS, Spec8141.STATUS_SUCCESS),
        (Spec8141.FRAMEPARAM_ATOMIC_BATCH, 0),
        (Spec8141.FRAMEPARAM_VALUE, 0),
        (Spec8141.FRAMEPARAM_STATE_GAS_LIMIT, 0),
        (Spec8141.FRAMEPARAM_EXECUTION_GAS_USED, verification_gas(fork, 2)),
        (Spec8141.FRAMEPARAM_STATE_GAS_USED, 0),
    ]
    expected_words = [
        word
        for scheme, data_hash, key in claims
        for word in (
            scheme,
            int.from_bytes(data_hash, "big"),
            int.from_bytes(key, "big"),
        )
    ]
    for param, expected in expected_params:
        probe_code += Op.SSTORE(
            storage.store_next(expected), Op.FRAMEPARAM(0, param)
        )
    for index, expected_word in enumerate(expected_words):
        probe_code += Op.SSTORE(
            storage.store_next(expected_word),
            Op.FRAMEDATALOAD(index * 32, 0),
        )
    probe_code += Op.STOP
    probe = pre.deploy_contract(code=probe_code)

    nonzero_slots = sum(
        1
        for value in [expected for _, expected in expected_params]
        + expected_words
        if value != 0
    )
    slot_creation = Op.SSTORE.with_metadata(
        original_value=0, new_value=1
    ).state_cost(fork)
    tx = Transaction(
        sender=sender,
        frames=[
            dependency_frame(fork, claims),
            verify_frame(),
            default_frame(
                target=probe,
                gas_limit=PROBE_FRAME_GAS,
                state_gas_limit=nonzero_slots * slot_creation,
            ),
        ],
    )
    state_test(pre=pre, tx=tx, post={probe: Account(storage=storage)})


ACCOUNT_KEY = 3
"""The test key whose public key the smart account stores."""


def claim_checking_account_code() -> Bytecode:
    """
    Return the code of an account that approves only when frame 0 is a
    dependency frame whose first claim matches its stored key and message.
    """
    return Conditional(
        condition=Op.AND(
            Op.EQ(
                Op.FRAMEPARAM(0, Spec8141.FRAMEPARAM_MODE),
                Spec.MODE_DEP_VERIFY,
            ),
            Op.AND(
                Op.EQ(Op.FRAMEDATALOAD(64, 0), Op.SLOAD(0)),
                Op.EQ(Op.FRAMEDATALOAD(32, 0), Op.SLOAD(1)),
            ),
        ),
        if_true=Op.APPROVE(0, 0, Spec8141.APPROVE_EXECUTION_AND_PAYMENT),
        if_false=Op.REVERT(0, 0),
    )


@pytest.mark.parametrize(
    "first_frame,approves",
    [
        pytest.param("matching_claim", True, id="matching_claim"),
        pytest.param(
            "other_key",
            False,
            id="other_key",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            "other_message",
            False,
            id="other_message",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            "plain_frame",
            False,
            id="plain_frame_same_data",
            marks=pytest.mark.exception_test,
        ),
    ],
)
def test_account_approves_on_declared_claim(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    first_frame: str,
    approves: bool,
) -> None:
    """
    Approve a smart account's transaction only when it declares a claim
    matching the account's stored key and fixed message. The signature
    hash cannot appear in its own dependency data without a fixed point.
    """
    account_key_claim = claim(1, key=ACCOUNT_KEY)
    sender = pre.deploy_contract(
        code=claim_checking_account_code(),
        storage={
            0: int.from_bytes(account_key_claim[2], "big"),
            1: int.from_bytes(account_key_claim[1], "big"),
        },
        balance=10**18,
    )
    marker = pre.deploy_contract(code=Op.SSTORE(0, 1))
    noop = pre.deploy_contract(code=Op.STOP)

    first: Frame
    if first_frame == "matching_claim":
        first = dependency_frame(fork, [account_key_claim])
    elif first_frame == "other_key":
        first = dependency_frame(fork, [claim(1, key=ACCOUNT_KEY + 1)])
    elif first_frame == "other_message":
        first = dependency_frame(fork, [claim(2, key=ACCOUNT_KEY)])
    elif first_frame == "plain_frame":
        first = dependency_frame(
            fork,
            [account_key_claim],
            mode=Spec8141.MODE_DEFAULT,
            target=noop,
            gas_limit=fork.frame_entry_gas_calculator()(target_warm=False),
        )
    else:
        raise ValueError(f"unknown first frame: {first_frame}")
    tx = Transaction(
        sender=sender,
        nonce=1,
        frames=[first, verify_frame(), sender_frame(target=marker)],
        error=(
            None
            if approves
            else TransactionException.TYPE_6_INVALID_FRAME_EXECUTION
        ),
    )
    state_test(
        pre=pre,
        tx=tx,
        post={marker: Account(storage={0: 1 if approves else 0})},
    )


def test_dependency_frame_in_reverted_body(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Keep a dependency frame's receipt and its claim when a failing
    `POST_TX` frame reverts the execution body it sits in: the claim is
    declared by the transaction, not created by execution.
    """
    sender = pre.fund_eoa()
    writer = pre.deploy_contract(code=Op.SSTORE(0, 1))
    failure = pre.deploy_contract(code=Op.REVERT(0, 0))
    dependency = claim(1)
    tx = Transaction(
        sender=sender,
        frames=[
            verify_frame(),
            body_frame(fork, target=writer),
            dependency_frame(fork, [dependency]),
            post_tx_frame(fork, target=failure),
        ],
        expected_receipt=TransactionReceipt(
            payer=sender,
            frame_receipts=[
                FrameReceipt(status=Spec8141.STATUS_SUCCESS),
                FrameReceipt(status=Spec8141.STATUS_SUCCESS, logs=[]),
                dependency_receipt(fork, 1),
                FrameReceipt(status=Spec8141.STATUS_FAILURE),
            ],
        ),
    )
    state_test(
        pre=pre,
        tx=tx,
        post={sender: Account(nonce=1), writer: Account(storage={0: 0})},
        blockchain_test_header_verify=Header(
            recursive_stark=expected_recursive_stark([dependency])
        ),
    )
