"""
Verify EIP-7997: Deterministic Factory Contract.

<https://eips.ethereum.org/EIPS/eip-7997>

The factory (the Arachnid deterministic deployment proxy) interprets
calldata as `salt (32) || initcode` and invokes `CREATE2` with the call
value forwarded. It returns the created address (20 bytes) on success
and reverts with empty return data on `CREATE2` failure. With calldata
shorter than 32 bytes, the factory's `CALLDATASIZE - 32` underflow makes
`CALLDATACOPY` request close to 2^256 bytes and the frame halts out of
gas.
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    AuthorizationTuple,
    BalAccountExpectation,
    BalCodeChange,
    BalNonceChange,
    BalStorageChange,
    BalStorageSlot,
    BlockAccessListExpectation,
    Bytecode,
    Bytes,
    CodeGasMeasure,
    EIPChecklist,
    Fork,
    Hash,
    Initcode,
    Op,
    StateTestFiller,
    Storage,
    Transaction,
    compute_create2_address,
    compute_create_address,
    keccak256,
)
from execution_testing import (
    Macros as Om,
)

from ...prague.eip7702_set_code_tx.spec import Spec as Spec7702
from .spec import Spec, ref_spec_7997

REFERENCE_SPEC_GIT_PATH = ref_spec_7997.git_path
REFERENCE_SPEC_VERSION = ref_spec_7997.version

pytestmark = [
    pytest.mark.valid_from("EIP7997"),
    pytest.mark.execute(
        pytest.mark.skip(
            reason="Fixed-salt deployments are single-shot on a live chain"
        )
    ),
]

FACTORY = Spec.FACTORY_ADDRESS
RUNTIME_CODE = Op.RETURN(0, 1)
RETURNED_ADDRESS_SIZE = 20


def test_factory_contract_account(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Verify the canonical code, initial nonce and balance through the EVM."""
    storage = Storage()
    extcodesize_slot = storage.store_next(
        len(Spec.FACTORY_BYTECODE), "extcodesize"
    )
    extcodehash_slot = storage.store_next(
        keccak256(Spec.FACTORY_BYTECODE), "extcodehash"
    )
    extcodecopy_hash_slot = storage.store_next(
        keccak256(Spec.FACTORY_BYTECODE), "extcodecopy_hash"
    )
    balance_slot = storage.store_next(0, "balance")
    caller = pre.deploy_contract(
        Op.SSTORE(extcodesize_slot, Op.EXTCODESIZE(FACTORY))
        + Op.SSTORE(extcodehash_slot, Op.EXTCODEHASH(FACTORY))
        + Op.EXTCODECOPY(FACTORY, 0, 0, Op.EXTCODESIZE(FACTORY))
        + Op.SSTORE(extcodecopy_hash_slot, Op.SHA3(0, Op.EXTCODESIZE(FACTORY)))
        + Op.SSTORE(balance_slot, Op.BALANCE(FACTORY))
        + Op.STOP,
        storage=storage.canary(),
    )
    state_test(
        pre=pre,
        tx=Transaction(
            sender=pre.fund_eoa(),
            to=caller,
        ),
        post={
            FACTORY: Account(
                nonce=1,
                balance=0,
                code=Spec.FACTORY_BYTECODE,
            ),
            caller: Account(storage=storage),
        },
    )


@pytest.mark.parametrize(
    "forwarded_value",
    [
        pytest.param(0, id="no_value"),
        pytest.param(
            1,
            id="with_value",
            marks=EIPChecklist.SystemContract.Test.ValueTransfer.NoFee(),
        ),
    ],
)
@EIPChecklist.SystemContract.Test.CallContexts.Normal()
@EIPChecklist.SystemContract.Test.Inputs.Valid()
def test_factory_deploys_contract(
    state_test: StateTestFiller,
    pre: Alloc,
    forwarded_value: int,
) -> None:
    """Verify deployment, unpadded return data and value forwarding."""
    salt = 0x42
    runtime_code = Op.PUSH1(0x01) + Op.PUSH1(0x00) + Op.RETURN
    initcode = Initcode(deploy_code=runtime_code)
    expected_address = compute_create2_address(FACTORY, salt, initcode)

    storage = Storage()
    caller = pre.deploy_contract(
        Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE)
        + Op.SSTORE(
            storage.store_next(1, "factory_call_success"),
            Op.CALL(
                gas=Op.GAS,
                address=FACTORY,
                value=forwarded_value,
                args_offset=0,
                args_size=Op.CALLDATASIZE,
                ret_offset=12,
                ret_size=RETURNED_ADDRESS_SIZE,
            ),
        )
        + Op.SSTORE(
            storage.store_next(expected_address, "returned_address"),
            Op.MLOAD(0),
        )
        + Op.SSTORE(
            storage.store_next(RETURNED_ADDRESS_SIZE, "returndatasize"),
            Op.RETURNDATASIZE,
        )
        + Op.STOP,
        balance=forwarded_value,
        storage=storage.canary(),
    )

    state_test(
        pre=pre,
        tx=Transaction(
            sender=pre.fund_eoa(),
            to=caller,
            data=Hash(salt) + bytes(initcode),
        ),
        post={
            caller: Account(storage=storage, balance=0),
            expected_address: Account(
                nonce=1,
                balance=forwarded_value,
                code=bytes(runtime_code),
            ),
        },
    )


