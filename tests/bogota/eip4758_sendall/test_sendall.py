"""
Tests for [EIP-4758: Deactivate SELFDESTRUCT](https://eips.ethereum.org/EIPS/eip-4758).

SENDALL sweeps the account's entire balance to the beneficiary and halts;
it no longer deletes accounts created in the same transaction. Deletion-era
coverage is parked before this EIP in the EIP-6780 and EIP-8246 suites.
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Block,
    BlockchainTestFiller,
    Bytecode,
    Fork,
    Hash,
    Initcode,
    Op,
    StateTestFiller,
    Storage,
    Transaction,
    compute_create_address,
)
from execution_testing import (
    Macros as Om,
)

from .spec import ref_spec_4758

REFERENCE_SPEC_GIT_PATH = ref_spec_4758.git_path
REFERENCE_SPEC_VERSION = ref_spec_4758.version

pytestmark = pytest.mark.valid_from("EIP4758")

VICTIM_BALANCE = 0x1234
CANARY = 0xC0DE
SALT = 0


def deploy_victim_factory(
    pre: Alloc,
    victim_code: Bytecode,
    create_opcode: Op = Op.CREATE,
    value: int = VICTIM_BALANCE,
    balance: int | None = None,
) -> tuple[Address, Address]:
    """
    Deploy a factory whose call creates the victim contract.

    The factory stores the created address in slot 0 and funds the victim
    with `value` from its own balance. Return the factory and the (future)
    victim address.
    """
    initcode = Initcode(deploy_code=victim_code)
    if create_opcode == Op.CREATE2:
        create_call = Op.CREATE2(value=value, size=len(initcode), salt=SALT)
    else:
        create_call = Op.CREATE(value=value, size=len(initcode))
    factory = pre.deploy_contract(
        code=Om.MSTORE(initcode, 0) + Op.SSTORE(0, create_call),
        balance=value if balance is None else balance,
    )
    victim = compute_create_address(
        address=factory,
        opcode=create_opcode,
        nonce=1,
        salt=SALT,
        initcode=initcode,
    )
    return factory, victim


@pytest.mark.parametrize("create_opcode", [Op.CREATE, Op.CREATE2])
@pytest.mark.parametrize("beneficiary_kind", ["fresh", "existing", "self"])
def test_created_account_persists(
    state_test: StateTestFiller,
    pre: Alloc,
    create_opcode: Op,
    beneficiary_kind: str,
) -> None:
    """
    A contract created and swept in the same transaction persists.

    The victim keeps its code, nonce, and storage; only the balance moves
    to the beneficiary, and a self-sweep leaves it in place.
    """
    beneficiary: Address | None = None
    sendall_target: Address | Op
    if beneficiary_kind == "fresh":
        beneficiary = pre.nonexistent_account()
        sendall_target = beneficiary
    elif beneficiary_kind == "existing":
        beneficiary = pre.fund_eoa(amount=1)
        sendall_target = beneficiary
    else:
        sendall_target = Op.ADDRESS

    victim_code = Op.SSTORE(0, CANARY) + Op.SELFDESTRUCT(sendall_target)
    factory, victim = deploy_victim_factory(pre, victim_code, create_opcode)

    entry_storage = Storage()
    entry = pre.deploy_contract(
        code=Op.SSTORE(entry_storage.store_next(1), Op.CALL(address=factory))
        + Op.SSTORE(entry_storage.store_next(1), Op.CALL(address=victim)),
        storage=entry_storage.canary(),
    )

    swept = beneficiary_kind != "self"
    post = {
        entry: Account(storage=entry_storage),
        factory: Account(storage={0: victim}),
        victim: Account(
            nonce=1,
            code=victim_code,
            balance=0 if swept else VICTIM_BALANCE,
            storage={0: CANARY},
        ),
    }
    if beneficiary is not None:
        held = 0 if beneficiary_kind == "fresh" else 1
        post[beneficiary] = Account(balance=held + VICTIM_BALANCE)

    state_test(
        pre=pre,
        post=post,
        tx=Transaction(sender=pre.fund_eoa(), to=entry),
    )


@pytest.mark.parametrize("create_opcode", [Op.CREATE, Op.CREATE2])
def test_sendall_in_initcode(
    state_test: StateTestFiller,
    pre: Alloc,
    create_opcode: Op,
) -> None:
    """
    SENDALL inside initcode completes the deployment.

    The frame halts with empty output, so the created account persists
    with empty code, its initcode storage writes, and nonce 1; its balance
    is swept to the beneficiary.
    """
    beneficiary = pre.fund_eoa(amount=1)
    initcode = Op.SSTORE(0, CANARY) + Op.SELFDESTRUCT(beneficiary)

    if create_opcode == Op.CREATE2:
        create_call = Op.CREATE2(
            value=VICTIM_BALANCE, size=len(initcode), salt=SALT
        )
    else:
        create_call = Op.CREATE(value=VICTIM_BALANCE, size=len(initcode))
    factory = pre.deploy_contract(
        code=Om.MSTORE(initcode, 0) + Op.SSTORE(0, create_call),
        balance=VICTIM_BALANCE,
    )
    victim = compute_create_address(
        address=factory,
        opcode=create_opcode,
        nonce=1,
        salt=SALT,
        initcode=initcode,
    )

    post = {
        factory: Account(storage={0: victim}),
        victim: Account(nonce=1, code=b"", balance=0, storage={0: CANARY}),
        beneficiary: Account(balance=1 + VICTIM_BALANCE),
    }

    state_test(
        pre=pre,
        post=post,
        tx=Transaction(sender=pre.fund_eoa(), to=factory),
    )


def test_create2_redeploy_collision(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    CREATE2 onto a swept account collides.

    The entry contract invokes the factory twice per transaction: the
    second attempt of the first transaction collides with the account
    created moments earlier, and both attempts of a later transaction
    collide even after the victim's balance has been swept away.

    Each attempt runs in its own factory frame so that a collision's
    EIP-684 gas burn is contained in that frame and cannot starve the
    following attempt.
    """
    beneficiary = pre.fund_eoa(amount=1)
    victim_code = Op.SELFDESTRUCT(beneficiary)
    initcode = Initcode(deploy_code=victim_code)

    canary = 0xDEAD
    factory = pre.deploy_contract(
        code=Om.MSTORE(initcode, 0)
        + Op.SSTORE(
            Op.CALLDATALOAD(0),
            Op.CREATE2(value=VICTIM_BALANCE, size=len(initcode), salt=SALT),
        ),
        balance=2 * VICTIM_BALANCE,
        storage=dict.fromkeys(range(4), canary),
    )
    victim = compute_create_address(
        address=factory,
        opcode=Op.CREATE2,
        salt=SALT,
        initcode=initcode,
    )

    # A collision burns all but 1/64 of the factory frame's gas
    # (EIP-684), so cap each attempt's frame to a budget whose retained
    # 1/64 still funds the cold store of the attempt's result.
    collision_store = Op.SSTORE.with_metadata(
        key_warm=False,
        original_value=canary,
        current_value=canary,
        new_value=0,
    )
    factory_gas = 64 * 2 * collision_store.gas_cost(fork)

    entry = pre.deploy_contract(
        code=Op.MSTORE(0, Op.CALLDATALOAD(0))
        + Op.POP(Op.CALL(gas=factory_gas, address=factory, args_size=32))
        + Op.MSTORE(0, Op.CALLDATALOAD(32))
        + Op.POP(Op.CALL(gas=factory_gas, address=factory, args_size=32)),
    )

    # First tx: creation succeeds, then the same-tx retry collides.
    # Second tx (after the sweep): both attempts still collide.
    factory_storage = {0: victim, 1: 0, 2: 0, 3: 0}

    sender = pre.fund_eoa()
    blocks = [
        Block(
            txs=[
                Transaction(sender=sender, to=entry, data=Hash(0) + Hash(1)),
                Transaction(sender=sender, to=victim),
                Transaction(sender=sender, to=entry, data=Hash(2) + Hash(3)),
            ]
        )
    ]

    post = {
        factory: Account(storage=factory_storage),
        victim: Account(nonce=1, code=victim_code, balance=0),
        beneficiary: Account(balance=1 + VICTIM_BALANCE),
    }

    blockchain_test(pre=pre, post=post, blocks=blocks)


