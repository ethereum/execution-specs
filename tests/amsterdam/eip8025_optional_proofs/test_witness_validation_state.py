"""Execution witness state validation tests."""

from typing import Callable, Type

import pytest
from ethereum_rlp import rlp
from ethereum_types.bytes import Bytes as TrieBytes
from execution_testing import (
    Account,
    Address,
    Alloc,
    AuthorizationTuple,
    Block,
    BlockchainTestFiller,
    Bytes,
    Environment,
    ExecutionWitnessStateExpectation,
    FeeSystemContractRequest,
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
    find_account_ending_absence_proof,
    find_account_with_shared_secured_nibble,
    large_storage_value,
    merge_with_amsterdam_pre_alloc,
    storage_root_node,
)

pytestmark = pytest.mark.valid_from("Amsterdam")

REFERENCE_SPEC_GIT_PATH = ref_spec_8025.git_path
REFERENCE_SPEC_VERSION = ref_spec_8025.version

SYSTEM_ADDRESS = Address(SpecEip4788.SYSTEM_ADDRESS)


def _required_node(nodes: list[Bytes]) -> Bytes:
    """Pick one required trie node from a proof set."""
    assert nodes
    return sorted(nodes)[0]


def _leaf_nodes(nodes: list[Bytes]) -> list[Bytes]:
    """Return the leaf nodes of a proof set."""
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
    return leaves


def _leaf_node(nodes: list[Bytes]) -> Bytes:
    """Pick the unique leaf node from a proof set."""
    leaves = _leaf_nodes(nodes)
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


@pytest.mark.parametrize("target_kind", ["eoa", "system_address", "absent"])
@pytest.mark.parametrize(
    "access",
    [
        "fee_recipient_without_tip",
        "zero_value_transfer",
        "zero_withdrawal",
        "authorization_wrong_nonce",
        pytest.param(
            "authorization_authority_has_code",
            marks=pytest.mark.pre_alloc_mutable,
        ),
        "balance",
        "extcodehash",
        "extcodesize",
        "selfdestruct_zero_balance",
    ],
)
@pytest.mark.parametrize(
    "witness_complete",
    [
        pytest.param(True, id="complete_witness"),
        pytest.param(False, id="missing_proof_leaf"),
    ],
)
def test_validation_state_unchanged_account_read(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    target_kind: str,
    access: str,
    witness_complete: bool,
) -> None:
    """
    Require an account's proof when the block reads it without a change.

    After such a read, a guest that treats a missing proof as an absent
    account computes the same post-state root, so only the witness check can
    reject a block whose witness leaves the proof out. SYSTEM_ADDRESS is a
    target of its own: system calls use it without reading it, so its proof
    is otherwise absent. An absent target is the account version of an
    absent slot: a guest that treats the missing node as empty reads the
    target as absent, which happens to be right.
    """
    # A funded target has its own leaf in the account trie.
    target: Address
    if target_kind == "eoa":
        if access == "authorization_authority_has_code":
            target = pre.fund_eoa(amount=1, code=Op.STOP, nonce=1)
        else:
            target = pre.fund_eoa(amount=1)
    elif target_kind == "system_address":
        if access.startswith("authorization_"):
            pytest.skip("SYSTEM_ADDRESS has no key to sign an authorization")
        target = SYSTEM_ADDRESS
        pre.fund_address(target, 1)
    elif target_kind == "absent":
        if access == "authorization_authority_has_code":
            pytest.skip("An absent account holds no code")
        # A key with no account, so that it can sign an authorization.
        target = pre.fund_eoa(amount=0)
    else:
        raise ValueError(f"Unknown target kind: {target_kind}")

    sender = pre.fund_eoa()
    txs: list[Transaction] = []
    withdrawals: list[Withdrawal] = []
    fee_recipient: Address | None = None
    # The opcode cases discard the result: storing it would change the
    # post-state root under a guest that reads the target as absent.
    if access == "fee_recipient_without_tip":
        # With no tip, paying the fee recipient reads it but adds nothing. The
        # max fee clears the base fee, so only the priority fee sets the tip.
        fee_recipient = target
        txs.append(
            Transaction(
                sender=sender,
                to=pre.fund_eoa(amount=0),
                max_fee_per_gas=1_000,
                max_priority_fee_per_gas=0,
            )
        )
    elif access == "zero_value_transfer":
        txs.append(Transaction(sender=sender, to=target, value=0))
    elif access == "zero_withdrawal":
        withdrawals.append(
            Withdrawal(index=0, validator_index=0, address=target, amount=0)
        )
    elif access in (
        "authorization_wrong_nonce",
        "authorization_authority_has_code",
    ):
        # The authorization fails for one reason: a nonce mismatch, or the
        # target's code. A guest that reads the target as absent sees nonce
        # 0, which does not match, so it skips the authorization too.
        txs.append(
            Transaction(
                sender=sender,
                to=pre.fund_eoa(amount=0),
                authorization_list=[
                    AuthorizationTuple(
                        address=pre.deploy_contract(code=Op.STOP),
                        nonce=1,
                        signer=target,
                    )
                ],
            )
        )
    elif access == "balance":
        contract = pre.deploy_contract(code=Op.POP(Op.BALANCE(target)))
        txs.append(Transaction(sender=sender, to=contract))
    elif access == "extcodehash":
        contract = pre.deploy_contract(code=Op.POP(Op.EXTCODEHASH(target)))
        txs.append(Transaction(sender=sender, to=contract))
    elif access == "extcodesize":
        contract = pre.deploy_contract(code=Op.POP(Op.EXTCODESIZE(target)))
        txs.append(Transaction(sender=sender, to=contract))
    elif access == "selfdestruct_zero_balance":
        # With no balance to move, the beneficiary only gets read.
        contract = pre.deploy_contract(code=Op.SELFDESTRUCT(target))
        txs.append(Transaction(sender=sender, to=contract))
    else:
        raise ValueError(f"Unknown access: {access}")

    sibling: Address | None = None
    if target_kind == "absent":
        # An absence proof ends in the node its path reaches: the root, a
        # branch or another account's leaf, which other proofs hold too. A
        # sibling whose leaf ends the target's proof gives it a node of its
        # own.
        sibling = find_account_ending_absence_proof(
            merge_with_amsterdam_pre_alloc(pre), target
        )
        pre.fund_address(sibling, 1)

    full_alloc = merge_with_amsterdam_pre_alloc(pre)
    proof_nodes = collect_account_proof_nodes(full_alloc, [target])
    if sibling is None:
        removed_node = _leaf_node(proof_nodes)
    else:
        # No other address the block names may need the sibling's leaf, or
        # the guest could reject the block for that address's read.
        named = {
            *full_alloc,
            *(tx.to for tx in txs if tx.to is not None),
            Environment().fee_recipient
            if fee_recipient is None
            else fee_recipient,
        }
        target_only_nodes = collect_account_path_only_nodes(
            full_alloc, target, list(named - {target, sibling})
        )
        assert len(target_only_nodes) == 1
        removed_node = _leaf_node(target_only_nodes)
    expectation = ExecutionWitnessStateExpectation(nodes_present=proof_nodes)
    if not witness_complete:
        expectation = expectation.modify(remove_state_node(removed_node))

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=txs,
                withdrawals=withdrawals,
                fee_recipient=fee_recipient,
                expected_execution_witness_state=expectation,
                expected_stateless_validation_success=witness_complete,
            )
        ],
        # The read leaves the target as it was.
        post={
            target: pre[target] if sibling is None else Account.NONEXISTENT,
        },
    )


