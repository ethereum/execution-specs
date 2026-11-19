"""
Properties of the requests a block hands to the consensus layer.

The framework builds a deposit and the log the deposit contract emits for
it, and hashes a list of requests, each written apart from `src/`. The
spec must read the same deposit back out of that log, refuse a log laid
out any other way, and commit to the same hash.
"""

import inspect
from types import ModuleType
from typing import Any, Dict, List, Tuple

import pytest
from ethereum_types.bytes import Bytes, Bytes32
from ethereum_types.numeric import Uint
from execution_testing.base_types import Bytes as FrameworkBytes
from execution_testing.forks import DepositRequest, Requests
from execution_testing.forks.forks.eips.prague.eip_6110 import (
    create_deposit_log_bytes,
)
from hypothesis import given
from hypothesis import strategies as st

from ethereum.crypto.hash import keccak256
from ethereum.exceptions import InvalidBlock
from ethereum.merkle_patricia_trie import trie_set
from ethereum.state import Address
from ethereum_spec_tools.forks import Hardfork

from .forks import requires
from .spec_api import transaction_types, zeroed
from .strategies import MAX_U64, MAX_U256, addresses, ints

pytestmark = requires(lambda fork: fork.header_requests_required())

# EIP-6110: the event the deposit contract logs for each deposit.
DEPOSIT_EVENT_TOPIC = keccak256(b"DepositEvent(bytes,bytes,bytes,bytes,bytes)")
# The framework's layout of a well-formed event: each field's offset and
# size word.
WELL_FORMED_LAYOUT: Dict[str, int] = {
    name: parameter.default
    for name, parameter in inspect.signature(
        create_deposit_log_bytes
    ).parameters.items()
    if name.endswith(("_offset", "_size"))
}


@pytest.fixture(scope="session")
def requests(spec: Hardfork) -> ModuleType:
    """Return the requests module of the fork under test."""
    return spec.module("requests")


deposits = st.tuples(
    st.binary(min_size=48, max_size=48),
    st.binary(min_size=32, max_size=32),
    ints(MAX_U64),
    st.binary(min_size=96, max_size=96),
    ints(MAX_U64),
).map(
    lambda fields: DepositRequest(
        pubkey=fields[0],
        withdrawal_credentials=fields[1],
        amount=fields[2],
        signature=fields[3],
        index=fields[4],
    )
)


def event_data(deposit: DepositRequest, **layout: int) -> bytes:
    """Return the deposit's event data, with `layout` words replaced."""
    return create_deposit_log_bytes(
        pubkey_data=bytes(deposit.pubkey),
        withdrawal_credentials_data=bytes(deposit.withdrawal_credentials),
        amount_data=deposit.amount.to_bytes(8, "little"),
        signature_data=bytes(deposit.signature),
        index_data=deposit.index.to_bytes(8, "little"),
        **layout,
    )


@pytest.mark.parametrize("word", sorted(WELL_FORMED_LAYOUT))
@given(deposit=deposits, data=st.data())
def test_deposit_event_layout_is_exact(
    requests: ModuleType,
    word: str,
    deposit: DepositRequest,
    data: st.DataObject,
) -> None:
    """
    The deposit in a well-formed event is read back field for field, and
    an event with one offset or size word changed is invalid.
    """
    well_formed = event_data(deposit)
    assert requests.extract_deposit_data(Bytes(well_formed)) == bytes(deposit)

    correct = WELL_FORMED_LAYOUT[word]
    # Another field's offset points at a size word that may equal this
    # field's, so every other word of the layout is tried as well.
    others = set(WELL_FORMED_LAYOUT.values()) | {
        data.draw(ints(MAX_U256), label="any other value")
    }
    for changed in sorted(others - {correct}):
        malformed = event_data(deposit, **{word: changed})
        with pytest.raises(InvalidBlock):
            requests.extract_deposit_data(Bytes(malformed))

    # An offset that points at a copy of its field's size word, planted in
    # the signature, is still not where the field belongs.
    field = word.removesuffix("_offset")
    if field in ("pubkey", "withdrawal_credentials", "amount", "index"):
        size_word = WELL_FORMED_LAYOUT[f"{field}_size"].to_bytes(32, "big")
        decoy = deposit.copy(
            signature=size_word + bytes(deposit.signature)[32:]
        )
        in_signature = WELL_FORMED_LAYOUT["signature_offset"] + 32
        with pytest.raises(InvalidBlock):
            requests.extract_deposit_data(
                Bytes(event_data(decoy, **{word: in_signature}))
            )


