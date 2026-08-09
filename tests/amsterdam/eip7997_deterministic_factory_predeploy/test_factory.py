"""
Tests for [EIP-7997: Deterministic Factory Predeploy](https://eips.ethereum.org/EIPS/eip-7997).

The factory (the Arachnid deterministic deployment proxy) interprets
calldata as `salt (32) || initcode` and invokes `CREATE2` with the call
value forwarded. It returns the created address (20 bytes) on success
and reverts on `CREATE2` failure. With calldata shorter than 32 bytes,
the factory's `CALLDATASIZE - 32` underflow triggers a copy of nearly
2^256 bytes and reverts via OOG.
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
    BlockAccessListExpectation,
    Bytes,
    Fork,
    Hash,
    Initcode,
    Op,
    StateTestFiller,
    Storage,
    Transaction,
    compute_create2_address,
    keccak256,
)

from ...prague.eip7702_set_code_tx.spec import Spec as Spec7702
from .spec import Spec, ref_spec_7997

REFERENCE_SPEC_GIT_PATH = ref_spec_7997.git_path
REFERENCE_SPEC_VERSION = ref_spec_7997.version

pytestmark = pytest.mark.valid_from("EIP7997")

FACTORY = Spec.FACTORY_ADDRESS


def test_factory_predeploy_account(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    The factory bytecode is present at the canonical Arachnid factory
    address with nonce 1 and balance 0. Verifies EVM-observable views of
    the predeploy via `EXTCODESIZE`, `EXTCODEHASH`, `EXTCODECOPY` +
    `SHA3`, and `BALANCE`.
    """
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
        pytest.param(1, id="with_value"),
    ],
)
def test_factory_deploys_contract(
    state_test: StateTestFiller,
    pre: Alloc,
    forwarded_value: int,
) -> None:
    """
    Calling the factory with `salt || initcode` deploys a contract at the
    expected `CREATE2` address and returns that address. When the call
    forwards a non-zero value, the deployed contract receives that
    balance.
    """
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
                ret_size=20,
            ),
        )
        + Op.SSTORE(
            storage.store_next(expected_address, "returned_address"),
            Op.MLOAD(0),
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


def test_factory_address_collision_reverts(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    A second deployment to the same `CREATE2` target reverts. `CREATE2`
    fails when the destination already has code, returns 0, and the factory
    reverts with the (empty) creation-frame return data.
    """
    salt = 0x77
    runtime_code = Op.STOP
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
        + Op.STOP,
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
            target: Account(nonce=1, code=bytes(runtime_code)),
        },
    )


def test_factory_different_salts_produce_different_addresses(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Two calls to the factory with the same initcode but different salts
    must deploy at distinct, salt-derived addresses, proving the salt is
    actually plumbed through to `CREATE2`.
    """
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


def test_factory_direct_eoa_call(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    A transaction sent directly to the factory address (no relay contract)
    deploys at the expected `CREATE2` address.
    """
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


def test_factory_staticcall_reverts(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Calling the factory via `STATICCALL` fails because `CREATE2` requires a
    writable context. No contract is deployed.
    """
    salt = 0x33
    runtime_code = Op.STOP
    initcode = Initcode(deploy_code=runtime_code)
    expected_address = compute_create2_address(FACTORY, salt, initcode)

    storage = Storage()
    caller = pre.deploy_contract(
        Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE)
        + Op.SSTORE(
            storage.store_next(0, "staticcall_failed"),
            Op.STATICCALL(
                gas=Op.GAS,
                address=FACTORY,
                args_offset=0,
                args_size=Op.CALLDATASIZE,
                ret_offset=0x100,
                ret_size=32,
            ),
        )
        + Op.STOP,
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


@pytest.mark.parametrize("call_opcode", [Op.DELEGATECALL, Op.CALLCODE])
def test_factory_in_caller_context(
    state_test: StateTestFiller,
    pre: Alloc,
    call_opcode: Op,
) -> None:
    """
    Under `DELEGATECALL` or `CALLCODE`, the factory's bytecode runs in the
    caller's context, so `CREATE2`'s deployer is the caller — not the
    factory. The contract is deployed at the address derived from the
    caller, and the factory-derived address is empty.
    """
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


def test_factory_deploys_to_pre_funded_address(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    `CREATE2` to an address that has only a balance (no code, no storage,
    nonce 0) succeeds and preserves the existing balance.
    """
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
    `SELFDESTRUCT` to the factory transfers the originator's balance to
    the factory address. The factory's other state is untouched: same
    nonce, same code. Calling the factory after the transfer still works.

    Tests that the factory address has no special handling under
    `SELFDESTRUCT` — it behaves like any other contract beneficiary.
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


def test_factory_via_eip7702_delegation(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    An EOA delegates its code to the factory via an EIP-7702
    authorization. When the EOA is then called with `salt || initcode`,
    the factory bytecode runs in the EOA's context, so `CREATE2` treats
    the EOA as the deployer. The deterministic address therefore
    derives from the EOA, not from the factory.
    """
    auth_signer = pre.fund_eoa()
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
                value=0,
                args_offset=0,
                args_size=Op.CALLDATASIZE,
                ret_offset=0x100,
                ret_size=20,
            ),
        )
        + Op.STOP,
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
                code=Spec7702.delegation_designation(Address(FACTORY)),
            ),
            expected_address: Account(nonce=1, code=bytes(runtime_code)),
            FACTORY: Account(
                nonce=1,
                balance=0,
                code=Spec.FACTORY_BYTECODE,
            ),
        },
    )


def test_factory_rejects_ef_prefix_deployment(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    EIP-3541: deploying code that begins with `0xEF` is rejected. The
    factory's `CREATE2` fails when the initcode would return such code;
    the factory reverts and no contract is deployed.
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


def test_factory_rejects_oversized_initcode(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    EIP-3860: initcode larger than the fork's max initcode size is
    rejected. The factory's `CREATE2` fails for oversized initcode and
    the factory reverts.
    """
    salt = 0x55
    initcode = Initcode(
        deploy_code=Op.STOP,
        initcode_length=fork.max_initcode_size() + 1,
    )
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


def test_factory_block_access_list(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    EIP-7928: a factory deployment is captured in the block-level
    access list. The factory's nonce bump from `CREATE2` and the
    deployed contract's `nonce`/`code` initialization both appear
    under their respective accounts.
    """
    salt = 0x42
    runtime_code = Op.PUSH1(0x01) + Op.PUSH1(0x00) + Op.RETURN
    initcode = Initcode(deploy_code=runtime_code)
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
                nonce=2,
                balance=0,
                code=Spec.FACTORY_BYTECODE,
            ),
            expected_address: Account(nonce=1, code=bytes(runtime_code)),
        },
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                sender: BalAccountExpectation(
                    nonce_changes=[
                        BalNonceChange(block_access_index=1, post_nonce=1),
                    ],
                ),
                Address(FACTORY): BalAccountExpectation(
                    nonce_changes=[
                        BalNonceChange(block_access_index=1, post_nonce=2),
                    ],
                ),
                expected_address: BalAccountExpectation(
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