@pytest.mark.parametrize("block_contents", ["empty", "transfer"])
def test_validation_state_system_address_unread(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    block_contents: str,
) -> None:
    """
    Leave out the SYSTEM_ADDRESS account proof when only system calls use it.

    The block's system calls use SYSTEM_ADDRESS as their origin without
    reading its account, so the witness must not prove it. This is the
    premise of the `system_address` cases of
    `test_validation_state_unchanged_account_read`.
    """
    # A funded SYSTEM_ADDRESS has its own leaf in the account trie.
    pre.fund_address(SYSTEM_ADDRESS, 1)

    txs: list[Transaction] = []
    post: dict[Address, Account] = {
        SYSTEM_ADDRESS: Account(balance=1, nonce=0),
    }
    if block_contents == "empty":
        pass
    elif block_contents == "transfer":
        sender = pre.fund_eoa()
        recipient = pre.fund_eoa(amount=1)
        txs.append(Transaction(sender=sender, to=recipient, value=1))
        post[sender] = Account(nonce=1)
        post[recipient] = Account(balance=2)
    else:
        raise ValueError(f"Unknown block contents: {block_contents}")

    full_alloc = merge_with_amsterdam_pre_alloc(pre)
    proof_nodes = collect_account_proof_nodes(full_alloc, [SYSTEM_ADDRESS])

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=txs,
                expected_execution_witness_state=(
                    ExecutionWitnessStateExpectation(
                        nodes_absent=[_leaf_node(proof_nodes)],
                    )
                ),
                expected_stateless_validation_success=True,
            )
        ],
        post=post,
    )


