"""Test Account Self-destruction and Re-creation."""

import pytest

from ethereum_test_forks import Fork
from ethereum_test_tools import (
    Account,
    Alloc,
    Block,
    BlockchainTestFiller,
    Environment,
    Initcode,
    Transaction,
    Yul,
    compute_create2_address,
)
from ethereum_test_tools import Opcodes as Op

from .spec import ref_spec_1014

REFERENCE_SPEC_GIT_PATH = ref_spec_1014.git_path
REFERENCE_SPEC_VERSION = ref_spec_1014.version


@pytest.mark.parametrize("recreate_on_separate_block", [True, False])
@pytest.mark.valid_from("Constantinople")
@pytest.mark.valid_until("Shanghai")
def test_recreate(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    recreate_on_separate_block: bool,
):
    """
    Test that the storage is cleared when a contract is first destructed then re-created using
    CREATE2.
    """
    env = Environment()

    creator_contract_code = Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE) + Op.CREATE2(
        0, 0, Op.CALLDATASIZE, 0
    )
    creator_address = pre.deploy_contract(creator_contract_code)
    sender = pre.fund_eoa()

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
        gas_limit=100000000,
        to=creator_address,
        data=initcode,
        sender=sender,
    )

    created_contract_address = compute_create2_address(
        address=creator_address, salt=0, initcode=initcode
    )

    set_storage_tx = Transaction(
        gas_limit=100000000,
        to=created_contract_address,
        value=1,
        sender=sender,
    )

    blocks = [Block(txs=[create_tx, set_storage_tx])]

    destruct_tx = Transaction(
        gas_limit=100000000,
        to=created_contract_address,
        value=0,
        sender=sender,
    )

    balance = 1
    send_funds_tx = Transaction(
        gas_limit=100000000,
        to=created_contract_address,
        value=balance,
        sender=sender,
    )

    re_create_tx = Transaction(
        gas_limit=100000000,
        to=creator_address,
        data=initcode,
        sender=sender,
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
