"""
Tests for [EIP-8360: TCREATE Opcode](https://eips.ethereum.org/EIPS/eip-8360).

Implements the rules from ethereum/EIPs#12370: ``0xfe`` address prefix,
no deployer nonce bump, end-of-tx code/nonce discard, ``SLOAD``/``SSTORE``
and ``CREATE2`` halt in a TCREATE account context.
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Bytecode,
    Initcode,
    Op,
    StateTestFiller,
    Storage,
    Transaction,
    compute_create2_address,
    compute_create_address,
    compute_tcreate_address,
)
from execution_testing import Macros as Om

from .spec import ref_spec_8360

REFERENCE_SPEC_GIT_PATH = ref_spec_8360.git_path
REFERENCE_SPEC_VERSION = ref_spec_8360.version

pytestmark = pytest.mark.valid_from("EIP8360")

SALT = 0x8360


def _factory_tcreate(initcode: Bytecode, value: int = 0) -> Bytecode:
    """Factory code: TCREATE then store the returned address in slot 0."""
    return Om.MSTORE(initcode, 0) + Op.SSTORE(
        0,
        Op.TCREATE(value=value, offset=0, size=len(initcode), salt=SALT),
    )


@pytest.mark.parametrize("endowment", [0, 3])
def test_tcreate_end_of_tx_clears_code_keeps_balance(
    state_test: StateTestFiller,
    pre: Alloc,
    endowment: int,
) -> None:
    """
    After TCREATE, the account has no code or nonce in the post-state;
    a non-zero endowment remains as balance.
    """
    runtime = Op.STOP
    initcode = Initcode(deploy_code=runtime)
    factory = pre.deploy_contract(
        code=_factory_tcreate(initcode, value=endowment),
        balance=endowment + 1,
    )
    tcreated = compute_tcreate_address(factory, SALT, initcode)

    storage = Storage()
    entry = pre.deploy_contract(
        code=Op.SSTORE(storage.store_next(1), Op.CALL(address=factory)),
        storage=storage.canary(),
    )
    sender = pre.fund_eoa()

    post: dict[Address, Account] = {
        entry: Account(storage=storage),
        factory: Account(
            storage={0: tcreated},
            balance=1,
            nonce=1,
        ),
    }
    if endowment:
        post[tcreated] = Account(balance=endowment, nonce=0, code=b"")
    else:
        # Empty after finalization: removed per EIP-161.
        post[tcreated] = Account.NONEXISTENT

    state_test(
        pre=pre,
        tx=Transaction(sender=sender, to=entry, gas_limit=1_000_000),
        post=post,
    )


def test_tcreate_address_differs_from_create2(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """``0xfe`` prefix separates TCREATE addresses from CREATE2."""
    initcode = Initcode(deploy_code=Op.STOP)
    factory = pre.deploy_contract(
        code=_factory_tcreate(initcode),
        balance=1,
    )
    tcreate_addr = compute_tcreate_address(factory, SALT, initcode)
    create2_addr = compute_create2_address(factory, SALT, initcode)
    assert tcreate_addr != create2_addr

    storage = Storage()
    entry = pre.deploy_contract(
        code=Op.SSTORE(storage.store_next(1), Op.CALL(address=factory)),
        storage=storage.canary(),
    )
    sender = pre.fund_eoa()

    state_test(
        pre=pre,
        tx=Transaction(sender=sender, to=entry, gas_limit=1_000_000),
        post={
            entry: Account(storage=storage),
            factory: Account(storage={0: tcreate_addr}, nonce=1),
            tcreate_addr: Account.NONEXISTENT,
            create2_addr: Account.NONEXISTENT,
        },
    )


def test_tcreate_does_not_increment_deployer_nonce(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """TCREATE leaves the executing account's nonce unchanged."""
    initcode = Initcode(deploy_code=Op.STOP)
    # nonce starts at 1 after deploy_contract
    factory = pre.deploy_contract(
        code=_factory_tcreate(initcode),
        balance=1,
    )
    tcreated = compute_tcreate_address(factory, SALT, initcode)

    storage = Storage()
    entry = pre.deploy_contract(
        code=Op.SSTORE(storage.store_next(1), Op.CALL(address=factory)),
        storage=storage.canary(),
    )
    sender = pre.fund_eoa()

    state_test(
        pre=pre,
        tx=Transaction(sender=sender, to=entry, gas_limit=1_000_000),
        post={
            entry: Account(storage=storage),
            factory: Account(storage={0: tcreated}, nonce=1),
            tcreated: Account.NONEXISTENT,
        },
    )


