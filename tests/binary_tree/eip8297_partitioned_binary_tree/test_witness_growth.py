"""
Witness cost of reading chunked code.

The rest of this suite pins that chunking is invisible to execution
semantics. It is not invisible to a witness. Executing one byte of a
contract requires proving every chunk that contract occupies, because
the code is reassembled from the tree rather than shipped alongside it.

Each test below executes a fixed 6 bytes -- `SSTORE(slot, value)` then
`STOP` -- while varying only the dead padding behind the `STOP`. Every
parametrisation performs identical work and touches identical state.
The only thing that changes is how many chunk leaves the contract
occupies, and therefore how large its proof is.

Measured on erigon's EIP-8297 engine (BLAKE3), a chunk leaf is 67 bytes
(1 tag + 34 key + 32 value) and the branch binding it is ~68, so a
contract costs about (67 + 68) / 31 = 4.35x its bytecode in witness
bytes. Against a Merkle-Patricia client, which ships the same bytecode
as one blob beside a short account proof, reading a 4,216-byte contract
measured 19,666 bytes against 5,238 -- 3.75x on total witness bytes,
for identical execution.

Two consequences these cases are built to expose:

  - The cost tracks code SIZE, not code EXECUTED. `deep_overflow` runs
    the same 6 bytes as `single_chunk` and proves 793 chunks.
  - It is asymmetric with deployment. Creating a contract proves no
    chunk pre-state, so deploying is cheap and reading back is not;
    `test_deploy_then_read_asymmetry` pairs the two in one chain.

Nothing here asserts a witness size -- no fixture format carries one
for this fork. These are ordinary state and blockchain tests whose
post-states are trivially correct; the cost shows up when a client
fills or proves them.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Block,
    BlockchainTestFiller,
    Initcode,
    Op,
    StateTestFiller,
    Transaction,
    keccak256,
)

from .helpers import sstore_then_pad
from .spec import Spec, ref_spec_8297

REFERENCE_SPEC_GIT_PATH = ref_spec_8297.git_path
REFERENCE_SPEC_VERSION = ref_spec_8297.version

pytestmark = pytest.mark.valid_from("BinaryTree")

# 31 * 128 = 3,968: the last byte that still fits the account header.
# One byte more opens the first content-addressed overflow chunk.
HEADER_CODE_BYTES = Spec.CODE_CHUNK_SIZE * (
    Spec.STEM_SUBTREE_WIDTH - Spec.CODE_OFFSET
)

# EIP-170. The largest contract deployable today, and so the largest
# single-account code proof reachable on mainnet.
MAX_CODE_SIZE = 24576

_SLOT = 0
_VALUE = 0xCAFE


@pytest.mark.parametrize(
    "code_size",
    [
        pytest.param(Spec.CODE_CHUNK_SIZE, id="single_chunk"),
        pytest.param(HEADER_CODE_BYTES, id="header_full"),
        pytest.param(HEADER_CODE_BYTES + 1, id="first_overflow_chunk"),
        pytest.param(HEADER_CODE_BYTES * 2, id="deep_overflow"),
        pytest.param(MAX_CODE_SIZE, id="max_code_size"),
    ],
)
def test_witness_cost_of_reading_chunked_code(
    state_test: StateTestFiller,
    pre: Alloc,
    code_size: int,
) -> None:
    """
    Execute the same 6 bytes against contracts of five different sizes.

    Work done, gas charged and state touched are identical across the
    parametrisation -- only the dead padding behind the `STOP` differs.
    The proof is not identical: it carries every chunk the contract
    occupies, which is 1, 128, 129, 256 and 793 leaves respectively.

    Padding is `INVALID`, so a client that mis-executes past the `STOP`
    fails loudly rather than quietly proving the point for the wrong
    reason.
    """
    contract = pre.deploy_contract(
        code=sstore_then_pad(slot=_SLOT, value=_VALUE, total_size=code_size),
    )
    sender = pre.fund_eoa()

    state_test(
        pre=pre,
        tx=Transaction(sender=sender, to=contract, gas_limit=200_000),
        post={contract: Account(storage={_SLOT: _VALUE})},
    )


def test_deploy_then_read_asymmetry(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
) -> None:
    """
    Deploy an overflowing contract in one block, call it in the next.

    The two blocks move the same bytecode through the tree in opposite
    directions. Block 1 writes 256 chunk leaves and proves none of them
    -- they have no pre-state. Block 2 executes 6 bytes and proves all
    256.

    Erigon measures 8 nodes for the deploying block against 284 for the
    reading block on a 4,216-byte contract. The asymmetry is the reason
    a code-heavy block's witness is dominated by contracts it merely
    called, not by contracts it created.
    """
    sender = pre.fund_eoa()
    runtime = sstore_then_pad(
        slot=_SLOT, value=_VALUE, total_size=HEADER_CODE_BYTES * 2
    )
    initcode = Initcode(deploy_code=runtime)

    deploy_tx = Transaction(
        sender=sender, to=None, data=initcode, gas_limit=15_000_000
    )
    deployed = deploy_tx.created_contract
    call_tx = Transaction(sender=sender, to=deployed, gas_limit=200_000)

    blockchain_test(
        pre=pre,
        blocks=[Block(txs=[deploy_tx]), Block(txs=[call_tx])],
        post={deployed: Account(code=runtime, storage={_SLOT: _VALUE})},
    )


@pytest.mark.parametrize(
    "op_name",
    [
        pytest.param("extcodesize", id="extcodesize"),
        pytest.param("extcodehash", id="extcodehash"),
    ],
)
def test_code_introspection_needs_no_chunk(
    state_test: StateTestFiller,
    pre: Alloc,
    op_name: str,
) -> None:
    """
    `EXTCODESIZE` and `EXTCODEHASH` against a maximum-size contract.

    Both are answered from the account header -- `code_size` is packed
    into `BASIC_DATA` and `code_hash` is its own leaf -- so each costs
    one leaf regardless of the 793 chunks the target occupies. Neither
    reads a chunk.

    Kept here as the control for the cases above: it separates what
    chunking actually defends against from what the header layout
    already answers on its own.
    """
    code = sstore_then_pad(slot=_SLOT, value=_VALUE, total_size=MAX_CODE_SIZE)
    target = pre.deploy_contract(code=code)

    if op_name == "extcodesize":
        probe, expected = Op.EXTCODESIZE, MAX_CODE_SIZE
    else:
        probe, expected = (
            Op.EXTCODEHASH,
            int.from_bytes(keccak256(bytes(code)), "big"),
        )

    caller = pre.deploy_contract(
        code=Op.SSTORE(_SLOT, probe(target)) + Op.STOP
    )
    sender = pre.fund_eoa()

    state_test(
        pre=pre,
        tx=Transaction(sender=sender, to=caller, gas_limit=200_000),
        post={caller: Account(storage={_SLOT: expected})},
    )