@pytest.mark.parametrize("destroy_before_retry", [False, True])
def test_factory_address_collision_reverts(
    state_test: StateTestFiller,
    pre: Alloc,
    destroy_before_retry: bool,
) -> None:
    """
    Reject reuse of a CREATE2 address within the same transaction.

    SELFDESTRUCT schedules deletion at transaction end under EIP-6780.
    Until then the code and nonce still prevent another creation, including
    under EIP-8246. Reverting the retry restores the factory nonce.
    """
    salt = 0x77
    beneficiary = pre.fund_eoa(amount=0)
    runtime_code = Op.SELFDESTRUCT(beneficiary)
    initcode = Initcode(deploy_code=runtime_code)
    target = compute_create2_address(FACTORY, salt, initcode)

    storage = Storage()
    caller = pre.deploy_contract(
        Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE)
        + Op.SSTORE(
            storage.store_next(1, "first_call_success"),
            Op.CALL(
                gas=Op.GAS,
                address=FACTORY,
                value=0,
                args_offset=0,
                args_size=Op.CALLDATASIZE,
                ret_offset=0x100,
                ret_size=32,
            ),
        )
        + Op.SSTORE(
            storage.store_next(RETURNED_ADDRESS_SIZE, "first_returndatasize"),
            Op.RETURNDATASIZE,
        )
        + (
            Op.SSTORE(
                storage.store_next(1, "selfdestruct_call_success"),
                Op.CALL(gas=Op.GAS, address=target),
            )
            + Op.SSTORE(
                storage.store_next(len(runtime_code), "code_before_retry"),
                Op.EXTCODESIZE(target),
            )
            if destroy_before_retry
            else Bytecode()
        )
        + Op.SSTORE(
            storage.store_next(0, "second_call_failed"),
            Op.CALL(
                gas=Op.GAS,
                address=FACTORY,
                value=0,
                args_offset=0,
                args_size=Op.CALLDATASIZE,
                ret_offset=0x100,
                ret_size=32,
            ),
        )
        + Op.SSTORE(
            storage.store_next(0, "second_returndatasize"),
            Op.RETURNDATASIZE,
        )
        + Op.STOP,
        storage=storage.canary(),
    )

    state_test(
        pre=pre,
        tx=Transaction(
            sender=pre.fund_eoa(),
            to=caller,
            data=Hash(salt) + bytes(initcode),
        ),
        post={
            caller: Account(storage=storage),
            target: (
                Account.NONEXISTENT
                if destroy_before_retry
                else Account(nonce=1, code=bytes(runtime_code))
            ),
            FACTORY: Account(nonce=2, code=Spec.FACTORY_BYTECODE),
        },
    )


@pytest.mark.parametrize(
    "initcode_failure",
    [
        pytest.param(
            Op.MSTORE(0, 0xDEADBEEF) + Op.REVERT(0, 32),
            id="revert_with_data",
        ),
        pytest.param(Op.INVALID, id="invalid_opcode"),
        pytest.param(Om.OOG, id="out_of_gas"),
    ],
)
@pytest.mark.parametrize(
    "forwarded_value",
    [
        pytest.param(0, id="no_value"),
        pytest.param(1, id="with_value"),
    ],
)
def test_factory_creation_failure_returns_empty_data(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    initcode_failure: Bytecode,
    forwarded_value: int,
) -> None:
    """
    Discard failed initcode return data and restore the caller's value.

    Revert the factory nonce increment together with the failed creation.
    """
    gas_limit = fork.transaction_gas_limit_cap()
    assert gas_limit is not None

    salt = 0x99
    initcode = initcode_failure
    expected_address = compute_create2_address(FACTORY, salt, initcode)

    storage = Storage()
    caller = pre.deploy_contract(
        Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE)
        + Op.SSTORE(
            storage.store_next(0, "factory_call_failed"),
            Op.CALL(
                # Bounded so the caller keeps gas for its stores even when
                # the initcode burns everything it is given.
                gas=gas_limit // 8,
                address=FACTORY,
                value=forwarded_value,
                args_offset=0,
                args_size=Op.CALLDATASIZE,
            ),
        )
        + Op.SSTORE(
            storage.store_next(0, "returndatasize"),
            Op.RETURNDATASIZE,
        )
        + Op.STOP,
        balance=forwarded_value,
        storage=storage.canary(),
    )

    state_test(
        pre=pre,
        tx=Transaction(
            sender=pre.fund_eoa(),
            to=caller,
            data=Hash(salt) + bytes(initcode),
        ),
        post={
            caller: Account(storage=storage, balance=forwarded_value),
            expected_address: Account.NONEXISTENT,
            FACTORY: Account(
                nonce=1,
                balance=0,
                code=Spec.FACTORY_BYTECODE,
            ),
        },
    )


