"""
`TXDIFF` views and flags (EIP-7906): the per-account change flags, and
the per-address slot and event views and the per-topic event view
mapped onto the transaction's tables.
"""

from typing import Callable, Dict, List

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Bytecode,
    Fork,
    Op,
    StateTestFiller,
)

from .helpers import (
    KEY_A,
    KEY_B,
    NEVER_EXISTED,
    TOPIC_1,
    TOPIC_2,
    TOPIC_3,
    TOPIC_4,
    MixedBody,
    as_int,
    assertion_transaction,
    body_frame,
    expect_eq,
    mixed_body,
    success_receipts,
)
from .spec import Spec, ref_spec_7906

REFERENCE_SPEC_GIT_PATH = ref_spec_7906.git_path
REFERENCE_SPEC_VERSION = ref_spec_7906.version

pytestmark = pytest.mark.valid_from("EIP7906")

TOPIC_ABSENT = (
    0x9999999999999999999999999999999999999999999999999999999999999999
)

BodyAccount = Callable[[MixedBody], Address]
"""Pick an account of the body."""


@pytest.mark.parametrize(
    "account,flags",
    [
        pytest.param(
            lambda body: body.sender,
            Spec.CHANGE_FLAG_NONCE | Spec.CHANGE_FLAG_BALANCE,
            id="payer",
        ),
        pytest.param(
            lambda body: body.writer,
            Spec.CHANGE_FLAG_STORAGE,
            id="storage_writer",
        ),
        pytest.param(
            lambda body: body.recipient,
            Spec.CHANGE_FLAG_BALANCE,
            id="recipient",
        ),
        pytest.param(
            lambda body: body.deployed,
            Spec.CHANGE_FLAG_NONCE | Spec.CHANGE_FLAG_CODE,
            id="deployed_contract",
        ),
        pytest.param(
            lambda body: body.factory, Spec.CHANGE_FLAG_NONCE, id="factory"
        ),
        pytest.param(lambda body: body.untouched, 0, id="untouched"),
        pytest.param(lambda body: body.restorer, 0, id="restored_storage"),
        pytest.param(lambda _: NEVER_EXISTED, 0, id="never_existed"),
    ],
)
def test_account_change_flags(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    account: BodyAccount,
    flags: int,
) -> None:
    """
    Summarize an account's net change in the flags bitmask, where a
    slot written then restored sets no bit.
    """
    body = mixed_body(pre, fork)
    assertion = pre.deploy_contract(
        code=expect_eq(
            Op.TXDIFF(Spec.TXDIFF_ACCOUNT_CHANGE_FLAGS, account(body), 0),
            flags,
        )
        + Op.STOP
    )
    state_test(pre=pre, tx=body.transaction(fork, assertion), post=body.post())


@pytest.mark.parametrize(
    "account,global_indices",
    [
        pytest.param(lambda body: body.writer, [0, 1], id="storage_writer"),
        pytest.param(lambda body: body.recipient, [], id="recipient"),
        pytest.param(lambda body: body.restorer, [], id="restored_storage"),
    ],
)
def test_address_slot_view(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    account: BodyAccount,
    global_indices: List[int],
) -> None:
    """
    Count an account's entries in `slots_changed` and map each local
    index onto the table, a slot written then restored having none.
    """
    body = mixed_body(pre, fork)
    address = account(body)
    checks = expect_eq(
        Op.TXDIFF(Spec.TXDIFF_ADDRESS_SLOTS_COUNT, address, 0),
        len(global_indices),
    )
    for local_index, global_index in enumerate(global_indices):
        checks += expect_eq(
            Op.TXDIFF(Spec.TXDIFF_ADDRESS_SLOT_INDEX, address, local_index),
            global_index,
        )
    assertion = pre.deploy_contract(code=checks + Op.STOP)
    state_test(pre=pre, tx=body.transaction(fork, assertion), post=body.post())


