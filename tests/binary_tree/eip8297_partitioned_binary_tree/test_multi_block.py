"""
Multi-block chain tests for the EIP-8297 partitioned binary tree:
storage evolving across several blocks, account creation and
destruction spread across blocks, withdrawals, empty and
transaction-less blocks, and a block carrying a wrong `state_root`
header field.

The wrong-root case only records an expectation for a future
consumer of these fixtures; see its own docstring for why `fill`
does not verify it today.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Block,
    BlockchainTestFiller,
    BlockException,
    Bytecode,
    Hash,
    Header,
    Initcode,
    Op,
    Transaction,
    Withdrawal,
)

from .helpers import FACTORY_CANARY_SLOT, create_contract_via_factory
from .spec import ref_spec_8297

REFERENCE_SPEC_GIT_PATH = ref_spec_8297.git_path
REFERENCE_SPEC_VERSION = ref_spec_8297.version

pytestmark = pytest.mark.valid_from("BinaryTree")

ONE_GWEI = 10**9

# SSTOREs calldata[32:64] into the slot given by calldata[0:32].
#
# Unlike `sstore_from_calldata_contract` (fixed slot, calldata-driven
# value only), this contract's SLOT is also calldata-driven, so one
# deployed instance can be driven to write different slots across
# several calls/blocks.
_DISPATCHER_CODE: Bytecode = (
    Op.SSTORE(Op.CALLDATALOAD(0), Op.CALLDATALOAD(32)) + Op.STOP
)


def _write_calldata(slot: int, value: int) -> bytes:
    """Pack (slot, value) as the two words `_DISPATCHER_CODE` expects."""
    return slot.to_bytes(32, "big") + value.to_bytes(32, "big")


def test_contract_evolves_across_four_blocks(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
) -> None:
    """
    Verify one contract's storage evolves correctly across a 4-block
    chain: block 1 creates it and writes a slot, block 2 overwrites
    that slot, block 3 zeroes it, and block 4 writes a brand-new HIGH
    slot (> 255, its own overflow storage group). The final post state
    reflects only the last write to each slot.

    `slot_a`'s omission from `post` below (zeroed in block 3) relies
    on `src/ethereum/state_pbt.py`'s zero-write-deletes-the-slot
    behavior, which is not EIP-8297-conformant -- see
    `test_storage_ops.py`'s module docstring for the disclosure.
    """
    slot_a, slot_b = 9, 400

    deploy_code = _DISPATCHER_CODE
    initcode = Initcode(
        deploy_code=deploy_code, initcode_prefix=Op.SSTORE(slot_a, 1)
    )
    factory, contract = create_contract_via_factory(pre, initcode)

    sender = pre.fund_eoa()

    blocks = [
        Block(txs=[Transaction(sender=sender, to=factory)]),
        Block(
            txs=[
                Transaction(
                    sender=sender,
                    to=contract,
                    data=_write_calldata(slot_a, 2),
                )
            ]
        ),
        Block(
            txs=[
                Transaction(
                    sender=sender,
                    to=contract,
                    data=_write_calldata(slot_a, 0),
                )
            ]
        ),
        Block(
            txs=[
                Transaction(
                    sender=sender,
                    to=contract,
                    data=_write_calldata(slot_b, 0xFEED),
                )
            ]
        ),
    ]

    blockchain_test(
        pre=pre,
        blocks=blocks,
        post={
            contract: Account(code=deploy_code, storage={slot_b: 0xFEED}),
            factory: Account(nonce=2, storage={FACTORY_CANARY_SLOT: 1}),
        },
    )


def test_account_created_then_aged_selfdestruct_next_block(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
) -> None:
    """
    Verify a contract created in block 1 and self-destructed in block
    2 is "aged" under post-6780 semantics: the SELFDESTRUCT sweeps its
    balance to the beneficiary but the account itself, its code, and
    its storage all survive into the final post state.
    """
    slot, value = 3, 0xBEEF
    endowment = 1_000
    beneficiary = pre.fund_eoa(amount=0)

    victim_code = Op.SELFDESTRUCT(beneficiary)
    initcode = Initcode(
        deploy_code=victim_code, initcode_prefix=Op.SSTORE(slot, value)
    )
    factory, victim = create_contract_via_factory(pre, initcode)
    pre.fund_address(victim, endowment)

    sender = pre.fund_eoa()

    blocks = [
        Block(txs=[Transaction(sender=sender, to=factory)]),
        Block(txs=[Transaction(sender=sender, to=victim)]),
    ]

    blockchain_test(
        pre=pre,
        blocks=blocks,
        post={
            victim: Account(
                balance=0, code=victim_code, storage={slot: value}
            ),
            beneficiary: Account(balance=endowment),
            factory: Account(nonce=2, storage={FACTORY_CANARY_SLOT: 1}),
        },
    )


def test_withdrawals_credit_new_and_existing_accounts_across_blocks(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
) -> None:
    """
    Verify EIP-4895 withdrawals across two blocks correctly credit
    both a pre-existing account and a brand-new, never-seen address:
    the existing account's balance increases exactly, and the new
    address materializes holding exactly the withdrawn amount.
    """
    existing_starting_balance = 1_000
    existing = pre.fund_eoa(amount=existing_starting_balance)
    new_address = pre.nonexistent_account()

    existing_withdrawal_amount = 5
    new_withdrawal_amount = 7

    blocks = [
        Block(
            withdrawals=[
                Withdrawal(
                    index=0,
                    validator_index=0,
                    address=existing,
                    amount=existing_withdrawal_amount,
                )
            ]
        ),
        Block(
            withdrawals=[
                Withdrawal(
                    index=0,
                    validator_index=0,
                    address=new_address,
                    amount=new_withdrawal_amount,
                )
            ]
        ),
    ]

    blockchain_test(
        pre=pre,
        blocks=blocks,
        post={
            existing: Account(
                balance=existing_starting_balance
                + existing_withdrawal_amount * ONE_GWEI
            ),
            new_address: Account(
                balance=new_withdrawal_amount * ONE_GWEI,
                nonce=0,
                code=b"",
            ),
        },
    )


def test_state_survives_empty_blocks_interleaved(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
) -> None:
    """
    Verify storage written in one block survives untouched across
    empty (no-transaction) blocks interleaved before the next write.
    """
    slot_x, slot_y = 2, 9
    value_x, value_y = 0x1111, 0x2222

    contract = pre.deploy_contract(code=_DISPATCHER_CODE)
    sender = pre.fund_eoa()

    blocks = [
        Block(
            txs=[
                Transaction(
                    sender=sender,
                    to=contract,
                    data=_write_calldata(slot_x, value_x),
                )
            ]
        ),
        Block(txs=[]),
        Block(txs=[]),
        Block(
            txs=[
                Transaction(
                    sender=sender,
                    to=contract,
                    data=_write_calldata(slot_y, value_y),
                )
            ]
        ),
    ]

    blockchain_test(
        pre=pre,
        blocks=blocks,
        post={contract: Account(storage={slot_x: value_x, slot_y: value_y})},
    )


def test_chain_with_no_transactions_at_all(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
) -> None:
    """
    Verify a chain of several blocks carrying NO transactions at all
    (only the automatic per-block system-contract activity: EIP-4788
    and EIP-2935 pre-execution calls, and post-execution calls
    including EIP-7002's withdrawal-request dequeue) fills and
    produces a consistent binary-tree-committed chain.
    """
    blocks = [Block() for _ in range(4)]

    blockchain_test(pre=pre, blocks=blocks, post={})


@pytest.mark.exception_test
def test_wrong_state_root_expectation_is_recorded_for_consumers(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
) -> None:
    """
    Record the expectation that a block whose header carries a WRONG
    `state_root` is rejected -- this does not verify it.

    The wrong root is injected via `rlp_modifier`, and
    `execution_testing`'s fill-time `verify_block_exception` only
    runs when `block.rlp_modifier is None`
    (`specs/blockchain.py:1073-1084`), so `fill` skips exactly the
    check this test's name suggests it performs. No client consumes
    `BinaryTree` fixtures either, so nothing downstream checks it
    today. `exception` is also an any-of match: a future consumer
    could satisfy it by rejecting on the header-hash mismatch alone,
    without ever comparing state roots. A direct, checked guarantee
    that the fork raises on a mismatched root now exists at
    `tests/binary_trie/test_block_execution.py::
    test_execute_block_rejects_a_tampered_state_root`, which drives
    `execute_block` through a real (if minimal) block rather than via
    a fixture `fill` cannot verify.
    """
    sender = pre.fund_eoa()
    recipient = pre.fund_eoa(amount=0)

    tx = Transaction(sender=sender, to=recipient, value=1)

    block = Block(
        txs=[tx],
        rlp_modifier=Header(state_root=Hash(1)),
        exception=[
            BlockException.INVALID_STATE_ROOT,
            BlockException.INVALID_BLOCK_HASH,
        ],
    )

    blockchain_test(pre=pre, post={}, blocks=[block])