@pytest.mark.parametrize(
    "calldata_size",
    [
        pytest.param(
            0,
            id="0_bytes",
            marks=EIPChecklist.SystemContract.Test.InputLengths.Zero(),
        ),
        pytest.param(1, id="1_byte"),
        pytest.param(Spec.SALT_SIZE - 1, id="31_bytes"),
    ],
)
@EIPChecklist.SystemContract.Test.InputLengths.Dynamic.TooShort()
@EIPChecklist.SystemContract.Test.Inputs.Invalid.Corrupted()
def test_factory_short_calldata_out_of_gas(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    calldata_size: int,
) -> None:
    """
    Exhaust the forwarded gas when calldata lacks a complete salt.

    The length subtraction wraps and CALLDATACOPY halts out of gas before
    CREATE2. Measure the exact call cost to distinguish a REVERT.
    """
    gas_limit = fork.transaction_gas_limit_cap()
    assert gas_limit is not None

    call_gas = gas_limit // 8
    storage = Storage()
    measured_call = Op.MSTORE(
        0x40,
        Op.CALL(
            gas=call_gas,
            address=FACTORY,
            value=0,
            args_offset=0,
            args_size=calldata_size,
            address_warm=False,
        ),
    )
    caller = pre.deploy_contract(
        Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE)
        + Op.MSTORE(0x40, 0)
        + CodeGasMeasure(
            code=measured_call,
            sstore_key=storage.store_next(
                measured_call.execution_cost(fork) + call_gas,
                "call_gas_consumed",
            ),
        )
        + Op.SSTORE(
            storage.store_next(0, "factory_call_failed"), Op.MLOAD(0x40)
        )
        + Op.SSTORE(storage.store_next(0, "returndatasize"), Op.RETURNDATASIZE)
        + Op.STOP,
        storage=storage.canary(),
    )

    state_test(
        pre=pre,
        tx=Transaction(
            sender=pre.fund_eoa(),
            to=caller,
            data=bytes([0xAA]) * calldata_size,
        ),
        post={
            caller: Account(storage=storage),
            FACTORY: Account(
                nonce=1,
                balance=0,
                code=Spec.FACTORY_BYTECODE,
            ),
        },
    )


@pytest.mark.parametrize(
    "salt,initcode,deployed_code",
    [
        pytest.param(
            0,
            Initcode(deploy_code=RUNTIME_CODE),
            RUNTIME_CODE,
            id="salt_zero",
        ),
        pytest.param(
            2**256 - 1,
            Initcode(deploy_code=RUNTIME_CODE),
            RUNTIME_CODE,
            id="salt_max",
            marks=EIPChecklist.SystemContract.Test.Inputs.MaxValues(),
        ),
        pytest.param(0x42, b"", b"", id="empty_initcode"),
        pytest.param(
            0,
            bytes(32),
            b"",
            id="all_zero_calldata",
            marks=EIPChecklist.SystemContract.Test.Inputs.AllZeros(),
        ),
    ],
)
@EIPChecklist.SystemContract.Test.Inputs.Boundary()
@EIPChecklist.SystemContract.Test.InputLengths.Dynamic.Valid()
def test_factory_calldata_layouts(
    state_test: StateTestFiller,
    pre: Alloc,
    salt: int,
    initcode: Bytecode | bytes,
    deployed_code: Bytecode | bytes,
) -> None:
    """Use the complete salt and remaining initcode, including empty code."""
    expected_address = compute_create2_address(FACTORY, salt, initcode)

    state_test(
        pre=pre,
        tx=Transaction(
            sender=pre.fund_eoa(),
            to=FACTORY,
            data=Hash(salt) + bytes(initcode),
        ),
        post={
            expected_address: Account(nonce=1, code=bytes(deployed_code)),
            FACTORY: Account(nonce=2, code=Spec.FACTORY_BYTECODE),
        },
    )


