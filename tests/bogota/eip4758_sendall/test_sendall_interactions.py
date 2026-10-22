"""
Tests for how [EIP-4758: Deactivate SELFDESTRUCT](https://eips.ethereum.org/EIPS/eip-4758)
composes with the features it inherits from Amsterdam.

Without the EIP-6780 same-transaction deletion there is no EIP-8246
balance-preserving clear either, so an account created and swept in one
transaction keeps every write it made. These tests pin the EIP-7928 block
access list entries, the EIP-7708 transfer logs, the gas and refund
accounting, and rollback of such an account.
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    AuthorizationTuple,
    BalAccountExpectation,
    BalBalanceChange,
    BalCodeChange,
    BalNonceChange,
    BalStorageChange,
    BalStorageSlot,
    Block,
    BlockAccessListExpectation,
    BlockchainTestFiller,
    Bytecode,
    Fork,
    Initcode,
    Op,
    StateTestFiller,
    Storage,
    Transaction,
    TransactionReceipt,
    compute_create_address,
    keccak256,
)
from execution_testing import (
    Macros as Om,
)

from tests.amsterdam.eip7708_eth_transfer_logs.spec import transfer_log
from tests.prague.eip7702_set_code_tx.spec import Spec as Spec7702

from .spec import ref_spec_4758

REFERENCE_SPEC_GIT_PATH = ref_spec_4758.git_path
REFERENCE_SPEC_VERSION = ref_spec_4758.version

pytestmark = pytest.mark.valid_from("EIP4758")

VICTIM_BALANCE = 0x1234
REFILL = 0x77
CANARY = 0xC0DE
SLOT = 0x07
SALT = 0


def create_call(create_opcode: Op, initcode: Bytecode, value: int) -> Bytecode:
    """Return a CREATE or CREATE2 of `initcode` stored at memory 0."""
    if create_opcode == Op.CREATE2:
        return Op.CREATE2(value=value, size=len(initcode), salt=SALT)
    return Op.CREATE(value=value, size=len(initcode))


@pytest.mark.parametrize("create_opcode", [Op.CREATE, Op.CREATE2])
@pytest.mark.parametrize("sweep_in", ["runtime", "initcode"])
def test_bal_created_account_keeps_writes(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    create_opcode: Op,
    sweep_in: str,
) -> None:
    """
    Record the writes of an account created and swept in one transaction.

    Before EIP-4758 the account was deleted at the end of the transaction,
    so its storage writes were demoted to reads and its nonce and code
    changes dropped. Now the nonce, code and storage writes all persist and
    appear in the block access list; the balance it was funded with and
    then swept nets to zero within the transaction, so no balance change
    is recorded for it.
    """
    beneficiary = pre.nonexistent_account()
    sweep = Op.SSTORE(SLOT, CANARY) + Op.SELFDESTRUCT(beneficiary)
    if sweep_in == "runtime":
        initcode: Bytecode = Initcode(deploy_code=sweep)
        deployed_code = bytes(sweep)
    else:
        initcode = sweep
        deployed_code = b""

    factory_code = Om.MSTORE(initcode, 0) + Op.SSTORE(
        0, create_call(create_opcode, initcode, VICTIM_BALANCE)
    )
    if sweep_in == "runtime":
        factory_code += Op.CALL(address=Op.SLOAD(0))
    factory = pre.deploy_contract(code=factory_code, balance=VICTIM_BALANCE)
    victim = compute_create_address(
        address=factory,
        nonce=1,
        salt=SALT,
        initcode=initcode,
        opcode=create_opcode,
    )

    block = Block(
        txs=[Transaction(sender=pre.fund_eoa(), to=factory)],
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                victim: BalAccountExpectation(
                    nonce_changes=[
                        BalNonceChange(block_access_index=1, post_nonce=1)
                    ],
                    code_changes=(
                        [
                            BalCodeChange(
                                block_access_index=1, new_code=deployed_code
                            )
                        ]
                        if deployed_code
                        else []
                    ),
                    storage_changes=[
                        BalStorageSlot(
                            slot=SLOT,
                            slot_changes=[
                                BalStorageChange(
                                    block_access_index=1, post_value=CANARY
                                )
                            ],
                        )
                    ],
                    storage_reads=[],
                    balance_changes=[],
                ),
                beneficiary: BalAccountExpectation(
                    balance_changes=[
                        BalBalanceChange(
                            block_access_index=1, post_balance=VICTIM_BALANCE
                        )
                    ],
                ),
            }
        ),
    )

    blockchain_test(
        pre=pre,
        blocks=[block],
        post={
            victim: Account(
                nonce=1,
                code=deployed_code,
                balance=0,
                storage={SLOT: CANARY},
            ),
            beneficiary: Account(balance=VICTIM_BALANCE),
        },
    )


def test_swept_account_refunded_keeps_code(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Fund an account after it swept itself in its creating transaction.

    Under EIP-8246 the account would end the transaction cleared down to
    its balance. Now it keeps its code, nonce and storage next to the new
    balance, which arrives from a second SENDALL so that the victim's own
    code is not run again.
    """
    beneficiary = pre.fund_eoa(amount=1)
    victim_code = Op.SSTORE(0, CANARY) + Op.SELFDESTRUCT(beneficiary)
    initcode = Initcode(deploy_code=victim_code)
    factory = pre.deploy_contract(
        code=Om.MSTORE(initcode, 0)
        + Op.SSTORE(0, Op.CREATE(value=VICTIM_BALANCE, size=len(initcode))),
        balance=VICTIM_BALANCE,
    )
    victim = compute_create_address(address=factory, nonce=1)
    funder = pre.deploy_contract(code=Op.SELFDESTRUCT(victim), balance=REFILL)

    entry_storage = Storage()
    entry = pre.deploy_contract(
        code=Op.SSTORE(entry_storage.store_next(1), Op.CALL(address=factory))
        + Op.SSTORE(entry_storage.store_next(1), Op.CALL(address=victim))
        + Op.SSTORE(entry_storage.store_next(1), Op.CALL(address=funder)),
        storage=entry_storage.canary(),
    )

    state_test(
        pre=pre,
        post={
            entry: Account(storage=entry_storage),
            victim: Account(
                nonce=1,
                code=victim_code,
                balance=REFILL,
                storage={0: CANARY},
            ),
            funder: Account(balance=0, code=Op.SELFDESTRUCT(victim)),
            beneficiary: Account(balance=1 + VICTIM_BALANCE),
        },
        tx=Transaction(sender=pre.fund_eoa(), to=entry),
    )