@given(deposit=deposits, extra=st.binary(min_size=1, max_size=32))
def test_deposit_event_length_is_exact(
    requests: ModuleType, deposit: DepositRequest, extra: bytes
) -> None:
    """An event with bytes missing or added is invalid."""
    well_formed = event_data(deposit)
    for data in (well_formed[: -len(extra)], well_formed + extra):
        with pytest.raises(InvalidBlock):
            requests.extract_deposit_data(Bytes(data))


# What a log is, next to a deposit event: `deposit` is one, and each other
# kind differs from one in the way its name says.
LOG_KINDS = ["deposit", "other_address", "other_topic", "no_topics"]


@given(data=st.data())
def test_only_deposit_events_become_requests(
    spec: Hardfork, requests: ModuleType, data: st.DataObject
) -> None:
    """
    The deposit requests of a block are its deposit events in log order:
    logs from another address, with another first topic or with no topic
    are passed over, whatever they hold.
    """
    blocks = spec.module("blocks")
    vm = spec.module("vm")
    make_receipt = spec.module("fork").make_receipt
    tx = zeroed(transaction_types(spec.module("transactions"))[0])
    contract = Address(DepositRequest.system_contract_address)
    other_address = data.draw(addresses().filter(lambda a: a != contract))
    other_topic = data.draw(
        st.binary(min_size=32, max_size=32).filter(
            lambda topic: topic != DEPOSIT_EVENT_TOPIC
        )
    )

    expected = b""
    block_output = vm.BlockOutput()
    receipts = data.draw(
        st.lists(
            st.lists(
                st.tuples(st.sampled_from(LOG_KINDS), deposits), max_size=3
            ),
            max_size=3,
        )
    )
    for index, receipt_logs in enumerate(receipts):
        logs: List[Any] = []
        for kind, deposit in receipt_logs:
            address = contract
            topics: Tuple[Bytes32, ...] = (Bytes32(DEPOSIT_EVENT_TOPIC),)
            log_data = event_data(deposit)
            if kind == "deposit":
                expected += bytes(deposit)
            elif kind == "other_address":
                address = other_address
            elif kind == "other_topic":
                # A log the contract emits that is no deposit event may
                # hold anything, so its data is cut short.
                topics = (Bytes32(other_topic),)
                log_data = log_data[:-1]
            elif kind == "no_topics":
                topics = ()
                log_data = log_data[:-1]
            else:
                raise ValueError(f"unknown log kind: {kind}")
            logs.append(blocks.Log(address, topics, Bytes(log_data)))
        key = Bytes(bytes([index]))
        trie_set(
            block_output.receipts_trie,
            key,
            make_receipt(tx, None, Uint(0), tuple(logs)),
        )
        block_output.receipt_keys += (key,)

    assert requests.parse_deposit_requests(block_output) == expected


@given(
    requests_list=st.lists(st.binary(min_size=1, max_size=64), max_size=6),
)
def test_requests_hash_matches_the_framework(
    requests: ModuleType, requests_list: List[bytes]
) -> None:
    """The commitment to a list of requests matches the framework's."""
    expected = bytes(
        Requests(requests_lists=[FrameworkBytes(r) for r in requests_list])
    )
    spec_requests = [Bytes(request) for request in requests_list]
    assert requests.compute_requests_hash(spec_requests) == expected