@EIPChecklist.SystemContract.Test.InputLengths.Dynamic.TooLong()
def test_factory_trailing_calldata_is_initcode(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Include trailing bytes in the CREATE2 initcode hash."""
    salt = 0x42
    initcode = Initcode(deploy_code=RUNTIME_CODE)
    padded_initcode = bytes(initcode) + b"\x00"
    unpadded_address = compute_create2_address(FACTORY, salt, initcode)
    padded_address = compute_create2_address(FACTORY, salt, padded_initcode)
    assert padded_address != unpadded_address

    state_test(
        pre=pre,
        tx=Transaction(
            sender=pre.fund_eoa(),
            to=FACTORY,
            data=Hash(salt) + padded_initcode,
        ),
        post={
            padded_address: Account(nonce=1, code=bytes(RUNTIME_CODE)),
            unpadded_address: Account.NONEXISTENT,
        },
    )


@EIPChecklist.SystemContract.Test.Inputs.Valid()
def test_factory_different_salts_produce_different_addresses(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Deploy identical initcode at distinct salt-derived addresses."""
    salt_a = 0x11
    salt_b = 0x22
    runtime_code = Op.PUSH1(0x01) + Op.PUSH1(0x00) + Op.RETURN
    initcode = Initcode(deploy_code=runtime_code)
    addr_a = compute_create2_address(FACTORY, salt_a, initcode)
    addr_b = compute_create2_address(FACTORY, salt_b, initcode)
    assert addr_a != addr_b

    initcode_offset = 32
    args_size = initcode_offset + len(bytes(initcode))

    storage = Storage()
    salt_a_call_slot = storage.store_next(1, "salt_a_call_success")
    salt_a_addr_slot = storage.store_next(addr_a, "salt_a_address")
    salt_b_call_slot = storage.store_next(1, "salt_b_call_success")
    salt_b_addr_slot = storage.store_next(addr_b, "salt_b_address")

    caller = pre.deploy_contract(
        Op.CALLDATACOPY(initcode_offset, 0, Op.CALLDATASIZE)
        + Op.MSTORE(0, salt_a)
        + Op.SSTORE(
            salt_a_call_slot,
            Op.CALL(
                gas=Op.GAS,
                address=FACTORY,
                value=0,
                args_offset=0,
                args_size=args_size,
                ret_offset=0x20C,
                ret_size=20,
            ),
        )
        + Op.SSTORE(salt_a_addr_slot, Op.MLOAD(0x200))
        + Op.MSTORE(0, salt_b)
        + Op.SSTORE(
            salt_b_call_slot,
            Op.CALL(
                gas=Op.GAS,
                address=FACTORY,
                value=0,
                args_offset=0,
                args_size=args_size,
                ret_offset=0x20C,
                ret_size=20,
            ),
        )
        + Op.SSTORE(salt_b_addr_slot, Op.MLOAD(0x200))
        + Op.STOP,
        storage=storage.canary(),
    )

    state_test(
        pre=pre,
        tx=Transaction(
            sender=pre.fund_eoa(),
            to=caller,
            data=bytes(initcode),
        ),
        post={
            caller: Account(storage=storage),
            addr_a: Account(nonce=1, code=bytes(runtime_code)),
            addr_b: Account(nonce=1, code=bytes(runtime_code)),
        },
    )


@EIPChecklist.SystemContract.Test.CallContexts.TxEntry()
def test_factory_direct_eoa_call(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Deploy through a transaction addressed directly to the factory."""
    salt = 0xCAFE
    runtime_code = Op.PUSH1(0x01) + Op.PUSH1(0x00) + Op.RETURN
    initcode = Initcode(deploy_code=runtime_code)
    expected_address = compute_create2_address(FACTORY, salt, initcode)

    state_test(
        pre=pre,
        tx=Transaction(
            sender=pre.fund_eoa(),
            to=FACTORY,
            data=Hash(salt) + bytes(initcode),
        ),
        post={
            expected_address: Account(nonce=1, code=bytes(runtime_code)),
        },
    )


@pytest.mark.parametrize("nested", [False, True])
@EIPChecklist.SystemContract.Test.CallContexts.Static()
def test_factory_staticcall_reverts(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    nested: bool,
) -> None:
    """
    Reject CREATE2 in both direct and inherited static contexts.

    Let the intermediate frame return the failed CALL result and its empty
    return data to prove the nested call executed without deploying.
    """
    gas_limit = fork.transaction_gas_limit_cap()
    assert gas_limit is not None

    salt = 0x33
    runtime_code = Op.STOP
    initcode = Initcode(deploy_code=runtime_code)
    expected_address = compute_create2_address(FACTORY, salt, initcode)

    target = Address(FACTORY)
    if nested:
        target = pre.deploy_contract(
            Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE)
            + Op.MSTORE(
                0,
                Op.CALL(
                    gas=gas_limit // 8,
                    address=FACTORY,
                    args_size=Op.CALLDATASIZE,
                ),
            )
            + Op.MSTORE(32, Op.RETURNDATASIZE)
            + Op.RETURN(0, 64)
        )

    storage = Storage()
    caller = pre.deploy_contract(
        Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE)
        + Op.SSTORE(
            storage.store_next(int(nested), "staticcall_success"),
            Op.STATICCALL(
                gas=gas_limit // 4,
                address=target,
                args_offset=0,
                args_size=Op.CALLDATASIZE,
                ret_offset=0x100,
                ret_size=64,
            ),
        )
        + Op.SSTORE(
            storage.store_next(64 if nested else 0, "returndatasize"),
            Op.RETURNDATASIZE,
        )
        + Op.SSTORE(
            storage.store_next(0, "nested_call_result"), Op.MLOAD(0x100)
        )
        + Op.SSTORE(
            storage.store_next(0, "nested_returndatasize"), Op.MLOAD(0x120)
        )
        + Op.STOP,
        storage=storage.canary(),
    )

    state_test(
        pre=pre,
        tx=Transaction(
            sender=pre.fund_eoa(),
            to=caller,
            data=Hash(salt) + bytes(initcode),
        ),
        post={
            caller: Account(storage=storage),
            expected_address: Account.NONEXISTENT,
            FACTORY: Account(nonce=1, balance=0),
        },
    )


@pytest.mark.parametrize("call_opcode", [Op.DELEGATECALL, Op.CALLCODE])
@EIPChecklist.SystemContract.Test.CallContexts.Delegate()
@EIPChecklist.SystemContract.Test.CallContexts.Callcode()
def test_factory_in_caller_context(
    state_test: StateTestFiller,
    pre: Alloc,
    call_opcode: Op,
) -> None:
    """Use the caller as the CREATE2 deployer for DELEGATECALL and CALLCODE."""
    salt = 0x44
    runtime_code = Op.STOP
    initcode = Initcode(deploy_code=runtime_code)
    factory_derived = compute_create2_address(FACTORY, salt, initcode)

    call_op = call_opcode(
        gas=Op.GAS,
        address=FACTORY,
        args_offset=0,
        args_size=Op.CALLDATASIZE,
        ret_offset=0x10C,
        ret_size=20,
    )

    storage = Storage()
    call_success_slot = storage.store_next(1, "delegated_call_success")
    derived_addr_slot = storage.store_next(0, "caller_derived_address")

    caller = pre.deploy_contract(
        Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE)
        + Op.SSTORE(call_success_slot, call_op)
        + Op.SSTORE(derived_addr_slot, Op.MLOAD(0x100))
        + Op.STOP,
        storage=storage.canary(),
    )
    caller_derived = compute_create2_address(caller, salt, initcode)
    storage[derived_addr_slot] = caller_derived

    state_test(
        pre=pre,
        tx=Transaction(
            sender=pre.fund_eoa(),
            to=caller,
            data=Hash(salt) + bytes(initcode),
        ),
        post={
            caller: Account(storage=storage),
            caller_derived: Account(nonce=1, code=bytes(runtime_code)),
            factory_derived: Account.NONEXISTENT,
        },
    )


@pytest.mark.parametrize(
    "creation_context",
    [
        pytest.param(
            "tx",
            id="initcode_of_create_tx",
            marks=EIPChecklist.SystemContract.Test.CallContexts.Initcode.Tx(),
        ),
        pytest.param(
            "create",
            id="initcode_of_create_opcode",
            marks=(
                EIPChecklist.SystemContract.Test.CallContexts.Initcode.CREATE()
            ),
        ),
        pytest.param(
            "factory",
            id="initcode_of_factory_create2",
            marks=(
                EIPChecklist.SystemContract.Test.CallContexts.Initcode.CREATE()
            ),
        ),
    ],
)
def test_factory_called_from_initcode(
    state_test: StateTestFiller,
    pre: Alloc,
    creation_context: str,
) -> None:
    """
    Call the factory from transaction, CREATE and factory CREATE2 initcode.

    Verify both deployments and the extra factory nonce increment when its
    own CREATE2 initcode re-enters it.
    """
    inner_salt = 0x1111
    inner_initcode = Initcode(deploy_code=RUNTIME_CODE)
    inner_address = compute_create2_address(
        FACTORY, inner_salt, inner_initcode
    )
    inner_calldata_size = Spec.SALT_SIZE + len(inner_initcode)

    outer_storage = Storage()
    outer_initcode = Initcode(
        initcode_prefix=(
            Op.MSTORE(0, inner_salt)
            + Om.MSTORE(bytes(inner_initcode), Spec.SALT_SIZE)
            + Op.SSTORE(
                outer_storage.store_next(1, "factory_call_success"),
                Op.CALL(
                    gas=Op.GAS,
                    address=FACTORY,
                    value=0,
                    args_offset=0,
                    args_size=inner_calldata_size,
                    ret_offset=0x100,
                    ret_size=RETURNED_ADDRESS_SIZE,
                ),
            )
            + Op.SSTORE(
                outer_storage.store_next(inner_address, "inner_address"),
                Op.MLOAD(0x100 - (32 - RETURNED_ADDRESS_SIZE)),
            )
        ),
        deploy_code=Op.STOP,
    )

    sender = pre.fund_eoa()
    post = {}
    factory_nonce = 2
    if creation_context == "tx":
        # Derive the address before building the transaction, which
        # advances the sender's nonce.
        outer_address = compute_create_address(
            address=sender, nonce=sender.nonce
        )
        tx = Transaction(sender=sender, to=None, data=bytes(outer_initcode))
    elif creation_context == "create":
        creator_storage = Storage()
        outer_address_slot = creator_storage.store_next(0, "outer_address")
        creator = pre.deploy_contract(
            Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE)
            + Op.SSTORE(outer_address_slot, Op.CREATE(0, 0, Op.CALLDATASIZE))
            + Op.STOP,
        )
        outer_address = compute_create_address(address=creator, nonce=1)
        creator_storage[outer_address_slot] = outer_address
        tx = Transaction(sender=sender, to=creator, data=bytes(outer_initcode))
        post[creator] = Account(storage=creator_storage)
    elif creation_context == "factory":
        outer_salt = 0x2222
        outer_address = compute_create2_address(
            FACTORY, outer_salt, outer_initcode
        )
        tx = Transaction(
            sender=sender,
            to=FACTORY,
            data=Hash(outer_salt) + bytes(outer_initcode),
        )
        factory_nonce = 3
    else:
        raise ValueError(creation_context)

    state_test(
        pre=pre,
        tx=tx,
        post={
            **post,
            outer_address: Account(
                nonce=1, code=bytes(Op.STOP), storage=outer_storage
            ),
            inner_address: Account(nonce=1, code=bytes(RUNTIME_CODE)),
            FACTORY: Account(
                nonce=factory_nonce,
                balance=0,
                code=Spec.FACTORY_BYTECODE,
            ),
        },
    )


def test_factory_deploys_to_pre_funded_address(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Preserve the funded address balance during CREATE2."""
    salt = 0x66
    runtime_code = Op.STOP
    initcode = Initcode(deploy_code=runtime_code)
    expected_address = compute_create2_address(FACTORY, salt, initcode)
    pre_balance = 1

    storage = Storage()
    caller = pre.deploy_contract(
        Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE)
        + Op.POP(
            Op.CALL(
                gas=Op.GAS,
                address=expected_address,
                value=pre_balance,
            )
        )
        + Op.SSTORE(
            storage.store_next(1, "factory_call_success"),
            Op.CALL(
                gas=Op.GAS,
                address=FACTORY,
                value=0,
                args_offset=0,
                args_size=Op.CALLDATASIZE,
                ret_offset=0x100,
                ret_size=32,
            ),
        )
        + Op.STOP,
        balance=pre_balance,
    )

    state_test(
        pre=pre,
        tx=Transaction(
            sender=pre.fund_eoa(),
            to=caller,
            data=Hash(salt) + bytes(initcode),
        ),
        post={
            caller: Account(storage=storage),
            expected_address: Account(
                nonce=1,
                balance=pre_balance,
                code=bytes(runtime_code),
            ),
        },
    )


def test_factory_receives_balance_via_selfdestruct(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Transfer a SELFDESTRUCT balance to the factory and then deploy through it.

    Preserve the received balance while CREATE2 advances the factory nonce.
    """
    forwarded_value = 1

    sd_actor = pre.deploy_contract(
        Op.SELFDESTRUCT(FACTORY),
        balance=forwarded_value,
    )

    salt = 0x88
    runtime_code = Op.STOP
    initcode = Initcode(deploy_code=runtime_code)
    expected_address = compute_create2_address(FACTORY, salt, initcode)

    storage = Storage()
    caller = pre.deploy_contract(
        Op.POP(Op.CALL(gas=Op.GAS, address=sd_actor))
        + Op.SSTORE(
            storage.store_next(forwarded_value, "factory_balance_after_sd"),
            Op.BALANCE(FACTORY),
        )
        + Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE)
        + Op.SSTORE(
            storage.store_next(1, "factory_call_success"),
            Op.CALL(
                gas=Op.GAS,
                address=FACTORY,
                value=0,
                args_offset=0,
                args_size=Op.CALLDATASIZE,
                ret_offset=0x100,
                ret_size=32,
            ),
        )
        + Op.STOP,
        storage=storage.canary(),
    )

    state_test(
        pre=pre,
        tx=Transaction(
            sender=pre.fund_eoa(),
            to=caller,
            data=Hash(salt) + bytes(initcode),
        ),
        post={
            caller: Account(storage=storage),
            FACTORY: Account(
                nonce=2,
                balance=forwarded_value,
                code=Spec.FACTORY_BYTECODE,
            ),
            expected_address: Account(
                nonce=1,
                code=bytes(runtime_code),
            ),
        },
    )


@EIPChecklist.SystemContract.Test.CallContexts.SetCode()
@pytest.mark.parametrize(
    "forwarded_value",
    [
        pytest.param(0, id="no_value"),
        pytest.param(1, id="with_value"),
    ],
)
def test_factory_via_eip7702_delegation(
    state_test: StateTestFiller,
    pre: Alloc,
    forwarded_value: int,
) -> None:
    """
    Execute delegated factory code with the authorized EOA as deployer.

    The delegated EOA funds the CREATE2 endowment from the forwarded value.
    """
    auth_signer = pre.fund_eoa(amount=0)
    auth_signer_nonce = auth_signer.nonce

    salt = 0x42
    runtime_code = Op.PUSH1(0x01) + Op.PUSH1(0x00) + Op.RETURN
    initcode = Initcode(deploy_code=runtime_code)
    expected_address = compute_create2_address(auth_signer, salt, initcode)

    caller = pre.deploy_contract(
        Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE)
        + Op.POP(
            Op.CALL(
                gas=Op.GAS,
                address=auth_signer,
                value=forwarded_value,
                args_offset=0,
                args_size=Op.CALLDATASIZE,
                ret_offset=0x100,
                ret_size=20,
            ),
        )
        + Op.STOP,
        balance=forwarded_value,
    )

    state_test(
        pre=pre,
        tx=Transaction(
            sender=pre.fund_eoa(),
            to=caller,
            data=Hash(salt) + bytes(initcode),
            authorization_list=[
                AuthorizationTuple(
                    address=Address(FACTORY),
                    nonce=auth_signer_nonce,
                    signer=auth_signer,
                ),
            ],
        ),
        post={
            auth_signer: Account(
                nonce=auth_signer_nonce + 2,
                balance=0,
                code=Spec7702.delegation_designation(Address(FACTORY)),
            ),
            caller: Account(balance=0),
            expected_address: Account(
                nonce=1,
                balance=forwarded_value,
                code=bytes(runtime_code),
            ),
            FACTORY: Account(
                nonce=1,
                balance=0,
                code=Spec.FACTORY_BYTECODE,
            ),
        },
    )


@EIPChecklist.SystemContract.Test.Inputs.Invalid(exact=True)
@EIPChecklist.SystemContract.Test.Inputs.Invalid.Checks()
def test_factory_rejects_ef_prefix_deployment(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Reject deployed code starting with 0xEF under EIP-3541.

    Revert the factory call when CREATE2 returns zero after code rejection.
    """
    salt = 0x3541
    deploy_code = Bytes(b"\xef\x00")
    initcode = Initcode(deploy_code=deploy_code)
    expected_address = compute_create2_address(FACTORY, salt, initcode)

    storage = Storage()
    caller = pre.deploy_contract(
        Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE)
        + Op.SSTORE(
            storage.store_next(0, "factory_call_failed"),
            Op.CALL(
                gas=Op.GAS,
                address=FACTORY,
                value=0,
                args_offset=0,
                args_size=Op.CALLDATASIZE,
            ),
        )
        + Op.STOP,
        storage=storage.canary(),
    )

    state_test(
        pre=pre,
        tx=Transaction(
            sender=pre.fund_eoa(),
            to=caller,
            data=Hash(salt) + bytes(initcode),
        ),
        post={
            caller: Account(storage=storage),
            expected_address: Account.NONEXISTENT,
        },
    )


@pytest.mark.parametrize(
    "oversize",
    [
        pytest.param(
            0,
            id="max",
            marks=EIPChecklist.SystemContract.Test.OutOfBounds.Max(),
        ),
        pytest.param(
            1,
            id="max_plus_one",
            marks=[
                EIPChecklist.SystemContract.Test.OutOfBounds.MaxPlusOne(),
                EIPChecklist.SystemContract.Test.Inputs.Invalid.Checks(),
            ],
        ),
    ],
)
def test_factory_initcode_size_boundary(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    oversize: int,
) -> None:
    """
    Deploy maximum-sized initcode and reject one additional byte.

    EIP-3860 raises OutOfGasError in CREATE2 for oversized initcode, which
    halts the factory frame before its own REVERT can execute.
    """
    gas_limit = fork.transaction_gas_limit_cap()
    assert gas_limit is not None

    salt = 0x55
    runtime_code = Op.STOP
    initcode = Initcode(
        deploy_code=runtime_code,
        initcode_length=fork.max_initcode_size() + oversize,
    )
    expected_address = compute_create2_address(FACTORY, salt, initcode)
    deploys = oversize == 0

    storage = Storage()
    call_gas = gas_limit // 8
    measured_call = Op.MSTORE(
        0x40,
        Op.CALL(
            gas=call_gas,
            address=FACTORY,
            args_size=Spec.SALT_SIZE + len(initcode),
            address_warm=False,
        ),
    )
    call = (
        measured_call
        if deploys
        else CodeGasMeasure(
            code=measured_call,
            sstore_key=storage.store_next(
                measured_call.execution_cost(fork) + call_gas,
                "call_gas_consumed",
            ),
        )
    )
    caller = pre.deploy_contract(
        Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE)
        + call
        + Op.SSTORE(
            storage.store_next(int(deploys), "factory_call_success"),
            Op.MLOAD(0x40),
        )
        + Op.SSTORE(
            storage.store_next(
                RETURNED_ADDRESS_SIZE if deploys else 0, "returndatasize"
            ),
            Op.RETURNDATASIZE,
        )
        + Op.STOP,
        storage=storage.canary(),
    )

    state_test(
        pre=pre,
        tx=Transaction(
            sender=pre.fund_eoa(),
            to=caller,
            data=Hash(salt) + bytes(initcode),
        ),
        post={
            caller: Account(storage=storage),
            FACTORY: Account(nonce=2 if deploys else 1, balance=0),
            expected_address: (
                Account(nonce=1, code=bytes(runtime_code))
                if deploys
                else Account.NONEXISTENT
            ),
        },
    )