@pytest.mark.parametrize(
    "beneficiary_kind,value",
    [
        pytest.param("other", VICTIM_BALANCE, id="other"),
        pytest.param("self", VICTIM_BALANCE, id="self"),
        pytest.param("other", 0, id="other_zero_balance"),
    ],
)
@pytest.mark.parametrize("sweep_in", ["runtime", "initcode"])
def test_created_account_transfer_logs(
    state_test: StateTestFiller,
    pre: Alloc,
    beneficiary_kind: str,
    value: int,
    sweep_in: str,
) -> None:
    """
    Emit EIP-7708 transfer logs for a sweep by a freshly created account.

    The funded CREATE logs the transfer into the new account, and the
    sweep logs the transfer out of it. A sweep to itself or of a zero
    balance logs nothing.
    """
    beneficiary = pre.fund_eoa(amount=1)
    target: Address | Op = (
        beneficiary if beneficiary_kind == "other" else Op.ADDRESS
    )
    sweep = Op.SELFDESTRUCT(target)
    if sweep_in == "runtime":
        initcode: Bytecode = Initcode(deploy_code=sweep)
        deployed_code = bytes(sweep)
    else:
        initcode = sweep
        deployed_code = b""

    factory_code = Om.MSTORE(initcode, 0) + Op.SSTORE(
        0, Op.CREATE(value=value, size=len(initcode))
    )
    if sweep_in == "runtime":
        factory_code += Op.CALL(address=Op.SLOAD(0))
    factory = pre.deploy_contract(code=factory_code, balance=value)
    victim = compute_create_address(address=factory, nonce=1)

    swept = beneficiary_kind == "other"
    logs = []
    if value > 0:
        logs.append(transfer_log(factory, victim, value))
        if swept:
            logs.append(transfer_log(victim, beneficiary, value))

    state_test(
        pre=pre,
        post={
            victim: Account(
                nonce=1,
                code=deployed_code,
                balance=0 if swept else value,
            ),
            beneficiary: Account(balance=1 + (value if swept else 0)),
        },
        tx=Transaction(
            sender=pre.fund_eoa(),
            to=factory,
            expected_receipt=TransactionReceipt(logs=logs),
        ),
    )