@pytest.mark.parametrize(
    "access",
    # `SSTORE(24, storage[24])` is not a case: a guest that reads slot 24 as
    # zero would charge it as setting a new slot, so its gas used would differ
    # from the block's and it would reject the block without the witness
    # check.
    ["sload_present", "sload_absent", "sstore_zero_to_absent"],
)
@pytest.mark.parametrize(
    "witness_complete",
    [
        pytest.param(True, id="complete_witness"),
        pytest.param(False, id="missing_proof_leaf"),
    ],
)
def test_validation_state_unchanged_storage_read(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    access: str,
    witness_complete: bool,
) -> None:
    """
    Require a slot's proof when the block reads it without a change.

    After such a read, a guest that treats a missing proof as an absent slot
    computes the same post-state root, so only the witness check can reject
    a block whose witness leaves the proof out.
    """
    # Slots 1 and 24 hash to keys starting with `b1`, and slot 14 to one
    # starting with `bb`. Below an extension on `b`, a branch sends both `b1`
    # keys to slot 24's leaf, so present slot 24 and absent slot 1 share one
    # proof, which ends in that leaf.
    storage = build_large_storage([14, 24])
    if access == "sload_present":
        slot = 24
        code = Op.POP(Op.SLOAD(slot))
    elif access == "sload_absent":
        slot = 1
        code = Op.POP(Op.SLOAD(slot))
    elif access == "sstore_zero_to_absent":
        slot = 1
        code = Op.SSTORE(slot, 0)
    else:
        raise ValueError(f"Unknown access: {access}")

    contract = pre.deploy_contract(code=code, storage=as_storage(storage))
    sender = pre.fund_eoa()
    proof_nodes = collect_storage_proof_nodes(storage, [slot])
    expectation = ExecutionWitnessStateExpectation(nodes_present=proof_nodes)
    if not witness_complete:
        expectation = expectation.modify(
            remove_state_node(_leaf_node(proof_nodes))
        )

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[Transaction(sender=sender, to=contract)],
                expected_execution_witness_state=expectation,
                expected_stateless_validation_success=witness_complete,
            )
        ],
        post={
            sender: Account(nonce=1),
            contract: Account(storage=storage),
        },
    )


@pytest.mark.pre_alloc_mutable
@pytest.mark.with_all_system_contract_request_types(
    selector=lambda cls: issubclass(cls, FeeSystemContractRequest)
)
@pytest.mark.parametrize(
    "missing_node",
    [
        pytest.param(None, id="complete_witness"),
        pytest.param("storage_root", id="missing_storage_root"),
        pytest.param("proof_leaf", id="missing_proof_leaf"),
    ],
)
def test_validation_state_unchanged_request_queue_read(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    fork: Fork,
    request_class: Type[FeeSystemContractRequest],
    missing_node: str | None,
) -> None:
    """
    Require the storage proof of an empty request queue's system call.

    With nothing queued, the end-of-block system call reads the excess,
    count, head and tail slots and writes back the same zeros. A guest that
    treats a missing proof as an absent slot computes the same post-state
    root, so only the witness check can reject a block whose witness leaves
    the proof out.
    """
    predeploy = request_class.system_contract_address
    genesis_account = Alloc.model_validate(fork.pre_allocation_blockchain())[
        predeploy
    ]
    assert genesis_account is not None
    # A drained queue resets its head and tail but keeps the slots of the
    # records it dequeued. One block's worth of them puts nodes below the
    # root on the paths of the slots the system call reads.
    storage = build_large_storage(
        request_class.record_slots(0, request_class.max_per_block)
    )
    pre[predeploy] = Account(
        nonce=genesis_account.nonce,
        code=genesis_account.code,
        storage=as_storage(storage),
    )

    queue_slots = [
        request_class.excess_slot,
        request_class.count_slot,
        request_class.queue_head_slot,
        request_class.queue_tail_slot,
    ]
    proof_nodes = collect_storage_proof_nodes(storage, queue_slots)
    expectation = ExecutionWitnessStateExpectation(nodes_present=proof_nodes)
    if missing_node is None:
        pass
    elif missing_node == "storage_root":
        expectation = expectation.modify(
            remove_state_node(storage_root_node(storage))
        )
    elif missing_node == "proof_leaf":
        # The block reads only the queue slots, so each leaf in their proof
        # ends one of their absence proofs.
        expectation = expectation.modify(
            remove_state_node(_required_node(_leaf_nodes(proof_nodes)))
        )
    else:
        raise ValueError(f"Unknown missing node: {missing_node}")

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                expected_execution_witness_state=expectation,
                expected_stateless_validation_success=missing_node is None,
            )
        ],
        post={predeploy: Account(storage=storage)},
    )
