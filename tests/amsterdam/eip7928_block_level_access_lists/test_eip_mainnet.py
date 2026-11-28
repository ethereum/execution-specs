"""
Mainnet marked execute checklist tests for
[EIP-7928: Block-level Access Lists](https://eips.ethereum.org/EIPS/eip-7928).
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    BalAccountExpectation,
    BalBalanceChange,
    BalCodeChange,
    BalNonceChange,
    BalStorageChange,
    BalStorageSlot,
    BlockAccessListExpectation,
    Fork,
    Initcode,
    Op,
    StateTestFiller,
    Transaction,
    compute_create_address,
)

from .spec import ref_spec_7928

REFERENCE_SPEC_GIT_PATH = ref_spec_7928.git_path
REFERENCE_SPEC_VERSION = ref_spec_7928.version

pytestmark = [pytest.mark.valid_at("Amsterdam"), pytest.mark.mainnet]


def test_bal_storage_and_value_mainnet(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Record a storage write, a storage read and a CALL value transfer in
    the BAL of one transaction on mainnet.
    """
    sender = pre.fund_eoa()
    recipient = pre.fund_eoa(amount=1)
    call_value = 1

    code = (
        Op.SSTORE(
            1,
            0x42,
            # gas accounting
            new_value=0x42,
        )
        + Op.POP(Op.SLOAD(2))
        + Op.POP(
            Op.CALL(
                address=recipient,
                value=call_value,
                # gas accounting
                value_transfer=True,
            )
        )
    )
    contract = pre.deploy_contract(code=code, balance=call_value)
    gas_limit = fork.transaction_intrinsic_cost_calculator()() + code.gas_cost(
        fork
    )

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=gas_limit,
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            contract: Account(storage={1: 0x42}, balance=0),
            recipient: Account(balance=1 + call_value),
        },
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                sender: BalAccountExpectation(
                    nonce_changes=[
                        BalNonceChange(block_access_index=1, post_nonce=1)
                    ],
                ),
                contract: BalAccountExpectation(
                    storage_changes=[
                        BalStorageSlot(
                            slot=1,
                            slot_changes=[
                                BalStorageChange(
                                    block_access_index=1, post_value=0x42
                                )
                            ],
                        ),
                    ],
                    storage_reads=[2],
                    balance_changes=[
                        BalBalanceChange(block_access_index=1, post_balance=0)
                    ],
                ),
                recipient: BalAccountExpectation(
                    balance_changes=[
                        BalBalanceChange(
                            block_access_index=1, post_balance=1 + call_value
                        )
                    ],
                ),
            }
        ),
    )


def test_bal_contract_creation_mainnet(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Record the deployed code and nonce of a contract created by a
    creation transaction in the BAL on mainnet.
    """
    sender = pre.fund_eoa()
    deploy_code = Op.PUSH1(0x42) + Op.STOP
    created = compute_create_address(address=sender, nonce=0)
    initcode = Initcode(deploy_code=deploy_code)
    gas_limit = (
        fork.transaction_intrinsic_cost_calculator()(
            calldata=initcode, contract_creation=True
        )
        + fork.transaction_top_frame_state_gas(contract_creation=True)
        + initcode.evm_gas(fork)
        + initcode.deployment_gas(fork)
    )

    tx = Transaction(
        sender=sender,
        to=None,
        data=initcode,
        gas_limit=gas_limit,
    )

    state_test(
        pre=pre,
        tx=tx,
        post={created: Account(nonce=1, code=deploy_code)},
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                sender: BalAccountExpectation(
                    nonce_changes=[
                        BalNonceChange(block_access_index=1, post_nonce=1)
                    ],
                ),
                created: BalAccountExpectation(
                    nonce_changes=[
                        BalNonceChange(block_access_index=1, post_nonce=1)
                    ],
                    code_changes=[
                        BalCodeChange(
                            block_access_index=1, new_code=bytes(deploy_code)
                        )
                    ],
                ),
            }
        ),
    )
