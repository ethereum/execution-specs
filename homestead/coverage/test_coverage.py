"""
Tests that address coverage gaps that result from updating `ethereum/tests` into EEST tests.
"""

import pytest

from ethereum_test_tools import Alloc, Environment, StateTestFiller, Transaction
from ethereum_test_tools.vm.opcode import Opcodes as Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.valid_from("Homestead")
def test_yul_coverage(
    state_test: StateTestFiller,
    pre: Alloc,
):
    """
    This test covers gaps that result from transforming Yul code into
    `ethereum_test_tools.vm.opcode.Opcodes` bytecode.

    E.g. Yul tends to optimize stack items by using `SWAP1` and `DUP1` opcodes, which are not
    regularly used in python code.

    Modify this test to cover more Yul code if required in the future.
    """
    missed_coverage = pre.deploy_contract(
        balance=0,
        code=Op.SHL(0x0000000000000000000000000000000000000000000000000000000000000001, 0x00)
        + Op.SHR(0x0000000000000000000000000000000000000000000000000000000000000001, 0x00)
        + Op.PUSH1(0x0A)
        + Op.PUSH1(0x0B)
        + Op.PUSH1(0x0C)
        + Op.PUSH1(0x0D)
        + Op.PUSH1(0x0E)
        + Op.SWAP1()
        + Op.DUP1()
        + Op.DUP2()
        + Op.PUSH0()
        + Op.PUSH2(0x0102)
        + Op.PUSH3(0x010203)
        + Op.PUSH4(0x01020304)
        + Op.POP(0x01),
        storage={},
    )
    address_to = pre.deploy_contract(
        balance=1_000_000_000_000_000_000,
        code=Op.MSTORE(0, Op.CALL(Op.GAS, missed_coverage, 0, 0, 0, 0, 0)) + Op.RETURN(0, 32),
    )

    tx = Transaction(
        sender=pre.fund_eoa(7_000_000_000_000_000_000),
        gas_limit=100000,
        to=address_to,
        data=b"",
        value=0,
        protected=False,
    )

    state_test(env=Environment(), pre=pre, post={}, tx=tx)
