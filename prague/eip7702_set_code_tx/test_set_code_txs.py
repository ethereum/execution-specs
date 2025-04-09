"""
abstract: Tests use of set-code transactions from [EIP-7702: Set EOA account code for one transaction](https://eips.ethereum.org/EIPS/eip-7702)
    Tests use of set-code transactions from [EIP-7702: Set EOA account code for one transaction](https://eips.ethereum.org/EIPS/eip-7702).
"""  # noqa: E501

from hashlib import sha256
from itertools import count
from typing import List

import pytest

from ethereum_test_base_types import HexNumber
from ethereum_test_forks import Fork
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
    Requests,
    StateTestFiller,
    Storage,
    Transaction,
    TransactionException,
    add_kzg_version,
    call_return_code,
    compute_create_address,
)
from ethereum_test_tools import Macros as Om
from ethereum_test_tools import Opcodes as Op
from ethereum_test_tools.eof.v1 import Container, Section
from ethereum_test_types import TransactionReceipt

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
    """Test the executing a simple SSTORE in a set-code transaction."""
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


def test_set_code_to_non_empty_storage_non_zero_nonce(
    state_test: StateTestFiller,
    pre: Alloc,
):
    """Test the setting the code to an account that has non-empty storage."""
    auth_signer = pre.fund_eoa(
        amount=0,
        storage=Storage({0: 1}),  # type: ignore
    )
    sender = pre.fund_eoa()

    set_code = Op.SSTORE(0, Op.ADD(Op.SLOAD(0), 1)) + Op.STOP
    set_code_to_address = pre.deploy_contract(
        set_code,
    )

    tx = Transaction(
        gas_limit=500_000,
        to=auth_signer,
        value=0,
        authorization_list=[
            AuthorizationTuple(
                address=set_code_to_address,
                nonce=auth_signer.nonce,
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
                storage={},
            ),
            auth_signer: Account(
                storage={0: 2},
            ),
        },
    )


def test_set_code_to_sstore_then_sload(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
):
    """Test the executing a simple SSTORE then SLOAD in two separate set-code transactions."""
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
    """Test the executing self-destruct opcode in a set-code transaction."""
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
    """Test the executing a contract-creating opcode in a set-code transaction."""
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
    """Test the executing a self-call in a set-code transaction."""
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


