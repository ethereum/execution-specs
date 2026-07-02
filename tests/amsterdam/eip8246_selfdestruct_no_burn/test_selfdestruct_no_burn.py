"""Tests for [EIP-8246: Remove SELFDESTRUCT balance burn](https://eips.ethereum.org/EIPS/eip-8246)."""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Block,
    BlockchainTestFiller,
    Bytecode,
    Hash,
    Initcode,
    Op,
    StateTestFiller,
    Storage,
    Transaction,
    compute_create_address,
    keccak256,
)

from .spec import ref_spec_8246

REFERENCE_SPEC_GIT_PATH = ref_spec_8246.git_path
REFERENCE_SPEC_VERSION = ref_spec_8246.version

pytestmark = pytest.mark.valid_from("EIP8246")


@pytest.mark.parametrize("initial_balance", [0, 1])
@pytest.mark.parametrize("create_opcode", [Op.CREATE, Op.CREATE2])
@pytest.mark.parametrize("post_send_count", [0, 1, 3])
@pytest.mark.parametrize(
    "post_send_opcode", [Op.CALL, Op.CALLCODE, Op.SELFDESTRUCT]
)
@pytest.mark.parametrize(
    "initial_storage",
    [
        pytest.param(False, id="no_storage"),
        pytest.param(True, id="with_storage"),
    ],
)
@pytest.mark.parametrize(
    "transfer_target, transfer_drains_victim",
    [
        pytest.param(Op.ADDRESS, False, id="self"),
        pytest.param(0x01, True, id="precompile"),
        pytest.param(
            Address(keccak256(b"eip-8246-eoa-target")[-20:]),
            True,
            id="eoa",
        ),
    ],
)
@pytest.mark.parametrize(
    "exit_op, execution_success",
    [
        pytest.param(Op.STOP, True, id="success"),
        pytest.param(Op.REVERT(0, 0), False, id="revert"),
        pytest.param(Op.MSTORE(2**32, 0), False, id="oog"),
    ],
)
def test_selfdestructing_initcode_preserves_balance(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    initial_balance: int,
    post_send_count: int,
    create_opcode: Op,
    post_send_opcode: Op,
    initial_storage: bool,
    transfer_target: Op,
    transfer_drains_victim: bool,
    exit_op: Op,
    execution_success: bool,
) -> None:
    """
    Same-tx SELFDESTRUCT preserves the victim's balance per EIP-8246.

    Test flow:
      selfdestruct_tx
        tx.to = entry_contract
          └─ CALL selfdestruct_contract_factory
              └─ initcode runs:
                  [optional] SSTORE(slot, value)
                  SELFDESTRUCT(transfer_target)   # registers victim
              └─ selfdestruct_contract_factory exits via STOP | REVERT | OOG
          └─ N * post-send to victim (CALL | CALLCODE | donor.SELFDESTRUCT)

        tx finalize
         - victim balance-only per EIP-8246,
         - or NONEXISTENT if EIP-161 cleans up a zero-balance account

      probe_tx
        tx.to = probe_contract
          └─ STORAGE [0] = BALANCE(victim)
             STORAGE [1] = EXTCODEHASH(victim)
             STORAGE [2] = EXTCODESIZE(victim)
             STORAGE [3] = SHA3(EXTCODECOPY(victim, 0, 0, size))
    """
    # Selfdestruct target contract template.
    # Optionally initializes storage to test clearing.
    storage_init = Op.SSTORE(0, 1) if initial_storage else Bytecode()
    selfdestruct_initcode = storage_init + Op.SELFDESTRUCT(transfer_target)

    selfdestruct_template = pre.deploy_contract(code=selfdestruct_initcode)

    # Build selfdestruct target contract via CREATE/CREATE2
    salt = 0
    if create_opcode == Op.CREATE2:
        create_call = create_opcode(
            value=initial_balance,
            size=len(selfdestruct_initcode),
            salt=salt,
        )
    else:
        create_call = create_opcode(
            value=initial_balance,
            size=len(selfdestruct_initcode),
        )

    # Selfdestruct target contract factory
    # Exits via STOP/REVERT/OOG for different scenario
    selfdestruct_contract_factory = pre.deploy_contract(
        code=Op.EXTCODECOPY(
            address=selfdestruct_template, size=len(selfdestruct_initcode)
        )
        + Op.POP(create_call)
        + exit_op
    )

    victim = compute_create_address(
        address=selfdestruct_contract_factory,
        opcode=create_opcode,
        nonce=1,
        salt=salt,
        initcode=selfdestruct_initcode,
    )

    # Post value sending to the victim
    # Ensure the ether transfer is not burned after eip-8246.
    post_send_value = 1
    if post_send_opcode == Op.SELFDESTRUCT:
        donor = pre.deploy_contract(code=Op.SELFDESTRUCT(victim))
        post_send = Op.POP(
            Op.CALL(gas=Op.GAS, address=donor, value=post_send_value)
        )
    else:
        post_send = Op.POP(
            post_send_opcode(gas=Op.GAS, address=victim, value=post_send_value)
        )

    entry_contract = pre.deploy_contract(
        code=Op.POP(
            Op.CALL(
                gas=Op.GAS,
                address=selfdestruct_contract_factory,
                value=initial_balance,
            )
        )
        + post_send * post_send_count
    )

    total_balance = initial_balance + post_send_count * post_send_value

    sender = pre.fund_eoa()
    selfdestruct_tx = Transaction(
        sender=sender, to=entry_contract, value=total_balance
    )

    # Balance verification
    #   retained:
    #       selfdestruct-to-self retains balance
    #       selfdestruct-to-others drains balance if not revert / OOG
    #   delivered: post-sends count except for CALLCODE
    retained = 0 if transfer_drains_victim else initial_balance
    delivered = (
        0
        if post_send_opcode == Op.CALLCODE
        else post_send_count * post_send_value
    )

    expected_balance = retained + delivered if execution_success else delivered
    victim_alive = expected_balance > 0

    probe_storage = Storage()
    probe_code = (
        Op.SSTORE(
            probe_storage.store_next(expected_balance),
            Op.BALANCE(Op.CALLDATALOAD(0)),
        )
        + Op.SSTORE(
            probe_storage.store_next(keccak256(b"") if victim_alive else 0),
            Op.EXTCODEHASH(Op.CALLDATALOAD(0)),
        )
        + Op.SSTORE(
            probe_storage.store_next(0),
            Op.EXTCODESIZE(Op.CALLDATALOAD(0)),
        )
        + Op.EXTCODECOPY(
            Op.CALLDATALOAD(0), 0, 0, Op.EXTCODESIZE(Op.CALLDATALOAD(0))
        )
        + Op.SSTORE(
            probe_storage.store_next(keccak256(b"")),
            Op.SHA3(0, Op.EXTCODESIZE(Op.CALLDATALOAD(0))),
        )
        + Op.STOP
    )

    probe_contract = pre.deploy_contract(
        code=probe_code, storage=probe_storage.canary()
    )

    probe_tx = Transaction(
        sender=sender, to=probe_contract, data=Hash(victim, left_padding=True)
    )

    blockchain_test(
        pre=pre,
        post={
            victim: (
                Account.NONEXISTENT
                if not victim_alive
                else Account(
                    balance=expected_balance, nonce=0, code=b"", storage={}
                )
            ),
            probe_contract: Account(storage=probe_storage),
        },
        blocks=[Block(txs=[selfdestruct_tx, probe_tx])],
    )


