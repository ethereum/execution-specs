"""
abstract: Tests use of set-code transactions from [EIP-7702: Set EOA account code for one transaction](https://eips.ethereum.org/EIPS/eip-7702)
    Tests use of set-code transactions from [EIP-7702: Set EOA account code for one transaction](https://eips.ethereum.org/EIPS/eip-7702).
"""  # noqa: E501

from enum import Enum
from hashlib import sha256
from itertools import count
from typing import List

import pytest
from ethereum.crypto.hash import keccak256

from ethereum_test_tools import (
    AccessList,
    Account,
    Address,
    Alloc,
    AuthorizationTuple,
    Block,
    BlockchainTestFiller,
    Bytecode,
    Bytes,
    CodeGasMeasure,
    Conditional,
    Environment,
    EVMCodeType,
    Hash,
    Initcode,
)
from ethereum_test_tools import Macros as Om
from ethereum_test_tools import Opcodes as Op
from ethereum_test_tools import (
    StateTestFiller,
    Storage,
    Transaction,
    TransactionException,
    add_kzg_version,
    call_return_code,
    compute_create_address,
)
from ethereum_test_tools.eof.v1 import Container, Section

from ...cancun.eip4844_blobs.spec import Spec as Spec4844
from ..eip6110_deposits.helpers import DepositRequest
from ..eip7002_el_triggerable_withdrawals.helpers import WithdrawalRequest
from ..eip7251_consolidations.helpers import ConsolidationRequest
from .helpers import AddressType
from .spec import Spec, ref_spec_7702

REFERENCE_SPEC_GIT_PATH = ref_spec_7702.git_path
REFERENCE_SPEC_VERSION = ref_spec_7702.version

pytestmark = pytest.mark.valid_from("Prague")

auth_account_start_balance = 0


@pytest.mark.parametrize(
    "tx_value",
    [0, 1],
)
@pytest.mark.parametrize(
    "suffix,succeeds",
    [
        pytest.param(Op.STOP, True, id="stop"),
        pytest.param(Op.RETURN(0, 0), True, id="return"),
        pytest.param(Op.REVERT, False, id="revert"),
        pytest.param(Op.INVALID, False, id="invalid"),
        pytest.param(Om.OOG, False, id="out-of-gas"),
    ],
)
def test_self_sponsored_set_code(
    state_test: StateTestFiller,
    pre: Alloc,
    suffix: Bytecode,
    succeeds: bool,
    tx_value: int,
):
    """
    Test the executing a self-sponsored set-code transaction.

    The transaction is sent to the sender, and the sender is the signer of the only authorization
    tuple in the authorization list.

    The authorization tuple has a nonce of 1 because the self-sponsored transaction increases the
    nonce of the sender from zero to one first.

    The expected nonce at the end of the transaction is 2.
    """
    storage = Storage()
    sender = pre.fund_eoa()

    set_code = (
        Op.SSTORE(storage.store_next(sender), Op.ORIGIN)
        + Op.SSTORE(storage.store_next(sender), Op.CALLER)
        + Op.SSTORE(storage.store_next(tx_value), Op.CALLVALUE)
        + suffix
    )
    set_code_to_address = pre.deploy_contract(
        set_code,
    )

    tx = Transaction(
        gas_limit=10_000_000,
        to=sender,
        value=tx_value,
        authorization_list=[
            AuthorizationTuple(
                address=set_code_to_address,
                nonce=1,
                signer=sender,
            ),
        ],
        sender=sender,
    )

    state_test(
        env=Environment(),
        pre=pre,
        tx=tx,
        post={
            set_code_to_address: Account(storage={k: 0 for k in storage}),
            sender: Account(
                nonce=2,
                code=Spec.delegation_designation(set_code_to_address),
                storage=storage if succeeds else {},
            ),
        },
    )


@pytest.mark.parametrize(
    "eoa_balance,self_sponsored",
    [
        pytest.param(0, False, id="zero_balance_authority"),
        pytest.param(1, False, id="one_wei_balance_authority"),
        pytest.param(None, True, id="self_sponsored_tx"),
    ],
)
@pytest.mark.parametrize(
    "tx_value",
    [0, 1],
)
@pytest.mark.parametrize(
    "suffix,succeeds",
    [
        pytest.param(Op.STOP, True, id="stop"),
        pytest.param(Op.RETURN(0, 0), True, id="return"),
        pytest.param(Op.REVERT(0, 0), False, id="revert"),
        pytest.param(Op.INVALID, False, id="invalid"),
        pytest.param(Om.OOG + Op.STOP, False, id="out-of-gas"),
    ],
)
def test_set_code_to_sstore(
    state_test: StateTestFiller,
    pre: Alloc,
    suffix: Bytecode,
    succeeds: bool,
    tx_value: int,
    eoa_balance: int,
    self_sponsored: bool,
):
    """
    Test the executing a simple SSTORE in a set-code transaction.
    """
    storage = Storage()
    if self_sponsored:
        sender = pre.fund_eoa()
        auth_signer = sender
    else:
        auth_signer = pre.fund_eoa(eoa_balance)
        sender = pre.fund_eoa()

    set_code = (
        Op.SSTORE(storage.store_next(sender), Op.ORIGIN)
        + Op.SSTORE(storage.store_next(sender), Op.CALLER)
        + Op.SSTORE(storage.store_next(tx_value), Op.CALLVALUE)
        + suffix
    )
    set_code_to_address = pre.deploy_contract(
        set_code,
    )

    tx = Transaction(
        gas_limit=500_000,
        to=auth_signer,
        value=tx_value,
        authorization_list=[
            AuthorizationTuple(
                address=set_code_to_address,
                nonce=1 if self_sponsored else 0,
                signer=auth_signer,
            ),
        ],
        sender=sender,
    )

    state_test(
        env=Environment(),
        pre=pre,
        tx=tx,
        post={
            set_code_to_address: Account(
                storage={k: 0 for k in storage},
            ),
            auth_signer: Account(
                nonce=2 if self_sponsored else 1,
                code=Spec.delegation_designation(set_code_to_address),
                storage=storage if succeeds else {},
            ),
        },
    )


def test_set_code_to_zero_address(
    state_test: StateTestFiller,
    pre: Alloc,
):
    """
    Test setting the code to the zero address (0x0) in a set-code transaction.
    """
    auth_signer = pre.fund_eoa(auth_account_start_balance)

    tx = Transaction(
        gas_limit=500_000,
        to=auth_signer,
        authorization_list=[
            AuthorizationTuple(
                address=Address(0),
                nonce=0,
                signer=auth_signer,
            ),
        ],
        sender=pre.fund_eoa(),
    )

    state_test(
        env=Environment(),
        pre=pre,
        tx=tx,
        post={
            auth_signer: Account(
                nonce=1,
                code=Spec.delegation_designation(Address(0)),
                storage={},
            ),
        },
    )


def test_set_code_to_sstore_then_sload(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
):
    """
    Test the executing a simple SSTORE then SLOAD in two separate set-code transactions.
    """
    auth_signer = pre.fund_eoa(auth_account_start_balance)
    sender = pre.fund_eoa()

    storage_key_1 = 0x1
    storage_key_2 = 0x2
    storage_value = 0x1234

    set_code_1 = Op.SSTORE(storage_key_1, storage_value) + Op.STOP
    set_code_1_address = pre.deploy_contract(set_code_1)

    set_code_2 = Op.SSTORE(storage_key_2, Op.ADD(Op.SLOAD(storage_key_1), 1)) + Op.STOP
    set_code_2_address = pre.deploy_contract(set_code_2)

    tx_1 = Transaction(
        gas_limit=100_000,
        to=auth_signer,
        value=0,
        authorization_list=[
            AuthorizationTuple(
                address=set_code_1_address,
                nonce=0,
                signer=auth_signer,
            ),
        ],
        sender=sender,
    )

    tx_2 = Transaction(
        gas_limit=100_000,
        to=auth_signer,
        value=0,
        authorization_list=[
            AuthorizationTuple(
                address=set_code_2_address,
                nonce=1,
                signer=auth_signer,
            ),
        ],
        sender=sender,
    )

    block = Block(
        txs=[tx_1, tx_2],
    )

    blockchain_test(
        pre=pre,
        post={
            auth_signer: Account(
                nonce=2,
                code=Spec.delegation_designation(set_code_2_address),
                storage={
                    storage_key_1: storage_value,
                    storage_key_2: storage_value + 1,
                },
            ),
        },
        blocks=[block],
    )


@pytest.mark.parametrize(
    "return_opcode",
    [
        Op.RETURN,
        Op.REVERT,
    ],
)
@pytest.mark.with_all_call_opcodes
def test_set_code_to_tstore_reentry(
    state_test: StateTestFiller,
    pre: Alloc,
    call_opcode: Op,
    return_opcode: Op,
    evm_code_type: EVMCodeType,
):
    """
    Test the executing a simple TSTORE in a set-code transaction, which also performs a
    re-entry to TLOAD the value.
    """
    auth_signer = pre.fund_eoa(auth_account_start_balance)

    tload_value = 0x1234
    set_code = Conditional(
        condition=Op.ISZERO(Op.TLOAD(1)),
        if_true=Op.TSTORE(1, tload_value)
        + call_opcode(address=Op.ADDRESS)
        + Op.RETURNDATACOPY(0, 0, 32)
        + Op.SSTORE(2, Op.MLOAD(0)),
        if_false=Op.MSTORE(0, Op.TLOAD(1)) + return_opcode(size=32),
        evm_code_type=evm_code_type,
    )
    set_code_to_address = pre.deploy_contract(set_code)

    tx = Transaction(
        gas_limit=100_000,
        to=auth_signer,
        value=0,
        authorization_list=[
            AuthorizationTuple(
                address=set_code_to_address,
                nonce=0,
                signer=auth_signer,
            ),
        ],
        sender=pre.fund_eoa(),
    )

    state_test(
        env=Environment(),
        pre=pre,
        tx=tx,
        post={
            auth_signer: Account(
                nonce=1,
                code=Spec.delegation_designation(set_code_to_address),
                storage={2: tload_value},
            ),
        },
    )