def test_sendall_static_context(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    SENDALL still fails in a static context.

    The STATICCALL into the freshly created victim fails, nothing is
    swept, and the victim persists with its balance.
    """
    beneficiary = pre.nonexistent_account()
    victim_code = Op.SELFDESTRUCT(beneficiary)
    factory, victim = deploy_victim_factory(pre, victim_code)

    entry_storage = Storage()
    entry = pre.deploy_contract(
        code=Op.SSTORE(entry_storage.store_next(1), Op.CALL(address=factory))
        + Op.SSTORE(
            entry_storage.store_next(1),
            Op.ADD(1, Op.STATICCALL(address=victim)),
        ),
        storage=entry_storage.canary(),
    )

    post = {
        entry: Account(storage=entry_storage),
        factory: Account(storage={0: victim}),
        victim: Account(nonce=1, code=victim_code, balance=VICTIM_BALANCE),
        beneficiary: Account.NONEXISTENT,
    }

    state_test(
        pre=pre,
        post=post,
        tx=Transaction(sender=pre.fund_eoa(), to=entry),
    )


def test_repeated_sendall(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Sweep the same account twice in one transaction.

    Both calls succeed: the first moves the balance, the second sweeps
    nothing, and the victim persists throughout.
    """
    beneficiary = pre.fund_eoa(amount=1)
    victim_code = Op.SELFDESTRUCT(beneficiary)
    factory, victim = deploy_victim_factory(pre, victim_code)

    entry_storage = Storage()
    entry = pre.deploy_contract(
        code=Op.SSTORE(entry_storage.store_next(1), Op.CALL(address=factory))
        + Op.SSTORE(entry_storage.store_next(1), Op.CALL(address=victim))
        + Op.SSTORE(entry_storage.store_next(1), Op.CALL(address=victim)),
        storage=entry_storage.canary(),
    )

    post = {
        entry: Account(storage=entry_storage),
        factory: Account(storage={0: victim}),
        victim: Account(nonce=1, code=victim_code, balance=0),
        beneficiary: Account(balance=1 + VICTIM_BALANCE),
    }

    state_test(
        pre=pre,
        post=post,
        tx=Transaction(sender=pre.fund_eoa(), to=entry),
    )


def test_zero_balance_sendall_fresh_beneficiary(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    A zero-balance sweep to a nonexistent beneficiary creates no account.
    """
    beneficiary = pre.nonexistent_account()
    victim_code = Op.SELFDESTRUCT(beneficiary)
    factory, victim = deploy_victim_factory(pre, victim_code, value=0)

    entry_storage = Storage()
    entry = pre.deploy_contract(
        code=Op.SSTORE(entry_storage.store_next(1), Op.CALL(address=factory))
        + Op.SSTORE(entry_storage.store_next(1), Op.CALL(address=victim)),
        storage=entry_storage.canary(),
    )

    post = {
        entry: Account(storage=entry_storage),
        factory: Account(storage={0: victim}),
        victim: Account(nonce=1, code=victim_code, balance=0),
        beneficiary: Account.NONEXISTENT,
    }

    state_test(
        pre=pre,
        post=post,
        tx=Transaction(sender=pre.fund_eoa(), to=entry),
    )
