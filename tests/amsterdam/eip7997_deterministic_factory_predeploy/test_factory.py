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
    AccessList,
    Account,
    Alloc,
    Hash,
    Initcode,
    Op,
    StateTestFiller,
    Storage,
    Transaction,
    compute_create2_address,
    keccak256,
)

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
    caller = pre.deploy_contract(
        Op.SSTORE(0, Op.EXTCODESIZE(FACTORY))
        + Op.SSTORE(1, Op.EXTCODEHASH(FACTORY))
        + Op.EXTCODECOPY(FACTORY, 0, 0, Op.EXTCODESIZE(FACTORY))
        + Op.SSTORE(2, Op.SHA3(0, Op.EXTCODESIZE(FACTORY)))
        + Op.SSTORE(3, Op.BALANCE(FACTORY))
        + Op.STOP,
    )
    state_test(
        pre=pre,
        tx=Transaction(
            sender=pre.fund_eoa(),
            to=caller,
            gas_limit=200_000,
        ),
        post={
            FACTORY: Account(
                nonce=1,
                balance=0,
                code=Spec.FACTORY_BYTECODE,
            ),
            caller: Account(
                storage={
                    0: len(Spec.FACTORY_BYTECODE),
                    1: keccak256(Spec.FACTORY_BYTECODE),
                    2: keccak256(Spec.FACTORY_BYTECODE),
                    3: 0,
                },
            ),
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
            gas_limit=500_000,
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
            gas_limit=1_000_000,
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

    caller = pre.deploy_contract(
        Op.CALLDATACOPY(initcode_offset, 0, Op.CALLDATASIZE)
        + Op.MSTORE(0, salt_a)
        + Op.SSTORE(
            0,
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
        + Op.SSTORE(1, Op.MLOAD(0x200))
        + Op.MSTORE(0, salt_b)
        + Op.SSTORE(
            2,
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
        + Op.SSTORE(3, Op.MLOAD(0x200))
        + Op.STOP,
    )

    state_test(
        pre=pre,
        tx=Transaction(
            sender=pre.fund_eoa(),
            to=caller,
            data=bytes(initcode),
            gas_limit=1_000_000,
        ),
        post={
            caller: Account(
                storage={0: 1, 1: addr_a, 2: 1, 3: addr_b},
            ),
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
            gas_limit=200_000,
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
            gas_limit=500_000,
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

    call_op = Op.DELEGATECALL(
        gas=Op.GAS,
        address=FACTORY,
        args_offset=0,
        args_size=Op.CALLDATASIZE,
        ret_offset=0x10C,
        ret_size=20,
    )

    caller = pre.deploy_contract(
        Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE)
        + Op.SSTORE(0, call_op)
        + Op.SSTORE(1, Op.MLOAD(0x100))
        + Op.STOP,
    )
    caller_derived = compute_create2_address(caller, salt, initcode)

    state_test(
        pre=pre,
        tx=Transaction(
            sender=pre.fund_eoa(),
            to=caller,
            data=Hash(salt) + bytes(initcode),
            gas_limit=500_000,
        ),
        post={
            caller: Account(storage={0: 1, 1: caller_derived}),
            caller_derived: Account(nonce=1, code=bytes(runtime_code)),
            factory_derived: Account.NONEXISTENT,
        },
    )


@pytest.mark.pre_alloc_mutable
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

    pre[expected_address] = Account(balance=pre_balance)

    storage = Storage()
    caller = pre.deploy_contract(
        Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE)
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
            gas_limit=500_000,
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


@pytest.mark.parametrize(
    "use_access_list,expected_delta",
    [
        pytest.param(False, 2500, id="without_access_list"),
        pytest.param(True, 0, id="with_access_list"),
    ],
)
def test_factory_access_list_prewarming(
    state_test: StateTestFiller,
    pre: Alloc,
    use_access_list: bool,
    expected_delta: int,
) -> None:
    """
    Measure the gas-cost difference between a first and second
    `EXTCODESIZE` of the factory in the same transaction. The opcode has
    deterministic gas cost (no inner frame), so the difference isolates
    the cold-vs-warm address access cost.

    - Without access list: difference is 2,500.
    - With access list including the factory: difference is 0.
    """
    # Identical measurement block around each EXTCODESIZE: GAS, op, POP,
    # GAS, SWAP1, SUB. Same operations on both sides cancels overhead.
    measure = (
        Op.GAS + Op.POP(Op.EXTCODESIZE(FACTORY)) + Op.GAS + Op.SWAP1 + Op.SUB
    )

    storage = Storage()
    caller = pre.deploy_contract(
        # First measurement: stack ends as [cost1].
        measure
        # Second measurement: stack ends as [cost2, cost1].
        + measure
        # delta = cost1 - cost2.
        + Op.SWAP1
        + Op.SUB
        # Stack: [delta]. SSTORE pops [key, value], so push the key.
        + Op.PUSH1(storage.store_next(expected_delta, "first_minus_second"))
        + Op.SSTORE
        + Op.STOP,
    )

    access_list = (
        [AccessList(address=FACTORY, storage_keys=[])]
        if use_access_list
        else None
    )

    state_test(
        pre=pre,
        tx=Transaction(
            sender=pre.fund_eoa(),
            to=caller,
            gas_limit=500_000,
            access_list=access_list,
        ),
        post={caller: Account(storage=storage)},
    )


@pytest.mark.pre_alloc_mutable
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
            gas_limit=1_000_000,
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