@pytest.mark.parametrize(
    "creation_succeeds",
    [
        pytest.param(True, id="deploys"),
        pytest.param(False, id="initcode_reverts"),
    ],
)
def test_factory_block_access_list(
    state_test: StateTestFiller,
    pre: Alloc,
    creation_succeeds: bool,
) -> None:
    """
    Record factory and created-account nonce and code writes in the BAL.

    A reverted creation leaves the factory and the target address as
    accessed accounts without changes.
    """
    salt = 0x42
    runtime_code = Op.PUSH1(0x01) + Op.PUSH1(0x00) + Op.RETURN
    initcode: Bytecode = (
        Initcode(deploy_code=runtime_code)
        if creation_succeeds
        else Op.MSTORE(0, 0xDEADBEEF) + Op.REVERT(0, 32)
    )
    expected_address = compute_create2_address(FACTORY, salt, initcode)

    sender = pre.fund_eoa()

    state_test(
        pre=pre,
        tx=Transaction(
            sender=sender,
            to=Address(FACTORY),
            data=Hash(salt) + bytes(initcode),
        ),
        post={
            FACTORY: Account(
                nonce=2 if creation_succeeds else 1,
                balance=0,
                code=Spec.FACTORY_BYTECODE,
            ),
            expected_address: (
                Account(nonce=1, code=bytes(runtime_code))
                if creation_succeeds
                else Account.NONEXISTENT
            ),
        },
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                sender: BalAccountExpectation(
                    nonce_changes=[
                        BalNonceChange(block_access_index=1, post_nonce=1),
                    ],
                ),
                Address(FACTORY): (
                    BalAccountExpectation(
                        nonce_changes=[
                            BalNonceChange(block_access_index=1, post_nonce=2),
                        ],
                    )
                    if creation_succeeds
                    else BalAccountExpectation.empty()
                ),
                expected_address: (
                    BalAccountExpectation(
                        nonce_changes=[
                            BalNonceChange(block_access_index=1, post_nonce=1),
                        ],
                        code_changes=[
                            BalCodeChange(
                                block_access_index=1,
                                new_code=bytes(runtime_code),
                            ),
                        ],
                    )
                    if creation_succeeds
                    else BalAccountExpectation.empty()
                ),
            },
        ),
    )


