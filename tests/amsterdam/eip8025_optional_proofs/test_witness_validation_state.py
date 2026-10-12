"""Execution witness state validation tests."""

from typing import Callable

import pytest
from ethereum_rlp import rlp
from ethereum_types.bytes import Bytes as TrieBytes
from execution_testing import (
    Account,
    Address,
    Alloc,
    Block,
    BlockchainTestFiller,
    Bytes,
    ExecutionWitnessStateExpectation,
    Fork,
    Op,
    Transaction,
    Withdrawal,
)
from execution_testing.forks import Amsterdam
from execution_testing.test_types.execution_witness import ExecutionWitness
from execution_testing.test_types.execution_witness.modifiers import (
    add_state_node,
    remove_state_node,
    reverse_state_nodes,
)

from ethereum.forks.amsterdam.incremental_mpt import compact_to_nibbles
from tests.cancun.eip4788_beacon_root.spec import Spec as SpecEip4788

from .gas_helpers import empty_account_value_transfer_gas_limit
from .spec import ref_spec_8025
from .state_helpers import (
    as_storage,
    build_large_storage,
    collect_account_path_only_nodes,
    collect_account_proof_nodes,
    collect_storage_delete_auxiliary_nodes,
    collect_storage_proof_nodes,
    find_account_with_shared_secured_nibble,
    large_storage_value,
    merge_with_amsterdam_pre_alloc,
)

pytestmark = pytest.mark.valid_from("Amsterdam")

REFERENCE_SPEC_GIT_PATH = ref_spec_8025.git_path
REFERENCE_SPEC_VERSION = ref_spec_8025.version

SYSTEM_ADDRESS = Address(SpecEip4788.SYSTEM_ADDRESS)
GWEI = 10**9


def _required_node(nodes: list[Bytes]) -> Bytes:
    """Pick one required trie node from a proof set."""
    assert nodes
    return sorted(nodes)[0]


def _leaf_node(nodes: list[Bytes]) -> Bytes:
    """Pick the unique leaf node from a proof set."""
    leaves: list[Bytes] = []
    for node in nodes:
        decoded = rlp.decode(bytes(node))
        if not isinstance(decoded, list) or len(decoded) != 2:
            continue
        path_bytes = decoded[0]
        assert isinstance(path_bytes, (bytes, bytearray))
        _, is_leaf = compact_to_nibbles(TrieBytes(path_bytes))
        if is_leaf:
            leaves.append(node)

    assert len(leaves) == 1
    return leaves[0]


def test_validation_state_missing_storage_proof_node(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """Removing a required storage proof node should fail the guest."""
    read_slot = 1
    write_slot = 2
    storage = build_large_storage([read_slot])
    proof_nodes = collect_storage_proof_nodes(storage, [read_slot])
    removed_node = _required_node(proof_nodes)

    contract = pre.deploy_contract(
        code=Op.SSTORE(write_slot, Op.SLOAD(read_slot)) + Op.STOP,
        storage=as_storage(storage),
    )
    sender = pre.fund_eoa()
    tx = Transaction(sender=sender, to=contract, gas_limit=500_000)
    post_storage = storage | {write_slot: storage[read_slot]}

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx],
                expected_execution_witness_state=(
                    ExecutionWitnessStateExpectation(
                        nodes_present=proof_nodes,
                    ).modify(remove_state_node(removed_node))
                ),
                expected_stateless_validation_success=False,
            )
        ],
        post={
            sender: Account(nonce=1),
            contract: Account(storage=post_storage),
        },
    )


def test_validation_state_missing_absent_slot_proof_leaf_node(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """Removing the absent-slot proof leaf should fail insertion."""
    # The contract will insert a value to a non-existent slot 1.

    # These slots produce a multi-node absence proof for slot 1:
    #
    #   keccak(1)  -> b1...
    #   keccak(24) -> b1...
    #   keccak(14) -> bx...  (x != 1)
    #
    #   ext("b") (root)
    #     |
    #   branch
    #   /    \
    # [x]    [1]
    #  |      |
    # leaf   leaf
    # (14)   (24)
    #         ^
    #         |
    #   absent slot 1 follows this edge, then diverges inside the leaf
    #
    # The proof for slot 1 is therefore `extension -> branch -> leaf`.
    # Removing that leaf makes the absence proof invalid due to missing
    # data.
    pre_storage = build_large_storage([14, 24])
    insert_slot = 1
    insert_value = large_storage_value(insert_slot)
    proof_nodes = collect_storage_proof_nodes(pre_storage, [insert_slot])
    assert len(proof_nodes) == 3
    removed_node = _leaf_node(proof_nodes)

    contract = pre.deploy_contract(
        code=Op.SSTORE(insert_slot, insert_value) + Op.STOP,
        storage=as_storage(pre_storage),
    )
    sender = pre.fund_eoa()
    tx = Transaction(sender=sender, to=contract, gas_limit=500_000)

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx],
                expected_execution_witness_state=(
                    ExecutionWitnessStateExpectation(
                        nodes_present=proof_nodes,
                    ).modify(remove_state_node(removed_node))
                ),
                expected_stateless_validation_success=False,
            )
        ],
        post={
            sender: Account(nonce=1),
            contract: Account(
                storage={**pre_storage, insert_slot: insert_value},
            ),
        },
    )


