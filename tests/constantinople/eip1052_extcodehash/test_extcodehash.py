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
from execution_testing import (
    Macros as Om,
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
@pytest.mark.eels_base_coverage
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
    target_address = pre.nonexistent_account()

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
    target_address = pre.nonexistent_account()

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
    target_address = pre.nonexistent_account()
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
    target_address = pre.nonexistent_account()
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
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stExtCodeHash/extCodeHashInInitCodeFiller.json",  # noqa: E501
    ],
)
@pytest.mark.parametrize(
    "create_opcode",
    [pytest.param(None, id="create_tx"), Op.CREATE, Op.CREATE2],
)
def test_extcodehash_in_init_code(
    state_test: StateTestFiller,
    pre: Alloc,
    create_opcode: Opcodes | None,
) -> None:
    """
    Test EXTCODEHASH/EXTCODESIZE of an external account during init code.

    The init code queries EXTCODEHASH and EXTCODESIZE of a pre-existing
    contract and stores the results. With a create transaction the checks
    run in the top-level init code; with CREATE/CREATE2 they run in a
    contract-initiated creation.
    """
    storage = Storage()
    target_code = b"\x11\x22\x33\x44"
    target = pre.deploy_contract(target_code)

    expected_hash = keccak256(target_code)
    expected_size = len(target_code)

    # Init code: execute EXTCODEHASH/EXTCODESIZE checks, then deploy.
    checks = Op.SSTORE(
        storage.store_next(expected_hash),
        Op.EXTCODEHASH(target),
    ) + Op.SSTORE(
        storage.store_next(expected_size),
        Op.EXTCODESIZE(target),
    )
    initcode = checks + Op.RETURN(0, 0)

    if create_opcode is None:
        # Transaction-level creation: init code runs directly.
        sender = pre.fund_eoa()
        tx = Transaction(
            sender=sender,
            to=None,
            data=initcode,
            gas_limit=400_000,
        )
        created = compute_create_address(
            address=sender,
            nonce=0,
        )
    else:
        # Contract-initiated CREATE/CREATE2: copy initcode from calldata.
        factory_code = (
            Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE)
            + create_opcode(
                value=0,
                offset=0,
                size=Op.CALLDATASIZE,
            )
            + Op.STOP
        )
        factory = pre.deploy_contract(factory_code)
        tx = Transaction(
            sender=pre.fund_eoa(),
            to=factory,
            data=initcode,
            gas_limit=400_000,
        )
        created = compute_create_address(
            address=factory,
            nonce=1,
            salt=0,
            initcode=initcode,
            opcode=create_opcode,
        )

    state_test(
        pre=pre,
        post={created: Account(storage=storage)},
        tx=tx,
    )


