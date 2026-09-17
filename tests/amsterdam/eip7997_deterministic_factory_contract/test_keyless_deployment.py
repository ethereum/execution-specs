"""
Verify keyless deployment of the Deterministic Factory Contract.

<https://eips.ethereum.org/EIPS/eip-7997>

Verify the fixed keyless creation transaction before and after the
creation state-gas increase. Chains may also allocate the factory at
genesis.
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    BalAccountExpectation,
    BalNonceChange,
    Block,
    BlockAccessListExpectation,
    BlockchainTestFiller,
    EIPChecklist,
    Fork,
    Hash,
    Initcode,
    Op,
    Transaction,
    compute_create2_address,
    compute_create_address,
)

from .spec import KeylessDeployment, Spec, ref_spec_7997

REFERENCE_SPEC_GIT_PATH = ref_spec_7997.git_path
REFERENCE_SPEC_VERSION = ref_spec_7997.version

FORK_TIMESTAMP = 15_000

FACTORY = Address(Spec.FACTORY_ADDRESS)


def keyless_deployment_tx() -> Transaction:
    """Return the pre-signed transaction that creates the factory."""
    tx = Transaction(
        ty=0,
        protected=False,
        nonce=0,
        gas_price=KeylessDeployment.GAS_PRICE,
        gas_limit=KeylessDeployment.GAS_LIMIT,
        to=None,
        value=0,
        data=KeylessDeployment.INITCODE,
        v=KeylessDeployment.V,
        r=KeylessDeployment.R,
        s=KeylessDeployment.S,
    ).with_signature_and_sender()
    assert tx.sender == KeylessDeployment.DEPLOYER_ADDRESS
    assert compute_create_address(address=tx.sender, nonce=0) == FACTORY
    return tx


def remove_factory_contract(pre: Alloc) -> None:
    """
    Drop the fork's factory contract from the genesis allocation.

    Merging an all-zero account over the pre-allocation entry removes it
    entirely, so the chain starts without the factory.
    """
    pre[FACTORY] = Account(nonce=0, balance=0, code=b"")


@pytest.mark.valid_at_transition_to("Amsterdam")
@pytest.mark.pre_alloc_mutable
@EIPChecklist.SystemContract.Test.Deployment.Address()
@EIPChecklist.SystemContract.Test.ForkTransition.CallBeforeFork()
def test_keyless_deployment_before_fork(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
) -> None:
    """
    Deploy and use the factory in one pre-fork block and use it after.

    Preserve the factory's accrued nonce across the transition.
    """
    remove_factory_contract(pre)
    deploy_tx = keyless_deployment_tx()
    deployer = deploy_tx.sender
    assert deployer is not None
    pre.fund_address(
        deployer,
        KeylessDeployment.GAS_LIMIT * KeylessDeployment.GAS_PRICE,
    )
    sender = pre.fund_eoa()

    runtime_code = Op.RETURN(0, 1)
    initcode = Initcode(deploy_code=runtime_code)
    salts = {FORK_TIMESTAMP - 1: 0x1, FORK_TIMESTAMP: 0x2}

    blocks = [
        Block(
            timestamp=FORK_TIMESTAMP - 1,
            txs=[
                deploy_tx,
                Transaction(
                    sender=sender,
                    to=FACTORY,
                    data=Hash(salts[FORK_TIMESTAMP - 1]) + bytes(initcode),
                ),
            ],
        ),
        Block(
            timestamp=FORK_TIMESTAMP,
            txs=[
                Transaction(
                    sender=sender,
                    to=FACTORY,
                    data=Hash(salts[FORK_TIMESTAMP]) + bytes(initcode),
                ),
            ],
            expected_block_access_list=BlockAccessListExpectation(
                account_expectations={
                    FACTORY: BalAccountExpectation(
                        nonce_changes=[
                            BalNonceChange(block_access_index=1, post_nonce=3)
                        ],
                    ),
                }
            ),
        ),
    ]

    blockchain_test(
        pre=pre,
        blocks=blocks,
        post={
            FACTORY: Account(
                nonce=3,
                balance=0,
                code=Spec.FACTORY_BYTECODE,
            ),
            deployer: Account(nonce=1),
            **{
                compute_create2_address(FACTORY, salt, initcode): Account(
                    nonce=1, code=bytes(runtime_code)
                )
                for salt in salts.values()
            },
        },
    )


@pytest.mark.valid_at_transition_to("Amsterdam")
@pytest.mark.pre_alloc_mutable
def test_keyless_deployment_after_fork(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Exhaust the fixed keyless transaction budget in the top frame.

    Verify intrinsic validity and insufficient account-creation state gas.
    Leave the factory absent and charge the sender the full gas limit.
    Repairing an existing chain requires a separately coordinated state
    transition outside this EIP.
    """
    remove_factory_contract(pre)
    deploy_tx = keyless_deployment_tx()
    deployer = deploy_tx.sender
    assert deployer is not None
    active_fork = fork.fork_at(timestamp=FORK_TIMESTAMP)
    intrinsic_gas = active_fork.transaction_intrinsic_cost_calculator()(
        calldata=deploy_tx.data,
        contract_creation=True,
    )
    state_gas = active_fork.transaction_top_frame_state_gas(
        contract_creation=True,
    )
    assert intrinsic_gas < KeylessDeployment.GAS_LIMIT
    assert intrinsic_gas + state_gas > KeylessDeployment.GAS_LIMIT
    funding = KeylessDeployment.GAS_LIMIT * KeylessDeployment.GAS_PRICE
    pre.fund_address(deployer, funding)

    blockchain_test(
        pre=pre,
        blocks=[
            Block(timestamp=FORK_TIMESTAMP - 1),
            Block(timestamp=FORK_TIMESTAMP, txs=[deploy_tx]),
        ],
        post={
            FACTORY: Account.NONEXISTENT,
            # The whole gas limit is charged at the fixed gas price.
            deployer: Account(nonce=1, balance=0),
        },
    )
