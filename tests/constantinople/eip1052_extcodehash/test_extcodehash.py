"""
Test EIP-1052 EXTCODEHASH.
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Bytecode,
    Initcode,
    Op,
    Opcodes,
    StateTestFiller,
    Storage,
    Transaction,
    compute_create2_address,
    compute_create_address,
)
from execution_testing.forks import Cancun
from execution_testing.forks.helpers import Fork

from ethereum.crypto.hash import keccak256

REFERENCE_SPEC_GIT_PATH = "EIPS/eip-1052.md"
REFERENCE_SPEC_VERSION = "2dcbc7ce1563e9624e137e9d447374600af876fa"

pytestmark = [
    pytest.mark.valid_from("ConstantinopleFix"),
]


@pytest.mark.ported_from(
    [
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stExtCodeHash/extCodeHashSelfFiller.json",  # noqa: E501
    ],
    pr=["https://github.com/ethereum/execution-specs/pull/2249"],
)
def test_extcodehash_self(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Test EXTCODEHASH/EXTCODESIZE of the currently executing account.
    """
    storage = Storage()
    slot_hash = storage.store_next(0)
    slot_size = storage.store_next(0)

    code = Op.SSTORE(slot_hash, Op.EXTCODEHASH(Op.ADDRESS)) + Op.SSTORE(
        slot_size, Op.EXTCODESIZE(Op.ADDRESS)
    )

    storage[slot_hash] = code.keccak256()
    storage[slot_size] = len(code)

    code_address = pre.deploy_contract(code, storage=storage.canary())

    tx = Transaction(
        sender=pre.fund_eoa(),
        to=code_address,
        gas_limit=400_000,
    )

    state_test(
        pre=pre,
        post={code_address: Account(storage=storage)},
        tx=tx,
    )


@pytest.mark.ported_from(
    [
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stExtCodeHash/extCodeHashNonExistingAccountFiller.yml",  # noqa: E501
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stExtCodeHash/extCodeHashAccountWithoutCodeFiller.yml",  # noqa: E501
    ],
    pr=["https://github.com/ethereum/execution-specs/pull/2237"],
)
@pytest.mark.parametrize("target_exists", [True, False])
def test_extcodehash_of_empty(
    state_test: StateTestFiller,
    pre: Alloc,
    target_exists: bool,
) -> None:
    """
    Test EXTCODEHASH/EXTCODESIZE for non-existent and empty accounts.
    """
    storage = Storage()
    target_address = pre.empty_account()

    if target_exists:
        pre.fund_address(target_address, 1)

    expected_hash = keccak256(b"") if target_exists else 0
    code = Op.SSTORE(
        storage.store_next(expected_hash),
        Op.EXTCODEHASH(target_address),
    ) + Op.SSTORE(
        storage.store_next(0),
        Op.EXTCODESIZE(target_address),
    )

    code_address = pre.deploy_contract(code, storage=storage.canary())

    tx = Transaction(
        sender=(pre.fund_eoa()),
        to=code_address,
        value=1,
        gas_limit=400_000,
    )

    state_test(
        pre=pre,
        post={
            code_address: Account(storage=storage),
        },
        tx=tx,
    )