@pytest.mark.execute(pytest.mark.skip(reason="excessive gas"))
def test_set_code_max_depth_call_stack(
    state_test: StateTestFiller,
    pre: Alloc,
):
    """Test re-entry to delegated account until the max call stack depth is reached."""
    storage = Storage()
    auth_signer = pre.fund_eoa(auth_account_start_balance)
    set_code = Conditional(
        condition=Op.ISZERO(Op.TLOAD(0)),
        if_true=Op.TSTORE(0, 1)
        + Op.CALL(address=auth_signer)
        + Op.SSTORE(storage.store_next(1025), Op.TLOAD(0)),
        if_false=Op.TSTORE(0, Op.ADD(1, Op.TLOAD(0))) + Op.CALL(address=auth_signer),
    )
    set_code_to_address = pre.deploy_contract(set_code)

    tx = Transaction(
        gas_limit=100_000_000_000_000,
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
                balance=auth_account_start_balance,
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
    """Test the calling a set-code account from another set-code account."""
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
    """Test the address opcode in a set-code transaction."""
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
    """Test a transaction that has entry-point into a set-code account that delegates to itself."""
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
    Test a transaction that has entry-point into a set-code account that delegates to another
    set-code account.
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
    """Test call into a set-code account that delegates to itself."""
    auth_signer = pre.fund_eoa(auth_account_start_balance)

    storage = Storage()
    entry_code = (
        Op.SSTORE(
            storage.store_next(
                call_return_code(
                    opcode=call_opcode,
                    success=False,
                    revert=(call_opcode == Op.EXTDELEGATECALL),
                )
            ),
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
    """Test call into a set-code account that delegates to another set-code account."""
    auth_signer_1 = pre.fund_eoa(auth_account_start_balance)
    auth_signer_2 = pre.fund_eoa(auth_account_start_balance)

    storage = Storage()
    entry_code = (
        Op.SSTORE(
            storage.store_next(
                call_return_code(
                    opcode=call_opcode,
                    success=False,
                    revert=(call_opcode == Op.EXTDELEGATECALL),
                )
            ),
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
    """Test different ext*code operations on a set-code address."""
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
    callee_storage[slot_ext_code_size_result] = len(
        Spec.delegation_designation(set_code_to_address)
    )
    callee_storage[slot_ext_code_hash_result] = Spec.delegation_designation(
        set_code_to_address
    ).keccak256()
    callee_storage[slot_ext_code_copy_result] = Hash(
        Spec.delegation_designation(set_code_to_address), right_padding=True
    )
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
    """Test different ext*code operations on self set-code address."""
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
    set_code_storage[slot_ext_code_size_result] = len(
        Spec.delegation_designation(set_code_address)
    )
    set_code_storage[slot_ext_code_hash_result] = Spec.delegation_designation(
        set_code_address
    ).keccak256()
    set_code_storage[slot_ext_code_copy_result] = Hash(
        Spec.delegation_designation(set_code_address), right_padding=True
    )
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


@pytest.mark.with_all_evm_code_types()
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

    call_opcode = Op.CALL
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

    callee_address = pre.deploy_contract(callee_code, evm_code_type=EVMCodeType.LEGACY)
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


@pytest.mark.with_all_call_opcodes()
@pytest.mark.parametrize(
    "set_code_address_first",
    [
        pytest.param(True, id="call_set_code_address_first_then_authority"),
        pytest.param(False, id="call_authority_first_then_set_code_address"),
    ],
)
def test_set_code_address_and_authority_warm_state_call_types(
    state_test: StateTestFiller,
    pre: Alloc,
    call_opcode: Op,
    set_code_address_first: bool,
):
    """
    Test set to code address and authority warm status after a call to
    authority address, or viceversa, using all available call opcodes
    without using `GAS` opcode (unavailable in EOF).
    """
    auth_signer = pre.fund_eoa(auth_account_start_balance)

    slot = count(1)
    slot_call_return_code = next(slot)
    slot_call_success = next(slot)

    set_code = Op.STOP
    set_code_to_address = pre.deploy_contract(set_code)

    call_set_code_to_address = Op.SSTORE(
        slot_call_return_code, call_opcode(address=set_code_to_address)
    )
    call_authority_address = Op.SSTORE(slot_call_return_code, call_opcode(address=auth_signer))

    callee_code = Bytecode()
    if set_code_address_first:
        callee_code += call_set_code_to_address + call_authority_address
    else:
        callee_code += call_authority_address + call_set_code_to_address
    callee_code += Op.SSTORE(slot_call_success, 1) + Op.STOP

    callee_address = pre.deploy_contract(callee_code)
    callee_storage = Storage()
    callee_storage[slot_call_return_code] = call_return_code(opcode=call_opcode, success=True)
    callee_storage[slot_call_success] = 1

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
    """Test different ext*code operations on a set-code address that delegates to itself."""
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

    callee_storage[slot_ext_code_size_result] = len(Spec.delegation_designation(auth_signer))
    callee_storage[slot_ext_code_hash_result] = Spec.delegation_designation(
        auth_signer
    ).keccak256()
    callee_storage[slot_ext_code_copy_result] = Hash(
        Spec.delegation_designation(auth_signer), right_padding=True
    )
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

    callee_storage[slot_ext_code_size_result_1] = len(Spec.delegation_designation(auth_signer_2))
    callee_storage[slot_ext_code_hash_result_1] = Spec.delegation_designation(
        auth_signer_2
    ).keccak256()
    callee_storage[slot_ext_code_copy_result_1] = Hash(
        Spec.delegation_designation(auth_signer_2), right_padding=True
    )
    callee_storage[slot_ext_balance_result_1] = auth_signer_1_balance

    callee_storage[slot_ext_code_size_result_2] = len(Spec.delegation_designation(auth_signer_1))
    callee_storage[slot_ext_code_hash_result_2] = Spec.delegation_designation(
        auth_signer_1
    ).keccak256()
    callee_storage[slot_ext_code_copy_result_2] = Hash(
        Spec.delegation_designation(auth_signer_1), right_padding=True
    )
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
    """Test codesize and codecopy operations on a set-code address."""
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
    Test setting the code of an account with multiple authorization tuples
    from the same signer.
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


def test_set_code_using_chain_specific_id(
    state_test: StateTestFiller,
    pre: Alloc,
):
    """Test sending a transaction to set the code of an account using a chain-specific ID."""
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
        pytest.param(0, SECP256K1N - 2, 1, id="v=0,r=SECP256K1N-2,s=1"),
        pytest.param(1, SECP256K1N - 2, 1, id="v=1,r=SECP256K1N-2,s=1"),
        pytest.param(0, 1, SECP256K1N_OVER_2, id="v=0,r=1,s=SECP256K1N_OVER_2"),
        pytest.param(1, 1, SECP256K1N_OVER_2, id="v=1,r=1,s=SECP256K1N_OVER_2"),
    ],
)
def test_set_code_using_valid_synthetic_signatures(
    state_test: StateTestFiller,
    pre: Alloc,
    v: int,
    r: int,
    s: int,
):
    """Test sending a transaction to set the code of an account using synthetic signatures."""
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


@pytest.mark.parametrize(
    "v,r,s",
    [
        # V
        pytest.param(2, 1, 1, id="v=2"),
        pytest.param(27, 1, 1, id="v=27"),  # Type-0 transaction valid value
        pytest.param(28, 1, 1, id="v=28"),  # Type-0 transaction valid value
        pytest.param(35, 1, 1, id="v=35"),  # Type-0 replay-protected transaction valid value
        pytest.param(36, 1, 1, id="v=36"),  # Type-0 replay-protected transaction valid value
        pytest.param(2**8 - 1, 1, 1, id="v=2**8-1"),
        # R
        pytest.param(1, 0, 1, id="r=0"),
        pytest.param(0, SECP256K1N - 1, 1, id="r=SECP256K1N-1"),
        pytest.param(0, SECP256K1N, 1, id="r=SECP256K1N"),
        pytest.param(0, SECP256K1N + 1, 1, id="r=SECP256K1N+1"),
        pytest.param(1, 2**256 - 1, 1, id="r=2**256-1"),
        # S
        pytest.param(1, 1, 0, id="s=0"),
        pytest.param(0, 1, SECP256K1N_OVER_2 - 1, id="s=SECP256K1N_OVER_2-1"),
        pytest.param(0, 1, SECP256K1N_OVER_2, id="s=SECP256K1N_OVER_2"),
        pytest.param(0, 1, SECP256K1N_OVER_2 + 1, id="s=SECP256K1N_OVER_2+1"),
        pytest.param(0, 1, SECP256K1N - 1, id="s=SECP256K1N-1"),
        pytest.param(0, 1, SECP256K1N, id="s=SECP256K1N"),
        pytest.param(0, 1, SECP256K1N + 1, id="s=SECP256K1N+1"),
        pytest.param(0, 1, 2**256 - 1, id="s=2**256-1"),
        # All Values
        pytest.param(0, 0, 0, id="v=r=s=0"),
        pytest.param(2**8 - 1, 2**256 - 1, 2**256 - 1, id="v=2**8-1,r=s=2**256-1"),
    ],
)
def test_valid_tx_invalid_auth_signature(
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


def test_signature_s_out_of_range(
    state_test: StateTestFiller,
    pre: Alloc,
):
    """
    Test sending a transaction with an authorization tuple where the signature s value is out of
    range by modifying its value to be `SECP256K1N - S` and flipping the v value.
    """
    auth_signer = pre.fund_eoa(0)

    set_code = Op.STOP
    set_code_to_address = pre.deploy_contract(set_code)

    authorization_tuple = AuthorizationTuple(
        address=set_code_to_address,
        nonce=0,
        chain_id=1,
        signer=auth_signer,
    )

    authorization_tuple.s = HexNumber(SECP256K1N - authorization_tuple.s)
    authorization_tuple.v = HexNumber(1 - authorization_tuple.v)

    assert authorization_tuple.s > SECP256K1N_OVER_2

    success_slot = 1
    entry_code = Op.SSTORE(success_slot, 1) + Op.STOP
    entry_address = pre.deploy_contract(entry_code)

    tx = Transaction(
        gas_limit=100_000,
        to=entry_address,
        value=0,
        authorization_list=[authorization_tuple],
        sender=pre.fund_eoa(),
    )

    state_test(
        env=Environment(),
        pre=pre,
        tx=tx,
        post={
            auth_signer: Account.NONEXISTENT,
            entry_address: Account(
                storage={success_slot: 1},
            ),
        },
    )


@pytest.mark.parametrize(
    "auth_chain_id",
    [
        pytest.param(Spec.MAX_AUTH_CHAIN_ID, id="auth_chain_id=2**256-1"),
        pytest.param(2, id="chain_id=2"),
    ],
)
def test_valid_tx_invalid_chain_id(
    state_test: StateTestFiller,
    pre: Alloc,
    auth_chain_id: int,
):
    """
    Test sending a transaction where the chain id field does not match
    the current chain's id.
    """
    auth_signer = pre.fund_eoa(auth_account_start_balance)

    success_slot = 1
    return_slot = 2

    set_code = Op.RETURN(0, 1)
    set_code_to_address = pre.deploy_contract(set_code)

    authorization = AuthorizationTuple(
        address=set_code_to_address,
        nonce=0,
        chain_id=auth_chain_id,
        signer=auth_signer,
    )

    entry_code = (
        Op.SSTORE(success_slot, 1)
        + Op.CALL(address=auth_signer)
        + Op.SSTORE(return_slot, Op.RETURNDATASIZE)
    )
    entry_address = pre.deploy_contract(entry_code)

    tx = Transaction(
        gas_limit=100_000,
        to=entry_address,
        value=0,
        authorization_list=[authorization],
        error=None,
        sender=pre.fund_eoa(),
    )

    state_test(
        env=Environment(),
        pre=pre,
        tx=tx,
        post={
            auth_signer: Account.NONEXISTENT,
            entry_address: Account(
                storage={
                    success_slot: 1,
                    return_slot: 0,
                },
            ),
        },
    )


@pytest.mark.parametrize(
    "account_nonce,authorization_nonce",
    [
        pytest.param(
            Spec.MAX_NONCE,
            Spec.MAX_NONCE,
            id="nonce=2**64-1",
            marks=pytest.mark.execute(pytest.mark.skip(reason="Impossible account nonce")),
        ),
        pytest.param(
            Spec.MAX_NONCE - 1,
            Spec.MAX_NONCE - 1,
            id="nonce=2**64-2",
            marks=pytest.mark.execute(pytest.mark.skip(reason="Impossible account nonce")),
        ),
        pytest.param(
            0,
            1,
            id="nonce=1,account_nonce=0",
        ),
        pytest.param(
            1,
            0,
            id="nonce=0,account_nonce=1",
        ),
    ],
)
def test_nonce_validity(
    state_test: StateTestFiller,
    pre: Alloc,
    account_nonce: int,
    authorization_nonce: int,
):
    """
    Test sending a transaction where the nonce field of an authorization almost overflows the
    maximum value.

    Also test calling the account of the authorization signer in order to verify that the account
    is not warm.
    """
    auth_signer = pre.fund_eoa(auth_account_start_balance, nonce=account_nonce)

    success_slot = 1
    return_slot = 2

    valid_authorization = authorization_nonce < 2**64 - 1 and account_nonce == authorization_nonce
    set_code = Op.RETURN(0, 1)
    set_code_to_address = pre.deploy_contract(set_code)

    authorization = AuthorizationTuple(
        address=set_code_to_address,
        nonce=authorization_nonce,
        signer=auth_signer,
    )

    entry_code = (
        Op.SSTORE(success_slot, 1)
        + Op.CALL(address=auth_signer)
        + Op.SSTORE(return_slot, Op.RETURNDATASIZE)
    )
    entry_address = pre.deploy_contract(entry_code)

    tx = Transaction(
        gas_limit=100_000,
        to=entry_address,
        value=0,
        authorization_list=[authorization],
        sender=pre.fund_eoa(),
    )

    state_test(
        env=Environment(),
        pre=pre,
        tx=tx,
        post={
            auth_signer: Account(
                nonce=(account_nonce + 1) if valid_authorization else account_nonce,
                code=Spec.delegation_designation(set_code_to_address)
                if valid_authorization
                else b"",
            )
            if authorization_nonce < 2**64 and account_nonce > 0
            else Account.NONEXISTENT,
            entry_address: Account(
                storage={
                    success_slot: 1,
                    return_slot: 1 if valid_authorization else 0,
                },
            ),
        },
    )


@pytest.mark.execute(pytest.mark.skip(reason="Impossible account nonce"))
def test_nonce_overflow_after_first_authorization(
    state_test: StateTestFiller,
    pre: Alloc,
):
    """
    Test sending a transaction with two authorization where the first one bumps the nonce
    to 2**64-1 and the second would result in overflow.
    """
    nonce = 2**64 - 2
    auth_signer = pre.fund_eoa(auth_account_start_balance, nonce=nonce)

    success_slot = 1
    return_slot = 2

    set_code_1 = Op.RETURN(0, 1)
    set_code_to_address_1 = pre.deploy_contract(set_code_1)
    set_code_2 = Op.RETURN(0, 2)
    set_code_to_address_2 = pre.deploy_contract(set_code_2)

    authorization_list = [
        AuthorizationTuple(
            address=set_code_to_address_1,
            nonce=nonce,
            signer=auth_signer,
        ),
        AuthorizationTuple(
            address=set_code_to_address_2,
            nonce=nonce + 1,
            signer=auth_signer,
        ),
    ]

    entry_code = (
        Op.SSTORE(success_slot, 1)
        + Op.CALL(address=auth_signer)
        + Op.SSTORE(return_slot, Op.RETURNDATASIZE)
    )
    entry_address = pre.deploy_contract(entry_code)

    tx = Transaction(
        gas_limit=200_000,
        to=entry_address,
        value=0,
        authorization_list=authorization_list,
        sender=pre.fund_eoa(),
    )

    state_test(
        env=Environment(),
        pre=pre,
        tx=tx,
        post={
            auth_signer: Account(
                nonce=nonce + 1,
                code=Spec.delegation_designation(set_code_to_address_1),
            ),
            entry_address: Account(
                storage={
                    success_slot: 1,
                    return_slot: 1,
                },
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
    """Test setting the code of an account to a contract that performs the log operation."""
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


@pytest.mark.with_all_call_opcodes
@pytest.mark.with_all_precompiles
def test_set_code_to_precompile(
    state_test: StateTestFiller,
    pre: Alloc,
    precompile: int,
    call_opcode: Op,
):
    """
    Test setting the code of an account to a pre-compile address and executing all call
    opcodes.
    """
    auth_signer = pre.fund_eoa(auth_account_start_balance)

    value = 1 if call_opcode in {Op.CALL, Op.CALLCODE, Op.EXTCALL} else 0
    caller_code_storage = Storage()
    caller_code = (
        Op.SSTORE(
            caller_code_storage.store_next(call_return_code(opcode=call_opcode, success=True)),
            call_opcode(address=auth_signer, value=value, gas=0),
        )
        + Op.SSTORE(caller_code_storage.store_next(0), Op.RETURNDATASIZE)
        + Op.STOP
    )
    caller_code_address = pre.deploy_contract(caller_code, balance=value)

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


@pytest.mark.with_all_precompiles
def test_set_code_to_precompile_not_enough_gas_for_precompile_execution(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    precompile: int,
):
    """
    Test set code to precompile and making direct call in same transaction with intrinsic gas
    only, no extra gas for precompile execution.
    """
    auth_signer = pre.fund_eoa(amount=1)
    auth = AuthorizationTuple(address=Address(precompile), nonce=0, signer=auth_signer)

    intrinsic_gas = fork.transaction_intrinsic_cost_calculator()(
        authorization_list_or_count=[auth],
    )
    discount = min(
        Spec.PER_EMPTY_ACCOUNT_COST - Spec.PER_AUTH_BASE_COST,
        intrinsic_gas // 5,  # max discount EIP-3529
    )

    tx = Transaction(
        sender=pre.fund_eoa(),
        to=auth_signer,
        gas_limit=intrinsic_gas,
        value=1,
        authorization_list=[auth],
        # explicitly check expected gas, no precompile code executed
        expected_receipt=TransactionReceipt(gas_used=intrinsic_gas - discount),
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            auth_signer: Account(
                # implicitly checks no OOG, successful tx transfers ``value=1``
                balance=2,
                code=Spec.delegation_designation(Address(precompile)),
                nonce=1,
            ),
        },
    )


def deposit_contract_initial_storage() -> Storage:
    """Return the initial storage of the deposit contract."""
    storage = Storage()
    deposit_contract_tree_depth = 32
    next_hash = sha256(b"\x00" * 64).digest()
    for i in range(deposit_contract_tree_depth + 2, deposit_contract_tree_depth * 2 + 1):
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
    fork: Fork,
    system_contract: int,
    call_opcode: Op,
):
    """Test setting the code of an account to a system contract."""
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
        case Address(0x00000961EF480EB55E80D19AD83579A64C007002):  # EIP-7002
            # Fabricate a valid withdrawal request to the set-code account
            withdrawal_request = WithdrawalRequest(
                source_address=0x01,
                validator_pubkey=0x02,
                amount=0x03,
                fee=0x01,
            )
            caller_payload = withdrawal_request.calldata
            call_value = withdrawal_request.value
        case Address(0x0000BBDDC7CE488642FB579F8B00F3A590007251):  # EIP-7251
            # Fabricate a valid consolidation request to the set-code account
            consolidation_request = ConsolidationRequest(
                source_address=0x01,
                source_pubkey=0x02,
                target_pubkey=0x03,
                fee=0x01,
            )
            caller_payload = consolidation_request.calldata
            call_value = consolidation_request.value
        case Address(0x0000F90827F1C53A10CB7A02335B175320002935):  # EIP-2935
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
    sender = pre.fund_eoa()
    if call_value > 0:
        pre.fund_address(sender, call_value)

    txs = [
        Transaction(
            sender=sender,
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
                requests_hash=Requests(),  # Verify nothing slipped into the requests trie
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
@pytest.mark.with_all_tx_types(
    selector=lambda tx_type: tx_type != 4,
    marks=lambda tx_type: pytest.mark.execute(pytest.mark.skip("incompatible tx"))
    if tx_type in [0, 3]
    else None,
)
@pytest.mark.parametrize(
    "same_block",
    [
        pytest.param(
            True,
            marks=[pytest.mark.execute(pytest.mark.skip("duplicate scenario for execute"))],
            id="same_block",
        ),
        pytest.param(False, id="different_block"),
    ],
)
def test_eoa_tx_after_set_code(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    tx_type: int,
    fork: Fork,
    evm_code_type: EVMCodeType,
    same_block: bool,
):
    """Test sending a transaction from an EOA after code has been set to the account."""
    auth_signer = pre.fund_eoa()

    set_code = Op.SSTORE(1, Op.ADD(Op.SLOAD(1), 1)) + Op.STOP
    set_code_to_address = pre.deploy_contract(set_code)

    first_eoa_tx = Transaction(
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
    auth_signer.nonce += 1  # type: ignore

    follow_up_eoa_txs: List[Transaction] = []
    match tx_type:
        case 0:
            follow_up_eoa_txs.extend(
                [
                    Transaction(
                        type=tx_type,
                        sender=auth_signer,
                        gas_limit=500_000,
                        to=auth_signer,
                        value=0,
                        protected=True,
                    ),
                    Transaction(
                        type=tx_type,
                        sender=auth_signer,
                        gas_limit=500_000,
                        to=auth_signer,
                        value=0,
                        protected=False,
                    ),
                ]
            )
        case 1:
            follow_up_eoa_txs.append(
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
                )
            )
        case 2:
            follow_up_eoa_txs.append(
                Transaction(
                    type=tx_type,
                    sender=auth_signer,
                    gas_limit=500_000,
                    to=auth_signer,
                    value=0,
                    max_fee_per_gas=1_000,
                    max_priority_fee_per_gas=1_000,
                )
            )
        case 3:
            follow_up_eoa_txs.append(
                Transaction(
                    type=tx_type,
                    sender=auth_signer,
                    gas_limit=500_000,
                    to=auth_signer,
                    value=0,
                    max_fee_per_gas=1_000,
                    max_priority_fee_per_gas=1_000,
                    max_fee_per_blob_gas=fork.min_base_fee_per_blob_gas() * 10,
                    blob_versioned_hashes=add_kzg_version(
                        [Hash(1)],
                        Spec4844.BLOB_COMMITMENT_VERSION_KZG,
                    ),
                )
            )
        case _:
            raise ValueError(f"Unsupported tx type: {tx_type}, test needs update")

    if same_block:
        blocks = [Block(txs=[first_eoa_tx] + follow_up_eoa_txs)]
    else:
        blocks = [
            Block(txs=[first_eoa_tx]),
            Block(txs=follow_up_eoa_txs),
        ]
    blockchain_test(
        pre=pre,
        blocks=blocks,
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
    Test sending type-4 tx to reset the code of an account after code has been
    set to the account.
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


def test_contract_create(
    state_test: StateTestFiller,
    pre: Alloc,
):
    """Test sending type-4 tx as a create transaction."""
    authorization_tuple = AuthorizationTuple(
        address=Address(0x01),
        nonce=0,
        signer=pre.fund_eoa(),
    )
    tx = Transaction(
        gas_limit=100_000,
        to=None,
        value=0,
        authorization_list=[authorization_tuple],
        error=TransactionException.TYPE_4_TX_CONTRACT_CREATION,
        sender=pre.fund_eoa(),
    )

    state_test(
        env=Environment(),
        pre=pre,
        tx=tx,
        post={},
    )


def test_empty_authorization_list(
    state_test: StateTestFiller,
    pre: Alloc,
):
    """Test sending an invalid transaction with empty authorization list."""
    tx = Transaction(
        gas_limit=100_000,
        to=pre.deploy_contract(code=b""),
        value=0,
        authorization_list=[],
        error=TransactionException.TYPE_4_EMPTY_AUTHORIZATION_LIST,
        sender=pre.fund_eoa(),
    )

    state_test(
        env=Environment(),
        pre=pre,
        tx=tx,
        post={},
    )


@pytest.mark.parametrize(
    "self_sponsored",
    [
        pytest.param(False, id="not_self_sponsored"),
        pytest.param(True, id="self_sponsored"),
    ],
)
@pytest.mark.parametrize(
    "pre_set_delegation_code",
    [
        pytest.param(Op.RETURN(0, 1), id="delegated_account"),
        pytest.param(None, id="undelegated_account"),
    ],
)
def test_delegation_clearing(
    state_test: StateTestFiller,
    pre: Alloc,
    pre_set_delegation_code: Bytecode | None,
    self_sponsored: bool,
):
    """
    Test clearing the delegation of an account under a variety of circumstances.

    - pre_set_delegation_code: The code to set on the account before clearing delegation, or None
        if the account should not have any code set.
    - self_sponsored: Whether the delegation clearing transaction is self-sponsored.

    """  # noqa: D417
    pre_set_delegation_address: Address | None = None
    if pre_set_delegation_code is not None:
        pre_set_delegation_address = pre.deploy_contract(pre_set_delegation_code)

    if self_sponsored:
        auth_signer = pre.fund_eoa(delegation=pre_set_delegation_address)
    else:
        auth_signer = pre.fund_eoa(0, delegation=pre_set_delegation_address)

    success_slot = 1
    return_slot = 2
    ext_code_size_slot = 3
    ext_code_hash_slot = 4
    ext_code_copy_slot = 5
    entry_code = (
        Op.SSTORE(success_slot, 1)
        + Op.CALL(address=auth_signer)
        + Op.SSTORE(return_slot, Op.RETURNDATASIZE)
        + Op.SSTORE(ext_code_size_slot, Op.EXTCODESIZE(address=auth_signer))
        + Op.SSTORE(ext_code_hash_slot, Op.EXTCODEHASH(address=auth_signer))
        + Op.EXTCODECOPY(address=auth_signer, size=32)
        + Op.SSTORE(ext_code_copy_slot, Op.MLOAD(0))
        + Op.STOP
    )
    entry_address = pre.deploy_contract(entry_code)

    authorization = AuthorizationTuple(
        address=Spec.RESET_DELEGATION_ADDRESS,  # Reset
        nonce=auth_signer.nonce + (1 if self_sponsored else 0),
        signer=auth_signer,
    )

    tx = Transaction(
        gas_limit=200_000,
        to=entry_address,
        value=0,
        authorization_list=[authorization],
        sender=pre.fund_eoa() if not self_sponsored else auth_signer,
    )

    state_test(
        env=Environment(),
        pre=pre,
        tx=tx,
        post={
            auth_signer: Account(
                nonce=auth_signer.nonce + 1,
                code=b"",
                storage={},
            ),
            entry_address: Account(
                storage={
                    success_slot: 1,
                    return_slot: 0,
                    ext_code_size_slot: 0,
                    ext_code_hash_slot: Bytes().keccak256(),
                    ext_code_copy_slot: 0,
                },
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
@pytest.mark.parametrize(
    "pre_set_delegation_code",
    [
        pytest.param(Op.RETURN(0, 1), id="delegated_account"),
        pytest.param(None, id="undelegated_account"),
    ],
)
def test_delegation_clearing_tx_to(
    state_test: StateTestFiller,
    pre: Alloc,
    pre_set_delegation_code: Bytecode | None,
    self_sponsored: bool,
):
    """
    Tests directly calling the account which delegation is being cleared.

    - pre_set_delegation_code: The code to set on the account before clearing delegation, or None
        if the account should not have any code set.
    - self_sponsored: Whether the delegation clearing transaction is self-sponsored.

    """  # noqa: D417
    pre_set_delegation_address: Address | None = None
    if pre_set_delegation_code is not None:
        pre_set_delegation_address = pre.deploy_contract(pre_set_delegation_code)

    if self_sponsored:
        auth_signer = pre.fund_eoa(delegation=pre_set_delegation_address)
    else:
        auth_signer = pre.fund_eoa(0, delegation=pre_set_delegation_address)

    sender = pre.fund_eoa() if not self_sponsored else auth_signer

    tx = Transaction(
        gas_limit=200_000,
        to=auth_signer,
        value=0,
        authorization_list=[
            AuthorizationTuple(
                address=Spec.RESET_DELEGATION_ADDRESS,  # Reset
                nonce=auth_signer.nonce + (1 if self_sponsored else 0),
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
            auth_signer: Account(
                nonce=auth_signer.nonce + 1,
                code=b"",
                storage={},
            ),
        },
    )


@pytest.mark.parametrize(
    "pre_set_delegation_code",
    [
        pytest.param(Op.RETURN(0, 1), id="delegated_account"),
        pytest.param(None, id="undelegated_account"),
    ],
)
def test_delegation_clearing_and_set(
    state_test: StateTestFiller,
    pre: Alloc,
    pre_set_delegation_code: Bytecode | None,
):
    """
    Tests clearing and setting the delegation again in the same authorization list.

    - pre_set_delegation_code: The code to set on the account before clearing delegation, or None
        if the account should not have any code set.

    """  # noqa: D417
    pre_set_delegation_address: Address | None = None
    if pre_set_delegation_code is not None:
        pre_set_delegation_address = pre.deploy_contract(pre_set_delegation_code)

    auth_signer = pre.fund_eoa(0, delegation=pre_set_delegation_address)

    reset_code_address = pre.deploy_contract(
        Op.CALL(address=Spec.RESET_DELEGATION_ADDRESS) + Op.SSTORE(0, 1) + Op.STOP
    )

    sender = pre.fund_eoa()

    tx = Transaction(
        gas_limit=200_000,
        to=auth_signer,
        value=0,
        authorization_list=[
            AuthorizationTuple(
                address=Spec.RESET_DELEGATION_ADDRESS,  # Reset
                nonce=auth_signer.nonce,
                signer=auth_signer,
            ),
            AuthorizationTuple(
                address=reset_code_address,
                nonce=auth_signer.nonce + 1,
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
            auth_signer: Account(
                nonce=auth_signer.nonce + 2,
                code=Spec.delegation_designation(reset_code_address),
                storage={
                    0: 1,
                },
            ),
        },
    )


@pytest.mark.parametrize(
    "entry_code",
    [
        pytest.param(Om.OOG + Op.STOP, id="out_of_gas"),
        pytest.param(Op.INVALID, id="invalid_opcode"),
        pytest.param(Op.REVERT(0, 0), id="revert"),
    ],
)
def test_delegation_clearing_failing_tx(
    state_test: StateTestFiller,
    pre: Alloc,
    entry_code: Bytecode,
):
    """Test clearing the delegation of an account in a transaction that fails, OOGs or reverts."""  # noqa: D417
    pre_set_delegation_code = Op.RETURN(0, 1)
    pre_set_delegation_address = pre.deploy_contract(pre_set_delegation_code)

    auth_signer = pre.fund_eoa(0, delegation=pre_set_delegation_address)

    entry_address = pre.deploy_contract(entry_code)

    authorization = AuthorizationTuple(
        address=Spec.RESET_DELEGATION_ADDRESS,  # Reset
        nonce=auth_signer.nonce,
        signer=auth_signer,
    )

    tx = Transaction(
        gas_limit=100_000,
        to=entry_address,
        value=0,
        authorization_list=[authorization],
        sender=pre.fund_eoa(),
    )

    state_test(
        env=Environment(),
        pre=pre,
        tx=tx,
        post={
            auth_signer: Account(
                nonce=auth_signer.nonce + 1,
                code=b"",
                storage={},
            ),
        },
    )


@pytest.mark.parametrize(
    "initcode_is_delegation_designation",
    [
        pytest.param(True, id="initcode_deploys_delegation_designation"),
        pytest.param(False, id="initcode_is_delegation_designation"),
    ],
)
def test_deploying_delegation_designation_contract(
    state_test: StateTestFiller,
    pre: Alloc,
    initcode_is_delegation_designation: bool,
):
    """
    Test attempting to deploy a contract that has the same format as a
    delegation designation.
    """
    sender = pre.fund_eoa()

    set_to_code = Op.RETURN(0, 1)
    set_to_address = pre.deploy_contract(set_to_code)

    initcode: Bytes | Bytecode
    if initcode_is_delegation_designation:
        initcode = Spec.delegation_designation(set_to_address)
    else:
        initcode = Initcode(deploy_code=Spec.delegation_designation(set_to_address))

    tx = Transaction(
        sender=sender,
        to=None,
        gas_limit=100_000,
        data=initcode,
    )

    state_test(
        env=Environment(),
        pre=pre,
        tx=tx,
        post={
            sender: Account(
                nonce=1,
            ),
            tx.created_contract: Account.NONEXISTENT,
        },
    )


@pytest.mark.parametrize(
    "initcode_is_delegation_designation",
    [
        pytest.param(True, id="initcode_deploys_delegation_designation"),
        pytest.param(False, id="initcode_is_delegation_designation"),
    ],
)
@pytest.mark.parametrize("create_opcode", [Op.CREATE, Op.CREATE2])
def test_creating_delegation_designation_contract(
    state_test: StateTestFiller,
    pre: Alloc,
    create_opcode: Op,
    initcode_is_delegation_designation: bool,
):
    """
    Tx -> create -> pointer bytecode
    Attempt to deploy contract with magic bytes result in no contract being created.
    """
    env = Environment()

    storage: Storage = Storage()

    sender = pre.fund_eoa()

    # An attempt to deploy code starting with ef01 result in no
    # contract being created as it is prohibited

    create_init: Bytes | Bytecode
    if initcode_is_delegation_designation:
        create_init = Spec.delegation_designation(sender)
    else:
        create_init = Initcode(deploy_code=Spec.delegation_designation(sender))
    contract_a = pre.deploy_contract(
        balance=100,
        code=Op.MSTORE(0, Op.CALLDATALOAD(0))
        + Op.SSTORE(
            storage.store_next(0, "contract_a_create_result"),
            create_opcode(value=1, offset=0, size=Op.CALLDATASIZE(), salt=0),
        )
        + Op.STOP,
    )

    tx = Transaction(
        to=contract_a,
        gas_limit=1_000_000,
        data=create_init,
        value=0,
        sender=sender,
    )

    create_address = compute_create_address(
        address=contract_a, nonce=1, initcode=create_init, salt=0, opcode=create_opcode
    )
    post = {
        contract_a: Account(balance=100, storage=storage),
        create_address: Account.NONEXISTENT,
    }
    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.parametrize(
    "signer_balance",
    [
        pytest.param(0, id="empty_balance"),
        pytest.param(
            1,
            id="non_empty_balance",
            marks=pytest.mark.execute(pytest.mark.skip(reason="excessive pre-fund txs")),
        ),
    ],
)
@pytest.mark.parametrize(
    "max_gas",
    [
        pytest.param(
            120_000_000,
            id="120m",
            marks=pytest.mark.execute(pytest.mark.skip(reason="excessive gas")),
        ),
        pytest.param(
            20_000_000,
            id="20m",
            marks=pytest.mark.fill(pytest.mark.skip(reason="execute-only test")),
        ),
    ],
)
def test_many_delegations(
    state_test: StateTestFiller,
    pre: Alloc,
    max_gas: int,
    signer_balance: int,
):
    """
    Perform as many delegations as possible in a single 120 million gas transaction.

    Every delegation comes from a different signer.

    The account of can be empty or not depending on the `signer_balance` parameter.

    The transaction is expected to succeed and the state after the transaction is expected to have
    the code of the entry contract set to 1.
    """
    gas_for_delegations = max_gas - 21_000 - 20_000 - (3 * 2)

    delegation_count = gas_for_delegations // Spec.PER_EMPTY_ACCOUNT_COST

    success_slot = 1
    entry_code = Op.SSTORE(success_slot, 1) + Op.STOP
    entry_address = pre.deploy_contract(entry_code)

    signers = [pre.fund_eoa(signer_balance) for _ in range(delegation_count)]

    tx = Transaction(
        gas_limit=max_gas,
        to=entry_address,
        value=0,
        authorization_list=[
            AuthorizationTuple(
                address=Address(i + 1),
                nonce=0,
                signer=signer,
            )
            for (i, signer) in enumerate(signers)
        ],
        sender=pre.fund_eoa(),
    )

    post = {
        entry_address: Account(
            storage={success_slot: 1},
        ),
    } | {
        signer: Account(
            code=Spec.delegation_designation(Address(i + 1)),
        )
        for (i, signer) in enumerate(signers)
    }

    state_test(
        env=Environment(),
        pre=pre,
        tx=tx,
        post=post,
    )


def test_invalid_transaction_after_authorization(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
):
    """
    Test an invalid block due to a transaction reusing the same nonce as an authorization
    included in a prior transaction.
    """
    auth_signer = pre.fund_eoa()

    txs = [
        Transaction(
            sender=pre.fund_eoa(),
            gas_limit=500_000,
            to=Address(0),
            value=0,
            authorization_list=[
                AuthorizationTuple(
                    address=Address(1),
                    nonce=0,
                    signer=auth_signer,
                ),
            ],
        ),
        Transaction(
            sender=auth_signer,
            nonce=0,
            gas_limit=21_000,
            to=Address(0),
            value=1,
            error=TransactionException.NONCE_MISMATCH_TOO_LOW,
        ),
    ]

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=txs,
                exception=TransactionException.NONCE_MISMATCH_TOO_LOW,
            )
        ],
        post={
            Address(0): None,
        },
    )


def test_authorization_reusing_nonce(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
):
    """
    Test an authorization reusing the same nonce as a prior transaction included in the same
    block.
    """
    auth_signer = pre.fund_eoa()
    sender = pre.fund_eoa()
    txs = [
        Transaction(
            sender=auth_signer,
            nonce=0,
            gas_limit=21_000,
            to=Address(0),
            value=1,
        ),
        Transaction(
            sender=sender,
            gas_limit=500_000,
            to=Address(0),
            value=0,
            authorization_list=[
                AuthorizationTuple(
                    address=Address(1),
                    nonce=0,
                    signer=auth_signer,
                ),
            ],
        ),
    ]

    blockchain_test(
        pre=pre,
        blocks=[Block(txs=txs)],
        post={
            Address(0): Account(balance=1),
            auth_signer: Account(nonce=1, code=b""),
            sender: Account(nonce=1),
        },
    )


@pytest.mark.parametrize(
    "set_code_type",
    list(AddressType),
    ids=lambda address_type: address_type.name,
)
@pytest.mark.parametrize(
    "self_sponsored",
    [True, False],
)
@pytest.mark.execute(pytest.mark.skip(reason="Requires contract-eoa address collision"))
def test_set_code_from_account_with_non_delegating_code(
    state_test: StateTestFiller,
    pre: Alloc,
    set_code_type: AddressType,
    self_sponsored: bool,
):
    """
    Test that a transaction is correctly rejected,
    if the sender account has a non-delegating code set.

    The auth transaction is sent from sender which has contract code (not delegating)
    But at the same time it has auth tuple that will point this sender account
    To be eoa, delegation, contract .. etc
    """
    sender = pre.fund_eoa(nonce=1)
    random_address = pre.fund_eoa(0)

    set_code_to_address: Address
    match set_code_type:
        case AddressType.EMPTY_ACCOUNT:
            set_code_to_address = pre.fund_eoa(0)
        case AddressType.EOA:
            set_code_to_address = pre.fund_eoa(1)
        case AddressType.EOA_WITH_SET_CODE:
            set_code_account = pre.fund_eoa(0)
            set_code_to_address = pre.fund_eoa(1, delegation=set_code_account)
        case AddressType.CONTRACT:
            set_code_to_address = pre.deploy_contract(Op.STOP)
        case _:
            raise ValueError(f"Unsupported set code type: {set_code_type}")
    callee_address = pre.deploy_contract(Op.SSTORE(0, 1) + Op.STOP)

    # Set the sender account to have some code, that is specifically not a delegation.
    sender_account = pre[sender]
    assert sender_account is not None
    sender_account.code = Bytes(Op.STOP)

    tx = Transaction(
        gas_limit=100_000,
        to=callee_address,
        authorization_list=[
            AuthorizationTuple(
                address=set_code_to_address,
                nonce=1 if self_sponsored else 0,
                signer=sender if self_sponsored else random_address,
            ),
        ],
        sender=sender,
        error=TransactionException.SENDER_NOT_EOA,
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
            random_address: Account.NONEXISTENT,
            sender: Account(nonce=1),
            callee_address: Account(storage={0: 0}),
        },
    )


@pytest.mark.parametrize(
    "max_fee_per_gas, max_priority_fee_per_gas, expected_error",
    [
        (6, 0, TransactionException.INSUFFICIENT_MAX_FEE_PER_GAS),
        (7, 8, TransactionException.PRIORITY_GREATER_THAN_MAX_FEE_PER_GAS),
    ],
    ids=[
        "insufficient_max_fee_per_gas",
        "priority_greater_than_max_fee_per_gas",
    ],
)
def test_set_code_transaction_fee_validations(
    state_test: StateTestFiller,
    pre: Alloc,
    max_fee_per_gas: int,
    max_priority_fee_per_gas: int,
    expected_error: TransactionException,
):
    """Test that a transaction with an insufficient max fee per gas is rejected."""
    set_to_code = pre.deploy_contract(Op.STOP)
    auth_signer = pre.fund_eoa(amount=0)
    tx = Transaction(
        sender=pre.fund_eoa(),
        gas_limit=500_000,
        to=auth_signer,
        value=0,
        max_fee_per_gas=max_fee_per_gas,
        max_priority_fee_per_gas=max_priority_fee_per_gas,
        authorization_list=[
            AuthorizationTuple(
                address=set_to_code,
                nonce=0,
                signer=auth_signer,
            ),
        ],
        error=expected_error,
    )

    state_test(
        env=Environment(),
        pre=pre,
        tx=tx,
        post={},
    )