@pytest.mark.with_all_call_opcodes(
    selector=lambda call_opcode: call_opcode
    not in [Op.DELEGATECALL, Op.CALLCODE, Op.STATICCALL, Op.EXTDELEGATECALL, Op.EXTSTATICCALL]
)
@pytest.mark.parametrize("call_eoa_first", [True, False])
def test_set_code_to_tstore_available_at_correct_address(
    state_test: StateTestFiller,
    pre: Alloc,
    call_opcode: Op,
    call_eoa_first: bool,
):
    """
    Test TLOADing from slot 2 and then SSTORE this in slot 1, then TSTORE 3 in slot 2.
    This is done both from the EOA which is delegated to account A, and then A is called.
    The storage should stay empty on both the EOA and the delegated account.
    """
    auth_signer = pre.fund_eoa(auth_account_start_balance)

    storage_slot = 1
    tload_slot = 2
    tstore_value = 3

    tstore_check_code = Op.SSTORE(storage_slot, Op.TLOAD(tload_slot)) + Op.TSTORE(
        tload_slot, tstore_value
    )

    set_code_to_address = pre.deploy_contract(tstore_check_code)

    def make_call(call_type: Op, call_eoa: bool) -> Bytecode:
        call_target = auth_signer if call_eoa else set_code_to_address
        return call_type(address=call_target)

    chain_code = make_call(call_type=call_opcode, call_eoa=call_eoa_first) + make_call(
        call_type=call_opcode, call_eoa=not call_eoa_first
    )

    target_call_chain_address = pre.deploy_contract(chain_code)

    tx = Transaction(
        gas_limit=100_000,
        to=target_call_chain_address,
        value=0,
        authorization_list=[
            AuthorizationTuple(
                address=set_code_to_address,
                nonce=0,
                signer=auth_signer,
            ),
        ],
        sender=pre.fund_eoa(),
    )

    state_test(
        env=Environment(),
        pre=pre,
        tx=tx,
        post={
            auth_signer: Account(
                storage={storage_slot: 0},
            ),
            set_code_to_address: Account(
                storage={storage_slot: 0},
            ),
        },
    )


@pytest.mark.parametrize(
    "external_sendall_recipient",
    [False, True],
)
@pytest.mark.parametrize(
    "balance",
    [0, 1],
)
def test_set_code_to_self_destruct(
    state_test: StateTestFiller,
    pre: Alloc,
    external_sendall_recipient: bool,
    balance: int,
):
    """
    Test the executing self-destruct opcode in a set-code transaction.
    """
    auth_signer = pre.fund_eoa(balance)
    if external_sendall_recipient:
        recipient = pre.fund_eoa(0)
    else:
        recipient = auth_signer

    set_code_to_address = pre.deploy_contract(Op.SSTORE(1, 1) + Op.SELFDESTRUCT(recipient))

    tx = Transaction(
        gas_limit=10_000_000,
        to=auth_signer,
        value=0,
        authorization_list=[
            AuthorizationTuple(
                address=set_code_to_address,
                nonce=0,
                signer=auth_signer,
            ),
        ],
        sender=pre.fund_eoa(),
    )

    post = {
        auth_signer: Account(
            nonce=1,
            code=Spec.delegation_designation(set_code_to_address),
            storage={1: 1},
            balance=balance if not external_sendall_recipient else 0,
        ),
    }

    if external_sendall_recipient and balance > 0:
        post[recipient] = Account(balance=balance)

    state_test(
        env=Environment(),
        pre=pre,
        tx=tx,
        post=post,
    )


@pytest.mark.with_all_create_opcodes
def test_set_code_to_contract_creator(
    state_test: StateTestFiller,
    pre: Alloc,
    create_opcode: Op,
    evm_code_type: EVMCodeType,
):
    """
    Test the executing a contract-creating opcode in a set-code transaction.
    """
    storage = Storage()
    auth_signer = pre.fund_eoa(auth_account_start_balance)

    deployed_code: Bytecode | Container = Op.STOP
    initcode: Bytecode | Container

    if evm_code_type == EVMCodeType.LEGACY:
        initcode = Initcode(deploy_code=deployed_code)
    elif evm_code_type == EVMCodeType.EOF_V1:
        deployed_code = Container.Code(deployed_code)
        initcode = Container.Init(deploy_container=deployed_code)
    else:
        raise ValueError(f"Unsupported EVM code type: {evm_code_type}")

    salt = 0

    deployed_contract_address = compute_create_address(
        address=auth_signer,
        nonce=1,
        salt=salt,
        initcode=initcode,
        opcode=create_opcode,
    )

    creator_code: Bytecode | Container
    if evm_code_type == EVMCodeType.LEGACY:
        creator_code = Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE) + Op.SSTORE(
            storage.store_next(deployed_contract_address),
            create_opcode(value=0, offset=0, size=Op.CALLDATASIZE, salt=salt),
        )
    elif evm_code_type == EVMCodeType.EOF_V1:
        creator_code = Container(
            sections=[
                Section.Code(
                    code=Op.EOFCREATE[0](0, 0, 0, 0) + Op.STOP(),
                ),
                Section.Container(
                    container=initcode,
                ),
            ]
        )
    else:
        raise ValueError(f"Unsupported EVM code type: {evm_code_type}")

    creator_code_address = pre.deploy_contract(creator_code)

    tx = Transaction(
        gas_limit=10_000_000,
        to=auth_signer,
        value=0,
        data=initcode if evm_code_type == EVMCodeType.LEGACY else b"",
        authorization_list=[
            AuthorizationTuple(
                address=creator_code_address,
                nonce=0,
                signer=auth_signer,
            ),
        ],
        sender=pre.fund_eoa(),
    )

    state_test(
        env=Environment(),
        pre=pre,
        tx=tx,
        post={
            creator_code_address: Account(storage={}),
            auth_signer: Account(
                nonce=2,
                code=Spec.delegation_designation(creator_code_address),
                storage=storage,
            ),
            deployed_contract_address: Account(
                code=deployed_code,
                storage={},
            ),
        },
    )


@pytest.mark.parametrize(
    "value",
    [0, 1],
)
@pytest.mark.with_all_call_opcodes
def test_set_code_to_self_caller(
    state_test: StateTestFiller,
    pre: Alloc,
    call_opcode: Op,
    value: int,
    evm_code_type: EVMCodeType,
):
    """
    Test the executing a self-call in a set-code transaction.
    """
    storage = Storage()
    auth_signer = pre.fund_eoa(auth_account_start_balance)

    static_call = call_opcode in [Op.STATICCALL, Op.EXTSTATICCALL]

    first_entry_slot = storage.store_next(True)
    re_entry_success_slot = storage.store_next(not static_call)
    re_entry_call_return_code_slot = storage.store_next(
        call_return_code(opcode=call_opcode, success=not static_call)
    )
    set_code = Conditional(
        condition=Op.ISZERO(Op.SLOAD(first_entry_slot)),
        if_true=Op.SSTORE(first_entry_slot, 1)
        + Op.SSTORE(re_entry_call_return_code_slot, call_opcode(address=auth_signer, value=value))
        + Op.STOP,
        if_false=Op.SSTORE(re_entry_success_slot, 1) + Op.STOP,
        evm_code_type=evm_code_type,
    )
    set_code_to_address = pre.deploy_contract(set_code)

    tx = Transaction(
        gas_limit=10_000_000,
        to=auth_signer,
        value=value,
        authorization_list=[
            AuthorizationTuple(
                address=set_code_to_address,
                nonce=0,
                signer=auth_signer,
            ),
        ],
        sender=pre.fund_eoa(),
    )

    state_test(
        env=Environment(),
        pre=pre,
        tx=tx,
        post={
            set_code_to_address: Account(storage={}),
            auth_signer: Account(
                nonce=1,
                code=Spec.delegation_designation(set_code_to_address),
                storage=storage,
                balance=auth_account_start_balance + value,
            ),
        },
    )


