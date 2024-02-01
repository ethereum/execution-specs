"""
abstract: Tests [EIP-3855: PUSH0 Instruction](https://eips.ethereum.org/EIPS/eip-3855)
    Tests for [EIP-3855: PUSH0 Instruction](https://eips.ethereum.org/EIPS/eip-3855).

note: Tests ported from:
    - [ethereum/tests/pull/1033](https://github.com/ethereum/tests/pull/1033).
"""

import pytest

from ethereum_test_tools import (
    Account,
    Address,
    CodeGasMeasure,
    Environment,
    StateTestFiller,
    TestAddress,
    Transaction,
)
from ethereum_test_tools.vm.opcode import Opcodes as Op

REFERENCE_SPEC_GIT_PATH = "EIPS/eip-3855.md"
REFERENCE_SPEC_VERSION = "42034250ae8dd4b21fdc6795773893c6f1e74d3a"

pytestmark = pytest.mark.valid_from("Shanghai")


@pytest.fixture
def env():  # noqa: D103
    return Environment()


@pytest.fixture
def pre():  # noqa: D103
    return {TestAddress: Account(balance=1000000000000000000000)}


@pytest.fixture
def post():  # noqa: D103
    return {}


@pytest.fixture
def addr_1():  # noqa: D103
    return Address(0x100)


@pytest.fixture
def tx(addr_1):  # noqa: D103
    return Transaction(
        to=addr_1,
        gas_limit=100000,
    )


def test_push0_key_sstore(
    state_test: StateTestFiller,
    env: Environment,
    pre: dict,
    post: dict,
    tx: Transaction,
    addr_1: str,
):
    """
    Use PUSH0 to set a key for SSTORE.
    """
    code = Op.SSTORE(Op.PUSH0, 1)

    pre[addr_1] = Account(code=code)
    post[addr_1] = Account(storage={0x00: 0x01})

    state_test(env=env, pre=pre, post=post, tx=tx, tag="key_sstore")


def test_push0_fill_stack(
    state_test: StateTestFiller,
    env: Environment,
    pre: dict,
    post: dict,
    tx: Transaction,
    addr_1: str,
):
    """
    Fill stack with PUSH0, then OR all values and save using SSTORE.
    """
    code = Op.PUSH0 * 1024
    code += Op.OR * 1023
    code += Op.SSTORE(Op.SWAP1, 1)

    pre[addr_1] = Account(code=code)
    post[addr_1] = Account(storage={0x00: 0x01})

    state_test(env=env, pre=pre, post=post, tx=tx, tag="fill_stack")


def test_push0_stack_overflow(
    state_test: StateTestFiller,
    env: Environment,
    pre: dict,
    post: dict,
    tx: Transaction,
    addr_1: str,
):
    """
    Stack overflow by using PUSH0 1025 times.
    """
    code = Op.SSTORE(Op.PUSH0, 1)
    code += Op.PUSH0 * 1025

    pre[addr_1] = Account(code=code)
    post[addr_1] = Account(storage={0x00: 0x00})

    state_test(env=env, pre=pre, post=post, tx=tx, tag="stack_overflow")


def test_push0_storage_overwrite(
    state_test: StateTestFiller,
    env: Environment,
    pre: dict,
    post: dict,
    tx: Transaction,
    addr_1: str,
):
    """
    Update an already existing storage value.
    """
    code = Op.SSTORE(Op.PUSH0, 2) + Op.SSTORE(1, Op.PUSH0)

    pre[addr_1] = Account(code=code, storage={0x00: 0x0A, 0x01: 0x0A})
    post[addr_1] = Account(storage={0x00: 0x02, 0x01: 0x00})

    state_test(env=env, pre=pre, post=post, tx=tx, tag="storage_overwrite")


def test_push0_during_staticcall(
    state_test: StateTestFiller,
    env: Environment,
    pre: dict,
    post: dict,
    tx: Transaction,
    addr_1: str,
):
    """
    Test PUSH0 during STATICCALL.
    """
    addr_2 = Address(0x200)

    code_1 = (
        Op.SSTORE(0, Op.STATICCALL(100000, 0x200, 0, 0, 0, 0))
        + Op.SSTORE(0, 1)
        + Op.RETURNDATACOPY(0x1F, 0, 1)
        + Op.SSTORE(1, Op.MLOAD(0))
    )
    code_2 = Op.MSTORE8(Op.PUSH0, 0xFF) + Op.RETURN(Op.PUSH0, 1)

    pre[addr_1] = Account(code=code_1)
    pre[addr_2] = Account(code=code_2)
    post[addr_1] = Account(storage={0x00: 0x01, 0x01: 0xFF})

    state_test(env=env, pre=pre, post=post, tx=tx, tag="during_staticcall")


def test_push0_before_jumpdest(
    state_test: StateTestFiller,
    env: Environment,
    pre: dict,
    post: dict,
    tx: Transaction,
    addr_1: str,
):
    """
    Jump to a JUMPDEST next to a PUSH0, must succeed.
    """
    code = Op.PUSH1(4) + Op.JUMP + Op.PUSH0 + Op.JUMPDEST + Op.SSTORE(Op.PUSH0, 1) + Op.STOP

    pre[addr_1] = Account(code=code)
    post[addr_1] = Account(storage={0x00: 0x01})

    state_test(env=env, pre=pre, post=post, tx=tx, tag="before_jumpdest")


def test_push0_gas_cost(
    state_test: StateTestFiller,
    env: Environment,
    pre: dict,
    post: dict,
    tx: Transaction,
    addr_1: str,
):
    """
    Test PUSH0 gas cost.
    """
    code = CodeGasMeasure(
        code=Op.PUSH0,
        extra_stack_items=1,
    )

    pre[addr_1] = Account(code=code)
    post[addr_1] = Account(storage={0x00: 0x02})

    state_test(env=env, pre=pre, post=post, tx=tx, tag="gas_cost")