@pytest.mark.ported_from(
    [
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stExtCodeHash/extCodeHashSelfInInitFiller.json",  # noqa: E501
    ],
)
@pytest.mark.parametrize(
    "create_opcode",
    [pytest.param(None, id="create_tx"), Op.CREATE, Op.CREATE2],
)
def test_extcodehash_self_in_init(
    state_test: StateTestFiller,
    pre: Alloc,
    create_opcode: Opcodes | None,
) -> None:
    """
    Test EXTCODEHASH/EXTCODESIZE of self during init code.

    During init code execution the account exists but has no code yet,
    so EXTCODEHASH(ADDRESS) returns keccak256("") and
    EXTCODESIZE(ADDRESS) returns 0.
    """
    storage = Storage()

    expected_hash = keccak256(b"")
    expected_size = 0

    checks = Op.SSTORE(
        storage.store_next(expected_hash),
        Op.EXTCODEHASH(Op.ADDRESS),
    ) + Op.SSTORE(
        storage.store_next(expected_size),
        Op.EXTCODESIZE(Op.ADDRESS),
    )
    initcode = checks + Op.RETURN(0, 0)

    if create_opcode is None:
        sender = pre.fund_eoa()
        tx = Transaction(
            sender=sender,
            to=None,
            data=initcode,
            gas_limit=400_000,
        )
        created = compute_create_address(
            address=sender,
            nonce=0,
        )
    else:
        factory_code = (
            Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE)
            + create_opcode(
                value=0,
                offset=0,
                size=Op.CALLDATASIZE,
            )
            + Op.STOP
        )
        factory = pre.deploy_contract(factory_code)
        tx = Transaction(
            sender=pre.fund_eoa(),
            to=factory,
            data=initcode,
            gas_limit=400_000,
        )
        created = compute_create_address(
            address=factory,
            nonce=1,
            salt=0,
            initcode=initcode,
            opcode=create_opcode,
        )

    state_test(
        pre=pre,
        post={created: Account(storage=storage)},
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


@pytest.mark.ported_from(
    [
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stExtCodeHash/callToNonExistentFiller.json",  # noqa: E501
    ],
    pr=["https://github.com/ethereum/execution-specs/pull/2410"],
)
@pytest.mark.with_all_call_opcodes
def test_extcodehash_call_to_nonexistent(
    state_test: StateTestFiller,
    pre: Alloc,
    call_opcode: Opcodes,
) -> None:
    """
    Test EXTCODEHASH after calling a non-existent account.

    Call a non-existent address using each call type, then check
    EXTCODEHASH — it returns 0 because the account does not exist.
    """
    storage = Storage()
    nonexistent = pre.nonexistent_account()

    code = Op.SSTORE(
        storage.store_next(1),
        call_opcode(address=nonexistent, gas=25_000),
    ) + Op.SSTORE(
        storage.store_next(0),
        Op.EXTCODEHASH(nonexistent),
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
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stExtCodeHash/callToSuicideThenExtcodehashFiller.json",  # noqa: E501
    ],
    pr=["https://github.com/ethereum/execution-specs/pull/2412"],
)
@pytest.mark.with_all_call_opcodes
def test_extcodehash_call_to_selfdestruct(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    call_opcode: Opcodes,
) -> None:
    """
    Test EXTCODEHASH after calling a contract that selfdestructs.

    Call a contract containing SELFDESTRUCT using each call type, then
    check EXTCODEHASH. The hash is always returned because the check
    happens within the same transaction. STATICCALL fails because
    SELFDESTRUCT modifies state. Pre-Cancun, CALLCODE/DELEGATECALL
    execute SELFDESTRUCT in the caller's context, destroying the test
    contract at end of transaction.
    """
    storage = Storage()
    beneficiary = pre.nonexistent_account()
    target_code = Op.SELFDESTRUCT(beneficiary)
    target = pre.deploy_contract(target_code, balance=5_555_555_555)

    call_succeeds = call_opcode != Op.STATICCALL

    code = Op.SSTORE(
        storage.store_next(int(call_succeeds)),
        call_opcode(address=target, gas=165_000),
    ) + Op.SSTORE(
        storage.store_next(target_code.keccak256()),
        Op.EXTCODEHASH(target),
    )

    code_address = pre.deploy_contract(code, storage=storage.canary())

    tx = Transaction(
        sender=pre.fund_eoa(),
        to=code_address,
        gas_limit=400_000,
    )

    # Pre-Cancun, CALLCODE/DELEGATECALL execute SELFDESTRUCT in the
    # caller's context, destroying the test contract at end of tx.
    caller_destroyed = fork < Cancun and call_opcode in (
        Op.CALLCODE,
        Op.DELEGATECALL,
    )

    post: dict[Address, Account | None] = {}
    if caller_destroyed:
        post[code_address] = Account.NONEXISTENT
    else:
        post[code_address] = Account(storage=storage)

    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    [
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stExtCodeHash/extCodeHashCreatedAndDeletedAccountFiller.json",  # noqa: E501
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stExtCodeHash/extCodeHashCreatedAndDeletedAccountCallFiller.json",  # noqa: E501
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stExtCodeHash/extCodeHashCreatedAndDeletedAccountStaticCallFiller.json",  # noqa: E501
    ],
    pr=["https://github.com/ethereum/execution-specs/pull/2416"],
)
@pytest.mark.parametrize(
    "trigger",
    [
        pytest.param(Op.CALL, id="call"),
        pytest.param(Op.STATICCALL, id="staticcall"),
    ],
)
def test_extcodehash_created_and_deleted(
    state_test: StateTestFiller,
    pre: Alloc,
    trigger: Opcodes,
) -> None:
    """
    Test EXTCODEHASH of an account created and selfdestructed in same tx.

    CREATE2 a contract with SELFDESTRUCT code, check EXTCODEHASH,
    EXTCODESIZE, and EXTCODECOPY before and after triggering it. Within
    the transaction, the values remain unchanged. With CALL the created
    contract is deleted at end of transaction; with STATICCALL the
    trigger fails and the contract persists.
    """
    storage = Storage()
    runtime = Op.SELFDESTRUCT(0)
    initcode = Initcode(deploy_code=runtime)
    salt = 0x10
    expected_hash = runtime.keccak256()
    expected_size = len(runtime)

    created_slot = storage.store_next(0)
    code = Bytecode()

    # Store initcode in memory and CREATE2
    code += Op.MSTORE(
        0,
        Op.PUSH32(bytes(initcode).ljust(32, b"\0")),
    ) + Op.SSTORE(
        created_slot,
        Op.CREATE2(value=0, offset=0, size=len(initcode), salt=salt),
    )

    target = Op.SLOAD(created_slot)

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
            + Op.EXTCODECOPY(target, 0, 0, 32)
            + Op.SSTORE(
                storage.store_next(bytes(runtime).ljust(32, b"\0")),
                Op.MLOAD(0),
            )
        )

    code += extcode_checks()
    code += trigger(address=target, gas=0x10000) + Op.POP
    code += extcode_checks()

    code_address = pre.deploy_contract(code, storage=storage.canary())

    created = compute_create2_address(
        address=code_address,
        salt=salt,
        initcode=initcode,
    )
    storage[created_slot] = created

    tx = Transaction(
        sender=pre.fund_eoa(),
        to=code_address,
        gas_limit=400_000,
    )

    post: dict[Address, Account | None] = {
        code_address: Account(storage=storage),
    }
    if trigger == Op.CALL:
        post[created] = Account.NONEXISTENT
    else:
        post[created] = Account(code=runtime)

    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    [
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stExtCodeHash/extCodeHashCreatedAndDeletedAccountRecheckInOuterCallFiller.json",  # noqa: E501
    ],
    pr=["https://github.com/ethereum/execution-specs/pull/2428"],
)
def test_extcodehash_created_and_deleted_recheck_outer(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Test EXTCODEHASH of a created-and-selfdestructed account rechecked
    from an outer call frame.

    Outer contract CALLs inner, which CREATE2s a contract with
    SELFDESTRUCT code then triggers it. After inner returns, outer
    re-checks EXTCODEHASH and EXTCODESIZE of the created address.
    Within the transaction all checks return the original code hash
    and size. The created contract is deleted at end of transaction.
    """
    inner_storage = Storage()
    outer_storage = Storage()

    runtime = Op.SELFDESTRUCT(0)
    initcode = Initcode(deploy_code=runtime)
    salt = 0x10
    expected_hash = runtime.keccak256()
    expected_size = len(runtime)

    # Inner contract: CREATE2, check, trigger SELFDESTRUCT, re-check.
    created_slot = inner_storage.store_next(0)
    inner_code = Bytecode()
    inner_code += Om.MSTORE(initcode, 0) + Op.SSTORE(
        created_slot,
        Op.CREATE2(value=0, offset=0, size=len(initcode), salt=salt),
    )

    target = Op.SLOAD(created_slot)
    expected_code = bytes(runtime).ljust(32, b"\0")

    def inner_extcode_checks() -> Bytecode:
        return (
            Op.SSTORE(
                inner_storage.store_next(expected_hash),
                Op.EXTCODEHASH(target),
            )
            + Op.SSTORE(
                inner_storage.store_next(expected_size),
                Op.EXTCODESIZE(target),
            )
            + Op.EXTCODECOPY(target, 0, 0, 32)
            + Op.SSTORE(
                inner_storage.store_next(expected_code),
                Op.MLOAD(0),
            )
        )

    inner_code += inner_extcode_checks()
    inner_code += Op.CALL(address=target, gas=Op.GAS) + Op.POP
    inner_code += inner_extcode_checks()
    inner = pre.deploy_contract(inner_code, storage=inner_storage.canary())

    created = compute_create2_address(
        address=inner,
        salt=salt,
        initcode=initcode,
    )
    inner_storage[created_slot] = created

    # Outer contract: CALL inner, then re-check the created address.
    outer_code = (
        Op.CALL(address=inner, gas=Op.GAS)
        + Op.POP
        + Op.SSTORE(
            outer_storage.store_next(expected_hash),
            Op.EXTCODEHASH(created),
        )
        + Op.SSTORE(
            outer_storage.store_next(expected_size),
            Op.EXTCODESIZE(created),
        )
        + Op.EXTCODECOPY(created, 0, 0, 32)
        + Op.SSTORE(
            outer_storage.store_next(expected_code),
            Op.MLOAD(0),
        )
    )
    outer = pre.deploy_contract(outer_code, storage=outer_storage.canary())

    tx = Transaction(
        sender=pre.fund_eoa(),
        to=outer,
        gas_limit=400_000,
    )

    post: dict[Address, Account | None] = {
        inner: Account(storage=inner_storage),
        outer: Account(storage=outer_storage),
        created: Account.NONEXISTENT,
    }

    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    [
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stExtCodeHash/extCodeHashSubcallSuicideFiller.yml",  # noqa: E501
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stExtCodeHash/extCodeHashSubcallSuicideCancunFiller.yml",  # noqa: E501
    ],
    pr=["https://github.com/ethereum/execution-specs/pull/2418"],
)
@pytest.mark.parametrize(
    "call_opcode",
    [
        pytest.param(Op.CALLCODE, id="callcode"),
        pytest.param(Op.DELEGATECALL, id="delegatecall"),
    ],
)
@pytest.mark.parametrize(
    "dynamic_a",
    [
        pytest.param(False, id="pre_existing"),
        pytest.param(True, id="dynamic"),
    ],
)
def test_extcodehash_subcall_selfdestruct(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    call_opcode: Opcodes,
    dynamic_a: bool,
) -> None:
    """
    Test EXTCODEHASH after subcall with CALLCODE/DELEGATECALL to SELFDESTRUCT.

    B calls A, which uses CALLCODE or DELEGATECALL to invoke a contract C
    containing SELFDESTRUCT, executing it in A's context. B checks
    EXTCODEHASH, EXTCODESIZE, and EXTCODECOPY of A before and after.
    Within the transaction, A's code properties are unchanged. Pre-Cancun,
    A is deleted at end of transaction. In Cancun, A survives only if
    pre-existing; a dynamically created A is still deleted (EIP-6780).
    """
    storage = Storage()
    beneficiary = pre.nonexistent_account()
    selfdestruct_code = Op.SELFDESTRUCT(beneficiary)
    target_c = pre.deploy_contract(selfdestruct_code)

    # A: executes C's code in A's context via CALLCODE/DELEGATECALL
    a_code = call_opcode(
        gas=350_000,
        address=target_c,
        ret_size=32,
    )

    if not dynamic_a:
        a = pre.deploy_contract(a_code, balance=1)

    a_hash = a_code.keccak256()
    a_size = len(a_code)
    a_code_word0 = bytes(a_code)[:32].ljust(32, b"\0")

    def extcode_checks(target: Address | Bytecode) -> Bytecode:
        """Check EXTCODEHASH, EXTCODESIZE, and EXTCODECOPY of A."""
        return (
            Op.SSTORE(storage.store_next(a_hash), Op.EXTCODEHASH(target))
            + Op.SSTORE(storage.store_next(a_size), Op.EXTCODESIZE(target))
            + Op.EXTCODECOPY(target, 0, 0, 32)
            + Op.SSTORE(
                storage.store_next(a_code_word0),
                Op.MLOAD(0),
            )
        )

    code = Bytecode()

    if dynamic_a:
        initcode = Initcode(deploy_code=a_code)
        code += Om.MSTORE(initcode)
        created_slot = storage.store_next(0)
        code += Op.SSTORE(
            created_slot,
            Op.CREATE(value=0, offset=0, size=len(initcode)),
        )
        a_target: Address | Bytecode = Op.SLOAD(created_slot)
    else:
        a_target = a

    code += extcode_checks(a_target)
    code += Op.SSTORE(
        storage.store_next(1),
        Op.CALL(gas=350_000, address=a_target),
    )
    code += extcode_checks(a_target)
    code += Op.SSTORE(
        storage.store_next(1),
        Op.CALL(gas=350_000, address=a_target),
    )

    code_address = pre.deploy_contract(code, storage=storage.canary())

    if dynamic_a:
        a = compute_create_address(address=code_address, nonce=1)
        storage[created_slot] = a

    tx = Transaction(
        sender=pre.fund_eoa(),
        to=code_address,
        gas_limit=500_000,
    )

    # Pre-Cancun, CALLCODE/DELEGATECALL executes SELFDESTRUCT in A's
    # context, deleting A at end of transaction.
    # In Cancun, pre-existing A survives (EIP-6780); dynamic A is deleted.
    post: dict[Address, Account | None] = {
        code_address: Account(storage=storage),
    }
    if fork >= Cancun and not dynamic_a:
        post[a] = Account(code=a_code, balance=0)
    else:
        post[a] = Account.NONEXISTENT

    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    [
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stExtCodeHash/extCodeHashSubcallOOGFiller.yml",  # noqa: E501
    ],
    pr=[
        "https://github.com/ethereum/execution-specs/pull/2458",
    ],
)
@pytest.mark.parametrize(
    "call_opcode",
    [
        pytest.param(Op.CALL, id="call"),
        pytest.param(Op.CALLCODE, id="callcode"),
        pytest.param(Op.DELEGATECALL, id="delegatecall"),
    ],
)
@pytest.mark.parametrize("oog", [False, True], ids=["success", "oog"])
def test_extcodehash_subcall_create2_oog(
    state_test: StateTestFiller,
    pre: Alloc,
    call_opcode: Opcodes,
    oog: bool,
) -> None:
    """
    Test EXTCODEHASH after CREATE2 in a subcall that goes out of gas.

    A factory contract creates a contract via CREATE2, then either
    returns normally or consumes all remaining gas. When the subcall
    OOGs, the entire frame reverts — including the CREATE2 — so the
    created contract should not exist. The caller checks
    EXTCODEHASH/EXTCODESIZE/EXTCODECOPY of the expected CREATE2 address.
    """
    storage = Storage()
    deploy_code = Op.SSTORE(0x20, 0x20)
    deploy_code_bytes = bytes(deploy_code)
    initcode = Initcode(deploy_code=deploy_code)

    # Factory: CREATE2, optionally consume all gas to trigger OOG.
    factory_code = Om.MSTORE(initcode, 0) + Op.MSTORE(
        0, Op.CREATE2(value=0, offset=0, size=len(initcode), salt=0)
    )
    if oog:
        factory_code += Om.OOG
    factory_code += Op.RETURN(0, 32)

    factory = pre.deploy_contract(factory_code)

    # Pass the pre-computed CREATE2 address as calldata so the test
    # does not depend on return data from a potentially OOG'd subcall.
    hash_slot = storage.store_next(0, "extcodehash")
    size_slot = storage.store_next(0, "extcodesize")
    code_slot = storage.store_next(0, "extcodecopy")
    code = (
        Op.SSTORE(
            storage.store_next(int(not oog), "call_result"),
            call_opcode(
                address=factory,
                gas=200_000,
                ret_offset=0,
                ret_size=32,
            ),
        )
        + Op.SSTORE(hash_slot, Op.EXTCODEHASH(Op.CALLDATALOAD(0)))
        + Op.SSTORE(size_slot, Op.EXTCODESIZE(Op.CALLDATALOAD(0)))
        + Op.EXTCODECOPY(Op.CALLDATALOAD(0), 0, 0, 32)
        + Op.SSTORE(code_slot, Op.MLOAD(0))
    )

    code_address = pre.deploy_contract(code, storage=storage.canary())

    # Compute the CREATE2 address to verify existence in post-state.
    if call_opcode == Op.CALL:
        deployer = factory
    else:
        # CALLCODE/DELEGATECALL: factory code runs in caller's context.
        deployer = code_address
    created = compute_create2_address(
        address=deployer, salt=0, initcode=initcode
    )

    if not oog:
        storage[hash_slot] = keccak256(deploy_code_bytes)
        storage[size_slot] = len(deploy_code)
        storage[code_slot] = deploy_code_bytes.ljust(32, b"\0")

    post: dict[Address, Account | None] = {
        code_address: Account(storage=storage),
    }
    if oog:
        post[created] = Account.NONEXISTENT
    else:
        post[created] = Account(nonce=1, code=deploy_code)

    tx = Transaction(
        sender=pre.fund_eoa(),
        to=code_address,
        gas_limit=500_000,
        data=created.rjust(32, b"\0"),
    )

    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    [
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stExtCodeHash/codeCopyZero_ParisFiller.yml",  # noqa: E501
    ],
)
@pytest.mark.parametrize(
    "target_type",
    [
        "nonexistent",
        "existing",
    ],
)
def test_extcodecopy_zero_code(
    state_test: StateTestFiller,
    pre: Alloc,
    target_type: str,
) -> None:
    """
    Test EXTCODECOPY/EXTCODESIZE/EXTCODEHASH of accounts with no code.

    Two account types: nonexistent (no state at all) and existing
    (EOA with balance, no code). EXTCODECOPY writes nothing to memory
    (stays zero). EXTCODEHASH is zero for nonexistent, keccak256("")
    for existing accounts.

    TODO: The original test also intended to cover empty accounts
    (zero nonce, zero balance, no code), but such accounts cannot
    exist in post-Paris forks due to EIP-161 cleanup.
    """
    storage = Storage()

    if target_type == "nonexistent":
        target = pre.nonexistent_account()
        expected_hash: int | bytes = 0
    else:  # existing
        target = pre.fund_eoa(amount=1)
        expected_hash = keccak256(b"")

    code = (
        Op.EXTCODECOPY(target, 0, 0, 32)
        + Op.SSTORE(storage.store_next(0, "extcodecopy"), Op.MLOAD(0))
        + Op.SSTORE(
            storage.store_next(0, "extcodesize"),
            Op.EXTCODESIZE(target),
        )
        + Op.SSTORE(
            storage.store_next(expected_hash, "extcodehash"),
            Op.EXTCODEHASH(target),
        )
        + Op.SSTORE(
            storage.store_next(1, "callcode_result"),
            Op.CALLCODE(50_000, target, 0, 0, 0, 0, 0),
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
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stExtCodeHash/codeCopyZero_ParisFiller.yml",  # noqa: E501
    ],
)
def test_codecopy_zero_in_create2(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Test CODECOPY inside CREATE2 initcode that deploys empty code.

    The initcode does CODECOPY(0,0,32) which copies the first 32 bytes
    of the initcode itself (not the deployed code). It then checks
    EXTCODESIZE(ADDRESS) and EXTCODEHASH(ADDRESS) of self during init,
    which see the account as having empty code. The deployed contract
    retains the storage set during init.
    """
    storage = Storage()

    # Build the initcode that queries itself and deploys empty code.
    # During init: CODECOPY copies the initcode, EXTCODESIZE(self)=0,
    # EXTCODEHASH(self)=keccak256("").
    initcode = (
        Op.CODECOPY(0, 0, 32)
        + Op.SSTORE(0x50, Op.MLOAD(0))
        + Op.SSTORE(0x51, Op.EXTCODESIZE(Op.ADDRESS))
        + Op.SSTORE(0x52, Op.EXTCODEHASH(Op.ADDRESS))
        + Op.SSTORE(
            0x53,
            Op.EXTCODESIZE(Op.CALLCODE(50_000, Op.ADDRESS, 0, 0, 0, 0, 0)),
        )
        + Op.EXTCODECOPY(Op.ADDRESS, 0, 0, 32)
        + Op.SSTORE(0x54, Op.MLOAD(0))
        # Return empty code (size 0).
        + Op.RETURN(0, 0)
    )

    # Factory: CREATE2 and return the created address.
    factory_code = (
        Om.MSTORE(initcode, 0)
        + Op.MSTORE(
            0,
            Op.CREATE2(value=0, offset=0, size=len(initcode), salt=0),
        )
        + Op.RETURN(0, 32)
    )

    factory = pre.deploy_contract(factory_code, balance=10**18)

    # Caller: invoke factory and store created address.
    caller_code = Op.CALL(550_000, factory, 0, 0, 0, 0, 32) + Op.SSTORE(
        storage.store_next(0, "created_address"), Op.MLOAD(0)
    )

    caller = pre.deploy_contract(caller_code, storage=storage.canary())

    created = compute_create2_address(
        address=factory, salt=0, initcode=initcode
    )
    storage[0] = created

    # First 32 bytes of initcode — what CODECOPY(0,0,32) returns.
    initcode_word0 = bytes(initcode)[:32]

    tx = Transaction(
        sender=pre.fund_eoa(),
        to=caller,
        gas_limit=1_400_000,
    )

    state_test(
        pre=pre,
        post={
            caller: Account(storage=storage),
            created: Account(
                nonce=1,
                code=b"",
                storage={
                    0x50: initcode_word0,
                    0x51: 0,
                    0x52: keccak256(b""),
                    0x53: 0,
                    0x54: 0,
                },
            ),
        },
        tx=tx,
    )
