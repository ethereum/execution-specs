"""
test execution semantics changes
"""
import pytest
from ethereum.crypto.hash import keccak256

from ethereum_test_tools import (
    Account,
    Address,
    Environment,
    StateTestFiller,
    Storage,
    TestAddress,
    Transaction,
)
from ethereum_test_tools.eof.v1 import Container, Section
from ethereum_test_tools.eof.v1.constants import NON_RETURNING_SECTION
from ethereum_test_tools.vm.opcode import Opcodes as Op

from .. import EOF_FORK_NAME

pytestmark = pytest.mark.valid_from(EOF_FORK_NAME)

REFERENCE_SPEC_GIT_PATH = "EIPS/eip-4750.md"
REFERENCE_SPEC_VERSION = "90f716078d0b08ce508a1e57803f885cc2f2e15e"


def test_legacy_calls_eof_sstore(
    state_test: StateTestFiller,
):
    """Test EXTCODE* opcodes calling EOF and legacy contracts"""
    env = Environment()
    address_eof_contract = Address(0x1000000)
    address_legacy_contract = Address(0x1000001)
    address_test_contract = Address(0x1000002)
    storage_test = Storage()

    legacy_code = Op.PUSH1(2) + Op.JUMPDEST + Op.STOP
    pre = {
        TestAddress: Account(
            balance=1000000000000000000000,
            nonce=1,
        ),
        address_eof_contract: Account(
            code=Container(
                sections=[
                    Section.Code(
                        code=Op.RJUMP[0] + Op.STOP,
                        code_outputs=NON_RETURNING_SECTION,
                    )
                ]
            ),
            nonce=1,
        ),
        address_legacy_contract: Account(
            code=legacy_code,
            nonce=1,
        ),
        address_test_contract: Account(
            code=Op.SSTORE(storage_test.store_next(4), Op.EXTCODESIZE(address_legacy_contract))
            + Op.EXTCODECOPY(
                address_legacy_contract, 0, 0, Op.EXTCODESIZE(address_legacy_contract)
            )
            + Op.SSTORE(
                storage_test.store_next(legacy_code + (b"\0" * (32 - len(legacy_code)))),
                Op.MLOAD(0),
            )
            + Op.SSTORE(
                storage_test.store_next(keccak256(legacy_code)),
                Op.EXTCODEHASH(address_legacy_contract),
            )
            + Op.SSTORE(storage_test.store_next(2), Op.EXTCODESIZE(address_eof_contract))
            + Op.EXTCODECOPY(address_eof_contract, 0x20, 0, Op.EXTCODESIZE(address_eof_contract))
            + Op.SSTORE(storage_test.store_next(b"\xef" + (b"\0" * 31)), Op.MLOAD(0x20))
            + Op.SSTORE(
                storage_test.store_next(keccak256(b"\xef\x00")),
                Op.EXTCODEHASH(address_eof_contract),
            )
        ),
    }

    tx = Transaction(
        nonce=1,
        to=Address(address_test_contract),
        gas_limit=50000000,
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