@pytest.mark.with_all_call_opcodes
@pytest.mark.parametrize(
    "value",
    [0, 1],
)
def test_set_code_call_set_code(
    state_test: StateTestFiller,
    pre: Alloc,
    call_opcode: Op,
    value: int,
):
    """
    Test the calling a set-code account from another set-code account.
    """
    auth_signer_1 = pre.fund_eoa(auth_account_start_balance)
    storage_1 = Storage()

    static_call = call_opcode in [Op.STATICCALL, Op.EXTSTATICCALL]

    set_code_1_call_result_slot = storage_1.store_next(
        call_return_code(opcode=call_opcode, success=not static_call)
    )
    set_code_1_success = storage_1.store_next(True)

    auth_signer_2 = pre.fund_eoa(auth_account_start_balance)
    storage_2 = Storage().set_next_slot(storage_1.peek_slot())
    set_code_2_success = storage_2.store_next(not static_call)

    set_code_1 = (
        Op.SSTORE(set_code_1_call_result_slot, call_opcode(address=auth_signer_2, value=value))
        + Op.SSTORE(set_code_1_success, 1)
        + Op.STOP
    )
    set_code_to_address_1 = pre.deploy_contract(set_code_1)

    set_code_2 = Op.SSTORE(set_code_2_success, 1) + Op.STOP
    set_code_to_address_2 = pre.deploy_contract(set_code_2)

    tx = Transaction(
        gas_limit=10_000_000,
        to=auth_signer_1,
        value=value,
        authorization_list=[
            AuthorizationTuple(
                address=set_code_to_address_1,
                nonce=0,
                signer=auth_signer_1,
            ),
            AuthorizationTuple(
                address=set_code_to_address_2,
                nonce=0,
                signer=auth_signer_2,
            ),
        ],
        sender=pre.fund_eoa(),
    )

    state_test(
        env=Environment(),
        pre=pre,
        tx=tx,
        post={
            set_code_to_address_1: Account(storage={k: 0 for k in storage_1}),
            set_code_to_address_2: Account(storage={k: 0 for k in storage_2}),
            auth_signer_1: Account(
                nonce=1,
                code=Spec.delegation_designation(set_code_to_address_1),
                storage=(
                    storage_1
                    if call_opcode in [Op.CALL, Op.STATICCALL, Op.EXTCALL, Op.EXTSTATICCALL]
                    else storage_1 + storage_2
                ),
                balance=(0 if call_opcode in [Op.CALL, Op.EXTCALL] else value)
                + auth_account_start_balance,
            ),
            auth_signer_2: Account(
                nonce=1,
                code=Spec.delegation_designation(set_code_to_address_2),
                storage=storage_2 if call_opcode in [Op.CALL, Op.EXTCALL] else {},
                balance=(value if call_opcode in [Op.CALL, Op.EXTCALL] else 0)
                + auth_account_start_balance,
            ),
        },
    )


def test_address_from_set_code(
    state_test: StateTestFiller,
    pre: Alloc,
):
    """
    Test the address opcode in a set-code transaction.
    """
    storage = Storage()
    auth_signer = pre.fund_eoa(auth_account_start_balance)

    set_code = Op.SSTORE(storage.store_next(auth_signer), Op.ADDRESS) + Op.STOP
    set_code_to_address = pre.deploy_contract(set_code)

    tx = Transaction(
        gas_limit=10_000_000,
        to=auth_signer,
        value=0,
        authorization_list=[
            AuthorizationTuple(
                address=set_code_to_address,
                nonce=0,
                signer=auth_signer,
            ),
        ],
        sender=pre.fund_eoa(),
    )

    state_test(
        env=Environment(),
        pre=pre,
        tx=tx,
        post={
            set_code_to_address: Account(storage={}),
            auth_signer: Account(
                nonce=1,
                code=Spec.delegation_designation(set_code_to_address),
                storage=storage,
            ),
        },
    )


def test_tx_into_self_delegating_set_code(
    state_test: StateTestFiller,
    pre: Alloc,
):
    """
    Test a transaction that has entry-point into a set-code address that delegates to itself.
    """
    auth_signer = pre.fund_eoa(auth_account_start_balance)

    tx = Transaction(
        gas_limit=10_000_000,
        to=auth_signer,
        value=0,
        authorization_list=[
            AuthorizationTuple(
                address=auth_signer,
                nonce=0,
                signer=auth_signer,
            ),
        ],
        sender=pre.fund_eoa(),
    )

    state_test(
        env=Environment(),
        pre=pre,
        tx=tx,
        post={
            auth_signer: Account(
                nonce=1,
                code=Spec.delegation_designation(auth_signer),
            ),
        },
    )


def test_tx_into_chain_delegating_set_code(
    state_test: StateTestFiller,
    pre: Alloc,
):
    """
    Test a transaction that has entry-point into a set-code address that delegates to itself.
    """
    auth_signer_1 = pre.fund_eoa(auth_account_start_balance)
    auth_signer_2 = pre.fund_eoa(auth_account_start_balance)

    tx = Transaction(
        gas_limit=10_000_000,
        to=auth_signer_1,
        value=0,
        authorization_list=[
            AuthorizationTuple(
                address=auth_signer_2,
                nonce=0,
                signer=auth_signer_1,
            ),
            AuthorizationTuple(
                address=auth_signer_1,
                nonce=0,
                signer=auth_signer_2,
            ),
        ],
        sender=pre.fund_eoa(),
    )

    state_test(
        env=Environment(),
        pre=pre,
        tx=tx,
        post={
            auth_signer_1: Account(nonce=1, code=Spec.delegation_designation(auth_signer_2)),
            auth_signer_2: Account(nonce=1, code=Spec.delegation_designation(auth_signer_1)),
        },
    )


@pytest.mark.with_all_call_opcodes
def test_call_into_self_delegating_set_code(
    state_test: StateTestFiller,
    pre: Alloc,
    call_opcode: Op,
):
    """
    Test a transaction that has entry-point into a set-code address that delegates to itself.
    """
    auth_signer = pre.fund_eoa(auth_account_start_balance)

    storage = Storage()
    entry_code = (
        Op.SSTORE(
            storage.store_next(call_return_code(opcode=call_opcode, success=False)),
            call_opcode(address=auth_signer),
        )
        + Op.STOP
    )
    entry_address = pre.deploy_contract(entry_code)

    tx = Transaction(
        gas_limit=10_000_000,
        to=entry_address,
        value=0,
        authorization_list=[
            AuthorizationTuple(
                address=auth_signer,
                nonce=0,
                signer=auth_signer,
            ),
        ],
        sender=pre.fund_eoa(),
    )

    state_test(
        env=Environment(),
        pre=pre,
        tx=tx,
        post={
            entry_address: Account(storage=storage),
            auth_signer: Account(nonce=1, code=Spec.delegation_designation(auth_signer)),
        },
    )


@pytest.mark.with_all_call_opcodes
def test_call_into_chain_delegating_set_code(
    state_test: StateTestFiller,
    pre: Alloc,
    call_opcode: Op,
):
    """
    Test a transaction that has entry-point into a set-code address that delegates to itself.
    """
    auth_signer_1 = pre.fund_eoa(auth_account_start_balance)
    auth_signer_2 = pre.fund_eoa(auth_account_start_balance)

    storage = Storage()
    entry_code = (
        Op.SSTORE(
            storage.store_next(call_return_code(opcode=call_opcode, success=False)),
            call_opcode(address=auth_signer_1),
        )
        + Op.STOP
    )
    entry_address = pre.deploy_contract(entry_code)

    tx = Transaction(
        gas_limit=10_000_000,
        to=entry_address,
        value=0,
        authorization_list=[
            AuthorizationTuple(
                address=auth_signer_2,
                nonce=0,
                signer=auth_signer_1,
            ),
            AuthorizationTuple(
                address=auth_signer_1,
                nonce=0,
                signer=auth_signer_2,
            ),
        ],
        sender=pre.fund_eoa(),
    )

    state_test(
        env=Environment(),
        pre=pre,
        tx=tx,
        post={
            entry_address: Account(storage=storage),
            auth_signer_1: Account(nonce=1, code=Spec.delegation_designation(auth_signer_2)),
            auth_signer_2: Account(nonce=1, code=Spec.delegation_designation(auth_signer_1)),
        },
    )


@pytest.mark.parametrize(
    "balance",
    [0, 1],
)
@pytest.mark.parametrize(
    "set_code_type",
    list(AddressType),
    ids=lambda address_type: address_type.name,
)
def test_ext_code_on_set_code(
    state_test: StateTestFiller,
    pre: Alloc,
    balance: int,
    set_code_type: AddressType,
):
    """
    Test different ext*code operations on a set-code address.
    """
    auth_signer = pre.fund_eoa(balance)

    slot = count(1)
    slot_ext_code_size_result = next(slot)
    slot_ext_code_hash_result = next(slot)
    slot_ext_code_copy_result = next(slot)
    slot_ext_balance_result = next(slot)

    callee_code = (
        Op.SSTORE(slot_ext_code_size_result, Op.EXTCODESIZE(auth_signer))
        + Op.SSTORE(slot_ext_code_hash_result, Op.EXTCODEHASH(auth_signer))
        + Op.EXTCODECOPY(auth_signer, 0, 0, Op.EXTCODESIZE(auth_signer))
        + Op.SSTORE(slot_ext_code_copy_result, Op.MLOAD(0))
        + Op.SSTORE(slot_ext_balance_result, Op.BALANCE(auth_signer))
        + Op.STOP
    )
    callee_address = pre.deploy_contract(callee_code)

    set_code_to_address: Address
    set_code: Bytecode | Bytes
    match set_code_type:
        case AddressType.EMPTY_ACCOUNT:
            set_code = Bytecode()
            set_code_to_address = pre.fund_eoa(0)
        case AddressType.EOA:
            set_code = Bytecode()
            set_code_to_address = pre.fund_eoa(1)
        case AddressType.EOA_WITH_SET_CODE:
            set_code_account = pre.fund_eoa(0)
            set_code = Spec.delegation_designation(set_code_account)
            set_code_to_address = pre.fund_eoa(1, delegation=set_code_account)
        case AddressType.CONTRACT:
            set_code = Op.STOP
            set_code_to_address = pre.deploy_contract(set_code)
        case _:
            raise ValueError(f"Unsupported set code type: {set_code_type}")

    callee_storage = Storage()
    callee_storage[slot_ext_code_size_result] = len(set_code)
    callee_storage[slot_ext_code_hash_result] = (
        set_code.keccak256() if set_code_type != AddressType.EMPTY_ACCOUNT else 0
    )
    callee_storage[slot_ext_code_copy_result] = bytes(set_code).ljust(32, b"\x00")[:32]
    callee_storage[slot_ext_balance_result] = balance

    tx = Transaction(
        gas_limit=10_000_000,
        to=callee_address,
        authorization_list=[
            AuthorizationTuple(
                address=set_code_to_address,
                nonce=0,
                signer=auth_signer,
            ),
        ],
        sender=pre.fund_eoa(),
    )

    state_test(
        env=Environment(),
        pre=pre,
        tx=tx,
        post={
            set_code_to_address: (
                Account.NONEXISTENT
                if set_code_type == AddressType.EMPTY_ACCOUNT
                else Account(storage={})
            ),
            auth_signer: Account(
                nonce=1,
                code=Spec.delegation_designation(set_code_to_address),
                balance=balance,
            ),
            callee_address: Account(storage=callee_storage),
        },
    )