def test_sstore_halts_in_tcreate_context(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """SSTORE in a TCREATE account exceptional-halts the create frame."""
    # Initcode that tries to SSTORE then returns STOP runtime.
    initcode = Initcode(deploy_code=Op.STOP, initcode_prefix=Op.SSTORE(0, 1))
    factory = pre.deploy_contract(
        code=_factory_tcreate(initcode),
        balance=1,
    )
    tcreated = compute_tcreate_address(factory, SALT, initcode)
    sender = pre.fund_eoa()

    # Create fails: factory stores 0, no leftover TCREATE account.
    # Send the tx to the factory directly so a gas-consuming exceptional
    # halt in the create frame cannot OOG an outer CALL wrapper.
    state_test(
        pre=pre,
        tx=Transaction(sender=sender, to=factory, gas_limit=3_000_000),
        post={
            factory: Account(storage={0: 0}, nonce=1),
            tcreated: Account.NONEXISTENT,
        },
    )


def test_create2_halts_in_tcreate_context(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """CREATE2 in a TCREATE account exceptional-halts."""
    inner_init = Initcode(deploy_code=Op.STOP)
    runtime = (
        Om.MSTORE(inner_init, 0)
        + Op.CREATE2(value=0, offset=0, size=len(inner_init), salt=1)
        + Op.STOP
    )
    initcode = Initcode(deploy_code=runtime)

    factory_code = (
        Om.MSTORE(initcode, 0)
        + Op.SSTORE(
            0, Op.TCREATE(value=0, offset=0, size=len(initcode), salt=SALT)
        )
        + Op.SSTORE(1, Op.CALL(address=Op.SLOAD(0), gas=500_000))
    )
    factory = pre.deploy_contract(code=factory_code, balance=1)
    tcreated = compute_tcreate_address(factory, SALT, initcode)
    sender = pre.fund_eoa()

    state_test(
        pre=pre,
        tx=Transaction(sender=sender, to=factory, gas_limit=3_000_000),
        post={
            # CALL into TCREATE account fails (CREATE2 halt) → slot 1 is 0
            factory: Account(storage={0: tcreated, 1: 0}, nonce=1),
            tcreated: Account.NONEXISTENT,
        },
    )


def test_create_from_tcreate_persists(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """CREATE from a TCREATE account deploys a persistent child."""
    child_runtime = Op.SSTORE(0, 0xC0DE) + Op.STOP
    child_init = Initcode(deploy_code=child_runtime)
    # TCREATE deploys runtime that CREATEs a persistent child (no SSTORE:
    # SSTORE would halt in a TCREATE account context).
    runtime = (
        Om.MSTORE(child_init, 0)
        + Op.CREATE(value=0, offset=0, size=len(child_init))
        + Op.STOP
    )
    initcode = Initcode(deploy_code=runtime)
    factory = pre.deploy_contract(
        code=(
            Om.MSTORE(initcode, 0)
            + Op.SSTORE(
                0,
                Op.TCREATE(value=0, offset=0, size=len(initcode), salt=SALT),
            )
            + Op.SSTORE(1, Op.CALL(address=Op.SLOAD(0)))
        ),
        balance=1,
    )
    tcreated = compute_tcreate_address(factory, SALT, initcode)
    child = compute_create_address(
        address=tcreated, nonce=1, opcode=Op.CREATE
    )

    storage = Storage()
    entry = pre.deploy_contract(
        code=Op.SSTORE(storage.store_next(1), Op.CALL(address=factory)),
        storage=storage.canary(),
    )
    sender = pre.fund_eoa()

    state_test(
        pre=pre,
        tx=Transaction(sender=sender, to=entry, gas_limit=3_000_000),
        post={
            entry: Account(storage=storage),
            factory: Account(storage={0: tcreated, 1: 1}, nonce=1),
            tcreated: Account.NONEXISTENT,
            child: Account(nonce=1, code=child_runtime),
        },
    )
