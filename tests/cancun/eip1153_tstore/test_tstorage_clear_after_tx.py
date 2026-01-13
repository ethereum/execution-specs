"""EIP-1153 Transient Storage tests."""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Block,
    BlockchainTestFiller,
    Environment,
    Initcode,
    Op,
    Transaction,
)

from .spec import ref_spec_1153

REFERENCE_SPEC_GIT_PATH = ref_spec_1153.git_path
REFERENCE_SPEC_VERSION = ref_spec_1153.version


@pytest.mark.valid_from("Cancun")
def test_tstore_clear_after_deployment_tx(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
) -> None:
    """
    First creates a contract, which TSTOREs a value 1 in slot 1. After creating
    the contract, a new tx will call this contract, storing TLOAD(1) into slot
    1. The transient storage should be cleared after creating the contract (at
    tx-level), so the storage should stay empty.
    """
    env = Environment()

    init_code = Op.TSTORE(1, 1)
    deploy_code = Op.SSTORE(1, Op.TLOAD(1))

    code = Initcode(deploy_code=deploy_code, initcode_prefix=init_code)

    sender = pre.fund_eoa()

    deployment_tx = Transaction(
        gas_limit=100000,
        data=code,
        to=None,
        sender=sender,
    )

    address = deployment_tx.created_contract

    invoke_contract_tx = Transaction(
        gas_limit=100000, to=address, sender=sender
    )

    txs = [deployment_tx, invoke_contract_tx]

    post = {
        address: Account(storage={0x01: 0x00}),
    }

    blockchain_test(
        genesis_environment=env, pre=pre, post=post, blocks=[Block(txs=txs)]
    )


@pytest.mark.valid_from("Cancun")
def test_tstore_clear_after_tx(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
) -> None:
    """
    First SSTOREs the TLOAD value of key 1 in slot 1. Then, it TSTOREs 1 in
    slot 1. The second tx will re-call the contract. The storage should stay
    empty, because the transient storage is cleared after the transaction.
    """
    env = Environment()

    code = Op.SSTORE(1, Op.TLOAD(1)) + Op.TSTORE(1, 1)
    account = pre.deploy_contract(code)

    sender = pre.fund_eoa()

    poke_tstore_tx = Transaction(
        gas_limit=100000,
        to=account,
        sender=sender,
    )

    re_poke_tstore_tx = Transaction(
        gas_limit=100000, to=account, sender=sender
    )

    txs = [poke_tstore_tx, re_poke_tstore_tx]

    post = {
        account: Account(storage={0x01: 0x00}),
    }

    blockchain_test(
        genesis_environment=env, pre=pre, post=post, blocks=[Block(txs=txs)]
    )
