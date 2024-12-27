"""test execution semantics changes."""

import pytest

from ethereum_test_tools import (
    Account,
    Alloc,
    Environment,
    StateTestFiller,
    Storage,
    Transaction,
    keccak256,
)
from ethereum_test_tools import Opcodes as Op
from ethereum_test_tools.eof.v1 import Container

from .. import EOF_FORK_NAME

pytestmark = pytest.mark.valid_from(EOF_FORK_NAME)

REFERENCE_SPEC_GIT_PATH = "EIPS/eip-4750.md"
REFERENCE_SPEC_VERSION = "90f716078d0b08ce508a1e57803f885cc2f2e15e"


def test_legacy_calls_eof_sstore(
    state_test: StateTestFiller,
    pre: Alloc,
):
    """Test EXTCODE* opcodes calling EOF and legacy contracts."""
    env = Environment()
    eof_code = Container.Code(Op.RJUMP[0] + Op.STOP)
    address_eof_contract = pre.deploy_contract(eof_code)
    legacy_code = Op.PUSH1(2) + Op.JUMPDEST + Op.STOP
    address_legacy_contract = pre.deploy_contract(legacy_code)

    storage_test = Storage()
    test_contract_code = (
        Op.SSTORE(storage_test.store_next(4), Op.EXTCODESIZE(address_legacy_contract))
        + Op.EXTCODECOPY(address_legacy_contract, 0, 0, Op.EXTCODESIZE(address_legacy_contract))
        + Op.SSTORE(
            storage_test.store_next(bytes(legacy_code).ljust(32, b"\0")),
            Op.MLOAD(0),
        )
        + Op.SSTORE(
            storage_test.store_next(legacy_code.keccak256()),
            Op.EXTCODEHASH(address_legacy_contract),
        )
        + Op.SSTORE(storage_test.store_next(2), Op.EXTCODESIZE(address_eof_contract))
        + Op.EXTCODECOPY(address_eof_contract, 0x20, 0, 6)
        + Op.SSTORE(storage_test.store_next(b"\xef".ljust(32, b"\0")), Op.MLOAD(0x20))
        + Op.MSTORE(0x40, b"\xcc" * 32)  # clobber memory slot
        + Op.EXTCODECOPY(address_eof_contract, 0x40, len(eof_code) - 4, 8)  # out-of-bounds "read"
        + Op.SSTORE(storage_test.store_next(b"\xcc" * 24), Op.MLOAD(0x40))
        + Op.SSTORE(
            storage_test.store_next(keccak256(b"\xef\x00")),
            Op.EXTCODEHASH(address_eof_contract),
        )
    )
    address_test_contract = pre.deploy_contract(test_contract_code)

    sender = pre.fund_eoa()

    tx = Transaction(
        sender=sender,
        to=address_test_contract,
        gas_limit=50_000_000,
        gas_price=10,
        protected=False,
        data="",
    )

    post = {
        address_test_contract: Account(storage=storage_test),
    }

    state_test(
        env=env,
        pre=pre,
        post=post,
        tx=tx,
    )