def test_txdiff_slot_view_maps_to_global_index(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Map each address's local slot index onto the global `slots_changed`
    index: the higher address's slots follow every slot of the lower.
    """
    sender = pre.fund_eoa()
    code = Op.SSTORE(KEY_A, 1) + Op.SSTORE(KEY_B, 1) + Op.STOP
    low, high = sorted(
        [pre.deploy_contract(code=code), pre.deploy_contract(code=code)],
        key=as_int,
    )
    checks = Bytecode()
    for writer, first_global_index in ((low, 0), (high, 2)):
        checks += expect_eq(
            Op.TXDIFF(Spec.TXDIFF_ADDRESS_SLOTS_COUNT, writer, 0), 2
        )
        for local_index in range(2):
            checks += expect_eq(
                Op.TXDIFF(Spec.TXDIFF_ADDRESS_SLOT_INDEX, writer, local_index),
                first_global_index + local_index,
            )
    assertion = pre.deploy_contract(code=checks + Op.STOP)

    state_test(
        pre=pre,
        tx=assertion_transaction(
            fork,
            sender,
            body=[body_frame(fork, target=high), body_frame(fork, target=low)],
            assertion=assertion,
            frame_receipts=success_receipts(4),
        ),
        post={
            sender: Account(nonce=1),
            low: Account(storage={KEY_A: 1, KEY_B: 1}),
            high: Account(storage={KEY_A: 1, KEY_B: 1}),
        },
    )


def view_checks(
    count_param: int, index_param: int, key: int | Address, indices: List[int]
) -> Bytecode:
    """Return checks of a view's count and its local-to-global indices."""
    checks = expect_eq(Op.TXDIFF(count_param, key, 0), len(indices))
    for local_index, global_index in enumerate(indices):
        checks += expect_eq(
            Op.TXDIFF(index_param, key, local_index), global_index
        )
    return checks


def fill_event_views(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    checks: Callable[[Dict[str, Address]], Bytecode],
) -> None:
    """
    Fill a body emitting, in order, a three-topic event from emitter
    `a`, a signature-only event from `b`, `a`'s event again and a
    four-topic event from `c`, followed by a `POST_TX` frame running
    `checks` on the event table of four entries.
    """
    sender = pre.fund_eoa()
    accounts = {
        "sender": sender,
        "a": pre.deploy_contract(
            code=Op.LOG3(0, 0, TOPIC_1, TOPIC_3, TOPIC_2) + Op.STOP
        ),
        "b": pre.deploy_contract(code=Op.LOG1(0, 0, TOPIC_1) + Op.STOP),
        "c": pre.deploy_contract(
            code=Op.LOG4(0, 0, TOPIC_1, TOPIC_2, TOPIC_3, TOPIC_4) + Op.STOP
        ),
    }
    assertion = pre.deploy_contract(
        code=expect_eq(Op.TXTRACE(Spec.TXTRACE_EVENTS_COUNT, 0), 4)
        + checks(accounts)
        + Op.STOP
    )
    state_test(
        pre=pre,
        tx=assertion_transaction(
            fork,
            sender,
            body=[
                body_frame(fork, target=accounts[name])
                for name in ("a", "b", "a", "c")
            ],
            assertion=assertion,
            frame_receipts=success_receipts(6),
        ),
        post={sender: Account(nonce=1)},
    )


@pytest.mark.parametrize(
    "emitter,global_indices",
    [
        pytest.param("a", [0, 2], id="emitter_of_two_events"),
        pytest.param("b", [1], id="emitter_of_one_event"),
        pytest.param("c", [3], id="last_emitter"),
        pytest.param("sender", [], id="non_emitter"),
    ],
)
def test_address_event_view(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    emitter: str,
    global_indices: List[int],
) -> None:
    """
    Count an address's events and map each local index onto the event
    table.
    """
    fill_event_views(
        state_test,
        pre,
        fork,
        lambda accounts: view_checks(
            Spec.TXDIFF_ADDRESS_EVENTS_COUNT,
            Spec.TXDIFF_ADDRESS_EVENT_INDEX,
            accounts[emitter],
            global_indices,
        ),
    )


@pytest.mark.parametrize(
    "topic,global_indices",
    [
        pytest.param(TOPIC_2, [0, 2, 3], id="in_topic2_then_topic1"),
        pytest.param(TOPIC_3, [0, 2, 3], id="in_topic1_then_topic2"),
        pytest.param(TOPIC_4, [3], id="only_in_topic3"),
        pytest.param(TOPIC_1, [], id="only_signature_topic"),
        pytest.param(TOPIC_ABSENT, [], id="absent"),
    ],
)
def test_topic_event_view(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    topic: int,
    global_indices: List[int],
) -> None:
    """
    Count the events carrying a value in any of `topic1` to `topic3`,
    excluding the signature topic, and map each local index onto the
    event table.
    """
    fill_event_views(
        state_test,
        pre,
        fork,
        lambda _: view_checks(
            Spec.TXDIFF_TOPIC_EVENTS_COUNT,
            Spec.TXDIFF_TOPIC_EVENT_INDEX,
            topic,
            global_indices,
        ),
    )