def test_validation_state_missing_delete_auxiliary_node(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """Removing the delete-collapse auxiliary node should fail."""
    storage = build_large_storage([1, 2])
    proof_nodes = collect_storage_proof_nodes(storage, [1])
    auxiliary_nodes = collect_storage_delete_auxiliary_nodes(storage, 1)
    assert len(auxiliary_nodes) == 1
    removed_node = auxiliary_nodes[0]

    contract = pre.deploy_contract(
        code=Op.SSTORE(1, 0) + Op.STOP,
        storage=as_storage(storage),
    )
    sender = pre.fund_eoa()
    tx = Transaction(sender=sender, to=contract, gas_limit=500_000)

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx],
                expected_execution_witness_state=(
                    ExecutionWitnessStateExpectation(
                        nodes_present=proof_nodes + auxiliary_nodes,
                    ).modify(remove_state_node(removed_node))
                ),
                expected_stateless_validation_success=False,
            )
        ],
        post={
            sender: Account(nonce=1),
            contract: Account(storage={2: storage[2]}),
        },
    )


def test_validation_state_missing_sender_account_proof_leaf_node(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """Removing the sender account proof leaf should fail a transfer."""
    sender = pre.fund_eoa()
    recipient = pre.fund_eoa(amount=1)
    full_alloc = merge_with_amsterdam_pre_alloc(pre)
    proof_nodes = collect_account_proof_nodes(full_alloc, [sender, recipient])
    sender_only_nodes = collect_account_path_only_nodes(
        full_alloc,
        sender,
        [recipient, *Amsterdam.execution_witness_implicit_code_addresses()],
    )
    assert len(sender_only_nodes) == 1
    removed_node = _leaf_node(sender_only_nodes)

    tx = Transaction(sender=sender, to=recipient, value=1, gas_limit=21_000)

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx],
                expected_execution_witness_state=(
                    ExecutionWitnessStateExpectation(
                        nodes_present=proof_nodes,
                    ).modify(remove_state_node(removed_node))
                ),
                expected_stateless_validation_success=False,
            )
        ],
        post={
            sender: Account(nonce=1),
            recipient: Account(balance=2),
        },
    )


def test_validation_state_missing_absent_account_proof_node(
    fork: Fork,
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """Removing a recipient-only absent-account proof node should fail."""
    sender = pre.fund_eoa()
    recipient = pre.fund_eoa(amount=0)
    # Add one untouched sibling under the recipient's secured-trie prefix so
    # the absence proof extends below the shared root node.
    sibling = find_account_with_shared_secured_nibble(
        recipient,
        {
            sender,
            recipient,
            *Amsterdam.execution_witness_implicit_code_addresses(),
        },
    )
    pre.fund_address(sibling, 1)
    full_alloc = merge_with_amsterdam_pre_alloc(pre)
    recipient_only_nodes = sorted(
        collect_account_path_only_nodes(
            full_alloc,
            recipient,
            [sender, *Amsterdam.execution_witness_implicit_code_addresses()],
        )
    )
    assert recipient_only_nodes
    proof_nodes = collect_account_proof_nodes(full_alloc, [recipient])
    removed_node = _required_node(recipient_only_nodes)

    tx = Transaction(
        sender=sender,
        to=recipient,
        value=1,
        gas_limit=empty_account_value_transfer_gas_limit(fork),
    )

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx],
                expected_execution_witness_state=(
                    ExecutionWitnessStateExpectation(
                        nodes_present=proof_nodes,
                    ).modify(remove_state_node(removed_node))
                ),
                expected_stateless_validation_success=False,
            )
        ],
        post={
            sender: Account(nonce=1),
            recipient: Account(balance=1),
        },
    )