@pytest.mark.parametrize(
    "balance",
    [0, 1],
)
def test_ext_code_on_self_set_code(
    state_test: StateTestFiller,
    pre: Alloc,
    balance: int,
):
    """
    Test different ext*code operations on self set-code address.
    """
    auth_signer = pre.fund_eoa(balance)

    slot = count(1)
    slot_ext_code_size_result = next(slot)
    slot_ext_code_hash_result = next(slot)
    slot_ext_code_copy_result = next(slot)
    slot_ext_balance_result = next(slot)

    set_code = (
        Op.SSTORE(slot_ext_code_size_result, Op.EXTCODESIZE(auth_signer))
        + Op.SSTORE(slot_ext_code_hash_result, Op.EXTCODEHASH(auth_signer))
        + Op.EXTCODECOPY(auth_signer, 0, 0, Op.EXTCODESIZE(auth_signer))
        + Op.SSTORE(slot_ext_code_copy_result, Op.MLOAD(0))
        + Op.SSTORE(slot_ext_balance_result, Op.BALANCE(auth_signer))
        + Op.STOP
    )
    set_code_address = pre.deploy_contract(set_code)

    set_code_storage = Storage()
    set_code_storage[slot_ext_code_size_result] = len(set_code)
    set_code_storage[slot_ext_code_hash_result] = set_code.keccak256()
    set_code_storage[slot_ext_code_copy_result] = bytes(set_code).ljust(32, b"\x00")[:32]
    set_code_storage[slot_ext_balance_result] = balance

    tx = Transaction(
        gas_limit=10_000_000,
        to=auth_signer,
        authorization_list=[
            AuthorizationTuple(
                address=set_code_address,
                nonce=0,
                signer=auth_signer,
            ),
        ],
        sender=pre.fund_eoa(),
    )

    state_test(
        env=Environment(),
        pre=pre,
        tx=tx,
        post={
            auth_signer: Account(storage=set_code_storage),
        },
    )


@pytest.mark.with_all_call_opcodes(
    selector=(
        lambda opcode: opcode
        not in [Op.STATICCALL, Op.CALLCODE, Op.DELEGATECALL, Op.EXTDELEGATECALL, Op.EXTSTATICCALL]
    )
)
@pytest.mark.parametrize(
    "set_code_address_first",
    [
        pytest.param(True, id="call_set_code_address_first_then_authority"),
        pytest.param(False, id="call_authority_first_then_set_code_address"),
    ],
)
def test_set_code_address_and_authority_warm_state(
    state_test: StateTestFiller,
    pre: Alloc,
    call_opcode: Op,
    set_code_address_first: bool,
):
    """
    Test set to code address and authority warm status after a call to
    authority address, or viceversa.
    """
    auth_signer = pre.fund_eoa(auth_account_start_balance)

    slot = count(1)
    slot_call_success = next(slot)
    slot_set_code_to_warm_state = next(slot)
    slot_authority_warm_state = next(slot)

    set_code = Op.STOP
    set_code_to_address = pre.deploy_contract(set_code)

    overhead_cost = 3 * len(call_opcode.kwargs)  # type: ignore
    if call_opcode == Op.CALL:
        overhead_cost -= 1  # GAS opcode is less expensive than a PUSH

    code_gas_measure_set_code = CodeGasMeasure(
        code=call_opcode(address=set_code_to_address),
        overhead_cost=overhead_cost,
        extra_stack_items=1,
        sstore_key=slot_set_code_to_warm_state,
        stop=False,
    )
    code_gas_measure_authority = CodeGasMeasure(
        code=call_opcode(address=auth_signer),
        overhead_cost=overhead_cost,
        extra_stack_items=1,
        sstore_key=slot_authority_warm_state,
        stop=False,
    )

    callee_code = Bytecode()
    if set_code_address_first:
        callee_code += code_gas_measure_set_code + code_gas_measure_authority
    else:
        callee_code += code_gas_measure_authority + code_gas_measure_set_code
    callee_code += Op.SSTORE(slot_call_success, 1) + Op.STOP

    callee_address = pre.deploy_contract(callee_code)
    callee_storage = Storage()
    callee_storage[slot_call_success] = 1
    callee_storage[slot_set_code_to_warm_state] = 2_600 if set_code_address_first else 100
    callee_storage[slot_authority_warm_state] = 200 if set_code_address_first else 2_700

    tx = Transaction(
        gas_limit=1_000_000,
        to=callee_address,
        authorization_list=[
            AuthorizationTuple(
                address=set_code_to_address,
                nonce=0,
                signer=auth_signer,
            ),
        ],
        sender=pre.fund_eoa(),
    )

    state_test(
        env=Environment(),
        pre=pre,
        tx=tx,
        post={
            callee_address: Account(storage=callee_storage),
            auth_signer: Account(
                nonce=1,
                code=Spec.delegation_designation(set_code_to_address),
                balance=auth_account_start_balance,
            ),
        },
    )


@pytest.mark.parametrize(
    "balance",
    [0, 1],
)
def test_ext_code_on_self_delegating_set_code(
    state_test: StateTestFiller,
    pre: Alloc,
    balance: int,
):
    """
    Test different ext*code operations on a set-code address that delegates to itself.
    """
    auth_signer = pre.fund_eoa(balance)

    slot = count(1)
    slot_ext_code_size_result = next(slot)
    slot_ext_code_hash_result = next(slot)
    slot_ext_code_copy_result = next(slot)
    slot_ext_balance_result = next(slot)

    callee_code = (
        Op.SSTORE(slot_ext_code_size_result, Op.EXTCODESIZE(auth_signer))
        + Op.SSTORE(slot_ext_code_hash_result, Op.EXTCODEHASH(auth_signer))
        + Op.EXTCODECOPY(auth_signer, 0, 0, Op.EXTCODESIZE(auth_signer))
        + Op.SSTORE(slot_ext_code_copy_result, Op.MLOAD(0))
        + Op.SSTORE(slot_ext_balance_result, Op.BALANCE(auth_signer))
        + Op.STOP
    )
    callee_address = pre.deploy_contract(callee_code)
    callee_storage = Storage()

    set_code = b"\xef\x01\x00" + bytes(auth_signer)
    callee_storage[slot_ext_code_size_result] = len(set_code)
    callee_storage[slot_ext_code_hash_result] = keccak256(set_code)
    callee_storage[slot_ext_code_copy_result] = bytes(set_code).ljust(32, b"\x00")[:32]
    callee_storage[slot_ext_balance_result] = balance

    tx = Transaction(
        gas_limit=10_000_000,
        to=callee_address,
        authorization_list=[
            AuthorizationTuple(
                address=auth_signer,
                nonce=0,
                signer=auth_signer,
            ),
        ],
        sender=pre.fund_eoa(),  # TODO: Test with sender as auth_signer
    )

    state_test(
        env=Environment(),
        pre=pre,
        tx=tx,
        post={
            auth_signer: Account(
                nonce=1,
                code=Spec.delegation_designation(auth_signer),
                balance=balance,
            ),
            callee_address: Account(storage=callee_storage),
        },
    )