@pytest.mark.parametrize("beneficiary_kind", ["other", "self"])
def test_create_transaction_initcode_sendall(
    state_test: StateTestFiller,
    pre: Alloc,
    beneficiary_kind: str,
) -> None:
    """
    SENDALL in the initcode of a contract-creation transaction.

    The created account persists with nonce 1, no code and its initcode's
    storage write; the transaction value is swept to the beneficiary, or
    stays put when the account sweeps itself.
    """
    beneficiary = pre.fund_eoa(amount=1)
    target: Address | Op = (
        beneficiary if beneficiary_kind == "other" else Op.ADDRESS
    )
    sender = pre.fund_eoa()
    initcode = Op.SSTORE(0, CANARY) + Op.SELFDESTRUCT(target)
    created = compute_create_address(address=sender, nonce=0)

    swept = beneficiary_kind == "other"
    state_test(
        pre=pre,
        post={
            created: Account(
                nonce=1,
                code=b"",
                balance=0 if swept else VICTIM_BALANCE,
                storage={0: CANARY},
            ),
            beneficiary: Account(balance=1 + (VICTIM_BALANCE if swept else 0)),
        },
        tx=Transaction(
            sender=sender, to=None, data=initcode, value=VICTIM_BALANCE
        ),
    )


def test_swept_account_code_visible_next_transaction(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
) -> None:
    """
    Read a swept account from the next transaction of the block.

    The account created and swept in the first transaction still exists in
    the second: EXTCODEHASH and EXTCODESIZE see its code, and its balance
    is zero.
    """
    beneficiary = pre.fund_eoa(amount=1)
    victim_code = Op.SELFDESTRUCT(beneficiary)
    initcode = Initcode(deploy_code=victim_code)
    factory = pre.deploy_contract(
        code=Om.MSTORE(initcode, 0)
        + Op.CALL(address=Op.CREATE(value=VICTIM_BALANCE, size=len(initcode))),
        balance=VICTIM_BALANCE,
    )
    victim = compute_create_address(address=factory, nonce=1)

    probe_storage = Storage()
    probe = pre.deploy_contract(
        code=Op.SSTORE(
            probe_storage.store_next(keccak256(bytes(victim_code))),
            Op.EXTCODEHASH(victim),
        )
        + Op.SSTORE(
            probe_storage.store_next(len(victim_code)),
            Op.EXTCODESIZE(victim),
        )
        + Op.SSTORE(probe_storage.store_next(0), Op.BALANCE(victim)),
        storage=probe_storage.canary(),
    )

    sender = pre.fund_eoa()
    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[
                    Transaction(sender=sender, to=factory),
                    Transaction(sender=sender, to=probe),
                ]
            )
        ],
        post={
            probe: Account(storage=probe_storage),
            victim: Account(nonce=1, code=victim_code, balance=0),
            beneficiary: Account(balance=1 + VICTIM_BALANCE),
        },
    )