def test_validation_state_missing_failed_call_target_account_proof_node(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """Removing the failed CALL target proof should fail witness replay."""
    target = pre.fund_eoa()
    caller_balance = 100
    transfer_value = 1_000
    caller_code = (
        Op.SSTORE(
            0,
            Op.CALL(
                Op.GAS,
                target,
                transfer_value,
                0,
                0,
                0,
                0,
            ),
        )
        + Op.STOP
    )
    caller = pre.deploy_contract(
        code=caller_code,
        balance=caller_balance,
        storage={0: 1},
    )
    sender = pre.fund_eoa()
    full_alloc = merge_with_amsterdam_pre_alloc(pre)
    proof_nodes = collect_account_proof_nodes(full_alloc, [target])
    assert proof_nodes
    removed_node = _leaf_node(proof_nodes)

    tx = Transaction(sender=sender, to=caller, gas_limit=500_000)

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx],
                expected_execution_witness_state=(
                    ExecutionWitnessStateExpectation(
                        nodes_present=proof_nodes,
                    ).modify(remove_state_node(removed_node))
                ),
                expected_stateless_validation_success=False,
            )
        ],
        post={
            sender: Account(nonce=1),
            caller: Account(balance=caller_balance, storage={0: 0}),
        },
    )


@pytest.mark.parametrize(
    "modifier",
    [
        pytest.param(
            add_state_node(Bytes(b"\x81\x99")),
            id="extra_unused_trie_node",
        ),
        pytest.param(reverse_state_nodes(), id="unsorted_but_complete"),
    ],
)
def test_validation_state_complete_witness_still_validates(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    modifier: Callable[[ExecutionWitness], ExecutionWitness],
) -> None:
    """
    Adding an unused state node or reordering a complete state witness
    should still validate.
    """
    storage = build_large_storage([1])
    proof_nodes = collect_storage_proof_nodes(storage, [1])

    contract = pre.deploy_contract(
        code=Op.SLOAD(1) + Op.POP + Op.STOP,
        storage=as_storage(storage),
    )
    sender = pre.fund_eoa()
    tx = Transaction(sender=sender, to=contract, gas_limit=500_000)

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx],
                expected_execution_witness_state=(
                    ExecutionWitnessStateExpectation(
                        nodes_present=proof_nodes,
                    ).modify(modifier)
                ),
                expected_stateless_validation_success=True,
            )
        ],
        post={
            sender: Account(nonce=1),
            contract: Account(storage=storage),
        },
    )


@pytest.mark.parametrize(
    "access",
    ["zero_withdrawal", "withdrawal", "balance"],
)
@pytest.mark.parametrize(
    "witness_complete",
    [
        pytest.param(True, id="complete_witness"),
        pytest.param(False, id="missing_proof_leaf"),
    ],
)
def test_validation_state_system_address_read(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    access: str,
    witness_complete: bool,
) -> None:
    """
    Require the SYSTEM_ADDRESS account proof when the block reads it.

    A system call uses SYSTEM_ADDRESS as its origin without reading its
    account, so its proof is otherwise absent. A withdrawal to it, even of
    zero, and a BALANCE of it both read the account, so the witness must
    prove it and removing its proof leaf must fail validation.
    """
    # A funded SYSTEM_ADDRESS has its own leaf in the account trie.
    pre.fund_address(SYSTEM_ADDRESS, 1)

    txs: list[Transaction] = []
    withdrawals: list[Withdrawal] = []
    post: dict[Address, Account] = {}
    if access == "balance":
        contract = pre.deploy_contract(
            code=Op.SSTORE(0, Op.BALANCE(SYSTEM_ADDRESS))
        )
        sender = pre.fund_eoa()
        txs.append(Transaction(sender=sender, to=contract))
        post[contract] = Account(storage={0: 1})
    else:
        amount = 0 if access == "zero_withdrawal" else 1
        withdrawals.append(
            Withdrawal(
                index=0,
                validator_index=0,
                address=SYSTEM_ADDRESS,
                amount=amount,
            )
        )
        post[SYSTEM_ADDRESS] = Account(balance=1 + amount * GWEI)

    full_alloc = merge_with_amsterdam_pre_alloc(pre)
    proof_nodes = collect_account_proof_nodes(full_alloc, [SYSTEM_ADDRESS])
    expectation = ExecutionWitnessStateExpectation(nodes_present=proof_nodes)
    if not witness_complete:
        expectation = expectation.modify(
            remove_state_node(_leaf_node(proof_nodes))
        )

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=txs,
                withdrawals=withdrawals,
                expected_execution_witness_state=expectation,
                expected_stateless_validation_success=witness_complete,
            )
        ],
        post=post,
    )