def test_ext_code_on_chain_delegating_set_code(
    state_test: StateTestFiller,
    pre: Alloc,
):
    """
    Test different ext*code operations on a set-code address that references another delegated
    address.
    """
    auth_signer_1_balance = 1
    auth_signer_2_balance = 0

    auth_signer_1 = pre.fund_eoa(auth_signer_1_balance)
    auth_signer_2 = pre.fund_eoa(auth_signer_2_balance)

    slot = count(1)

    slot_ext_code_size_result_1 = next(slot)
    slot_ext_code_hash_result_1 = next(slot)
    slot_ext_code_copy_result_1 = next(slot)
    slot_ext_balance_result_1 = next(slot)

    slot_ext_code_size_result_2 = next(slot)
    slot_ext_code_hash_result_2 = next(slot)
    slot_ext_code_copy_result_2 = next(slot)
    slot_ext_balance_result_2 = next(slot)

    callee_code = (
        # Address 1
        Op.SSTORE(slot_ext_code_size_result_1, Op.EXTCODESIZE(auth_signer_1))
        + Op.SSTORE(slot_ext_code_hash_result_1, Op.EXTCODEHASH(auth_signer_1))
        + Op.EXTCODECOPY(auth_signer_1, 0, 0, Op.EXTCODESIZE(auth_signer_1))
        + Op.SSTORE(slot_ext_code_copy_result_1, Op.MLOAD(0))
        + Op.SSTORE(slot_ext_balance_result_1, Op.BALANCE(auth_signer_1))
        # Address 2
        + Op.SSTORE(slot_ext_code_size_result_2, Op.EXTCODESIZE(auth_signer_2))
        + Op.SSTORE(slot_ext_code_hash_result_2, Op.EXTCODEHASH(auth_signer_2))
        + Op.EXTCODECOPY(auth_signer_2, 0, 0, Op.EXTCODESIZE(auth_signer_2))
        + Op.SSTORE(slot_ext_code_copy_result_2, Op.MLOAD(0))
        + Op.SSTORE(slot_ext_balance_result_2, Op.BALANCE(auth_signer_2))
        + Op.STOP
    )
    callee_address = pre.deploy_contract(callee_code)
    callee_storage = Storage()

    set_code_1 = Spec.delegation_designation(auth_signer_2)
    set_code_2 = Spec.delegation_designation(auth_signer_1)

    callee_storage[slot_ext_code_size_result_1] = len(set_code_2)
    callee_storage[slot_ext_code_hash_result_1] = keccak256(set_code_2)
    callee_storage[slot_ext_code_copy_result_1] = bytes(set_code_2).ljust(32, b"\x00")[:32]
    callee_storage[slot_ext_balance_result_1] = auth_signer_1_balance

    callee_storage[slot_ext_code_size_result_2] = len(set_code_1)
    callee_storage[slot_ext_code_hash_result_2] = keccak256(set_code_1)
    callee_storage[slot_ext_code_copy_result_2] = bytes(set_code_1).ljust(32, b"\x00")[:32]
    callee_storage[slot_ext_balance_result_2] = auth_signer_2_balance

    tx = Transaction(
        gas_limit=10_000_000,
        to=callee_address,
        authorization_list=[
            AuthorizationTuple(
                address=auth_signer_2,
                nonce=0,
                signer=auth_signer_1,
            ),
            AuthorizationTuple(
                address=auth_signer_1,
                nonce=0,
                signer=auth_signer_2,
            ),
        ],
        sender=pre.fund_eoa(),  # TODO: Test with sender as auth_signer
    )

    state_test(
        env=Environment(),
        pre=pre,
        tx=tx,
        post={
            auth_signer_1: Account(
                nonce=1,
                code=Spec.delegation_designation(auth_signer_2),
                balance=auth_signer_1_balance,
            ),
            auth_signer_2: Account(
                nonce=1,
                code=Spec.delegation_designation(auth_signer_1),
                balance=auth_signer_2_balance,
            ),
            callee_address: Account(storage=callee_storage),
        },
    )


@pytest.mark.parametrize(
    "balance",
    [0, 1],
)
def test_self_code_on_set_code(
    state_test: StateTestFiller,
    pre: Alloc,
    balance: int,
):
    """
    Test codesize and codecopy operations on a set-code address.
    """
    auth_signer = pre.fund_eoa(balance)

    slot = count(1)
    slot_code_size_result = next(slot)
    slot_code_copy_result = next(slot)
    slot_self_balance_result = next(slot)

    set_code = (
        Op.SSTORE(slot_code_size_result, Op.CODESIZE)
        + Op.CODECOPY(0, 0, Op.CODESIZE)
        + Op.SSTORE(slot_code_copy_result, Op.MLOAD(0))
        + Op.SSTORE(slot_self_balance_result, Op.SELFBALANCE)
        + Op.STOP
    )
    set_code_to_address = pre.deploy_contract(set_code)

    storage = Storage()
    storage[slot_code_size_result] = len(set_code)
    storage[slot_code_copy_result] = bytes(set_code).ljust(32, b"\x00")[:32]
    storage[slot_self_balance_result] = balance

    tx = Transaction(
        gas_limit=10_000_000,
        to=auth_signer,
        authorization_list=[
            AuthorizationTuple(
                address=set_code_to_address,
                nonce=0,
                signer=auth_signer,
            ),
        ],
        sender=pre.fund_eoa(),
    )

    state_test(
        env=Environment(),
        pre=pre,
        tx=tx,
        post={
            set_code_to_address: Account(storage={}),
            auth_signer: Account(
                nonce=1,
                code=Spec.delegation_designation(set_code_to_address),
                storage=storage,
                balance=balance,
            ),
        },
    )


@pytest.mark.with_all_create_opcodes
def test_set_code_to_account_deployed_in_same_tx(
    state_test: StateTestFiller,
    pre: Alloc,
    create_opcode: Op,
    evm_code_type: EVMCodeType,
):
    """
    Test setting the code of an account to an address that is deployed in the same transaction,
    and test calling the set-code address and the deployed contract.
    """
    auth_signer = pre.fund_eoa(auth_account_start_balance)

    success_slot = 1

    deployed_code: Bytecode | Container = Op.SSTORE(success_slot, 1) + Op.STOP
    initcode: Bytecode | Container

    if evm_code_type == EVMCodeType.LEGACY:
        initcode = Initcode(deploy_code=deployed_code)
    elif evm_code_type == EVMCodeType.EOF_V1:
        deployed_code = Container.Code(deployed_code)
        initcode = Container.Init(deploy_container=deployed_code)
    else:
        raise ValueError(f"Unsupported EVM code type: {evm_code_type}")

    deployed_contract_address_slot = 1
    signer_call_return_code_slot = 2
    deployed_contract_call_return_code_slot = 3

    salt = 0
    call_opcode = Op.CALL if evm_code_type == EVMCodeType.LEGACY else Op.EXTCALL

    if create_opcode == Op.EOFCREATE:
        create_opcode = Op.EOFCREATE[0]  # type: ignore

    contract_creator_code: Bytecode | Container = (
        Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE)  # NOOP on EOF
        + Op.SSTORE(
            deployed_contract_address_slot,
            create_opcode(offset=0, salt=salt, size=Op.CALLDATASIZE),
        )
        + Op.SSTORE(signer_call_return_code_slot, call_opcode(address=auth_signer))
        + Op.SSTORE(
            deployed_contract_call_return_code_slot,
            call_opcode(address=Op.SLOAD(deployed_contract_address_slot)),
        )
        + Op.STOP()
    )

    if evm_code_type == EVMCodeType.EOF_V1:
        contract_creator_code = Container(
            sections=[
                Section.Code(contract_creator_code),
                Section.Container(container=initcode),
            ],
        )

    contract_creator_address = pre.deploy_contract(contract_creator_code)

    deployed_contract_address = compute_create_address(
        address=contract_creator_address,
        nonce=1,
        salt=salt,
        initcode=initcode,
        opcode=create_opcode,
    )

    tx = Transaction(
        gas_limit=10_000_000,
        to=contract_creator_address,
        value=0,
        data=initcode if evm_code_type == EVMCodeType.LEGACY else b"",
        authorization_list=[
            AuthorizationTuple(
                address=deployed_contract_address,
                nonce=0,
                signer=auth_signer,
            ),
        ],
        sender=pre.fund_eoa(),
    )

    state_test(
        env=Environment(),
        pre=pre,
        tx=tx,
        post={
            deployed_contract_address: Account(
                storage={success_slot: 1},
            ),
            auth_signer: Account(
                nonce=1,
                code=Spec.delegation_designation(deployed_contract_address),
                storage={success_slot: 1},
            ),
            contract_creator_address: Account(
                storage={
                    deployed_contract_address_slot: deployed_contract_address,
                    signer_call_return_code_slot: 1,
                    deployed_contract_call_return_code_slot: 1,
                }
            ),
        },
    )


@pytest.mark.parametrize(
    "external_sendall_recipient",
    [False, True],
)
@pytest.mark.parametrize(
    "balance",
    [0, 1],
)
@pytest.mark.parametrize("call_set_code_first", [False, True])
@pytest.mark.parametrize(
    "create_opcode", [Op.CREATE, Op.CREATE2]
)  # EOF code does not support SELFDESTRUCT
def test_set_code_to_self_destructing_account_deployed_in_same_tx(
    state_test: StateTestFiller,
    pre: Alloc,
    create_opcode: Op,
    call_set_code_first: bool,
    external_sendall_recipient: bool,
    balance: int,
):
    """
    Test setting the code of an account to an account that contains the SELFDESTRUCT opcode and
    was deployed in the same transaction, and test calling the set-code address and the deployed
    in both sequence orders.
    """
    auth_signer = pre.fund_eoa(balance)
    if external_sendall_recipient:
        recipient = pre.fund_eoa(0)
    else:
        recipient = auth_signer

    success_slot = 1

    deployed_code = Op.SSTORE(success_slot, 1) + Op.SELFDESTRUCT(recipient)
    initcode = Initcode(deploy_code=deployed_code)

    deployed_contract_address_slot = 1
    signer_call_return_code_slot = 2
    deployed_contract_call_return_code_slot = 3

    salt = 0
    call_opcode = Op.CALL

    contract_creator_code: Bytecode = Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE) + Op.SSTORE(
        deployed_contract_address_slot,
        create_opcode(offset=0, salt=salt, size=Op.CALLDATASIZE),
    )
    if call_set_code_first:
        contract_creator_code += Op.SSTORE(
            signer_call_return_code_slot, call_opcode(address=auth_signer)
        ) + Op.SSTORE(
            deployed_contract_call_return_code_slot,
            call_opcode(address=Op.SLOAD(deployed_contract_address_slot)),
        )
    else:
        contract_creator_code += Op.SSTORE(
            deployed_contract_call_return_code_slot,
            call_opcode(address=Op.SLOAD(deployed_contract_address_slot)),
        ) + Op.SSTORE(signer_call_return_code_slot, call_opcode(address=auth_signer))

    contract_creator_code += Op.STOP

    contract_creator_address = pre.deploy_contract(contract_creator_code)

    deployed_contract_address = compute_create_address(
        address=contract_creator_address,
        nonce=1,
        salt=salt,
        initcode=initcode,
        opcode=create_opcode,
    )

    tx = Transaction(
        gas_limit=10_000_000,
        to=contract_creator_address,
        value=0,
        data=initcode,
        authorization_list=[
            AuthorizationTuple(
                address=deployed_contract_address,
                nonce=0,
                signer=auth_signer,
            ),
        ],
        sender=pre.fund_eoa(),
    )

    post = {
        deployed_contract_address: Account.NONEXISTENT,
        auth_signer: Account(
            nonce=1,
            code=Spec.delegation_designation(deployed_contract_address),
            storage={success_slot: 1},
            balance=balance if not external_sendall_recipient else 0,
        ),
        contract_creator_address: Account(
            storage={
                deployed_contract_address_slot: deployed_contract_address,
                signer_call_return_code_slot: 1,
                deployed_contract_call_return_code_slot: 1,
            }
        ),
    }

    if external_sendall_recipient and balance > 0:
        post[recipient] = Account(balance=balance)

    state_test(
        env=Environment(),
        pre=pre,
        tx=tx,
        post=post,
    )


