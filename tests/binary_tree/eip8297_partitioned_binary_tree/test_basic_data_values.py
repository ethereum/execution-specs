"""
BASIC_DATA field-range tests for the EIP-8297 partitioned binary tree.

The BASIC_DATA leaf packs version, code_size, nonce and balance into
one 32-byte value, but account-level post-state verification cannot
observe that leaf directly. These tests instead exercise its field
ranges through execution and opcode reads: a maxed-out 16-byte
balance transacting successfully, a near-maximum 8-byte nonce
incrementing correctly, and the balance/code_size fields read back
through their own opcodes agreeing with committed state. The packed
encoding's byte layout itself is pinned directly by
`tests/binary_trie/test_embedding.py::test_encode_basic_data_layout`.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Fork,
    Initcode,
    Op,
    RecipientType,
    StateTestFiller,
    Transaction,
)

from .helpers import create_contract_via_factory
from .spec import ref_spec_8297

REFERENCE_SPEC_GIT_PATH = ref_spec_8297.git_path
REFERENCE_SPEC_VERSION = ref_spec_8297.version

pytestmark = pytest.mark.valid_from("BinaryTree")


def test_account_at_max_balance_field_transacts(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Verify an account funded at exactly `2**128 - 1` wei -- the largest
    value the BASIC_DATA leaf's 16-byte balance field can hold -- sends
    a value-transferring transaction successfully, with exact post
    balances on both ends.

    `2**128` and above overflow the field with no protocol-level cap;
    that gap is pinned as a unit test, not exercised here.
    """
    max_balance = 2**128 - 1
    value = 12345
    sender = pre.fund_eoa(amount=max_balance)
    recipient = pre.fund_eoa(amount=1)

    # An already-funded EOA recipient carries no top-frame NEW_ACCOUNT
    # charge, so the total cost below is exact and fork-generic.
    intrinsic_gas = fork.transaction_intrinsic_cost_calculator()(
        sends_value=True,
        recipient_type=RecipientType.EOA,
        return_cost_deducted_prior_execution=True,
    )
    top_frame_gas = fork.transaction_top_frame_gas_calculator()(
        sends_value=True,
        recipient_type=RecipientType.EOA,
    )
    top_frame_state_gas = fork.transaction_top_frame_state_gas(
        sends_value=True,
        recipient_type=RecipientType.EOA,
    )
    total_gas_cost = intrinsic_gas + top_frame_gas + top_frame_state_gas

    gas_price = 10**9
    tx = Transaction(
        sender=sender,
        to=recipient,
        value=value,
        gas_limit=total_gas_cost,
        gas_price=gas_price,
    )

    post = {
        sender: Account(
            balance=max_balance - value - total_gas_cost * gas_price
        ),
        recipient: Account(balance=1 + value),
    }
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.pre_alloc_mutable
def test_sender_high_nonce_increments_correctly(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Verify a sender parked one below the maximum nonce (`2**64 - 2`,
    the largest value from which the BASIC_DATA leaf's 8-byte nonce
    field can increment without overflowing) transacts successfully
    and increments to exactly `2**64 - 1`.
    """
    max_nonce = 2**64 - 1
    starting_nonce = max_nonce - 1
    sender = pre.fund_eoa(nonce=starting_nonce)
    contract = pre.deploy_contract(code=Op.SSTORE(0, 1) + Op.STOP)

    tx = Transaction(sender=sender, to=contract, nonce=starting_nonce)

    post = {
        sender: Account(nonce=max_nonce),
        contract: Account(storage={0: 1}),
    }
    state_test(pre=pre, post=post, tx=tx)


def test_balance_field_round_trip_after_value_transfer(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Verify `SELFBALANCE` and `BALANCE(ADDRESS)`, read from inside a
    contract in the same call that transfers it value, both match the
    contract's exact post-state balance -- the value credit lands
    before the callee's code starts, and both opcodes' readings agree
    with the account's committed balance.
    """
    starting_balance = 10**17
    value = 10**18
    self_slot, ext_slot = 0, 1

    contract = pre.deploy_contract(
        code=Op.SSTORE(self_slot, Op.SELFBALANCE)
        + Op.SSTORE(ext_slot, Op.BALANCE(Op.ADDRESS))
        + Op.STOP,
        balance=starting_balance,
    )

    tx = Transaction(sender=pre.fund_eoa(), to=contract, value=value)

    final_balance = starting_balance + value
    post = {
        contract: Account(
            balance=final_balance,
            storage={self_slot: final_balance, ext_slot: final_balance},
        ),
    }
    state_test(pre=pre, post=post, tx=tx)


def test_code_size_field_round_trip_after_create(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Verify `EXTCODESIZE(ADDRESS)` and `CODESIZE`, both read from
    inside a freshly `CREATE`d contract's own frame, agree with each
    other and with the deployed code's actual length -- what the
    BASIC_DATA leaf encodes at root-computation time, though neither
    opcode reads that leaf directly.
    """
    codesize_slot, extcodesize_slot = 0, 1
    deploy_code = (
        Op.SSTORE(codesize_slot, Op.CODESIZE)
        + Op.SSTORE(extcodesize_slot, Op.EXTCODESIZE(Op.ADDRESS))
        + Op.STOP
    )
    initcode = Initcode(deploy_code=deploy_code)

    factory, created = create_contract_via_factory(pre, initcode)
    caller = pre.deploy_contract(
        code=Op.POP(Op.CALL(address=factory))
        + Op.POP(Op.CALL(address=created))
        + Op.STOP
    )

    tx = Transaction(sender=pre.fund_eoa(), to=caller)

    post = {
        created: Account(
            storage={
                codesize_slot: len(deploy_code),
                extcodesize_slot: len(deploy_code),
            }
        ),
    }
    state_test(pre=pre, post=post, tx=tx)
