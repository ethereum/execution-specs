"""
Test Account Self-destruction and Re-creation
"""

import pytest

from ethereum_test_forks import Fork
from ethereum_test_tools import Account, Block, BlockchainTestFiller, Environment, Initcode
from ethereum_test_tools import Opcodes as Op
from ethereum_test_tools import TestAddress, Transaction, Yul, compute_create2_address


@pytest.mark.parametrize("recreate_on_separate_block", [True, False])
@pytest.mark.valid_from("Constantinople")
@pytest.mark.valid_until("Shanghai")
def test_recreate(
    blockchain_test: BlockchainTestFiller, fork: Fork, recreate_on_separate_block: bool
):
    """
    Test that the storage is cleared when a contract is first destructed then re-created using
    CREATE2.
    """
    env = Environment()

    creator_address = 0x100
    creator_contract_code = Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE) + Op.CREATE2(
        0, 0, Op.CALLDATASIZE, 0
    )

    pre = {
        TestAddress: Account(balance=1000000000000000000000),
        creator_address: Account(
            code=creator_contract_code,
            nonce=1,
        ),
    }

    deploy_code = Yul(
        """
        {
            switch callvalue()
            case 0 {
                selfdestruct(0)
            }
            default {
                sstore(0, callvalue())
            }
        }
        """,
        fork=fork,
    )

    initcode = Initcode(deploy_code=deploy_code)

    create_tx = Transaction(
        nonce=0,
        gas_limit=100000000,
        to=creator_address,
        data=initcode,
    )

    created_contract_address = compute_create2_address(
        address=creator_address, salt=0, initcode=initcode
    )

    set_storage_tx = Transaction(
        nonce=1,
        gas_limit=100000000,
        to=created_contract_address,
        value=1,
    )

    blocks = [Block(txs=[create_tx, set_storage_tx])]

    destruct_tx = Transaction(
        nonce=2,
        gas_limit=100000000,
        to=created_contract_address,
        value=0,
    )

    balance = 1
    send_funds_tx = Transaction(
        nonce=3,
        gas_limit=100000000,
        to=created_contract_address,
        value=balance,
    )

    re_create_tx = Transaction(
        nonce=4,
        gas_limit=100000000,
        to=creator_address,
        data=initcode,
    )

    if recreate_on_separate_block:
        blocks.append(Block(txs=[destruct_tx, send_funds_tx]))
        blocks.append(Block(txs=[re_create_tx]))
    else:
        blocks.append(Block(txs=[destruct_tx, send_funds_tx, re_create_tx]))

    post = {
        created_contract_address: Account(
            nonce=1,
            balance=balance,
            code=deploy_code,
            storage={},
        ),
    }

    blockchain_test(genesis_environment=env, pre=pre, post=post, blocks=blocks)