def test_set_code_multiple_first_valid_authorization_tuples_same_signer(
    state_test: StateTestFiller,
    pre: Alloc,
):
    """
    Test setting the code of an account with multiple authorization tuples from the same signer.
    """
    auth_signer = pre.fund_eoa(auth_account_start_balance)

    tuple_count = 10

    success_slot = 0

    addresses = [pre.deploy_contract(Op.SSTORE(i, 1) + Op.STOP) for i in range(tuple_count)]

    tx = Transaction(
        gas_limit=10_000_000,
        to=auth_signer,
        value=0,
        authorization_list=[
            AuthorizationTuple(
                address=address,
                nonce=0,
                signer=auth_signer,
            )
            for address in addresses
        ],
        sender=pre.fund_eoa(),
    )

    state_test(
        env=Environment(),
        pre=pre,
        tx=tx,
        post={
            auth_signer: Account(
                nonce=1,
                code=Spec.delegation_designation(addresses[0]),
                storage={
                    success_slot: 1,
                },
            ),
        },
    )


def test_set_code_multiple_valid_authorization_tuples_same_signer_increasing_nonce(
    state_test: StateTestFiller,
    pre: Alloc,
):
    """
    Test setting the code of an account with multiple authorization tuples from the same signer
    and each authorization tuple has an increasing nonce, therefore the last tuple is executed.
    """
    auth_signer = pre.fund_eoa(auth_account_start_balance)

    tuple_count = 10

    success_slot = tuple_count - 1

    addresses = [pre.deploy_contract(Op.SSTORE(i, 1) + Op.STOP) for i in range(tuple_count)]

    tx = Transaction(
        gas_limit=10_000_000,  # TODO: Reduce gas limit of all tests
        to=auth_signer,
        value=0,
        authorization_list=[
            AuthorizationTuple(
                address=address,
                nonce=i,
                signer=auth_signer,
            )
            for i, address in enumerate(addresses)
        ],
        sender=pre.fund_eoa(),
    )

    state_test(
        env=Environment(),
        pre=pre,
        tx=tx,
        post={
            auth_signer: Account(
                nonce=10,
                code=Spec.delegation_designation(addresses[success_slot]),
                storage={
                    success_slot: 1,
                },
            ),
        },
    )


def test_set_code_multiple_valid_authorization_tuples_same_signer_increasing_nonce_self_sponsored(
    state_test: StateTestFiller,
    pre: Alloc,
):
    """
    Test setting the code of an account with multiple authorization tuples from the same signer
    and each authorization tuple has an increasing nonce, therefore the last tuple is executed,
    and the transaction is self-sponsored.
    """
    auth_signer = pre.fund_eoa()

    tuple_count = 10

    success_slot = tuple_count - 1

    addresses = [pre.deploy_contract(Op.SSTORE(i, 1) + Op.STOP) for i in range(tuple_count)]

    tx = Transaction(
        gas_limit=10_000_000,  # TODO: Reduce gas limit of all tests
        to=auth_signer,
        value=0,
        authorization_list=[
            AuthorizationTuple(
                address=address,
                nonce=i + 1,
                signer=auth_signer,
            )
            for i, address in enumerate(addresses)
        ],
        sender=auth_signer,
    )

    state_test(
        env=Environment(),
        pre=pre,
        tx=tx,
        post={
            auth_signer: Account(
                nonce=11,
                code=Spec.delegation_designation(addresses[success_slot]),
                storage={
                    success_slot: 1,
                },
            ),
        },
    )


def test_set_code_multiple_valid_authorization_tuples_first_invalid_same_signer(
    state_test: StateTestFiller,
    pre: Alloc,
):
    """
    Test setting the code of an account with multiple authorization tuples from the same signer
    but the first tuple is invalid.
    """
    auth_signer = pre.fund_eoa(auth_account_start_balance)

    success_slot = 1

    tuple_count = 10

    addresses = [pre.deploy_contract(Op.SSTORE(i, 1) + Op.STOP) for i in range(tuple_count)]

    tx = Transaction(
        gas_limit=10_000_000,
        to=auth_signer,
        value=0,
        authorization_list=[
            AuthorizationTuple(
                address=address,
                nonce=1 if i == 0 else 0,
                signer=auth_signer,
            )
            for i, address in enumerate(addresses)
        ],
        sender=pre.fund_eoa(),
    )

    state_test(
        env=Environment(),
        pre=pre,
        tx=tx,
        post={
            auth_signer: Account(
                nonce=1,
                code=Spec.delegation_designation(addresses[1]),
                storage={
                    success_slot: 1,
                },
            ),
        },
    )


def test_set_code_all_invalid_authorization_tuples(
    state_test: StateTestFiller,
    pre: Alloc,
):
    """
    Test setting the code of an account with multiple authorization tuples from the same signer
    and all of them are invalid.
    """
    auth_signer = pre.fund_eoa(auth_account_start_balance)

    tuple_count = 10

    addresses = [pre.deploy_contract(Op.SSTORE(i, 1) + Op.STOP) for i in range(tuple_count)]

    tx = Transaction(
        gas_limit=10_000_000,
        to=auth_signer,
        value=0,
        authorization_list=[
            AuthorizationTuple(
                address=address,
                nonce=1,
                signer=auth_signer,
            )
            for _, address in enumerate(addresses)
        ],
        sender=pre.fund_eoa(),
    )

    state_test(
        env=Environment(),
        pre=pre,
        tx=tx,
        post={
            auth_signer: Account.NONEXISTENT,
        },
    )


class InvalidityReason(Enum):
    """
    Reasons for invalidity of a set-code transaction.
    """

    NONCE = "nonce"
    MULTIPLE_NONCE = "multiple_nonce"
    CHAIN_ID = "chain_id"
    EMPTY_AUTHORIZATION_LIST = "empty_authorization_list"
    INVALID_SIGNATURE_S_VALUE = "invalid_signature_s_value"  # TODO: Implement


@pytest.mark.parametrize(
    "invalidity_reason,transaction_exception",
    [
        pytest.param(
            InvalidityReason.NONCE,
            None,  # Transaction is valid and accepted, but no authorization tuple is processed
        ),
        pytest.param(
            InvalidityReason.MULTIPLE_NONCE,
            None,
            marks=pytest.mark.xfail(reason="test issue"),
        ),
        pytest.param(
            InvalidityReason.CHAIN_ID,
            None,  # Transaction is valid and accepted, but no authorization tuple is processed
        ),
        pytest.param(
            InvalidityReason.EMPTY_AUTHORIZATION_LIST,
            TransactionException.TYPE_4_EMPTY_AUTHORIZATION_LIST,
        ),
    ],
)
def test_set_code_invalid_authorization_tuple(
    state_test: StateTestFiller,
    pre: Alloc,
    invalidity_reason: InvalidityReason,
    transaction_exception: TransactionException | None,
):
    """
    Test attempting to set the code of an account with invalid authorization tuple.
    """
    auth_signer = pre.fund_eoa(auth_account_start_balance)

    success_slot = 1

    set_code = Op.SSTORE(success_slot, 1) + Op.STOP
    set_code_to_address = pre.deploy_contract(set_code)

    authorization_list: List[AuthorizationTuple] = []

    if invalidity_reason != InvalidityReason.EMPTY_AUTHORIZATION_LIST:
        authorization_list = [
            AuthorizationTuple(
                address=set_code_to_address,
                nonce=(
                    1
                    if invalidity_reason == InvalidityReason.NONCE
                    else [0, 1]
                    if invalidity_reason == InvalidityReason.MULTIPLE_NONCE
                    else 0
                ),
                chain_id=2 if invalidity_reason == InvalidityReason.CHAIN_ID else 0,
                signer=auth_signer,
            )
        ]

    tx = Transaction(
        gas_limit=10_000_000,
        to=auth_signer,
        value=0,
        authorization_list=authorization_list,
        error=transaction_exception,
        sender=pre.fund_eoa(),
    )

    state_test(
        env=Environment(),
        pre=pre,
        tx=tx,
        post={
            auth_signer: Account.NONEXISTENT,
        },
    )


def test_set_code_using_chain_specific_id(
    state_test: StateTestFiller,
    pre: Alloc,
):
    """
    Test sending a transaction to set the code of an account using a chain-specific ID.
    """
    auth_signer = pre.fund_eoa(auth_account_start_balance)

    success_slot = 1

    set_code = Op.SSTORE(success_slot, 1) + Op.STOP
    set_code_to_address = pre.deploy_contract(set_code)

    tx = Transaction(
        gas_limit=100_000,
        to=auth_signer,
        value=0,
        authorization_list=[
            AuthorizationTuple(
                address=set_code_to_address,
                nonce=0,
                chain_id=1,
                signer=auth_signer,
            )
        ],
        sender=pre.fund_eoa(),
    )

    state_test(
        env=Environment(),
        pre=pre,
        tx=tx,
        post={
            auth_signer: Account(
                nonce=1,
                code=Spec.delegation_designation(set_code_to_address),
                storage={
                    success_slot: 1,
                },
            ),
        },
    )


