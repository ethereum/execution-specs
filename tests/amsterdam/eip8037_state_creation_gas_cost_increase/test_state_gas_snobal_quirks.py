"""
Snøbal devnet-specific tests locking in current spec behavior under
EIP-8037.

These tests document accounting quirks present in the snøbal devnet
spec so client implementations targeting the devnet can be verified
end-to-end. They do **not** describe the intended long-term semantics.

Bug locked in here:
  `set_delegation` (vm/eoa_delegation.py) credits
  `message.state_gas_reservoir` when the authority pre-exists in state,
  but `process_transaction` (fork.py) does not deduct that refund from
  `tx_state_gas`. Result: `block_state_gas_used` over-counts state gas
  by `STATE_BYTES_PER_NEW_ACCOUNT * COST_PER_STATE_BYTE` per
  existing-authority auth tuple.

Delete this file when the spec is fixed (e.g. by adding
`MessageCallOutput.state_refund` and subtracting it from `tx_state_gas`,
mirroring the post-execution selfdestruct refund pattern).
"""

import pytest
from execution_testing import (
    Alloc,
    AuthorizationTuple,
    Block,
    BlockchainTestFiller,
    Fork,
    Header,
    Op,
    Transaction,
)

from .spec import ref_spec_8037

REFERENCE_SPEC_GIT_PATH = ref_spec_8037.git_path
REFERENCE_SPEC_VERSION = ref_spec_8037.version


@pytest.mark.valid_from("EIP8037")
def test_snobal_block_gas_used_inflated_by_7702_auth_refund(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Lock in: block.header.gas_used reflects the FULL intrinsic state
    gas for an EIP-7702 SetCodeTx whose authority pre-exists in state.

    Scenario: one SetCodeTx with one authorization tuple pointing at a
    do-nothing contract. The authority is funded so it pre-exists,
    triggering the auth-refund credit to `state_gas_reservoir` inside
    `set_delegation`. The tx body executes only the delegated `STOP`,
    so `state_gas_used == 0` and `tx_state_gas == intrinsic_state_gas`
    under the current (buggy) accounting.

    Snøbal expected: block.gas_used = intrinsic_state_gas
        (since intrinsic_state_gas dominates intrinsic_regular)
    Post-fix expected: block.gas_used = intrinsic_regular
        (after auth_state_refund deduction, regular dominates)
    """
    sender = pre.fund_eoa()
    authority = pre.fund_eoa()
    target = pre.deploy_contract(code=Op.STOP)

    auth_state_gas = fork.transaction_intrinsic_state_gas(
        authorization_count=1,
    )
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None

    tx = Transaction(
        to=authority,
        gas_limit=gas_limit_cap + auth_state_gas,
        sender=sender,
        authorization_list=[
            AuthorizationTuple(
                address=target,
                nonce=0,
                signer=authority,
            ),
        ],
    )

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx],
                header_verify=Header(gas_used=auth_state_gas),
            )
        ],
        post={},
    )