def test_reverted_sendall_rolls_back(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Revert a frame that called a freshly created account's SENDALL.

    The sweep and its transfer log roll back with the reverting frame; the
    created account keeps its balance and code.
    """
    beneficiary = pre.fund_eoa(amount=1)
    victim_code = Op.SELFDESTRUCT(beneficiary)
    initcode = Initcode(deploy_code=victim_code)
    factory = pre.deploy_contract(
        code=Om.MSTORE(initcode, 0)
        + Op.SSTORE(0, Op.CREATE(value=VICTIM_BALANCE, size=len(initcode))),
        balance=VICTIM_BALANCE,
    )
    victim = compute_create_address(address=factory, nonce=1)
    reverter = pre.deploy_contract(
        code=Op.POP(Op.CALL(address=victim)) + Op.REVERT(0, 0)
    )

    entry_storage = Storage()
    entry = pre.deploy_contract(
        code=Op.SSTORE(entry_storage.store_next(1), Op.CALL(address=factory))
        + Op.SSTORE(entry_storage.store_next(0), Op.CALL(address=reverter)),
        storage=entry_storage.canary(),
    )

    state_test(
        pre=pre,
        post={
            entry: Account(storage=entry_storage),
            victim: Account(nonce=1, code=victim_code, balance=VICTIM_BALANCE),
            beneficiary: Account(balance=1),
        },
        tx=Transaction(
            sender=pre.fund_eoa(),
            to=entry,
            expected_receipt=TransactionReceipt(
                logs=[transfer_log(factory, victim, VICTIM_BALANCE)]
            ),
        ),
    )


def test_sendall_grants_no_refund(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Charge SENDALL without any refund.

    The swept account also clears a storage slot, so the receipt's gas
    used shows that the only refund is the slot clear's, capped as usual.
    """
    beneficiary = pre.fund_eoa(amount=1)
    clear = Op.SSTORE.with_metadata(
        key_warm=False,
        original_value=1,
        current_value=1,
        new_value=0,
    )(0, 0)
    sweep = Op.SELFDESTRUCT(beneficiary, address_warm=False, account_new=False)
    victim = pre.deploy_contract(
        code=clear + sweep, storage={0: 1}, balance=VICTIM_BALANCE
    )

    intrinsic = fork.transaction_intrinsic_cost_calculator()(
        return_cost_deducted_prior_execution=True
    )
    executed = intrinsic + clear.gas_cost(fork) + sweep.gas_cost(fork)
    refund = min(clear.refund(fork), executed // fork.max_refund_quotient())
    assert refund > 0

    state_test(
        pre=pre,
        post={
            victim: Account(balance=0, code=clear + sweep, storage={}),
            beneficiary: Account(balance=1 + VICTIM_BALANCE),
        },
        tx=Transaction(
            sender=pre.fund_eoa(),
            to=victim,
            expected_receipt=TransactionReceipt(
                cumulative_gas_used=executed - refund
            ),
        ),
    )


def test_bal_created_account_storage_read(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
) -> None:
    """
    Record a storage read by an account created and swept in one tx.

    The read stays a read next to the nonce and code changes that now
    persist.
    """
    beneficiary = pre.fund_eoa(amount=1)
    victim_code = Op.POP(Op.SLOAD(SLOT)) + Op.SELFDESTRUCT(beneficiary)
    initcode = Initcode(deploy_code=victim_code)
    factory = pre.deploy_contract(
        code=Om.MSTORE(initcode, 0)
        + Op.CALL(address=Op.CREATE(value=VICTIM_BALANCE, size=len(initcode))),
        balance=VICTIM_BALANCE,
    )
    victim = compute_create_address(address=factory, nonce=1)

    block = Block(
        txs=[Transaction(sender=pre.fund_eoa(), to=factory)],
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                victim: BalAccountExpectation(
                    nonce_changes=[
                        BalNonceChange(block_access_index=1, post_nonce=1)
                    ],
                    code_changes=[
                        BalCodeChange(
                            block_access_index=1, new_code=bytes(victim_code)
                        )
                    ],
                    storage_changes=[],
                    storage_reads=[SLOT],
                    balance_changes=[],
                ),
            }
        ),
    )

    blockchain_test(
        pre=pre,
        blocks=[block],
        post={
            victim: Account(nonce=1, code=victim_code, balance=0, storage={}),
            beneficiary: Account(balance=1 + VICTIM_BALANCE),
        },
    )


def test_delegation_to_swept_account(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
) -> None:
    """
    Delegate an EOA to a contract that is created and swept in one tx.

    The swept contract persists, so a later transaction to the authority
    still runs its code against the authority's storage and balance.
    """
    beneficiary = pre.fund_eoa(amount=1)
    victim_code = Op.SSTORE(SLOT, CANARY) + Op.SELFDESTRUCT(beneficiary)
    initcode = Initcode(deploy_code=victim_code)
    factory = pre.deploy_contract(
        code=Om.MSTORE(initcode, 0)
        + Op.CALL(address=Op.CREATE(value=VICTIM_BALANCE, size=len(initcode))),
        balance=VICTIM_BALANCE,
    )
    victim = compute_create_address(address=factory, nonce=1)
    authority = pre.fund_eoa(amount=REFILL)

    sender = pre.fund_eoa()
    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[
                    Transaction(
                        sender=sender,
                        to=factory,
                        authorization_list=[
                            AuthorizationTuple(
                                address=victim, nonce=0, signer=authority
                            )
                        ],
                    ),
                    Transaction(sender=sender, to=authority),
                ]
            )
        ],
        post={
            victim: Account(
                nonce=1,
                code=victim_code,
                balance=0,
                storage={SLOT: CANARY},
            ),
            authority: Account(
                nonce=1,
                code=Spec7702.delegation_designation(victim),
                balance=0,
                storage={SLOT: CANARY},
            ),
            beneficiary: Account(balance=1 + VICTIM_BALANCE + REFILL),
        },
    )
