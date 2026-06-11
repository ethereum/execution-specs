"""Tests for [EIP-8246: Remove SELFDESTRUCT balance burn](https://eips.ethereum.org/EIPS/eip-8246)."""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Block,
    BlockchainTestFiller,
    Bytecode,
    Op,
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
def test_selfdestruct_preserves_balance(
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
        sender=sender,
        to=entry_contract,
        value=total_balance,
        gas_limit=5_000_000,
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
            Op.BALANCE(victim),
        )
        + Op.SSTORE(
            probe_storage.store_next(keccak256(b"") if victim_alive else 0),
            Op.EXTCODEHASH(victim),
        )
        + Op.SSTORE(
            probe_storage.store_next(0),
            Op.EXTCODESIZE(victim),
        )
        + Op.EXTCODECOPY(victim, 0, 0, len(selfdestruct_initcode))
        + Op.SSTORE(
            probe_storage.store_next(
                keccak256(b"\x00" * len(selfdestruct_initcode))
            ),
            Op.SHA3(0, len(selfdestruct_initcode)),
        )
        + Op.STOP
    )

    probe_contract = pre.deploy_contract(
        code=probe_code, storage=probe_storage.canary()
    )

    probe_tx = Transaction(
        sender=sender,
        to=probe_contract,
        gas_limit=200_000,
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