def test_factory_block_access_list_address_collision(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Keep a reverted CREATE2 address collision out of the BAL.

    The colliding retry increments the factory nonce before the factory
    reverts, so the BAL records one nonce change and one creation.
    """
    salt = 0x42
    runtime_code = Op.PUSH1(0x01) + Op.PUSH1(0x00) + Op.RETURN
    initcode = Initcode(deploy_code=runtime_code)
    target = compute_create2_address(FACTORY, salt, initcode)

    storage = Storage()
    first_call_slot = storage.store_next(1, "first_call_success")
    second_call_slot = storage.store_next(0, "second_call_failed")
    factory_call = Op.CALL(
        gas=Op.GAS,
        address=FACTORY,
        value=0,
        args_offset=0,
        args_size=Op.CALLDATASIZE,
    )
    caller = pre.deploy_contract(
        Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE)
        + Op.SSTORE(first_call_slot, factory_call)
        + Op.SSTORE(second_call_slot, factory_call)
        + Op.STOP,
        storage=storage.canary(),
    )
    sender = pre.fund_eoa()

    state_test(
        pre=pre,
        tx=Transaction(
            sender=sender,
            to=caller,
            data=Hash(salt) + bytes(initcode),
        ),
        post={
            caller: Account(storage=storage),
            target: Account(nonce=1, code=bytes(runtime_code)),
            FACTORY: Account(
                nonce=2,
                balance=0,
                code=Spec.FACTORY_BYTECODE,
            ),
        },
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                sender: BalAccountExpectation(
                    nonce_changes=[
                        BalNonceChange(block_access_index=1, post_nonce=1),
                    ],
                ),
                caller: BalAccountExpectation(
                    storage_changes=[
                        BalStorageSlot(
                            slot=first_call_slot,
                            slot_changes=[
                                BalStorageChange(
                                    block_access_index=1, post_value=1
                                ),
                            ],
                        ),
                        BalStorageSlot(
                            slot=second_call_slot,
                            slot_changes=[
                                BalStorageChange(
                                    block_access_index=1, post_value=0
                                ),
                            ],
                        ),
                    ],
                ),
                Address(FACTORY): BalAccountExpectation(
                    nonce_changes=[
                        BalNonceChange(block_access_index=1, post_nonce=2),
                    ],
                ),
                target: BalAccountExpectation(
                    nonce_changes=[
                        BalNonceChange(block_access_index=1, post_nonce=1),
                    ],
                    code_changes=[
                        BalCodeChange(
                            block_access_index=1,
                            new_code=bytes(runtime_code),
                        ),
                    ],
                ),
            },
        ),
    )


@EIPChecklist.SystemContract.Test.CallContexts.SetCode()
def test_delegated_sender_forwards_value(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Forward a delegated EOA's call value through the canonical factory."""
    authority = pre.fund_eoa(amount=0)
    value = 1
    salt = 0x7702
    initcode = Initcode(deploy_code=RUNTIME_CODE)
    target = compute_create2_address(FACTORY, salt, initcode)
    storage = Storage()
    implementation = pre.deploy_contract(
        Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE)
        + Op.SSTORE(
            storage.store_next(1, "factory_call_success"),
            Op.CALL(
                gas=Op.GAS,
                address=FACTORY,
                value=Op.CALLVALUE,
                args_size=Op.CALLDATASIZE,
                ret_offset=0x10C,
                ret_size=RETURNED_ADDRESS_SIZE,
            ),
        )
        + Op.SSTORE(storage.store_next(target), Op.MLOAD(0x100))
        + Op.SSTORE(
            storage.store_next(RETURNED_ADDRESS_SIZE), Op.RETURNDATASIZE
        )
    )
    state_test(
        pre=pre,
        tx=Transaction(
            sender=pre.fund_eoa(),
            to=authority,
            value=value,
            data=Hash(salt) + bytes(initcode),
            authorization_list=[
                AuthorizationTuple(
                    address=implementation,
                    nonce=authority.nonce,
                    signer=authority,
                )
            ],
        ),
        post={
            authority: Account(nonce=1, balance=0, storage=storage),
            implementation: Account(nonce=1, balance=0, storage={}),
            FACTORY: Account(nonce=2, balance=0),
            target: Account(nonce=1, balance=value, code=RUNTIME_CODE),
            compute_create2_address(authority, salt, initcode): (
                Account.NONEXISTENT
            ),
        },
    )