SECP256K1N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
SECP256K1N_OVER_2 = SECP256K1N // 2


@pytest.mark.parametrize(
    "v,r,s",
    [
        pytest.param(0, 1, 1, id="v=0,r=1,s=1"),
        pytest.param(1, 1, 1, id="v=1,r=1,s=1"),
        pytest.param(
            2, 1, 1, id="v=2,r=1,s=1", marks=pytest.mark.xfail(reason="invalid signature")
        ),
        pytest.param(
            1, 0, 1, id="v=1,r=0,s=1", marks=pytest.mark.xfail(reason="invalid signature")
        ),
        pytest.param(
            1, 1, 0, id="v=1,r=1,s=0", marks=pytest.mark.xfail(reason="invalid signature")
        ),
        pytest.param(
            0,
            SECP256K1N - 0,
            1,
            id="v=0,r=SECP256K1N,s=1",
            marks=pytest.mark.xfail(reason="invalid signature"),
        ),
        pytest.param(
            0,
            SECP256K1N - 1,
            1,
            id="v=0,r=SECP256K1N-1,s=1",
            marks=pytest.mark.xfail(reason="invalid signature"),
        ),
        pytest.param(0, SECP256K1N - 2, 1, id="v=0,r=SECP256K1N-2,s=1"),
        pytest.param(1, SECP256K1N - 2, 1, id="v=1,r=SECP256K1N-2,s=1"),
        pytest.param(0, 1, SECP256K1N_OVER_2, id="v=0,r=1,s=SECP256K1N_OVER_2"),
        pytest.param(1, 1, SECP256K1N_OVER_2, id="v=1,r=1,s=SECP256K1N_OVER_2"),
        pytest.param(
            0,
            1,
            SECP256K1N_OVER_2 + 1,
            id="v=0,r=1,s=SECP256K1N_OVER_2+1",
            marks=pytest.mark.xfail(reason="invalid signature"),
        ),
    ],
)
def test_set_code_using_valid_synthetic_signatures(
    state_test: StateTestFiller,
    pre: Alloc,
    v: int,
    r: int,
    s: int,
):
    """
    Test sending a transaction to set the code of an account using synthetic signatures.
    """
    success_slot = 1

    set_code = Op.SSTORE(success_slot, 1) + Op.STOP
    set_code_to_address = pre.deploy_contract(set_code)

    authorization_tuple = AuthorizationTuple(
        address=set_code_to_address,
        nonce=0,
        chain_id=1,
        v=v,
        r=r,
        s=s,
    )

    auth_signer = authorization_tuple.signer

    tx = Transaction(
        gas_limit=100_000,
        to=auth_signer,
        value=0,
        authorization_list=[authorization_tuple],
        sender=pre.fund_eoa(),
    )

    state_test(
        env=Environment(),
        pre=pre,
        tx=tx,
        post={
            auth_signer: Account(
                nonce=1,
                code=Spec.delegation_designation(set_code_to_address),
                storage={
                    success_slot: 1,
                },
            ),
        },
    )


# TODO: invalid RLP in the rest of the authority tuple fields
@pytest.mark.parametrize(
    "v,r,s",
    [
        pytest.param(2, 1, 1, id="v_2,r_1,s_1"),
        pytest.param(
            0,
            1,
            SECP256K1N_OVER_2 + 1,
            id="v_0,r_1,s_SECP256K1N_OVER_2+1",
        ),
        pytest.param(
            2**256 - 1,
            1,
            1,
            id="v_2**256-1,r_1,s_1",
        ),
        pytest.param(
            0,
            1,
            2**256 - 1,
            id="v_0,r_1,s_2**256-1",
        ),
    ],
)
def test_invalid_tx_invalid_auth_signature(
    state_test: StateTestFiller,
    pre: Alloc,
    v: int,
    r: int,
    s: int,
):
    """
    Test sending a transaction to set the code of an account using synthetic signatures.
    """
    success_slot = 1

    callee_code = Op.SSTORE(success_slot, 1) + Op.STOP
    callee_address = pre.deploy_contract(callee_code)

    authorization_tuple = AuthorizationTuple(
        address=0,
        nonce=0,
        chain_id=1,
        v=v,
        r=r,
        s=s,
    )

    tx = Transaction(
        gas_limit=100_000,
        to=callee_address,
        value=0,
        authorization_list=[authorization_tuple],
        error=TransactionException.TYPE_4_INVALID_AUTHORITY_SIGNATURE,
        sender=pre.fund_eoa(),
    )

    state_test(
        env=Environment(),
        pre=pre,
        tx=tx,
        post={
            callee_address: Account(
                storage={success_slot: 0},
            ),
        },
    )


@pytest.mark.parametrize(
    "v,r,s",
    [
        pytest.param(1, 0, 1, id="v_1,r_0,s_1"),
        pytest.param(1, 1, 0, id="v_1,r_1,s_0"),
        pytest.param(
            0,
            SECP256K1N,
            1,
            id="v_0,r_SECP256K1N,s_1",
        ),
        pytest.param(
            0,
            SECP256K1N - 1,
            1,
            id="v_0,r_SECP256K1N-1,s_1",
        ),
        pytest.param(
            0,
            1,
            SECP256K1N_OVER_2,
            id="v_0,r_1,s_SECP256K1N_OVER_2",
        ),
        pytest.param(
            0,
            1,
            SECP256K1N_OVER_2 - 1,
            id="v_0,r_1,s_SECP256K1N_OVER_2_minus_one",
        ),
        pytest.param(
            1,
            2**256 - 1,
            1,
            id="v_1,r_2**256-1,s_1",
        ),
    ],
)
def test_set_code_using_invalid_signatures(
    state_test: StateTestFiller,
    pre: Alloc,
    v: int,
    r: int,
    s: int,
):
    """
    Test sending a transaction to set the code of an account using synthetic signatures,
    the transaction is valid but the authorization should not go through.
    """
    success_slot = 1

    callee_code = Op.SSTORE(success_slot, 1) + Op.STOP
    callee_address = pre.deploy_contract(callee_code)

    authorization_tuple = AuthorizationTuple(
        address=0,
        nonce=0,
        chain_id=1,
        v=v,
        r=r,
        s=s,
    )

    tx = Transaction(
        gas_limit=100_000,
        to=callee_address,
        value=0,
        authorization_list=[authorization_tuple],
        sender=pre.fund_eoa(),
    )

    state_test(
        env=Environment(),
        pre=pre,
        tx=tx,
        post={
            callee_address: Account(
                storage={success_slot: 1},
            ),
        },
    )


@pytest.mark.parametrize(
    "log_opcode",
    [
        Op.LOG0,
        Op.LOG1,
        Op.LOG2,
        Op.LOG3,
        Op.LOG4,
    ],
)
@pytest.mark.with_all_evm_code_types
def test_set_code_to_log(
    state_test: StateTestFiller,
    pre: Alloc,
    log_opcode: Op,
):
    """
    Test setting the code of an account to a contract that performs the log operation.
    """
    sender = pre.fund_eoa()

    set_to_code = (
        Op.MSTORE(0, 0x1234)
        + log_opcode(size=32, topic_1=1, topic_2=2, topic_3=3, topic_4=4)
        + Op.STOP
    )
    set_to_address = pre.deploy_contract(set_to_code)

    tx = Transaction(
        gas_limit=10_000_000,
        to=sender,
        value=0,
        authorization_list=[
            AuthorizationTuple(
                address=set_to_address,
                nonce=1,
                signer=sender,
            ),
        ],
        sender=sender,
    )

    state_test(
        env=Environment(),
        pre=pre,
        tx=tx,
        post={
            sender: Account(
                nonce=2,
                code=Spec.delegation_designation(set_to_address),
            ),
        },
    )


@pytest.mark.with_all_call_opcodes(
    selector=(
        lambda opcode: opcode
        not in [Op.STATICCALL, Op.CALLCODE, Op.DELEGATECALL, Op.EXTDELEGATECALL, Op.EXTSTATICCALL]
    )
)
@pytest.mark.with_all_precompiles
def test_set_code_to_precompile(
    state_test: StateTestFiller,
    pre: Alloc,
    precompile: int,
    call_opcode: Op,
):
    """
    Test setting the code of an account to a pre-compile address.
    """
    auth_signer = pre.fund_eoa(auth_account_start_balance)

    caller_code_storage = Storage()
    caller_code = (
        Op.SSTORE(
            caller_code_storage.store_next(call_return_code(opcode=call_opcode, success=True)),
            call_opcode(address=auth_signer),
        )
        + Op.SSTORE(caller_code_storage.store_next(0), Op.RETURNDATASIZE)
        + Op.STOP
    )
    caller_code_address = pre.deploy_contract(caller_code)

    tx = Transaction(
        sender=pre.fund_eoa(),
        gas_limit=500_000,
        to=caller_code_address,
        authorization_list=[
            AuthorizationTuple(
                address=Address(precompile),
                nonce=0,
                signer=auth_signer,
            ),
        ],
    )

    state_test(
        env=Environment(),
        pre=pre,
        tx=tx,
        post={
            auth_signer: Account(
                nonce=1,
                code=Spec.delegation_designation(Address(precompile)),
            ),
            caller_code_address: Account(
                storage=caller_code_storage,
            ),
        },
    )


