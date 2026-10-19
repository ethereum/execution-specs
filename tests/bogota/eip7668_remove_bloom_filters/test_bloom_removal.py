"""Tests for [EIP-7668: Remove bloom filters](https://eips.ethereum.org/EIPS/eip-7668)."""

import pytest
from execution_testing import (
    Alloc,
    Block,
    BlockchainTestFiller,
    BlockException,
    Bloom,
    Bytecode,
    EngineAPIError,
    Hash,
    Header,
    Op,
    StateTestFiller,
    Transaction,
    TransactionLog,
    TransactionReceipt,
)

from .spec import ref_spec_7668

REFERENCE_SPEC_GIT_PATH = ref_spec_7668.git_path
REFERENCE_SPEC_VERSION = ref_spec_7668.version

FORK_TIMESTAMP = 15_000

EMPTY_BLOOM = Bloom(b"")

LOG_DATA = b"\x5a" * 32

TOPICS = [0x1111, 0x2222, 0x3333, 0x4444]


def log_code(topic_count: int) -> Bytecode:
    """Return code emitting one log with `topic_count` topics and LOG_DATA."""
    log_opcode = getattr(Op, f"LOG{topic_count}")
    return Op.MSTORE(0, int.from_bytes(LOG_DATA, "big")) + log_opcode(
        0, len(LOG_DATA), *TOPICS[:topic_count]
    )


@pytest.mark.valid_from("EIP7668")
@pytest.mark.parametrize("topic_count", range(5))
def test_empty_bloom_with_logs(
    state_test: StateTestFiller,
    pre: Alloc,
    topic_count: int,
) -> None:
    """
    A transaction emitting logs leaves the receipt and header blooms empty.

    The emitted logs are asserted on the receipt so that the empty bloom
    cannot be the trivial consequence of a transaction without logs.
    """
    emitter = pre.deploy_contract(code=log_code(topic_count))
    sender = pre.fund_eoa()

    tx = Transaction(
        sender=sender,
        to=emitter,
        expected_receipt=TransactionReceipt(
            bloom=EMPTY_BLOOM,
            logs=[
                TransactionLog(
                    address=emitter,
                    topics=[Hash(topic) for topic in TOPICS[:topic_count]],
                    data=LOG_DATA,
                )
            ],
        ),
    )

    state_test(
        pre=pre,
        post={},
        tx=tx,
        blockchain_test_header_verify=Header(logs_bloom=EMPTY_BLOOM),
    )


@pytest.mark.valid_from("EIP7668")
@pytest.mark.exception_test
def test_invalid_non_empty_bloom(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
) -> None:
    """
    Reject a block whose header carries a bloom of the pre-fork length.

    The block emits logs, so a client that still computes the filter and
    compares it against the header is the one that accepts this block.
    """
    sender = pre.fund_eoa()
    emitter = pre.deploy_contract(code=log_code(1))

    blockchain_test(
        pre=pre,
        post={},
        blocks=[
            Block(
                txs=[Transaction(sender=sender, to=emitter)],
                rlp_modifier=Header(logs_bloom=Bloom(LOG_DATA * 8)),
                exception=BlockException.INCORRECT_BLOCK_FORMAT,
                engine_api_error_code=EngineAPIError.InvalidParams,
            )
        ],
    )


@pytest.mark.valid_from("EIP7668")
@pytest.mark.exception_test
@pytest.mark.blockchain_test_only
def test_invalid_all_zero_bloom(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
) -> None:
    """
    Reject a block whose header carries 256 zero bytes where the bloom used
    to be.

    EIP-7668 constrains the length and not the value, so a client that only
    checks that the bloom bits are clear accepts this block. The violation
    lives in the RLP encoding alone: the execution payload keeps a 256-byte
    zero bloom either way, so this case is blockchain-test only.
    """
    sender = pre.fund_eoa()
    emitter = pre.deploy_contract(code=log_code(1))

    blockchain_test(
        pre=pre,
        post={},
        blocks=[
            Block(
                txs=[Transaction(sender=sender, to=emitter)],
                rlp_modifier=Header(logs_bloom=Bloom(0)),
                exception=BlockException.INCORRECT_BLOCK_FORMAT,
            )
        ],
    )


@pytest.mark.valid_at_transition_to("EIP7668")
def test_bloom_removal_at_fork_transition(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
) -> None:
    """
    The header bloom loses its 256 bytes exactly at the fork activation.

    The pre-fork block emits no logs so that its bloom is the all-zero
    filter, which differs from the post-fork bloom only in length.
    """
    sender = pre.fund_eoa()
    emitter = pre.deploy_contract(code=log_code(4))

    blockchain_test(
        pre=pre,
        post={},
        blocks=[
            Block(
                timestamp=FORK_TIMESTAMP // 2,
                txs=[],
                header_verify=Header(logs_bloom=Bloom(0)),
            ),
            Block(
                timestamp=FORK_TIMESTAMP,
                txs=[Transaction(sender=sender, to=emitter)],
                header_verify=Header(logs_bloom=EMPTY_BLOOM),
            ),
        ],
    )