def create_and_call_contract(
    pre: Alloc, runtime_code: Bytecode, value: int
) -> tuple[Address, Address]:
    """
    Deploy a factory that CREATEs a `runtime_code` contract funded with
    `value` and immediately calls it, so the contract is created and
    self-destructed in one transaction. Return (factory, created).
    """
    initcode = Initcode(deploy_code=runtime_code)
    holder = pre.deploy_contract(code=initcode)
    factory = pre.deploy_contract(
        code=Op.EXTCODECOPY(holder, 0, 0, len(initcode))
        + Op.CALL(
            gas=Op.GAS,
            address=Op.CREATE(value=value, offset=0, size=len(initcode)),
        )
    )
    return factory, compute_create_address(address=factory, nonce=1)


@pytest.mark.parametrize(
    "initial_balance",
    [pytest.param(1, id="kept"), pytest.param(0, id="removed")],
)
def test_deployed_contract_selfdestruct_clears_code(
    state_test: StateTestFiller,
    pre: Alloc,
    initial_balance: int,
) -> None:
    """
    Same-tx SELFDESTRUCT of a deployed contract clears its code.

    The created contract carries runtime code (unlike the
    initcode-selfdestruct case) and self-destructs to itself, so EIP-8246
    keeps its balance. A nonzero-balance account survives as a
    balance-only account with empty code; a zero-balance account is
    removed by EIP-161.
    """
    factory, created = create_and_call_contract(
        pre, Op.SELFDESTRUCT(Op.ADDRESS), initial_balance
    )
    tx = Transaction(sender=pre.fund_eoa(), to=factory, value=initial_balance)
    post = {
        created: (
            Account(balance=initial_balance, nonce=0, code=b"", storage={})
            if initial_balance
            else Account.NONEXISTENT
        )
    }
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.parametrize(
    "self_beneficiary",
    [
        pytest.param(False, id="drained_removed"),
        pytest.param(True, id="self_kept"),
    ],
)
def test_selfdestruct_removes_prefunded_create_address(
    state_test: StateTestFiller,
    pre: Alloc,
    self_beneficiary: bool,
) -> None:
    """
    Same-tx SELFDESTRUCT clears a pre-funded create address from state.

    The contract is created at an address already funded in genesis, so
    the delete path must remove that pre-existing entry, not merely skip
    it. Draining to another beneficiary leaves balance 0 and the address
    is removed; self-destructing to self keeps the combined balance as a
    balance-only account.
    """
    prefund = 100
    endowment = 1
    total = prefund + endowment
    beneficiary = Address(keccak256(b"eip-8246-t4-beneficiary")[-20:])

    target = Op.ADDRESS if self_beneficiary else beneficiary
    factory, created = create_and_call_contract(
        pre, Op.SELFDESTRUCT(target), endowment
    )
    pre.fund_address(created, prefund)

    tx = Transaction(sender=pre.fund_eoa(), to=factory, value=endowment)
    post = {
        created: (
            Account(balance=total, nonce=0, code=b"", storage={})
            if self_beneficiary
            else Account.NONEXISTENT
        ),
    }
    if not self_beneficiary:
        post[beneficiary] = Account(balance=total)
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.parametrize(
    "value",
    [pytest.param(1, id="kept"), pytest.param(0, id="removed")],
)
def test_create_transaction_initcode_selfdestruct(
    state_test: StateTestFiller,
    pre: Alloc,
    value: int,
) -> None:
    """
    Depth-0 creation-tx initcode SELFDESTRUCT keeps balance per EIP-8246.

    A creation transaction (``tx.to is None``) whose initcode
    self-destructs to itself exercises the depth-0 create path. A nonzero
    endowment is kept as a balance-only account; a zero endowment is
    removed.
    """
    sender = pre.fund_eoa()
    created = compute_create_address(address=sender, nonce=sender.nonce)

    tx = Transaction(
        sender=sender,
        to=None,
        value=value,
        data=Op.SELFDESTRUCT(Op.ADDRESS),
    )
    post = {
        created: (
            Account(balance=value, nonce=0, code=b"", storage={})
            if value
            else Account.NONEXISTENT
        )
    }
    state_test(pre=pre, post=post, tx=tx)