@pytest.mark.ported_from(
    [
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stExtCodeHash/extcodehashEmpty_ParisFiller.yml",  # noqa: E501
    ],
    pr=["https://github.com/ethereum/execution-specs/pull/2237"],
)
def test_extcodehash_empty_send_value(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Test EXTCODEHASH of non-existent account before and after sending value.

    Verify that EXTCODEHASH transitions from 0 to keccak256("") when
    the account receives value within the same transaction.
    """
    storage = Storage()
    target_address = pre.empty_account()

    code = (
        # EXTCODEHASH before sending value: expect 0 (non-existent).
        Op.SSTORE(
            storage.store_next(0),
            Op.EXTCODEHASH(target_address),
        )
        # Send 1 wei to target, creating the account.
        + Op.CALL(gas=Op.GAS, address=target_address, value=1)
        # EXTCODEHASH after sending value: expect keccak256("").
        + Op.SSTORE(
            storage.store_next(keccak256(b"")),
            Op.EXTCODEHASH(target_address),
        )
    )

    code_address = pre.deploy_contract(
        code, balance=10**18, storage=storage.canary()
    )

    tx = Transaction(
        sender=pre.fund_eoa(),
        to=code_address,
        gas_limit=400_000,
    )

    state_test(
        pre=pre,
        post={
            code_address: Account(storage=storage),
        },
        tx=tx,
    )


@pytest.mark.ported_from(
    [
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stExtCodeHash/extcodehashEmpty_ParisFiller.yml",  # noqa: E501
    ],
    pr=["https://github.com/ethereum/execution-specs/pull/2237"],
)
@pytest.mark.pre_alloc_mutable
@pytest.mark.parametrize(
    "account,call_before,expected_hash,expected_size,expected_copy",
    [
        pytest.param(
            Account(nonce=1),
            False,
            keccak256(b""),
            0,
            0,
            id="nonce-only",
        ),
        pytest.param(
            Account(balance=1),
            False,
            keccak256(b""),
            0,
            0,
            id="balance-only",
        ),
        pytest.param(
            Account(
                balance=10,
                storage={0x00: 0x01000000, 0xFFFFFFF: 0xFFFFFFFF},
            ),
            False,
            keccak256(b""),
            0,
            0,
            id="balance-storage",
        ),
        pytest.param(
            Account(code=Op.STOP),
            False,
            keccak256(bytes(Op.STOP)),
            1,
            0,
            id="single-byte-code",
        ),
        pytest.param(
            Account(balance=100, code=Op.PUSH2(0x60A7) + Op.SELFDESTRUCT),
            True,
            keccak256(bytes(Op.PUSH2(0x60A7) + Op.SELFDESTRUCT)),
            4,
            bytes(Op.PUSH2(0x60A7) + Op.SELFDESTRUCT).ljust(32, b"\0"),
            id="selfdestruct",
        ),
    ],
)
def test_extcodehash_empty_account_variants(
    state_test: StateTestFiller,
    pre: Alloc,
    account: Account,
    call_before: bool,
    expected_hash: bytes,
    expected_size: int,
    expected_copy: int | bytes,
) -> None:
    """
    Test EXTCODEHASH/EXTCODESIZE/EXTCODECOPY for empty-account variants.
    """
    storage = Storage()
    target_address = pre.empty_account()
    pre[target_address] = account

    code = Op.JUMPDEST + (
        Op.CALL(gas=Op.GAS, address=target_address, value=0)
        if call_before
        else Op.NOOP
    )

    code += (
        Op.SSTORE(
            storage.store_next(expected_size),
            Op.EXTCODESIZE(target_address),
        )
        + Op.SSTORE(
            storage.store_next(expected_hash),
            Op.EXTCODEHASH(target_address),
        )
        + Op.EXTCODECOPY(target_address, 0, 0, 32)
        + Op.SSTORE(
            storage.store_next(expected_copy),
            Op.MLOAD(0),
        )
    )

    code_address = pre.deploy_contract(
        code, balance=10**18, storage=storage.canary()
    )

    tx = Transaction(
        sender=pre.fund_eoa(),
        to=code_address,
        value=1,
        gas_limit=400_000,
    )

    state_test(
        pre=pre,
        post={
            code_address: Account(storage=storage),
        },
        tx=tx,
    )


@pytest.mark.ported_from(
    [
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stExtCodeHash/extcodehashEmpty_ParisFiller.yml",  # noqa: E501
    ],
    pr=["https://github.com/ethereum/execution-specs/pull/2237"],
)
@pytest.mark.parametrize("opcode", [Op.CREATE, Op.CREATE2])
def test_extcodehash_empty_contract_creation(
    state_test: StateTestFiller,
    pre: Alloc,
    opcode: Op,
) -> None:
    """
    Test EXTCODEHASH/EXTCODESIZE for empty contracts created with
    CREATE/CREATE2.
    """
    storage = Storage()
    initcode = Op.RETURN(0, 0)
    expected_hash = keccak256(b"")

    created_slot = storage.store_next(0)
    hash_slot = storage.store_next(expected_hash)
    size_slot = storage.store_next(0)
    copy_slot = storage.store_next(0)

    create_op = (
        opcode(value=0, offset=0, size=len(initcode), salt=0)
        if opcode == Op.CREATE2
        else opcode(value=0, offset=0, size=len(initcode))
    )

    code = (
        Op.MSTORE(0, Op.PUSH32(bytes(initcode).ljust(32, b"\0")))
        + Op.SSTORE(created_slot, create_op)
        + Op.SSTORE(
            hash_slot,
            Op.EXTCODEHASH(Op.SLOAD(created_slot)),
        )
        + Op.SSTORE(
            size_slot,
            Op.EXTCODESIZE(Op.SLOAD(created_slot)),
        )
        + Op.EXTCODECOPY(Op.SLOAD(created_slot), 0, 0, 32)
        + Op.SSTORE(copy_slot, Op.MLOAD(0))
        + Op.STOP
    )

    code_address = pre.deploy_contract(code, storage=storage.canary())
    created_address = (
        compute_create2_address(
            address=code_address,
            salt=0,
            initcode=initcode,
        )
        if opcode == Op.CREATE2
        else compute_create_address(address=code_address, nonce=1)
    )
    storage[created_slot] = created_address

    tx = Transaction(
        sender=pre.fund_eoa(),
        to=code_address,
        gas_limit=400_000,
    )

    state_test(
        pre=pre,
        post={
            code_address: Account(storage=storage),
            created_address: Account(nonce=1, code=b""),
        },
        tx=tx,
    )


@pytest.mark.ported_from(
    [
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stExtCodeHash/dynamicAccountOverwriteEmpty_ParisFiller.yml",  # noqa: E501
    ],
    pr=["https://github.com/ethereum/execution-specs/pull/2291"],
)
@pytest.mark.pre_alloc_mutable
@pytest.mark.parametrize(
    "balance, nonce",
    [
        pytest.param(1, 0, id="balance"),
        pytest.param(0, 1, id="nonce"),
        pytest.param(1, 1, id="balance_and_nonce"),
    ],
)
def test_extcodehash_codeless_with_storage(
    state_test: StateTestFiller,
    pre: Alloc,
    balance: int,
    nonce: int,
) -> None:
    """
    Test EXTCODEHASH/EXTCODESIZE of a codeless account that has storage.

    All three variants are non-empty per EIP-161 (non-zero balance or nonce),
    so EXTCODEHASH returns keccak256("") and EXTCODESIZE returns 0.
    Storage is not part of the EIP-161 emptiness check.
    """
    target_address = pre.empty_account()
    pre[target_address] = Account(balance=balance, nonce=nonce, storage={1: 1})

    storage = Storage()
    code = Op.SSTORE(
        storage.store_next(keccak256(b"")),
        Op.EXTCODEHASH(target_address),
    ) + Op.SSTORE(
        storage.store_next(0),
        Op.EXTCODESIZE(target_address),
    )

    code_address = pre.deploy_contract(code, storage=storage.canary())

    tx = Transaction(
        sender=pre.fund_eoa(),
        to=code_address,
        gas_limit=100_000,
    )

    state_test(
        pre=pre,
        post={code_address: Account(storage=storage)},
        tx=tx,
    )


@pytest.mark.ported_from(
    [
        "https://github.com/ethereum/tests/tree/v13.3/src/GeneralStateTestsFiller/stExtCodeHash/dynamicAccountOverwriteEmpty_ParisFiller.yml",  # noqa: E501
    ],
    pr=["https://github.com/ethereum/execution-specs/pull/2032"],
)
@pytest.mark.parametrize(
    "target_exists",
    [True, False],
)
def test_extcodehash_dynamic_account_overwrite(
    state_test: StateTestFiller,
    pre: Alloc,
    target_exists: bool,
) -> None:
    """
    Test EXTCODEHASH of non-existent/no-code account,
    then with code deployed at the address via CREATE2.

    This verifies that the code hash cache is correctly updated during the
    transaction when an account is overwritten by CREATE2.

    The target address is computed after the caller contract code is deployed,
    and passed as calldata to the caller contract.

    The target account code sets a fixed storage slot. This code is executed
    at the caller account via DELEGATECALL and at the target account via CALL.

    Modified from original test: target account has no storage to avoid
    EIP-7610 collision behavior.
    """
    target_storage_slot = 0x4A
    caller_storage = Storage()
    target_storage = Storage()

    deploy_code = Op.SSTORE(target_storage_slot, 1)
    create2_initcode = Initcode(deploy_code=deploy_code)

    caller_code = (
        # EXTCODEHASH of the pre-CREATE2 target account.
        Op.SSTORE(
            caller_storage.store_next(keccak256(b"") if target_exists else 0),
            Op.EXTCODEHASH(Op.CALLDATALOAD(0)),
        )
        # EXTCODESIZE of target account.
        + Op.SSTORE(
            caller_storage.store_next(0), Op.EXTCODESIZE(Op.CALLDATALOAD(0))
        )
        # EXTCODECOPY of target account.
        + Op.EXTCODECOPY(Op.CALLDATALOAD(0), 0, 0, 32)
        + Op.SSTORE(caller_storage.store_next(0), Op.MLOAD(0))
        # DELEGATECALL the target account.
        + Op.SSTORE(
            caller_storage.store_next(1),
            Op.DELEGATECALL(
                address=Op.CALLDATALOAD(0),
                gas=0,  # Pass zero gas to ensure no execution.
            ),
        )
    )
    # Target address to be set later.
    target_address_slot = caller_storage.store_next(0, "target_address")
    caller_code += (
        # CREATE2 to overwrite the account
        Op.MSTORE(0, Op.PUSH32(bytes(create2_initcode).ljust(32, b"\0")))
        + Op.SSTORE(
            target_address_slot,
            Op.CREATE2(value=0, offset=0, size=len(create2_initcode), salt=0),
        )
        # EXTCODEHASH of the target account.
        + Op.SSTORE(
            caller_storage.store_next(deploy_code.keccak256()),
            Op.EXTCODEHASH(Op.CALLDATALOAD(0)),
        )
        # EXTCODESIZE of the target account.
        + Op.SSTORE(
            caller_storage.store_next(len(deploy_code)),
            Op.EXTCODESIZE(Op.CALLDATALOAD(0)),
        )
        # EXTCODECOPY of the target account.
        + Op.EXTCODECOPY(Op.CALLDATALOAD(0), 0, 0, 32)
        + Op.SSTORE(
            caller_storage.store_next(bytes(deploy_code).ljust(32, b"\0")),
            Op.MLOAD(0),
        )
        # DELEGATECALL the target account.
        + Op.SSTORE(
            caller_storage.store_next(1),
            Op.DELEGATECALL(
                address=Op.CALLDATALOAD(0),
                gas=Op.GAS,
            ),
        )
        # Call the deployed contract to execute its "deploy_code".
        + Op.SSTORE(
            caller_storage.store_next(1),
            Op.CALL(address=Op.CALLDATALOAD(0), gas=Op.GAS),
        )
    )

    caller_address = pre.deploy_contract(
        caller_code, balance=1, storage=caller_storage.canary()
    )

    target_address = compute_create2_address(
        address=caller_address,
        salt=0,
        initcode=create2_initcode,
    )

    if target_exists:
        pre.fund_address(target_address, 1)

    caller_storage[target_address_slot] = target_address
    caller_storage[target_storage_slot] = 1
    target_storage[target_storage_slot] = 1

    sender = pre.fund_eoa()
    tx = Transaction(
        sender=sender,
        to=caller_address,
        data=bytes(target_address).rjust(32, b"\0"),
        gas_limit=400_000,
    )

    state_test(
        pre=pre,
        post={
            caller_address: Account(storage=caller_storage),
            target_address: Account(
                nonce=1,
                code=deploy_code,
                storage=target_storage,
            ),
        },
        tx=tx,
    )


@pytest.mark.ported_from(
    [
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stExtCodeHash/extCodeHashPrecompilesFiller.yml",  # noqa: E501
    ],
    pr=["https://github.com/ethereum/execution-specs/pull/2302"],
)
@pytest.mark.with_all_precompiles
def test_extcodehash_precompile(
    state_test: StateTestFiller,
    pre: Alloc,
    precompile: Address,
) -> None:
    """
    Test EXTCODEHASH/EXTCODESIZE of precompile addresses.

    Precompiles have no associated code, so both return 0.
    """
    storage = Storage()

    code = Op.SSTORE(
        storage.store_next(0),
        Op.EXTCODEHASH(precompile),
    ) + Op.SSTORE(
        storage.store_next(0),
        Op.EXTCODESIZE(precompile),
    )

    code_address = pre.deploy_contract(code, storage=storage.canary())

    tx = Transaction(
        sender=pre.fund_eoa(),
        to=code_address,
        gas_limit=400_000,
    )

    state_test(
        pre=pre,
        post={code_address: Account(storage=storage)},
        tx=tx,
    )


@pytest.mark.ported_from(
    [
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stExtCodeHash/extCodeHashNewAccountFiller.json",  # noqa: E501
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stExtCodeHash/createEmptyThenExtcodehashFiller.json",  # noqa: E501
    ],
    pr=["https://github.com/ethereum/execution-specs/pull/2326"],
)
@pytest.mark.parametrize("opcode", [Op.CREATE, Op.CREATE2])
@pytest.mark.parametrize(
    "deployed_code",
    [
        pytest.param((0x1234).to_bytes(32, "big"), id="non-empty"),
        pytest.param(b"", id="empty"),
    ],
)
def test_extcodehash_new_account(
    state_test: StateTestFiller,
    pre: Alloc,
    deployed_code: bytes,
    opcode: Opcodes,
) -> None:
    """
    Test EXTCODEHASH/EXTCODESIZE of a contract created within the same tx.

    Uses CREATE/CREATE2 to deploy a contract, then verifies that EXTCODEHASH
    and EXTCODESIZE reflect the newly deployed code.
    """
    storage = Storage()

    initcode = Op.MSTORE(
        0, int.from_bytes(deployed_code.ljust(32, b"\0"), "big")
    ) + Op.RETURN(0, len(deployed_code))

    created_slot = storage.store_next(0)
    hash_slot = storage.store_next(keccak256(deployed_code))
    size_slot = storage.store_next(len(deployed_code))

    code = (
        Op.MSTORE(0, Op.PUSH32(bytes(initcode).ljust(32, b"\0")))
        + Op.SSTORE(
            created_slot,
            opcode(value=0, offset=0, size=len(initcode)),
        )
        + Op.SSTORE(hash_slot, Op.EXTCODEHASH(Op.SLOAD(created_slot)))
        + Op.SSTORE(size_slot, Op.EXTCODESIZE(Op.SLOAD(created_slot)))
        + Op.STOP
    )

    code_address = pre.deploy_contract(code, storage=storage.canary())
    created_address = compute_create_address(
        address=code_address,
        nonce=1,
        salt=0,
        initcode=initcode,
        opcode=opcode,
    )
    storage[created_slot] = created_address

    tx = Transaction(
        sender=pre.fund_eoa(),
        to=code_address,
        gas_limit=400_000,
    )

    state_test(
        pre=pre,
        post={
            code_address: Account(storage=storage),
            created_address: Account(nonce=1, code=deployed_code),
        },
        tx=tx,
    )


@pytest.mark.ported_from(
    [
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stExtCodeHash/extCodeHashCALLFiller.json",  # noqa: E501
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stExtCodeHash/extCodeHashCALLCODEFiller.json",  # noqa: E501
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stExtCodeHash/extCodeHashDELEGATECALLFiller.json",  # noqa: E501
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stExtCodeHash/extCodeHashSTATICCALLFiller.json",  # noqa: E501
    ],
    pr=["https://github.com/ethereum/execution-specs/pull/2348"],
)
@pytest.mark.parametrize(
    "opcode",
    [Op.CALL, Op.CALLCODE, Op.DELEGATECALL, Op.STATICCALL],
)
def test_extcodehash_via_call(
    state_test: StateTestFiller,
    pre: Alloc,
    opcode: Opcodes,
) -> None:
    """
    Test EXTCODEHASH/EXTCODESIZE queried via different call types.

    A helper contract computes EXTCODEHASH and EXTCODESIZE of a target
    and returns them. The caller invokes the helper using the
    parametrized call type and stores the results.
    """
    storage = Storage()
    target_code = b"\x12\x34"
    target_address = pre.deploy_contract(target_code)

    helper_code = (
        Op.MSTORE(0, Op.EXTCODEHASH(target_address))
        + Op.MSTORE(32, Op.EXTCODESIZE(target_address))
        + Op.RETURN(0, 64)
    )
    helper_address = pre.deploy_contract(helper_code)

    code = (
        opcode(address=helper_address, gas=150_000)
        + Op.RETURNDATACOPY(0, 0, 64)
        + Op.SSTORE(
            storage.store_next(keccak256(target_code)),
            Op.MLOAD(0),
        )
        + Op.SSTORE(
            storage.store_next(len(target_code)),
            Op.MLOAD(32),
        )
    )

    code_address = pre.deploy_contract(code, storage=storage.canary())

    tx = Transaction(
        sender=pre.fund_eoa(),
        to=code_address,
        gas_limit=400_000,
    )

    state_test(
        pre=pre,
        post={code_address: Account(storage=storage)},
        tx=tx,
    )


@pytest.mark.ported_from(
    [
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stExtCodeHash/extCodeHashDeletedAccountFiller.yml",  # noqa: E501
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stExtCodeHash/extCodeHashDeletedAccount1Filler.yml",  # noqa: E501
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stExtCodeHash/extCodeHashDeletedAccount2Filler.yml",  # noqa: E501
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stExtCodeHash/extCodeHashDeletedAccountCancunFiller.yml",  # noqa: E501
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stExtCodeHash/extCodeHashDeletedAccount1CancunFiller.yml",  # noqa: E501
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stExtCodeHash/extCodeHashDeletedAccount2CancunFiller.yml",  # noqa: E501
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stExtCodeHash/extCodeHashDeletedAccount3Filler.yml",  # noqa: E501
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stExtCodeHash/extCodeHashDeletedAccount4Filler.yml",  # noqa: E501
    ],
    pr=["https://github.com/ethereum/execution-specs/pull/2366"],
)
@pytest.mark.parametrize(
    "create_opcode",
    [
        pytest.param(None, id="pre_existing"),
        pytest.param(Op.CREATE, id="create"),
        pytest.param(Op.CREATE2, id="create2"),
    ],
)
def test_extcodehash_after_selfdestruct(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    create_opcode: Opcodes | None,
) -> None:
    """
    Test EXTCODEHASH/EXTCODESIZE/EXTCODECOPY before and after SELFDESTRUCT.

    Verifies that code hash, size, and copied code remain unchanged
    within the transaction after SELFDESTRUCT is triggered.
    Pre-Cancun, all selfdestructed accounts are deleted. From Cancun
    (EIP-6780), only accounts created in the same transaction are
    deleted; pre-existing accounts persist with balance drained.
    """
    storage = Storage()
    target_runtime = Op.SELFDESTRUCT(Op.ORIGIN)
    expected_hash = keccak256(bytes(target_runtime))
    expected_size = len(target_runtime)
    expected_code = bytes(target_runtime).ljust(32, b"\0")

    code = Bytecode()
    if create_opcode is None:
        target_address = pre.deploy_contract(target_runtime, balance=1)
        target: Address | Bytecode = target_address
    else:
        initcode = Initcode(deploy_code=target_runtime)
        created_slot = storage.store_next(0)
        target = Op.SLOAD(created_slot)
        code += Op.MSTORE(
            0,
            Op.PUSH32(bytes(initcode).ljust(32, b"\0")),
        ) + Op.SSTORE(
            created_slot,
            create_opcode(value=0, offset=0, size=len(initcode)),
        )

    def extcode_checks() -> Bytecode:
        return (
            Op.SSTORE(
                storage.store_next(expected_hash),
                Op.EXTCODEHASH(target),
            )
            + Op.SSTORE(
                storage.store_next(expected_size),
                Op.EXTCODESIZE(target),
            )
            + Op.MSTORE(0, 0)
            + Op.EXTCODECOPY(target, 0, 0, len(target_runtime))
            + Op.SSTORE(
                storage.store_next(expected_code),
                Op.MLOAD(0),
            )
        )

    code += extcode_checks()
    code += Op.CALL(address=target, gas=100_000) + Op.POP
    code += extcode_checks()

    code_address = pre.deploy_contract(code, storage=storage.canary())

    if create_opcode is not None:
        target_address = compute_create_address(
            address=code_address,
            nonce=1,
            salt=0,
            initcode=initcode,
            opcode=create_opcode,
        )
        storage[created_slot] = target_address

    tx = Transaction(
        sender=pre.fund_eoa(),
        to=code_address,
        gas_limit=400_000,
    )

    post: dict[Address, Account | None] = {
        code_address: Account(storage=storage),
    }
    if create_opcode is None and fork >= Cancun:
        # EIP-6780: pre-existing account persists after SELFDESTRUCT.
        post[target_address] = Account(balance=0, code=target_runtime)
    else:
        post[target_address] = Account.NONEXISTENT

    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    [
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stExtCodeHash/extCodeHashChangedAccountFiller.json",  # noqa: E501
    ],
    pr=["https://github.com/ethereum/execution-specs/pull/2394"],
)
def test_extcodehash_changed_account(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Test EXTCODEHASH/EXTCODESIZE before and after changing account state.

    A secondary contract has its nonce incremented (via CREATE), balance
    increased (via CALL value), and storage modified (via SSTORE) when
    called. The caller verifies that EXTCODEHASH and EXTCODESIZE return
    the same values before and after these mutations.
    """
    storage = Storage()

    # CREATE bumps nonce, receives value, sets storage.
    secondary_code = Op.CREATE(value=0, offset=0, size=0) + Op.SSTORE(
        0, 0x1234
    )
    secondary = pre.deploy_contract(secondary_code)

    expected_hash = keccak256(bytes(secondary_code))
    expected_size = len(secondary_code)

    def extcode_checks() -> Bytecode:
        return Op.SSTORE(
            storage.store_next(expected_hash),
            Op.EXTCODEHASH(secondary),
        ) + Op.SSTORE(
            storage.store_next(expected_size),
            Op.EXTCODESIZE(secondary),
        )

    code = (
        extcode_checks()
        + Op.CALL(gas=Op.GAS, address=secondary, value=1)
        + Op.POP
        + extcode_checks()
    )

    code_address = pre.deploy_contract(
        code, balance=1, storage=storage.canary()
    )

    tx = Transaction(
        sender=pre.fund_eoa(),
        to=code_address,
        gas_limit=400_000,
    )

    state_test(
        pre=pre,
        post={
            code_address: Account(storage=storage),
            secondary: Account(
                nonce=2,
                balance=1,
                storage={0: 0x1234},
            ),
        },
        tx=tx,
    )


@pytest.mark.ported_from(
    [
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stExtCodeHash/extCodeHashMaxCodeSizeFiller.yml",  # noqa: E501
    ],
    pr=["https://github.com/ethereum/execution-specs/pull/2397"],
)
@pytest.mark.parametrize("code_byte", [0x00, 0xFE], ids=["stop", "invalid"])
@pytest.mark.parametrize("size_delta", [0, 1], ids=["max", "max_minus_1"])
def test_extcodehash_max_code_size(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    code_byte: int,
    size_delta: int,
) -> None:
    """
    Test EXTCODEHASH/EXTCODESIZE of a contract near max code size.

    Deploy a contract with MAXCODESIZE or MAXCODESIZE-1 bytes of code
    filled with a single byte pattern and verify that EXTCODEHASH and
    EXTCODESIZE return the correct values.
    """
    storage = Storage()
    target_code = bytes([code_byte] * (fork.max_code_size() - size_delta))
    target = pre.deploy_contract(target_code)

    code = Op.SSTORE(
        storage.store_next(keccak256(target_code)),
        Op.EXTCODEHASH(target),
    ) + Op.SSTORE(
        storage.store_next(len(target_code)),
        Op.EXTCODESIZE(target),
    )

    code_address = pre.deploy_contract(code, storage=storage.canary())

    tx = Transaction(
        sender=pre.fund_eoa(),
        to=code_address,
        gas_limit=400_000,
    )

    state_test(
        pre=pre,
        post={code_address: Account(storage=storage)},
        tx=tx,
    )


@pytest.mark.ported_from(
    [
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stExtCodeHash/extCodeHashDynamicArgumentFiller.json",  # noqa: E501
    ],
    pr=["https://github.com/ethereum/execution-specs/pull/2379"],
)
@pytest.mark.parametrize(
    "target_type",
    [
        "precompile",
        "precompile_with_balance",
        "contract",
        "eoa",
        "nonexistent",
    ],
)
def test_extcodehash_dynamic_argument(
    state_test: StateTestFiller,
    pre: Alloc,
    target_type: str,
) -> None:
    """
    Test EXTCODEHASH/EXTCODESIZE with address loaded dynamically from calldata.

    The target address is not hardcoded in bytecode but read via
    CALLDATALOAD at runtime. Five target types are tested: a precompile
    with no state, a precompile with balance, a contract with code,
    an EOA with balance, and a non-existent address.
    """
    storage = Storage()
    target_code = b"\x12\x34"

    if target_type == "precompile":
        target_address = Address(1)
        expected_hash: int | bytes = 0
        expected_size = 0
    elif target_type == "precompile_with_balance":
        target_address = Address(2)
        pre.fund_address(target_address, 1)
        expected_hash = keccak256(b"")
        expected_size = 0
    elif target_type == "contract":
        target_address = pre.deploy_contract(target_code)
        expected_hash = keccak256(target_code)
        expected_size = len(target_code)
    elif target_type == "eoa":
        target_address = pre.fund_eoa(amount=1)
        expected_hash = keccak256(b"")
        expected_size = 0
    else:  # nonexistent
        target_address = pre.fund_eoa(amount=0)
        expected_hash = 0
        expected_size = 0

    code = Op.SSTORE(
        storage.store_next(expected_hash),
        Op.EXTCODEHASH(Op.CALLDATALOAD(0)),
    ) + Op.SSTORE(
        storage.store_next(expected_size),
        Op.EXTCODESIZE(Op.CALLDATALOAD(0)),
    )

    code_address = pre.deploy_contract(code, storage=storage.canary())

    tx = Transaction(
        sender=pre.fund_eoa(),
        to=code_address,
        data=bytes(target_address).rjust(32, b"\0"),
        gas_limit=400_000,
    )

    state_test(
        pre=pre,
        post={code_address: Account(storage=storage)},
        tx=tx,
    )