def deposit_contract_initial_storage() -> Storage:
    """
    Return the initial storage of the deposit contract.
    """
    storage = Storage()
    DEPOSIT_CONTRACT_TREE_DEPTH = 32
    next_hash = sha256(b"\x00" * 64).digest()
    for i in range(DEPOSIT_CONTRACT_TREE_DEPTH + 2, DEPOSIT_CONTRACT_TREE_DEPTH * 2 + 1):
        storage[i] = next_hash
        next_hash = sha256(next_hash + next_hash).digest()
    return storage


@pytest.mark.with_all_call_opcodes(
    selector=(
        lambda opcode: opcode
        not in [Op.STATICCALL, Op.CALLCODE, Op.DELEGATECALL, Op.EXTDELEGATECALL, Op.EXTSTATICCALL]
    )
)
@pytest.mark.with_all_system_contracts
def test_set_code_to_system_contract(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    system_contract: int,
    call_opcode: Op,
):
    """
    Test setting the code of an account to a pre-compile address.
    """
    caller_code_storage = Storage()
    call_return_code_slot = caller_code_storage.store_next(
        call_return_code(
            opcode=call_opcode,
            success=True,
        )
    )
    call_return_data_size_slot = caller_code_storage.store_next(0)

    call_value = 0

    # Setup the initial storage of the account to mimic the system contract if required
    match system_contract:
        case Address(0x00000000219AB540356CBB839CBE05303D7705FA):  # EIP-6110
            # Deposit contract needs specific storage values, so we set them on the account
            auth_signer = pre.fund_eoa(
                auth_account_start_balance, storage=deposit_contract_initial_storage()
            )
        case Address(0x000F3DF6D732807EF1319FB7B8BB8522D0BEAC02):  # EIP-4788
            auth_signer = pre.fund_eoa(auth_account_start_balance, storage=Storage({1: 1}))
        case _:
            # Pre-fund without storage
            auth_signer = pre.fund_eoa(auth_account_start_balance)

    # Fabricate the payload for the system contract
    match system_contract:
        case Address(0x000F3DF6D732807EF1319FB7B8BB8522D0BEAC02):  # EIP-4788
            caller_payload = Hash(1)
            caller_code_storage[call_return_data_size_slot] = 32
        case Address(0x00000000219AB540356CBB839CBE05303D7705FA):  # EIP-6110
            # Fabricate a valid deposit request to the set-code account
            deposit_request = DepositRequest(
                pubkey=0x01,
                withdrawal_credentials=0x02,
                amount=1_000_000_000,
                signature=0x03,
                index=0x0,
            )
            caller_payload = deposit_request.calldata
            call_value = deposit_request.value
        case Address(0x00A3CA265EBCB825B45F985A16CEFB49958CE017):  # EIP-7002
            # Fabricate a valid withdrawal request to the set-code account
            withdrawal_request = WithdrawalRequest(
                source_address=0x01,
                validator_pubkey=0x02,
                amount=0x03,
                fee=0x01,
            )
            caller_payload = withdrawal_request.calldata
            call_value = withdrawal_request.value
        case Address(0x00B42DBF2194E931E80326D950320F7D9DBEAC02):  # EIP-7251
            # Fabricate a valid consolidation request to the set-code account
            consolidation_request = ConsolidationRequest(
                source_address=0x01,
                source_pubkey=0x02,
                target_pubkey=0x03,
                fee=0x01,
            )
            caller_payload = consolidation_request.calldata
            call_value = consolidation_request.value
        case Address(0x0AAE40965E6800CD9B1F4B05FF21581047E3F91E):  # EIP-2935
            caller_payload = Hash(0)
            caller_code_storage[call_return_data_size_slot] = 32
        case _:
            raise ValueError(f"Not implemented system contract: {system_contract}")

    caller_code = (
        Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE)
        + Op.SSTORE(
            call_return_code_slot,
            call_opcode(address=auth_signer, value=call_value, args_size=Op.CALLDATASIZE),
        )
        + Op.SSTORE(call_return_data_size_slot, Op.RETURNDATASIZE)
        + Op.STOP
    )
    caller_code_address = pre.deploy_contract(caller_code)

    txs = [
        Transaction(
            sender=pre.fund_eoa(),
            gas_limit=500_000,
            to=caller_code_address,
            value=call_value,
            data=caller_payload,
            authorization_list=[
                AuthorizationTuple(
                    address=Address(system_contract),
                    nonce=auth_signer.nonce,
                    signer=auth_signer,
                ),
            ],
        )
    ]

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=txs,
                requests_root=[],  # Verify nothing slipped into the requests trie
            )
        ],
        post={
            auth_signer: Account(
                nonce=auth_signer.nonce + 1,
                code=Spec.delegation_designation(Address(system_contract)),
            ),
            caller_code_address: Account(
                storage=caller_code_storage,
            ),
        },
    )


@pytest.mark.with_all_evm_code_types
@pytest.mark.with_all_tx_types(selector=lambda tx_type: tx_type != 4)
def test_eoa_tx_after_set_code(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    tx_type: int,
    evm_code_type: EVMCodeType,
):
    """
    Test sending a transaction from an EOA after code has been set to the account.
    """
    auth_signer = pre.fund_eoa()

    set_code = Op.SSTORE(1, Op.ADD(Op.SLOAD(1), 1)) + Op.STOP
    set_code_to_address = pre.deploy_contract(set_code)

    txs = [
        Transaction(
            sender=pre.fund_eoa(),
            gas_limit=500_000,
            to=auth_signer,
            value=0,
            authorization_list=[
                AuthorizationTuple(
                    address=set_code_to_address,
                    nonce=0,
                    signer=auth_signer,
                ),
            ],
        )
    ]
    auth_signer.nonce += 1  # type: ignore

    match tx_type:
        case 0:
            txs.append(
                Transaction(
                    type=tx_type,
                    sender=auth_signer,
                    gas_limit=500_000,
                    to=auth_signer,
                    value=0,
                    protected=True,
                ),
            )
            txs.append(
                Transaction(
                    type=tx_type,
                    sender=auth_signer,
                    gas_limit=500_000,
                    to=auth_signer,
                    value=0,
                    protected=False,
                ),
            )
        case 1:
            txs.append(
                Transaction(
                    type=tx_type,
                    sender=auth_signer,
                    gas_limit=500_000,
                    to=auth_signer,
                    value=0,
                    access_list=[
                        AccessList(
                            address=auth_signer,
                            storage_keys=[1],
                        )
                    ],
                ),
            )
        case 2:
            txs.append(
                Transaction(
                    type=tx_type,
                    sender=auth_signer,
                    gas_limit=500_000,
                    to=auth_signer,
                    value=0,
                    max_fee_per_gas=1_000,
                    max_priority_fee_per_gas=1_000,
                ),
            )
        case 3:
            txs.append(
                Transaction(
                    type=tx_type,
                    sender=auth_signer,
                    gas_limit=500_000,
                    to=auth_signer,
                    value=0,
                    max_fee_per_gas=1_000,
                    max_priority_fee_per_gas=1_000,
                    max_fee_per_blob_gas=1_000,
                    blob_versioned_hashes=add_kzg_version(
                        [Hash(1)],
                        Spec4844.BLOB_COMMITMENT_VERSION_KZG,
                    ),
                ),
            )
        case _:
            raise ValueError(f"Unsupported tx type: {tx_type}, test needs update")

    blockchain_test(
        pre=pre,
        blocks=[Block(txs=txs)],
        post={
            auth_signer: Account(
                nonce=3 if tx_type == 0 else 2,
                code=Spec.delegation_designation(set_code_to_address),
                storage={1: 3 if tx_type == 0 else 2},
            ),
        },
    )


@pytest.mark.parametrize(
    "self_sponsored",
    [
        pytest.param(False, id="not_self_sponsored"),
        pytest.param(True, id="self_sponsored"),
    ],
)
def test_reset_code(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    self_sponsored: bool,
):
    """
    Test sending type-4 tx to reset the code of an account after code has been set to the account.
    """
    auth_signer = pre.fund_eoa()

    set_code_1 = Op.SSTORE(1, Op.ADD(Op.SLOAD(1), 1)) + Op.STOP
    set_code_1_address = pre.deploy_contract(set_code_1)

    set_code_2 = Op.SSTORE(2, Op.ADD(Op.SLOAD(2), 1)) + Op.STOP
    set_code_2_address = pre.deploy_contract(set_code_2)

    sender = pre.fund_eoa()

    txs = [
        Transaction(
            sender=sender,
            gas_limit=500_000,
            to=auth_signer,
            value=0,
            authorization_list=[
                AuthorizationTuple(
                    address=set_code_1_address,
                    nonce=0,
                    signer=auth_signer,
                ),
            ],
        )
    ]

    auth_signer.nonce += 1  # type: ignore

    if self_sponsored:
        sender = auth_signer

    txs.append(
        Transaction(
            sender=sender,
            gas_limit=500_000,
            to=auth_signer,
            value=0,
            authorization_list=[
                AuthorizationTuple(
                    address=set_code_2_address,
                    nonce=auth_signer.nonce + 1 if self_sponsored else auth_signer.nonce,
                    signer=auth_signer,
                ),
            ],
        ),
    )

    blockchain_test(
        pre=pre,
        blocks=[Block(txs=txs)],
        post={
            auth_signer: Account(
                nonce=3 if self_sponsored else 2,
                code=Spec.delegation_designation(set_code_2_address),
                storage={1: 1, 2: 1},
            ),
        },
    )
