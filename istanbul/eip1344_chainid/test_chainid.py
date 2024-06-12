"""
abstract: Tests [EIP-1344: CHAINID opcode](https://eips.ethereum.org/EIPS/eip-1344)
    Test cases for [EIP-1344: CHAINID opcode](https://eips.ethereum.org/EIPS/eip-1344).
"""

import pytest

from ethereum_test_tools import Account, Alloc, Environment, StateTestFiller, Transaction
from ethereum_test_tools.vm.opcode import Opcodes as Op

REFERENCE_SPEC_GIT_PATH = "EIPS/eip-1344.md"
REFERENCE_SPEC_VERSION = "02e46aebc80e6e5006ab4d2daa41876139f9a9e2"


@pytest.mark.valid_from("Istanbul")
def test_chainid(state_test: StateTestFiller, pre: Alloc):
    """
    Test CHAINID opcode.
    """
    env = Environment(
        fee_recipient="0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba",
        difficulty=0x20000,
        gas_limit=10000000000,
        number=1,
        timestamp=1000,
    )

    contract_address = pre.deploy_contract(Op.SSTORE(1, Op.CHAINID) + Op.STOP)
    sender = pre.fund_eoa()

    tx = Transaction(
        ty=0x0,
        chain_id=0x01,
        to=contract_address,
        gas_limit=100000000,
        gas_price=10,
        sender=sender,
    )

    post = {
        contract_address: Account(storage={"0x01": "0x01"}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
