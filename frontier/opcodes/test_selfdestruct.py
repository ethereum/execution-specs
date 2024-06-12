"""
Test the SELFDESTRUCT opcode.
"""

import pytest

from ethereum_test_tools import Account, Alloc, Block, BlockchainTestFiller, Environment, Initcode
from ethereum_test_tools import Opcodes as Op
from ethereum_test_tools import Transaction


@pytest.mark.valid_from("Frontier")
@pytest.mark.valid_until("Homestead")
def test_double_kill(blockchain_test: BlockchainTestFiller, pre: Alloc):
    """
    Test that when two transactions attempt to destruct a contract,
    the second transaction actually resurrects the contract as an empty account (prior to Spurious
    Dragon).
    """
    env = Environment()
    sender = pre.fund_eoa()

    deploy_code = Op.SELFDESTRUCT(Op.ADDRESS)

    initcode = Initcode(deploy_code=deploy_code)

    create_tx = Transaction(
        gas_limit=100000000,
        protected=False,
        to=None,
        data=initcode,
        sender=sender,
    )

    block_1 = Block(txs=[create_tx])

    first_kill = Transaction(
        gas_limit=100000000,
        protected=False,
        to=create_tx.created_contract,
        sender=sender,
    )

    second_kill = Transaction(
        gas_limit=100000000,
        protected=False,
        to=create_tx.created_contract,
        sender=sender,
    )

    block_2 = Block(txs=[first_kill, second_kill])

    post = {
        create_tx.created_contract: Account(
            nonce=0,
            balance=0,
            code=b"",
            storage={},
        ),
    }

    blockchain_test(genesis_environment=env, pre=pre, post=post, blocks=[block_1, block_2])
